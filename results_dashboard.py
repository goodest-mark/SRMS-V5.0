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
from db_utils import fetch_all, fetch_one
from event_bus import EventBus
from system_state import SystemState
from theme import APP_STYLE
import combo_loaders


class ResultsDashboard(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Results Dashboard")
        self.setMinimumSize(850, 550)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("RESULTS PREPARATION DASHBOARD")
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

        self.subject_filter = QComboBox()
        self.subject_filter.addItems([
            "All",
            "Pending",
            "Completed",
        ])

        self.refresh_btn = QPushButton("REFRESH")
        self.refresh_btn.clicked.connect(self.refresh_all)

        filters.addWidget(QLabel("Exam"))
        filters.addWidget(self.exam)
        filters.addWidget(QLabel("Class"))
        filters.addWidget(self.class_box)
        filters.addWidget(QLabel("Subjects"))
        filters.addWidget(self.subject_filter)
        filters.addStretch()
        filters.addWidget(self.refresh_btn)

        layout.addLayout(filters)

        # =====================================
        # OVERALL SUMMARY
        # =====================================
        summary_group = QGroupBox("Overall Progress")
        summary_layout = QGridLayout(summary_group)

        self.expected_results_value = QLabel("0")
        self.entered_results_value = QLabel("0")
        self.missing_results_value = QLabel("0")
        self.overall_completion_value = QLabel("0.00%")

        summary_values = (
            self.expected_results_value,
            self.entered_results_value,
            self.missing_results_value,
            self.overall_completion_value,
        )

        for label in summary_values:
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(
                "font-size: 18px; font-weight: bold; color: white;"
            )

        summary_layout.addWidget(QLabel("Expected Results"), 0, 0)
        summary_layout.addWidget(QLabel("Entered Results"), 0, 1)
        summary_layout.addWidget(QLabel("Missing Results"), 0, 2)
        summary_layout.addWidget(QLabel("Overall Completion %"), 0, 3)
        summary_layout.addWidget(self.expected_results_value, 1, 0)
        summary_layout.addWidget(self.entered_results_value, 1, 1)
        summary_layout.addWidget(self.missing_results_value, 1, 2)
        summary_layout.addWidget(self.overall_completion_value, 1, 3)

        layout.addWidget(summary_group)

        # =====================================
        # SUBJECT TABLE
        # =====================================
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Subject",
            "Expected",
            "Entered",
            "Missing",
            "Completion %",
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
        self.table.doubleClicked.connect(self.open_results_entry)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Stretch,
        )

        for column in range(1, 6):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )

        layout.addWidget(self.table, 1)

        self.exam.currentIndexChanged.connect(self.load_dashboard)
        self.class_box.currentIndexChanged.connect(self.load_dashboard)
        self.subject_filter.currentIndexChanged.connect(
            self.load_dashboard
        )

        EventBus.subscribe("LEVEL_CHANGED", self.on_level_changed)
        EventBus.subscribe("RESULTS_UPDATED", self.load_dashboard)
        EventBus.subscribe("STUDENTS_UPDATED", self.load_dashboard)
        EventBus.subscribe("EXAMS_UPDATED", self.refresh_all)

        self.refresh_all()

    def on_level_changed(self):
        self.refresh_all()

    def load(self):
        self.load_dashboard()

    def refresh_all(self):
        self.load_exams()
        self.load_classes()
        self.load_dashboard()

    def load_exams(self):
        combo_loaders.load_open_exams(self.exam)

    def load_classes(self):
        combo_loaders.load_classes(self.class_box)

    def load_dashboard(self):
        exam_id = self.exam.currentData()
        class_name = self.class_box.currentText().strip()
        level = SystemState.get_level()

        if exam_id is None or not class_name:
            self.table.setRowCount(0)
            self._set_summary(0, 0)
            return

        from db_utils import get_exam_context
        context = get_exam_context(exam_id)
        
        if not context:
            self.table.setRowCount(0)
            self._set_summary(0, 0)
            return
            
        year_id, term_id = context

        rows = fetch_all("""
            SELECT 
                e.subject_name,
                COUNT(DISTINCT e.admission_no) as expected,
                COUNT(DISTINCT r.admission_no) as entered
            FROM enrollments e
            JOIN students s ON s.admission_no = e.admission_no
            LEFT JOIN results r ON r.subject_name = e.subject_name
                AND r.exam_id = ?
                AND r.admission_no = e.admission_no
            WHERE s.class = ? AND s.level = ?
              AND e.academic_year_id = ? AND e.term_id = ?
            GROUP BY e.subject_name
            ORDER BY e.subject_name
        """, (
            exam_id,
            class_name,
            level,
            year_id,
            term_id
        ))

        overall_expected = sum(row[1] for row in rows)
        overall_entered = sum(row[2] for row in rows)
        self._set_summary(overall_expected, overall_entered)

        selected_filter = self.subject_filter.currentText()
        visible_rows = []

        for subject_name, expected, entered in rows:
            missing = max(expected - entered, 0)
            completion = (
                entered / expected * 100
                if expected > 0
                else 0
            )

            # STATUS RULES V4:
            # 0% = NOT STARTED
            # 1% - 99% = IN PROGRESS
            # 100% = COMPLETE
            if completion >= 100:
                completion = 100
                status = "COMPLETE"
                status_color = QColor("#22c55e")
            elif completion > 0:
                status = "IN PROGRESS"
                status_color = QColor("#f59e0b")
            else:
                status = "NOT STARTED"
                status_color = QColor("#ef4444")

            if selected_filter == "Completed" and status != "COMPLETE":
                continue

            if selected_filter == "Pending" and status == "COMPLETE":
                continue

            visible_rows.append((
                subject_name,
                expected,
                entered,
                missing,
                completion,
                status,
                status_color,
            ))

        self.table.setRowCount(len(visible_rows))

        for row_index, row in enumerate(visible_rows):
            (
                subject_name,
                subject_expected,
                entered,
                missing,
                completion,
                status,
                status_color,
            ) = row

            values = (
                subject_name,
                subject_expected,
                entered,
                missing,
                f"{completion:.2f}%",
                status,
            )

            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))

                if column > 0:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                if column == 5:
                    item.setForeground(status_color)
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

                self.table.setItem(row_index, column, item)

    def _set_summary(self, expected, entered):
        missing = max(expected - entered, 0)
        completion = (
            entered / expected * 100
            if expected > 0
            else 0
        )

        self.expected_results_value.setText(str(expected))
        self.entered_results_value.setText(str(entered))
        self.missing_results_value.setText(str(missing))
        self.overall_completion_value.setText(
            f"{completion:.2f}%"
        )

    def open_results_entry(self, _index=None):
        row = self.table.currentRow()
        exam_id = self.exam.currentData()
        class_name = self.class_box.currentText().strip()

        if row < 0 or exam_id is None or not class_name:
            return

        subject_item = self.table.item(row, 0)

        if subject_item is None:
            return

        EventBus.emit(
            "OPEN_RESULTS_ENTRY",
            exam_id,
            class_name,
            subject_item.text(),
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)

    window = ResultsDashboard()
    window.show()

    sys.exit(app.exec())
