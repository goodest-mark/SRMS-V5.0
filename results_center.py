from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStackedWidget
)

from results_page import ResultsPage
from results_dashboard import ResultsDashboard
from ranking import RankingPage
from broadsheet_page import BroadsheetPage
from report_book_page import ReportBookPage


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
        self.btn_ranking = QPushButton("Ranking")
        self.btn_broadsheet = QPushButton("Broadsheet")
        self.btn_reports = QPushButton("Report Book")

        nav.addWidget(self.btn_entry)
        nav.addWidget(self.btn_dashboard)
        nav.addWidget(self.btn_ranking)
        nav.addWidget(self.btn_broadsheet)
        nav.addWidget(self.btn_reports)

        root.addLayout(nav)

        # =====================================
        # STACK
        # =====================================

        self.stack = QStackedWidget()

        self.results_entry_page = ResultsPage()
        self.dashboard_page = ResultsDashboard()
        self.ranking_page = RankingPage()
        self.broadsheet_page = BroadsheetPage()
        self.report_book_page = ReportBookPage()

        self.stack.addWidget(self.results_entry_page)
        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.ranking_page)
        self.stack.addWidget(self.broadsheet_page)
        self.stack.addWidget(self.report_book_page)

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

        self.btn_ranking.clicked.connect(
            lambda: self.stack.setCurrentWidget(
                self.ranking_page
            )
        )

        self.btn_broadsheet.clicked.connect(
            lambda: self.stack.setCurrentWidget(
                self.broadsheet_page
            )
        )

        self.btn_reports.clicked.connect(
            lambda: self.stack.setCurrentWidget(
                self.report_book_page
            )
        )

        self.stack.setCurrentWidget(
            self.dashboard_page
        )

    def load(self):

        for page in [
            self.results_entry_page,
            self.dashboard_page,
            self.ranking_page,
            self.broadsheet_page,
            self.report_book_page
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

    def open_report_book(self):

        self.stack.setCurrentWidget(
            self.report_book_page
        )


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
            print(
                "ResultsCenter error:",
                error
            )

