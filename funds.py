#!/usr/bin/python

import os
import json
import requests
import sys
import StringIO
import csv
import time
import datetime
from prettytable import PrettyTable
from copy import deepcopy

import settings
from error import InvalidUsage

class Investment:
    _cache_directory = "/tmp"

    def __init__(self, ticker):
        self.ticker = ticker
        self.quotes_source_url = settings.quotes_source_url.format(self.ticker)
        self.filename = "%s/%s.json" % (self._cache_directory, self.ticker)
        self._get_from_cache()

    def _get_quotes_from_remote(self):
        start = time.time()
        quotes = requests.get(self.quotes_source_url).text
        f = StringIO.StringIO(quotes)
        reader = csv.reader(f)
        quotes = [map(lambda x: x.encode("utf-8").strip(), row) for row in reader]
        header = quotes.pop(0)

        def row_to_dict(row, header):
            return {header[i]: row[i] for i in range(0, len(header))}

        self._put_in_cache([row_to_dict(row, header) for row in quotes])
        self._get_from_cache()


    def _fill_date_holes_in_quotes(self, quotes):
        i = 1
        while i < len(quotes):
            day_after_yesterday = quotes[i - 1]["quote_date"] + datetime.timedelta(days=1)
            if day_after_yesterday != quotes[i]["quote_date"]:
                copy = deepcopy(quotes[i - 1])
                copy["quote_date"] = day_after_yesterday
                quotes = quotes[:i] + [copy] + quotes[i:]
            else:
                i += 1

        return quotes

    def _put_in_cache(self, quotes):
        to_store = {
            "fetch_time": int(time.time()),
            "quotes": quotes
        }
        with open(self.filename, "wr") as f:
            f.write(json.dumps(to_store, indent=2))

    def _get_from_cache(self):
        if not os.path.isfile(self.filename):
            self.quotes = None
            return

        self.quotes = json.loads(open(self.filename, "r").read())

        def map_datestring_to_datetime(q):
            if "quote_date" not in q:
                return q
            q["quote_date"] = datetime.datetime.strptime(q["quote_date"], "%Y%m%d").date()
            return q

        quotes = list(reversed(map(map_datestring_to_datetime, self.quotes["quotes"])))
        self.quotes["quotes"] = self._fill_date_holes_in_quotes(quotes)


    def _quotes_has_expired(self):
        deprecated_timestamp = time.mktime(datetime.datetime.today().replace(hour=18, minute=0, second=0).timetuple())
        day_of_week = datetime.datetime.today().weekday()
        weekend = [5, 6]

        if day_of_week in weekend:
            return False

        if self.quotes["fetch_time"] > int(deprecated_timestamp):
            return False

        if time.time() - self.quotes["fetch_time"] < 30 * 60:
            return False

        return True

    def get_quotes(self):
        if not self.quotes:
            self._get_quotes_from_remote()
        elif self._quotes_has_expired():
            self._get_quotes_from_remote()

        return self.quotes["quotes"]

class Fond:
    def __init__(self, ticker=None, name=None, ref_index_ticker=None, deposits=[]):
        if not ticker:
            raise Exception("Ticker must contain a valid ticker (was {})".format(ticker))
        self.ticker = ticker
        self.name = name
        self.fond_quotes = Investment("%s.FOND" % self.ticker)
        self.ref_index_ticker = ref_index_ticker
        self.deposits = map(lambda x: {
            "date": datetime.datetime.strptime(x["date"], "%Y-%m-%d").date(),
            "amount": int(x["amount"])
        }, deposits)

        if ref_index_ticker:
            self.ref_quotes = Investment(self.ref_index_ticker)
            print self.ref_quotes.get_quotes()

    def __eq__(self, other): 
        return self.ticker == other.ticker

    def __str__(self):
        return json.dumps(self.fond_summary(), indent=4)

    def to_json(self):
        return {
                "name": self.name,
                "ticker": self.ticker,
                "ref_index_ticker": self.ref_index_ticker,
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
        
    def deposit(self, amount, date):
        if self.get_deposit_by_date(date):
            raise InvalidUsage("A deposit for that date is already registered")

        updated_deposits = self.deposits + [{"amount": amount, "date": date}]
        self.deposits = sorted(updated_deposits, key=lambda deposit: deposit["date"])

    def delete_deposit(self, date):
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

class Portfolio:
    def __init__(self, data):
        self.data = data
        self.user_id = data["user"]["user_id"]
        self.portfolio = {fond_data["ticker"]: Fond(**fond_data) for fond_data in data.get("fonds", [])}

    def __str__(self):
        return json.dumps(self.get_summary(), indent=4)

    @staticmethod
    def json_serializer(obj):
        if isinstance(obj, Fond):
            return obj.to_json()
        elif isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date):
            return obj.isoformat()
        else:
            return None

    def to_json(self):
        return self.portfolio.values()

    def get_deposits_by_date(self, date):
        return sum([fond.get_deposit_by_date(date) for ticker, fond in self.portfolio.items()])

    def get_summary(self):
        summary = [fond.get_summary() for fond in self.portfolio.values()]
        combined_development = self.get_total_development(map(lambda x: deepcopy(x["development"]), summary))

        return summary + [combined_development]

    def get_total_development(self, fonds):
        def add_lists(list_a, list_b):
            res = list_a
            for b_entry in list_b:
                a_entry = filter(lambda x: x["date"] == b_entry["date"], res)

                if not a_entry:
                    res += [b_entry]
                else:
                    a_entry[0]["value"] += b_entry["value"]
                    a_entry[0]["deposit"] += b_entry["deposit"]

            
            return sorted(res, key=lambda x: x["date"])

        result = reduce(add_lists, fonds, [])
        accumulated_deposits = 0
        for quote in result:
            accumulated_deposits += self.get_deposits_by_date(quote["date"])

        return {"name": "Portfolio", "ticker": "Portfolio", "development": result, "total_deposited": accumulated_deposits}

    def deposit(self, ticker, date, amount):
        if ticker not in self.portfolio:
            raise InvalidUsage("%s is not registered in the portfolio" % ticker)

        if isinstance(date, str) or isinstance(date, unicode):
            date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

        return self.portfolio[ticker].deposit(amount, date)

    def delete_deposit(self, ticker, date):
        if ticker not in self.portfolio:
            raise InvalidUsage("%s is not registered in the portfolio" % ticker)

        if isinstance(date, str) or isinstance(date, unicode):
            date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

        return self.portfolio[ticker].delete_deposit(date)

    def add_fond(self, ticker, name, ref_idx_ticker):
        if ticker in self.portfolio:
            raise InvalidUsage("Portfolio already contains", ticker)

        self.portfolio[ticker] = Fond(**{"ticker": ticker, "name": name, "ref_index_ticker": ref_idx_ticker})

    def get_monetary_value_of_fonds(self):
        fonds_development = [fond.get_summary() for ticker, fond in self.portfolio.items()]
        combined_development = self.get_total_development(map(lambda x: deepcopy(x["development"]), fonds_development))
        return [combined_development] + fonds_development
