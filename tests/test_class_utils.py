"""Unit tests for class_utils module."""
import pytest
from system_state import SystemState
from class_utils import get_classes, get_level_for_class


class TestGetClasses:
    def setup_method(self):
        """Reset system state before each test."""
        SystemState.level = "O_LEVEL"

    def test_o_level_classes(self):
        SystemState.level = "O_LEVEL"
        result = get_classes()
        assert result == ["Form I", "Form II", "Form III", "Form IV"]

    def test_a_level_classes(self):
        SystemState.level = "A_LEVEL"
        result = get_classes()
        assert result == ["Form V", "Form VI"]

    def test_unknown_level_returns_empty(self):
        SystemState.level = "UNKNOWN"
        result = get_classes()
        assert result == []

    def test_empty_level_returns_empty(self):
        SystemState.level = ""
        result = get_classes()
        assert result == []

    def test_none_level_returns_empty(self):
        SystemState.level = None
        result = get_classes()
        assert result == []

    def test_class_to_level_mapping(self):
        assert get_level_for_class("Form I") == "O_LEVEL"
        assert get_level_for_class("Form IV") == "O_LEVEL"
        assert get_level_for_class("Form V") == "A_LEVEL"
        assert get_level_for_class("Form VI") == "A_LEVEL"

    def test_unknown_class_returns_none(self):
        assert get_level_for_class("Form VII") is None
