#!/usr/bin/python

import sys
import json
import requests
import uuid
import urlparse
from flask import Flask, url_for, request, Response, redirect, session
from flask_cors import CORS
from flask_oauthlib.client import OAuth
from datetime import datetime, date
from cachetools import TTLCache

from repository import Repository
import settings

repo = Repository()
app = Flask(__name__)
app.secret_key = settings.secret_key
CORS(app)
oauth = OAuth(app)

google = oauth.remote_app('google',
                          consumer_key=settings.google_client_id,
                          consumer_secret=settings.google_client_secret,
                          request_token_params={
                              'scope': 'https://www.googleapis.com/auth/userinfo.email'
                          },
                          base_url='https://www.google.com/accounts/',
                          request_token_url=None,
                          access_token_method='POST',
                          access_token_url='https://accounts.google.com/o/oauth2/token',
                          authorize_url='https://accounts.google.com/o/oauth2/auth')

login_state = TTLCache(maxsize=128, ttl=1*60) # 1 minute ttl

@app.route('/login')
def login():
    success, failure = request.args.get("onSuccess"), request.args.get("onFailure")
    state = str(uuid.uuid4())
    login_state[state] = (success, failure)

    callback=url_for('authorized', _external=True)
    return google.authorize(callback=callback, state=state)

@app.route(settings.redirect_uri)
@google.authorized_handler
def authorized(resp):
    access_token = resp['access_token']
    session['access_token'] = access_token
    session['state'] = request.args.get("state")

    return redirect(url_for('login_verify'))

@google.tokengetter
def get_access_token():
    return session.get('access_token')

@app.route("/login/verify")
def login_verify():
    access_token = session.get('access_token')
    if access_token is None:
        return redirect(url_for('login'))

    onSuccessUrl, onFailureUrl = login_state[session.get("state")]
    del login_state[session.get("state")]

    headers = {'Authorization': 'OAuth {}'.format(access_token)}
    res = requests.get("https://www.googleapis.com/oauth2/v1/userinfo", headers=headers)
    if res.status_code == 401:
        # Unauthorized - bad token
        session.pop('access_token', None)
        return redirect(onFailureUrl)

    session_key = repo.generate_session_key(res.json())
    return redirect(urlparse.urljoin(onSuccessUrl, session_key))

@app.route("/create_user", methods=["POST"])
def create_user():
    username = request.form["username"]
    password = request.form["password"]

    js = repo.create_user(username, password)
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
