"""Unit tests for backup utilities."""

import os
import sqlite3

import backup_utils
from backup_utils import create_pre_operation_backup, create_startup_auto_backup, inspect_backup


class TestPreOperationBackup:
    def test_creates_backup_file(self, initialized_db, tmp_path):
        backup_path = create_pre_operation_backup(
            "promotion wizard",
            backup_dir=str(tmp_path),
        )

        assert os.path.exists(backup_path)
        assert os.path.basename(backup_path).startswith(
            "srms_pre_promotion_wizard_"
        )
        assert backup_path.endswith(".db")

    def test_backup_contains_database_tables(self, initialized_db, tmp_path):
        backup_path = create_pre_operation_backup(
            "results import",
            backup_dir=str(tmp_path),
        )

        conn = sqlite3.connect(backup_path)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='students'"
            )
            assert cur.fetchone() is not None
        finally:
            conn.close()

    def test_inspect_backup_reports_compatible_database_metadata(self, initialized_db, tmp_path):
        backup_path = create_pre_operation_backup(
            "inspection",
            backup_dir=str(tmp_path),
        )

        metadata = inspect_backup(backup_path)

        assert metadata["path"] == backup_path
        assert metadata["students"] >= 0
        assert metadata["exams"] >= 0
        assert metadata["results"] >= 0

    def test_inspect_backup_rejects_non_sqlite_file(self, tmp_path):
        invalid_backup = tmp_path / "not_a_backup.db"
        invalid_backup.write_text("not a sqlite database")

        try:
            inspect_backup(str(invalid_backup))
        except ValueError as error:
            assert "SQLite" in str(error)
        else:
            raise AssertionError("Expected invalid backup to be rejected")

    def test_auto_backup_runs_once_per_day_when_enabled(self, initialized_db, tmp_path, monkeypatch):
        with sqlite3.connect(initialized_db) as conn:
            conn.execute(
                "UPDATE system_settings SET setting_value='1' WHERE setting_key='auto_backup'"
            )

        monkeypatch.setattr(backup_utils, "_default_backup_dir", lambda: str(tmp_path / "pre_operations"))

        first_path = create_startup_auto_backup()
        second_path = create_startup_auto_backup()

        assert first_path == second_path
        assert os.path.exists(first_path)
