"""Shared fixtures for SRMS unit tests."""
import sys
import os
import sqlite3
import pytest

# Add project root to path so modules can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    """Create a temporary SQLite database for testing."""
    db_path = str(tmp_path / "test_srms.db")
    monkeypatch.setattr("database.DB_NAME", db_path)
    return db_path


@pytest.fixture
def initialized_db(tmp_db):
    """Create and initialize a temporary database with schema and default data."""
    from database import init_db
    init_db()
    return tmp_db
