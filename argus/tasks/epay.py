import re
import time
from dataclasses import asdict, dataclass

import pandas as pd
import requests
from bs4 import BeautifulSoup
from telegram.helpers import escape_markdown

from argus.tasks.base.format_utils import dataframe_to_str
from argus.tasks.base.notifier import DataFormatter
from argus.tasks.base.serializable import JsonDict, Serializable
from argus.tasks.base.task import ChangeDetectingTask


@dataclass(frozen=True)
class BillEntry:
    name: str
    id: str
    amount: float


class Bills(list[BillEntry], Serializable):
    def to_dict(self) -> JsonDict:
        return {'bills': [asdict(entry) for entry in self]}

    @classmethod
    def from_dict(cls, data: JsonDict) -> 'Bills':
        return Bills([BillEntry(**entry) for entry in data['bills']])


class EpayClient:
    def __init__(self, username: str, password: str):
        self.session = requests.Session()
        self.username = username
        self.password = password
        self.base_url = 'https://www.epay.bg'
        self.headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': self.base_url,
            'Referer': f'{self.base_url}/v3main/login',
        }

    def __enter__(self):
        """Logs in to ePay upon entering the context."""
        if not self.login():
            raise RuntimeError('Failed to log in.')
        return self  # Returns the instance for use within the 'with' block

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Logs out of ePay upon exiting the context."""
        self.logout()

    def get_login_salt(self) -> str:
        """Fetches the login salt required for logging in."""
        url = f'{self.base_url}/v3main/front'
        response = self.session.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        login_salt_input = soup.find('input', {'name': 'loginsalt'})
        assert login_salt_input
        return login_salt_input['value']

    def login(self) -> bool:
        """Logs in to ePay with the provided credentials."""
        login_salt = self.get_login_salt()
        if not login_salt:
            raise ValueError('Failed to retrieve login salt.')

        url = f'{self.base_url}/v3main/login'
        login_data = {
            'loginsalt': login_salt,
            'username': self.username,
            'password': self.password,
            'submit': 'Вход в ePay.bg',
        }

        response = self.session.post(url, data=login_data, headers=self.headers)
        return response.ok  # Returns True if login was successful, False otherwise

    def get_bills(self, rows: int = 10, page_num: int = 1) -> Bills:
        """Fetches a list of bills after successful login."""
        bills_url = f'{self.base_url}/v3main/bills/list'
        bills_data = {
            'rows': str(rows),
            'action': 'init',
            'grid_type': 'default',
            'page_num': str(page_num),
            'sort_col': 'NaN',
            'ts': str(int(time.time() * 1000)),  # Current timestamp in milliseconds
        }

        # Update headers for AJAX request
        bills_headers = self.headers.copy()
        bills_headers.update(
            {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': f'{self.base_url}/v3main/bills',
            }
        )

        response = self.session.post(bills_url, data=bills_data, headers=bills_headers)
        assert response.ok
        data = response.json()
        bills = []
        for bill_entry in data['DATA']:
            float_match = re.search(r'\d+\.\d+', bill_entry['BILL_STATUS_DESC'])
            amount = float(float_match.group(0)) if float_match else 0.0
            bills.append(
                BillEntry(
                    name=bill_entry['REG_DESCR'],
                    id=bill_entry['IDN'][-8:],
                    amount=amount,
                )
            )
        return Bills(bills)

    def logout(self) -> bool:
        """Logs out of the ePay session."""
        logout_url = f'{self.base_url}/v3main/logout'
        response = self.session.get(logout_url, headers=self.headers)
        return response.ok  # Returns True if logout was successful


class EPayTask(ChangeDetectingTask[Bills]):
    def __init__(self, username: str, password: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._username = username
        self._password = password

    def run(self) -> Bills:
        with EpayClient(self._username, self._password) as epay_client:
            bills = epay_client.get_bills()
        return bills

    def to_dict(self) -> JsonDict:
        return super().to_dict() | {
            'username': self._username,
            'password': self._password,
        }

    @classmethod
    def from_dict(cls: type['EPayTask'], data: JsonDict) -> 'EPayTask':
        return EPayTask(
            username=data['username'],
            password=data['password'],
            **cls.serialize_parameters(data),
        )


def _format_data_to_markdown(data: Bills) -> str:
    df = pd.DataFrame(data.to_dict()['bills'])
    df = df.sort_values('name')
    df = pd.concat(
        [df, pd.DataFrame([{'name': 'Total', 'id': '', 'amount': df.amount.sum()}])]
    ).reset_index(drop=True)
    return '💸 *Bills* 💸\n```\n' + escape_markdown(dataframe_to_str(df), version=2) + '\n```'


class EPayMarkdownFormatter(DataFormatter[Bills]):
    def format(self, data: Bills) -> str:
        return _format_data_to_markdown(data)
