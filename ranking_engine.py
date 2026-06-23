from database import connect
from grade_utils import get_grade, get_points
from division_utils import get_division
from settings_page import get_setting

def compute_student_scores(level, exam_id=None):
    """
    Ranking Engine V3.1
    Calculates student ranks based on subject count requirements.
    O_LEVEL: Requires >= 7 COUNTED subjects.
    A_LEVEL: Requires >= 3 PRINCIPAL subjects.
    """
    with connect() as conn:
        cur = conn.cursor()

        if exam_id is None:
            # V3.2 Fix: MAX(id) was removed because it could return an exam record 
            # that has been created but does not yet contain any results/marks.
            # We now join with the results table to ensure we only rank for 
            # the latest exam that actually has data recorded.
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

        # Fetch results for the specified exam, skipping NULL marks. Include class & gender.
        # Ensure subject level is matched against the exam's level to support historic views.
        cur.execute("""
            SELECT
                s.admission_no,
                s.full_name,
                s.gender,
                s.class,
                r.subject_name,
                r.marks,
                sub.subject_type
            FROM results r
            JOIN students s ON s.admission_no = r.admission_no
            JOIN exams ex ON ex.id = r.exam_id
            LEFT JOIN subjects sub ON sub.subject_name = r.subject_name AND sub.level = ex.level
            WHERE r.exam_id = ?
              AND r.marks IS NOT NULL
        """, (exam_id,))

        rows = cur.fetchall()

        # Fetch division rules for in-memory lookup to avoid N+1 query loop
        cur.execute("""
            SELECT division, min_points, max_points 
            FROM division_rules 
            WHERE level=?
        """, (level,))
        division_rules = cur.fetchall()

    if not rows:
        return []

    # Group results by student
    students_data = {}
    for row in rows:
        adm, name, gender, class_name, subject, marks, subject_type = row
        
        grade = get_grade(marks, level=level)
        points = get_points(grade, level=level)

        if adm not in students_data:
            students_data[adm] = {
                "name": name,
                "gender": gender,
                "class": class_name,
                "subjects": []
            }

        students_data[adm]["subjects"].append({
            "subject": subject,
            "marks": marks,
            "grade": grade,
            "points": points,
            "subject_type": subject_type
        })

    ready_students = []
    incomplete_students = []

    for adm, data in students_data.items():
        subjects = data["subjects"]
        
        if level == "A_LEVEL":
            required_type = "PRINCIPAL"
            required_count = int(get_setting('a_level_principal', '3'))
        else:
            required_type = "COUNTED"
            required_count = int(get_setting('o_level_counted', '7'))

        # Filter subjects based on required type
        eligible_subjects = [s for s in subjects if s["subject_type"] == required_type]
        eligible_count = len(eligible_subjects)

        if eligible_count < required_count:
            # PART 3 — INCOMPLETE RULES
            incomplete_students.append({
                "position": "-",
                "admission": adm,
                "name": data["name"],
                "gender": data["gender"],
                "class": data["class"],
                "subjects": eligible_count,
                "points": "-",
                "average": "-",
                "division": "-",
                "status": "INCOMPLETE"
            })
        else:
            # PART 2 — READY RULES
            # Sort by points (lower is better) to pick best X
            eligible_subjects.sort(key=lambda x: x["points"])
            best_subjects = eligible_subjects[:required_count]
            
            total_points = sum(s["points"] for s in best_subjects)
            
            # Calculate Average
            total_marks = sum(s["marks"] for s in best_subjects)
            average = round(total_marks / required_count, 2)
            
            # In-memory division lookup (No N+1 database queries)
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
                "subjects": eligible_count,
                "points": total_points,
                "average": average,
                "division": division,
                "status": "READY"
            })

    # SORTING: READY students first. 
    # We sort by points ascending (lower points is better).
    # In case of a tie in points, we sort by average descending (higher average is better).
    # Using -x["average"] allows us to sort in descending order within the same key function.
    ready_students.sort(key=lambda x: (x["points"], -x["average"]))

    for pos, item in enumerate(ready_students, start=1):
        item["position"] = pos

    # Combine: READY first, then INCOMPLETE
    ranking = ready_students + incomplete_students
    return ranking
