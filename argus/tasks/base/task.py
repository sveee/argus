import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Generic, List, Optional

from argus.tasks.base.data import JsonType, T
from argus.tasks.base.database import TaskResult, db
from argus.tasks.base.notifier import FormattedNotifier
from argus.tasks.base.scheduler import Scheduler

logger = logging.getLogger(__name__)


class Task(ABC, Generic[T]):
    def __init__(
        self,
        scheduler: Optional[Scheduler] = None,
        notifier: Optional[FormattedNotifier] = None,
        store_to_db: bool = True,
    ) -> None:
        self._scheduler = scheduler if scheduler else None
        self._notifier = notifier
        self._name = type(self).__name__
        self._store_to_db = store_to_db

    @abstractmethod
    def run(self) -> T:
        """Runs the task and returns the result."""
        pass

    def save_result(self, result: T) -> None:
        """Stores the result in the database."""
        with db:
            serialized_result = json.dumps(result.to_json_data())
            TaskResult.create(
                task_name=self.__class__.__name__, result=serialized_result
            )

    def notify_result(self, result: T) -> None:
        """Notifies using the notifier if available."""
        if self._notifier:
            self._notifier.notify(result)

    def on_run_completed(self, result: T) -> None:
        """Handles result storage and notifications."""
        if self._store_to_db:
            self.save_result(result)
        self.notify_result(result)

    def run_if_due(self) -> bool:
        """Runs the task if it is due, handles scheduling, storing, and notifying."""
        did_run = False
        if not self._scheduler or self._scheduler.is_due():
            logger.info('%s running', self._name)
            result = self.run()
            self.on_run_completed(result)
            if self._scheduler:
                self._scheduler.set_next_runtime()
            logger.info('%s finished', self._name)
            did_run = True
        return did_run

    @property
    def next_runtime(self) -> datetime | None:
        if not self._scheduler:
            return None
        return self._scheduler.next_runtime

    def __repr__(self) -> str:
        return f'{self._name}[{self._scheduler}]'


class ChangeDetectingTask(Task[T], ABC):
    def get_previous_result_json(self) -> JsonType | None:
        """Fetches the previous result from the database."""
        with db:
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
        return previous_result_json != current_result.to_json_data()

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
    def __init__(self, tasks: List[Task], run_delay: int = 30) -> None:
        self._tasks = tasks
        self._run_delay = run_delay
        self._running = True

    def _log_next_task_to_run(self) -> None:
        next_task_to_run = min(
            self._tasks,
            key=lambda t: (
                t.next_runtime.replace(tzinfo=None) if t.next_runtime else datetime.max
            ),
        )
        logger.info('Next task to run: %s', next_task_to_run)

    def run(self):
        logger.info('Tasks: %s', self._tasks)
        self._log_next_task_to_run()
        while self._running:
            for task in self._tasks:
                if task.run_if_due():
                    self._log_next_task_to_run()
            time.sleep(self._run_delay)
