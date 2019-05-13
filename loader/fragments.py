"""All github fragments."""

REPOSITORY =  """
fragment RepositoryFragment on Repository {
    id
    name
    description
    createdAt
    diskUsage
    forkCount
    squashMergeAllowed
    pushedAt
    isArchived
    isDisabled
    isFork
    isLocked
    isMirror
    isPrivate
    url
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
    createdAt
    description
    id
    isDraft
    isPrerelease
    name
    publishedAt
    url
    updatedAt
}
"""

ISSUE = """
fragment IssueFragment on Issue {
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
    bodyText
    changedFiles
    mergeable
    mergedAt
    merged
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
