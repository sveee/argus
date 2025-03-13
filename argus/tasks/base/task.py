import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from typing import Generic

from argus.tasks.base.database import RunningTask, TaskResult
from argus.tasks.base.notifier import DataFormatter, Notifier
from argus.tasks.base.scheduler import Scheduler
from argus.tasks.base.serializable import JsonDict, Serializable, T, cast

logger = logging.getLogger(__name__)


def camel_to_snake(s: str) -> str:
    return ''.join('_' + c.lower() if c.isupper() else c for c in s).lstrip('_')


class Task(Serializable, ABC, Generic[T]):
    def __init__(
        self,
        task_id: str | None = None,
        scheduler: Scheduler | None = None,
        formatter: DataFormatter | None = None,
        notifier: Notifier | None = None,
    ) -> None:
        self._scheduler = scheduler if scheduler else None
        self._formatter = formatter
        self._notifier = notifier
        self.task_id = task_id if task_id is not None else self.generate_unique_task_name()

    @classmethod
    def generate_unique_task_name(cls) -> str:
        unique_id = uuid.uuid4().hex[:8]
        return f'{camel_to_snake(cls.__name__)}_{unique_id}'

    @abstractmethod
    def run(self) -> T:
        """Runs the task and returns the result."""
        pass

    def save_result(self, result: T) -> None:
        """Stores the result in the database."""
        serialized_result = json.dumps(result.to_dict())
        TaskResult.create(task_id=self.task_id, result=serialized_result)

    def get_last_result(self) -> T | None:
        """Retrieve a result in the database."""
        entry = (
            TaskResult.select()
            .where(TaskResult.task_id == self.task_id)
            .order_by(TaskResult.created_at.desc())
            .first()
        )
        return cast(T, Serializable.from_dict(json.loads(entry.result))) if entry else None

    def notify_result(self, result: T) -> None:
        """Notifies using the notifier if available."""
        if self._notifier and self._formatter:
            self._notifier.notify(self._formatter.format(result))

    def _should_notify(self, result: T) -> bool:
        return True

    def run_if_due(self) -> None:
        """Runs the task if it is due, handles scheduling, storing, and notifying."""
        if not self._scheduler or self._scheduler.is_due():
            logger.info('%s running', self.task_id)
            result = self.run()
            should_notify = self._should_notify(result)
            self.save_result(result)
            if should_notify:
                self.notify_result(result)
            if self._scheduler:
                self._scheduler.set_next_runtime()
            logger.info('%s finished. Next run time: %s', self.task_id, self._scheduler)

    @staticmethod
    def serialize_parameters(data: JsonDict) -> JsonDict:
        return {
            'task_id': data['task_id'],
            'scheduler': (Scheduler.from_dict(data['scheduler']) if data['scheduler'] else None),
            'formatter': (
                DataFormatter.from_dict(data['formatter']) if data['formatter'] else None
            ),
            'notifier': (Notifier.from_dict(data['notifier']) if data['notifier'] else None),
        }

    def to_dict(self) -> JsonDict:
        return {
            '__class__': type(self).__name__,
            'task_id': self.task_id,
            'scheduler': self._scheduler.to_dict() if self._scheduler else None,
            'notifier': self._notifier.to_dict() if self._notifier else None,
            'formatter': self._formatter.to_dict() if self._formatter else None,
        }

    def __repr__(self) -> str:
        return f'{self.task_id}[{self._scheduler}]'


class ChangeDetectingTask(Task[T], ABC):
    def _should_notify(self, result: T) -> bool:
        return result != self.get_last_result()


class TaskManager:
    def __init__(self, run_delay: int = 30) -> None:
        self._tasks: list[Task] = []
        self._run_delay = run_delay
        self._is_running = True
        self._tasks = []
        self._last_updated = None
        self._n_running_tasks = 0

    def _check_for_updates(self):
        latest_update = (
            RunningTask.select(RunningTask.last_updated)
            .order_by(RunningTask.last_updated.desc())
            .first()
        )
        updated = False
        n_current_tasks = len(RunningTask.select())
        if n_current_tasks != self._n_running_tasks:
            self._n_running_tasks = n_current_tasks
            updated = True

        if latest_update and (
            not self._last_updated or latest_update.last_updated > self._last_updated
        ):
            self._last_updated = latest_update.last_updated
            updated = True
        return updated

    def _load_running_tasks(self) -> None:
        """Fetch and deserialize active tasks from the database."""
        tasks = list(RunningTask.select().order_by())
        self._tasks = [Task.from_dict(json.loads(task.serialized_data)) for task in tasks]
        logger.info('New tasks: %s', self._tasks)

    def run(self):
        logger.info('Task Manager started')
        while self._is_running:
            if self._check_for_updates():
                logger.info('Tasks updated, reloading...')
                self._load_running_tasks()

            for task in self._tasks:
                task.run_if_due()

            time.sleep(self._run_delay)
