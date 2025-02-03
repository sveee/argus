# pylint: disable=W0212
from datetime import datetime, timedelta
from unittest import TestCase

from argus.tasks.base.notifier import TelegamNotifier
from argus.tasks.ml.hugging_face import (
    HuggingFaceTrendingModelsTask,
    HuggingFaceTrendingPapersTask,
)
from argus.tasks.ml.paper_with_code import TrendingPapersWithCodeTask
from argus.tasks.todo import TodoFormatter, TodoTask


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


class TestSerialization(TestCase):

    def test_todo_serialization(self) -> None:
        date = datetime.now()
        task = TodoTask(
            target_date=date,
            title='Test Todo',
            remind_in=[timedelta(seconds=15)],
            formatter=TodoFormatter(),
            notifier=TelegamNotifier('test_token', ['chat_id1', 'chat_id2']),
        )
        deserialized_task: TodoTask = TodoTask.from_dict(task.to_dict())
        self.assertEqual(task._target_date, deserialized_task._target_date)
        self.assertEqual(task._title, deserialized_task._title)
        self.assertEqual(task._remind_in, deserialized_task._remind_in)
