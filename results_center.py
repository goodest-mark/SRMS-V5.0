from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStackedWidget
)

from results_page import ResultsPage
from results_dashboard import ResultsDashboard
from readiness_page import ReadinessPage
from excel_results_import import ExcelResultsImport


class ResultsCenter(QWidget):

    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)

        # =====================================
        # RESULTS NAVIGATION
        # =====================================

        nav = QHBoxLayout()

        self.btn_entry = QPushButton("Results Entry")
        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_readiness = QPushButton("Readiness")
        self.btn_import = QPushButton("Excel Import")

        nav.addWidget(self.btn_entry)
        nav.addWidget(self.btn_dashboard)
        nav.addWidget(self.btn_readiness)
        nav.addWidget(self.btn_import)

        root.addLayout(nav)

        # =====================================
        # STACK
        # =====================================

        self.stack = QStackedWidget()

        self.results_entry_page = ResultsPage()
        self.dashboard_page = ResultsDashboard()
        self.readiness_page = ReadinessPage()
        self.import_page = ExcelResultsImport()

        self.stack.addWidget(self.results_entry_page)
        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.readiness_page)
        self.stack.addWidget(self.import_page)

        root.addWidget(self.stack)

        # =====================================
        # EVENTS
        # =====================================

        self.btn_entry.clicked.connect(
            lambda: self.stack.setCurrentWidget(
                self.results_entry_page
            )
        )

        self.btn_dashboard.clicked.connect(
            lambda: self.stack.setCurrentWidget(
                self.dashboard_page
            )
        )

        self.btn_readiness.clicked.connect(
            lambda: self.stack.setCurrentWidget(
                self.readiness_page
            )
        )

        self.btn_import.clicked.connect(
            lambda: self.stack.setCurrentWidget(
                self.import_page
            )
        )

        self.stack.setCurrentWidget(
            self.dashboard_page
        )

    def load(self):
        page = self.stack.currentWidget()
        if page is None:
            return

        for method_name in ("refresh_all", "load_data", "load"):
            method = getattr(page, method_name, None)
            if callable(method):
                try:
                    method()
                except Exception as e:
                    print(f"[ERROR] Failed to call {method_name}: {e}")
                break

    def open_readiness(self):
        self.stack.setCurrentWidget(self.readiness_page)

    def open_import(self):
        self.stack.setCurrentWidget(self.import_page)


    # =====================================
    # OPEN FROM DASHBOARD
    # =====================================

    def open_from_dashboard(
        self,
        exam_id,
        class_name,
        subject_name
    ):

        self.stack.setCurrentWidget(
            self.results_entry_page
        )

        try:
            self.results_entry_page.open_from_dashboard(
                exam_id,
                class_name,
                subject_name
            )
        except Exception as error:
            print(f"[ERROR] ResultsCenter failed to open results entry: {error}")
