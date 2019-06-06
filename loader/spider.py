"""GitHub graph crawler."""

import logging
import time
import traceback
from concurrent import futures
from itertools import chain

from gremlin_python.process.graph_traversal import GraphTraversal, __
from gremlin_python.process.traversal import P
from timeout_decorator import timeout
from tqdm import tqdm

from loader.github import GitHub

URI = '_uri'
TIME_CREATED = '_created'
TIME_PROCESSED = '_processed'
ERROR = '_error'
ERROR_TRACE = '_error_trace'


class Spider:
    def __init__(self, g: GraphTraversal, github: GitHub, relatives_limit, max_property_size, tokens):
        super().__init__()
        self.github = github
        self.g = g
        self.relatives_limit = relatives_limit
        self.max_property_size = max_property_size
        self.tokens = tokens

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
                if hasattr(value, '__len__') and len(value) > self.max_property_size:
                    raise ValueError('Property exceded length limit.')
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

    def _mark_processed(self, node_id: int):
        self.g.V(node_id).property(TIME_PROCESSED, time.time()).next()

    @timeout(600)
    def _process_relatives(self, parent_id, relatives, label, edge_label, reverse_edge=False):
        fs = []
        for relative in relatives:
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

        # self._process_relatives(node_id, self.github.get_repository_forks(uri, self.relatives_limit),
        #                         'repository', 'fork')
        self._process_relatives(node_id, self.github.get_repository_assignable_users(uri, self.relatives_limit),
                                'user', 'assignable')
        # Must have access for collaborators...
        # self._process_relatives(node_id, self.github.get_repository_collaborators(uri, self.relatives_limit),
        #                         'user', 'collaborator')
        self._process_relatives(node_id, self.github.get_repository_stargazers(uri, self.relatives_limit),
                                'user', 'stargazer')

        self._process_relatives(node_id, self.github.get_repository_commit_comments(uri, self.relatives_limit),
                                'commit-comment', 'contains')
        self._process_relatives(node_id, self.github.get_repository_releases(uri, self.relatives_limit),
                                'release', 'contains')
        self._process_relatives(node_id, self.github.get_repository_issues(uri, self.relatives_limit),
                                'issue', 'contains')
        self._process_relatives(node_id, self.github.get_repository_milestones(uri, self.relatives_limit),
                                'milestone', 'contains')
        # TODO these often causes 502
        # self._process_relatives(node_id, self.github.get_repository_pull_requests(uri, self.relatives_limit), 'pull', 'contains')

        self._process_relatives(node_id, self.github.get_repository_languages(uri, self.relatives_limit), 'language', 'uses')

        self._mark_processed(node_id)

    def _process_user(self, uri:str):
        node_id = self._get_node_id(uri)

        self._process_relatives(node_id, self.github.get_user_followers(uri, self.relatives_limit),
                                'user', 'follows', reverse_edge=True)
        self._process_relatives(node_id, self.github.get_user_following(uri, self.relatives_limit),
                                'user', 'follows')
        self._process_relatives(node_id, self.github.get_user_commit_comments(uri, self.relatives_limit),
                                'commit-comment', 'wrote')
        self._process_relatives(node_id, self.github.get_user_issues(uri, self.relatives_limit),
                                'issue', 'wrote')
        # TODO these often causes 502
        # self._process_relatives(node_id, self.github.get_user_pull_requests(uri, self.relatives_limit),
        #                         'pull', 'created')
        self._process_relatives(node_id, self.github.get_user_repositories(uri, self.relatives_limit),
                                'repository', 'created')
        self._process_relatives(node_id, self.github.get_user_repositories_contributed_to(uri, self.relatives_limit),
                                'repository', 'contributed-to')
        self._process_relatives(node_id, self.github.get_user_watching(uri, self.relatives_limit),
                                'repository', 'watches')

        self._mark_processed(node_id)

    def _process_do_nothing(self, uri:str):
        node_id = self._get_node_id(uri)
        self._mark_processed(node_id)

    def load_repository(self, ghid_or_url):
        return self._merge_node('repository', self.github.get_repository(ghid_or_url)).id().next()

    def has_unprocessed(self):
        return self.g.V().has(TIME_PROCESSED, 0.0).hasNext()

    def process(self, change_limit, quiet=False, repos_first=True, skip_errors=True, token_checking_number=10):
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

        if repos_first:
            repo_nodes = self.g.V().has(TIME_PROCESSED, 0.0).has(TIME_CREATED, P.lte(start)).hasLabel('repository')
            other_nodes = self.g.V().has(TIME_PROCESSED, 0.0).has(TIME_CREATED, P.lte(start)).not_(__.hasLabel('repository'))
            if skip_errors:
                repo_nodes = repo_nodes.hasNot('_error')
                other_nodes = other_nodes.hasNot('_error')
            nodes = chain(repo_nodes, other_nodes)
        else:
            nodes = self.g.V().has(TIME_PROCESSED, 0.0).has(TIME_CREATED, P.lte(start))
            if skip_errors:
                nodes = nodes.hasNot('_error')

        for n, node in enumerate(tqdm(nodes, total=nodes_count, unit='node', disable=quiet)):
            label = self.g.V(node).label().next()
            uri = self.g.V(node).properties(URI).value().next()

            if n % token_checking_number == 0:
                self.github.adjust_token(self.tokens, quiet, change_limit=change_limit)

            try:
                processors[label](uri)
            except Exception as e:
                logging.exception(e)
                self.g.V(node)\
                    .property(ERROR, str(e))\
                    .property(ERROR_TRACE, traceback.format_exc())\
                    .iterate()
