"""Unit tests for grade_utils module."""
import pytest
from grade_utils import get_grade, get_points


class TestGetGradeOLevel:
    """Tests for get_grade with O_LEVEL."""

    @pytest.mark.parametrize("mark,expected", [
        (100, "A"), (75, "A"), (85, "A"),
        (74, "B"), (65, "B"), (70, "B"),
        (64, "C"), (45, "C"), (55, "C"),
        (44, "D"), (30, "D"), (35, "D"),
        (29, "F"), (0, "F"), (25, "F"),
    ])
    def test_o_level_grades(self, initialized_db, mark, expected):
        assert get_grade(mark, level="O_LEVEL") == expected

    def test_boundary_a_b(self, initialized_db):
        assert get_grade(75, level="O_LEVEL") == "A"
        assert get_grade(74, level="O_LEVEL") == "B"

    def test_boundary_b_c(self, initialized_db):
        assert get_grade(65, level="O_LEVEL") == "B"
        assert get_grade(64, level="O_LEVEL") == "C"

    def test_boundary_c_d(self, initialized_db):
        assert get_grade(45, level="O_LEVEL") == "C"
        assert get_grade(44, level="O_LEVEL") == "D"

    def test_boundary_d_f(self, initialized_db):
        assert get_grade(30, level="O_LEVEL") == "D"
        assert get_grade(29, level="O_LEVEL") == "F"


class TestGetGradeALevel:
    """Tests for get_grade with A_LEVEL."""

    @pytest.mark.parametrize("mark,expected", [
        (100, "A"), (80, "A"), (85, "A"),
        (79, "B"), (70, "B"), (75, "B"),
        (69, "C"), (60, "C"), (65, "C"),
        (59, "D"), (50, "D"), (55, "D"),
        (49, "E"), (40, "E"), (45, "E"),
        (39, "S"), (35, "S"), (37, "S"),
        (34, "F"), (0, "F"), (20, "F"),
    ])
    def test_a_level_grades(self, initialized_db, mark, expected):
        assert get_grade(mark, level="A_LEVEL") == expected

    def test_boundary_e_s(self, initialized_db):
        assert get_grade(40, level="A_LEVEL") == "E"
        assert get_grade(39, level="A_LEVEL") == "S"

    def test_boundary_s_f(self, initialized_db):
        assert get_grade(35, level="A_LEVEL") == "S"
        assert get_grade(34, level="A_LEVEL") == "F"


class TestGetGradeDefaultLevel:
    """Tests for get_grade using SystemState default level."""

    def test_uses_system_state_when_no_level(self, initialized_db, monkeypatch):
        from system_state import SystemState
        monkeypatch.setattr(SystemState, "level", "O_LEVEL")
        assert get_grade(75) == "A"
        assert get_grade(29) == "F"

    def test_uses_a_level_from_system_state(self, initialized_db, monkeypatch):
        from system_state import SystemState
        monkeypatch.setattr(SystemState, "level", "A_LEVEL")
        assert get_grade(35) == "S"
        assert get_grade(34) == "F"


class TestGetPointsOLevel:
    """Tests for get_points with O_LEVEL."""

    @pytest.mark.parametrize("grade,expected", [
        ("A", 1), ("B", 2), ("C", 3), ("D", 4), ("F", 5),
    ])
    def test_o_level_points(self, initialized_db, grade, expected):
        assert get_points(grade, level="O_LEVEL") == expected

    def test_unknown_grade_returns_5(self, initialized_db):
        assert get_points("Z", level="O_LEVEL") == 5
        assert get_points("", level="O_LEVEL") == 5


class TestGetPointsALevel:
    """Tests for get_points with A_LEVEL."""

    @pytest.mark.parametrize("grade,expected", [
        ("A", 1), ("B", 2), ("C", 3), ("D", 4), ("E", 5), ("S", 6), ("F", 7),
    ])
    def test_a_level_points(self, initialized_db, grade, expected):
        assert get_points(grade, level="A_LEVEL") == expected

    def test_unknown_grade_returns_7(self, initialized_db):
        assert get_points("Z", level="A_LEVEL") == 7
        assert get_points("", level="A_LEVEL") == 7


class TestGetPointsDefaultLevel:
    """Tests for get_points using SystemState default level."""

    def test_uses_system_state_when_no_level(self, initialized_db, monkeypatch):
        from system_state import SystemState
        monkeypatch.setattr(SystemState, "level", "O_LEVEL")
        assert get_points("A") == 1
        assert get_points("F") == 5
