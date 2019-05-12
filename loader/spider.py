"""GitHub graph crawler."""

import time
import logging
import traceback

from itertools import islice
from concurrent import futures

from tqdm import tqdm
from gremlin_python.process.graph_traversal import GraphTraversal, __
from gremlin_python.process.traversal import P, Order

from loader.github import GitHub


URI = '_uri'
TIME_CREATED = '_created'
TIME_PROCESSED = '_processed'
ERROR = '_error'
ERROR_TRACE = '_error_trace'


class Spider:

    def __init__(self, g:GraphTraversal, github:GitHub, relatives_cap):
        super().__init__()
        self.github = github
        self.g = g
        self.relatives_cap = relatives_cap

    def _get_or_create_node(self, label:str, uri:str):
        return self.g.V().has(URI, uri).hasLabel(label).fold().coalesce(
            __.unfold(),
            __.addV(label).property(URI, uri)
        )

    def _get_or_created_edge_from(self, node: GraphTraversal, other: int, label: str):
        return node.coalesce(
            __.inE(label).filter(__.outV().hasId(other)),
            __.addE(label).from_(self.g.V(other))
        )

    def _get_or_created_edge_to(self, node: GraphTraversal, other: int, label: str):
        return node.coalesce(
            __.outE(label).filter(__.inV().hasId(other)),
            __.addE(label).to(self.g.V(other))
        )

    def _get_node_id(self, uri:str):
        nodes = self.g.V().has(URI, uri).id().toList()
        assert len(nodes) <= 1

        if nodes:
            return nodes[0]
        return None

    def _add_properties(self, element, properties):
        if properties is not None:
            for key, value in properties.items():
                if value is not None:
                    element = element.property(key, value)
        return element

    def _merge_node(self, label:str, properties: dict):
        assert URI not in properties
        assert 'id' in properties

        uri = properties.pop('id')

        # assert self.g.V().has(URI, uri).count().next() <= 1
        vertex = self._get_or_create_node(label, uri)

        vertex.property(TIME_CREATED, time.time())
        vertex.property(TIME_PROCESSED, 0.0)
        vertex = self._add_properties(vertex, properties)

        return vertex

    def _mark_processed(self, node_id:int):
        self.g.V(node_id).property(TIME_PROCESSED, time.time()).next()

    def _process_relatives(self, parent_id, relatives, label, edge_label, reverse_edge=False):
        fs = []
        for relative in islice(relatives, self.relatives_cap):
            if 'node' in relative:
                edge_props = relative
                relative = relative.pop('node')
            else:
                edge_props = None

            relative_node = self._merge_node(label, relative)

            if reverse_edge:
                edge = self._get_or_created_edge_from(relative_node, parent_id, edge_label)
            else:
                edge = self._get_or_created_edge_to(relative_node, parent_id, edge_label)

            fs.append(self._add_properties(edge, edge_props).promise())

        futures.wait(fs)

    def _process_repository(self, uri:str):
        node_id = self._get_node_id(uri)

        # TODO get ancestors (OG fork)
        # TODO fix broken ones
        # TODO add nested fields
        # TODO bulk/async?
        # TODO rename?
        # self._process_relatives(node_id, islice(self.github.get_repository_forks(uri), 3), 'repository', 'fork')
        self._process_relatives(node_id, self.github.get_repository_assignable_users(uri), 'user', 'assignable')
        # Must have access for collaborators...
        # self._process_relatives(node_id, self.github.get_repository_collaborators(uri), 'user', 'collaborator')
        # TODO why are stargazers only in repo?
        self._process_relatives(node_id, self.github.get_repository_stargazers(uri), 'user', 'stargazer')

        self._process_relatives(node_id, self.github.get_repository_commit_comments(uri), 'commit-comment', 'contains')
        self._process_relatives(node_id, self.github.get_repository_releases(uri), 'release', 'contains')
        self._process_relatives(node_id, self.github.get_repository_issues(uri), 'issue', 'contains')
        self._process_relatives(node_id, self.github.get_repository_milestones(uri), 'milestone', 'contains')
        # TODO these often cause 502
        # self._process_relatives(node_id, self.github.get_repository_pull_requests(uri), 'pull', 'contains')

        self._process_relatives(node_id, self.github.get_repository_languages(uri), 'language', 'uses')

        self._mark_processed(node_id)

    def _process_user(self, uri:str):
        node_id = self._get_node_id(uri)

        self._process_relatives(node_id, self.github.get_user_followers(uri), 'user', 'follows', reverse_edge=True)
        self._process_relatives(node_id, self.github.get_user_following(uri), 'user', 'follows')
        self._process_relatives(node_id, self.github.get_user_commit_comments(uri), 'commit-comment', 'wrote')
        self._process_relatives(node_id, self.github.get_user_issues(uri), 'issue', 'wrote')
        # TODO these often cause 502
        # self._process_relatives(node_id, self.github.get_user_pull_requests(uri), 'pull', 'created')
        self._process_relatives(node_id, self.github.get_user_repositories(uri), 'repository', 'created')
        self._process_relatives(node_id, self.github.get_user_repositories_contributed_to(uri), 'repository', 'contributed-to')
        self._process_relatives(node_id, self.github.get_user_watching(uri), 'repository', 'watches')

        self._mark_processed(node_id)

    def _process_do_nothing(self, uri:str):
        node_id = self._get_node_id(uri)
        self._mark_processed(node_id)

    def load_repository(self, ghid_or_url):
        return self._merge_node('repository', self.github.get_repository(ghid_or_url)).id().next()

    def has_unprocessed(self):
        return self.g.V().has(TIME_PROCESSED, 0.0).hasNext()

    def process(self, quiet=False):
        start = time.time()
        nodes_count = self.g.V().has(TIME_PROCESSED, 0.0).has(TIME_CREATED, P.lte(start)).count().next()

        if not quiet:
            logging.info('Starting iteration at {} with {}/{} nodes to process.'.format(start, nodes_count, self.g.V().count().next()))

        processors = {
            'repository': self._process_repository,
            'user': self._process_user,
            'language': self._process_do_nothing,
            'commit-comment': self._process_do_nothing,
            'release': self._process_do_nothing,
            'issue': self._process_do_nothing,
            'pull': self._process_do_nothing,
            'milestone': self._process_do_nothing,
        }

        # shuffle takes a long time, we process nodes in order instead
        nodes = self.g.V().has(TIME_PROCESSED, 0.0).has(TIME_CREATED, P.lte(start))
        for node in tqdm(nodes, total=nodes_count, unit='node', disable=quiet):
            label = self.g.V(node).label().next()
            uri = self.g.V(node).properties(URI).value().next()

            try:
                processors[label](uri)
            except Exception as e:
                logging.exception(e)
                self.g.V(node)\
                    .property(ERROR, str(e))\
                    .property(ERROR_TRACE, traceback.format_exc())\
                    .iterate()
