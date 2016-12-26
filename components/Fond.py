#!/usr/bin/python

import os
import json
import requests
import sys
import StringIO
import csv
import time
import datetime
from copy import deepcopy

from Investment import Investment
from error import InvalidUsage, InvalidDate

class Fond:
    def __init__(self, ticker=None, name=None, deposits=[]):
        if not ticker:
            raise InvalidUsage("Ticker must contain a valid ticker (was {})".format(ticker))
        self.ticker = ticker
        self.name = name
        self.fond_quotes = Investment("%s.FOND" % self.ticker)
        self.deposits = map(lambda x: {
            "date": datetime.datetime.strptime(x["date"], "%Y-%m-%d").date(),
            "amount": int(x["amount"])
        }, deposits)

    def __eq__(self, other): 
        return isinstance(other, Fond) and self.ticker == other.ticker

    def to_json(self):
        return {
                "name": self.name,
                "ticker": self.ticker,
                "deposits": self.deposits,
            }

    @property
    def quotes(self):
        quotes = self.fond_quotes.get_quotes()
        if self.deposits:
            start_idx = self.find_quote_entry_by_date(quotes, self.deposits[0]["date"])
        else:
            start_idx = -10

        return quotes[start_idx:]

    def _string_to_date(self, date):
        if isinstance(date, str) or isinstance(date, unicode):
            return datetime.datetime.strptime(date, "%Y-%m-%d").date()
        elif isinstance(date, datetime.date):
            return date

        raise InvalidDate("Unknown type '%s' for date" % type(date).__name__)
        
    def deposit(self, amount, date):
        date = self._string_to_date(date)
        if self.get_deposit_by_date(date):
            raise InvalidUsage("A deposit for that date is already registered")

        updated_deposits = self.deposits + [{"amount": amount, "date": date}]
        self.deposits = sorted(updated_deposits, key=lambda deposit: deposit["date"])

    def delete_deposit(self, date):
        date = self._string_to_date(date)
        num_deposits_before = len(self.deposits)
        self.deposits = filter(lambda x: x["date"] != date, self.deposits)
        num_deposits_after = len(self.deposits)

        num_deleted = num_deposits_before - num_deposits_after
        if num_deleted is not 1:
            raise InvalidUsage("failed to delete deposit (%s)" % num_deleted)

    def find_quote_entry_by_date(self, quotes, date):
        for i in range(len(quotes) - 1, -1, -1):
            if quotes[i]["quote_date"] == date:
                return i
        return None

    def get_deposit_by_date(self, date):
        date = self._string_to_date(date)
        return sum([deposit["amount"] for deposit in self.deposits if deposit["date"] == date])

    def _price_developement_percent(self, before, after):
        return float(after["close"])/float(before["close"])

    def get_developement(self):
        rows = []
        cash = 0

        for i in range(0, len(self.quotes)):
            curr_date = self.quotes[i]["quote_date"]
            deposit = self.get_deposit_by_date(curr_date)

            if i == 0:
                percent_development = 1
            else:
                percent_development = self._price_developement_percent(self.quotes[i - 1], self.quotes[i])

            cash = cash * percent_development + deposit
            rows.append({
                "date": curr_date,
                "value": cash,
                "deposit": deposit
            })

        return rows

    def get_summary(self):
        development = self.get_developement()
        return {
            "ticker": self.ticker,
            "name": self.name,
            "development": development,
            "total_deposited": sum(map(lambda x: x["deposit"], development))
        }

