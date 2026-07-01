import os
import sqlite3
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox, QProgressDialog

from database import DB_NAME, connect
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


def export_backup(parent, backup_dir=None):
    if backup_dir is None:
        backup_dir = QFileDialog.getExistingDirectory(
            parent,
            "Select Backup Folder",
            os.path.dirname(DB_NAME) or ".",
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
        source = connect()
        dest = sqlite3.connect(backup_path)

        def progress_cb(status, remaining, total):
            done = total - remaining
            percent = 0 if total <= 0 else int((done / total) * 100)
            _set_progress(progress, percent, "Exporting backup")

        source.backup(dest, pages=50, progress=progress_cb)
        dest.close()
        source.close()
        _set_progress(progress, 100, "Backup exported")
        QMessageBox.information(parent, "Backup Export", f"Backup saved to:\n{backup_path}")
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
