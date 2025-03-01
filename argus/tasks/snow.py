from itertools import product

import pandas as pd
import requests
from bs4 import BeautifulSoup

from argus.tasks.base.format_utils import dataframe_to_str
from argus.tasks.base.notifier import DataFormatter
from argus.tasks.base.serializable import JsonDict, Serializable
from argus.tasks.base.task import Task


class SnowReportData(dict[str, dict[str, float]], Serializable):
    def to_dict(self) -> JsonDict:
        return self

    @classmethod
    def from_dict(cls: type['SnowReportData'], data: JsonDict) -> 'SnowReportData':
        return SnowReportData(data)


class SnowForecastTask(Task):
    def __init__(self, resorts: list[str], levels: list[str], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.resorts = resorts
        for level in levels:
            assert level in ['bot', 'mid', 'top']
        self.levels = levels

    @staticmethod
    def get_snow_forecast(resort: str, level: str) -> dict[str, float]:
        response = requests.get(
            f'https://www.snow-forecast.com/resorts/{resort}/6day/{level}',
            timeout=30,
        )
        soup = BeautifulSoup(response.text, features='lxml')
        day = [
            element['data-value'].split('_')[0]
            for element in soup.find_all('td', {'class': 'forecast-table-days__cell'})
            for _index in range(int(element['colspan']))
        ]
        time = [
            element.text
            for element in soup.find(
                'tr', {'class': 'forecast-table__row', 'data-row': 'time'}
            ).find_all('td')
        ]
        snow = [
            0 if element.text == '—' else float(element.text)
            for element in soup.find(
                'tr', {'class': 'forecast-table__row', 'data-row': 'snow'}
            ).find_all('td')
        ]
        df = pd.DataFrame([day, time, snow], index=['day', 'time', 'snow']).T
        df = df.loc[(df.time == 'AM').idxmax() :]
        snow_report = df.groupby('day', sort=False).snow.sum()
        return snow_report.to_dict()

    def run(self) -> SnowReportData:
        data = {}
        for resort, level in product(self.resorts, self.levels):
            data[f'{resort}/{level}'] = self.get_snow_forecast(resort, level)
        return SnowReportData(data)

    def to_dict(self) -> JsonDict:
        return super().to_dict() | {
            'resorts': self.resorts,
            'levels': self.levels,
        }

    @classmethod
    def from_dict(cls, data: JsonDict) -> 'SnowForecastTask':
        return SnowForecastTask(
            resorts=data['resorts'],
            levels=data['levels'],
            **cls.serialize_parameters(data),
        )


class SnowReportFormatter(DataFormatter[SnowReportData]):
    def format(self, data: SnowReportData) -> str:
        return (
            '❄️ *Snow Report \\(cm\\)*\n```\n'
            + dataframe_to_str(pd.DataFrame(data), show_index=True)
            + '```'
        )
