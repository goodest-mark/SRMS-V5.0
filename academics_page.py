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

        self.tabs.setStyleSheet("""
        QTabWidget::pane {
            border:1px solid #2f3f5b;
            border-radius:8px;
            background:#0f172a;
        }

        QTabBar::tab {
            background:#1e293b;
            color:white;
            padding:10px 24px;
            margin-right:2px;
            border-top-left-radius:6px;
            border-top-right-radius:6px;
        }

        QTabBar::tab:selected {
            background:#2563eb;
            font-weight:bold;
        }

        QTabBar::tab:hover {
            background:#3b82f6;
        }
        """)

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

        for page in (
            self.subjects_page,
            self.enrollment_page,
            self.years_page,
            self.terms_page,
        ):

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