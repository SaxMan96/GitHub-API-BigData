"""All github fragments."""

USER = """
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

LANGUAGE = """
fragment LanguageFragment on Language{
    id
    name
}
"""