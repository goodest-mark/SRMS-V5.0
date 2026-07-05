from system_state import SystemState


def get_classes():
    level = SystemState.get_level()

    classes_map = {
        "O_LEVEL": [
            "Form I",
            "Form II",
            "Form III",
            "Form IV"
        ],

        "A_LEVEL": [
            "Form V",
            "Form VI"
        ]
    }

    return classes_map.get(level, [])


def get_level_for_class(class_name):
    """Return the canonical level for a given class name."""
    class_name = (class_name or "").strip()
    if class_name in {"Form I", "Form II", "Form III", "Form IV"}:
        return "O_LEVEL"
    if class_name in {"Form V", "Form VI"}:
        return "A_LEVEL"
    return None
