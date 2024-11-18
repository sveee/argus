import os
import re
import time
from dataclasses import asdict, dataclass
from typing import List

import pandas as pd
import requests
from bs4 import BeautifulSoup

from argus.tasks.base.data import JsonSerializable, JsonType
from argus.tasks.base.format_utils import dataframe_to_str
from argus.tasks.base.notifier import MessageFormatter
from argus.tasks.base.task import ChangeDetectingTask


@dataclass(frozen=True)
class BillEntry:
    name: str
    amount: float


class Bills(List[BillEntry], JsonSerializable):
    def to_json_data(self) -> JsonType:
        return [asdict(entry) for entry in self]


class EpayClient:
    def __init__(self, username: str, password: str):
        self.session = requests.Session()
        self.username = username
        self.password = password
        self.base_url = "https://www.epay.bg"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/v3main/login",
        }

    def __enter__(self):
        """Logs in to ePay upon entering the context."""
        if not self.login():
            raise RuntimeError("Failed to log in.")
        return self  # Returns the instance for use within the 'with' block

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Logs out of ePay upon exiting the context."""
        self.logout()

    def get_login_salt(self) -> str:
        """Fetches the login salt required for logging in."""
        url = f"{self.base_url}/v3main/front"
        response = self.session.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        login_salt_input = soup.find('input', {'name': 'loginsalt'})
        assert login_salt_input
        return login_salt_input['value']

    def login(self) -> bool:
        """Logs in to ePay with the provided credentials."""
        login_salt = self.get_login_salt()
        if not login_salt:
            raise ValueError("Failed to retrieve login salt.")

        url = f"{self.base_url}/v3main/login"
        login_data = {
            "loginsalt": login_salt,
            "username": self.username,
            "password": self.password,
            "submit": "Вход в ePay.bg",
        }

        response = self.session.post(url, data=login_data, headers=self.headers)
        return response.ok  # Returns True if login was successful, False otherwise

    def get_bills(self, rows: int = 10, page_num: int = 1) -> Bills:
        """Fetches a list of bills after successful login."""
        bills_url = f"{self.base_url}/v3main/bills/list"
        bills_data = {
            "rows": str(rows),
            "action": "init",
            "grid_type": "default",
            "page_num": str(page_num),
            "sort_col": "NaN",
            "ts": str(int(time.time() * 1000)),  # Current timestamp in milliseconds
        }

        # Update headers for AJAX request
        bills_headers = self.headers.copy()
        bills_headers.update(
            {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{self.base_url}/v3main/bills",
            }
        )

        response = self.session.post(bills_url, data=bills_data, headers=bills_headers)
        assert response.ok
        data = response.json()
        bills = []
        for bill_entry in data['DATA']:
            float_match = re.search(r'\d+\.\d+', bill_entry['BILL_STATUS_DESC'])
            amount = float(float_match.group(0)) if float_match else 0.0
            bills.append(BillEntry(bill_entry['REG_DESCR'], amount))
        return Bills(bills)

    def logout(self) -> bool:
        """Logs out of the ePay session."""
        logout_url = f"{self.base_url}/v3main/logout"
        response = self.session.get(logout_url, headers=self.headers)
        return response.ok  # Returns True if logout was successful


class EPayTask(ChangeDetectingTask[Bills]):
    def run(self) -> Bills:
        with EpayClient(
            os.environ['EPAY_USERNAME'], os.environ['EPAY_PASSWORD']
        ) as epay_client:
            bills = epay_client.get_bills()
        return bills


def _prepare_data(data: Bills) -> pd.DataFrame:
    df = pd.DataFrame(data.to_json_data())
    df = pd.concat(
        [df, pd.DataFrame([{"name": 'Total', "amount": df.amount.sum()}])]
    ).reset_index(drop=True)
    return '💸 *Bills* 💸\n```\n' + dataframe_to_str(df) + '\n```'


class EPayFormatter(MessageFormatter[Bills]):
    def format(self, data: Bills) -> str:
        return _prepare_data(data)
