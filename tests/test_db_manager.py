"""Unit tests for db_manager module."""
import sqlite3
import pytest


class TestGetConnection:
    def test_returns_connection(self, initialized_db):
        from db_manager import get_connection
        conn = get_connection()
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_connection_is_usable(self, initialized_db):
        from db_manager import get_connection
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        assert cur.fetchone()[0] == 1
        conn.close()
