import logging
import re
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass

import pandas as pd
import requests
from bs4 import BeautifulSoup
from telegram.helpers import escape_markdown

from argus.tasks.base.format_utils import dataframe_to_str
from argus.tasks.base.notifier import DataFormatter
from argus.tasks.base.serializable import JsonDict, Serializable
from argus.tasks.base.task import Task

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProductPrice:
    name: str
    price: float
    url: str
    vendor: str
    discount: float = 0


class PriceFetcher(ABC, Serializable):
    VENDOR: str

    def __init__(self, url: str) -> None:
        self.url = url

    @abstractmethod
    def fetch(self) -> ProductPrice:
        pass

    def to_dict(self) -> JsonDict:
        return super().to_dict() | {'url': self.url}


class ProductPrices(list[ProductPrice], Serializable):
    def to_dict(self) -> JsonDict:
        return super().to_dict() | {'discounts': [asdict(discount) for discount in self]}

    @classmethod
    def from_dict(cls, data: JsonDict) -> 'ProductPrices':
        return ProductPrices([ProductPrice(**discount) for discount in data['discounts']])


class PriceDiscountsTask(Task[ProductPrices]):
    def __init__(self, fetchers: list[PriceFetcher], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fetchers = fetchers

    def _should_notify(self, result: ProductPrices) -> bool:
        return any(product.discount > 0 for product in result)

    def run(self) -> ProductPrices:
        product_discounts = (
            product_discounts
            if (product_discounts := self.get_last_result())
            else ProductPrices([])
        )
        product_prices = [fetcher.fetch() for fetcher in self.fetchers]
        old_products_by_url = {product.url: product for product in product_discounts}
        new_products_by_url = {product.url: product for product in product_prices}
        discounted_products = []
        for url, new_product in new_products_by_url.items():
            old_product = old_products_by_url.get(url)
            discount = (
                (old_product.price - new_product.price) / old_product.price
                if old_product and old_product.price
                else 0
            )
            discounted_products.append(
                ProductPrice(
                    name=new_product.name,
                    price=new_product.price,
                    url=new_product.url,
                    vendor=new_product.vendor,
                    discount=discount,
                )
            )
        return ProductPrices(discounted_products)

    def to_dict(self) -> JsonDict:
        return super().to_dict() | {'fetchers': [fetcher.to_dict() for fetcher in self.fetchers]}

    @classmethod
    def from_dict(cls, data: JsonDict) -> 'PriceDiscountsTask':
        return PriceDiscountsTask(
            fetchers=[PriceFetcher.from_dict(fetcher) for fetcher in data['fetchers']],
            **cls.serialize_parameters(data),
        )


class LillyPriceFetcher(PriceFetcher):
    VENDOR = 'Lilly'

    def fetch(self) -> ProductPrice:
        logger.info('Fetching %s', self.url)
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, features='lxml')
        price_text = soup.find('div', {'class': 'price-box'}).find('span', {'class': 'price'}).text
        re_result = re.search('\d+,\d+', price_text)
        assert re_result, self.url
        price = float(re_result.group(0).replace(',', '.'))
        name = soup.find('h1', {'class': 'page-title'}).text.strip()
        return ProductPrice(
            name=name,
            price=price,
            url=self.url,
            vendor=self.VENDOR,
        )


class PriceDiscountsFormatter(DataFormatter[ProductPrices]):
    def format(self, data: ProductPrices) -> str:
        df = pd.DataFrame(data.to_dict()['discounts'])
        df = df[['vendor', 'name', 'discount']]
        df['name'] = df['name'].str[:15]
        df = df[df.discount > 0]
        df = df.sort_values('name')
        return (
            '💸 *Discounts* 💸\n```\n' + escape_markdown(dataframe_to_str(df), version=2) + '\n```'
        )
