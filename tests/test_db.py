#!/usr/bin/env python

import unittest
import json
import time
from mock import PropertyMock, MagicMock, patch, Mock
from random import randint, uniform
from datetime import date, datetime, timedelta

from settings import test_db_credentials
from components.db import Database

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db = Database(**test_db_credentials)

    def delete_all_from_table(self, table):
        self.db._execute_query("DELETE FROM {}.{}".format(test_db_credentials["schema"], table))

    def test_get_session_invalid_uuid(self):
        """get_session should return None if uuid is invalid"""
        self.assertIsNone(self.db.get_session("jklsdfjkldsf"))

    def test_get_session(self):
        """get_session should return a tuple containing session data"""
        self.assertIsNone(self.db.get_session("jklsdfjkldsf"))

        uuid = self.db.new_session(1)
        key, user_id, created = self.db.get_session(uuid)
        self.assertEquals(user_id, 1)
        self.assertEquals(created.replace(microsecond=0), datetime.now().replace(microsecond=0))
        self.assertIsInstance(key, str)

        self.delete_all_from_table(self.db.session_table)

    def test_delete_sessions_for_user(self):
        """delete_sessions_for_user deletes all sessions for a user"""
        user_id = 1

        key = self.db.new_session(user_id)
        self.assertIsNotNone(self.db.get_session(key))

        self.db.delete_sessions_for_user(user_id)
        self.assertIsNone(self.db.get_session(key))

        self.delete_all_from_table(self.db.session_table)

    def test_new_session_only_allows_one_session_per_user(self):
        """new_session only allows one session_per user"""
        user_id = 1

        key = self.db.new_session(user_id)
        key2 = self.db.new_session(user_id)
        self.assertIsNone(self.db.get_session(key))
        self.assertIsNotNone(self.db.get_session(key2))

        self.delete_all_from_table(self.db.session_table)

    def test_create_user(self):
        """create_user should create a new user"""
        user_info = {"id": "123124124", "name": "Kari", "family_name": "Nordmann"}
        user_id = self.db.create_user(user_info)
        self.assertIsNotNone(self.db.get_user_info_by_user_id(user_id))

        self.delete_all_from_table(self.db.table)

    def test_get_user_info_returns_none_on_error(self):
        """get_user_info should return None if session token is invalid"""
        user_info = {"id": "123124124", "name": "Kari", "family_name": "Nordmann"}
        user_id = self.db.create_user(user_info)
        self.assertIsNone(self.db.get_user_info("123123123"))

        self.delete_all_from_table(self.db.table)

    def test_get_user_info(self):
        """get_user_info should return user info on success"""
        user_info = {"id": "123124124", "name": "Kari", "family_name": "Nordmann"}
        user_id = self.db.create_user(user_info)
        session_key = self.db.new_session(user_id)

        user_info["user_id"] = user_id
        self.assertEquals(self.db.get_user_info(session_key), {"user": user_info})

        self.delete_all_from_table(self.db.table)

    def test_get_user_info_by_user_id_returns_none_on_error(self):
        """get_user_info_by_user_id should return None if user_id does not exists"""
        self.assertIsNone(self.db.get_user_info_by_user_id(999999999999))

        self.delete_all_from_table(self.db.table)

    def test_get_user_info_by_user_id(self):
        """get_user_info_by_user_id should user info if user_id exists"""
        user_info = {"id": "123124124", "name": "Kari", "family_name": "Nordmann"}
        user_id = self.db.create_user(user_info)

        user_info["user_id"] = user_id
        self.assertEquals(self.db.get_user_info_by_user_id(user_id), {"user": user_info})

        self.delete_all_from_table(self.db.table)

    def test_get_user_info_by_google_id(self):
        """get_user_info_by_google_id should return user info if user exists"""
        google_id = u"123123123"
        user_info = {u"id": google_id, u"name": u"Kari", u"family_name": u"Nordmann"}
        user_id = self.db.create_user(user_info)

        user_info["user_id"] = user_id
        self.assertEquals(self.db.get_user_info_by_google_id(google_id), user_info)

        self.delete_all_from_table(self.db.table)

    def test_get_user_info_by_google_id_return_none_on_error(self):
        """get_user_info_by_google_id should return None if user does not exist"""
        self.assertIsNone(self.db.get_user_info_by_google_id("123123"))

        self.delete_all_from_table(self.db.table)

    def test_save_user_updates_user(self):
        """save_user should update user information if user exists"""
        user_info = {u"id": u"123123123", u"name": u"Kari", u"family_name": u"Nordmann"}
        user_id = self.db.create_user(user_info)

        user_info[u"user_id"] = user_id
        self.assertEquals(self.db.get_user_info_by_user_id(user_id), {u"user": user_info})

        user_info[u"middle_name"] = u"Tarzan"
        self.db.save_user(user_info, user_id)

        self.assertEquals(self.db.get_user_info_by_user_id(user_id), {u"user": user_info})

        self.delete_all_from_table(self.db.table)
