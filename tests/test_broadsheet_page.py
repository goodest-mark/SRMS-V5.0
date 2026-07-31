import os
import sqlite3

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from ui.pages.broadsheet_page import BroadsheetPage
from database import connect, init_db


def test_broadsheet_page_initializes_history_level(tmp_db):
    init_db()
    app = QApplication.instance() or QApplication([])
    page = BroadsheetPage()
    assert page.history_level is None
    app.quit()


def test_broadsheet_page_preserves_historical_class_subjects(tmp_db):
    init_db()
    conn = sqlite3.connect(tmp_db)
    cur = conn.cursor()

    # Explicit exam context for this isolated scenario.
    term_id = cur.execute("SELECT id FROM terms WHERE is_active=1 LIMIT 1").fetchone()[0]
    cur.execute(
        "INSERT INTO exams (exam_name, term_id, level, status) VALUES (?, ?, ?, ?)",
        ("Broadsheet Test", term_id, "O_LEVEL", "OPEN"),
    )
    exam_id = cur.lastrowid

    # Create subjects
    cur.execute(
        "INSERT OR IGNORE INTO subjects (subject_name, subject_short_name, level, subject_type) VALUES (?, ?, ?, ?)",
        ("Mathematics", "MATH", "O_LEVEL", "COUNTED"),
    )

    # Student was in Form I at exam time, later moved to Form II
    cur.execute(
        "INSERT OR IGNORE INTO students (admission_no, full_name, gender, class, stream, level) VALUES (?, ?, ?, ?, ?, ?)",
        ("ADM001", "Alice Mwanza", "Female", "Form I", None, "O_LEVEL"),
    )
    cur.execute(
        "INSERT OR IGNORE INTO results (admission_no, subject_name, marks, exam_id, class_name) VALUES (?, ?, ?, ?, ?)",
        ("ADM001", "Mathematics", 85, exam_id, "Form I"),
    )

    year_term = cur.execute("SELECT term_id FROM exams WHERE id=?", (exam_id,)).fetchone()[0]
    cur.execute("SELECT academic_year_id FROM terms WHERE id=?", (year_term,))
    year_id = cur.fetchone()[0]

    cur.execute(
        "INSERT OR IGNORE INTO enrollments (admission_no, subject_name, academic_year_id, term_id) VALUES (?, ?, ?, ?)",
        ("ADM001", "Mathematics", year_id, year_term),
    )

    # Promote student after the exam
    cur.execute("UPDATE students SET class=? WHERE admission_no=?", ("Form II", "ADM001"))
    conn.commit()
    conn.close()

    app = QApplication.instance() or QApplication([])
    page = BroadsheetPage()
    data = page._service.fetch_data(
        exam_id=exam_id,
        class_name="Form I",
        year_id=year_id,
        term_id=year_term,
        level="O_LEVEL",
    ).to_dict()
    assert data is not None
    assert data['rows']
    assert "Mathematics" in data['subjects']
    assert data['subject_headers'][0] == "MATH"
    app.quit()
