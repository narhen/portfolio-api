#!/usr/bin/python

from settings import db_credentials
from db import Database
from Fond import Fond
from Portfolio import Portfolio
import json

class Repository:
    def __init__(self):
        self.db = Database(**db_credentials)

    def get_portfolio(self, session_token):
        data = self.db.get_portfolio(session_token)
        if not data:
            return None

        if not "user" in data:
            raise InvalidUsage("missing data ('user') in portfolio")
        if not "user_id" in data["user"]:
            raise InvalidUsage("missing data ('user_id') in portfolio")

        fonds = {fond_data["ticker"]: Fond(**fond_data) for fond_data in data.get("fonds", [])}
        return Portfolio(data["user"]["user_id"], fonds)

    def put_portfolio(self, portfolio):
        user_info = self.db.get_user_info_by_user_id(portfolio.user_id)
        user_info["fonds"] = portfolio.to_json()
        self.db.save_user(json.dumps(user_info, default=portfolio.json_serializer), portfolio.user_id)

    def get_user_info(self, session_token):
        user_info = self.db.get_user_info(session_token)
        if not user_info:
            return None
        return user_info["user"]

    def _get_user_info_by_google_id(self, google_id):
        return self.db.get_user_info_by_google_id(google_id)

    def create_user(self, user_info):
        return self.db.create_user(user_info)

    def generate_session_key(self, user_data):
        user_info = self._get_user_info_by_google_id(user_data["id"])
        if user_info:
            user_id = user_info["user_id"]
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
