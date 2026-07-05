from system_state import SystemState
from grading_config import get_grading_system, get_points_map


def get_grade(mark, level=None):
    """
    Return grade for a given mark using database configuration.
    """

    if level is None:
        level = SystemState.get_level()

    grading = get_grading_system(level)

    for grade, (minimum, maximum) in grading.items():
        if minimum <= mark <= maximum:
            return grade

    return "-"


def get_points(grade, level=None):
    """
    Return points assigned to a grade using database configuration.
    """

    if level is None:
        level = SystemState.get_level()

    points = get_points_map(level)

    if level == "A_LEVEL":
        return points.get(grade, 7)

    return points.get(grade, 5)