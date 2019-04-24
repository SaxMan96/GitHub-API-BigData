"""GitHub graph clawrer."""

import time
from itertools import islice

from gremlin_python.process.graph_traversal import GraphTraversal, __
from gremlin_python.process.traversal import P, Order

from loader.github import GitHub


URI = '_uri'
TIME_CREATED = '_created'
TIME_PROCESSED = '_processed'


class Spider:

    def __init__(self, g:GraphTraversal, github:GitHub, relatives_cap):
        super().__init__()
        self.github = github
        self.g = g
        self.relatives_cap = relatives_cap

    def _get_or_create_node(self, label:str, uri:str):
        return self.g.V().hasLabel(label).has(URI, uri).fold().coalesce(
            __.unfold(),
            __.addV(label)
        )

    def _get_or_create_edge(self, label:str, start:int, end:int):
        return self.g.V(start).outE(label).filter(__.inV().hasId(end)).fold().coalesce(
            __.unfold(),
            self.g.V(start).addE(label).to(self.g.V(end))
        )

    def _get_node_id(self, uri:str):
        nodes = self.g.V().has(URI, uri).id().toList()
        assert len(nodes) <= 1

        if nodes:
            return nodes[0]
        return None

    def _add_properties(self, vertex, properties):
        if properties is not None:
            for key, value in properties.items():
                if value is not None:
                    vertex = vertex.property(key, value)
        return vertex

    def _merge_node(self, label:str, properties: dict):
        assert URI not in properties
        assert 'id' in properties

        uri = properties.pop('id')

        assert self.g.V().has(URI, uri).count().next() <= 1
        vertex = self._get_or_create_node(label, uri)

        vertex.property(URI, uri)
        vertex.property(TIME_CREATED, time.time())
        vertex = self._add_properties(vertex, properties)

        return vertex.id().next()

    def _has_edge(self, label:str, start:int, end:int):
        return self.g.V(start).outE(label).filter(__.inV().hasId(end)).hasNext()

    def _add_edge(self, label:str, start:int, end:int, properties=None):
        edge = self._get_or_create_edge(label, start, end)
        edge = self._add_properties(edge, properties)
        return edge.id().next()

    def _mark_processed(self, node_id:int):
        self.g.V(node_id).property(TIME_PROCESSED, time.time()).next()

    def load_repository(self, ghid_or_url):
        return self._merge_node('repository', self.github.get_repository(ghid_or_url))

    def _process_relatives(self, parent_id, relatives, label, edge):
        for relative in islice(relatives, self.relatives_cap):
            if 'node' in relative:
                edge_props = relative
                relative = relative.pop('node')
            else:
                edge_props = None
            relative_id = self._merge_node(label, relative)
            t = self._add_edge(edge, parent_id, relative_id, edge_props)

    def _process_repository(self, uri:str):
        node_id = self._get_node_id(uri)

        # TODO remove limit
        # TODO get ancestors (OG fork)
        # self._process_relatives(node_id, islice(self.github.get_repository_forks(uri), 3), 'repository', 'fork')
        self._process_relatives(node_id, self.github.get_repository_assignable_users(uri), 'user', 'assignable')
        # self._process_relatives(node_id, self.github.get_repository_collaborators(uri), 'user', 'collaborates')
        self._process_relatives(node_id, self.github.get_repository_stargazers(uri), 'user', 'stargazer')

        self._process_relatives(node_id, self.github.get_repository_commit_comments(uri), 'commit-comment', 'describes')
        self._process_relatives(node_id, self.github.get_repository_releases(uri), 'release', 'describes')
        self._process_relatives(node_id, self.github.get_repository_releases(uri), 'issue', 'describes')
        self._process_relatives(node_id, self.github.get_repository_milestones(uri), 'milestone', 'describes')
        self._process_relatives(node_id, self.github.get_repository_pull_requests(uri), 'pull', 'describes')

        self._process_relatives(node_id, self.github.get_repository_languages(uri), 'language', 'uses')

        self._mark_processed(node_id)

    def _process_user(self, uri:str):
        node_id = self._get_node_id(uri)

        self._process_relatives(node_id, self.github.get_user_followers(uri), 'user', 'follower')
        self._process_relatives(node_id, self.github.get_user_following(uri), 'user', 'follows')
        self._process_relatives(node_id, self.github.get_user_commit_comments(uri), 'commit-comment', 'wrote')
        self._process_relatives(node_id, self.github.get_user_issues(uri), 'issue', 'wrote')
        # self._process_relatives(node_id, self.github.get_user_pull_requests(uri), 'pull', 'created')
        self._process_relatives(node_id, self.github.get_user_repositories(uri), 'repository', 'created')
        self._process_relatives(node_id, self.github.get_user_repositories_contributed_to(uri), 'repository', 'contributed-to')
        self._process_relatives(node_id, self.github.get_user_watching(uri), 'repository', 'watches')

        self._mark_processed(node_id)

    def _process_do_nothing(self, uri:str):
        node_id = self._get_node_id(uri)
        self._mark_processed(node_id)

    def has_unprocessed(self):
        return self.g.V().hasNot(TIME_PROCESSED).hasNext()

    def process(self):
        start = time.time()
        nodes_count = self.g.V().hasNot(TIME_PROCESSED).has(TIME_CREATED, P.lte(start)).count().next()
        print('Starting iteration at {} with {}/{} nodes to process.'.format(start, nodes_count, self.g.V().count().next()))

        processors = {
            'repository': self._process_repository,
            'user': self._process_user,
            'language': self._process_do_nothing,
            'commit-comment': self._process_do_nothing,
            'release': self._process_do_nothing,
            'issue': self._process_do_nothing,
            'pull': self._process_do_nothing,
        }

        for node in self.g.V().hasNot(TIME_PROCESSED).has(TIME_CREATED, P.lte(start)).order().by(Order.shuffle):
            label = self.g.V(node).label().next()
            uri = self.g.V(node).properties(URI).value().next()
            processors[label](uri)
