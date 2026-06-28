import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from class_utils import get_classes
from db_utils import fetch_all
from event_bus import EventBus
from system_state import SystemState
from theme import APP_STYLE
import combo_loaders


class ReadinessPage(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ranking Readiness")
        self.setMinimumSize(850, 550)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("RANKING READINESS")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: white;"
        )
        layout.addWidget(title)

        filters = QHBoxLayout()

        self.exam = QComboBox()
        self.exam.setMinimumWidth(200)
        self.exam.setPlaceholderText("Select Exam")

        self.class_box = QComboBox()
        self.class_box.setMinimumWidth(160)
        self.class_box.setPlaceholderText("Select Class")

        self.refresh_btn = QPushButton("REFRESH")
        self.refresh_btn.clicked.connect(self.refresh_all)

        filters.addWidget(QLabel("Exam"))
        filters.addWidget(self.exam)
        filters.addWidget(QLabel("Class"))
        filters.addWidget(self.class_box)
        filters.addStretch()
        filters.addWidget(self.refresh_btn)

        layout.addLayout(filters)

        summary_group = QGroupBox("Summary")
        summary_layout = QGridLayout(summary_group)

        self.students_value = QLabel("0")
        self.ready_value = QLabel("0")
        self.incomplete_value = QLabel("0")
        self.completion_value = QLabel("0.00%")

        summary_values = (
            self.students_value,
            self.ready_value,
            self.incomplete_value,
            self.completion_value,
        )

        for label in summary_values:
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(
                "font-size: 18px; font-weight: bold; color: white;"
            )

        summary_layout.addWidget(QLabel("Students"), 0, 0)
        summary_layout.addWidget(QLabel("Ready"), 0, 1)
        summary_layout.addWidget(QLabel("Incomplete"), 0, 2)
        summary_layout.addWidget(QLabel("Completion %"), 0, 3)
        summary_layout.addWidget(self.students_value, 1, 0)
        summary_layout.addWidget(self.ready_value, 1, 1)
        summary_layout.addWidget(self.incomplete_value, 1, 2)
        summary_layout.addWidget(self.completion_value, 1, 3)

        layout.addWidget(summary_group)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Admission No",
            "Student Name",
            "Required",
            "Available",
            "Missing",
            "Status",
        ])
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )

        for column in range(2, 6):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )

        layout.addWidget(self.table, 1)

        self.exam.currentIndexChanged.connect(self.load_readiness)
        self.class_box.currentIndexChanged.connect(self.load_readiness)

        EventBus.subscribe("LEVEL_CHANGED", self.on_level_changed)
        EventBus.subscribe("RESULTS_UPDATED", self.load_readiness)
        EventBus.subscribe("STUDENTS_UPDATED", self.load_readiness)
        EventBus.subscribe("SUBJECTS_UPDATED", self.load_readiness)
        EventBus.subscribe("EXAMS_UPDATED", self.refresh_all)

        self.refresh_all()

    def on_level_changed(self):
        self.refresh_all()

    def load(self):
        self.load_readiness()

    def refresh_all(self):
        self.load_exams()
        self.load_classes()
        self.load_readiness()

    def load_exams(self):
        combo_loaders.load_all_exams(self.exam)

    def load_classes(self):
        combo_loaders.load_classes(self.class_box)

    def load_readiness(self):
        exam_id = self.exam.currentData()
        class_name = self.class_box.currentText().strip()
        level = SystemState.get_level()

        if exam_id is None or not class_name:
            self.table.setRowCount(0)
            self._set_summary(0, 0)
            return

        required = 3 if level == "A_LEVEL" else 7
        subject_type = (
            "PRINCIPAL"
            if level == "A_LEVEL"
            else "COUNTED"
        )

        rows = fetch_all("""
            SELECT s.admission_no,
                   s.full_name,
                   COUNT(DISTINCT sub.subject_name)
            FROM students s
            LEFT JOIN results r
              ON r.admission_no=s.admission_no
             AND r.exam_id=?
            LEFT JOIN subjects sub
              ON sub.subject_name=r.subject_name
             AND sub.level=s.level
             AND sub.subject_type=?
            WHERE s.level=?
              AND s.class=?
            GROUP BY s.id,
                     s.admission_no,
                     s.full_name
            ORDER BY s.full_name,
                     s.admission_no
        """, (
            exam_id,
            subject_type,
            level,
            class_name,
        ))

        ready_count = sum(
            available >= required
            for _, _, available in rows
        )

        self.table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            admission_no, full_name, available = row
            missing = max(required - available, 0)

            if available >= required:
                status = "READY"
                status_color = QColor("#22c55e")
            else:
                status = "INCOMPLETE"
                status_color = QColor("#ef4444")

            values = (
                admission_no,
                full_name or "",
                required,
                available,
                missing,
                status,
            )

            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))

                if column >= 2:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                if column == 5:
                    item.setForeground(status_color)
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

                self.table.setItem(row_index, column, item)

        self._set_summary(len(rows), ready_count)

    def _set_summary(self, students, ready):
        incomplete = max(students - ready, 0)
        completion = (
            ready / students * 100
            if students > 0
            else 0
        )

        self.students_value.setText(str(students))
        self.ready_value.setText(str(ready))
        self.incomplete_value.setText(str(incomplete))
        self.completion_value.setText(f"{completion:.2f}%")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)

    window = ReadinessPage()
    window.show()

    sys.exit(app.exec())
