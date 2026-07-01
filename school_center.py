from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStackedWidget
)

from progress_dialog import ProgressDialog

from school_profile import SchoolProfilePage
from requirements_page import RequirementsPage
from academic_configuration_page import AcademicConfigurationPage


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

        self.btn_academic_config = QPushButton(
            "Academic Config"
        )

        nav.addWidget(
            self.btn_profile
        )

        nav.addWidget(
            self.btn_requirements
        )
        nav.addWidget(
            self.btn_academic_config
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

        self.academic_config_page = (
            AcademicConfigurationPage()
        )

        self.stack.addWidget(
            self.profile_page
        )

        self.stack.addWidget(
            self.requirements_page
        )

        self.stack.addWidget(
            self.academic_config_page
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

        self.btn_academic_config.clicked.connect(
            lambda: self.stack.setCurrentWidget(
                self.academic_config_page
            )
        )

        self.stack.setCurrentWidget(
            self.profile_page
        )

    def load(self):
        page = self.stack.currentWidget()
        if page is None:
            return

        for method_name in (
            "refresh_all",
            "load_data",
            "load"
        ):
            method = getattr(page, method_name, None)
            if callable(method):
                try:
                    method()
                except Exception as e:
                    print(f"[ERROR] Failed to call {method_name}: {e}")
                break

    def open_profile(self):
        self.stack.setCurrentWidget(self.profile_page)

    def open_requirements(self):
        self.stack.setCurrentWidget(self.requirements_page)

    def open_academic_config(self, tab_index=0):
        self.stack.setCurrentWidget(self.academic_config_page)
        try:
            self.academic_config_page.tabs.setCurrentIndex(tab_index)
        except Exception:
            pass
