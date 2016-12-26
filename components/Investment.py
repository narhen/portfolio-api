#!/usr/bin/env python

import os
import time
import requests
import StringIO
import csv
import json
from copy import deepcopy
import datetime

from components.error import InvalidUsage

class Investment:
    _cache_directory = "/tmp"

    def __init__(self, ticker):
        self.ticker = ticker
        self.quotes_source_url = os.environ["QUOTES_URL"].format(self.ticker)
        self.filename = "%s/%s.json" % (self._cache_directory, self.ticker)
        self.quotes = None

    def _get_quotes_from_remote(self):
        response = requests.get(self.quotes_source_url)
        if response.status_code is not 200:
            return None

        quotes = response.text
        f = StringIO.StringIO(quotes)
        reader = csv.reader(f)
        quotes = [map(lambda x: x.encode("utf-8").strip(), row) for row in reader]
        header = quotes.pop(0)

        def row_to_dict(row, header):
            return {header[i]: row[i] for i in range(0, len(header))}

        return {
            "fetch_time": int(time.time()),
            "quotes": [row_to_dict(row, header) for row in quotes]
        }

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
        with open(self.filename, "wr") as f:
            f.write(json.dumps(quotes, indent=2))

    def _get_from_cache(self):
        if not os.path.isfile(self.filename):
            self.quotes = None
            return

        quotes = json.loads(open(self.filename, "r").read())

        def map_datestring_to_datetime(q):
            if "quote_date" not in q:
                return q
            q["quote_date"] = datetime.datetime.strptime(q["quote_date"], "%Y%m%d").date()
            return q

        quotes = list(reversed(map(map_datestring_to_datetime, self.quotes["quotes"])))
        quotes["quotes"] = self._fill_date_holes_in_quotes(quotes)
        return quotes

    def _get_date_today(self):
        return datetime.datetime.today()

    def _quotes_has_expired(self, quotes):
        deprecated_timestamp = time.mktime(self._get_date_today().replace(hour=18, minute=0, second=0).timetuple())
        day_of_week = self._get_date_today().weekday()
        weekend = [5, 6]

        if day_of_week in weekend:
            return False

        if quotes["fetch_time"] > int(deprecated_timestamp):
            return False

        if time.mktime(self._get_date_today().timetuple()) - quotes["fetch_time"] < 30 * 60:
            return False

        return True

    def get_quotes(self):
        if not self.quotes:
            self.quotes = self._get_from_cache() or self._get_quotes_from_remote()
            if not self.quotes:
                raise InvalidUsage("%s is not a valid ticker" % self.ticker)

        if self._quotes_has_expired(self.quotes):
            self.quotes = self._get_quotes_from_remote()
            self._put_in_cache(self.quotes)

        return self.quotes["quotes"]
