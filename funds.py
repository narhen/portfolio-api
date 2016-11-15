#!/usr/bin/python

import os
import json
import requests
import sys
import StringIO
import csv
import time
from flask import Flask, url_for, Response
from flask_cors import CORS
from datetime import datetime, date
from prettytable import PrettyTable
from copy import deepcopy

class Investment:
    _cache_directory = "/tmp"
    _quotes_source_url = "http://norma.netfonds.no/paperhistory.php?paper={}&csv_format=csv"

    def __init__(self, ticker):
        self.ticker = ticker
        self.quotes_source_url = Investment._quotes_source_url.format(self.ticker)
        self.filename = "%s/%s.json" % (self._cache_directory, self.ticker)
        self._get_from_cache()

    def _get_quotes_from_remote(self):
        start = time.time()
        print "start: get quotes from remote"
        quotes = requests.get(self.quotes_source_url).text
        f = StringIO.StringIO(quotes)
        reader = csv.reader(f)
        quotes = [map(lambda x: x.encode("utf-8").strip(), row) for row in reader]
        header = quotes.pop(0)

        def row_to_dict(row, header):
            return {header[i]: row[i] for i in range(0, len(header))}

        self._put_in_cache([row_to_dict(row, header) for row in quotes])
        self._get_from_cache()


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
            q["quote_date"] = datetime.strptime(q["quote_date"], "%Y%m%d").date()
            return q
        self.quotes["quotes"] = list(reversed(map(map_datestring_to_datetime, self.quotes["quotes"])))

    def _quotes_has_expired(self):
        deprecated_timestamp = time.mktime(datetime.today().replace(hour=18, minute=0, second=0).timetuple())
        day_of_week = datetime.today().weekday()
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
    def __init__(self, ticker, name, ref_index_ticker, start_date, start_value):
        self.ticker = ticker
        self.name = name
        self.ref_index_ticker = ref_index_ticker
        self.deposits = []

        self.fond_quotes = Investment("%s.FOND" % self.ticker)

        if self.ref_index_ticker:
            self.ref_quotes = Investment(self.ref_index_ticker)
            print self.ref_quotes.get_quotes()

        self.deposit(start_value, start_date)

    def __eq__(self, other): 
        return self.ticker == other.ticker

    def __str__(self):
        return json.dumps(self.fond_summary(), indent=4)

    @property
    def quotes(self):
        quotes = self.fond_quotes.get_quotes()
        start_idx = self.find_entry_by_date(quotes, self.deposits[0]["date"])
        if not start_idx:
            raise Exception("Couldn't find {} in quote data".format(str(start_date)))

        return quotes[start_idx:]
        
    def deposit(self, amount, date):
        self.deposits += [{"amount": amount, "date": date}]

    def find_entry_by_date(self, quotes, date):
        for i in range(0, len(quotes)):
            if quotes[i]["quote_date"] == date:
                return i
        return None

    def get_deposit_by_date(self, date):
        return sum([deposit["amount"] for deposit in self.deposits if deposit["date"] == date])

    def _price_developement_percent(self, before, after):
        return float(after["close"])/float(before["close"])

    def get_developement(self):
        start = time.time()
        rows = []
        cash = 0
        deposits_to_date = 0

        for i in range(0, len(self.quotes)):
            curr_date = self.quotes[i]["quote_date"]
            deposit = self.get_deposit_by_date(curr_date)
            deposits_to_date += deposit

            if i == 0:
                percent_development = 1
            else:
                percent_development = self._price_developement_percent(self.quotes[i - 1], self.quotes[i])

            cash = cash * percent_development + deposit
            rows.append({
                "date": curr_date,
                "monetary": cash,
                "percent": (percent_development - 1) * 100,
                "normalized": (float(cash)/deposits_to_date - 1) * 100,
                "deposit": deposit
            })

        return rows

    def get_summary(self):
        development = self.get_developement()
        return {
            "ticker": self.ticker,
            "name": self.name,
            "development": development,
            "total_deposted": sum(map(lambda x: x["deposit"], development))
        }

class Portfolio:
    def __init__(self, filename=None):
        self.portfolio = []

    def __str__(self):
        ret = []
        for date, value in self.get_quotes():
            ret += ["%s %.2f" % (date, value)]
        return "\n".join(ret)

    def get_deposits_by_date(self, date):
        return sum([f.get_deposit_by_date(date) for f in self.portfolio])

    def get_total_development(self, fonds):
        def add_lists(list_a, list_b):
            res = list_a
            for b_entry in list_b:
                a_entry = filter(lambda x: x["date"] == b_entry["date"], res)

                if not a_entry:
                    res += [b_entry]
                else:
                    a_entry[0]["monetary"] += b_entry["monetary"]
                    a_entry[0]["deposit"] += b_entry["deposit"]

            
            res = sorted(res, key=lambda x: x["date"])

            for i in range(0, len(res)):
                if i == 0:
                    res[i]["percent"] = 0
                    continue

                deposit = self.get_deposits_by_date(res[i]["date"])
                res[i]["percent"] = ((res[i]["monetary"] - deposit) / res[i - 1]["monetary"] - 1) * 100

            return res

        result = reduce(add_lists, fonds)
        accumulated_deposits = 0
        for quote in result:
            accumulated_deposits += self.get_deposits_by_date(quote["date"])
            quote["normalized"] = (quote["monetary"] / accumulated_deposits - 1) * 100

        return {"name": "Portfolio", "development": result, "total_deposited": accumulated_deposits}

    def add_fond(self, ticker, description, ref_idx_ticker, start_date, start_value=0):
        if filter(lambda x: x.ticker == ticker, self.portfolio):
            print "Portfolio already contains", ticker

        self.portfolio += [Fond(ticker, description, ref_idx_ticker, start_date, start_value)]

    def get_monetary_value_of_fonds(self):
        fonds_development = [fond.get_summary() for fond in self.portfolio]
        combined_development = self.get_total_development(map(lambda x: deepcopy(x["development"]), fonds_development))
        return [combined_development] + fonds_development

def main():
    port = Portfolio()
    port.add_fond("KL-ANIII", "KLP AksjeNorge Indeks II", "OSEBX.OSE", date(2016, 10, 17), 3000)
    port.add_fond("KL-AFMI2", "KLP Aksje Fremvoksende Marked Indeks II", None, date(2016, 10, 25), 5250)
    port.add_fond("DK-GLBIX", "DNB Global Indeks", None, date(2016, 10, 25), 6750)

    print json.dumps(port.get_monetary_value_of_fonds(), indent=4)

app = Flask(__name__)
CORS(app)

port = Portfolio()
port.add_fond("KL-ANIII", "KLP AksjeNorge Indeks II", None, date(2016, 10, 17), 3000)
port.add_fond("KL-AFMI2", "KLP Aksje Fremvoksende Marked Indeks II", None, date(2016, 10, 25), 5250)
port.add_fond("DK-GLBIX", "DNB Global Indeks", None, date(2016, 10, 25), 6750)

@app.route("/")
def api_root():
    return "Welcome"

@app.route("/value/monetary")
def api_monetary():
    date_handler = lambda obj: (
        obj.isoformat()
        if isinstance(obj, datetime)
        or isinstance(obj, date)
        else None
    )

    js = json.dumps(port.get_monetary_value_of_fonds(), default=date_handler)
    resp = Response(js, status=200, mimetype="application/json")

    return resp

def main2():
    app.run(debug=True, host="0.0.0.0")

if __name__ == "__main__":
    sys.exit(eval(sys.argv[1])())

