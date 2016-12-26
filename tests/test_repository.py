#!/usr/bin/env python

import unittest
from mock import PropertyMock, MagicMock, patch, Mock
from random import randint, uniform
from datetime import date, datetime, timedelta

from components.Portfolio import Portfolio
from components.repository import Repository
from components.error import InvalidUsage, InvalidDate

class TestFond(unittest.TestCase):
    @patch('components.db.Database.get_portfolio')
    def test_get_portfolio(self, db_mock):
        """get_portfolio returns None if portfolio was not fount"""
        repo = Repository()
        db_mock.return_value = None
        self.assertIsNone(repo.get_portfolio("123"))

        db_mock.return_value = {"user": {"user_id": 1}}
        self.assertIsInstance(repo.get_portfolio("123"), Portfolio)

    @patch('components.db.Database.get_portfolio')
    def test_get_portfolio_raises_exception(self, db_mock):
        "get_portfolio raises an exception if portfolio does not contain needed data"""
        repo = Repository()

        db_mock.return_value = {"fonds": []}
        with self.assertRaises(InvalidUsage):
            repo.get_portfolio("123")

        db_mock.return_value = {"user": {}}
        with self.assertRaises(InvalidUsage):
            repo.get_portfolio("123")

    @patch('components.db.Database.get_user_info_by_user_id')
    @patch('components.db.Database.save_user')
    def test_get_portfolio_raises_exception(self, save_mock, get_user_mock):
        """put_portfolio saves portfolio to db"""
        repo = Repository()
        get_user_mock.return_value = {}

        repo.put_portfolio(Portfolio(1, {}))
        save_mock.assert_called_once()

    @patch('components.db.Database.get_user_info')
    def test_get_user_info(self, get_user_mock):
        """get_user_info returns None if user was not found"""
        repo = Repository()
        get_user_mock.return_value = None
        self.assertIsNone(repo.get_user_info("123"))

    @patch('components.db.Database.get_user_info')
    def test_get_user_info_returns_user(self, get_user_mock):
        """get_user_info returns user data if user was found"""
        repo = Repository()
        get_user_mock.return_value = {"user": {"user_id": 1}}
        self.assertEquals(repo.get_user_info("123"), {"user_id": 1})

    @patch('components.db.Database.create_user')
    @patch('components.db.Database.get_user_info_by_google_id')
    @patch('components.db.Database.new_session')
    def test_get_user_info_returns_user(self, new_session_mock, google_user_info_mock, create_user_mock):
        """get_user_info returns user data if user was found"""
        repo = Repository()

        google_user_info_mock.return_value = {"user_id": 1}
        new_session_mock.return_value = "1234"
        
        self.assertEquals(repo.generate_session_key({"id": 123}), "1234")

        new_session_mock.assert_called_once()
        create_user_mock.assert_not_called()

    @patch('components.db.Database.create_user')
    @patch('components.db.Database.get_user_info_by_google_id')
    @patch('components.db.Database.new_session')
    def test_get_user_info_creates_user(self, new_session_mock, google_user_info_mock, create_user_mock):
        """get_user_info creates a new user if not found"""
        repo = Repository()

        google_user_info_mock.return_value = None
        new_session_mock.return_value = "1234"

        self.assertEquals(repo.generate_session_key({"id": 123}), "1234")

        new_session_mock.assert_called_once()
        create_user_mock.assert_called_once()

    @patch('components.db.Database.delete_sessions_for_user')
    @patch('components.db.Database.get_session')
    def test_delete_session_key_invalid_session(self, get_session_mock, delete_sessions_mock):
        """delete_session_key should not not perform any database operations if session key was not fond"""
        repo = Repository()

        get_session_mock.return_value = None
        repo.delete_session_key("1234")

        delete_sessions_mock.assert_not_called()

    @patch('components.db.Database.delete_sessions_for_user')
    @patch('components.db.Database.get_session')
    def test_delete_session_key_valid_session(self, get_session_mock, delete_sessions_mock):
        """delete_session_key delete session key if session key is valid"""
        repo = Repository()

        get_session_mock.return_value = ("1234", 1, 4321)
        repo.delete_session_key("1234")

        delete_sessions_mock.assert_called_once()

    @patch('components.db.Database.get_session')
    def test_valid_session_key(self, get_session_mock):
        """valid_session_key returns True if session key is valid"""
        repo = Repository()

        get_session_mock.return_value = ("1234", 1, 4321)
        self.assertTrue(repo.valid_session_key("1234"))

        get_session_mock.return_value = None
        self.assertFalse(repo.valid_session_key("1234"))
