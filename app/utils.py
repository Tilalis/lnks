import sqlite3

from threading import RLock
from urllib.parse import urlparse


class LinksDB:
    def __init__(self, database):
        self._connection = LinksDB._create_db(database)
        self._connection.execute(
            "CREATE TABLE IF NOT EXISTS lnks ("
            "   id INTEGER PRIMARY KEY,"
            "   alias TEXT NOT NULL UNIQUE,"
            "   link TEXT NOT NULL"
            ")"
        )
        self._connection.commit()

        self._lock = RLock()
        self._cursor = self._connection.cursor()

    def __enter__(self):
        with self._lock:
            self._cursor = self._connection.cursor()
            return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._connection.commit()

    @staticmethod
    def _create_db(database):
        return sqlite3.connect(database, check_same_thread=False)

    @staticmethod
    def _check_url(url):
        try:
            parsed = urlparse(url)
            return all((parsed.scheme, parsed.netloc))
        except ValueError:
            return False

    def execute(self, sql, parameters=None):
        with self:
            if parameters is None:
                self._cursor = self._cursor.execute(sql)
            else:
                self._cursor = self._cursor.execute(sql, parameters)

            return self._cursor

    def alias(self, link, alias=None):
        if not LinksDB._check_url(link):
            return False

        if alias is None:
            return self._get(
                field='alias',
                parameter='link',
                argument=link
            )

        with self:
            try:
                self.execute(
                    "INSERT INTO lnks (id, alias, link) VALUES (NULL, ?, ?)",
                    (alias, link)
                )
            except sqlite3.IntegrityError:
                return False

            return True

    def link(self, alias):
        return self._get(
            field='link',
            parameter='alias',
            argument=alias
        )

    def _get(self, *, field, parameter, argument, default=None):
        with self:
            cursor = self.execute(
                "SELECT {field} FROM lnks WHERE {parameter} == ?".format(
                    field=field,
                    parameter=parameter
                ),

                (argument, )
            )

            fetched = cursor.fetchone()

            if fetched is not None:
                (result, ) = fetched
                return result

            return default
