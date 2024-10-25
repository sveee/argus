import logging
from abc import ABC, abstractmethod
from typing import Generic, List

import requests

from argus.tasks.base.data import T

logger = logging.getLogger(__name__)


class Notifier(ABC, Generic[T]):
    @abstractmethod
    def format(self, data: T) -> str:
        """Format the data into a notification message."""
        pass

    @abstractmethod
    def notify(self, text: str) -> None:
        """Send a notification with the provided message."""
        pass

    def notify_formatted(self, data: T) -> None:
        """Format the data and send the notification."""
        self.notify(self.format(data))


class SlackNotifier(Notifier[T], ABC):
    SLACK_MESSAGE_MAX_LENGTH = 4000

    def __init__(self, slack_hooks: List[str]) -> None:
        self._slack_hooks = slack_hooks

    @abstractmethod
    def format(self, data: T) -> str:
        """Abstract method to format data for Slack."""
        pass

    @staticmethod
    def post(text: str, webhook: str) -> None:
        payload = {
            'text': text,
            'username': 'Argus',
            'icon_url': 'https://i.ibb.co/y8Ydz0X/argus.png',
        }
        requests.post(webhook, json=payload, timeout=300)

    def notify(self, text: str) -> None:
        logger.info(f'Slack message size: %s', len(text))
        if len(text) >= self.SLACK_MESSAGE_MAX_LENGTH:
            raise ValueError(
                f"Message exceeds Slack limit of {self.SLACK_MESSAGE_MAX_LENGTH} characters."
            )
        for slack_hook in self._slack_hooks:
            self.post(text, slack_hook)
