import json
import logging
import time
from abc import ABC, abstractmethod
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
        pass

    def save_result(self, result: T) -> None:
        """
        Stores the result in the database if db_connector is provided.
        The result is stored as a JSON string by calling to_json_data.
        """
        with db:
            serialized_result = json.dumps(result.to_json_data())
            TaskResult.create(
                task_name=self.__class__.__name__, result=serialized_result
            )

    def run_if_due(self) -> None:
        if not self._scheduler or self._scheduler.is_due():
            logger.info('%s running', self._name)
            result = self.run()
            if self._store_to_db:
                self.save_result(result)
            if self._notifier:
                self._notifier.notify(result)
            logger.info('%s finished. Next run time: %s', self._name, self._scheduler)

    def __repr__(self) -> str:
        return f'{self._name}[{self._scheduler}]'


class ChangeDetectingTask(Task[T], ABC):
    def get_previous_result_json(self) -> JsonType | None:
        with db:
            previous_entry = (
                TaskResult.select()
                .where(TaskResult.task_name == self.__class__.__name__)
                .order_by(TaskResult.created_at.desc())
                .get_or_none()
            )
        return json.loads(previous_entry.result) if previous_entry else None

    def run_if_due(self) -> None:
        if not self._scheduler or self._scheduler.is_due():
            logger.info('%s running', self._name)
            current_result = self.run()
            get_previous_result_json = self.get_previous_result_json()
            has_change = get_previous_result_json != current_result.to_json_data()
            if has_change:
                self.save_result(current_result)
                if self._notifier:
                    self._notifier.notify(current_result)
                logger.info('%s detected changes and saved results', self._name)
            else:
                logger.info('%s no changes detected', self._name)

            logger.info('%s finished. Next run time: %s', self._name, self._scheduler)


class TaskManager:
    def __init__(self, tasks: List[Task], run_delay: int = 30) -> None:
        self._tasks = tasks
        self._run_delay = run_delay
        self._running = True

    def run(self):
        logger.info('Tasks: %s', self._tasks)
        while self._running:
            for task in self._tasks:
                task.run_if_due()
            time.sleep(self._run_delay)
