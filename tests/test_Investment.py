#!/usr/bin/env python

import unittest
import requests_mock
from mock import PropertyMock, MagicMock, patch, Mock
from random import randint, uniform
from datetime import date, datetime, timedelta
from time import mktime, time

from components.Investment import Investment
from components.error import InvalidUsage

class TestFond(unittest.TestCase):
    csvdata = """quote_date,paper,exch,open,high,low,close,volume,value
20161222,T1,Fonds,1814.05,1814.05,1814.05,1814.05,0,0
20161221,T1,Fonds,1807.52,1807.52,1807.52,1807.52,0,0
20161220,T1,Fonds,1814.28,1814.28,1814.28,1814.28,0,0
"""
    parsed_csvdata = [{
        "quote_date": date(year=2016, month=12, day=22),
        "paper": "T1",
        "exch": "Fonds",
        "open": '1814.05',
        "high": '1814.05',
        "low": '1814.05',
        "close": '1814.05',
        "volume": '0',
        "value": '0'
    }, {
        "quote_date": date(year=2016, month=12, day=21),
        "paper": "T1",
        "exch": "Fonds",
        "open": '1807.52',
        "high": '1807.52',
        "low": '1807.52',
        "close": '1807.52',
        "volume": '0',
        "value": '0'
    }, {
        "quote_date": date(year=2016, month=12, day=20),
        "paper": "T1",
        "exch": "Fonds",
        "open": '1814.28',
        "high": '1814.28',
        "low": '1814.28',
        "close": '1814.28',
        "volume": '0',
        "value": '0'
    }]

    @requests_mock.mock()
    def test_get_quotes_from_remote(self, req_mock):
        """get_quotes from remote should fetch quotes and parse as csv"""
        inv = Investment("T1")
        req_mock.get(inv.quotes_source_url, text=self.csvdata)
        self.assertEquals(inv._get_quotes_from_remote(), {
            "fetch_time": int(time()),
            "quotes": self.parsed_csvdata
        })

    def test__fill_date_holes_in_quotes(self):
        """_fill_date_holes_in_quotes fills in missing entries in a sequence of quotes"""
        inv = Investment("T1")
        incomplete_quotes = [{
            "quote_date": date(2016, 1, 1),
            "close": 10
        }, {
            "quote_date": date(2016, 1, 3),
            "close": 12
        }]

        self.assertEquals(inv._fill_date_holes_in_quotes(incomplete_quotes), [
        {
            "quote_date": date(2016, 1, 1),
            "close": 10
        }, {
            "quote_date": date(2016, 1, 2),
            "close": 10
        }, {
            "quote_date": date(2016, 1, 3),
            "close": 12
        }])

    @patch('components.Investment.Investment._get_date_today')
    def test__quotes_has_expired(self, mock):
        """_quotes_has_expired_should return False if today is a week end day"""
        mock.return_value = datetime(year=2016, month=1, day=2, hour=12)
        inv = Investment("T1")
        quotes = { "fetch_time": mktime(datetime(year=2016, month=1, day=1).timetuple())}

        self.assertFalse(inv._quotes_has_expired(quotes))

    @patch('components.Investment.Investment._get_date_today')
    def test__quotes_has_expired(self, mock):
        """_quotes_has_expired_should return False if fetch time was after 18:00 today"""
        mock.return_value = datetime(year=2016, month=1, day=4)
        inv = Investment("T1")
        quotes = { "fetch_time": mktime(datetime(year=2016, month=1, day=4, hour=19).timetuple())}

        self.assertFalse(inv._quotes_has_expired(quotes))

    @patch('components.Investment.Investment._get_date_today')
    def test__quotes_has_expired(self, mock):
        """_quotes_has_expired_should return False if fetch time is within the last 30 minutes"""
        mock.return_value = datetime(year=2016, month=1, day=4, hour=12, minute=10)
        inv = Investment("T1")
        quotes = { "fetch_time": mktime(datetime(year=2016, month=1, day=4, hour=12, minute=0).timetuple())}

        self.assertFalse(inv._quotes_has_expired(quotes))

    @patch('components.Investment.Investment._get_date_today')
    def test__quotes_has_expired(self, mock):
        """_quotes_has_expired_should return True if fetch time was over 30 minutes ago"""
        mock.return_value = datetime(year=2016, month=1, day=4, hour=12, minute=40)
        inv = Investment("T1")
        quotes = { "fetch_time": mktime(datetime(year=2016, month=1, day=4, hour=12, minute=0).timetuple())}

        self.assertTrue(inv._quotes_has_expired(quotes))

    @patch('components.Investment.Investment._get_quotes_from_remote')
    def test__quotes_has_expired(self, mock):
        """_quotes_has_expired_should return True if fetch time was over 30 minutes ago"""
        mock.return_value = datetime(year=2016, month=1, day=4, hour=12, minute=40)
        inv = Investment("T1")
        quotes = { "fetch_time": mktime(datetime(year=2016, month=1, day=4, hour=12, minute=0).timetuple())}

        self.assertTrue(inv._quotes_has_expired(quotes))

    @patch('components.Investment.Investment._get_from_cache')
    @patch('components.Investment.Investment._get_quotes_from_remote')
    def test_get_quotes(self, cache_mock, remote_mock):
        """get_quotes should raise an exception if ticker is not valid"""
        inv = Investment("T1")

        cache_mock.return_value = None
        remote_mock.return_value = None

        with self.assertRaises(InvalidUsage):
             inv.get_quotes()

    @patch('components.Investment.Investment._get_from_cache')
    @patch('components.Investment.Investment._get_quotes_from_remote')
    @patch('components.Investment.Investment._quotes_has_expired')
    def test_get_quotes(self, cache_mock, remote_mock, expired_mock):
        """get_quotes should fetch quotes if expired"""
        inv = Investment("T1")

        cache_mock.return_value = {"fetch_time": 1234, "quotes": [1, 2, 3]}
        expired_mock.return_value = True
        remote_mock.return_value = {"fetch_time": 12345, "quotes": []}
        expired_mock.return_value = False

        self.assertEquals(inv.get_quotes(), [])

    @patch('components.Investment.Investment._get_from_cache')
    @patch('components.Investment.Investment._get_quotes_from_remote')
    @patch('components.Investment.Investment._quotes_has_expired')
    def test_get_quotes(self, expired_mock, remote_mock, cache_mock):
        """get_quotes should retrieve quotes from cache if not expired"""
        inv = Investment("T1")
        quotes = [
            {"quote_date": date(year=2016, month=1, day=5), "close": 100},
            {"quote_date": date(year=2016, month=1, day=4), "close": 101},
            {"quote_date": date(year=2016, month=1, day=3), "close": 102},
            {"quote_date": date(year=2016, month=1, day=2), "close": 103},
            {"quote_date": date(year=2016, month=1, day=1), "close": 104},
        ]

        cache_mock.return_value = {"fetch_time": 1234, "quotes": quotes[:3]}
        expired_mock.return_value = False

        self.assertEquals(inv.get_quotes(), quotes[:3][::-1])

        expired_mock.return_value = True
        remote_mock.return_value = {"fetch_time": 12345, "quotes": quotes}

        self.assertEquals(inv.get_quotes(), quotes[::-1])

# TODO add test that checks that get_quotes fills in holes in quotes
