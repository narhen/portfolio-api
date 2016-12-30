#!/usr/bin/env python

import unittest
import json
from mock import PropertyMock, MagicMock, patch, Mock
from random import randint, uniform
from datetime import date, datetime, timedelta

from components.repository import Repository
from components.Portfolio import Portfolio
import components.controller as controller
from components.controller import app

class TestFond(unittest.TestCase):

    def setUp(self):
        controller.repo = Mock(spec=Repository)
        self.app = app.test_client()
        self.app.testing = True

    def test_userinfo(self):
        """GET /userinfo should return user info if a valid session key is provided"""
        result = self.app.get("/userinfo")
        self.assertEquals(result.status_code, 401)

        controller.repo.get_user_info.return_value = {"user_id": 1}
        controller.repo.valid_session_key.return_value = True
        result = self.app.get("/userinfo", headers={"api-key": "123"})
        self.assertEquals(result.status_code, 200)
        self.assertEquals(json.loads(result.get_data()), {"user_id": 1})

    def test_summary(self):
        """GET /summary should return portfolio summary for a given user"""
        result = self.app.get("/summary")
        self.assertEquals(result.status_code, 401)

        controller.repo.get_portfolio.return_value = Portfolio(1, {})
        controller.repo.valid_session_key.return_value = True
        result = self.app.get("/summary", headers={"api-key": "123"})
        self.assertEquals(result.status_code, 200)

        data = json.loads(result.get_data())
        for field in ["development", "total_deposited", "ticker", "name"]:
            self.assertIn(field, data[0].keys())

    def test_addfond(self):
        """POST /addfond should return 204 on success"""

        result = self.app.post("/addfond")
        self.assertEquals(result.status_code, 401)

        portfolio_mock = Mock(spec=Portfolio)
        controller.repo.get_portfolio.return_value = portfolio_mock
        controller.repo.valid_session_key.return_value = True

        result = self.app.post("/addfond",
            headers={"api-key": "123"},
            data=json.dumps({"ticker": "T1", "name": "Ticker 1"}),
            content_type="application/json")
        self.assertEquals(result.status_code, 204)
        portfolio_mock.add_fond.assert_called_once()

    def test_addfond_returns_401_on_validation_error(self):
        """ POST /addfond with an invalid json request should return 400"""
        portfolio_mock = Mock(spec=Portfolio)
        controller.repo.get_portfolio.return_value = portfolio_mock
        controller.repo.valid_session_key.return_value = True

        result = self.app.post("/addfond",
            headers={"api-key": "123"},
            data=json.dumps({"sticker": "T1"}),
            content_type="application/json")
        self.assertEquals(result.status_code, 400)
        portfolio_mock.add_fond.assert_not_called()

    def test_add_deposit(self):
        """PUT deposit should return 204 on success"""
        result = self.app.put("/deposit")
        self.assertEquals(result.status_code, 401)

        portfolio_mock = Mock(spec=Portfolio)
        controller.repo.get_portfolio.return_value = portfolio_mock

        to_deposit = json.dumps({
            "date": "2016-01-01", 
            "fonds": [{"ticker": "T1", "amount": 1000}]
        })

        result = self.app.put("/deposit",
            headers={"api-key": "123"},
            data=to_deposit,
            content_type='application/json')
        self.assertEquals(result.status_code, 204)
        portfolio_mock.deposit.assert_called_once()

    def test_deletedeposit(self):
        """DELETE deposit should return 204 on success"""
        result = self.app.delete("/deposit")
        self.assertEquals(result.status_code, 401)

        portfolio_mock = Mock(spec=Portfolio)
        controller.repo.get_portfolio.return_value = portfolio_mock

        to_deposit = json.dumps({
            "date": "2016-01-01", 
            "tickers": ["T1"]
        })

        result = self.app.delete("/deposit",
            headers={"api-key": "123"},
            data=to_deposit,
            content_type='application/json')
        self.assertEquals(result.status_code, 204)
        portfolio_mock.delete_deposit.assert_called_once()
