#!/usr/bin/python

import sys
import json
import psycopg2
import bcrypt

class Database:
    def __init__(self, dbname, host, port, user, password):
        self.connection = psycopg2.connect("dbname='{}' user='{}' host='{}' password='{}'" \
            .format(dbname, user, host, password))
        self.cur = self.connection.cursor()

        self.schema = "portfolioapi"
        self.table = "user"

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

    def get_user(self, username, password):
        sql = """SELECT id, document -> 'user' FROM %s.%s WHERE document #>> '{user,username}' = %%s""" % (self.schema, self.table)
        data = (username,)
        self.cur.execute(sql, data)
        self.connection.commit()

        result = self.cur.fetchone()
        if not result:
            return None

        user_id, user_doc = result
        user_doc["user_id"] = user_id

        hashed_pw = user_doc["password"]
        if not bcrypt.hashpw(str(password), str(hashed_pw)) == hashed_pw:
            return None

        return user_doc

    def get_user_by_id(self, user_id):
        sql = """SELECT * FROM {}.{} WHERE id=%s""".format(self.schema, self.table)
        data = (user_id,)
        self.cur.execute(sql, data)
        self.connection.commit()

        user_info = self.cur.fetchone()[1]
        user_info["user"]["user_id"] = user_id
        return user_info

    def create_user(self, username, password):
        sql = """INSERT INTO {}.{} (document) VALUES (%s) RETURNING id""".format(self.schema, self.table)
        data = (json.dumps(
        {
            "user": {
                "username": username,
                "password": bcrypt.hashpw(str(password), bcrypt.gensalt())
            }
        }),)

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
