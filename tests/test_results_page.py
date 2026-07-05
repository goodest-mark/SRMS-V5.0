import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from results_page import _subject_name_matches


def test_subject_name_matches_ignores_display_suffixes_and_case():
    assert _subject_name_matches(" Mathematics (90%) ", "mathematics")
    assert _subject_name_matches("MATHEMATICS", "mathematics")
    assert not _subject_name_matches("Science", "Mathematics")
