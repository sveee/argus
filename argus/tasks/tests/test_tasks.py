from unittest import TestCase

from argus.tasks.ml.hugging_face import (
    HuggingFaceTrendingModelsTask,
    HuggingFaceTrendingPapersTask,
)
from argus.tasks.ml.paper_with_code import TrendingPapersWithCodeTask


class TestDataFetchers(TestCase):

    def test_hugging_face_models(self):
        task = HuggingFaceTrendingModelsTask(store_to_db=False)
        models = task.run()
        self.assertGreater(len(models), 0)

    def test_hugging_face_papers(self):
        task = HuggingFaceTrendingPapersTask(store_to_db=False)
        papers = task.run()
        self.assertGreater(len(papers), 0)

    def test_papers_with_code(self):
        task = TrendingPapersWithCodeTask(store_to_db=False)
        papers = task.run()
        self.assertGreater(len(papers), 0)
