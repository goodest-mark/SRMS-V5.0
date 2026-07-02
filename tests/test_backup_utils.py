"""Unit tests for backup utilities."""

import os
import sqlite3

from backup_utils import create_pre_operation_backup


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
