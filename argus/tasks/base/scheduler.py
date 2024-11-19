from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta


class Frequency(Enum):
    MONTHLY = 'monthly'
    WEEKLY = 'weekly'
    DAILY = 'daily'
    HOURLY = 'hourly'
    MINUTELY = 'minutely'
    LIST = 'list'


FREQ_TO_DELTA = {
    Frequency.MONTHLY: relativedelta(months=1),
    Frequency.WEEKLY: relativedelta(weeks=1),
    Frequency.DAILY: relativedelta(days=1),
    Frequency.HOURLY: relativedelta(hours=1),
    Frequency.MINUTELY: relativedelta(minutes=1),
    Frequency.LIST: None,
}


class Day(Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class Month(Enum):
    JANUARY = 1
    FEBRUARY = 2
    MARCH = 3
    APRIL = 4
    MAY = 5
    JUNE = 6
    JULY = 7
    AUGUST = 8
    SEPTEMBER = 9
    OCTOBER = 10
    NOVEMBER = 11
    DECEMBER = 12


WEEKEND = [Day.SATURDAY, Day.SUNDAY]


@dataclass(frozen=True)
class SchedulerConfig:
    frequency: Frequency = Frequency.LIST
    timezone: str = 'Europe/Sofia'
    adjust_to_current_time: bool = True
    skip_months: list[int] | None = None
    skip_days: list[Day] | None = None


class Scheduler:
    def __init__(
        self,
        runtimes: list[datetime],
        config: SchedulerConfig | None = None,
    ) -> None:
        self._config = config if config else SchedulerConfig()
        self._delta = FREQ_TO_DELTA[self._config.frequency]
        self._runtimes = sorted(
            runtime.replace(tzinfo=ZoneInfo(self._config.timezone))
            for runtime in runtimes
        )
        self.next_runtime: datetime | None = self._runtimes[0]
        if self._config.adjust_to_current_time:
            while self.next_runtime is not None and self.next_runtime < self.now():
                self.set_next_runtime()

    def now(self) -> datetime:
        return datetime.now(ZoneInfo(self._config.timezone))

    def _is_valid_runtime(self, runtime: datetime | None) -> bool:
        if runtime is None:
            return False
        if self._config.skip_days and Day(runtime.weekday()) in self._config.skip_days:
            return False
        if (
            self._config.skip_months
            and Month(runtime.month) in self._config.skip_months
        ):
            return False
        return True

    def set_next_runtime(self) -> None:
        if self.next_runtime is None:
            return
        if self._config.frequency == Frequency.LIST:
            self.next_runtime = next(
                (
                    runtime
                    for runtime in self._runtimes
                    if runtime > self.next_runtime and self._is_valid_runtime(runtime)
                ),
                None,
            )
        else:
            self.next_runtime = self.next_runtime + self._delta
            for _step in range(1000):
                if self._is_valid_runtime(self.next_runtime):
                    return
                self.next_runtime = self.next_runtime + self._delta
            raise RuntimeError('Infinite loop')

    def is_due(self) -> bool:
        return self.next_runtime is not None and self.now() >= self.next_runtime

    def __repr__(self) -> str:
        return (
            self.next_runtime.strftime('%Y-%m-%d %H:%M:%S')
            if self.next_runtime
            else str(None)
        )
