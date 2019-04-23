#!/usr/bin/env python

"""Script for downloading repositories from GitHub nad loading them into JanusGraph."""

import time
import logging
import argparse

from pprint import pprint
from itertools import islice

from gremlin_python.process.graph_traversal import GraphTraversal
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import P, Order
from gremlin_python.structure.graph import Graph
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection

from loader.github import GitHub


DB_URL = 'ws://localhost:8182/gremlin'


class Spider:

    def __init__(self, g:GraphTraversal, github:GitHub):
        super().__init__()
        self.github = github
        self.g = g

    def _get_or_create_node(self, label:str, uri:str):
        return self.g.V().hasLabel(label).has('uri', uri).fold().coalesce(
            __.unfold(),
            __.addV(label)
        )

    def _get_node_id(self, uri:str):
        nodes = self.g.V().has('uri', uri).id().toList()
        assert len(nodes) <= 1

        if nodes:
            return nodes[0]
        return None

    def _add_node(self, label:str, properties: dict):
        assert 'uri' not in properties
        assert 'id' in properties

        uri = properties.pop('id')

        assert self.g.V().has('uri', uri).count().next() <= 1
        vertex = self._get_or_create_node(label, uri)

        vertex.property('uri', uri)
        vertex.property('created', time.time())
        for key, value in properties.items():
            vertex = vertex.property(key, value)

        return vertex.id().next()

    def _has_edge(self, label:str, start:int, end:int):
        return self.g.V(start).outE(label).filter(__.inV().hasId(end)).hasNext()

    def _add_edge(self, label:str, start:int, end:int):
        if not self._has_edge(label, start, end):
            return self.g.V(start).addE(label).to(self.g.V(end)).id().next()

    def _mark_processed(self, node_id:int):
        self.g.V(node_id).property('processed', time.time()).next()

    def load_repository(self, ghid_or_url):
        return self._add_node('repository', self.github.get_repository(ghid_or_url))

    def process_repository(self, uri:str):
        repo_id = self._get_node_id(uri)

        # TODO remove limit
        for fork in islice(self.github.get_repository_forks(uri), 3):
            fork_id = self._add_node('repository', fork)
            self._add_edge('fork', repo_id, fork_id)

        self._mark_processed(repo_id)

    def process(self):
        start = time.time()
        nodes_count = self.g.V().hasNot('processed').has('created', P.lte(start)).count().next()
        print('Starting iteration at {} with {} nodes to process.'.format(start, nodes_count))

        processors = {
            'repository': self.process_repository
        }

        for node in self.g.V().hasNot('processed').has('created', P.lte(start)).order().by(Order.shuffle):
            label = self.g.V(node).label().next()
            uri = self.g.V(node).uri.next()
            processors[label](uri)


def main(args):
    # TODO quiet + logging

    graph = Graph()
    g = graph.traversal().withRemote(DriverRemoteConnection(DB_URL,'g'))

    github = GitHub(args.token)
    spider = Spider(g, github)

    # example rate limit:
    print(github.get_rate_limit())

    repo_id_or_url = "https://github.com/tensorflow/tensorflow"

    repo_id = spider.load_repository(repo_id_or_url)
    # repo_uri = g.V(repo_id).properties('uri').value().next()
    # spider.process_repository(repo_uri)

    spider.process()

    print('vertexes')
    pprint(g.V().hasLabel('repository').valueMap().toList())

    print('edges')
    pprint(g.V().outE('fork').inV().valueMap().toList())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db-url', type=str, default=DB_URL)
    parser.add_argument('--quiet', action='store_true')
    parser.add_argument('token', type=str, help="See https://help.github.com/en/articles/creating-a-personal-access-token-for-the-command-line.")
    main(parser.parse_args())
