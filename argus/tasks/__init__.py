from argus.tasks.base.notifier import SlackNotifier, TelegramNotifier
from argus.tasks.epay import EPayTask
from argus.tasks.github import TrendingGithubReposTask
from argus.tasks.ml.hugging_face import (
    HuggingFaceTrendingModelsTask,
    HuggingFaceTrendingPapersTask,
)
from argus.tasks.ml.paper_with_code import TrendingPapersWithCodeTask
from argus.tasks.product import PriceDiscountsTask
from argus.tasks.snow import SnowForecastTask, SnowReportData
from argus.tasks.todo import TodoTask

__all__ = [
    'SlackNotifier',
    'TelegramNotifier',
    'EPayTask',
    'TrendingGithubReposTask',
    'HuggingFaceTrendingModelsTask',
    'HuggingFaceTrendingPapersTask',
    'PriceDiscountsTask',
    'TrendingPapersWithCodeTask',
    'TodoTask',
    'SnowForecastTask',
    'SnowReportData',
]
