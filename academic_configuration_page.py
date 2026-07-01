from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
)

from grade_rules_page import GradeRulesPage
from division_rules_page import DivisionRulesPage
from subject_requirements_page import SubjectRequirementsPage


class AcademicConfigurationPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setUsesScrollButtons(False)

        self.grade_rules = GradeRulesPage()
        self.division_rules = DivisionRulesPage()
        self.subject_requirements = SubjectRequirementsPage()

        self.tabs.addTab(self.grade_rules, "Grades")
        self.tabs.addTab(self.division_rules, "Divisions")
        self.tabs.addTab(self.subject_requirements, "Requirements")

        layout.addWidget(self.tabs)

    def load(self):
        page = self.tabs.currentWidget()
        if page is None:
            return

        for method in (
            "refresh_all",
            "load_data",
            "load",
        ):
            fn = getattr(page, method, None)
            if callable(fn):
                try:
                    fn()
                except Exception as e:
                    print(e)
                break
