import os
import sqlite3
import time

from .schema import MYSQL_SCHEMA, SQLITE_SCHEMA


class MySQLDatabase:
    def __init__(self, host, port, user, password, name):
        import pymysql
        import pymysql.cursors

        self.driver = pymysql
        self.params = dict(
            host=host,
            port=port,
            user=user,
            password=password,
            database=name,
            charset="utf8mb4",
            autocommit=True,
            connect_timeout=5,
            cursorclass=pymysql.cursors.DictCursor,
        )

    def _connect(self):
        return self.driver.connect(**self.params)

    def query(self, sql, params=()):
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return list(cur.fetchall())
        finally:
            conn.close()

    def execute(self, sql, params=()):
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.lastrowid, cur.rowcount
        finally:
            conn.close()

    def create_schema(self):
        for statement in MYSQL_SCHEMA:
            self.execute(statement)

    def wait_until_ready(self, retries=30, interval=2):
        last_error = None
        for _ in range(retries):
            try:
                self.query("SELECT 1 AS ok")
                return
            except self.driver.err.Error as exc:
                last_error = exc
                time.sleep(interval)
        raise RuntimeError(f"Database tidak siap setelah {retries} percobaan: {last_error}")


class SQLiteDatabase:
    def __init__(self, path):
        self.path = path

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @staticmethod
    def _fix(sql):
        return sql.replace("%s", "?")

    def query(self, sql, params=()):
        conn = self._connect()
        try:
            return [dict(row) for row in conn.execute(self._fix(sql), params).fetchall()]
        finally:
            conn.close()

    def execute(self, sql, params=()):
        conn = self._connect()
        try:
            cur = conn.execute(self._fix(sql), params)
            conn.commit()
            return cur.lastrowid, cur.rowcount
        finally:
            conn.close()

    def create_schema(self):
        for statement in SQLITE_SCHEMA:
            self.execute(statement)

    def wait_until_ready(self, retries=1, interval=0):
        self.query("SELECT 1 AS ok")


def database_from_env():
    if os.environ.get("DB_BACKEND", "mysql") == "sqlite":
        return SQLiteDatabase(os.environ.get("SQLITE_PATH", "dev.sqlite3"))
    return MySQLDatabase(
        host=os.environ.get("DB_HOST", "database"),
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        name=os.environ["DB_NAME"],
    )
