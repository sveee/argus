from argus.tasks.base.notifier import SlackNotifier, TelegamNotifier
from argus.tasks.epay import EPayTask
from argus.tasks.github import TrendingGithubReposTask
from argus.tasks.ml.hugging_face import (
    HuggingFaceTrendingModelsTask,
    HuggingFaceTrendingPapersTask,
)
from argus.tasks.ml.paper_with_code import TrendingPapersWithCodeTask
from argus.tasks.todo import TodoFormatter, TodoTask
