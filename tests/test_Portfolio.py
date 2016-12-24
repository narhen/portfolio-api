#!/usr/bin/env python

import unittest
from mock import MagicMock, patch
import datetime

from components.Portfolio import Portfolio
from components.error import InvalidUsage, InvalidDate

class TestPortfolio(unittest.TestCase):
    basic_data = {"user": {"user_id": 1}}
    data_with_fonds = {
        "user": {"user_id": 1},
        "fonds": [
            {
                "ticker": "T1",
                "deposits": [{"date": "2016-01-01", "amount": 100},
                             {"date": "2016-02-01", "amount": 100},
                             {"date": "2016-03-01", "amount": 100}]

            },
            {
                "ticker": "T2",
                "deposits": [{"date": "2016-01-01", "amount": 100},
                             {"date": "2016-03-01", "amount": 200}]

            }
        ]
    }

    def test___init___raises_exception_on_failure(self):
        """__init__ should raise an exception if data does not contain a user_id"""
        with self.assertRaises(InvalidUsage):
            Portfolio({})

        with self.assertRaises(InvalidUsage):
            Portfolio({"user": {}})

    def test__string_to_date(self):
        """_string_to_date converts a string to an datetime.date object"""
        portfolio = Portfolio(basic_data)
        self.assertTrue(isinstance(portfolio._string_to_date("2016-01-01"), datetime.date))
        self.assertTrue(isinstance(portfolio._string_to_date(datetime.date(2016, 1, 1)), datetime.date))


    def test__string_to_date(self):
        """_string_to_date raises an exception if type of date is not string or datetime.date"""
        portfolio = Portfolio(self.basic_data)
        with self.assertRaises(InvalidDate):
            portfolio = portfolio._string_to_date(dict())

    def test_get_deposit_by_date(self):
        """get_deposit_by_date returns the sum of all deposits for a given date"""

        portfolio = Portfolio(self.data_with_fonds)
        self.assertEquals(portfolio.get_deposits_by_date("2016-01-01"), 200)
        self.assertEquals(portfolio.get_deposits_by_date("2016-02-01"), 100)
        self.assertEquals(portfolio.get_deposits_by_date("2016-03-01"), 300)
        self.assertEquals(portfolio.get_deposits_by_date("2016-04-01"), 0)


if __name__ == "__main__":
    unittest.main()
