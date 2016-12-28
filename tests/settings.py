#!/usr/bin/env python

from os import environ

test_db_credentials = {
    "dbname": "test_db",
    "schema": "portfolioapi_test",
    "user": environ["DB_USER"],
    "host": environ["DB_HOST"],
    "port": environ["DB_PORT"],
    "password": environ["DB_PASSWORD"],
}
