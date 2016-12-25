#!/usr/bin/env python

import sys
import json
import requests
import uuid
import urlparse
from flask import Flask, url_for, request, Response, redirect, session, jsonify
from flask_cors import CORS
from flask_oauthlib.client import OAuth
from datetime import datetime, date
from cachetools import TTLCache

from repository import Repository
import settings
from validation import validate_deposit
from error import InvalidUsage

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

@app.before_request
def check_if_valid_session_key():
    if request.method == "OPTIONS":
        return None

    if request.endpoint in ["login", "authorized", "login_verify"]:
        return None

    session_key = request.headers.get("api-key")
    if not session_key or not repo.valid_session_key(session_key):
        raise InvalidUsage("invalid session key", status_code=401)

@app.route('/logout')
def logout():
    session_token = request.headers.get("api-key")
    repo.delete_session_key(session_token)
    return Response(status=204)

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

@app.route("/userinfo")
def userinfo():
    session_token = request.headers.get("api-key")

    js = repo.get_user_info(session_token)
    return Response(json.dumps(js), status=200, mimetype="application/json")

@app.route("/summary")
def api_summary():
    session_token = request.headers.get("api-key")

    date_handler = lambda obj: (
        obj.isoformat()
        if isinstance(obj, datetime)
        or isinstance(obj, date)
        else None
    )

    portfolio = repo.get_portfolio(session_token)
    js = json.dumps(portfolio.get_summary(), default=date_handler)
    return Response(js, status=200, mimetype="application/json")

@app.route("/addfond", methods=["POST"])
def add_fond():
    session_token = request.headers.get("api-key")
    ticker = request.form["ticker"]
    name = request.form["name"]
    ref_ticker = request.form.get("ref_ticker", None)

    portfolio = repo.get_portfolio(session_token)
    portfolio.add_fond(ticker, name, ref_ticker)

    repo.put_portfolio(portfolio)

    return Response(status=204)

def add_deposits(deposit_data, portfolio):
    for fond in deposit_data["fonds"]:
        portfolio.deposit(fond["ticker"], deposit_data["date"], fond["amount"])
    return True

def delete_deposits(deposit_data, portfolio):
    for ticker in deposit_data["tickers"]:
        if not portfolio.delete_deposit(ticker, deposit_data["date"]):
            return False
    return True

@app.route("/deposit", methods=["PUT", "DELETE"])
def deposit():
    if not validate_deposit(request):
        raise InvalidUsage("invalid input")

    session_token = request.headers.get("api-key")
    portfolio = repo.get_portfolio(session_token)

    task_functions = {
        "DELETE": delete_deposits,
        "PUT": add_deposits
    }

    deposit_data = request.get_json()
    task_functions[request.method.upper()](deposit_data, portfolio)

    repo.put_portfolio(portfolio)
    return Response(status=204)

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

def main():
    app.run(debug=settings.debug, host="0.0.0.0")

if __name__ == "__main__":
    sys.exit(main())
