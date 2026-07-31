from PySide6.QtCore import Qt, Signal, QSignalBlocker
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget,
    QButtonGroup, QComboBox, QLabel, QSizePolicy
)
from system_state import SystemState
from event_bus import EventBus
import combo_loaders
from class_utils import get_classes

# Relative imports – all pages are in the same directory
from .broadsheet_page import BroadsheetPage
from .remarks_page import RemarksPage
from .report_book_page import ReportBookPage


class HistoricalResultsPage(QWidget):
    open_broadsheet_requested = Signal(int, str)
    open_reports_requested = Signal(int, str)

    def __init__(self):
        super().__init__()
        self._history_level = SystemState.get_level()
        self._needs_refresh = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        # ─── 1. CENTERED FILTER BAR ──────────────────────────────────
        filter_bar = QWidget()
        filter_layout = QHBoxLayout(filter_bar)
        filter_layout.setContentsMargins(20, 15, 20, 10)
        filter_layout.setSpacing(10)
        filter_layout.setAlignment(Qt.AlignCenter)

        self.year_box = QComboBox()
        self.term_box = QComboBox()
        self.exam_box = QComboBox()
        self.class_box = QComboBox()
        self.class_box.addItems(get_classes())

        self.year_box.currentIndexChanged.connect(self._on_year_changed)
        self.term_box.currentIndexChanged.connect(self._on_term_changed)
        self.exam_box.currentIndexChanged.connect(self._on_filter_changed)
        self.class_box.currentIndexChanged.connect(self._on_filter_changed)

        filter_layout.addWidget(QLabel("Year:"))
        filter_layout.addWidget(self.year_box)
        filter_layout.addWidget(QLabel("Term:"))
        filter_layout.addWidget(self.term_box)
        filter_layout.addWidget(QLabel("Exam:"))
        filter_layout.addWidget(self.exam_box)
        filter_layout.addWidget(QLabel("Class:"))
        filter_layout.addWidget(self.class_box)

        root.addWidget(filter_bar)

        # ─── 2. CENTERED BUTTONS ──────────────────────────────────────
        button_bar = QWidget()
        button_layout = QHBoxLayout(button_bar)
        button_layout.setContentsMargins(20, 0, 20, 10)
        button_layout.setSpacing(15)
        button_layout.setAlignment(Qt.AlignCenter)

        self.btn_broadsheet = QPushButton("📋 Broadsheet")
        self.btn_remarks = QPushButton("✏️ Remarks")
        self.btn_reports = QPushButton("📄 Reports")

        self.btn_broadsheet.setCheckable(True)
        self.btn_remarks.setCheckable(True)
        self.btn_reports.setCheckable(True)
        for button in (self.btn_broadsheet, self.btn_remarks, self.btn_reports):
            button.setObjectName("workflowTab")

        self.page_button_group = QButtonGroup(self)
        self.page_button_group.setExclusive(True)
        self.page_button_group.addButton(self.btn_broadsheet, 0)
        self.page_button_group.addButton(self.btn_remarks, 1)
        self.page_button_group.addButton(self.btn_reports, 2)

        self.btn_broadsheet.clicked.connect(lambda: self._switch_page(0))
        self.btn_remarks.clicked.connect(lambda: self._switch_page(1))
        self.btn_reports.clicked.connect(lambda: self._switch_page(2))

        button_layout.addWidget(self.btn_broadsheet)
        button_layout.addWidget(self.btn_remarks)
        button_layout.addWidget(self.btn_reports)

        root.addWidget(button_bar)

        # ─── 3. STACKED CONTENT ────────────────────────────────────────
        self.stacked = QStackedWidget()
        self.stacked.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.broadsheet_page = BroadsheetPage()
        self.remarks_page = RemarksPage()
        self.reports_page = ReportBookPage()

        self.stacked.addWidget(self.broadsheet_page)   # index 0
        self.stacked.addWidget(self.remarks_page)      # index 1
        self.stacked.addWidget(self.reports_page)      # index 2

        root.addWidget(self.stacked, 1)

        # ─── Initial Load ────────────────────────────────────────────
        self._load_initial_filters()
        self._switch_page(0)   # default = Broadsheet

        # ─── Event Bus ───────────────────────────────────────────────
        EventBus.subscribe("LEVEL_CHANGED", self.refresh_all)
        EventBus.subscribe("RESULTS_UPDATED", self._on_data_changed)
        EventBus.subscribe("STUDENTS_UPDATED", self._on_data_changed)
        EventBus.subscribe("EXAMS_UPDATED", self.refresh_all)
        EventBus.subscribe("SUBJECT_REQUIREMENTS_CHANGED", self.refresh_all)
        EventBus.subscribe("GRADE_RULES_CHANGED", self.refresh_all)
        EventBus.subscribe("DIVISION_RULES_CHANGED", self.refresh_all)

    # ─── Filter Logic ────────────────────────────────────────────────
    def _load_initial_filters(self):
        combo_loaders.load_years(self.year_box)
        self._on_year_changed()

    def _on_year_changed(self):
        with QSignalBlocker(self.term_box), QSignalBlocker(self.exam_box):
            combo_loaders.load_terms(self.term_box, self.year_box.currentData())
            self._on_term_changed()

    def _on_term_changed(self):
        with QSignalBlocker(self.exam_box):
            combo_loaders.load_all_exams_for_report(
                self.exam_box,
                year_id=self.year_box.currentData(),
                term_id=self.term_box.currentData(),
                level=self._history_level
            )
            self._on_filter_changed()

    def _on_filter_changed(self):
        self._update_current_page()

    def _get_current_context(self):
        exam_id = self.exam_box.currentData()
        class_name = self.class_box.currentText().strip()
        if exam_id is None or not class_name:
            return None
        return exam_id, class_name, self._history_level

    def _update_current_page(self):
        context = self._get_current_context()
        page = self.stacked.currentWidget()
        if not context:
            if hasattr(page, "clear_history_context"):
                page.clear_history_context()
            return
        if hasattr(page, "set_history_context"):
            page.set_history_context(*context)

    # ─── Page Switching ──────────────────────────────────────────────
    def _switch_page(self, index):
        self.btn_broadsheet.setChecked(index == 0)
        self.btn_remarks.setChecked(index == 1)
        self.btn_reports.setChecked(index == 2)

        self.stacked.setCurrentIndex(index)
        self._update_current_page()

    # ─── Refresh & Events ────────────────────────────────────────────
    def refresh_all(self):
        self._history_level = SystemState.get_level()
        if not self.isVisible():
            self._needs_refresh = True
            return
        with QSignalBlocker(self.year_box), QSignalBlocker(self.term_box), QSignalBlocker(self.exam_box):
            combo_loaders.load_years(self.year_box)
            self._on_year_changed()
        self._update_current_page()

    def _on_data_changed(self):
        if self.isVisible():
            self._update_current_page()
        else:
            self._needs_refresh = True

    def showEvent(self, event):
        super().showEvent(event)
        if self._needs_refresh:
            self._needs_refresh = False
            self.refresh_all()

    # ─── Compatibility for MainWindow navigation ─────────────────────
    def activate_broadsheet(self, exam_id, class_name, level=None):
        self._set_filters_from_context(exam_id, class_name, level)
        self._switch_page(0)

    def activate_reports(self, exam_id, class_name, level=None):
        self._set_filters_from_context(exam_id, class_name, level)
        self._switch_page(2)

    def _set_filters_from_context(self, exam_id, class_name, level):
        from db_utils import fetch_one
        row = fetch_one("""
            SELECT e.term_id, t.academic_year_id
            FROM exams e
            JOIN terms t ON e.term_id = t.id
            WHERE e.id = ?
        """, (exam_id,))
        if row:
            term_id, year_id = row
            with QSignalBlocker(self.year_box), QSignalBlocker(self.term_box), \
                 QSignalBlocker(self.exam_box), QSignalBlocker(self.class_box):
                idx = self.year_box.findData(year_id)
                if idx >= 0:
                    self.year_box.setCurrentIndex(idx)
                combo_loaders.load_terms(self.term_box, year_id)
                idx = self.term_box.findData(term_id)
                if idx >= 0:
                    self.term_box.setCurrentIndex(idx)
                combo_loaders.load_all_exams_for_report(
                    self.exam_box,
                    year_id=year_id,
                    term_id=term_id,
                    level=level or self._history_level
                )
                idx = self.exam_box.findData(exam_id)
                if idx >= 0:
                    self.exam_box.setCurrentIndex(idx)
                self.class_box.setCurrentText(class_name)
        self._update_current_page()
