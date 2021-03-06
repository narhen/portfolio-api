#!/usr/bin/python

from settings import db_credentials
from db import Database
from Fond import Fond
from Portfolio import Portfolio
import json

from error import InvalidUsage

class Repository:
    def __init__(self):
        self.db = Database(**db_credentials)

    def get_portfolio(self, session_token):
        result = self.db.get_portfolio(session_token)
        if not result:
            return None

        user_id, data = result

        fonds = {fond_data["ticker"]: Fond(**fond_data) for fond_data in data}
        return Portfolio(user_id, fonds)

    def put_portfolio(self, portfolio):
        self.db.save_portfolio(portfolio.to_json(), portfolio.user_id)

    def get_user_info(self, session_token):
        return self.db.get_user_info(session_token)

    def _get_user_info_by_google_id(self, google_id):
        return self.db.get_user_info_by_google_id(google_id)

    def create_user(self, user_info):
        return self.db.create_user(user_info)

    def generate_session_key(self, user_data):
        user_info = self._get_user_info_by_google_id(user_data["id"])
        if user_info:
            user_id, data = user_info
        else:
            user_id = self.create_user(user_data)

        return self.db.new_session(user_id)

    def delete_session_key(self, session_key):
        session = self.db.get_session(session_key)
        if not session:
            return None

        key, user_id, created = session
        self.db.delete_sessions_for_user(user_id)

    def valid_session_key(self, session_key):
        return self.db.get_session(session_key) is not None

    def close(self):
        self.db.close()
