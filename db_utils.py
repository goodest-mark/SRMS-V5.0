"""Shared database utilities to eliminate repeated connect/close boilerplate."""

from contextlib import contextmanager
from database import connect


@contextmanager
def get_cursor(commit=False):
    """Context manager yielding a DB cursor with automatic close/commit.

    Usage:
        with get_cursor() as cur:
            cur.execute("SELECT ...")
            rows = cur.fetchall()

        with get_cursor(commit=True) as cur:
            cur.execute("INSERT ...")
    """
    conn = connect()
    cur = conn.cursor()
    try:
        yield cur
        if commit:
            conn.commit()
    finally:
        conn.close()


def fetch_all(query, params=()):
    """Execute a SELECT and return all rows."""
    with get_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def fetch_one(query, params=()):
    """Execute a SELECT and return a single row or None."""
    with get_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchone()


def execute(query, params=(), commit=True):
    """Execute a single write statement."""
    with get_cursor(commit=commit) as cur:
        cur.execute(query, params)
        return cur.lastrowid


def execute_many(query, params_list, commit=True):
    """Execute a statement for each param tuple in params_list."""
    with get_cursor(commit=commit) as cur:
        cur.executemany(query, params_list)


def get_exam_context(exam_id):
    """Return (academic_year_id, term_id) for an exam, or None if not found."""
    return fetch_one("""
        SELECT t.academic_year_id, e.term_id
        FROM exams e
        JOIN terms t ON e.term_id = t.id
        WHERE e.id = ?
    """, (exam_id,))
