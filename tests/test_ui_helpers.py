import pytest
from ui_helpers import get_subject_short_name


def test_get_subject_short_name_uses_given_short_name():
    assert get_subject_short_name("Mathematics", "MATH") == "MATH"
    assert get_subject_short_name("English Language", "ENG") == "ENG"


def test_get_subject_short_name_derives_four_letter_abbrev():
    assert get_subject_short_name("English Language") == "ENGL"
    assert get_subject_short_name("History and Government") == "HIST"
    assert get_subject_short_name("Biology") == "BIOL"
    assert get_subject_short_name("Art") == "ART"
    assert get_subject_short_name("Computer Science") == "COMP"
