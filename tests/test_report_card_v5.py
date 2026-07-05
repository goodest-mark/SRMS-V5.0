"""Tests for student report-card selection and generation helpers."""

import os
import sqlite3

import report_card_v5 as report_card_module
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

    cur.execute("SELECT id FROM academic_years ORDER BY id DESC LIMIT 1")
    year_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM terms WHERE academic_year_id=? ORDER BY id LIMIT 1", (year_id,))
    term_id = cur.fetchone()[0]

    cur.execute(
        """
        INSERT INTO exams (exam_name, term_id, level, status)
        VALUES ('Open Report Exam', ?, 'O_LEVEL', 'OPEN')
        """,
        (term_id,),
    )
    open_exam_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO exams (exam_name, term_id, level, status)
        VALUES ('Closed Report Exam', ?, 'O_LEVEL', 'CLOSED')
        """,
        (term_id,),
    )
    closed_exam_id = cur.lastrowid

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
    def test_student_page_metrics_uses_rank_division_points_percentage_status(self):
        table = report_card_module._build_student_page_metrics(
            report_card_module._get_student_styles(),
            position=5,
            total_students=45,
            division="I",
            points=7,
            average=74.55,
            status="READY",
        )

        labels = [cell.getPlainText() for cell in table._cellvalues[0]]
        values = [cell.getPlainText() for cell in table._cellvalues[1]]

        assert labels == ["RANK", "DIVISION", "POINTS", "PERCENTAGE", "STATUS"]
        assert values[0] == "5 / 45"
        assert values[3] == "74.55%"

    def test_student_page_results_uses_short_subject_headers(self):
        table = report_card_module._build_student_page_results(
            report_card_module._get_student_styles(),
            short_names=["BIO", "CHEM", "PHYS"],
            marks=[56, 78, 64],
            grades=["C/", "A/", "B"],
        )

        header = [cell.getPlainText() for cell in table._cellvalues[0]]
        marks_row = [cell.getPlainText() for cell in table._cellvalues[1]]
        grades_row = [cell.getPlainText() for cell in table._cellvalues[2]]

        assert header == ["ITEM", "BIO", "CHEM", "PHYS"]
        assert marks_row == ["MARKS (%)", "56", "78", "64"]
        assert grades_row == ["GRADE", "C/", "A/", "B"]

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

    def test_report_uses_historical_class_not_current_class(self, initialized_db, monkeypatch):
        open_exam_id, _, _ = _seed_student_report_data(initialized_db)
        conn = sqlite3.connect(initialized_db)
        cur = conn.cursor()
        cur.execute("UPDATE students SET exam_no='EX/2026/001' WHERE admission_no='ADM-RPT'")
        cur.execute("UPDATE results SET class_name='Form I' WHERE admission_no='ADM-RPT' AND exam_id=?", (open_exam_id,))
        cur.execute("UPDATE students SET class='Form II' WHERE admission_no='ADM-RPT'")
        conn.commit()
        conn.close()

        captured = {}

        class FakeDoc:
            def __init__(self, *args, **kwargs):
                self.width = 1
                self.height = 1

            def build(self, *args, **kwargs):
                return None

        def fake_content(**kwargs):
            captured["class_name"] = kwargs["class_name"]
            return []

        monkeypatch.setattr(report_card_module, "SimpleDocTemplate", FakeDoc)
        monkeypatch.setattr(report_card_module, "_build_student_report_content", fake_content)

        success, result = generate_student_report_card(
            None,
            "ADM-RPT",
            "O_LEVEL",
            save_path=str(initialized_db) + ".pdf",
            exam_id=open_exam_id,
        )

        assert success is True
        assert captured["class_name"] == "Form I"
        assert result.endswith(".pdf")

    def test_report_receives_exam_number_when_present(self, initialized_db, monkeypatch):
        open_exam_id, _, _ = _seed_student_report_data(initialized_db)
        conn = sqlite3.connect(initialized_db)
        cur = conn.cursor()
        cur.execute("UPDATE students SET exam_no='EX/2026/002' WHERE admission_no='ADM-RPT'")
        conn.commit()
        conn.close()

        captured = {}

        class FakeDoc:
            def __init__(self, *args, **kwargs):
                self.width = 1
                self.height = 1

            def build(self, *args, **kwargs):
                return None

        def fake_content(**kwargs):
            captured["exam_no"] = kwargs["exam_no"]
            return []

        monkeypatch.setattr(report_card_module, "SimpleDocTemplate", FakeDoc)
        monkeypatch.setattr(report_card_module, "_build_student_report_content", fake_content)

        success, result = generate_student_report_card(
            None,
            "ADM-RPT",
            "O_LEVEL",
            save_path=str(initialized_db) + ".pdf",
            exam_id=open_exam_id,
        )

        assert success is True
        assert captured["exam_no"] == "EX/2026/002"
        assert result.endswith(".pdf")

    def test_student_comments_column_is_available(self, initialized_db):
        import sqlite3
        conn = sqlite3.connect(initialized_db)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(students)")
        columns = [row[1] for row in cur.fetchall()]
        conn.close()

        assert "comments" in columns

    def test_signature_section_only_exposes_head_teacher_signature(self):
        table = report_card_module._build_signatures(
            report_card_module._get_student_styles(),
            head_teacher="Head Teacher Name",
            academic_master="Academic Master Name",
            discipline_master="Discipline Master Name",
            class_master="Class Master Name",
            head_teacher_signature=None,
            academic_master_signature=None,
            discipline_master_signature=None,
            class_master_signature=None,
            stamp_path=None,
        )

        left_block = table._cellvalues[0][0]
        right_block = table._cellvalues[0][1]
        left_text = " ".join(
            cell.getPlainText()
            for row in left_block._cellvalues
            for cell in row
            if hasattr(cell, "getPlainText")
        )
        right_text = " ".join(
            cell.getPlainText()
            for row in right_block._cellvalues
            for cell in row
            if hasattr(cell, "getPlainText")
        )

        assert "HEAD TEACHER / HEADMASTER SIGNATURE" in left_text
        assert "Head Teacher Name" in left_text
        assert "ACADEMIC MASTER" not in left_text
        assert "DISCIPLINE MASTER" not in left_text
        assert "CLASS MASTER" not in left_text
        assert "SCHOOL OFFICIAL STAMP" in right_text
