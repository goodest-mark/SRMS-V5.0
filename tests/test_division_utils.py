"""Unit tests for division_utils module."""
import pytest
from division_utils import get_division, get_rules, update_rule


class TestGetDivision:
    """Tests for get_division function."""

    def test_o_level_division_i(self, initialized_db):
        assert get_division("O_LEVEL", 7) == "I"
        assert get_division("O_LEVEL", 17) == "I"
        assert get_division("O_LEVEL", 12) == "I"

    def test_o_level_division_ii(self, initialized_db):
        assert get_division("O_LEVEL", 18) == "II"
        assert get_division("O_LEVEL", 21) == "II"

    def test_o_level_division_iii(self, initialized_db):
        assert get_division("O_LEVEL", 22) == "III"
        assert get_division("O_LEVEL", 25) == "III"

    def test_o_level_division_iv(self, initialized_db):
        assert get_division("O_LEVEL", 26) == "IV"
        assert get_division("O_LEVEL", 33) == "IV"

    def test_o_level_division_zero(self, initialized_db):
        assert get_division("O_LEVEL", 34) == "0"
        assert get_division("O_LEVEL", 35) == "0"

    def test_a_level_division_i(self, initialized_db):
        assert get_division("A_LEVEL", 3) == "I"
        assert get_division("A_LEVEL", 9) == "I"

    def test_a_level_division_ii(self, initialized_db):
        assert get_division("A_LEVEL", 10) == "II"
        assert get_division("A_LEVEL", 12) == "II"

    def test_a_level_division_iii(self, initialized_db):
        assert get_division("A_LEVEL", 13) == "III"
        assert get_division("A_LEVEL", 17) == "III"

    def test_a_level_division_iv(self, initialized_db):
        assert get_division("A_LEVEL", 18) == "IV"
        assert get_division("A_LEVEL", 19) == "IV"

    def test_a_level_division_zero(self, initialized_db):
        assert get_division("A_LEVEL", 20) == "0"
        assert get_division("A_LEVEL", 21) == "0"

    def test_points_out_of_range_returns_unknown(self, initialized_db):
        assert get_division("O_LEVEL", 100) == "UNKNOWN"
        assert get_division("O_LEVEL", 0) == "UNKNOWN"

    def test_invalid_level_returns_unknown(self, initialized_db):
        assert get_division("INVALID_LEVEL", 10) == "UNKNOWN"


class TestGetRules:
    """Tests for get_rules function."""

    def test_o_level_returns_5_rules(self, initialized_db):
        rules = get_rules("O_LEVEL")
        assert len(rules) == 5

    def test_a_level_returns_5_rules(self, initialized_db):
        rules = get_rules("A_LEVEL")
        assert len(rules) == 5

    def test_rules_ordered_by_min_points(self, initialized_db):
        rules = get_rules("O_LEVEL")
        min_points = [r[2] for r in rules]
        assert min_points == sorted(min_points)

    def test_rule_structure(self, initialized_db):
        rules = get_rules("O_LEVEL")
        for rule in rules:
            assert len(rule) == 4  # id, division, min_points, max_points
            assert isinstance(rule[0], int)  # id
            assert isinstance(rule[1], str)  # division
            assert isinstance(rule[2], int)  # min_points
            assert isinstance(rule[3], int)  # max_points

    def test_invalid_level_returns_empty(self, initialized_db):
        rules = get_rules("INVALID")
        assert rules == []


class TestUpdateRule:
    """Tests for update_rule function."""

    def test_update_rule_changes_values(self, initialized_db):
        rules = get_rules("O_LEVEL")
        rule_id = rules[0][0]
        original_min = rules[0][2]
        original_max = rules[0][3]

        update_rule(rule_id, 5, 20)

        updated_rules = get_rules("O_LEVEL")
        updated = next(r for r in updated_rules if r[0] == rule_id)
        assert updated[2] == 5
        assert updated[3] == 20

    def test_update_rule_does_not_affect_other_rules(self, initialized_db):
        rules = get_rules("O_LEVEL")
        first_id = rules[0][0]
        second_rule = rules[1]

        update_rule(first_id, 1, 10)

        updated_rules = get_rules("O_LEVEL")
        second_updated = next(r for r in updated_rules if r[0] == second_rule[0])
        assert second_updated[2] == second_rule[2]
        assert second_updated[3] == second_rule[3]
