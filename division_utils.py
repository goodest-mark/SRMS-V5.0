"""Shared database access helpers for division rules."""

from db_utils import execute, fetch_all, fetch_one


def get_division(level, points):
    row = fetch_one(
        """
        SELECT division
        FROM division_rules
        WHERE level = ? AND ? BETWEEN min_points AND max_points
        """,
        (level, points),
    )
    return row[0] if row else "UNKNOWN"


def get_rules(level):
    return fetch_all(
        """
        SELECT id, division, min_points, max_points
        FROM division_rules
        WHERE level = ?
        ORDER BY min_points
        """,
        (level,),
    )


def update_rule(rule_id, minimum, maximum):
    execute(
        "UPDATE division_rules SET min_points = ?, max_points = ? WHERE id = ?",
        (minimum, maximum, rule_id),
    )
