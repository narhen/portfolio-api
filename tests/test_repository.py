#!/usr/bin/env python

import unittest
from mock import PropertyMock, MagicMock, patch, Mock
from random import randint, uniform
from datetime import date, datetime, timedelta

from components.Portfolio import Portfolio
from components.repository import Repository
from components.error import InvalidUsage, InvalidDate

class TestFond(unittest.TestCase):
    @patch('components.repository.Database')
    def test_get_portfolio(self, db_mock):
        """get_portfolio returns None if portfolio was not found"""
        repo = Repository()

        db_instance = db_mock.return_value
        db_instance.get_portfolio.return_value = None
        self.assertIsNone(repo.get_portfolio("123"))

        db_instance.get_portfolio.return_value = (1, [])
        self.assertIsInstance(repo.get_portfolio("123"), Portfolio)

    @patch('components.repository.Database')
    def test_put_portfolio_raises_exception(self, db_mock):
        """put_portfolio saves portfolio to db"""
        repo = Repository()

        db_instance = db_mock.return_value
        db_instance.get_user_info_by_iser_id.return_value = {}

        repo.put_portfolio(Portfolio(1, {}))
        db_instance.save_portfolio.assert_called_once()

    @patch('components.repository.Database')
    def test_get_user_info(self, db_mock):
        """get_user_info returns None if user was not found"""
        repo = Repository()

        db_instance = db_mock.return_value
        db_instance.get_user_info.return_value = None
        self.assertIsNone(repo.get_user_info("123"))

    @patch('components.repository.Database')
    def test_get_user_info_returns_user(self, db_mock):
        """get_user_info returns user data if user was found"""
        repo = Repository()
        db_instance = db_mock.return_value
        db_instance.get_user_info.return_value = (1, {"name": "Kari"})
        self.assertEquals(repo.get_user_info("123"), (1, {"name": "Kari"}))

    @patch('components.repository.Database')
    def test_generate_session_key(self, db_mock):
        """generate_session_key returns a session key if user was found"""
        repo = Repository()

        db_instance = db_mock.return_value

        db_instance.get_user_info_by_google_id.return_value = (1, {"id": 12345})
        db_instance.new_session.return_value = "1234abcd"
        
        self.assertEquals(repo.generate_session_key({"id": 12345}), "1234abcd")

        db_instance.new_session.assert_called_once()
        db_instance.create_user.assert_not_called()

    @patch('components.repository.Database')
    def test_generate_session_key_creates_user(self, db_mock):
        """generate_session_key creates a new user if not found"""
        repo = Repository()
        db_instance = db_mock.return_value

        db_instance.get_user_info_by_google_id.return_value = None
        db_instance.new_session.return_value = "1234"

        self.assertEquals(repo.generate_session_key({"id": 123}), "1234")

        db_instance.new_session.assert_called_once()
        db_instance.create_user.assert_called_once()

    @patch('components.repository.Database')
    def test_delete_session_key_invalid_session(self, db_mock):
        """delete_session_key should not not perform any database operations if session key was not fond"""
        repo = Repository()
        db_instance = db_mock.return_value

        db_instance.get_session.return_value = None
        repo.delete_session_key("1234")

        db_instance.delete_sessions_for_user.assert_not_called()

    @patch('components.repository.Database')
    def test_delete_session_key_valid_session(self, db_mock):
        """delete_session_key delete session key if session key is valid"""
        repo = Repository()
        db_instance = db_mock.return_value

        db_instance.get_session.return_value = ("1234", 1, 4321)
        repo.delete_session_key("1234")

        db_instance.delete_sessions_for_user.assert_called_once()

    @patch('components.repository.Database')
    def test_valid_session_key(self, db_mock):
        """valid_session_key returns True if session key is valid"""
        repo = Repository()
        db_instance = db_mock.return_value

        db_instance.get_session.return_value = ("1234", 1, 4321)
        self.assertTrue(repo.valid_session_key("1234"))

        db_instance.get_session.return_value = None
        self.assertFalse(repo.valid_session_key("1234"))
