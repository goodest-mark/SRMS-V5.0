"""
Diagnostic for the 'historical page shows no results for a completed exam' bug.

Run from your project root (SRMS-V5.0), inside the venv:

    python diagnose_exam.py                 -> lists COMPLETED exams so you can find the exam_id
    python diagnose_exam.py <EXAM_ID>       -> shows the class_name mismatch for that exam
"""
import sys
from database import connect


def list_completed_exams():
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT e.id, e.exam_name, e.level, t.term_name, y.year_name,
                   (SELECT COUNT(*) FROM results r WHERE r.exam_id = e.id) AS result_rows
            FROM exams e
            JOIN terms t ON e.term_id = t.id
            JOIN academic_years y ON y.id = t.academic_year_id
            WHERE e.status = 'COMPLETED'
            ORDER BY e.id DESC
        """)
        rows = cur.fetchall()

    if not rows:
        print("No COMPLETED exams found.")
        return

    print(f"{'ID':<5} {'Exam':<25} {'Level':<10} {'Term':<10} {'Year':<8} {'Result rows':<12}")
    print("-" * 75)
    for exam_id, name, level, term, year, result_rows in rows:
        print(f"{exam_id:<5} {name:<25} {level:<10} {term:<10} {year:<8} {result_rows:<12}")

    print("\nRun again with an exam ID, e.g.:  python diagnose_exam.py " + str(rows[0][0]))


def diagnose(exam_id):
    with connect() as conn:
        cur = conn.cursor()

        cur.execute("SELECT exam_name, level, status FROM exams WHERE id = ?", (exam_id,))
        exam_row = cur.fetchone()
        if not exam_row:
            print(f"No exam found with id={exam_id}")
            return
        exam_name, level, status = exam_row
        print(f"Exam #{exam_id}: {exam_name} ({level}, status={status})\n")

        # Exact byte-for-byte class_name values stored on results for this exam
        cur.execute("""
            SELECT DISTINCT class_name FROM results WHERE exam_id = ?
        """, (exam_id,))
        distinct_classes = [row[0] for row in cur.fetchall()]
        print("Distinct results.class_name values for this exam (repr, to expose hidden whitespace/case):")
        for c in distinct_classes:
            cur.execute("SELECT COUNT(*) FROM results WHERE exam_id = ? AND class_name = ?", (exam_id, c))
            count = cur.fetchone()[0]
            print(f"  {repr(c):<25} -> {count} rows")
        print()

        cur.execute("SELECT DISTINCT level FROM students")
        print("Distinct students.level values in DB:", [repr(r[0]) for r in cur.fetchall()])
        cur.execute("SELECT level FROM exams WHERE id = ?", (exam_id,))
        print("This exam's level value:", repr(cur.fetchone()[0]))
        print()

        cur.execute("""
            SELECT t.academic_year_id, ex.term_id FROM exams ex
            LEFT JOIN terms t ON t.id = ex.term_id WHERE ex.id = ?
        """, (exam_id,))
        ay_id, term_id = cur.fetchone()
        cur.execute("""
            SELECT COUNT(*) FROM enrollments
            WHERE academic_year_id = ? AND term_id = ?
        """, (ay_id, term_id))
        enroll_count_term = cur.fetchone()[0]
        cur.execute("""
            SELECT class_name, COUNT(*) FROM enrollments
            WHERE academic_year_id = ? AND term_id = ?
            GROUP BY class_name
        """, (ay_id, term_id))
        print(f"Enrollment rows for this exam's (academic_year_id={ay_id}, term_id={term_id}): {enroll_count_term}")
        for cname, cnt in cur.fetchall():
            print(f"  class_name={repr(cname):<25} -> {cnt} rows")
        print()

        cur.execute("""
            SELECT r.admission_no, r.class_name AS result_snapshot,
                   s.class AS student_current_class, s.full_name
            FROM results r
            JOIN students s ON s.admission_no = r.admission_no
            WHERE r.exam_id = ?
            ORDER BY s.full_name
        """, (exam_id,))
        rows = cur.fetchall()

    if not rows:
        print("No results rows found for this exam at all — this is a different"
              " issue (results were never saved), not the class_name snapshot bug.")
        return

    mismatches = [r for r in rows if (r[1] or '').strip().upper() != (r[2] or '').strip().upper()]
    null_snapshots = [r for r in rows if not (r[1] or '').strip()]

    print(f"Total result rows: {len(rows)}")
    print(f"Rows where class_name snapshot != student's CURRENT class: {len(mismatches)}")
    print(f"Rows where class_name snapshot is NULL/empty: {len(null_snapshots)}\n")

    if mismatches:
        print("Sample mismatches (these students will be MISSING when you filter")
        print("the historical page by their old class, e.g. 'Form I'):\n")
        print(f"{'Admission':<12} {'Result snapshot':<18} {'Current class':<15} {'Name'}")
        print("-" * 70)
        for adm, snap, cur_class, name in mismatches[:20]:
            print(f"{adm:<12} {str(snap):<18} {str(cur_class):<15} {name}")
        if len(mismatches) > 20:
            print(f"... and {len(mismatches) - 20} more")
    elif null_snapshots:
        print("class_name snapshots are missing (NULL/empty) for these rows —")
        print("results.class_name was never backfilled or set for them.")
    else:
        print("No mismatch found — every result row's class_name snapshot matches")
        print("the student's current class. This exam is NOT affected by the")
        print("migration backfill bug; the missing-results issue has a different cause.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        diagnose(int(sys.argv[1]))
    else:
        list_completed_exams()
