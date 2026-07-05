from event_bus import EventBus


class SystemState:
    level = "O_LEVEL"

    @classmethod
    def set_level(cls, value):
        cls.level = value
        EventBus.emit("LEVEL_CHANGED")

    @classmethod
    def get_level(cls):
        return cls.level