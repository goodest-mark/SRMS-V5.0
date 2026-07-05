"""Unit tests for system_state module."""
import pytest
from system_state import SystemState
from event_bus import EventBus


@pytest.fixture(autouse=True)
def reset_state():
    """Reset SystemState and EventBus before each test."""
    SystemState.level = "O_LEVEL"
    EventBus.listeners = {}
    yield
    SystemState.level = "O_LEVEL"
    EventBus.listeners = {}


class TestSystemState:
    def test_default_level_is_o_level(self):
        assert SystemState.get_level() == "O_LEVEL"

    def test_set_level_changes_value(self):
        SystemState.set_level("A_LEVEL")
        assert SystemState.get_level() == "A_LEVEL"

    def test_set_level_emits_event(self):
        emitted = []
        EventBus.subscribe("LEVEL_CHANGED", lambda: emitted.append(True))
        SystemState.set_level("A_LEVEL")
        assert emitted == [True]

    def test_set_level_back_to_o_level(self):
        SystemState.set_level("A_LEVEL")
        SystemState.set_level("O_LEVEL")
        assert SystemState.get_level() == "O_LEVEL"

    def test_multiple_level_changes_emit_multiple_events(self):
        count = []
        EventBus.subscribe("LEVEL_CHANGED", lambda: count.append(1))
        SystemState.set_level("A_LEVEL")
        SystemState.set_level("O_LEVEL")
        SystemState.set_level("A_LEVEL")
        assert len(count) == 3
