#!/usr/bin/python

import sys
import json
import psycopg2
import bcrypt
import uuid
from datetime import datetime

class Database:
    def __init__(self, dbname, host, port, user, password):
        self.connection = psycopg2.connect("dbname='{}' user='{}' host='{}' password='{}'" \
            .format(dbname, user, host, password))
        self.cur = self.connection.cursor()

        self.schema = "portfolioapi"
        self.table = "user"
        self.session_table = "session"

        self._initialize_database()

    def _initialize_database(self):
        self.cur.execute("""CREATE SCHEMA IF NOT EXISTS {}""".format(self.schema))
        self.cur.execute("""CREATE TABLE IF NOT EXISTS {}.{}(id BIGSERIAL PRIMARY KEY, document JSONB)""".format(self.schema, self.table))
        self.cur.execute("""CREATE TABLE IF NOT EXISTS {}.{} (key uuid PRIMARY KEY, user_id BIGSERIAL, created TIMESTAMP)"""
            .format(self.schema, self.session_table))
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

    def get_user_info_by_google_id(self, google_id):
        sql = """SELECT id, document -> 'user' FROM %s.%s WHERE document #>> '{user,id}' = %%s""" % (self.schema, self.table)
        data = (google_id,)

        self.cur.execute(sql, data)
        self.connection.commit()

        user_info = self.cur.fetchone()
        if not user_info:
            return None

        user_id, user_info = user_info
        user_info["user_id"] = user_id
        return user_info

    def get_user_info_by_id(self, user_id):
        sql = """SELECT document FROM {}.{} WHERE id = %%s""".format(self.schema, self.table)
        data = (user_id,)
        self.cur.execute(sql, data)
        self.connection.commit()

        user_info = self.cur.fetchone()[0]
        user_info["user"]["user_id"] = user_id
        return user_info

    def create_user(self, user_info):
        sql = """INSERT INTO {}.{} (document) VALUES (%s) RETURNING id""".format(self.schema, self.table)
        data = (json.dumps({ "user": user_info}),)

        self.cur.execute(sql, data)
        self.connection.commit()

        return self.cur.fetchone()[0]

    def save_portfolio(self, portfolio, user_id):
        sql = """UPDATE {}.{} SET document=%s WHERE ID=%s""".format(self.schema, self.table)
        data = (portfolio, user_id)

        self.cur.execute(sql, data)
        self.connection.commit()

    def delete_sessions_for_user(self, user_id):
        sql = """DELETE from {}.{} where user_id = %s""".format(self.schema, self.session_table)
        data = (user_id,)

        self.cur.execute(sql, data)
        self.connection.commit()

    def new_session(self, user_id):
        self.delete_sessions_for_user(user_id)
        new_uuid = str(uuid.uuid4())
        sql = """INSERT INTO {}.{} (key, user_id, created) VALUES (%s, %s, %s)""".format(self.schema, self.session_table)
        data = (new_uuid, user_id, datetime.now())

        self.cur.execute(sql, data)
        self.connection.commit()

        return new_uuid

    def get_session(self, uuid):
        sql = """SELECT * FROM {}.{} WHERE key = %s""".format(self.schema, self.session_table)
        data = (uuid,)

        self.cur.execute(sql, data)
        self.connection.commit()
        return self.cur.fetchone()

    def close(self):
        self.cur.close()
        self.connection.close()
