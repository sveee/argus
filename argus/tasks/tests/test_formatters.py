from unittest import TestCase

from argus.tasks.epay import Bills, EPayMarkdownFormatter
from argus.tasks.product import PriceDiscountsFormatter, ProductPrice, ProductPrices


class TestFormatter(TestCase):
    def test_epay(self):
        formatter = EPayMarkdownFormatter()
        formatter.format(Bills([]))

    def test_product_discount(self):
        formatter = PriceDiscountsFormatter()
        formatter.format(
            ProductPrices([ProductPrice('test', 0, 'www.example.com', 'vendor', discount=0)])
        )
