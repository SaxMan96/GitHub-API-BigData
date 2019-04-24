"""All github queries."""


from loader import fragments


REPOSITORY = """
query {
    $selector {
        ... RepositoryFragment
    }
}
""" + fragments.REPOSITORY

REPOSITORY_FORKS = """
query {
    $selector {
        ... on Repository {
            forks(first: 100, after: $cursor) {
                nodes {
                    ... RepositoryFragment
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }
}		
""" + fragments.REPOSITORY

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

REPOSITORY_COLABORATORS = """
query {
    $selector {
        ... on Repository {
            collaborators(first: 100, after: $cursor) {
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

REPOSITORY_COMMIT_COMMENTS = """
query {
    $selector {
        ... on Repository {
            commitComments(first: 100, after: $cursor) {
                nodes {
                    ... CommitCommentFragment
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }
}
""" + fragments.COMMIT_COMMENT

REPOSITORY_STARGAZERS = """
query {
    $selector {
        ... on Repository {
            stargazers(first: 100, after: $cursor) {
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

REPOSITORY_RELEASES = """
query {
    $selector {
        ... on Repository {
            releases(first: 100, after: $cursor) {
                nodes {
                    ... ReleaseFragment
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }
}
""" + fragments.RELEASE

REPOSITORY_ISSUES = """
query {
    $selector {
        ... on Repository {
            issues(first: 100, after: $cursor) {
                nodes {
                    ... IssueFragment
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }
}
""" + fragments.ISSUE

REPOSITORY_MILESTONES = """
query {
    $selector {
        ... on Repository {
            milestones(first: 100, after: $cursor) {
                nodes {
                    ... MilestonesFragment
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }
}
""" + fragments.MILESTONES

REPOSITORY_PULL_REQUESTS = """
query {
    $selector {
        ... on Repository {
            pullRequests(first: 16, after: $cursor) {
                nodes {
                    ... PullRequestFragment
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }
}
""" + fragments.PULL_REQUEST

USER_COMMIT_COMMENTS = """
query {
    $selector {
        ... on User {
            commitComments(first: 100, after: $cursor) {
                nodes {
                    ... CommitCommentFragment
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }
}
""" + fragments.COMMIT_COMMENT

USER_FOLLOWERS = """
query {
    $selector {
        ... on User {
            followers(first: 100, after: $cursor) {
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

USER_FOLLOWING = """
query {
    $selector {
        ... on User {
            following(first: 100, after: $cursor) {
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

USER_ISSUES = """
query {
    $selector {
        ... on User {
            issues(first: 100, after: $cursor) {
                nodes {
                    ... IssueFragment
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }
}
""" + fragments.ISSUE

USER_PULL_REQUESTS = """
query {
    $selector {
        ... on User {
            pullRequests(first: 100, after: $cursor) {
                nodes {
                    ... PullRequestFragment
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }
}
""" + fragments.PULL_REQUEST

USER_REPOSITORIES = """
query {
    $selector {
        ... on User {
            repositories(first: 100, after: $cursor) {
                nodes {
                    ... RepositoryFragment
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }
}
""" + fragments.REPOSITORY

USER_REPOSITORIES_CONTRIBUTED_TO = """
query {
    $selector {
        ... on User {
            repositoriesContributedTo(first: 100, after: $cursor) {
                nodes {
                    ... RepositoryFragment
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }
}
""" + fragments.REPOSITORY

USER_WATCHING = """
query {
    $selector {
        ... on User {
            watching(first: 100, after: $cursor) {
                nodes {
                    ... RepositoryFragment
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }
}
""" + fragments.REPOSITORY
