import pandas as pd
from gremlin_python.process.graph_traversal import GraphTraversal
from gremlin_python.process.traversal import P

UNCLOSED_ISSUES = 'unclosed_issues'
CLOSED = 'closed'
CONTAINS = 'contains'

REPOSITORY = 'repository'
TIME_PROCESSED = '_processed'
USES = 'uses'
NAME = 'name'
SIZE = 'size'


class Stats:
    def __init__(self, g: GraphTraversal):
        super().__init__()
        self.g = g
        self.df = self._create_main_dataframe()

    def _create_main_dataframe(self):
        repo_id = self.g.V().has(TIME_PROCESSED, P.gt(0.0)).hasLabel(REPOSITORY).id().next()
        return pd.DataFrame(columns=self.g.V(repo_id).properties().label().toList())

    def create_train_set(self, filename):
        repo_ids = self.g.V().has(TIME_PROCESSED, P.gt(0.0)).hasLabel(REPOSITORY).id().toList()
        print(f"{len(repo_ids)} ids downloaded...")
        for i, repo_id in enumerate(repo_ids[:10]):
            self._create_repository_row(repo_id)
            print(f"Repository {i} with id {repo_id} added...")
        self._save(filename)

    def _create_repository_row(self, repo_id):
        added = self._create_basic_df(repo_id)
        added = pd.concat([added,
                           self._add_language_features(repo_id),
                           self._add_issue_features(repo_id)],
                          axis=1)
        self.df = pd.concat([self.df, added])

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
        sizes = [size / sum(sizes) for size in sizes]
        return pd.DataFrame([sizes], columns=labels)

    def _add_issue_features(self, repo_id):
        n_of_unclosed_issues = self.g.V(repo_id).inE().hasLabel(CONTAINS).outV().has(CLOSED, False).count().toList()
        return pd.DataFrame([n_of_unclosed_issues], columns=[UNCLOSED_ISSUES])

    def _save(self, filename):
        self.df.to_csv(filename)
