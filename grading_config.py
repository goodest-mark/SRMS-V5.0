"""
Academic grading configuration.

This module is the single source of truth for:

- Grade boundaries
- Grade points
- Required subjects
- Best-of rules

All values come from the database.
"""

from db_utils import fetch_all, fetch_one
from system_state import SystemState


def _level(level=None):
    """Return requested level or current system level."""
    return level or SystemState.get_level()


def get_grading_system(level=None):
    """
    Returns

    {
        "A": (75,100),
        "B": (65,74),
        ...
    }
    """

    level = _level(level)

    rows = fetch_all("""
        SELECT grade,min_mark,max_mark
        FROM grade_rules
        WHERE level=?
        ORDER BY sort_order
    """, (level,))

    return {
        grade: (minimum, maximum)
        for grade, minimum, maximum in rows
    }


def get_points_map(level=None):
    """
    Returns

    {
        "A":1,
        "B":2,
        ...
    }
    """

    level = _level(level)

    rows = fetch_all("""
        SELECT grade,points
        FROM grade_rules
        WHERE level=?
        ORDER BY sort_order
    """, (level,))

    return {
        grade: points
        for grade, points in rows
    }


def get_required_subjects(level=None):

    level = _level(level)

    row = fetch_one("""
        SELECT required_subjects
        FROM subject_requirements
        WHERE level=?
    """, (level,))

    if row and row[0] is not None:
        return row[0]

    return 3 if level == "A_LEVEL" else 7


def get_best_of(level=None):

    level = _level(level)

    row = fetch_one("""
        SELECT best_of
        FROM subject_requirements
        WHERE level=?
    """, (level,))

    if row and row[0] is not None:
        return row[0]

    return 3 if level == "A_LEVEL" else 7
