from dataclasses import dataclass
from datetime import datetime, timedelta

from argus.tasks.base.notifier import DataFormatter
from argus.tasks.base.scheduler import Frequency, Scheduler, SchedulerConfig
from argus.tasks.base.serializable import JsonDict, Serializable
from argus.tasks.base.task import Task


@dataclass(frozen=True)
class Todo(Serializable):
    title: str
    target_date: datetime

    def to_dict(self) -> JsonDict:
        return {
            'title': self.title,
            'target_date': self.target_date.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: JsonDict) -> 'Todo':
        return cls(
            title=data['title'], target_date=datetime.fromisoformat(data['target_date'])
        )


class TodoTask(Task[Todo]):
    def __init__(
        self,
        title: str,
        target_date: datetime | None = None,
        remind_in: list[timedelta] | None = None,
        **kwargs,
    ) -> None:
        if target_date:
            remind_in = sorted(remind_in if remind_in else [timedelta()], reverse=True)
            scheduler = Scheduler(
                [target_date - delta for delta in remind_in],
                SchedulerConfig(frequency=Frequency.LIST),
            )
        else:
            scheduler = kwargs['scheduler']
        super().__init__(
            scheduler=scheduler,
            task_id=kwargs.get('task_id'),
            formatter=kwargs.get('formatter'),
            notifier=kwargs.get('notifier'),
        )
        self._title = title
        self._target_date = target_date

    def run(self) -> Todo:
        return Todo(
            self._title,
            self._target_date if self._target_date else datetime.now(),
        )

    def to_dict(self) -> JsonDict:
        return super().to_dict() | {
            'title': self._title,
            'target_date': self._target_date.isoformat() if self._target_date else None,
        }

    @classmethod
    def from_dict(cls: type['TodoTask'], data: dict) -> 'TodoTask':
        return TodoTask(
            title=data['title'],
            target_date=(
                datetime.fromisoformat(data['target_date'])
                if data.get('target_date')
                else None
            ),
            **cls.serialize_parameters(data),
        )


class TodoFormatter(DataFormatter[Todo]):
    def format(self, data: Todo) -> str:
        remaining_days = (datetime.now() - data.target_date).days
        when_message = (
            'today'
            if remaining_days == 0
            else '1 day'
            if remaining_days == 1
            else f'{remaining_days} days'
        )
        return f'*TODO \\({when_message}\\)*\n{data.title}'
