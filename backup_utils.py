import os
import sqlite3
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox, QProgressDialog

import database
from database import connect
from db_utils import fetch_one
from event_bus import EventBus


_REQUIRED_BACKUP_TABLES = {
    "students", "exams", "results", "system_settings",
}


def _read_only_database_uri(path):
    """Return a URI that cannot create or modify the selected backup file."""
    return f"{Path(path).resolve().as_uri()}?mode=ro"


def inspect_backup(backup_path):
    """Validate an SRMS SQLite backup and return safe, displayable metadata."""
    path = Path(backup_path)
    if not path.is_file():
        raise ValueError("The selected backup file does not exist.")

    conn = None
    try:
        conn = sqlite3.connect(_read_only_database_uri(path), uri=True)
        integrity = conn.execute("PRAGMA quick_check").fetchone()
        if not integrity or integrity[0] != "ok":
            raise ValueError("The selected backup failed SQLite integrity validation.")

        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        missing_tables = _REQUIRED_BACKUP_TABLES - tables
        if missing_tables:
            missing = ", ".join(sorted(missing_tables))
            raise ValueError(f"The selected file is not a compatible SRMS backup (missing: {missing}).")

        school_row = conn.execute(
            "SELECT school_name FROM school_profile LIMIT 1"
        ).fetchone() if "school_profile" in tables else None
        version_row = conn.execute(
            "SELECT setting_value FROM system_settings WHERE setting_key='schema_version'"
        ).fetchone()

        return {
            "path": str(path),
            "size": path.stat().st_size,
            "school_name": school_row[0] if school_row and school_row[0] else "Not configured",
            "schema_version": version_row[0] if version_row else "Unknown",
            "students": conn.execute("SELECT COUNT(*) FROM students").fetchone()[0],
            "exams": conn.execute("SELECT COUNT(*) FROM exams").fetchone()[0],
            "results": conn.execute("SELECT COUNT(*) FROM results").fetchone()[0],
        }
    except sqlite3.Error as error:
        raise ValueError(f"The selected file is not a readable SQLite backup: {error}") from error
    finally:
        if conn is not None:
            conn.close()


def _make_progress(parent, title):
    progress = QProgressDialog(title, None, 0, 100, parent)
    progress.setWindowTitle(title)
    progress.setWindowModality(Qt.WindowModal if parent else Qt.NonModal)
    progress.setAutoClose(False)
    progress.setAutoReset(False)
    progress.setMinimumDuration(0)
    progress.setValue(0)
    progress.setLabelText(f"{title}\n\nProgress: 0%")
    QApplication.processEvents()
    return progress


def _set_progress(progress, percent, message):
    if progress is None:
        return
    progress.setValue(max(0, min(100, int(percent))))
    progress.setLabelText(f"{message}\n\nProgress: {max(0, min(100, int(percent)))}%")
    QApplication.processEvents()


def _backup_database_to_path(backup_path, progress=None, message="Backing up database"):
    os.makedirs(os.path.dirname(backup_path) or ".", exist_ok=True)
    source = None
    dest = None
    try:
        source = connect()
        dest = sqlite3.connect(backup_path)

        def progress_cb(status, remaining, total):
            done = total - remaining
            percent = 0 if total <= 0 else int((done / total) * 100)
            _set_progress(progress, percent, message)

        source.backup(dest, pages=50, progress=progress_cb)
        _set_progress(progress, 100, message)
        return backup_path
    finally:
        if dest is not None:
            dest.close()
        if source is not None:
            source.close()


def _safe_operation_name(operation_name):
    text = str(operation_name or "operation").strip().lower()
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in text)
    cleaned = "_".join(part for part in cleaned.split("_") if part)
    return cleaned or "operation"


def _default_backup_dir():
    row = fetch_one(
        "SELECT setting_value FROM system_settings WHERE setting_key='backup_folder'"
    )
    configured = row[0] if row and row[0] else "./backups"
    return os.path.join(configured, "pre_operations")


def create_pre_operation_backup(operation_name, backup_dir=None):
    """Create a silent backup before a risky bulk operation.

    Returns the backup path. Raises the original exception if backup fails so
    callers can stop destructive work before it starts.
    """
    backup_dir = backup_dir or _default_backup_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    safe_name = _safe_operation_name(operation_name)
    backup_path = os.path.join(
        backup_dir,
        f"srms_pre_{safe_name}_{timestamp}.db",
    )
    return _backup_database_to_path(
        backup_path,
        progress=None,
        message=f"Backing up before {safe_name}",
    )


