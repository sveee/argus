# pylint: disable=W0212
import json
from datetime import datetime, timedelta
from unittest import TestCase

from peewee import SqliteDatabase

from argus.tasks.base.database import RunningTask, TaskResult
from argus.tasks.base.notifier import TelegramNotifier
from argus.tasks.ml.hugging_face import (
    HuggingFaceTrendingModelsTask,
    HuggingFaceTrendingPapersTask,
)
from argus.tasks.ml.paper_with_code import TrendingPapersWithCodeTask
from argus.tasks.todo import Todo, TodoFormatter, TodoTask


class TestDataFetchers(TestCase):
    def setUp(self):
        self.test_db = SqliteDatabase(':memory:')
        self.test_db.bind([TaskResult, RunningTask])
        self.test_db.connect()
        self.test_db.create_tables([TaskResult, RunningTask])

    def tearDown(self):
        self.test_db.drop_tables([TaskResult, RunningTask])
        self.test_db.close()

    def test_hugging_face_models(self):
        task = HuggingFaceTrendingModelsTask()
        task.run_if_due()
        self.assertEqual(len(TaskResult.select()), 1)

    def test_hugging_face_papers(self):
        task = HuggingFaceTrendingPapersTask()
        task.run_if_due()
        self.assertEqual(len(TaskResult.select()), 1)

    def test_papers_with_code(self):
        task = TrendingPapersWithCodeTask()
        task.run_if_due()
        self.assertEqual(len(TaskResult.select()), 1)


class TestDataSerialization(TestCase):
    def test_todo(self) -> None:
        date = datetime.now()
        data = Todo(title='Test Todo', target_date=date)
        self.assertEqual(data, Todo.from_dict(json.loads(json.dumps(data.to_dict()))))


class TestTaskSerialization(TestCase):
    def test_todo_serialization(self) -> None:
        date = datetime.now()
        task = TodoTask(
            target_date=date,
            title='Test Todo',
            remind_in=[timedelta(seconds=15)],
            formatter=TodoFormatter(),
            notifier=TelegramNotifier('test_token', ['chat_id1', 'chat_id2']),
        )
        deserialized_task: TodoTask = TodoTask.from_dict(task.to_dict())
        self.assertEqual(task._target_date, deserialized_task._target_date)
        self.assertEqual(task._title, deserialized_task._title)

    def test_huggingface_models_serialization(self) -> None:
        task = HuggingFaceTrendingModelsTask(
            formatter=TodoFormatter(),
            notifier=TelegramNotifier('test_token', ['chat_id1', 'chat_id2']),
        )
        deserialized_task = HuggingFaceTrendingModelsTask.from_dict(task.to_dict())
        self.assertTrue(isinstance(deserialized_task._formatter, TodoFormatter))
        self.assertTrue(isinstance(deserialized_task._notifier, TelegramNotifier))
