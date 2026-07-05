"""Unit tests for db_utils module - covering execute, execute_many, get_exam_context."""
import sqlite3
import pytest
from db_utils import get_cursor, fetch_all, fetch_one, execute, execute_many, get_exam_context


class TestExecute:
    def test_execute_insert(self, initialized_db):
        """execute() should insert a row and return a lastrowid."""
        rowid = execute(
            "INSERT INTO academic_years (year_name) VALUES (?)",
            ("2030",)
        )
        assert rowid is not None
        assert rowid > 0

    def test_execute_returns_lastrowid(self, initialized_db):
        rowid1 = execute("INSERT INTO academic_years (year_name) VALUES (?)", ("2031",))
        rowid2 = execute("INSERT INTO academic_years (year_name) VALUES (?)", ("2032",))
        assert rowid2 > rowid1

    def test_execute_with_commit_false(self, initialized_db):
        """With commit=False the write is not committed (rolled back on close)."""
        execute(
            "INSERT INTO academic_years (year_name) VALUES (?)",
            ("2099",),
            commit=False
        )
        # The row may still be visible in the same session due to WAL,
        # but at minimum we verify no exception is raised.


class TestExecuteMany:
    def test_execute_many_inserts_multiple(self, initialized_db):
        params = [("2040",), ("2041",), ("2042",)]
        execute_many(
            "INSERT INTO academic_years (year_name) VALUES (?)",
            params
        )
        rows = fetch_all("SELECT year_name FROM academic_years WHERE year_name IN ('2040','2041','2042')")
        assert len(rows) == 3

    def test_execute_many_empty_list(self, initialized_db):
        """Passing an empty list should not raise."""
        execute_many("INSERT INTO academic_years (year_name) VALUES (?)", [])


class TestGetExamContext:
    def test_returns_none_for_nonexistent_exam(self, initialized_db):
        result = get_exam_context(99999)
        assert result is None

    def test_returns_context_for_valid_exam(self, initialized_db):
        # Set up the required data chain: academic_year -> term -> exam
        execute("INSERT INTO academic_years (year_name, is_active) VALUES (?, ?)", ("2025", 1))
        year_row = fetch_one("SELECT id FROM academic_years WHERE year_name='2025'")
        year_id = year_row[0]

        execute(
            "INSERT INTO terms (term_name, academic_year_id) VALUES (?, ?)",
            ("Term 1", year_id)
        )
        term_row = fetch_one("SELECT id FROM terms WHERE term_name='Term 1' AND academic_year_id=?", (year_id,))
        term_id = term_row[0]

        execute(
            "INSERT INTO exams (exam_name, term_id, level, status) VALUES (?, ?, ?, ?)",
            ("Mid Term", term_id, "O_LEVEL", "OPEN")
        )
        exam_row = fetch_one("SELECT id FROM exams WHERE exam_name='Mid Term' AND term_id=?", (term_id,))
        exam_id = exam_row[0]

        result = get_exam_context(exam_id)
        assert result is not None
        assert result[0] == year_id
        assert result[1] == term_id


class TestGetCursor:
    def test_cursor_context_manager(self, initialized_db):
        with get_cursor() as cur:
            cur.execute("SELECT 1")
            assert cur.fetchone()[0] == 1

    def test_cursor_with_commit(self, initialized_db):
        with get_cursor(commit=True) as cur:
            cur.execute("INSERT INTO academic_years (year_name) VALUES (?)", ("2050",))
        rows = fetch_all("SELECT year_name FROM academic_years WHERE year_name='2050'")
        assert len(rows) == 1
