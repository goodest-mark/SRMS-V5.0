from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QHeaderView,
    QAbstractItemView
)

from progress_dialog import ProgressDialog
from PySide6.QtCore import Qt

from system_state import SystemState
from event_bus import EventBus
from ranking_engine import compute_student_scores


class RankingPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.title = QLabel("CLASS RANKING")
        self.title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        layout.addWidget(self.title)

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

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)

        layout.addWidget(self.table)

        # EVENTS
        EventBus.subscribe("RESULTS_UPDATED", self.load)
        EventBus.subscribe("STUDENTS_UPDATED", self.load)
        EventBus.subscribe("LEVEL_CHANGED", self.load)

        self.load()

    def load(self):
        level = SystemState.get_level()
        ranking = compute_student_scores(level)

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
