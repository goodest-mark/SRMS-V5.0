from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStackedWidget
)

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

        self.results_entry_page = None
        self.dashboard_page = None
        self.readiness_page = None
        self.import_page = None

        root.addWidget(self.stack)

        # =====================================
        # EVENTS
        # =====================================

        self.btn_entry.clicked.connect(
            lambda: self._switch_page("results_entry")
        )

        self.btn_dashboard.clicked.connect(
            lambda: self._switch_page("dashboard")
        )

        self.btn_readiness.clicked.connect(
            lambda: self._switch_page("readiness")
        )

        self.btn_import.clicked.connect(
            lambda: self._switch_page("import")
        )

        self._switch_page("dashboard")

    def _ensure_page(self, name):
        if name == "results_entry":
            if self.results_entry_page is None:
                from results_page import ResultsPage
                self.results_entry_page = ResultsPage()
                self.stack.addWidget(self.results_entry_page)
            return self.results_entry_page
        if name == "dashboard":
            if self.dashboard_page is None:
                from ui.pages.results_dashboard import ResultsDashboard
                self.dashboard_page = ResultsDashboard()
                self.stack.addWidget(self.dashboard_page)
            return self.dashboard_page
        if name == "readiness":
            if self.readiness_page is None:
                from readiness_page import ReadinessPage
                self.readiness_page = ReadinessPage()
                self.stack.addWidget(self.readiness_page)
            return self.readiness_page
        if name == "import":
            if self.import_page is None:
                from excel_results_import import ExcelResultsImport
                self.import_page = ExcelResultsImport()
                self.stack.addWidget(self.import_page)
            return self.import_page
        return None

    def _switch_page(self, name):
        page = self._ensure_page(name)
        if page is not None:
            self.stack.setCurrentWidget(page)

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
        self._switch_page("readiness")

    def open_import(self):
        self._switch_page("import")


    # =====================================
    # OPEN FROM DASHBOARD
    # =====================================

    def open_from_dashboard(
        self,
        exam_id,
        class_name,
        subject_name
    ):

        self._switch_page("results_entry")

        try:
            self.results_entry_page.open_from_dashboard(
                exam_id,
                class_name,
                subject_name
            )
        except Exception as error:
            print(f"[ERROR] ResultsCenter failed to open results entry: {error}")
