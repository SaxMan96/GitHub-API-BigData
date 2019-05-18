import os
from subprocess import Popen, PIPE

import pandas as pd
from gremlin_python.process.graph_traversal import GraphTraversal
from gremlin_python.process.traversal import P
from tqdm import tqdm

# hadoop
HADOOP = "hadoop"
USER = "user"

# gremlin
WATCHES = 'watches'
WROTE = 'wrote'
FOLLOWS = 'follows'
CREATED = 'created'
CONTRIBUTED_TO = 'contributed-to'

IS_PRERELEASE = 'isPrerelease'
IS_DRAFT = 'isDraft'
RELEASE = 'release'

MILESTONE = "milestone"
STARGAZER_PREFIX = 'stargazer_'
STARGAZER = 'stargazer'
COMPANY = 'company'

BIO = "bio"
ASSIGNABLE_PREFIX = 'assign_'
ASSIGNABLE = "assignable"

UNCLOSED_ISSUES = 'unclosed_issues'
CLOSED = 'closed'
CONTAINS = 'contains'

REPOSITORY = 'repository'
TIME_PROCESSED = '_processed'
USES = 'uses'
NAME = 'name'
SIZE = 'size'
UNDERSCORE = '_'


class Stats:
    def __init__(self, g: GraphTraversal):
        super().__init__()
        self.g = g
        self.df = self._create_main_dataframe()

    def _create_main_dataframe(self):
        repo_id = self.g.V().has(TIME_PROCESSED, P.gt(0.0)).hasLabel(REPOSITORY).id().next()

        return pd.DataFrame(columns=self.g.V(repo_id).properties().label().toList())

    def create_train_set(self, filename, username, quiet=False):
        repo_ids = self.g.V().has(TIME_PROCESSED, P.gt(0.0)).hasLabel(REPOSITORY).id().toList()

        print(f"{len(repo_ids)} ids downloaded...")

        for repo_id in tqdm(repo_ids, total=len(repo_ids), unit='repository', disable=quiet):
            self._create_repository_row(repo_id)
        self._save(filename, username)

    def _create_repository_row(self, repo_id):
        added = self._create_basic_df(repo_id)

        added = pd.concat([added,
                           self._add_language_features(repo_id),
                           self._add_issue_features(repo_id),
                           self._add_assignable_features(repo_id),
                           self._add_stargazer_features(repo_id),
                           self._add_milestone_features(repo_id),
                           self._add_release_features(repo_id),
                           self._add_contributors_features(repo_id)],
                          axis=1,
                          sort=False)

        self.df = pd.concat([self.df, added], sort=False)

    def _create_basic_df(self, repo_id):
        properties = self.g.V(repo_id).properties().toList()

        labels = [p.label for p in properties]
        values = [p.value for p in properties]

        return pd.DataFrame([values], columns=labels)

    def _add_language_features(self, repo_id):
        # TODO: convert to map
        languages = self.g.V(repo_id).inE().hasLabel(USES).outV().path().by(NAME).by(SIZE).by(NAME).toList()

        labels = [language[2] for language in languages]
        sizes = [language[1] for language in languages]

        if sum(sizes) > 0:
            sizes = [size / sum(sizes) for size in sizes]
        else:
            sizes = [0] * len(sizes)

        return pd.DataFrame([sizes], columns=labels)

    def _add_issue_features(self, repo_id):
        n_of_unclosed_issues = self.g.V(repo_id).inE().hasLabel(CONTAINS).outV().has(CLOSED, False).count().toList()

        return pd.DataFrame([n_of_unclosed_issues], columns=[UNCLOSED_ISSUES])

    def _add_assignable_features(self, repo_id):
        number = self.g.V(repo_id).inE().hasLabel(ASSIGNABLE).count().next()
        bio_number = self.g.V(repo_id).inE().hasLabel(ASSIGNABLE).has(BIO).count().next()
        company_number = self.g.V(repo_id).inE().hasLabel(ASSIGNABLE).has(COMPANY).count().next()

        values = [number, bio_number, company_number]
        labels = [ASSIGNABLE_PREFIX, ASSIGNABLE_PREFIX + BIO, ASSIGNABLE_PREFIX + COMPANY]

        return pd.DataFrame([values], columns=labels)

    def _add_stargazer_features(self, repo_id):
        number = self.g.V(repo_id).inE().hasLabel(STARGAZER).count().next()
        bio_number = self.g.V(repo_id).inE().hasLabel(STARGAZER).has(BIO).count().next()
        company_number = self.g.V(repo_id).inE().hasLabel(STARGAZER).has(COMPANY).count().next()

        values = [number, bio_number, company_number]
        labels = [STARGAZER_PREFIX, STARGAZER_PREFIX + BIO, STARGAZER_PREFIX + COMPANY]

        return pd.DataFrame([values], columns=labels)

    def _add_milestone_features(self, repo_id):
        ms_number = self.g.V(repo_id).inE().outV().hasLabel(MILESTONE).count().next()
        closed_ms = self.g.V(repo_id).inE().outV().hasLabel(MILESTONE).has(CLOSED, True).count().next()

        values = [ms_number, closed_ms]
        labels = [MILESTONE, MILESTONE + UNDERSCORE + CLOSED]

        return pd.DataFrame([values], columns=labels)

    def _add_release_features(self, repo_id):
        release_number = self.g.V(repo_id).inE().outV().hasLabel(RELEASE).count().next()
        draft_number = self.g.V(repo_id).inE().outV().hasLabel(RELEASE).has(IS_DRAFT, True).count().next()
        prerelease_number = self.g.V(repo_id).inE().outV().hasLabel(RELEASE).has(IS_PRERELEASE, True).count().next()

        values = [release_number, draft_number, prerelease_number]
        labels = [RELEASE + UNDERSCORE, RELEASE + UNDERSCORE + IS_DRAFT, RELEASE + UNDERSCORE + IS_PRERELEASE]

        return pd.DataFrame([values], columns=labels)

    def _add_contributors_features(self, repo_id):

        number = self.g.V(repo_id).outE().hasLabel(CONTRIBUTED_TO).count().next()
        bio_number = self.g.V(repo_id).outE().hasLabel(CONTRIBUTED_TO).inV().has(BIO).count().next()
        company_number = self.g.V(repo_id).outE().hasLabel(CONTRIBUTED_TO).inV().has(COMPANY).count().next()
        creations = self.g.V(repo_id).outE().hasLabel(CONTRIBUTED_TO).inV().inE().hasLabel(CREATED).count().next()
        followers = self.g.V(repo_id).outE().hasLabel(CONTRIBUTED_TO).inV().inE().hasLabel(FOLLOWS).count().next()
        wrotes = self.g.V(repo_id).outE().hasLabel(CONTRIBUTED_TO).inV().inE().hasLabel(WROTE).count().next()
        watchers = self.g.V(repo_id).outE().hasLabel(CONTRIBUTED_TO).inV().inE().hasLabel(WATCHES).count().next()

        values = [number, bio_number, company_number, creations, followers, wrotes, watchers]
        labels = [CONTRIBUTED_TO,
                  CONTRIBUTED_TO + UNDERSCORE + BIO,
                  CONTRIBUTED_TO + UNDERSCORE + COMPANY,
                  CONTRIBUTED_TO + UNDERSCORE + CREATED,
                  CONTRIBUTED_TO + UNDERSCORE + FOLLOWS,
                  CONTRIBUTED_TO + UNDERSCORE + WROTE,
                  CONTRIBUTED_TO + UNDERSCORE + WATCHES]

        return pd.DataFrame([values], columns=labels)

    def _save(self, filename, username):
        self.df.to_csv(filename)
        hdfs_path = os.path.join(os.sep, USER, username, filename)
        put = Popen([HADOOP, "fs", "-put", filename, hdfs_path], stdin=PIPE, bufsize=-1)
        put.communicate()
