from dataclasses import asdict, dataclass

import pandas as pd
import requests
from bs4 import BeautifulSoup

from argus.tasks.base.format_utils import dataframe_to_str
from argus.tasks.base.notifier import DataFormatter
from argus.tasks.base.serializable import JsonDict, Serializable
from argus.tasks.base.task import Task


@dataclass(frozen=True)
class Paper:
    title: str
    stars: int
    stars_per_hour: float
    url: str


class Papers(list[Paper], Serializable):
    def to_dict(self) -> JsonDict:
        return {'papers': [asdict(paper) for paper in self]}

    @classmethod
    def from_dict(cls, data: JsonDict) -> 'Papers':
        return Papers([Paper(**entry) for entry in data['papers']])


class TrendingPapersWithCodeTask(Task[Papers]):
    LIMIT = 10

    def run(self) -> Papers:
        soup = BeautifulSoup(
            requests.get('https://paperswithcode.com/', timeout=300).text,
            features='html.parser',
        )
        return Papers(
            [
                Paper(
                    title=item.find('h1').text.strip(),
                    stars=int(
                        item.find('span', {'class': 'badge-secondary'})
                        .text.strip()
                        .replace(',', '')
                    ),
                    stars_per_hour=float(
                        item.find('div', {'class': 'stars-accumulated'}).text.strip().split()[0]
                    ),
                    url='https://paperswithcode.com' + item.find('a')['href'],
                )
                for item in soup.find_all('div', {'class': 'infinite-item'})
            ]
        )


class PapersWithCodeSlackFormatter(DataFormatter[Papers]):
    TOP_K = 10

    def format(self, data: Papers) -> str:
        df = pd.DataFrame(data.to_dict()['papers'])
        df = df.sort_values('stars', ascending=False)
        df = df.iloc[: self.TOP_K]
        return '📝 *PaperWithCode Trending Papers*\n```' + dataframe_to_str(df) + '```'
