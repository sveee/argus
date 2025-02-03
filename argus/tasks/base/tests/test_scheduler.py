import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from argus.tasks.base.scheduler import (
    WEEKEND,
    Day,
    Frequency,
    Month,
    Scheduler,
    SchedulerConfig,
)


class TestScheduler(unittest.TestCase):
    def setUp(self):
        self.tzinfo = ZoneInfo('Europe/Sofia')
        self.now = datetime(2023, 1, 1, 9, 0).replace(tzinfo=self.tzinfo)

    def test_once_frequency(self):
        scheduler = Scheduler(
            runtimes=[self.now],
            config=SchedulerConfig(
                adjust_to_current_time=False,
            ),
        )
        self.assertTrue(scheduler.is_due())
        scheduler.set_next_runtime()
        self.assertIsNone(scheduler.next_runtime)

    def test_daily_frequency_skip_weekend(self):
        config = SchedulerConfig(
            frequency=Frequency.DAILY,
            skip_days=WEEKEND,
            adjust_to_current_time=False,
        )
        scheduler = Scheduler(
            runtimes=[datetime(2023, 12, 29, 9, 0)],  # Friday
            config=config,
        )
        scheduler.set_next_runtime()
        self.assertEqual(
            scheduler.next_runtime,
            datetime(2024, 1, 1, 9, 0).replace(tzinfo=self.tzinfo),
        )

    def test_monthly_with_skips(self):
        scheduler = Scheduler(
            runtimes=[self.now],
            config=SchedulerConfig(
                frequency=Frequency.MONTHLY,
                skip_months=[Month.FEBRUARY, Month.MARCH],
                adjust_to_current_time=False,
            ),
        )
        scheduler.set_next_runtime()
        self.assertEqual(
            scheduler.next_runtime,
            datetime(2023, 4, 1, 9, 0).replace(tzinfo=self.tzinfo),
        )

    def test_multiple_runtimes(self):
        runtimes = [self.now + timedelta(days=i) for i in range(1, 4)]
        scheduler = Scheduler(
            runtimes,
            SchedulerConfig(
                frequency=Frequency.LIST,
                adjust_to_current_time=False,
            ),
        )

        for expected_run in runtimes:
            self.assertTrue(scheduler.is_due())
            self.assertEqual(
                scheduler.next_runtime,
                expected_run,
            )
            scheduler.set_next_runtime()

        self.assertIsNone(scheduler.next_runtime)

    def test_hourly_frequency(self):
        scheduler = Scheduler(
            [self.now],
            SchedulerConfig(
                frequency=Frequency.HOURLY,
                adjust_to_current_time=False,
            ),
        )
        scheduler.set_next_runtime()
        self.assertEqual(scheduler.next_runtime, self.now + timedelta(hours=1))

    def test_adjust_with_current_time(self):
        scheduler = Scheduler(
            [self.now],
            SchedulerConfig(
                frequency=Frequency.MONTHLY,
                adjust_to_current_time=True,
            ),
        )
        self.assertGreater(scheduler.next_runtime, scheduler.now())
        scheduler = Scheduler(
            [self.now],
            SchedulerConfig(
                frequency=Frequency.MONTHLY,
                adjust_to_current_time=False,
            ),
        )
        self.assertLess(scheduler.next_runtime, scheduler.now())

    def test_infinite_loop_protection(self):
        scheduler = Scheduler(
            [self.now],
            SchedulerConfig(
                frequency=Frequency.DAILY,
                skip_days=list(Day),
                adjust_to_current_time=False,
            ),
        )
        with self.assertRaises(RuntimeError):
            scheduler.set_next_runtime()

    def test_serialization(self):
        scheduler = Scheduler(
            runtimes=[datetime(2023, 12, 29, 9, 0)],
            config=SchedulerConfig(
                adjust_to_current_time=False,
            ),
        )
        serialized_scheduler = scheduler.to_dict()
        deserialized_scheduler = Scheduler.from_dict(serialized_scheduler)
        self.assertEqual(scheduler.next_runtime, deserialized_scheduler.next_runtime)
        self.assertEqual(scheduler.config, deserialized_scheduler.config)


if __name__ == "__main__":
    unittest.main()
