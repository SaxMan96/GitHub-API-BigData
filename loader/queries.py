"""All github queries."""


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
