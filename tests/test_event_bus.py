"""Unit tests for event_bus module."""
import pytest
from event_bus import EventBus


@pytest.fixture(autouse=True)
def clean_event_bus():
    """Reset EventBus listeners before each test."""
    EventBus.listeners = {}
    yield
    EventBus.listeners = {}


class TestEventBusSubscribe:
    def test_subscribe_adds_callback(self):
        called = []
        EventBus.subscribe("TEST_EVENT", lambda: called.append(True))
        assert "TEST_EVENT" in EventBus.listeners
        assert len(EventBus.listeners["TEST_EVENT"]) == 1

    def test_subscribe_multiple_callbacks(self):
        cb1 = lambda: None
        cb2 = lambda: None
        EventBus.subscribe("TEST_EVENT", cb1)
        EventBus.subscribe("TEST_EVENT", cb2)
        assert len(EventBus.listeners["TEST_EVENT"]) == 2

    def test_subscribe_same_callback_twice_is_idempotent(self):
        cb = lambda: None
        EventBus.subscribe("TEST_EVENT", cb)
        EventBus.subscribe("TEST_EVENT", cb)
        assert len(EventBus.listeners["TEST_EVENT"]) == 1

    def test_subscribe_different_events(self):
        cb = lambda: None
        EventBus.subscribe("EVENT_A", cb)
        EventBus.subscribe("EVENT_B", cb)
        assert "EVENT_A" in EventBus.listeners
        assert "EVENT_B" in EventBus.listeners


class TestEventBusEmit:
    def test_emit_calls_subscribed_callback(self):
        called = []
        EventBus.subscribe("TEST_EVENT", lambda: called.append(True))
        EventBus.emit("TEST_EVENT")
        assert called == [True]

    def test_emit_calls_multiple_callbacks(self):
        results = []
        EventBus.subscribe("TEST_EVENT", lambda: results.append("first"))
        EventBus.subscribe("TEST_EVENT", lambda: results.append("second"))
        EventBus.emit("TEST_EVENT")
        assert results == ["first", "second"]

    def test_emit_passes_args(self):
        received = []
        EventBus.subscribe("DATA_EVENT", lambda x, y: received.append((x, y)))
        EventBus.emit("DATA_EVENT", 42, "hello")
        assert received == [(42, "hello")]

    def test_emit_passes_kwargs(self):
        received = []
        EventBus.subscribe("DATA_EVENT", lambda name=None: received.append(name))
        EventBus.emit("DATA_EVENT", name="test")
        assert received == ["test"]

    def test_emit_nonexistent_event_does_not_raise(self):
        EventBus.emit("NO_SUCH_EVENT")

    def test_emit_handles_callback_exception_gracefully(self, capsys):
        def bad_callback():
            raise ValueError("test error")

        EventBus.subscribe("ERROR_EVENT", bad_callback)
        EventBus.emit("ERROR_EVENT")
        captured = capsys.readouterr()
        assert "Event error [ERROR_EVENT]:" in captured.out

    def test_emit_continues_after_exception(self):
        results = []

        def bad_callback():
            raise RuntimeError("fail")

        EventBus.subscribe("MIXED", bad_callback)
        EventBus.subscribe("MIXED", lambda: results.append("ok"))
        EventBus.emit("MIXED")
        assert results == ["ok"]
