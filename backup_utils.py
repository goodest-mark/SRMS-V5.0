import os
import sqlite3
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox, QProgressDialog

import database
from database import connect
from db_utils import fetch_one
from event_bus import EventBus


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
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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

    progress = _make_progress(parent, "Importing backup...")
    try:
        source = sqlite3.connect(backup_path)
        dest = connect()

        def progress_cb(status, remaining, total):
            done = total - remaining
            percent = 0 if total <= 0 else int((done / total) * 100)
            _set_progress(progress, percent, "Importing backup")

        source.backup(dest, pages=50, progress=progress_cb)
        dest.close()
        source.close()
        _set_progress(progress, 100, "Backup imported")
        EventBus.emit("STUDENTS_UPDATED")
        EventBus.emit("RESULTS_UPDATED")
        EventBus.emit("EXAMS_UPDATED")
        QMessageBox.information(parent, "Backup Import", "Backup imported successfully.")
        return True
    except Exception as error:
        QMessageBox.critical(parent, "Backup Import", f"Backup import failed:\n{error}")
        return False
    finally:
        progress.close()
