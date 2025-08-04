# pylint: disable=W0212
import json
from datetime import datetime, timedelta
from unittest import TestCase

from argus.tasks.base.notifier import TelegramNotifier
from argus.tasks.base.serializable import JsonDict
from argus.tasks.ml.hugging_face import (
    HuggingFaceTrendingModelsTask,
)
from argus.tasks.product import (
    PriceDiscountsTask,
    PriceFetcher,
    ProductPrice,
    ProductPrices,
)
from argus.tasks.todo import Todo, TodoFormatter, TodoTask


class TestDataSerialization(TestCase):
    def test_todo(self) -> None:
        date = datetime.now()
        data = Todo(title='Test Todo', target_date=date)
        self.assertEqual(data, Todo.from_dict(json.loads(json.dumps(data.to_dict()))))

    def test_product(self) -> None:
        data = ProductPrices(
            [
                ProductPrice(
                    name='test',
                    price=1.23,
                    url='www.example.com',
                    discount=0.1,
                    vendor='vendor',
                )
            ]
        )
        self.assertEqual(data, ProductPrices.from_dict(data.to_dict()))


class MockPriceFetcher(PriceFetcher):
    def __init__(self, url: str, price: float) -> None:
        super().__init__(url)
        self.price = price

    def fetch(self) -> ProductPrice:
        return ProductPrice(name='', price=self.price, url=self.url, vendor='')

    def to_dict(self) -> JsonDict:
        return super().to_dict() | {'price': self.price}


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

    def test_product_discount_serialization(self) -> None:
        task = PriceDiscountsTask(fetchers=[MockPriceFetcher('www.example.com', 1.23)])
        deserialized_task = PriceDiscountsTask.from_dict(task.to_dict())
        self.assertEqual(task.fetchers[0].url, deserialized_task.fetchers[0].url)
