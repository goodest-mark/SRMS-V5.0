import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from database import init_db
from enrollment_page import EnrollmentPage


def test_enrollment_page_preview_mode_disables_edits(tmp_db):
    init_db()
    app = QApplication.instance() or QApplication([])

    page = EnrollmentPage()
    page.enrollment_mode_checkbox.setChecked(False)
    page.set_enrollment_mode(False)

    assert not page.save_btn.isEnabled()
    assert not page.enrollment_table.isEnabled()
    assert "Preview" in page.preview_label.text()

    app.quit()
