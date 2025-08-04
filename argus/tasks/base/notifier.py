import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Generic

import requests
from telegram import Bot

from argus.tasks.base.serializable import JsonDict, Serializable, T

logger = logging.getLogger(__name__)


class DataFormatter(Serializable, ABC, Generic[T]):
    @abstractmethod
    def format(self, data: T) -> str:
        """Format the data into a notification message."""
        pass


class SimpleFormatter(DataFormatter[T]):
    def format(self, data: T) -> str:
        return str(data)


class Notifier(Serializable):
    @abstractmethod
    def notify(self, text: str) -> None:
        """Send a notification with the provided message."""
        pass


class SlackNotifier(Notifier):
    SLACK_MESSAGE_MAX_LENGTH = 4000

    def __init__(self, slack_hooks: list[str]) -> None:
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
                f'Message exceeds Slack limit of {self.SLACK_MESSAGE_MAX_LENGTH} characters.'
            )
        for slack_hook in self._slack_hooks:
            self.post(text, slack_hook)

    def to_dict(self) -> JsonDict:
        return super().to_dict() | {'slack_hooks': self._slack_hooks}

    @classmethod
    def from_dict(cls, data: JsonDict) -> 'SlackNotifier':
        return cls(slack_hooks=data['slack_hooks'])


class TelegramNotifier(Notifier):
    def __init__(self, bot_token: str, chat_ids: list[str]) -> None:
        self._bot_token = bot_token
        self._telegram_bot = Bot(token=bot_token)
        self._chat_ids = chat_ids
        self._loop = asyncio.new_event_loop()

    async def send_messages(self, text: str) -> None:
        for chat_id in self._chat_ids:
            logger.info(
                'Telegram message with length %d sent to chat %s', len(text), chat_id
            )
            await self._telegram_bot.send_message(
                chat_id=chat_id, text=text, parse_mode='MarkdownV2'
            )

    def notify(self, text: str) -> None:
        self._loop.run_until_complete(self.send_messages(text))

    def to_dict(self) -> JsonDict:
        return super().to_dict() | {
            'bot_token': self._bot_token,
            'chat_ids': self._chat_ids,
        }

    @classmethod
    def from_dict(cls, data: JsonDict) -> 'TelegramNotifier':
        return cls(bot_token=data['bot_token'], chat_ids=data['chat_ids'])


class StaticTelegramNotifier(TelegramNotifier):
    def __init__(self, text: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._text = text

    def notify(self, text: str) -> None:
        return super().notify(self._text)

    def to_dict(self) -> JsonDict:
        return super().to_dict() | {
            'text': self._text,
        }

    @classmethod
    def from_dict(cls, data: JsonDict) -> 'StaticTelegramNotifier':
        return cls(
            text=data['text'], bot_token=data['bot_token'], chat_ids=data['chat_ids']
        )
