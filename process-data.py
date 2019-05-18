import argparse

from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.structure.graph import Graph

from preparator.stats import Stats

DB_URL = 'ws://localhost:8182/gremlin'
RESULT_FILENAME = './result.csv'
MARIA_DEV = 'maria_dev'


def main(args):
    graph = Graph()
    g = graph.traversal().withRemote(DriverRemoteConnection(DB_URL, 'g'))
    stats = Stats(g)
    stats.create_train_set(args.o, args.username)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db-url', type=str, default=DB_URL)
    parser.add_argument('--o', type=str, default=RESULT_FILENAME)
    parser.add_argument('--username', type=str, default=MARIA_DEV)
    main(parser.parse_args())
