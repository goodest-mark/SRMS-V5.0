import os
import sqlite3

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from academic_rules import normalize_subject_type
from database import init_db
from subjects_page import SubjectsPage
from system_state import SystemState


def test_normalize_subject_type_maps_invalid_values_to_level_default():
    assert normalize_subject_type("O_LEVEL", "PRINCIPAL") == "COUNTED"
    assert normalize_subject_type("A_LEVEL", "COUNTED") == "PRINCIPAL"
    assert normalize_subject_type("O_LEVEL", "NOT_COUNTED") == "NOT_COUNTED"


def test_init_db_normalizes_existing_invalid_subject_types(initialized_db):
    conn = sqlite3.connect(initialized_db)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO subjects (subject_name, subject_short_name, level, subject_type)
        VALUES (?, ?, ?, ?)
        """,
        ("Biology", "BIO", "O_LEVEL", "PRINCIPAL"),
    )
    conn.commit()
    conn.close()

    init_db()

    conn = sqlite3.connect(initialized_db)
    cur = conn.cursor()
    cur.execute(
        "SELECT subject_type FROM subjects WHERE subject_name='Biology' AND level='O_LEVEL'"
    )
    assert cur.fetchone()[0] == "COUNTED"
    conn.close()


def test_add_subject_normalizes_type_for_o_level(initialized_db):
    app = QApplication.instance() or QApplication([])
    SystemState.set_level("O_LEVEL")

    page = SubjectsPage()
    page.name.setText("Physics")
    page.subject_type.addItem("PRINCIPAL")
    page.subject_type.setCurrentText("PRINCIPAL")
    page.add_subject()

    conn = sqlite3.connect(initialized_db)
    cur = conn.cursor()
    cur.execute(
        "SELECT subject_type FROM subjects WHERE subject_name='Physics' AND level='O_LEVEL'"
    )
    assert cur.fetchone()[0] == "COUNTED"
    conn.close()

    app.quit()
