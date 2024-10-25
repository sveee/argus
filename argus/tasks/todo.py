from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, List

from argus.tasks.base.data import JsonSerializable, JsonType
from argus.tasks.base.format_utils import dataframe_to_str
from argus.tasks.base.notifier import Notifier, SlackNotifier
from argus.tasks.base.scheduler import Frequency, Scheduler
from argus.tasks.base.task import Task


@dataclass(frozen=True)
class Todo(JsonSerializable):
    title: str
    date: str

    def to_json_data(self) -> JsonType:
        return asdict(self)


class TodoTask(Task[Todo]):

    def __init__(
        self,
        target_date: datetime,
        title: str,
        remind_in: timedelta = timedelta(days=14),
        notifier: Notifier | None = None,
    ) -> None:
        super().__init__(
            Scheduler(target_date - remind_in, Frequency.ONCE),
            notifier,
            store_to_db=False,
        )
        self._title = title
        self._target_date = target_date

    def run(self) -> Todo:
        return Todo(
            self._title,
            self._target_date.strftime('%-d %B %H:%M'),
        )


class TodoSlackNotifier(SlackNotifier[Todo]):
    def format(self, data: Todo) -> str:
        return f'📝 {data.title}, {data.date}'
