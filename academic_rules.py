"""
Academic rules shared across the entire SRMS.

These are structural rules of the education system.
They are intentionally kept in code rather than the database.
"""


ALLOWED_SUBJECT_TYPES = {
    "O_LEVEL": [
        "COUNTED",
        "NOT_COUNTED",
    ],

    "A_LEVEL": [
        "PRINCIPAL",
        "SUBSIDIARY",
    ],
}


RANKING_SUBJECT_TYPES = {
    "O_LEVEL": [
        "COUNTED",
    ],

    "A_LEVEL": [
        "PRINCIPAL",
    ],
}


NON_RANKING_SUBJECT_TYPES = {
    "O_LEVEL": [
        "NOT_COUNTED",
    ],

    "A_LEVEL": [
        "SUBSIDIARY",
    ],
}


def allowed_subject_types(level):
    return ALLOWED_SUBJECT_TYPES.get(level, [])


def ranking_subject_types(level):
    return RANKING_SUBJECT_TYPES.get(level, [])


def non_ranking_subject_types(level):
    return NON_RANKING_SUBJECT_TYPES.get(level, [])


def is_ranking_subject(level, subject_type):
    return subject_type in ranking_subject_types(level)


def validate_subject_type(level, subject_type):
    return subject_type in allowed_subject_types(level)


def default_subject_type(level):
    allowed = allowed_subject_types(level)
    return allowed[0] if allowed else None


def normalize_subject_type(level, subject_type):
    subject_type = (subject_type or "").strip().upper()
    if validate_subject_type(level, subject_type):
        return subject_type
    return default_subject_type(level)
