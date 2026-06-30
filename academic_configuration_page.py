from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTabWidget,
)

from progress_dialog import ProgressDialog

from grade_rules_page import GradeRulesPage
from division_rules_page import DivisionRulesPage
from subject_requirements_page import SubjectRequirementsPage


class AcademicConfigurationPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel("ACADEMIC CONFIGURATION")
        title.setStyleSheet("""
            font-size:22px;
            font-weight:bold;
            color:#60a5fa;
            padding:8px;
        """)
        layout.addWidget(title)

        self.tabs = QTabWidget()

        self.tabs.addTab(
            GradeRulesPage(),
            "Grade Rules"
        )

        self.tabs.addTab(
            DivisionRulesPage(),
            "Division Rules"
        )

        self.tabs.addTab(
            SubjectRequirementsPage(),
            "Subject Requirements"
        )

        layout.addWidget(self.tabs, 1)

