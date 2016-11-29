#!/usr/bin/python

import sys
import json
import psycopg2

class Database:
    def __init__(self, dbname, host, port, user, password):
        self.connection = psycopg2.connect("dbname='{}' user='{}' host='{}' password='{}'" \
            .format(dbname, user, host, password))
        self.cur = self.connection.cursor()

        self.schema = "portfolioapi"
        self.table = "portfolio"

        self._initialize_database()

    def _initialize_database(self):
        self.cur.execute("""CREATE SCHEMA IF NOT EXISTS {}""".format(self.schema))
        self.cur.execute("""CREATE TABLE IF NOT EXISTS {}.{}(id BIGSERIAL PRIMARY KEY, document JSONB)""".format(self.schema, self.table))
        self.connection.commit()

    def get_portfolio(self, user_id):
        sql = """SELECT * FROM {}.{} WHERE ID=%s""".format(self.schema, self.table)
        data = (user_id,)
        self.cur.execute(sql, data)
        self.connection.commit()

        return self.cur.fetchone()[1]

    def create_user(self):
        sql = """INSERT INTO {}.{} (document) VALUES (%s) RETURNING id""".format(self.schema, self.table)
        data = (json.dumps({}),)

        self.cur.execute(sql, data)
        self.connection.commit()

        return self.cur.fetchone()[0]

    def save_portfolio(self, portfolio, user_id):
        sql = """UPDATE {}.{} SET document=%s WHERE ID=%s""".format(self.schema, self.table)
        data = (portfolio, user_id)

        self.cur.execute(sql, data)
        self.connection.commit()

    def close(self):
        self.cur.close()
        self.connection.close()
