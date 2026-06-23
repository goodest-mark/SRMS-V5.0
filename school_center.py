from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStackedWidget
)

from school_profile import SchoolProfilePage
from requirements_page import RequirementsPage


class SchoolCenter(QWidget):

    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)

        # =====================================
        # SCHOOL NAVIGATION
        # =====================================

        nav = QHBoxLayout()

        self.btn_profile = QPushButton(
            "School Profile"
        )

        self.btn_requirements = QPushButton(
            "Requirements"
        )

        nav.addWidget(
            self.btn_profile
        )

        nav.addWidget(
            self.btn_requirements
        )

        root.addLayout(nav)

        # =====================================
        # STACK
        # =====================================

        self.stack = QStackedWidget()

        self.profile_page = (
            SchoolProfilePage()
        )

        self.requirements_page = (
            RequirementsPage()
        )

        self.stack.addWidget(
            self.profile_page
        )

        self.stack.addWidget(
            self.requirements_page
        )

        root.addWidget(
            self.stack
        )

        # =====================================
        # EVENTS
        # =====================================

        self.btn_profile.clicked.connect(
            lambda: self.stack.setCurrentWidget(
                self.profile_page
            )
        )

        self.btn_requirements.clicked.connect(
            lambda: self.stack.setCurrentWidget(
                self.requirements_page
            )
        )

        self.stack.setCurrentWidget(
            self.profile_page
        )

    def load(self):

        for page in [
            self.profile_page,
            self.requirements_page
        ]:

            for method_name in (
                "refresh_all",
                "load_data",
                "load"
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
