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