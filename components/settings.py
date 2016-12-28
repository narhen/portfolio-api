#!/usr/bin/env python

from os import environ

debug=True

secret_key = environ["SECRET_KEY"]
google_client_id = environ["GOOGLE_CLIENT_ID"]
google_client_secret = environ["GOOGLE_CLIENT_SECRET"]
redirect_uri = "/login/verify"

db_credentials = {
    "dbname": environ["DB_NAME"],
    "schema": "portfolioapi",
    "user": environ["DB_USER"],
    "host": environ["DB_HOST"],
    "port": environ["DB_PORT"],
    "password": environ["DB_PASSWORD"],
}
