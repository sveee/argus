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
    ONCE = 'once'


FREQ_TO_DELTA = {
    Frequency.MONTHLY: relativedelta(months=1),
    Frequency.WEEKLY: relativedelta(weeks=1),
    Frequency.DAILY: relativedelta(days=1),
    Frequency.HOURLY: relativedelta(hours=1),
    Frequency.MINUTELY: relativedelta(minutes=1),
    Frequency.ONCE: relativedelta(),
}


class Scheduler:
    def __init__(
        self,
        start_date: datetime | None = None,
        frequency: Frequency = Frequency.ONCE,
        timezone: str = 'Europe/Sofia',
    ) -> None:
        self._timezone = timezone
        self._delta = FREQ_TO_DELTA[frequency]
        self._next_date = (
            start_date.replace(tzinfo=ZoneInfo(self._timezone))
            if start_date
            else self._now()
        ).replace(second=0, microsecond=0)
        assert self._next_date >= self._now()

    def _now(self) -> datetime:
        return datetime.now(ZoneInfo(self._timezone))

    def is_due(self) -> bool:
        if self._now() < self._next_date:
            return False
        self._next_date += self._delta
        return True

    def __repr__(self) -> str:
        return self._next_date.strftime('%Y-%m-%d %H:%M:%S')
