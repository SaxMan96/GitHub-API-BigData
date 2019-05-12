"""GitHub API connector"""

import re
import logging
import requests

from pprint import pformat
from string import Template

import backoff

from loader import queries


DEFAULT_ENDPOINT = 'https://api.github.com/graphql'


def _is_id(id_or_url):
    return re.match(r'^[A-Za-z0-9+/]*={0,2}$', id_or_url)


def _on_backoff(details):
    logging.info(pformat(details['args'][1]))


class Connection:

    def __init__(self, token, endpoint=None):
        super().__init__()
        self.endpoint = endpoint or DEFAULT_ENDPOINT
        self.token = token

    @backoff.on_exception(backoff.fibo, requests.exceptions.HTTPError, on_backoff=_on_backoff)
    def query(self, query, ignore_error=False):
        headers = {'Authorization': 'bearer {}'.format(self.token)}

        response = requests.post(self.endpoint, json={'query': query}, headers=headers)

        if not ignore_error:
            response.raise_for_status()
        return response


def _selector(id_or_url):
    if _is_id(id_or_url):
        return 'node(id: "{}")'.format(id_or_url)
    else:
        return 'resource(url: "{}")'.format(id_or_url)


def _cursor(cursor):
    return 'null' if cursor is None else '"{}"'.format(cursor)


class GitHub:

    def __init__(self, token, endpoint=None):
        super().__init__()
        self.connection = Connection(token, endpoint)

    def _get(self, id_or_url, query):
        response = self.connection.query(query).json()

        if 'errors' in response:
            raise RuntimeError(response['errors'])

        data = response['data']
        if _is_id(id_or_url):
            return data['node']
        else:
            return data['resource']

    def _query_with_template(self, id_or_url, query_template, cursor, **kwargs):
        return self._get(id_or_url, Template(query_template) \
                .substitute(selector=_selector(id_or_url), cursor=_cursor(cursor), **kwargs))

    def __paginated(self, method, cursor=None):
        cursor = cursor
        has_next = True
        while has_next:
            nodes, cursor, has_next = method(cursor)
            for result in nodes:
                yield result

    def _paginated_nodes(self, id_or_url, query, field, **kwargs):
        def standard(cursor):
            output = self._query_with_template(id_or_url, query, cursor, **kwargs)
            nodes = output[field]['nodes']
            cursor = output[field]['pageInfo']['endCursor']
            has_next = output[field]['pageInfo']['hasNextPage']
            return nodes, cursor, has_next
        yield from self.__paginated(standard)

    def _paginated_edges(self, id_or_url, query, field, **kwargs):
        def standard(cursor):
            output = self._query_with_template(id_or_url, query, cursor, **kwargs)
            edges = output[field]['edges']
            cursor = output[field]['pageInfo']['endCursor']
            has_next = output[field]['pageInfo']['hasNextPage']
            return edges, cursor, has_next
        yield from self.__paginated(standard)

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
        return self._get(id_or_url, Template(queries.REPOSITORY).substitute(selector=_selector(id_or_url)))

    def get_repository_forks(self, id_or_url):
        yield from self._paginated_nodes(id_or_url, queries.REPOSITORY_FORKS, 'forks')

    def get_repository_languages(self, id_or_url):
        yield from self._paginated_edges(id_or_url, queries.REPOSITORY_LANGUAGES, 'languages')

    def get_repository_assignable_users(self, id_or_url):
        yield from self._paginated_nodes(id_or_url, queries.REPOSITORY_ASSIGNABLE_USERS, 'assignableUsers')

    def get_repository_collaborators(self, id_or_url):
        yield from self._paginated_nodes(id_or_url, queries.REPOSITORY_COLABORATORS, 'collaborators')

    def get_repository_stargazers(self, id_or_url):
        yield from self._paginated_nodes(id_or_url, queries.REPOSITORY_STARGAZERS, 'stargazers')

    def get_repository_commit_comments(self, id_or_url):
        yield from self._paginated_nodes(id_or_url, queries.REPOSITORY_COMMIT_COMMENTS, 'commitComments')

    def get_repository_releases(self, id_or_url):
        yield from self._paginated_nodes(id_or_url, queries.REPOSITORY_RELEASES, 'releases')

    def get_repository_issues(self, id_or_url):
        yield from self._paginated_nodes(id_or_url, queries.REPOSITORY_ISSUES, 'issues')

    def get_repository_milestones(self, id_or_url):
        yield from self._paginated_nodes(id_or_url, queries.REPOSITORY_MILESTONES, 'milestones')

    def get_repository_pull_requests(self, id_or_url):
        yield from self._paginated_nodes(id_or_url, queries.REPOSITORY_PULL_REQUESTS, 'pullRequests')

    def get_user_followers(self, id_or_url):
        yield from self._paginated_nodes(id_or_url, queries.USER_FOLLOWERS, 'followers')

    def get_user_following(self, id_or_url):
        yield from self._paginated_nodes(id_or_url, queries.USER_FOLLOWING, 'following')

    def get_user_commit_comments(self, id_or_url):
        yield from self._paginated_nodes(id_or_url, queries.USER_COMMIT_COMMENTS, 'commitComments')

    def get_user_issues(self, id_or_url):
        yield from self._paginated_nodes(id_or_url, queries.USER_ISSUES, 'issues')

    def get_user_pull_requests(self, id_or_url):
        yield from self._paginated_nodes(id_or_url, queries.USER_PULL_REQUESTS, 'pullRequests')

    def get_user_repositories(self, id_or_url):
        yield from self._paginated_nodes(id_or_url, queries.USER_REPOSITORIES, 'repositories')

    def get_user_repositories_contributed_to(self, id_or_url):
        yield from self._paginated_nodes(id_or_url, queries.USER_REPOSITORIES_CONTRIBUTED_TO, 'repositoriesContributedTo')

    def get_user_watching(self, id_or_url):
        yield from self._paginated_nodes(id_or_url, queries.USER_WATCHING, 'watching')
