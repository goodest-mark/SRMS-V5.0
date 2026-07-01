from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
)

from progress_dialog import ProgressDialog

from subjects_page import SubjectsPage
from enrollment_page import EnrollmentPage
from academic_years import AcademicYearsPage
from terms_page import TermsPage


class AcademicsPage(QWidget):

    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(False)
        self.tabs.setUsesScrollButtons(False)

        root.addWidget(self.tabs)

        self.subjects_page = SubjectsPage()
        self.enrollment_page = EnrollmentPage()
        self.years_page = AcademicYearsPage()
        self.terms_page = TermsPage()

        self.tabs.addTab(self.subjects_page, "Subjects")
        self.tabs.addTab(self.enrollment_page, "Enrollment")
        self.tabs.addTab(self.years_page, "Academic Years")
        self.tabs.addTab(self.terms_page, "Terms")

        self.tabs.setCurrentIndex(0)

    def load(self):
        page = self.tabs.currentWidget()
        if page is None:
            return

        for method_name in (
            "refresh_all",
            "load_data",
            "load",
            "load_years",
        ):
            method = getattr(page, method_name, None)
            if callable(method):
                try:
                    method()
                except Exception as e:
                    print(f"[ERROR] Failed to call {method_name}: {e}")
                break
