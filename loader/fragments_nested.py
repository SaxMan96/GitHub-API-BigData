"""All github fragments."""

REPOSITORY =  """
fragment RepositoryFragment on Repository {
    id
    name
    description
    codeOfConduct {
        id
    }
    createdAt
    diskUsage
    forkCount
    isArchived
    isDisabled
    isFork
    isLocked
    isMirror
    isPrivate
    url
    licenseInfo{
        id
        body
        description
        featured
        nickname
        permissions{
            description
            label
        }
    }
}
"""

LANGUAGE =  """
fragment LanguageFragment on Language{
    id
    name
}
"""

USER =  """
fragment UserFragment on User {
    id
    name
    login
    bio
    company
    createdAt
    isBountyHunter
    isCampusExpert
    isDeveloperProgramMember
    isEmployee
    isHireable
    isSiteAdmin
    isViewer
    location
    status {
      id,
      message
    }
    updatedAt
    url
    viewerCanCreateProjects
    viewerCanFollow
    viewerIsFollowing
}
"""

COMMIT_COMMENT =  """
fragment CommitCommentFragment on CommitComment {
    id  
    authorAssociation
    bodyText
    createdAt
    url
}
"""

RELEASE =  """
fragment ReleaseFragment on Release {
    author{
        login
    }
    createdAt
    description
    id
    isDraft
    isPrerelease
    name
    publishedAt
    tag
    url
    updatedAt
}
"""

ISSUE = """
fragment IssueFragment on Issue {
    author{
        login
    }
    bodyText
    closed
    closedAt
    createdViaEmail
    id
    locked
    number
    publishedAt
    state
    title
    updatedAt
    url
}
"""

MILESTONES =  """
fragment MilestonesFragment on Milestone {
    description
    dueOn
    closed
    closedAt
    id
    number
    state
    title
    updatedAt
    url
}
"""

PULL_REQUEST =  """
fragment PullRequestFragment on PullRequest {
    additions
    author{
        login
    }
    bodyText
    changedFiles
    mergeable
    mergedAt
    merged
    milestone{
        id
    }
    permalink
    closed
    closedAt
    id
    number
    state
    title
    updatedAt
    url
}
"""

REPOSITORY_DESCRIPTION = """
query {
    $selector {
        ... RepositoryFragment
    }
}	
"""
