"""Compatibility entry point for code that still imports ``db_manager``."""

from database import connect


def get_connection():
    return connect()
