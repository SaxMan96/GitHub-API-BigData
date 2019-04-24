"""All github queries."""


from loader import fragments


REPOSITORY = """
    ... on Repository {
        id
        description
    }
"""

REPOSITORY_FORKS = """
    ... on Repository {{
        id
        forks(first: 100, after: {after}) {{
            nodes {{
                ... on Repository {{
                    id
                    description
                }}
            }}
            pageInfo {{
                endCursor
                hasNextPage
            }}
        }}
    }}
"""

REPOSITORY_LANGUAGES = """
query {
    $selector {
        ... on Repository {
            languages(first:100, after: $cursor) {
                edges {
                    size
                    node {
                        ... LanguageFragment
                    }
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }
}
""" + fragments.LANGUAGE

REPOSITORY_ASSIGNABLE_USERS = """
query {
    $selector {
        ... on Repository {
            assignableUsers(first: 100, after: $cursor) {
                nodes {
                    ... UserFragment
                }
                 pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }
}
""" + fragments.USER
