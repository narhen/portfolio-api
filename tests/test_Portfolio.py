#!/usr/bin/env python

import unittest
from mock import PropertyMock, MagicMock, patch, Mock
from datetime import datetime, timedelta, date
from random import randint, uniform

from components.Portfolio import Portfolio
from components.Fond import Fond
from components.error import InvalidUsage, InvalidDate

class TestPortfolio(unittest.TestCase):
    def setUp(self):
        self.fond1 = Fond("T1", "Ticker 1", deposits=[{ "date": "2016-01-01", "amount": 100},
                                        {"date": "2016-01-02", "amount": 100}])

        self.fond2 = Fond("T2", "Ticker 2", deposits=[{ "date": "2016-01-01", "amount": 100},
                                        {"date": "2016-01-03", "amount": 100}])
        self.portfolio = Portfolio(1, {"T1": self.fond1, "T2": self.fond2})

    def generate_quotes(self, from_date, num_quotes):
        quotes = [{"quote_date": from_date, "close": randint(10, 1000)}]
        for i in range(1, num_quotes):
            quotes += [{
                "quote_date": from_date + timedelta(days=i),
                "close": quotes[i - 1]["close"] * uniform(0.75, 1.25)
            }]

        return quotes

    def test__string_to_date(self):
        """_string_to_date converts a string to an datetime.date object"""
        self.assertTrue(isinstance(self.portfolio._string_to_date("2016-01-01"), date))
        self.assertTrue(isinstance(self.portfolio._string_to_date(date(2016, 1, 1)), date))

    def test__string_to_date_raises_exception(self):
        """_string_to_date raises an exception if type of date is not string or datetime.date"""
        with self.assertRaises(InvalidDate):
             self.portfolio._string_to_date(dict())

    def test_get_deposit_by_date(self):
        """get_deposit_by_date returns the sum of all deposits for a given date"""
        
        self.assertEquals(self.portfolio.get_deposits_by_date("2016-01-01"), 200)
        self.assertEquals(self.portfolio.get_deposits_by_date("2016-01-02"), 100)
        self.assertEquals(self.portfolio.get_deposits_by_date("2016-01-03"), 100)
        self.assertEquals(self.portfolio.get_deposits_by_date("2016-01-04"), 0)

    @patch('components.Fond.Fond.quotes', new_callable=PropertyMock)
    def test_get_summary(self, quotes_mock):
        """get_summary returns a list with a summary for each fond and a combined summary"""
        quotes_mock.return_value = self.generate_quotes(date(2016, 1, 1), 3)
        res = self.portfolio.get_summary()

        for entry in res:
            self.assertEquals(set(entry.keys()).issubset(set(["ticker", "name", "development", "total_deposited"])), True)

        self.assertEquals(len(res), 3)
        self.assertEquals(res[-1]["name"], "Portfolio")
        self.assertEquals(res[-1]["ticker"], "Portfolio")
        self.assertEquals(res[-1]["total_deposited"], 400)
        self.assertEquals(len(res[-1]["development"]), 3)

    def test_get_total_development(self):
        """get_total_development combines fonds into a portfolio development"""
        fonds = [[
            { "date": date(2016, 1, 1), "deposit": 1000, "value": 1000 },
            { "date": date(2016, 1, 2), "deposit": 0, "value": 1001 },
            { "date": date(2016, 1, 3), "deposit": 0, "value": 1000 },
        ], [
            { "date": date(2016, 1, 1), "deposit": 10, "value": 10},
            { "date": date(2016, 1, 2), "deposit": 0, "value": 11 },
            { "date": date(2016, 1, 3), "deposit": 1000, "value": 1012 },
        ]]

        expected_result = [
            { "date": date(2016, 1, 1), "deposit": 1010, "value": 1010},
            { "date": date(2016, 1, 2), "deposit": 0, "value": 1012 },
            { "date": date(2016, 1, 3), "deposit": 1000, "value": 2012 },
        ]

        total_dev = self.portfolio.get_total_development(fonds)
        for result, expected in zip(total_dev["development"], expected_result):
            self.assertEquals(result, expected)

    def test_deposit_raises_exception(self):
        """deposit should raise exception if fond with ticker is not registered"""
        with self.assertRaises(InvalidUsage):
             self.portfolio.deposit("garbage", date(2016, 1, 1), 100)

    def test_deposit(self):
        """deposit should register a deposit in the right fond"""
        fond = Mock(spec=Fond)
        portfolio = Portfolio(1, {"T1": fond})
        portfolio.deposit("T1", date(2016, 1, 1), 1234)

        fond.deposit.assert_called_once_with(1234, date(2016, 1, 1))

    def test_delete_deposit_raises_exception(self):
        """deposit should raise exception if fond with ticker is not registered"""
        with self.assertRaises(InvalidUsage):
             self.portfolio.delete_deposit("garbage", date(2016, 1, 1))

    def test_delete_deposit(self):
        """deposit should delete a deposit in the right fond"""
        fond = Mock(spec=Fond)
        portfolio = Portfolio(1, {"T1": fond})
        portfolio.delete_deposit("T1", date(2016, 1, 1))

        fond.delete_deposit.assert_called_once_with(date(2016, 1, 1))

    def test_add_fond_raises_exception(self):
        """add_fond should raise exception if fond is already registered"""
        portfolio = Portfolio(1, {"T1": Mock(spec=Fond)})
        with self.assertRaises(InvalidUsage):
            portfolio.add_fond("T1", "Ticker 1")

    def test_add_fond(self):
        """add_fond should add fond to portfolio"""
        portfolio = Portfolio(1, {})
        portfolio.add_fond("T1", "Ticker 1")
        self.assertTrue("T1" in portfolio.portfolio.keys())

if __name__ == "__main__":
    unittest.main()
