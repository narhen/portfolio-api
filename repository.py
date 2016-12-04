#!/usr/bin/python

from settings import db_credentials
from db import Database
from funds import Portfolio
from user import User

class Repository:
    def __init__(self):
        self.db = Database(**db_credentials)

    def get_portfolio(self, user_id):
        data = self.db.get_portfolio(user_id)
        data["user_id"] = user_id
        return Portfolio(data)

    def put_portfolio(self, portfolio):
        self.db.save_portfolio(portfolio.to_json(), portfolio.user_id)

    def create_user(self, user_info):
        return self.db.create_user(user_info)

    def get_user_info(self, username, password):
        user_json = self.db.get_user(username, password)
        if not user_json:
            return None

        return User(user_json["user_id"], user_json["username"])

    def _get_user_info_by_google_id(self, google_id):
        return self.db.get_user_info_by_google_id(google_id)

    def _get_user_info_by_portfolio_api_id(self, user_id):
        return self.db.get_user_info_by_id(user_id)

    def generate_session_key(self, user_data):
        user_info = self._get_user_info_by_google_id(user_data["id"])
        if user_info:
            user_id = user_info["user_id"]
        else:
            user_id = self.create_user(user_data)

        return self.db.new_session(user_id)

    def delete_session_key(self, uuid):
        session = self.db.get_session(uuid)
        if not session:
            return None

        key, user_id, created = session

        self.db.delete_sessions_for_user(user_id)

    def close(self):
        self.db.close()
