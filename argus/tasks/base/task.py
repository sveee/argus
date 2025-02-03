import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Generic

from argus.tasks.base.database import RunningTask, TaskResult
from argus.tasks.base.notifier import DataFormatter, Notifier
from argus.tasks.base.scheduler import Scheduler
from argus.tasks.base.serializable import JsonDict, Serializable, T

logger = logging.getLogger(__name__)


class Task(Serializable, ABC, Generic[T]):
    def __init__(
        self,
        scheduler: Scheduler | None = None,
        formatter: DataFormatter | None = None,
        notifier: Notifier | None = None,
        store_to_db: bool = True,
    ) -> None:
        self._scheduler = scheduler if scheduler else None
        self._formatter = formatter
        self._notifier = notifier
        self._name = type(self).__name__
        self._store_to_db = store_to_db

    @abstractmethod
    def run(self) -> T:
        """Runs the task and returns the result."""
        pass

    def save_result(self, result: T) -> None:
        """Stores the result in the database."""
        serialized_result = json.dumps(result.to_dict())
        TaskResult.create(task_name=self._name, result=serialized_result)

    def notify_result(self, result: T) -> None:
        """Notifies using the notifier if available."""
        if self._notifier and self._formatter:
            self._notifier.notify(self._formatter.format(result))

    def on_run_completed(self, result: T) -> None:
        """Handles result storage and notifications."""
        if self._store_to_db:
            self.save_result(result)
        self.notify_result(result)

    def run_if_due(self) -> None:
        """Runs the task if it is due, handles scheduling, storing, and notifying."""
        if not self._scheduler or self._scheduler.is_due():
            logger.info('%s running', self._name)
            result = self.run()
            self.on_run_completed(result)
            if self._scheduler:
                self._scheduler.set_next_runtime()
            logger.info('%s finished. Next run time: %s', self._name, self._scheduler)

    def to_dict(self) -> JsonDict:
        return {
            '__class__': type(self).__name__,
            'scheduler': self._scheduler.to_dict() if self._scheduler else None,
            'notifier': self._notifier.to_dict() if self._notifier else None,
            'formatter': self._formatter.to_dict() if self._formatter else None,
        }

    def __repr__(self) -> str:
        return f'{self._name}[{self._scheduler}]'


class ChangeDetectingTask(Task[T], ABC):
    def get_previous_result_json(self) -> JsonDict | None:
        """Fetches the previous result from the database."""
        previous_entry = (
            TaskResult.select()
            .where(TaskResult.task_name == self.__class__.__name__)
            .order_by(TaskResult.created_at.desc())
            .get_or_none()
        )
        return json.loads(previous_entry.result) if previous_entry else None

    def has_changes(self, current_result: T) -> bool:
        """Compares the current result with the previous result."""
        previous_result_json = self.get_previous_result_json()
        return previous_result_json != current_result.to_dict()

    def on_run_completed(self, result: T) -> None:
        """Saves and notifies only if changes are detected."""
        if self.has_changes(result):
            logger.info('%s detected changes and saved results', self._name)
            self.notify_result(result)
            if self._store_to_db:
                self.save_result(result)
        else:
            logger.info('%s no changes detected', self._name)


class TaskManager:
    def __init__(self, tasks: list[Task], run_delay: int = 30) -> None:
        self._tasks = tasks
        self._run_delay = run_delay
        self._running = True
        self._tasks = []
        self._last_updated = None

    def _check_for_updates(self):
        latest_update = (
            RunningTask.select(RunningTask.last_updated)
            .order_by(RunningTask.last_updated.desc())
            .first()
        )
        if latest_update and (
            not self._last_updated or latest_update.last_updated > self._last_updated
        ):
            self._last_updated = latest_update.last_updated
            return True
        return False

    def _load_running_tasks(self) -> None:
        """Fetch and deserialize active tasks from the database."""
        tasks = RunningTask.select().order_by(RunningTask.last_updated.desc())
        self._tasks = [
            Task.from_dict(json.loads(task.serialized_data)) for task in tasks
        ]

    def run(self):
        logger.info('Task Manager started')
        while self._running:
            if self._check_for_updates():
                logger.info('Tasks updated, reloading...')
                self._load_running_tasks()

            for task in self._tasks:
                task.run_if_due()

            time.sleep(self._run_delay)
