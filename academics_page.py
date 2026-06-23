from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStackedWidget
)

from subjects_page import SubjectsPage
from enrollment_page import EnrollmentPage
from academic_years import AcademicYearsPage
from terms_page import TermsPage


class AcademicsPage(QWidget):

    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)

        # =====================================
        # TOP NAV
        # =====================================

        nav = QHBoxLayout()

        self.btn_subjects = QPushButton("Subjects")
        self.btn_enrollment = QPushButton("Enrollment")
        self.btn_years = QPushButton("Academic Years")
        self.btn_terms = QPushButton("Terms")

        nav.addWidget(self.btn_subjects)
        nav.addWidget(self.btn_enrollment)
        nav.addWidget(self.btn_years)
        nav.addWidget(self.btn_terms)

        root.addLayout(nav)

        # =====================================
        # STACK
        # =====================================

        self.stack = QStackedWidget()

        self.subjects_page = SubjectsPage()
        self.enrollment_page = EnrollmentPage()
        self.years_page = AcademicYearsPage()
        self.terms_page = TermsPage()

        self.stack.addWidget(self.subjects_page)
        self.stack.addWidget(self.enrollment_page)
        self.stack.addWidget(self.years_page)
        self.stack.addWidget(self.terms_page)

        root.addWidget(self.stack)

        # =====================================
        # EVENTS
        # =====================================

        self.btn_subjects.clicked.connect(
            lambda: self.stack.setCurrentWidget(
                self.subjects_page
            )
        )

        self.btn_enrollment.clicked.connect(
            lambda: self.stack.setCurrentWidget(
                self.enrollment_page
            )
        )

        self.btn_years.clicked.connect(
            lambda: self.stack.setCurrentWidget(
                self.years_page
            )
        )

        self.btn_terms.clicked.connect(
            lambda: self.stack.setCurrentWidget(
                self.terms_page
            )
        )

        self.stack.setCurrentWidget(
            self.subjects_page
        )

    def load(self):

        for page in [
            self.subjects_page,
            self.enrollment_page,
            self.years_page,
            self.terms_page
        ]:

            for method_name in (
                "refresh_all",
                "load_data",
                "load",
                "load_years"
            ):

                method = getattr(
                    page,
                    method_name,
                    None
                )

                if callable(method):
                    try:
                        method()
                    except Exception as e:
                        print(f"[ERROR] Failed to call {method_name}: {e}")
                    break
