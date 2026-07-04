"""Unit tests for database module."""
import sqlite3
import pytest
from database import connect, init_db


class TestConnect:
    """Tests for the connect function."""

    def test_returns_connection(self, tmp_db):
        conn = connect()
        assert conn is not None
        conn.close()

    def test_foreign_keys_enabled(self, tmp_db):
        conn = connect()
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys")
        result = cur.fetchone()[0]
        conn.close()
        assert result == 1

    def test_journal_mode_wal(self, tmp_db):
        conn = connect()
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode")
        result = cur.fetchone()[0]
        conn.close()
        assert result.lower() == "wal"


class TestInitDb:
    """Tests for the init_db function."""

    def test_creates_students_table(self, initialized_db):
        conn = sqlite3.connect(initialized_db)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='students'")
        assert cur.fetchone() is not None
        conn.close()

    def test_creates_teachers_table(self, initialized_db):
        conn = sqlite3.connect(initialized_db)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teachers'")
        assert cur.fetchone() is not None
        conn.close()

    def test_creates_subjects_table(self, initialized_db):
        conn = sqlite3.connect(initialized_db)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subjects'")
        assert cur.fetchone() is not None
        conn.close()

    def test_creates_exams_table(self, initialized_db):
        conn = sqlite3.connect(initialized_db)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='exams'")
        assert cur.fetchone() is not None
        conn.close()

    def test_exams_table_has_holiday_fields(self, initialized_db):
        conn = sqlite3.connect(initialized_db)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(exams)")
        columns = {row[1] for row in cur.fetchall()}
        conn.close()
        assert {"it_has_holiday", "opening_date", "closing_date"} <= columns

    def test_creates_results_table(self, initialized_db):
        conn = sqlite3.connect(initialized_db)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='results'")
        assert cur.fetchone() is not None
        conn.close()

    def test_creates_division_rules_table(self, initialized_db):
        conn = sqlite3.connect(initialized_db)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='division_rules'")
        assert cur.fetchone() is not None
        conn.close()

    def test_students_table_has_optional_exam_no_column(self, initialized_db):
        conn = sqlite3.connect(initialized_db)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(students)")
        columns = {row[1] for row in cur.fetchall()}
        conn.close()
        assert "exam_no" in columns

    def test_school_profile_has_stamp_and_signature_columns(self, initialized_db):
        conn = sqlite3.connect(initialized_db)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(school_profile)")
        columns = {row[1] for row in cur.fetchall()}
        conn.close()
        assert {
            "school_stamp",
            "head_teacher_signature",
            "academic_master_signature",
            "discipline_master_signature",
            "class_master_signature",
        } <= columns

    def test_creates_enrollments_table(self, initialized_db):
        conn = sqlite3.connect(initialized_db)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='enrollments'")
        assert cur.fetchone() is not None
        conn.close()

    def test_creates_academic_years_table(self, initialized_db):
        conn = sqlite3.connect(initialized_db)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='academic_years'")
        assert cur.fetchone() is not None
        conn.close()

    def test_creates_terms_table(self, initialized_db):
        conn = sqlite3.connect(initialized_db)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='terms'")
        assert cur.fetchone() is not None
        conn.close()

    def test_default_academic_year_created(self, initialized_db):
        conn = sqlite3.connect(initialized_db)
        cur = conn.cursor()
        cur.execute("SELECT year_name, is_active FROM academic_years")
        row = cur.fetchone()
        conn.close()
        assert row is not None
        assert row[0] == "2026"
        assert row[1] == 1

    def test_default_terms_created(self, initialized_db):
        conn = sqlite3.connect(initialized_db)
        cur = conn.cursor()
        cur.execute("SELECT term_name FROM terms ORDER BY id")
        terms = [r[0] for r in cur.fetchall()]
        conn.close()
        assert "Term I" in terms
        assert "Term II" in terms

    def test_default_division_rules_created(self, initialized_db):
        conn = sqlite3.connect(initialized_db)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM division_rules")
        count = cur.fetchone()[0]
        conn.close()
        assert count == 10  # 5 O_LEVEL + 5 A_LEVEL

    def test_default_exams_created(self, initialized_db):
        conn = sqlite3.connect(initialized_db)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM exams")
        count = cur.fetchone()[0]
        conn.close()
        assert count == 0

    def test_default_system_settings_created(self, initialized_db):
        conn = sqlite3.connect(initialized_db)
        cur = conn.cursor()
        cur.execute("SELECT setting_key, setting_value FROM system_settings WHERE setting_key='o_level_counted'")
        row = cur.fetchone()
        conn.close()
        assert row is not None
        assert row[1] == "7"

    def test_system_security_default_passcode(self, initialized_db):
        import hashlib
        import secrets as _secrets
        conn = sqlite3.connect(initialized_db)
        cur = conn.cursor()
        cur.execute("SELECT admin_passcode FROM system_security")
        row = cur.fetchone()
        conn.close()
        stored = row[0]
        assert "$" in stored, "Passcode should use PBKDF2 salt$hash format"
        salt, stored_hash = stored.split("$", 1)
        dk = hashlib.pbkdf2_hmac(
            "sha256", "000000".encode("utf-8"),
            salt.encode("utf-8"), iterations=260000,
        )
        assert _secrets.compare_digest(dk.hex(), stored_hash)

    def test_idempotent_init(self, initialized_db):
        """Calling init_db twice should not raise or duplicate data."""
        init_db()
        conn = sqlite3.connect(initialized_db)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM academic_years")
        count = cur.fetchone()[0]
        conn.close()
        assert count == 1

    def test_only_one_open_exam_per_level(self, initialized_db):
        conn = sqlite3.connect(initialized_db)
        cur = conn.cursor()
        cur.execute("SELECT level, COUNT(*) FROM exams WHERE status='OPEN' GROUP BY level")
        rows = cur.fetchall()
        conn.close()
        for level, count in rows:
            assert count == 1, f"Level {level} has {count} OPEN exams, expected 1"
