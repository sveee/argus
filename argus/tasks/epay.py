import os
import re
from dataclasses import asdict, dataclass
from typing import Any, List

import pandas as pd
from playwright.sync_api import expect, sync_playwright

from argus.tasks.base.data import JsonSerializable, JsonType
from argus.tasks.base.format_utils import dataframe_to_str
from argus.tasks.base.notifier import SlackNotifier
from argus.tasks.base.task import ChangeDetectingTask


@dataclass(frozen=True)
class BillEntry:
    name: str
    amount: float


class Bills(List[BillEntry], JsonSerializable):
    def to_json_data(self) -> JsonType:
        return [asdict(entry) for entry in self]


class EPayTask(ChangeDetectingTask[Bills]):
    def run(self) -> Bills:
        bill_entries = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto('https://www.epay.bg/v3main/front')
            login_user = page.locator('#login_user')
            login_user.click()
            login_user.fill(os.environ['EPAY_USERNAME'])
            login_user.press('Tab')
            page.locator('#login_pass').fill(os.environ['EPAY_PASSWORD'])
            page.get_by_role('button', name='Вход в ePay.bg').click()
            page.get_by_role('link', name='Регистрирани сметки').click()
            with page.expect_response(
                lambda response: 'v3main/bills/list' in response.url
                and response.request.resource_type == 'xhr'
            ) as event:
                bill_entries = event.value.json()['DATA']
            context.close()
            browser.close()
        entries = []
        for entry in bill_entries:
            match = re.search(r'\d+\.\d+', entry['BILL_STATUS_DESC'])
            amount = float(match.group()) if match else 0
            entries.append(BillEntry(name=entry['REG_DESCR'].strip(), amount=amount))
        return Bills(sorted(entries, key=lambda x: x.name))


class EPaySlackNotifier(SlackNotifier[Bills]):
    def format(self, data: Bills) -> str:
        df = pd.DataFrame(data.to_json_data())
        df = pd.concat(
            [df, pd.DataFrame([{"name": 'Total', "amount": df.amount.sum()}])]
        ).reset_index(drop=True)
        return f'💸 *Bills* 💸\n```' + dataframe_to_str(df) + '```'
