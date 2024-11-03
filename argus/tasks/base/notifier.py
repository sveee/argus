import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Generic, List

import requests
from telegram import Bot

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


class SlackNotifier(Notifier[T]):
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
        logger.info(f'Slack message size: %s', len(text))
        if len(text) >= self.SLACK_MESSAGE_MAX_LENGTH:
            raise ValueError(
                f"Message exceeds Slack limit of {self.SLACK_MESSAGE_MAX_LENGTH} characters."
            )
        for slack_hook in self._slack_hooks:
            self.post(text, slack_hook)


class TelegamNotifier(Notifier[T]):

    def __init__(self, bot_token: str, chat_ids: list[str]) -> None:
        self._telegram_bot = Bot(token=bot_token)
        self._chat_ids = chat_ids

    def notify(self, text: str) -> None:
        async def async_send_message(chat_id: str) -> None:
            await self._telegram_bot.send_message(
                chat_id=chat_id, text=text, parse_mode='MarkdownV2'
            )

        for chat_id in self._chat_ids:
            logger.info(
                f'Telegram message with length %d sent to chat %s', len(text), chat_id
            )
            asyncio.run(async_send_message(chat_id))
