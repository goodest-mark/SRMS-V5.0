class EventBus:
    listeners = {}

    @classmethod
    def subscribe(cls, event, callback):
        if event not in cls.listeners:
            cls.listeners[event] = []

        if callback not in cls.listeners[event]:
            cls.listeners[event].append(callback)

    @classmethod
    def emit(cls, event, *args, visible_only=False, **kwargs):
        # Rankings are derived from these records and settings.  Clear the
        # short-lived cache before listeners redraw, otherwise a refresh can
        # briefly show the pre-save class or stream result.
        if event in {
            "RESULTS_UPDATED", "STUDENTS_UPDATED", "LEVEL_CHANGED",
            "SUBJECT_REQUIREMENTS_CHANGED", "GRADE_RULES_CHANGED",
            "DIVISION_RULES_CHANGED",
        }:
            from cache_utils import ranking_cache
            ranking_cache.clear()
        callbacks = list(cls.listeners.get(event, []))

        for callback in callbacks:
            owner = getattr(callback, "__self__", None)
            is_visible = getattr(owner, "isVisible", None)
            if visible_only and callable(is_visible) and not is_visible():
                if hasattr(owner, "_needs_refresh"):
                    owner._needs_refresh = True
                continue
            try:
                callback(*args, **kwargs)
            except Exception as error:
                print(f"Event error [{event}]:", error)
