#!/usr/bin/env python

import unittest
from mock import PropertyMock, MagicMock, patch, Mock
from random import randint, uniform
from datetime import date, datetime, timedelta

from components.Fond import Fond
from components.error import InvalidUsage, InvalidDate

class TestFond(unittest.TestCase):
    def test___init__(self):
        """__init__ should raise an exception if ticker is not specified"""
        with self.assertRaises(InvalidUsage):
             Fond()

    def test___eq__(self):
        """__eq__ compares Fond objects by ticker"""
        class Tmp:
            def __init__(self, ticker):
                self.ticker = ticker

        self.assertTrue(Fond("T1") == Fond("T1"))
        self.assertFalse(Fond("T1") == Fond("T2"))
        self.assertFalse(Fond("T1") == Tmp("T1"))

    def generate_quotes(self, from_date, num_quotes):
        quotes = [{"quote_date": from_date, "close": randint(10, 1000)}]
        for i in range(1, num_quotes):
            quotes += [{
                "quote_date": from_date + timedelta(days=i),
                "close": quotes[i - 1]["close"] * uniform(0.75, 1.25)
            }]

        return quotes

    @patch('components.Fond.Investment.get_quotes')
    def test_quotes(self, mock):
        """quotes should return quotes starting from the date of the first deposit"""
        mock.return_value = self.generate_quotes(date(2016, 1, 1), 21)
        fond = Fond("T1", "ticker 1", [
            {"date": "2016-1-10", "amount": 1000},
            {"date": "2016-1-20", "amount": 1000}
        ])
        self.assertEquals(len(fond.quotes), 12)
        self.assertEquals(fond.quotes[0]["quote_date"], date(2016, 1, 1))

    @patch('components.Fond.Investment.get_quotes')
    def test_quotes(self, mock):
        """quotes should the last 10 quotes if no deposit is registered"""
        mock.return_value = self.generate_quotes(date(2016, 1, 1), 30)
        fond = Fond("T1", "ticker 1")
        self.assertEquals(len(fond.quotes), 10)
        self.assertEquals(fond.quotes[0]["quote_date"], date(2016, 1, 21))

    def test__string_to_date(self):
        """_string_to_date converts a string to an datetime.date object"""
        fond = Fond("T1", "ticker 1")
        self.assertTrue(isinstance(fond._string_to_date("2016-01-01"), date))
        self.assertTrue(isinstance(fond._string_to_date(date(2016, 1, 1)), date))

    def test__string_to_date_raises_exception(self):
        """_string_to_date raises an exception if type of date is not string or datetime.date"""
        fond = Fond("T1", "ticker 1")
        with self.assertRaises(InvalidDate):
             fond._string_to_date(dict())

    def test_deposit_raises_exception(self):
        """deposit should raise an exception if a deposit is already registered for a date"""
        fond = Fond("T1", "ticker 1", [{"date": "2016-1-1", "amount": 1000}])
        with self.assertRaises(InvalidUsage):
            fond.deposit(1000, date(2016, 1, 1))

    def test_deposit(self):
        """deposit adds a deposit"""
        fond = Fond("T1", "ticker 1")
        fond.deposit(1000, date(2016, 2, 1))
        fond.deposit(1000, date(2016, 1, 1))
        fond.deposit(1000, date(2016, 3, 1))
        self.assertEquals(fond.deposits, [
            {"date": date(2016, 1, 1), "amount": 1000},
            {"date": date(2016, 2, 1), "amount": 1000},
            {"date": date(2016, 3, 1), "amount": 1000},
        ])

    def test_delete_deposit(self):
        """delete_deposit deletes a deposit from the deposit list if it exists"""
        fond = Fond("T1", "ticker 1", [
            {"date": "2016-1-1", "amount": 1000},
            {"date": "2016-2-1", "amount": 1000},
        ])
        fond.delete_deposit(date(2016, 2, 1))
        self.assertEquals(len(fond.deposits), 1)

        fond.delete_deposit("2016-1-1")
        self.assertEquals(len(fond.deposits), 0)

    def test_get_quote_entry_by_date(self):
        """get_quote_entry_by_date should return an index of a quote entry based on date"""
        fond = Fond("T1", "ticker 1")

        quotes = self.generate_quotes(date(2016, 1, 1), 21)
        self.assertIsNotNone(fond.find_quote_entry_by_date(quotes, date(2016, 1, 10)))
        self.assertEquals(fond.find_quote_entry_by_date(quotes, date(2016, 1, 1)), 0)
        self.assertEquals(fond.find_quote_entry_by_date(quotes, date(2016, 1, 10)), 9)
        self.assertIsNone(fond.find_quote_entry_by_date(quotes, date(2016, 1, 31)))

    def test_get_deposit_by_date(self):
        """get_deposit_by_date should return the deposit as an integer for a given date"""
        fond = Fond("T1", "ticker 1", [
            {"date": "2016-1-1", "amount": 1000},
            {"date": "2016-2-1", "amount": 2000},
        ])
        self.assertEquals(fond.get_deposit_by_date("2016-1-1"), 1000)
        self.assertEquals(fond.get_deposit_by_date(date(2016, 2, 1)), 2000)
        self.assertEquals(fond.get_deposit_by_date(date(2016, 3, 1)), 0)

    def test__price_development_percent(self):
        """_price_developement_percent should return the change in percent between two dates"""
        fond = Fond("T1", "Ticker 1")
        self.assertEquals(fond._price_developement_percent({"close": 100}, {"close": 100}), 1)
        self.assertEquals(fond._price_developement_percent({"close": 50}, {"close": 100}), 2)
        self.assertEquals(fond._price_developement_percent({"close": 100}, {"close": 50}), 0.5)

    @patch('components.Fond.Investment.get_quotes')
    def test_get_development(self, mock):
        """get_development should return a list of dictionaries containing day-to-day value"""
        mock.return_value = self.generate_quotes(date(2016, 1, 1), 60)
        fond = Fond("T1", "ticker 1", [
            {"date": "2016-1-1", "amount": 1000},
            {"date": "2016-2-1", "amount": 2000},
        ])
        development = fond.get_developement()
        self.assertEquals(len(development), 60)
        self.assertEquals(development[0], {"date": date(2016, 1, 1), "value": 1000, "deposit": 1000})
        for entry in development:
            self.assertIn("date", entry)
            self.assertIn("value", entry)
            self.assertIn("deposit", entry)
            self.assertEquals(len(entry.keys()), 3)

    @patch('components.Fond.Investment.get_quotes')
    def test_get_summary(self, mock):
        """get_summary should return a dictionary containing summary data"""
        mock.return_value = self.generate_quotes(date(2016, 1, 1), 60)
        fond = Fond("T1", "ticker 1", [
            {"date": "2016-1-1", "amount": 1000},
            {"date": "2016-2-1", "amount": 2000},
        ])
        summary = fond.get_summary()
        self.assertEquals(set(summary.keys()), set(["ticker", "name", "development", "total_deposited"]))
        self.assertEquals(summary["ticker"], "T1")
        self.assertEquals(summary["name"], "ticker 1")
        self.assertEquals(summary["total_deposited"], 3000)
