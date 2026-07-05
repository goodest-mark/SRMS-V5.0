from db_utils import fetch_all


def get_grade_rules(level):
    rows = fetch_all("""
        SELECT grade,
               min_mark,
               max_mark,
               points
        FROM grade_rules
        WHERE level=?
        ORDER BY sort_order
    """, (level,))

    return rows