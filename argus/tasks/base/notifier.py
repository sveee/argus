import logging
from abc import ABC, abstractmethod
from typing import Generic, List

import requests
from telegram import Bot

from argus.tasks.base.data import T

logger = logging.getLogger(__name__)


class MessageFormatter(ABC, Generic[T]):
    @abstractmethod
    def format(self, data: T) -> str:
        """Format the data into a notification message."""
        pass


class Notifier:
    @abstractmethod
    def notify(self, text: str) -> None:
        """Send a notification with the provided message."""
        pass


class FormattedNotifier:
    """
    A service that combines a notifier with a formatter to handle the complete
    notification workflow for a specific type of data.
    """

    def __init__(self, notifier: Notifier, formatter: MessageFormatter) -> None:
        self._notifier = notifier
        self._formatter = formatter

    def notify(self, data: T) -> None:
        """Format the data and send the notification using the configured notifier."""
        formatted_message = self._formatter.format(data)
        self._notifier.notify(formatted_message)


class SlackNotifier:
    SLACK_MESSAGE_MAX_LENGTH = 4000

    def __init__(self, slack_hooks: List[str]) -> None:
        self._slack_hooks = slack_hooks

    @staticmethod
    def post(text: str, webhook: str) -> None:
        payload = {
            'text': text,
            'username': 'Argus',
            'icon_url': 'https://i.ibb.co/y8Ydz0X/argus.png',
        }
        requests.post(webhook, json=payload, timeout=300)

    def notify(self, text: str) -> None:
        logger.info('Slack message size: %s', len(text))
        if len(text) >= self.SLACK_MESSAGE_MAX_LENGTH:
            raise ValueError(
                f"Message exceeds Slack limit of {self.SLACK_MESSAGE_MAX_LENGTH} characters."
            )
        for slack_hook in self._slack_hooks:
            self.post(text, slack_hook)


class TelegamNotifier:

    def __init__(self, bot_token: str, chat_ids: list[str]) -> None:
        self._telegram_bot = Bot(token=bot_token)
        self._chat_ids = chat_ids

    async def notify(self, text: str) -> None:
        for chat_id in self._chat_ids:
            logger.info(
                'Telegram message with length %d sent to chat %s', len(text), chat_id
            )
            await self._telegram_bot.send_message(
                chat_id=chat_id, text=text, parse_mode='MarkdownV2'
            )
