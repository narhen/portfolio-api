#!/usr/bin/python

import sys
import json
import uuid
import MySQLdb
from datetime import datetime

class Database:
    def __init__(self, dbname, host, port, user, password):
        self.connection = MySQLdb.connect(db=dbname, host=host, user=user, passwd=password)
        self.cur = self.connection.cursor()

        self.table = "user"
        self.session_table = "session"

        self._initialize_database()

    def _execute_query(self, query, data=None):
        self.cur.execute(query, data)
        self.connection.commit()

    def _initialize_database(self):
        self.cur.execute("""CREATE TABLE IF NOT EXISTS {} (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, user_data JSON, portfolio JSON)""".format(self.table))
        self.cur.execute("""CREATE TABLE IF NOT EXISTS {} (uuid VARCHAR(36) UNIQUE NOT NULL PRIMARY KEY, user_id INT, created TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""".format(self.session_table))
        self.connection.commit()

    def get_portfolio(self, session_token):
        session = self.get_session(session_token)
        if not session:
            return None

        uuid, user_id, timestamp = session

        sql = """SELECT id, portfolio FROM {} WHERE ID=%s""".format(self.table)
        data = (user_id,)
        self.cur.execute(sql, data)
        self.connection.commit()

        id, portfolio = self.cur.fetchone()
        return id, json.loads(portfolio, "ISO-8859-1")

    def _update_document(self, document_name, user_id, document):
        sql = """UPDATE {} SET {}=%s WHERE ID=%s""".format(self.table, document_name)
        data = (document, user_id)
        self._execute_query(sql, data)

    def save_portfolio(self, portfolio, user_id):
        self._update_document("portfolio", user_id, portfolio)

    def save_user(self, user_info, user_id):
        self._update_document("user_data", user_id, user_info)

    def get_user_info_by_google_id(self, google_id):
        sql = """SELECT id, user_data FROM %s WHERE user_data->"$.id" = %%s""" % self.table
        data = (google_id,)

        self.cur.execute(sql, data)
        self.connection.commit()

        result = self.cur.fetchone()
        if not result:
            return None

        id, user_data = result
        return id, json.loads(user_data, "ISO-8859-1")

    def _get_document_by_user_id(self, user_id, document_name):
        sql = """SELECT id, {} FROM {} WHERE id = %s""".format(document_name, self.table)
        data = (user_id,)
        self.cur.execute(sql, data)
        self.connection.commit()

        result = self.cur.fetchone()
        if not result:
            return None
        id, document = result
        return id, json.loads(document, "ISO-8859-1")

    def get_user_info_by_user_id(self, user_id):
        return self._get_document_by_user_id(user_id, "user_data")

    def get_portfolio_by_user_id(self, user_id):
        return self._get_document_by_user_id(user_id, "portfolio")

    def get_user_info(self, session_token):
        session = self.get_session(session_token)
        if not session:
            return None

        uuid, user_id, timestamp = session

        sql = """SELECT user_data FROM {} WHERE id = %s""".format(self.table)
        data = (user_id,)
        self.cur.execute(sql, data)
        self.connection.commit()

        user_info, = self.cur.fetchone()
        user_info = json.loads(user_info, "ISO-8859-1")

        user_info["user_id"] = user_id
        return user_info

    def create_user(self, user_info):
        sql = """INSERT INTO {} (user_data, portfolio) VALUES (%s, '[]')""".format(self.table)
        data = (json.dumps(user_info),)

        self.cur.execute(sql, data)
        self.connection.commit()

        self.cur.execute("SELECT LAST_INSERT_ID()")
        self.connection.commit()

        return self.cur.fetchone()[0]

    def delete_sessions_for_user(self, user_id):
        sql = """DELETE FROM {} WHERE user_id = %s""".format(self.session_table)
        data = (user_id,)

        self.cur.execute(sql, data)
        self.connection.commit()

    def new_session(self, user_id):
        self.delete_sessions_for_user(user_id)

        new_uuid = str(uuid.uuid4())
        sql = """INSERT INTO {} (uuid, user_id, created) VALUES (%s, %s, %s)""".format(self.session_table)
        data = (new_uuid, user_id, datetime.now())

        self.cur.execute(sql, data)
        self.connection.commit()

        return new_uuid

    def _is_valid_uuid4(self, uuid_string):
        try:
            uuid.UUID(uuid_string, version=4)
        except ValueError:
            return False
        return True

    def get_session(self, uuid_string):
        if not self._is_valid_uuid4(uuid_string):
            return None

        sql = """SELECT * FROM {} WHERE uuid = %s""".format(self.session_table)
        data = (uuid_string,)

        self.cur.execute(sql, data)
        self.connection.commit()
        return self.cur.fetchone()

    def close(self):
        self.cur.close()
        self.connection.close()
