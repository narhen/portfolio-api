#!/usr/bin/python

from settings import db_credentials
from db import Database
from funds import Portfolio

class Repository:
    def __init__(self):
        self.db = Database(**db_credentials)

    def get_portfolio(self, user_id):
        data = self.db.get_portfolio(user_id)
        data["user_id"] = user_id
        return Portfolio(data)

    def put_portfolio(self, portfolio):
        self.db.save_portfolio(portfolio.to_json(), portfolio.user_id)

    def create_user(self):
        user_id = self.db.create_user()
        return Portfolio({"user_id": user_id})

    def close(self):
        self.db.close()
