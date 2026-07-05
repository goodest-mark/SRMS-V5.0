"""Unit tests for class_utils module."""
import pytest
from system_state import SystemState
from class_utils import get_classes


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
