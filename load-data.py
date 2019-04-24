#!/usr/bin/env python

"""Script for downloading repositories from GitHub nad loading them into JanusGraph."""

import argparse

from gremlin_python.structure.graph import Graph
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection

from loader.github import GitHub
from loader.spider import Spider

DB_URL = 'ws://localhost:8182/gremlin'


def main(args):
    # TODO quiet + logging

    graph = Graph()
    g = graph.traversal().withRemote(DriverRemoteConnection(DB_URL,'g'))

    github = GitHub(args.token)
    spider = Spider(g, github, args.relatives_cap)

    print(github.get_rate_limit())

    spider.load_repository("https://github.com/tensorflow/tensorflow")

    # TODO loop (this is just a single iteration)
    while spider.has_unprocessed():
        spider.process()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db-url', type=str, default=DB_URL)
    parser.add_argument('--quiet', action='store_true')
    parser.add_argument('--relatives-cap', type=int, default=128)
    parser.add_argument('token', type=str, help="See https://help.github.com/en/articles/creating-a-personal-access-token-for-the-command-line.")
    main(parser.parse_args())
