class EventBus:
    listeners = {}

    @classmethod
    def subscribe(cls, event, callback):
        if event not in cls.listeners:
            cls.listeners[event] = []

        if callback not in cls.listeners[event]:
            cls.listeners[event].append(callback)

    @classmethod
    def emit(cls, event, *args, **kwargs):
        callbacks = list(cls.listeners.get(event, []))

        for callback in callbacks:
            try:
                callback(*args, **kwargs)
            except Exception as error:
                print(f"Event error [{event}]:", error)
