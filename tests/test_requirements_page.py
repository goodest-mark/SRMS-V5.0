import pytest
from PySide6.QtWidgets import QApplication

from requirements_page import RequirementsPage


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_requirements_page_initializes_filters(tmp_db, qt_app):
    from database import init_db

    init_db()
    page = RequirementsPage()

    assert page.year_box.count() > 0
    assert page.term_box.count() > 0
    assert page.class_box.count() > 0

    page.close()
