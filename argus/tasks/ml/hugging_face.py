from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Type

import pandas as pd
import requests
from bs4 import BeautifulSoup

from argus.tasks.base.data import JsonSerializable, JsonType
from argus.tasks.base.format_utils import dataframe_to_str
from argus.tasks.base.notifier import SlackNotifier
from argus.tasks.base.task import Task


@dataclass
class ModelInfo:
    model_id: str
    n_likes: int
    n_downloads: int


class TrendingModelsData(List[ModelInfo], JsonSerializable):
    def to_json_data(self) -> JsonType:
        return [asdict(model_info) for model_info in self]


class HuggingFaceTrendingModels(Task[TrendingModelsData]):

    LIMIT = 10

    def run(self) -> TrendingModelsData:
        response = requests.get(
            f'https://huggingface.co/api/trending?limit={self.LIMIT}&type=model',
            timeout=300,
        ).json()
        return TrendingModelsData(
            [
                ModelInfo(
                    model_id=sample['repoData']['id'],
                    n_likes=sample['repoData']['likes'],
                    n_downloads=sample['repoData']['downloads'],
                )
                for sample in response['recentlyTrending']
            ]
        )


class HuggingFaceModelNotifier(SlackNotifier[TrendingModelsData]):
    TOP_K = 10

    def format(self, data: TrendingModelsData) -> str:
        df = pd.DataFrame(data.to_json_data())
        df = df.sort_values('n_likes', ascending=False)
        df['model_id'] = 'https://huggingface.co/' + df['model_id'].str.lstrip('/')
        df = df.iloc[: self.TOP_K]
        return f'🤗 *HuggingFace Trending Models*\n```' + dataframe_to_str(df) + '```'


@dataclass(frozen=True, order=True)
class Paper:
    url: str
    title: str
    n_likes: int


class Papers(List[Paper], JsonSerializable):
    def to_json_data(self) -> JsonType:
        return [asdict(paper) for paper in self]


class HuggingFaceTrendingPapers(Task[Papers]):

    LIMIT = 10
    LAST_N_DAYS = 7

    def run(self) -> Papers:
        current_date = datetime.now()
        papers: list[Paper] = []
        for days_delta in range(1, self.LAST_N_DAYS + 1):
            date = current_date - timedelta(days=days_delta)
            url = date.strftime('https://huggingface.co/papers?date=%Y-%m-%d')
            soup = BeautifulSoup(requests.get(url, timeout=300).text, features='lxml')
            for div in soup.find_all(
                lambda tag: tag.name == 'article'
                and tag.get('class')
                and {'flex', 'flex-col'} <= set(tag.get('class'))
            ):
                parent = div.find('div', {'class': 'w-full'})
                a = parent.find('a', {'class': 'cursor-pointer'})
                n_likes = parent.find('div', {'class': 'leading-none'}).text.strip()
                n_likes = int(n_likes) if n_likes.isdigit() else 0
                papers.append(
                    Paper(url=a['href'], title=a.text.strip(), n_likes=n_likes)
                )

        return Papers(sorted(set(papers)))


class HuggingFacePapersNotifier(SlackNotifier[Papers]):
    TOP_K = 10

    def format(self, data: Papers) -> str:
        df = pd.DataFrame(data.to_json_data())
        df = df.sort_values('n_likes', ascending=False)
        df['url'] = 'https://huggingface.co/' + df['url'].str.lstrip('/')
        df = df.iloc[: self.TOP_K]
        return f'🤗 *HuggingFace Trending Papers*\n```' + dataframe_to_str(df) + '```'