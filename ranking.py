from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QComboBox,
    QLabel,
    QHeaderView,
    QAbstractItemView,
    QScrollArea,
    QSizePolicy,
    QFrame,
)

from PySide6.QtCore import Qt

from db_utils import fetch_one
from system_state import SystemState
from event_bus import EventBus
from ranking_engine import compute_student_scores
import combo_loaders


class RankingPage(QWidget):

    def __init__(self):
        super().__init__()

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

        filters = QHBoxLayout()
        self.class_box = QComboBox()
        combo_loaders.load_classes(self.class_box)
        self.class_box.currentIndexChanged.connect(self.load)
        filters.addWidget(QLabel("Class"))
        filters.addWidget(self.class_box)
        filters.addStretch()
        layout.addLayout(filters)

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
        EventBus.subscribe("LEVEL_CHANGED", self.refresh_classes)
        EventBus.subscribe("SUBJECT_REQUIREMENTS_CHANGED", self.load)
        EventBus.subscribe("GRADE_RULES_CHANGED", self.load)
        EventBus.subscribe("DIVISION_RULES_CHANGED", self.load)

        self.history_exam_id = None
        self.history_class_name = None

        self.load()

    def refresh_classes(self):
        current_class = self.class_box.currentText().strip()
        combo_loaders.load_classes(self.class_box)
        index = self.class_box.findText(current_class)
        if index >= 0:
            self.class_box.setCurrentIndex(index)
        self.load()

    def set_history_context(self, exam_id, class_name):
        self.history_exam_id = exam_id
        self.history_class_name = class_name

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

        index = self.class_box.findText(class_name)
        if index >= 0:
            self.class_box.setCurrentIndex(index)
        self.load()

    def clear_history_context(self):
        self.history_exam_id = None
        self.history_class_name = None
        self.context_label.setText("")
        self.load()

    def load(self):
        level = SystemState.get_level()
        class_name = self.history_class_name or self.class_box.currentText().strip()
        exam_id = self.history_exam_id
        ranking = compute_student_scores(level, exam_id=exam_id, class_name=class_name)

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
                
                # Ensure items are read-only but still allow selection and copying
                table_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                
                # Center align metrics
                if col in [0, 3, 4, 5, 6, 7, 8]:
                    table_item.setTextAlignment(Qt.AlignCenter)

                # Styling based on status
                if item.get("status") == "INCOMPLETE":
                    table_item.setForeground(Qt.gray)
                elif item.get("status") == "READY":
                    if col == 8: # Status column
                        table_item.setForeground(Qt.darkGreen)
                        font = table_item.font()
                        font.setBold(True)
                        table_item.setFont(font)
                
                self.table.setItem(row, col, table_item)

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
