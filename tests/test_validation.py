#!/usr/bin/env python

import unittest
from mock import PropertyMock, MagicMock, patch, Mock
from random import randint, uniform
from datetime import date, datetime, timedelta

from components import validation
from components.error import InvalidUsage, InvalidDate

class Request:
    def __init__(self, method, json):
        self.method = method.upper()
        self.json = json
        self.is_json = True

    def get_json(self):
        return self.json

class TestFond(unittest.TestCase):

    def test_validate_deposit_put(self):
        """validate_deposit for PUT returns False if request does not contain required fields"""
        self.assertFalse(validation.validate_deposit(
            Request("PUT", {
                "date": "2016-01-01",
                "fonds": [{
                    "ticker": "T1",
                }]
            }))
        )

        self.assertFalse(validation.validate_deposit(
            Request("PUT", {
                "date": "2016-01-01",
                "fonds": [{
                    "amount": 100,
                }]
            }))
        )

        self.assertFalse(validation.validate_deposit(
            Request("PUT", {
                "date": "2016-01-01",
                "fonds": [{}]
            }))
        )

        self.assertFalse(validation.validate_deposit(
            Request("PUT", {
                "date": "2016-01-01",
            }))
        )

        self.assertTrue(validation.validate_deposit(
            Request("PUT", {
                "date": "2016-01-01",
                "fonds": [{
                    "ticker": "T1",
                    "amount": 100,
                }]
            }))
        )

    def test_validate_deposit_delete(self):
        """validate_deposit for DELETE returns False if request does not contain required fields"""
        self.assertFalse(validation.validate_deposit(
            Request("DELETE", {
                "date": "2016-01-01",
            }))
        )

        self.assertFalse(validation.validate_deposit(
            Request("DELETE", {
                "tickers": ["T1"]
            }))
        )

        self.assertTrue(validation.validate_deposit(
            Request("DELETE", {
                "date": "2016-01-01",
                "tickers": ["T1"]
            }))
        )
