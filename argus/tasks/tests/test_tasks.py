from unittest import TestCase

from argus.tasks.ml.hugging_face import (
    HuggingFaceTrendingModels,
    HuggingFaceTrendingPapers,
)


class TestDataFetchers(TestCase):

    def test_hugging_face_models(self):
        fetcher = HuggingFaceTrendingModels(store_to_db=False)
        models = fetcher.run()
        self.assertGreater(len(models), 0)

    def test_hugging_face_papers(self):
        fetcher = HuggingFaceTrendingPapers(store_to_db=False)
        papers = fetcher.run()
        self.assertGreater(len(papers), 0)
