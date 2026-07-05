"""Unit tests for database-backed grading configuration."""

from grading_config import get_grading_system, get_points_map
from grade_utils import get_grade, get_points


class TestGradingSystem:
    def test_o_level_default_rules_loaded_from_database(self, initialized_db):
        o_level = get_grading_system("O_LEVEL")

        assert o_level == {
            "A": (75, 100),
            "B": (65, 74),
            "C": (45, 64),
            "D": (30, 44),
            "F": (0, 29),
        }

    def test_a_level_default_rules_loaded_from_database(self, initialized_db):
        a_level = get_grading_system("A_LEVEL")

        assert a_level == {
            "A": (80, 100),
            "B": (70, 79),
            "C": (60, 69),
            "D": (50, 59),
            "E": (40, 49),
            "S": (35, 39),
            "F": (0, 34),
        }

    def test_ranges_cover_full_mark_range(self, initialized_db):
        for level in ("O_LEVEL", "A_LEVEL"):
            grading = get_grading_system(level)
            for mark in range(0, 101):
                matches = [
                    grade
                    for grade, (minimum, maximum) in grading.items()
                    if minimum <= mark <= maximum
                ]
                assert len(matches) == 1, f"{level} mark {mark} matched {matches}"

    def test_points_map_loaded_from_database(self, initialized_db):
        assert get_points_map("O_LEVEL")["A"] == 1
        assert get_points_map("O_LEVEL")["F"] == 5
        assert get_points_map("A_LEVEL")["S"] == 6
        assert get_points_map("A_LEVEL")["F"] == 7

    def test_editable_rules_are_source_of_truth(self, initialized_db):
        from db_utils import execute

        execute(
            """
            UPDATE grade_rules
            SET min_mark=90, max_mark=100
            WHERE level='O_LEVEL' AND grade='A'
            """
        )
        execute(
            """
            UPDATE grade_rules
            SET min_mark=75, max_mark=89
            WHERE level='O_LEVEL' AND grade='B'
            """
        )

        assert get_grading_system("O_LEVEL")["A"] == (90, 100)
        assert get_grade(89, level="O_LEVEL") == "B"
        assert get_grade(90, level="O_LEVEL") == "A"
        assert get_points("A", level="O_LEVEL") == 1
