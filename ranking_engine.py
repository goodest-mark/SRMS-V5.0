from database import connect
from grade_utils import get_grade, get_points
from grading_config import get_required_subjects, get_best_of
from academic_rules import is_ranking_subject


def compute_student_scores(level, exam_id=None, class_name=None):
    """
    Ranking Engine V3.3

    Positions are based on AVERAGE across all results for the selected exam.
    Total marks remain available for display and as a tie-breaker.
    When class_name is provided, ranking is limited to that class.
    """
    with connect() as conn:
        cur = conn.cursor()

        if exam_id is None:
            cur.execute("""
                SELECT ex.id
                FROM exams ex
                JOIN results r ON r.exam_id = ex.id
                WHERE ex.level = ?
                GROUP BY ex.id
                ORDER BY ex.id DESC
                LIMIT 1
            """, (level,))

            exam_res = cur.fetchone()
            if not exam_res:
                return []
            exam_id = exam_res[0]

        cur.execute("""
            SELECT t.academic_year_id, ex.term_id
            FROM exams ex
            LEFT JOIN terms t ON t.id = ex.term_id
            WHERE ex.id = ?
        """, (exam_id,))
        exam_context = cur.fetchone()
        academic_year_id = exam_context[0] if exam_context else None
        term_id = exam_context[1] if exam_context else None

        enrolled_pairs = set()
        has_enrollments = False
        if academic_year_id is not None and term_id is not None:
            cur.execute("""
                SELECT e.admission_no, e.subject_name
                FROM enrollments e
                WHERE e.academic_year_id = ?
                  AND e.term_id = ?
                  AND COALESCE(e.class_name, '') = ?
                  AND EXISTS (
                      SELECT 1
                      FROM students s
                      WHERE s.admission_no = e.admission_no
                        AND s.level = ?
                  )
            """, (academic_year_id, term_id, class_name or "", level))
            enrolled_pairs = {
                (admission_no, subject_name)
                for admission_no, subject_name in cur.fetchall()
            }
            has_enrollments = bool(enrolled_pairs)

        query = """
            SELECT
                s.admission_no,
                s.full_name,
                s.gender,
                COALESCE(r.class_name, s.class) AS historical_class,
                r.subject_name,
                r.marks,
                sub.subject_type
            FROM results r
            JOIN students s ON s.admission_no = r.admission_no
            JOIN exams ex ON ex.id = r.exam_id
            LEFT JOIN subjects sub
              ON sub.subject_name = r.subject_name
             AND sub.level = ex.level
            WHERE r.exam_id = ?
              AND ex.level = ?
              AND r.marks IS NOT NULL
        """
        params = [exam_id, level]
        if class_name:
            query += " AND COALESCE(r.class_name, s.class) = ?"
            params.append(class_name)

        cur.execute(query, params)
        rows = cur.fetchall()

        cur.execute("""
            SELECT division, min_points, max_points
            FROM division_rules
            WHERE level=?
        """, (level,))
        division_rules = cur.fetchall()

    if not rows:
        return []

    students_data = {}
    for row in rows:
        adm, name, gender, student_class, subject, marks, subject_type = row

        if has_enrollments and (adm, subject) not in enrolled_pairs:
            continue

        try:
            marks = float(marks)
        except (TypeError, ValueError):
            continue

        grade = get_grade(marks, level=level)
        points = get_points(grade, level=level)

        if adm not in students_data:
            students_data[adm] = {
                "name": name,
                "gender": gender,
                "class": student_class,
                "subjects": []
            }

        students_data[adm]["subjects"].append({
            "subject": subject,
            "marks": marks,
            "grade": grade,
            "points": points,
            "subject_type": subject_type
        })

    if not students_data:
        return []

    if class_name is not None:
        students_data = {
            adm: data
            for adm, data in students_data.items()
            if data["class"] == class_name
        }

    if not students_data:
        return []

    ready_students = []
    incomplete_students = []

    required_count = get_required_subjects(level)
    best_of = get_best_of(level)

    for adm, data in students_data.items():
        subjects = data["subjects"]
        score_subjects = subjects
        total_marks = sum(s["marks"] for s in score_subjects)
        subject_count = len(score_subjects)
        average = round(total_marks / subject_count, 2) if subject_count else 0

        eligible_subjects = [
            s for s in subjects
            if is_ranking_subject(level, s["subject_type"])
        ]
        eligible_count = len(eligible_subjects)

        if eligible_count < required_count:
            incomplete_students.append({
                "position": "-",
                "admission": adm,
                "name": data["name"],
                "gender": data["gender"],
                "class": data["class"],
                "subjects": f"{eligible_count}/{required_count}",
                "total_marks": _format_number(total_marks),
                "points": "-",
                "average": "-",
                "division": "-",
                "status": "INCOMPLETE"
            })
            continue

        eligible_subjects.sort(key=lambda x: x["points"])
        best_subjects = eligible_subjects[:best_of]
        total_points = sum(s["points"] for s in best_subjects)

        division = "UNKNOWN"
        for div_name, min_pts, max_pts in division_rules:
            if min_pts <= total_points <= max_pts:
                division = div_name
                break

        ready_students.append({
            "admission": adm,
            "name": data["name"],
            "gender": data["gender"],
            "class": data["class"],
            "subjects": subject_count,
            "total_marks": _format_number(total_marks),
            "points": total_points,
            "average": average,
            "division": division,
            "status": "READY"
        })

    ready_students.sort(
        key=lambda x: (
            -float(x["average"]),
            -float(x["total_marks"]),
            x["admission"]
        )
    )

    for pos, item in enumerate(ready_students, start=1):
        item["position"] = pos

    return ready_students + incomplete_students


def _format_number(value):
    if float(value).is_integer():
        return int(value)
    return round(value, 2)
