import json
import datetime
from copy import deepcopy

from Fond import Fond
from error import InvalidUsage, InvalidDate

class Portfolio:
    def __init__(self, user_id, fonds):
        self.user_id = user_id
        self.portfolio = fonds

    @staticmethod
    def json_serializer(obj):
        if isinstance(obj, Fond):
            return obj.to_json()
        elif isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date):
            return obj.isoformat()
        else:
            return None

    def _string_to_date(self, date):
        if isinstance(date, str) or isinstance(date, unicode):
            return datetime.datetime.strptime(date, "%Y-%m-%d").date()
        elif isinstance(date, datetime.date):
            return date

        raise InvalidDate("Unknown type '%s' for date" % type(date).__name__)

    def to_json(self):
        return self.portfolio.values()

    def get_deposits_by_date(self, date):
        return sum([fond.get_deposit_by_date(self._string_to_date(date)) for ticker, fond in self.portfolio.items()])

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

        return self.portfolio[ticker].deposit(amount, self._string_to_date(date))

    def delete_deposit(self, ticker, date):
        if ticker not in self.portfolio:
            raise InvalidUsage("%s is not registered in the portfolio" % ticker)

        return self.portfolio[ticker].delete_deposit(self._string_to_date(date))

    def add_fond(self, ticker, name):
        if ticker in self.portfolio:
            raise InvalidUsage("Portfolio already contains", ticker)

        self.portfolio[ticker] = Fond(**{"ticker": ticker, "name": name})

