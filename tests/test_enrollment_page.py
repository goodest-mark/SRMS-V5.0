import os
import sqlite3

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from database import init_db
from enrollment_page import EnrollmentPage
from system_state import SystemState


def test_enrollment_page_preview_mode_disables_edits(tmp_db):
    init_db()
    app = QApplication.instance() or QApplication([])

    page = EnrollmentPage()
    page.enrollment_mode_checkbox.setChecked(False)
    page.set_enrollment_mode(False)

    assert not page.save_btn.isEnabled()
    assert not page.enrollment_table.isEnabled()
    assert "Preview" in page.preview_label.text()

    app.quit()


def test_enrollment_page_shows_only_student_name(initialized_db):
    app = QApplication.instance() or QApplication([])

    conn = sqlite3.connect(initialized_db)
    cur = conn.cursor()
    cur.execute("SELECT id FROM academic_years ORDER BY id LIMIT 1")
    year_id = cur.fetchone()[0]
    cur.execute(
        "SELECT id FROM terms WHERE academic_year_id=? ORDER BY id LIMIT 1",
        (year_id,),
    )
    term_id = cur.fetchone()[0]
    cur.execute(
        """
        INSERT INTO students (admission_no, exam_no, full_name, gender, class, stream, level, comments)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("ADM001", "EX001", "Alice Mwanza", "Female", "Form I", "A", "O_LEVEL", ""),
    )
    cur.execute(
        """
        INSERT INTO subjects (subject_name, subject_short_name, level, subject_type)
        VALUES (?, ?, ?, ?)
        """,
        ("Mathematics", "MATH", "O_LEVEL", "COUNTED"),
    )
    cur.execute(
        """
        INSERT INTO enrollments (admission_no, subject_name, class_name, academic_year_id, term_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("ADM001", "Mathematics", "Form I", year_id, term_id),
    )
    conn.commit()
    conn.close()

    SystemState.set_level("O_LEVEL")
    page = EnrollmentPage()
    page.year_box.setCurrentIndex(page.year_box.findData(year_id))
    page.term_box.setCurrentIndex(page.term_box.findData(term_id))
    page.class_box.setCurrentText("Form I")
    page.load_students()

    assert page.enrollment_table.item(0, 0).text() == "Alice Mwanza"
    assert page.enrollment_table.item(0, 0).toolTip() == "ADM001"

    app.quit()
