#!/usr/bin/python

import sys
import json
from flask import Flask, url_for, request, Response
from flask_cors import CORS
from datetime import datetime, date

from repository import Repository
import settings

repo = Repository()
app = Flask(__name__)
CORS(app)

@app.route("/")
def api_root():
    return "Welcome"

@app.route("/create_user")
def create_user():
    js = repo.create_user().to_json()
    return Response(js, status=201, mimetype="application/json")

@app.route("/user/<user_id>/summary")
def api_summary(user_id):
    date_handler = lambda obj: (
        obj.isoformat()
        if isinstance(obj, datetime)
        or isinstance(obj, date)
        else None
    )

    portfolio = repo.get_portfolio(user_id)
    js = json.dumps(portfolio.get_summary(), default=date_handler)
    return Response(js, status=200, mimetype="application/json")

@app.route("/user/<user_id>/addfond", methods=["POST"])
def add_fond(user_id):
    ticker = request.form["ticker"]
    name = request.form["name"]
    ref_ticker = request.form.get("ref_ticker", None)
    print "add_fond", ticker, name, ref_ticker

    portfolio = repo.get_portfolio(user_id)
    portfolio.add_fond(ticker, name, ref_ticker)

    repo.put_portfolio(portfolio)

    return Response(status=201)

@app.route("/user/<user_id>/deposit", methods=["PUT"])
def deposit(user_id):
    ticker = request.form["ticker"]
    date = datetime.strptime(request.form["date"], "%Y-%m-%d").date()
    amount = request.form["amount"]

    print date

    portfolio = repo.get_portfolio(user_id)
    portfolio.deposit(ticker, date, amount)
    repo.put_portfolio(portfolio)

    return Response(status=201)
    
def main():
    app.run(debug=settings.debug, host="0.0.0.0")

if __name__ == "__main__":
    sys.exit(main())
