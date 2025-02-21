from dataclasses import asdict, dataclass
from enum import Enum

import pandas as pd
import requests
from bs4 import BeautifulSoup

from argus.tasks.base.format_utils import dataframe_to_str
from argus.tasks.base.notifier import DataFormatter
from argus.tasks.base.serializable import JsonDict, Serializable
from argus.tasks.base.task import Task


@dataclass(frozen=True)
class Repo:
    description: str
    n_stars: int
    n_recent_stars: int
    language: str
    url: str


class RepoDateRange(Enum):
    DAYLY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'


class RepoLanguage(Enum):
    PYTHON = 'Python'
    JUPYTER = 'Jupyter Notebook'


class Repos(list[Repo], Serializable):
    def to_dict(self) -> JsonDict:
        return {'repos': [asdict(repo) for repo in self]}

    @classmethod
    def from_dict(cls, data: JsonDict) -> 'Repos':
        return Repos([Repo(**repo) for repo in data['repos']])


class TrendingGithubReposTask(Task[Repos]):

    LIMIT = 10

    def __init__(
        self,
        date_range: RepoDateRange = RepoDateRange.WEEKLY,
        languages: list[RepoLanguage] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.date_range = date_range.value
        self.languages: set[str] = (
            {language.value for language in languages} if languages else set()
        )

    def run(self) -> Repos:
        soup = BeautifulSoup(
            requests.get(
                f'https://github.com/trending?since={self.date_range}',
                timeout=300,
            ).text,
            features='html.parser',
        )
        articles = soup.find_all('article', {'class': 'Box-row'})
        repos = []
        for article in articles:
            name_element = article.find('span', {'class': 'text-normal'}).parent
            description_element = article.find('p')
            description = description_element.text if description_element else ''
            n_stars_element, recent_stars_element = article.find_all(
                'a', {'class': 'Link--muted'}
            )
            n_stars = n_stars_element.text.strip().replace(',', '')
            n_recent_stars = recent_stars_element.text.strip().replace(',', '')
            language_element = article.find('span', {'itemprop': 'programmingLanguage'})
            language = language_element.text if language_element else ''
            if self.languages and language not in self.languages:
                continue
            repos.append(
                Repo(
                    description=description,
                    n_stars=int(n_stars),
                    n_recent_stars=int(n_recent_stars),
                    language=language,
                    url='https://github.com' + name_element['href'],
                )
            )
        return Repos(repos)

    def to_dict(self) -> JsonDict:
        return super().to_dict() | {
            'date_range': RepoDateRange.WEEKLY.value,
            'languages': sorted(self.languages),
        }

    @classmethod
    def from_dict(
        cls: type['TrendingGithubReposTask'], data: JsonDict
    ) -> 'TrendingGithubReposTask':
        return TrendingGithubReposTask(
            date_range=RepoDateRange(data['date_range']),
            languages=(
                [RepoLanguage(language) for language in data['languages']]
                if data['languages']
                else data['languages']
            ),
            **cls.serialize_parameters(data),
        )


class GithubSlackFormatter(DataFormatter[Repos]):
    TOP_K = 10

    def format(self, data: Repos) -> str:
        df = pd.DataFrame(data.to_dict()['repos'])
        df['gain'] = df['n_recent_stars'] / df['n_stars']
        df = df.sort_values('gain', ascending=False)
        df['description'] = df.description.str.strip()
        df = df[['url', 'description', 'n_stars', 'n_recent_stars']]
        df['description'] = df['description'].apply(lambda s: s[:75])
        return '🐙 *Github Repos*\n```' + dataframe_to_str(df) + '```'
