from PySide6.QtCore import Qt, QTimer, Signal, QSignalBlocker
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QScrollArea,
    QTabWidget,
    QSizePolicy,
    QWidget,
)

from class_utils import get_classes
from event_bus import EventBus
from ranking_engine import compute_student_scores
from system_state import SystemState
import combo_loaders

class HistoricalResultsPage(QWidget):
    open_ranking_requested = Signal(int, str)
    open_broadsheet_requested = Signal(int, str)
    open_reports_requested = Signal(int, str)

    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setUsesScrollButtons(False)
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(self.tabs, 1)

        self._history_reload_timer = QTimer(self)
        self._history_reload_timer.setSingleShot(True)
        self._history_reload_timer.setInterval(40)
        self._history_reload_timer.timeout.connect(self._load_history_now)
        self._history_cache = {}

        self._pages = {}
        self._page_factories = {
            "Ranking": lambda: self._create_ranking_page(),
            "Broadsheet": lambda: self._create_broadsheet_page(),
            "Remarks": lambda: self._create_remarks_page(),
            "Reports": lambda: self._create_reports_page(),
        }

        self.list_tab = QWidget()
        self.tabs.addTab(self.list_tab, "List")
        self._build_list_tab(self.list_tab)

        # Placeholders
        for name in ["Ranking", "Broadsheet", "Remarks", "Reports"]:
            self.tabs.addTab(QWidget(), name)

        self.tabs.currentChanged.connect(self._on_tab_changed)

        self._ranking_page = None
        self._broadsheet_page = None
        self._report_book_page = None
        self._active_history_exam_id = None
        self._active_history_class_name = None
        self._active_history_level = None
        self._history_level = SystemState.get_level()

        EventBus.subscribe("LEVEL_CHANGED", self.refresh_all)
        EventBus.subscribe("RESULTS_UPDATED", self._on_history_data_changed)
        EventBus.subscribe("STUDENTS_UPDATED", self._on_history_data_changed)
        EventBus.subscribe("EXAMS_UPDATED", self.refresh_all)

    def _on_tab_changed(self, index):
        if index < 0: return
        name = self.tabs.tabText(index)
        
        if name in self._page_factories and name not in self._pages:
            self.tabs.blockSignals(True)
            page = self._page_factories[name]()
            self._pages[name] = page
            
            # Replace placeholder
            old_widget = self.tabs.widget(index)
            self.tabs.removeTab(index)
            self.tabs.insertTab(index, page, name)
            self.tabs.setCurrentIndex(index)
            self.tabs.blockSignals(False)
            
            if old_widget:
                old_widget.deleteLater()
            
            # If we have an active context, set it immediately
            context = self._selected_or_active_context()
            if context:
                page.set_history_context(*context)
        
        elif name in self._pages:
            # Already loaded, just ensure context is synced if needed
            context = self._selected_or_active_context()
            if context:
                self._pages[name].set_history_context(*context)

    def _create_ranking_page(self):
        from ranking import RankingPage
        return RankingPage()

    def _create_broadsheet_page(self):
        from ui.pages.broadsheet_page import BroadsheetPage
        return BroadsheetPage()

    def _create_reports_page(self):
        from report_book_page import ReportBookPage
        return ReportBookPage()

    def _create_remarks_page(self):
        from remarks_page import RemarksPage
        return RemarksPage()

    def _selected_or_active_context(self):
        context = self._selected_history_context()
        if context:
            return context
        if self._active_history_exam_id is not None and self._active_history_class_name:
            return (
                self._active_history_exam_id,
                self._active_history_class_name,
                self._active_history_level or self._history_level,
            )
        return None

    def _build_list_tab(self, parent):
        outer = QVBoxLayout(parent)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(scroll, 1)

        content = QWidget()
        scroll.setWidget(content)

        root = QVBoxLayout(content)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        title = QLabel("HISTORICAL RESULTS")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search completed exam...")
        self.search_bar.textChanged.connect(self.load_exams)
        root.addWidget(self.search_bar)

        filters = QHBoxLayout()
        self.year_box = QComboBox()
        self.term_box = QComboBox()
        self.exam_box = QComboBox()
        self.class_box = QComboBox()
        self.class_box.addItems(get_classes())

        self.year_box.currentIndexChanged.connect(self.load_terms)
        self.term_box.currentIndexChanged.connect(self.load_exams)
        self.exam_box.currentIndexChanged.connect(self.load_history)
        self.class_box.currentIndexChanged.connect(self.load_history)

        for label, widget in (
            ("Year", self.year_box),
            ("Term", self.term_box),
            ("Exam", self.exam_box),
            ("Class", self.class_box),
        ):
            filters.addWidget(QLabel(label))
            filters.addWidget(widget)
        filters.addStretch()
        root.addLayout(filters)

        summary = QGroupBox("Historical Summary")
        summary_layout = QGridLayout(summary)

        self.total_value = QLabel("0")
        self.ready_value = QLabel("0")
        self.incomplete_value = QLabel("0")
        self.class_avg_value = QLabel("0.00%")

        for widget in (
            self.total_value,
            self.ready_value,
            self.incomplete_value,
            self.class_avg_value,
        ):
            widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        summary_layout.addWidget(QLabel("Students"), 0, 0)
        summary_layout.addWidget(QLabel("Ready"), 0, 1)
        summary_layout.addWidget(QLabel("Incomplete"), 0, 2)
        summary_layout.addWidget(QLabel("Class Avg"), 0, 3)
        summary_layout.addWidget(self.total_value, 1, 0)
        summary_layout.addWidget(self.ready_value, 1, 1)
        summary_layout.addWidget(self.incomplete_value, 1, 2)
        summary_layout.addWidget(self.class_avg_value, 1, 3)
        root.addWidget(summary)

        self.empty_label = QLabel("")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setWordWrap(True)
        root.addWidget(self.empty_label)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Position",
            "Admission",
            "Name",
            "Gender",
            "Subjects",
            "Total Marks",
            "Average",
            "Division",
            "Status",
        ])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        for column in range(3, 9):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
        root.addWidget(self.table, 1)

        self.detail_hint = QLabel(
            "Select a completed exam and a class, then choose a view action from the history tabs."
        )
        self.detail_hint.setWordWrap(True)
        self.detail_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.detail_hint)

    def _create_archive_tab(self, message):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        label = QLabel(message)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        layout.addWidget(label)
        return tab

    def refresh_all(self):
        self._history_level = SystemState.get_level()
        self._invalidate_history_cache()
        blockers = [QSignalBlocker(widget) for widget in (self.year_box, self.term_box, self.exam_box, self.class_box)]
        try:
            combo_loaders.load_years(self.year_box)
            combo_loaders.load_terms(self.term_box, self.year_box.currentData())
            combo_loaders.load_completed_exams(
                self.exam_box,
                self.year_box.currentData(),
                self.term_box.currentData(),
                level=self._history_level,
                search_text=self.search_bar.text().strip(),
            )
            combo_loaders.load_classes(self.class_box)
        finally:
            del blockers
        self._schedule_history_reload()

    def load_terms(self):
        blockers = [QSignalBlocker(self.term_box), QSignalBlocker(self.exam_box)]
        try:
            combo_loaders.load_terms(self.term_box, self.year_box.currentData())
            self.load_exams()
        finally:
            del blockers

    def load_exams(self):
        blockers = [QSignalBlocker(self.exam_box)]
        try:
            combo_loaders.load_completed_exams(
                self.exam_box,
                self.year_box.currentData(),
                self.term_box.currentData(),
                level=self._history_level or SystemState.get_level(),
                search_text=self.search_bar.text().strip(),
            )
        finally:
            del blockers
        self._schedule_history_reload()

    def _selected_history_context(self):
        exam_id = self.exam_box.currentData()
        class_name = self.class_box.currentText().strip()
        if exam_id is None or not class_name:
            return None
        return exam_id, class_name, self._history_level or SystemState.get_level()

    def show_list(self):
        self.tabs.setCurrentIndex(0)
        self._schedule_history_reload()

    def showEvent(self, event):
        super().showEvent(event)
        if getattr(self, "_needs_refresh", False):
            self._needs_refresh = False
            self.refresh_all()


    def activate_ranking(self, exam_id, class_name, level=None):
        self.tabs.setCurrentIndex(1)
        page = self._pages.get("Ranking")
        if page:
            page.set_history_context(exam_id, class_name, level=level)
            self.detail_hint.setText(f"Showing ranking for exam #{exam_id} in {class_name}.")
        return page

    def activate_broadsheet(self, exam_id, class_name, level=None):
        self.tabs.setCurrentIndex(2)
        page = self._pages.get("Broadsheet")
        if page:
            page.set_history_context(exam_id, class_name, level=level)
            self.detail_hint.setText(f"Showing broadsheet for exam #{exam_id} in {class_name}.")
        return page

    def activate_reports(self, exam_id, class_name, level=None):
        self.tabs.setCurrentIndex(3)
        page = self._pages.get("Reports")
        if page:
            page.set_history_context(exam_id, class_name, level=level)
            self.detail_hint.setText(f"Showing report books for exam #{exam_id} in {class_name}.")
        return page

    def open_ranking(self):
        context = self._selected_history_context()
        if not context:
            QMessageBox.information(
                self,
                "History",
                "Select a completed exam and class first.",
            )
            return
        exam_id, class_name, level = context
        self._active_history_exam_id = exam_id
        self._active_history_class_name = class_name
        self._active_history_level = level
        self.activate_ranking(exam_id, class_name, level=level)

    def open_broadsheet(self):
        context = self._selected_history_context()
        if not context:
            QMessageBox.information(
                self,
                "History",
                "Select a completed exam and class first.",
            )
            return
        exam_id, class_name, level = context
        self._active_history_exam_id = exam_id
        self._active_history_class_name = class_name
        self._active_history_level = level
        self.activate_broadsheet(exam_id, class_name, level=level)

    def open_reports(self):
        context = self._selected_history_context()
        if not context:
            QMessageBox.information(
                self,
                "History",
                "Select a completed exam and class first.",
            )
            return
        exam_id, class_name, level = context
        self._active_history_exam_id = exam_id
        self._active_history_class_name = class_name
        self._active_history_level = level
        self.activate_reports(exam_id, class_name, level=level)

    def load_history(self):
        self._schedule_history_reload()

    def _schedule_history_reload(self):
        self._load_history_now()

    def _on_history_data_changed(self):
        self._invalidate_history_cache()
        if self.isVisible():
            self._schedule_history_reload()
        else:
            self._needs_refresh = True

    def _invalidate_history_cache(self):
        self._history_cache.clear()

    def _load_history_now(self):
        exam_id = self.exam_box.currentData()
        class_name = self.class_box.currentText().strip()
        level = self._history_level or SystemState.get_level()

        if exam_id is None or not class_name:
            self.table.setRowCount(0)
            self._set_summary(0, 0, 0, 0)
            self.empty_label.setText("Select a completed exam and a class to view archived results.")
            self.detail_hint.setText(
                "History is empty until you choose a completed exam and class."
            )
            return

        self._active_history_exam_id = exam_id
        self._active_history_class_name = class_name

        cache_key = (level, exam_id, class_name)
        ranking = self._history_cache.get(cache_key)
        if ranking is None:
            ranking = compute_student_scores(level, exam_id, class_name)
            self._history_cache[cache_key] = ranking

        class_students = [s for s in ranking if s.get("class") == class_name]
        if not class_students:
            self.table.setRowCount(0)
            self._set_summary(0, 0, 0, 0)
            self.empty_label.setText("No archived results found for the selected exam and class.")
            self.detail_hint.setText("No archived results matched the selected filters.")
            return

        ready_students = [s for s in class_students if s["status"] == "READY"]
        incomplete_students = [s for s in class_students if s["status"] != "READY"]
        class_avg = round(
            sum(s["average"] for s in ready_students) / len(ready_students), 2
        ) if ready_students else 0

        self.table.setUpdatesEnabled(False)
        try:
            self.table.setRowCount(len(class_students))
            self.empty_label.setText("")
            for row, student in enumerate(class_students):
                values = [
                    student.get("position", "-"),
                    student.get("admission", ""),
                    student.get("name", ""),
                    student.get("gender", ""),
                    student.get("subjects", 0),
                    student.get("total_marks", "-"),
                    student.get("average", "-"),
                    student.get("division", "-"),
                    student.get("status", "UNKNOWN"),
                ]

                for column, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    if column in (0, 4, 5, 6, 7, 8):
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if column == 8:
                        item.setForeground(Qt.darkGreen if student.get("status") == "READY" else Qt.red)
                    self.table.setItem(row, column, item)
        finally:
            self.table.setUpdatesEnabled(True)
            self.table.resizeRowsToContents()
        table_height = (
            self.table.horizontalHeader().height()
            + self.table.verticalHeader().length()
            + self.table.frameWidth() * 2
            + 4
        )
        self.table.setFixedHeight(table_height)

        self._set_summary(len(class_students), len(ready_students), len(incomplete_students), class_avg)
        self.detail_hint.setText(
            f"Showing archived results for exam #{exam_id} in {class_name}."
        )

    def _set_summary(self, total, ready, incomplete, class_avg):
        self.total_value.setText(str(total))
        self.ready_value.setText(str(ready))
        self.incomplete_value.setText(str(incomplete))
        self.class_avg_value.setText(f"{class_avg:.2f}%")
