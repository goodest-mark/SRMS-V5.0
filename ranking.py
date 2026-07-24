from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QHeaderView,
    QAbstractItemView,
    QScrollArea,
    QSizePolicy,
    QFrame,
    QProgressBar,
)

from db_utils import fetch_one
from system_state import SystemState
from event_bus import EventBus
from ranking_engine import compute_student_scores


# ------------------------------------------------------------------
# Background worker for ranking data
# ------------------------------------------------------------------
class RankingWorker(QThread):
    finished = Signal(list)

    def __init__(self, level, exam_id, class_name):
        super().__init__()
        self.level = level
        self.exam_id = exam_id
        self.class_name = class_name

    def run(self):
        ranking = compute_student_scores(self.level, exam_id=self.exam_id, class_name=self.class_name)
        self.finished.emit(ranking)


class RankingPage(QWidget):

    def __init__(self):
        super().__init__()

        self.history_exam_id = None
        self.history_class_name = None
        self.history_level = None
        self._worker = None
        self._needs_refresh = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        root.addWidget(self.scroll_area, 1)

        content = QWidget()
        self.scroll_area.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.title = QLabel("CLASS RANKING")
        layout.addWidget(self.title)

        self.context_label = QLabel("")
        layout.addWidget(self.context_label)

        # Loading progress bar (hidden by default)
        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 0)  # Indeterminate – spinning animation
        self.loading_bar.setFormat("Loading ranking data...")
        self.loading_bar.setVisible(False)
        layout.addWidget(self.loading_bar)

        # TABLE
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Position",
            "Admission",
            "Full Name",
            "Subjects",
            "Total Marks",
            "Average",
            "Points",
            "Division",
            "Status"
        ])

        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)

        layout.addWidget(self.table)

        # EVENTS
        EventBus.subscribe("RESULTS_UPDATED", self.load)
        EventBus.subscribe("STUDENTS_UPDATED", self.load)
        EventBus.subscribe("LEVEL_CHANGED", self.refresh_level)
        EventBus.subscribe("SUBJECT_REQUIREMENTS_CHANGED", self.load)
        EventBus.subscribe("GRADE_RULES_CHANGED", self.load)
        EventBus.subscribe("DIVISION_RULES_CHANGED", self.load)

        # Load initially (will show empty because no context yet)
        self.load()

    # ------------------------------------------------------------------
    # Background loading
    # ------------------------------------------------------------------
    def start_background_load(self):
        """Start loading ranking data in the background with a loading bar."""
        if self._worker is not None and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait()

        self.loading_bar.setVisible(True)
        self.table.setRowCount(0)
        self.table.setVisible(False)

        level = self.history_level or SystemState.get_level()
        class_name = self.history_class_name
        exam_id = self.history_exam_id

        # If no context, just show empty
        if not exam_id or not class_name:
            self.loading_bar.setVisible(False)
            self.table.setVisible(True)
            self.table.setRowCount(0)
            self._update_table_height()
            return

        self._worker = RankingWorker(level, exam_id, class_name)
        self._worker.finished.connect(self.on_data_loaded)
        self._worker.start()

    def on_data_loaded(self, ranking):
        """Callback when ranking data is ready."""
        self.loading_bar.setVisible(False)
        self.table.setVisible(True)
        self._populate_table(ranking)
        self._update_table_height()

    # ------------------------------------------------------------------
    # Table population
    # ------------------------------------------------------------------
    def _populate_table(self, ranking):
        self.table.setUpdatesEnabled(False)
        try:
            self.table.setRowCount(len(ranking))

            for row, item in enumerate(ranking):
                values = [
                    item.get("position", "-"),
                    item.get("admission", ""),
                    item.get("name", ""),
                    item.get("subjects", 0),
                    item.get("total_marks", "-"),
                    item.get("average", "-"),
                    item.get("points", "-"),
                    item.get("division", "-"),
                    item.get("status", "UNKNOWN")
                ]

                for col, value in enumerate(values):
                    table_item = QTableWidgetItem(str(value))
                    table_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

                    if col in [0, 3, 4, 5, 6, 7, 8]:
                        table_item.setTextAlignment(Qt.AlignCenter)

                    if item.get("status") == "INCOMPLETE":
                        table_item.setForeground(Qt.gray)
                    elif item.get("status") == "READY":
                        if col == 8:
                            table_item.setForeground(Qt.darkGreen)
                            font = table_item.font()
                            font.setBold(True)
                            table_item.setFont(font)

                    self.table.setItem(row, col, table_item)

        finally:
            self.table.setUpdatesEnabled(True)

    def _update_table_height(self):
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        table_height = (
            self.table.horizontalHeader().height()
            + self.table.frameWidth() * 2
            + self.table.verticalHeader().length()
            + 4
        )
        self.table.setMinimumHeight(table_height)
        self.table.setMaximumHeight(table_height)

    # ------------------------------------------------------------------
    # Public methods / event handlers
    # ------------------------------------------------------------------
    def refresh_level(self):
        self.history_level = SystemState.get_level()
        self.load()

    def set_history_context(self, exam_id, class_name, level=None):
        self.history_exam_id = exam_id
        self.history_class_name = class_name
        self.history_level = level or SystemState.get_level()

        row = fetch_one("""
            SELECT e.exam_name, t.term_name, y.year_name
            FROM exams e
            JOIN terms t ON t.id = e.term_id
            JOIN academic_years y ON y.id = t.academic_year_id
            WHERE e.id = ?
        """, (exam_id,))

        if row:
            exam_name, term_name, year_name = row
            self.context_label.setText(
                f"History context: {exam_name} - {term_name} - {year_name} - {class_name}"
            )
        else:
            self.context_label.setText(f"History context: Exam #{exam_id} - {class_name}")

        self.load()

    def clear_history_context(self):
        self.history_exam_id = None
        self.history_class_name = None
        self.history_level = None
        self.context_label.setText("")
        self.load()

    def showEvent(self, event):
        super().showEvent(event)
        if self._needs_refresh:
            self._needs_refresh = False
            self.load()

    def load(self):
        if not self.isVisible():
            self._needs_refresh = True
            return
        self.start_background_load()