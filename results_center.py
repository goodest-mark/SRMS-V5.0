from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QButtonGroup,
    QFrame,
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
        nav.setContentsMargins(0, 0, 0, 12)

        nav_container = QFrame()
        nav_container.setObjectName("resultsNavContainer")
        nav_container_layout = QHBoxLayout(nav_container)
        nav_container_layout.setContentsMargins(4, 4, 4, 4)
        nav_container_layout.setSpacing(4)

        self.btn_entry = QPushButton("Results Entry")
        self.btn_dashboard = QPushButton("Dashboard")

        for btn in (self.btn_entry, self.btn_dashboard):
            btn.setObjectName("resultsNavButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(38)
            btn.setMinimumWidth(140)
            nav_container_layout.addWidget(btn)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_group.addButton(self.btn_entry)
        self.nav_group.addButton(self.btn_dashboard)

        nav_container.setStyleSheet("""
            QFrame#resultsNavContainer {
                background-color: #EEF1F6;
                border-radius: 12px;
            }
            QPushButton#resultsNavButton {
                background-color: transparent;
                border: none;
                border-radius: 9px;
                padding: 8px 22px;
                font-weight: 600;
                font-size: 13px;
                color: #5B6472;
            }
            QPushButton#resultsNavButton:hover {
                background-color: #E0E4EC;
                color: #1E293B;
            }
            QPushButton#resultsNavButton:checked {
                background-color: #1E3A8A;
                color: #FFFFFF;
            }
            QPushButton#resultsNavButton:checked:hover {
                background-color: #1E3A8A;
            }
        """)

        nav.addWidget(nav_container)
        nav.addStretch()
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
        self._update_nav_highlight(name)

    def _update_nav_highlight(self, name):
        """Keep the tab highlight in sync even when the page switch was
        triggered programmatically (e.g. open_from_dashboard) rather than by
        clicking a nav button. Pages with no corresponding button (readiness,
        import) leave both tabs unhighlighted rather than showing a stale
        selection."""
        for btn, matches in (
            (self.btn_entry, name == "results_entry"),
            (self.btn_dashboard, name == "dashboard"),
        ):
            btn.blockSignals(True)
            btn.setChecked(matches)
            btn.blockSignals(False)

    def load(self):
        page = self.stack.currentWidget()
        if page is None:
            return

        # Call only the first matching refresh method a page implements, in
        # priority order. A page may implement more than one of these names
        # (e.g. ResultsPage has both refresh_all() and load(), where load()
        # just calls refresh_all() again) — calling every match would run
        # the same refresh twice.
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