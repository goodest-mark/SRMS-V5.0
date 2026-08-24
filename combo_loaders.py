"""Shared combo-box data loaders for academic-context filters.

All loaders now show ALL years and terms (active and inactive).
Inactive items are shown with a [ARCHIVED] suffix.
"""

from db_utils import fetch_all
from class_utils import get_classes
from system_state import SystemState


def load_years(combo):
    """Populate a year combo box with all years (active + inactive)."""
    current = combo.currentData()
    combo.blockSignals(True)
    combo.clear()
    for row in fetch_all("SELECT id, year_name, is_active FROM academic_years ORDER BY year_name DESC"):
        year_id, year_name, is_active = row
        label = f"{year_name} [ARCHIVED]" if not is_active else year_name
        combo.addItem(label, year_id)
    _restore_by_data(combo, current)
    combo.blockSignals(False)


def load_terms(combo, year_id):
    """Populate a term combo box for the given *year_id* (all terms)."""
    current = combo.currentData()
    combo.blockSignals(True)
    combo.clear()
    if year_id:
        for row in fetch_all("SELECT id, term_name, is_active FROM terms WHERE academic_year_id=? ORDER BY term_name", (year_id,)):
            term_id, term_name, is_active = row
            label = f"{term_name} [ARCHIVED]" if not is_active else term_name
            combo.addItem(label, term_id)
    _restore_by_data(combo, current)
    combo.blockSignals(False)


def load_exams(combo, term_id, level=None, *, status_filter=None):
    """Populate an exam combo box for the given *term_id*."""
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
    """Reload a class combo box, preserving the current selection."""
    current = combo.currentText()
    combo.blockSignals(True)
    combo.clear()
    if placeholder:
        combo.addItem(placeholder)
    combo.addItems(get_classes())
    _restore_by_text(combo, current)
    combo.blockSignals(False)


def load_streams(combo, *, class_name=None, exam_id=None, level=None,
                 include_all=True):
    """Populate stream choices for a class, retaining ``None`` for all streams.

    Current student streams are included for results entry.  When an exam is
    supplied, stored result streams are included too, so old historical views
    remain selectable after a student changes stream.
    """
    current = combo.currentData()
    combo.blockSignals(True)
    combo.clear()
    if include_all:
        combo.addItem("All Streams", None)

    if level is None:
        level = SystemState.get_level()
    if not class_name:
        combo.blockSignals(False)
        return

    params = [class_name, level]
    query = """
        SELECT DISTINCT TRIM(stream)
        FROM students
        WHERE class=? AND level=? AND TRIM(COALESCE(stream, '')) != ''
    """
    if exam_id is not None:
        query += """
            UNION
            SELECT DISTINCT TRIM(COALESCE(r.stream, s.stream))
            FROM results r
            JOIN students s ON s.admission_no = r.admission_no
            WHERE r.exam_id=?
              AND COALESCE(r.class_name, s.class)=?
              AND s.level=?
              AND TRIM(COALESCE(r.stream, s.stream, '')) != ''
        """
        params.extend([exam_id, class_name, level])
    query += " ORDER BY 1 COLLATE NOCASE"
    for (stream,) in fetch_all(query, tuple(params)):
        combo.addItem(stream, stream)
    _restore_by_data(combo, current)
    combo.blockSignals(False)


def load_open_exams(combo, level=None):
    """Populate an exam combo box with OPEN exams for the given *level*."""
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
    """Populate exams usable in Results Entry."""
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


def load_completed_exams(combo, year_id=None, term_id=None, level=None, search_text=""):
    """Populate an exam combo box with COMPLETED exams for historical review."""
    current = combo.currentData()
    if level is None:
        level = SystemState.get_level()
    combo.blockSignals(True)
    combo.clear()
    query = """
        SELECT e.id, e.exam_name
        FROM exams e
        JOIN terms t ON e.term_id = t.id
        WHERE e.level=?
          AND e.status='COMPLETED'
    """
    params = [level]
    if year_id:
        query += " AND t.academic_year_id=?"
        params.append(year_id)
    if term_id:
        query += " AND term_id=?"
        params.append(term_id)
    if search_text:
        query += " AND e.exam_name LIKE ?"
        params.append(f"%{search_text}%")
    query += " ORDER BY e.exam_name, e.id DESC"
    rows = fetch_all(query, tuple(params))
    if not rows and year_id and term_id:
        fallback_query = """
            SELECT e.id, e.exam_name
            FROM exams e
            JOIN terms t ON e.term_id = t.id
            WHERE e.level=?
              AND e.status='COMPLETED'
              AND t.academic_year_id=?
        """
        fallback_params = [level, year_id]
        if search_text:
            fallback_query += " AND e.exam_name LIKE ?"
            fallback_params.append(f"%{search_text}%")
        fallback_query += " ORDER BY e.exam_name, e.id DESC"
        rows = fetch_all(fallback_query, tuple(fallback_params))
    for exam_id, exam_name in rows:
        combo.addItem(f"{exam_name} [COMPLETED]", exam_id)
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


def load_all_exams_for_report(combo, year_id=None, term_id=None, level=None, search_text=""):
    """Load ALL exams (OPEN, CLOSED, COMPLETED) for the Report Book dropdown.
    Shows status in the label.
    """
    current = combo.currentData()
    if level is None:
        level = SystemState.get_level()
    combo.blockSignals(True)
    combo.clear()
    query = """
        SELECT e.id, e.exam_name, e.status
        FROM exams e
        JOIN terms t ON e.term_id = t.id
        WHERE e.level=?
    """
    params = [level]
    if year_id:
        query += " AND t.academic_year_id=?"
        params.append(year_id)
    if term_id:
        query += " AND term_id=?"
        params.append(term_id)
    if search_text:
        query += " AND e.exam_name LIKE ?"
        params.append(f"%{search_text}%")
    query += " ORDER BY e.status, e.exam_name, e.id DESC"
    rows = fetch_all(query, tuple(params))
    for exam_id, exam_name, status in rows:
        label = f"{exam_name} [{status}]"
        combo.addItem(label, exam_id)
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
