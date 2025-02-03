from dataclasses import asdict, dataclass
from datetime import datetime, timedelta

from argus.tasks.base.notifier import DataFormatter, Notifier
from argus.tasks.base.scheduler import Frequency, Scheduler, SchedulerConfig
from argus.tasks.base.serializable import JsonDict, Serializable
from argus.tasks.base.task import Task


@dataclass(frozen=True)
class Todo(Serializable):
    title: str
    date: datetime

    def to_dict(self) -> JsonDict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: JsonDict) -> 'Todo':
        return cls(**data)


class TodoTask(Task[Todo]):

    def __init__(
        self,
        target_date: datetime,
        title: str,
        remind_in: list[timedelta] | None = None,
        formatter: DataFormatter | None = None,
        notifier: Notifier | None = None,
    ) -> None:
        target_date = target_date.replace(hour=9, minute=0)
        remind_in = sorted(remind_in if remind_in else [timedelta()], reverse=True)
        super().__init__(
            Scheduler(
                [target_date - delta for delta in remind_in],
                SchedulerConfig(frequency=Frequency.LIST),
            ),
            formatter=formatter,
            notifier=notifier,
            store_to_db=False,
        )
        self._remind_in = remind_in
        self._title = title
        self._target_date = target_date

    def run(self) -> Todo:
        return Todo(
            self._title,
            self._target_date,
        )

    def to_dict(self) -> JsonDict:
        data = super().to_dict()
        data['target_date'] = self._target_date.isoformat()
        data['title'] = self._title
        data['remind_in'] = (
            [delta.total_seconds() for delta in self._remind_in]
            if self._remind_in
            else None
        )
        return data

    @classmethod
    def from_dict(cls: type['TodoTask'], data: dict) -> 'TodoTask':
        return TodoTask(
            target_date=datetime.fromisoformat(data['target_date']),
            title=data['title'],
            remind_in=[timedelta(seconds=seconds) for seconds in data['remind_in']],
            formatter=(
                DataFormatter.from_dict(data['formatter'])
                if data['formatter']
                else None
            ),
            notifier=(
                Notifier.from_dict(data['notifier']) if data['notifier'] else None
            ),
        )


class TodoFormatter(DataFormatter[Todo]):
    def format(self, data: Todo) -> str:
        remaining_days = (datetime.now() - data.date).days
        when_message = (
            'today'
            if remaining_days == 0
            else '1 day' if remaining_days == 1 else f'{remaining_days} days'
        )
        return f'✅ *TODO ({when_message})*\n{data.title}'
