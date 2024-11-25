from dataclasses import asdict, dataclass
from datetime import datetime, timedelta

from argus.tasks.base.data import JsonSerializable, JsonType
from argus.tasks.base.notifier import FormattedNotifier, MessageFormatter
from argus.tasks.base.scheduler import Frequency, Scheduler, SchedulerConfig
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
        remind_in: list[timedelta] | None = None,
        notifier: FormattedNotifier | None = None,
    ) -> None:
        target_date = target_date.replace(hour=9, minute=0)
        remind_in = sorted(remind_in if remind_in else [timedelta()], reverse=True)
        super().__init__(
            Scheduler(
                [target_date - delta for delta in remind_in],
                SchedulerConfig(frequency=Frequency.LIST),
            ),
            notifier,
            store_to_db=False,
        )
        self._title = title
        self._target_date = target_date

    def run(self) -> Todo:
        return Todo(
            self._title,
            self._target_date.strftime('%-d %b %H:%M'),
        )


class TodoFormatter(MessageFormatter[Todo]):
    def format(self, data: Todo) -> str:
        return '📝 *TODO*\n' f'*Task:* {data.title}\n' f'*Date:* {data.date}'
