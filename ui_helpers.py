"""Shared UI helper functions to eliminate repeated dialog/widget boilerplate."""

import re

from PySide6.QtWidgets import QMessageBox, QComboBox


def get_subject_short_name(subject_name, subject_short_name=None):
    """Return a normalized 4-letter subject abbreviation."""
    if subject_short_name:
        cleaned = re.sub(r"[^A-Z0-9]", "", str(subject_short_name).strip().upper())
        return cleaned[:4] if cleaned else str(subject_short_name).strip().upper()

    if not subject_name:
        return ""

    text = str(subject_name).strip().upper()
    tokens = re.findall(r"[A-Z0-9]+", text)
    if len(tokens) > 1:
        abbr = "".join(token[0] for token in tokens)[:4]
        if len(abbr) == 4:
            return abbr
    compact = re.sub(r"[^A-Z0-9]", "", text)
    return compact[:4] if len(compact) >= 4 else compact


def confirm_action(parent, title, message):
    """Show a Yes/No confirmation dialog. Returns True if user clicked Yes."""
    reply = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.Yes | QMessageBox.No,
    )
    return reply == QMessageBox.Yes


def show_error(parent, message, title="Error"):
    """Show a warning message box."""
    QMessageBox.warning(parent, title, message)


def show_info(parent, message, title="Success"):
    """Show an informational message box."""
    QMessageBox.information(parent, title, message)


def load_combo(combo, items, block_signals=True):
    """Reload a QComboBox with (text, data) tuples.

    Args:
        combo: QComboBox instance
        items: list of (display_text, user_data) tuples, or plain strings
        block_signals: temporarily block signals during reload
    """
    if block_signals:
        combo.blockSignals(True)
    combo.clear()
    for item in items:
        if isinstance(item, (list, tuple)):
            combo.addItem(str(item[0]), item[1] if len(item) > 1 else None)
        else:
            combo.addItem(str(item))
    if block_signals:
        combo.blockSignals(False)