def create_startup_auto_backup():
    """Create at most one automatic backup per day when the setting is enabled."""
    row = fetch_one(
        "SELECT setting_value FROM system_settings WHERE setting_key='auto_backup'"
    )
    if not row or row[0] != "1":
        return None

    backup_dir = os.path.join(_default_backup_dir(), "..", "automatic")
    backup_dir = os.path.normpath(backup_dir)
    backup_path = os.path.join(
        backup_dir,
        f"srms_auto_{datetime.now().strftime('%Y%m%d')}.db",
    )
    if os.path.exists(backup_path):
        return backup_path

    return _backup_database_to_path(
        backup_path,
        progress=None,
        message="Creating automatic backup",
    )


def export_backup(parent, backup_dir=None):
    if backup_dir is None:
        backup_dir = QFileDialog.getExistingDirectory(
            parent,
            "Select Backup Folder",
            os.path.dirname(database.DB_NAME) or ".",
        )
    if not backup_dir:
        return False

    os.makedirs(backup_dir, exist_ok=True)
    backup_path = os.path.join(
        backup_dir,
        f"srms_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
    )

    progress = _make_progress(parent, "Exporting backup...")
    try:
        _backup_database_to_path(
            backup_path,
            progress=progress,
            message="Exporting backup",
        )
        _set_progress(progress, 100, "Backup exported")
        QMessageBox.information(
            parent,
            "Backup Export",
            f"Backup saved to:\n{backup_path}",
        )
        return True
    except Exception as error:
        QMessageBox.critical(parent, "Backup Export", f"Backup export failed:\n{error}")
        return False
    finally:
        progress.close()


def import_backup(parent):
    backup_path, _ = QFileDialog.getOpenFileName(
        parent,
        "Import Backup",
        "",
        "SQLite Backup (*.db *.sqlite *.sqlite3);;All Files (*)",
    )
    if not backup_path:
        return False

    try:
        metadata = inspect_backup(backup_path)
    except ValueError as error:
        QMessageBox.critical(parent, "Backup Import", str(error))
        return False

    size_mb = metadata["size"] / (1024 * 1024)
    summary = (
        "Validated backup:\n"
        f"School: {metadata['school_name']}\n"
        f"Schema version: {metadata['schema_version']}\n"
        f"Students: {metadata['students']} | Exams: {metadata['exams']} | Results: {metadata['results']}\n"
        f"File size: {size_mb:.2f} MB\n\n"
        "A safety backup of the current database will be created before restore.\n"
        "Restore this backup?"
    )
    reply = QMessageBox.question(
        parent,
        "Confirm Validated Backup Restore",
        summary,
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
    )
    if reply != QMessageBox.Yes:
        return False

    try:
        safety_backup_path = create_pre_operation_backup("before_restore")
    except Exception as error:
        QMessageBox.critical(
            parent,
            "Backup Import",
            f"Could not create a safety backup. Restore cancelled.\n\n{error}",
        )
        return False

    progress = _make_progress(parent, "Restoring validated backup...")
    source = None
    dest = None
    try:
        source = sqlite3.connect(_read_only_database_uri(backup_path), uri=True)
        dest = connect()

        def progress_cb(status, remaining, total):
            done = total - remaining
            percent = 0 if total <= 0 else int((done / total) * 100)
            _set_progress(progress, percent, "Importing backup")

        source.backup(dest, pages=50, progress=progress_cb)
        dest.close()
        dest = None
        source.close()
        source = None

        # Restore can bring in an older schema. Apply all current migrations
        # before any page reads the restored database.
        database.init_db()

        from cache_utils import ranking_cache
        ranking_cache.clear()
        _set_progress(progress, 100, "Backup imported")
        EventBus.emit("STUDENTS_UPDATED")
        EventBus.emit("RESULTS_UPDATED")
        EventBus.emit("EXAMS_UPDATED")
        EventBus.emit("SUBJECTS_UPDATED")
        EventBus.emit("SCHOOL_PROFILE_UPDATED")
        EventBus.emit("GRADE_RULES_CHANGED")
        EventBus.emit("DIVISION_RULES_CHANGED")
        EventBus.emit("SUBJECT_REQUIREMENTS_CHANGED")
        EventBus.emit("SETTINGS_UPDATED")
        QMessageBox.information(
            parent,
            "Backup Import",
            "Backup restored successfully.\n\n"
            f"Safety backup: {safety_backup_path}\n\n"
            "Please restart SRMS now so every open page reloads the restored settings.",
        )
        return True
    except Exception as error:
        QMessageBox.critical(parent, "Backup Import", f"Backup import failed:\n{error}")
        return False
    finally:
        if dest is not None:
            dest.close()
        if source is not None:
            source.close()
        progress.close()
