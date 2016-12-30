#!/usr/bin/env python

from os import environ

debug=environ.get("DEBUG", False) != False

secret_key = environ["SECRET_KEY"]
google_client_id = environ["GOOGLE_CLIENT_ID"]
google_client_secret = environ["GOOGLE_CLIENT_SECRET"]
redirect_uri = "/oauth2callback"
quotes_source_url = environ["QUOTES_URL"]

db_credentials = {
    "dbname": environ["DB_NAME"],
    "schema": "portfolioapi",
    "user": environ["DB_USER"],
    "host": environ["DB_HOST"],
    "port": environ["DB_PORT"],
    "password": environ["DB_PASSWORD"],
}
