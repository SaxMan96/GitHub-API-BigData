"""GitHub API connector"""

import re
import requests

from loader import queries


DEFAULT_ENDPOINT = 'https://api.github.com/graphql'

TMPL_URL_QUERY = """
    query {{
        resource(url: "{url}") {{
            {query}
        }}
    }}
"""

TMPL_ID_QUERY = """
    query {{
        node(id: "{id}") {{
            {query}
        }}
    }}
"""


def _is_id(id_or_url):
    return re.match(r'^[A-Za-z0-9+/]*={0,2}$', id_or_url)


def _format_query(id_or_url, query):
    if _is_id(id_or_url):
        return TMPL_ID_QUERY.format(id=id_or_url, query=query)
    else:
        return TMPL_URL_QUERY.format(url=id_or_url, query=query)


class Connection:

    def __init__(self, token, endpoint=None):
        super().__init__()
        self.endpoint = endpoint or DEFAULT_ENDPOINT
        self.token = token

    def query(self, query, ignore_error=False):
        headers = {'Authorization': 'bearer {}'.format(self.token)}

        response = requests.post(self.endpoint, json={'query': query}, headers=headers)

        if not ignore_error:
            response.raise_for_status()
        return response

    def get(self, id_or_url, query):
        data = self.query(_format_query(id_or_url, query)).json()['data']
        if _is_id(id_or_url):
            return data['node']
        else:
            return data['resource']


def paginated(method):
    def node_generator(self, id_or_url):
        cursor = 'null'
        has_next = True
        while has_next:
            results, cursor, has_next = method(self, id_or_url, cursor)
            for result in results:
                yield result
    return node_generator


class GitHub:

    def __init__(self, token, endpoint=None):
        super().__init__()
        self.connection = Connection(token, endpoint)

    def get_rate_limit(self):
        return self.connection.query("""
        query {
            rateLimit {
                limit
                cost
                remaining
                resetAt
            }
        }
        """).json()['data']['rateLimit']

    def get_repository(self, id_or_url):
        return self.connection.get(id_or_url, queries.REPOSITORY)

    @paginated
    def get_repository_forks(self, id_or_url, cursor):
        res = self.connection.get(id_or_url, queries.REPOSITORY_FORKS.format(after=cursor))
        results = res['forks']['nodes']
        cursor = res['forks']['pageInfo']['endCursor']
        has_next = res['forks']['pageInfo']['hasNextPage']
        return results, cursor, has_next
