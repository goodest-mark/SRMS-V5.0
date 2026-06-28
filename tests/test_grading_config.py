"""Unit tests for grading_config module."""
from grading_config import GRADING_SYSTEM


class TestGradingSystem:
    def test_has_o_level(self):
        assert "O_LEVEL" in GRADING_SYSTEM

    def test_has_a_level(self):
        assert "A_LEVEL" in GRADING_SYSTEM

    def test_o_level_grades(self):
        o_level = GRADING_SYSTEM["O_LEVEL"]
        assert "A" in o_level
        assert "B" in o_level
        assert "C" in o_level
        assert "D" in o_level
        assert "F" in o_level

    def test_a_level_grades(self):
        a_level = GRADING_SYSTEM["A_LEVEL"]
        assert "A" in a_level
        assert "B" in a_level
        assert "C" in a_level
        assert "D" in a_level
        assert "E" in a_level
        assert "S" in a_level
        assert "F" in a_level

    def test_o_level_ranges_are_tuples(self):
        for grade, (low, high) in GRADING_SYSTEM["O_LEVEL"].items():
            assert isinstance(low, int)
            assert isinstance(high, int)
            assert low <= high

    def test_a_level_ranges_are_tuples(self):
        for grade, (low, high) in GRADING_SYSTEM["A_LEVEL"].items():
            assert isinstance(low, int)
            assert isinstance(high, int)
            assert low <= high

    def test_o_level_covers_full_range(self):
        """All marks 0-100 should map to exactly one O-Level grade."""
        o_level = GRADING_SYSTEM["O_LEVEL"]
        for mark in range(0, 101):
            matches = [g for g, (lo, hi) in o_level.items() if lo <= mark <= hi]
            assert len(matches) == 1, f"Mark {mark} matched {matches}"

    def test_a_level_covers_full_range(self):
        """All marks 0-100 should map to exactly one A-Level grade."""
        a_level = GRADING_SYSTEM["A_LEVEL"]
        for mark in range(0, 101):
            matches = [g for g, (lo, hi) in a_level.items() if lo <= mark <= hi]
            assert len(matches) == 1, f"Mark {mark} matched {matches}"

    def test_o_level_a_grade_range(self):
        assert GRADING_SYSTEM["O_LEVEL"]["A"] == (80, 100)

    def test_o_level_f_grade_range(self):
        assert GRADING_SYSTEM["O_LEVEL"]["F"] == (0, 49)

    def test_a_level_a_grade_range(self):
        assert GRADING_SYSTEM["A_LEVEL"]["A"] == (80, 100)

    def test_a_level_f_grade_range(self):
        assert GRADING_SYSTEM["A_LEVEL"]["F"] == (0, 34)
