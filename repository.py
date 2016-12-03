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

    def create_user(self, username, password):
        user_id = self.db.create_user(username, password)
        return Portfolio({"user_id": user_id})

    def get_user_info(self, username, password):
        user_json = self.db.get_user(username, password)
        if not user_json:
            return None

        return User(user_json["user_id"], user_json["username"])

    def get_user_info_by_id(self, user_id):
        user_json = self.db.get_user_by_id(user_id)
        if not user_json:
            return None

        return User(user_json["user"]["user_id"], user_json["user"]["username"])

    def close(self):
        self.db.close()
