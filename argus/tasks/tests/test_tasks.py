# pylint: disable=W0212
from unittest import TestCase
from unittest.mock import MagicMock, patch

from peewee import SqliteDatabase

from argus.tasks.base.database import RunningTask, TaskResult
from argus.tasks.base.notifier import Notifier, SimpleFormatter
from argus.tasks.epay import BillEntry, Bills, EPayTask
from argus.tasks.ml.hugging_face import (
    HuggingFaceTrendingModelsTask,
    HuggingFaceTrendingPapersTask,
)
from argus.tasks.ml.paper_with_code import TrendingPapersWithCodeTask
from argus.tasks.product import (
    PriceDiscountsTask,
)
from argus.tasks.tests.test_serialization import MockPriceFetcher


class _MockNotifier(Notifier):
    def __init__(self) -> None:
        self.notified = False

    def notify(self, text: str) -> None:
        self.notified = True


class TestDataFetchers(TestCase):
    def setUp(self) -> None:
        self.test_db = SqliteDatabase(':memory:')
        self.test_db.bind([TaskResult, RunningTask])
        self.test_db.connect()
        self.test_db.create_tables([TaskResult, RunningTask])

    def tearDown(self) -> None:
        self.test_db.drop_tables([TaskResult, RunningTask])
        self.test_db.close()

    def test_hugging_face_models(self) -> None:
        task = HuggingFaceTrendingModelsTask()
        task.run_if_due()
        self.assertEqual(len(TaskResult.select()), 1)

    def test_hugging_face_papers(self) -> None:
        task = HuggingFaceTrendingPapersTask()
        task.run_if_due()
        self.assertEqual(len(TaskResult.select()), 1)

    def test_papers_with_code(self) -> None:
        task = TrendingPapersWithCodeTask()
        task.run_if_due()
        self.assertEqual(len(TaskResult.select()), 1)

    @patch('argus.tasks.epay.EpayClient')
    def test_epay_client(self, MockEpayClient: MagicMock) -> None:
        mock_client = MagicMock()
        MockEpayClient.return_value = mock_client
        mock_client.__enter__.return_value = mock_client
        bills = [
            BillEntry(name='Electricity', id='12345678', amount=1),
            BillEntry(name='Water', id='87654321', amount=2),
        ]
        mock_client.get_bills.return_value = Bills(bills)
        notifier = _MockNotifier()
        task = EPayTask(
            username='user', password='pass', notifier=notifier, formatter=SimpleFormatter()
        )
        task.run_if_due()
        self.assertTrue(notifier.notified)
        notifier.notified = False
        mock_client.get_bills.return_value = Bills(bills)
        task.run_if_due()
        self.assertFalse(notifier.notified)
        notifier.notified = False
        mock_client.get_bills.return_value = Bills(
            [
                BillEntry(name='Electricity', id='12345678', amount=1),
                BillEntry(name='Water', id='87654321', amount=3),
            ]
        )
        task.run_if_due()
        self.assertTrue(notifier.notified)

    def test_product_discounts(self) -> None:
        task = PriceDiscountsTask(
            task_id='price_discounts_test', fetchers=[MockPriceFetcher('www.example.com', 1)]
        )
        task.run_if_due()
        task.fetchers = [MockPriceFetcher('www.example.com', 0.25)]
        discounts = task.run()
        self.assertEqual(len(discounts), 1)
        self.assertAlmostEqual(discounts[0].discount, 0.75)
