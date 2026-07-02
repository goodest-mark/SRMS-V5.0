"""Tests for student report-card selection and generation helpers."""

import os
import sqlite3

from report_card_v5 import generate_student_report_card, list_student_report_exams


def _seed_student_report_data(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR IGNORE INTO subjects
        (subject_name, subject_short_name, level, subject_type)
        VALUES ('Mathematics', 'MATH', 'O_LEVEL', 'COUNTED')
        """
    )
    cur.execute(
        """
        INSERT OR IGNORE INTO students
        (admission_no, full_name, gender, class, stream, level)
        VALUES ('ADM-RPT', 'Report Student', 'Female', 'Form I', 'A', 'O_LEVEL')
        """
    )

    cur.execute(
        "SELECT id FROM exams WHERE level='O_LEVEL' AND status='OPEN' ORDER BY id DESC LIMIT 1"
    )
    open_exam_id = cur.fetchone()[0]
    cur.execute(
        "SELECT id FROM exams WHERE level='O_LEVEL' AND status='CLOSED' ORDER BY id DESC LIMIT 1"
    )
    closed_exam_id = cur.fetchone()[0]

    cur.execute(
        """
        INSERT INTO exams (exam_name, term_id, level, status)
        SELECT 'Completed Report Exam', term_id, level, 'COMPLETED'
        FROM exams
        WHERE id=?
        """,
        (open_exam_id,),
    )
    completed_exam_id = cur.lastrowid

    cur.executemany(
        """
        INSERT OR REPLACE INTO results
        (admission_no, subject_name, marks, exam_id)
        VALUES (?, ?, ?, ?)
        """,
        [
            ("ADM-RPT", "Mathematics", 80, open_exam_id),
            ("ADM-RPT", "Mathematics", 70, closed_exam_id),
            ("ADM-RPT", "Mathematics", 90, completed_exam_id),
        ],
    )

    conn.commit()
    conn.close()
    return open_exam_id, closed_exam_id, completed_exam_id


class TestStudentReportCards:
    def test_report_exam_list_includes_all_statuses_with_results(self, initialized_db):
        open_exam_id, closed_exam_id, completed_exam_id = _seed_student_report_data(
            initialized_db
        )

        reports = list_student_report_exams("ADM-RPT", "O_LEVEL")
        exam_ids = {report["exam_id"] for report in reports}

        assert open_exam_id in exam_ids
        assert closed_exam_id in exam_ids
        assert completed_exam_id in exam_ids

    def test_can_generate_report_for_exact_exam(self, initialized_db, tmp_path):
        open_exam_id, _, _ = _seed_student_report_data(initialized_db)
        save_path = tmp_path / "student_report.pdf"

        success, result = generate_student_report_card(
            None,
            "ADM-RPT",
            "O_LEVEL",
            save_path=str(save_path),
            exam_id=open_exam_id,
        )

        assert success is True
        assert result == str(save_path)
        assert os.path.exists(save_path)
        assert os.path.getsize(save_path) > 0
