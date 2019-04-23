#!/usr/bin/env python

"""Script for downloading repositories from GitHub nad loading them into JanusGraph."""

import argparse

from pprint import pprint
from itertools import islice

from gremlin_python.process.graph_traversal import GraphTraversal
from gremlin_python.structure.graph import Graph
from gremlin_python.process.graph_traversal import __
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection

from loader.github import GitHub


DB_URL = 'ws://localhost:8182/gremlin'


def add_node(g:GraphTraversal, label:str, properties: dict):
    assert 'id' in properties
    assert g.V().has('id', properties['id']).count().next() <= 1

    if g.V().has('id', properties['id']).hasNext():
       return g.V().has('id', properties['id']).id().next()

    vertex = g.addV(label)
    for key, value in properties.items():
        vertex = vertex.property(key, value)
    return vertex.id().next()


def has_edge(g:GraphTraversal, label:str, start:int, end:int):
    return g.V(start).outE(label).filter(__.inV().hasId(end)).hasNext()


def add_edge(g:GraphTraversal, label:str, start:int, end:int):
    if not has_edge(g, label, start, end):
        return g.V(start).addE(label).to(g.V(end)).id().next()


def main(args):
    graph = Graph()
    g = graph.traversal().withRemote(DriverRemoteConnection(DB_URL,'g'))

    github = GitHub(args.token)

    # example rate limit:
    print(github.get_rate_limit())

    repo_id_or_url = "https://github.com/tensorflow/tensorflow"
    max_forks = 3

    # example repo download:
    repo_id = add_node(g, 'repository', github.get_repository(repo_id_or_url))

    # example forks download:
    for fork in islice(github.get_repository_forks(repo_id_or_url), max_forks):
        fork_id = add_node(g, 'repository', fork)
        add_edge(g, 'fork', repo_id, fork_id)

    print('vertexes')
    pprint(g.V().hasLabel('repository').valueMap().toList())

    print('edges')
    pprint(g.V().outE('fork').inV().valueMap().toList())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db-url', type=str, default=DB_URL)
    parser.add_argument('token', type=str, help="See https://help.github.com/en/articles/creating-a-personal-access-token-for-the-command-line.")
    main(parser.parse_args())
