"""Shared combo-box data loaders for academic-context filters.

Many pages (broadsheet, report book, requirements, enrollment, readiness,
results dashboard, excel import) need identical year/term/exam/class combo
loading logic.  This module eliminates that duplication.
"""

from db_utils import fetch_all
from class_utils import get_classes
from system_state import SystemState


def load_years(combo):
    """Populate a year combo box, preserving the current selection."""
    current = combo.currentData()
    combo.blockSignals(True)
    combo.clear()
    for row in fetch_all(
        "SELECT id, year_name FROM academic_years ORDER BY year_name DESC"
    ):
        combo.addItem(row[1], row[0])
    _restore_by_data(combo, current)
    combo.blockSignals(False)


def load_terms(combo, year_id):
    """Populate a term combo box for the given *year_id*."""
    current = combo.currentData()
    combo.blockSignals(True)
    combo.clear()
    if year_id:
        for row in fetch_all(
            "SELECT id, term_name FROM terms WHERE academic_year_id=? ORDER BY term_name",
            (year_id,),
        ):
            combo.addItem(row[1], row[0])
    _restore_by_data(combo, current)
    combo.blockSignals(False)


def load_exams(combo, term_id, level=None, *, status_filter=None):
    """Populate an exam combo box for the given *term_id*.

    Args:
        combo: QComboBox to populate.
        term_id: term foreign-key value (may be ``None``).
        level: education level string; defaults to ``SystemState.get_level()``.
        status_filter: optional exam status string (e.g. ``'OPEN'``).
            When ``None`` all statuses are included.
    """
    current = combo.currentData()
    combo.blockSignals(True)
    combo.clear()
    if term_id:
        if level is None:
            level = SystemState.get_level()
        query = "SELECT id, exam_name FROM exams WHERE term_id=? AND level=? AND status!='COMPLETED'"
        params = [term_id, level]
        if status_filter:
            query += " AND status=?"
            params.append(status_filter)
        query += " ORDER BY id"
        for row in fetch_all(query, tuple(params)):
            combo.addItem(row[1], row[0])
    _restore_by_data(combo, current)
    combo.blockSignals(False)


def load_classes(combo, *, placeholder=None):
    """Reload a class combo box, preserving the current selection.

    Args:
        combo: QComboBox to populate.
        placeholder: optional first entry (e.g. ``'-- Select Class --'``).
    """
    current = combo.currentText()
    combo.blockSignals(True)
    combo.clear()
    if placeholder:
        combo.addItem(placeholder)
    combo.addItems(get_classes())
    _restore_by_text(combo, current)
    combo.blockSignals(False)


def load_open_exams(combo, level=None):
    """Populate an exam combo box with OPEN exams for the given *level*.

    This variant queries exams directly by level and status without
    requiring a term_id, matching the pattern used by results_page,
    results_dashboard, and readiness_page.
    """
    current = combo.currentData()
    if level is None:
        level = SystemState.get_level()
    combo.blockSignals(True)
    combo.clear()
    for row in fetch_all(
        "SELECT id, exam_name FROM exams WHERE level=? AND status='OPEN' ORDER BY id",
        (level,),
    ):
        combo.addItem(row[1], row[0])
    _restore_by_data(combo, current)
    combo.blockSignals(False)


def load_results_exams(combo, level=None):
    """Populate exams usable in Results Entry.

    OPEN exams are editable. COMPLETED exams are visible for read-only review.
    CLOSED exams remain hidden because they are inactive drafts/history slots.
    """
    current = combo.currentData()
    if level is None:
        level = SystemState.get_level()
    combo.blockSignals(True)
    combo.clear()
    for exam_id, exam_name, status in fetch_all(
        """
        SELECT id, exam_name, status
        FROM exams
        WHERE level=?
          AND status IN ('OPEN', 'CLOSED')
        ORDER BY
            CASE status WHEN 'OPEN' THEN 0 ELSE 1 END,
            id DESC
        """,
        (level,),
    ):
        label = exam_name if status == "OPEN" else f"{exam_name} [CLOSED]"
        combo.addItem(label, exam_id)
    _restore_by_data(combo, current)
    combo.blockSignals(False)


def load_completed_exams(combo, term_id=None, level=None, search_text=""):
    """Populate an exam combo box with COMPLETED exams for historical review."""
    current = combo.currentData()
    if level is None:
        level = SystemState.get_level()
    combo.blockSignals(True)
    combo.clear()
    query = """
        SELECT id, exam_name
        FROM exams
        WHERE level=?
          AND status='COMPLETED'
    """
    params = [level]
    if term_id:
        query += " AND term_id=?"
        params.append(term_id)
    if search_text:
        query += " AND exam_name LIKE ?"
        params.append(f"%{search_text}%")
    query += " ORDER BY exam_name"
    for row in fetch_all(query, tuple(params)):
        combo.addItem(f"{row[1]} [COMPLETED]", row[0])
    _restore_by_data(combo, current)
    combo.blockSignals(False)


def load_all_exams(combo, level=None):
    """Populate an exam combo box with active exams for *level*."""
    current = combo.currentData()
    if level is None:
        level = SystemState.get_level()
    combo.blockSignals(True)
    combo.clear()
    for row in fetch_all(
        "SELECT id, exam_name FROM exams WHERE level=? AND status!='COMPLETED' ORDER BY id DESC",
        (level,),
    ):
        combo.addItem(row[1], row[0])
    _restore_by_data(combo, current)
    combo.blockSignals(False)


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _restore_by_data(combo, previous_data):
    """Try to re-select the item whose user-data matches *previous_data*."""
    if previous_data is not None:
        idx = combo.findData(previous_data)
        if idx >= 0:
            combo.setCurrentIndex(idx)
            return
    if combo.count() > 0:
        combo.setCurrentIndex(0)


def _restore_by_text(combo, previous_text):
    """Try to re-select the item whose display text matches *previous_text*."""
    if previous_text:
        idx = combo.findText(previous_text)
        if idx >= 0:
            combo.setCurrentIndex(idx)
            return
    if combo.count() > 0:
        combo.setCurrentIndex(0)
