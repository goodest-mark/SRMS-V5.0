"""Unit tests for ranking_engine module."""
import sqlite3
import pytest
from database import connect, init_db
from ranking_engine import compute_student_scores


@pytest.fixture
def db_with_results(initialized_db):
    """Set up a database with students, subjects, and results for ranking tests."""
    conn = sqlite3.connect(initialized_db)
    cur = conn.cursor()

    # Get the active exam
    cur.execute("SELECT id FROM exams WHERE level='O_LEVEL' AND status='OPEN' LIMIT 1")
    exam_id = cur.fetchone()[0]

    # Add O-Level subjects (COUNTED type)
    o_level_subjects = [
        ("Mathematics", "MATH", "O_LEVEL", "COUNTED"),
        ("English", "ENG", "O_LEVEL", "COUNTED"),
        ("Biology", "BIO", "O_LEVEL", "COUNTED"),
        ("Chemistry", "CHEM", "O_LEVEL", "COUNTED"),
        ("Physics", "PHY", "O_LEVEL", "COUNTED"),
        ("Geography", "GEO", "O_LEVEL", "COUNTED"),
        ("History", "HIST", "O_LEVEL", "COUNTED"),
        ("Kiswahili", "KIS", "O_LEVEL", "COUNTED"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO subjects (subject_name, subject_short_name, level, subject_type) VALUES (?, ?, ?, ?)",
        o_level_subjects,
    )

    # Add students
    students = [
        ("ADM001", "Alice Mwanza", "Female", "Form I", None, "O_LEVEL"),
        ("ADM002", "Bob Kimaro", "Male", "Form I", None, "O_LEVEL"),
        ("ADM003", "Carol Temba", "Female", "Form I", None, "O_LEVEL"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO students (admission_no, full_name, gender, class, stream, level) VALUES (?, ?, ?, ?, ?, ?)",
        students,
    )

    # Add results for Alice (all 8 subjects - complete)
    alice_marks = [
        ("ADM001", "Mathematics", 85, exam_id),
        ("ADM001", "English", 78, exam_id),
        ("ADM001", "Biology", 72, exam_id),
        ("ADM001", "Chemistry", 68, exam_id),
        ("ADM001", "Physics", 90, exam_id),
        ("ADM001", "Geography", 65, exam_id),
        ("ADM001", "History", 60, exam_id),
        ("ADM001", "Kiswahili", 55, exam_id),
    ]

    # Add results for Bob (all 8 subjects - complete)
    bob_marks = [
        ("ADM002", "Mathematics", 70, exam_id),
        ("ADM002", "English", 65, exam_id),
        ("ADM002", "Biology", 60, exam_id),
        ("ADM002", "Chemistry", 55, exam_id),
        ("ADM002", "Physics", 75, exam_id),
        ("ADM002", "Geography", 50, exam_id),
        ("ADM002", "History", 48, exam_id),
        ("ADM002", "Kiswahili", 52, exam_id),
    ]

    # Add results for Carol (only 5 subjects - incomplete)
    carol_marks = [
        ("ADM003", "Mathematics", 90, exam_id),
        ("ADM003", "English", 88, exam_id),
        ("ADM003", "Biology", 85, exam_id),
        ("ADM003", "Chemistry", 80, exam_id),
        ("ADM003", "Physics", 92, exam_id),
    ]

    all_marks = alice_marks + bob_marks + carol_marks
    cur.executemany(
        "INSERT OR IGNORE INTO results (admission_no, subject_name, marks, exam_id) VALUES (?, ?, ?, ?)",
        all_marks,
    )

    conn.commit()
    conn.close()

    return {"exam_id": exam_id, "db_path": initialized_db}


@pytest.fixture
def db_with_average_ranking_case(initialized_db):
    """Set up a pair of ready students where average and total marks disagree."""
    conn = sqlite3.connect(initialized_db)
    cur = conn.cursor()

    cur.execute("SELECT id FROM exams WHERE level='O_LEVEL' AND status='OPEN' LIMIT 1")
    exam_id = cur.fetchone()[0]

    subjects = [
        ("Mathematics", "MATH", "O_LEVEL", "COUNTED"),
        ("English", "ENG", "O_LEVEL", "COUNTED"),
        ("Biology", "BIO", "O_LEVEL", "COUNTED"),
        ("Chemistry", "CHEM", "O_LEVEL", "COUNTED"),
        ("Physics", "PHY", "O_LEVEL", "COUNTED"),
        ("Geography", "GEO", "O_LEVEL", "COUNTED"),
        ("History", "HIST", "O_LEVEL", "COUNTED"),
        ("Life Skills", "LSK", "O_LEVEL", "NOT_COUNTED"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO subjects (subject_name, subject_short_name, level, subject_type) VALUES (?, ?, ?, ?)",
        subjects,
    )

    cur.executemany(
        "INSERT OR IGNORE INTO students (admission_no, full_name, gender, class, stream, level) VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("ADM101", "High Average", "Female", "Form I", None, "O_LEVEL"),
            ("ADM102", "High Total", "Male", "Form I", None, "O_LEVEL"),
        ],
    )

    high_average_marks = [
        ("ADM101", "Mathematics", 90, exam_id),
        ("ADM101", "English", 90, exam_id),
        ("ADM101", "Biology", 90, exam_id),
        ("ADM101", "Chemistry", 90, exam_id),
        ("ADM101", "Physics", 90, exam_id),
        ("ADM101", "Geography", 90, exam_id),
        ("ADM101", "History", 90, exam_id),
    ]
    high_total_marks = [
        ("ADM102", "Mathematics", 80, exam_id),
        ("ADM102", "English", 80, exam_id),
        ("ADM102", "Biology", 80, exam_id),
        ("ADM102", "Chemistry", 80, exam_id),
        ("ADM102", "Physics", 80, exam_id),
        ("ADM102", "Geography", 80, exam_id),
        ("ADM102", "History", 80, exam_id),
        ("ADM102", "Life Skills", 100, exam_id),
    ]

    cur.executemany(
        "INSERT OR IGNORE INTO results (admission_no, subject_name, marks, exam_id) VALUES (?, ?, ?, ?)",
        high_average_marks + high_total_marks,
    )

    conn.commit()
    conn.close()

    return {"exam_id": exam_id, "db_path": initialized_db}


@pytest.fixture
def db_with_a_level_results(initialized_db):
    """Set up database with A-Level results."""
    conn = sqlite3.connect(initialized_db)
    cur = conn.cursor()

    cur.execute("SELECT id FROM exams WHERE level='A_LEVEL' AND status='OPEN' LIMIT 1")
    exam_id = cur.fetchone()[0]

    # Add A-Level subjects (PRINCIPAL type)
    a_level_subjects = [
        ("Physics AL", "PHY", "A_LEVEL", "PRINCIPAL"),
        ("Chemistry AL", "CHEM", "A_LEVEL", "PRINCIPAL"),
        ("Mathematics AL", "MATH", "A_LEVEL", "PRINCIPAL"),
        ("Biology AL", "BIO", "A_LEVEL", "PRINCIPAL"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO subjects (subject_name, subject_short_name, level, subject_type) VALUES (?, ?, ?, ?)",
        a_level_subjects,
    )

    # Add A-Level student
    cur.execute(
        "INSERT OR IGNORE INTO students (admission_no, full_name, gender, class, stream, level) VALUES (?, ?, ?, ?, ?, ?)",
        ("ADM010", "David Mushi", "Male", "Form V", None, "A_LEVEL"),
    )

    # Results for David (3 principal subjects)
    marks = [
        ("ADM010", "Physics AL", 75, exam_id),
        ("ADM010", "Chemistry AL", 68, exam_id),
        ("ADM010", "Mathematics AL", 82, exam_id),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO results (admission_no, subject_name, marks, exam_id) VALUES (?, ?, ?, ?)",
        marks,
    )

    conn.commit()
    conn.close()

    return {"exam_id": exam_id, "db_path": initialized_db}


class TestComputeStudentScoresOLevel:
    def test_returns_list(self, db_with_results):
        ranking = compute_student_scores("O_LEVEL", exam_id=db_with_results["exam_id"])
        assert isinstance(ranking, list)

    def test_ready_students_have_position(self, db_with_results):
        ranking = compute_student_scores("O_LEVEL", exam_id=db_with_results["exam_id"])
        ready = [r for r in ranking if r["status"] == "READY"]
        for student in ready:
            assert isinstance(student["position"], int)
            assert student["position"] > 0

    def test_incomplete_students_have_dash_position(self, db_with_results):
        ranking = compute_student_scores("O_LEVEL", exam_id=db_with_results["exam_id"])
        incomplete = [r for r in ranking if r["status"] == "INCOMPLETE"]
        for student in incomplete:
            assert student["position"] == "-"

    def test_carol_is_incomplete_with_5_subjects(self, db_with_results):
        ranking = compute_student_scores("O_LEVEL", exam_id=db_with_results["exam_id"])
        carol = next((r for r in ranking if r["admission"] == "ADM003"), None)
        assert carol is not None
        assert carol["status"] == "INCOMPLETE"
        assert carol["subjects"] == "5/7"

    def test_alice_ranked_above_bob(self, db_with_results):
        ranking = compute_student_scores("O_LEVEL", exam_id=db_with_results["exam_id"])
        alice = next(r for r in ranking if r["admission"] == "ADM001")
        bob = next(r for r in ranking if r["admission"] == "ADM002")
        assert alice["position"] < bob["position"]

    def test_ready_students_sorted_by_average_descending(self, db_with_results):
        ranking = compute_student_scores("O_LEVEL", exam_id=db_with_results["exam_id"])
        ready = [r for r in ranking if r["status"] == "READY"]
        averages = [r["average"] for r in ready]
        assert averages == sorted(averages, reverse=True)

    def test_average_beats_total_marks_for_ranking(self, db_with_average_ranking_case):
        ranking = compute_student_scores("O_LEVEL", exam_id=db_with_average_ranking_case["exam_id"])
        high_average = next(r for r in ranking if r["admission"] == "ADM101")
        high_total = next(r for r in ranking if r["admission"] == "ADM102")

        assert high_average["average"] > high_total["average"]
        assert high_average["total_marks"] < high_total["total_marks"]
        assert high_average["position"] < high_total["position"]

    def test_ready_students_come_before_incomplete(self, db_with_results):
        ranking = compute_student_scores("O_LEVEL", exam_id=db_with_results["exam_id"])
        found_incomplete = False
        for r in ranking:
            if r["status"] == "INCOMPLETE":
                found_incomplete = True
            elif found_incomplete:
                pytest.fail("READY student found after INCOMPLETE student")

    def test_student_has_required_fields(self, db_with_results):
        ranking = compute_student_scores("O_LEVEL", exam_id=db_with_results["exam_id"])
        required_fields = ["position", "admission", "name", "gender", "class", "subjects", "total_marks", "points", "average", "division", "status"]
        for student in ranking:
            for field in required_fields:
                assert field in student

    def test_division_assigned_for_ready_students(self, db_with_results):
        ranking = compute_student_scores("O_LEVEL", exam_id=db_with_results["exam_id"])
        ready = [r for r in ranking if r["status"] == "READY"]
        for student in ready:
            assert student["division"] in ["I", "II", "III", "IV", "0", "UNKNOWN"]

    def test_empty_results_returns_empty_list(self, initialized_db):
        ranking = compute_student_scores("O_LEVEL")
        assert ranking == []


class TestComputeStudentScoresALevel:
    def test_a_level_ranking(self, db_with_a_level_results):
        ranking = compute_student_scores("A_LEVEL", exam_id=db_with_a_level_results["exam_id"])
        assert len(ranking) >= 1

    def test_a_level_student_has_division(self, db_with_a_level_results):
        ranking = compute_student_scores("A_LEVEL", exam_id=db_with_a_level_results["exam_id"])
        david = next((r for r in ranking if r["admission"] == "ADM010"), None)
        assert david is not None
        assert david["status"] == "READY"
        assert david["division"] != "UNKNOWN"

    def test_a_level_uses_best_3_subjects(self, db_with_a_level_results):
        ranking = compute_student_scores("A_LEVEL", exam_id=db_with_a_level_results["exam_id"])
        david = next(r for r in ranking if r["admission"] == "ADM010")
        # Points should be sum of best 3 grades
        assert isinstance(david["points"], int)
        assert david["points"] >= 3  # Minimum possible (all A's = 1+1+1)


class TestComputeStudentScoresAutoExam:
    def test_auto_selects_latest_exam_with_results(self, db_with_results):
        ranking = compute_student_scores("O_LEVEL")
        assert len(ranking) > 0

    def test_no_exam_with_results_returns_empty(self, initialized_db):
        ranking = compute_student_scores("O_LEVEL")
        assert ranking == []
