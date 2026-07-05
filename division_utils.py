from db_utils import fetch_one, fetch_all, execute


def get_division(level, points):
    row = fetch_one("""
        SELECT division
        FROM division_rules
        WHERE level=? AND ? BETWEEN min_points AND max_points
    """, (level, points))

    if row:
        return row[0]
    return "UNKNOWN"


def get_rules(level):
    return fetch_all("""
        SELECT id, division, min_points, max_points
        FROM division_rules
        WHERE level=?
        ORDER BY min_points
    """, (level,))


def update_rule(rule_id, minimum, maximum):
    execute("""
        UPDATE division_rules
        SET min_points=?, max_points=?
        WHERE id=?
    """, (minimum, maximum, rule_id))