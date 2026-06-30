from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView,
    QAbstractItemView,
)

from progress_dialog import ProgressDialog

from PySide6.QtGui import QColor


from db_utils import fetch_all, execute_many
from system_state import SystemState
from event_bus import EventBus


class GradeRulesPage(QWidget):

    def __init__(self):
        super().__init__()
        self.resize(900,650)
        self.setMinimumSize(800,600)

        self.setObjectName("GradeRulesPage")

        layout = QVBoxLayout(self)

        self.title = QLabel()
        self.title.setStyleSheet("""
            font-size:22px;
            font-weight:bold;
            color:#60a5fa;
            padding:8px;
        """)
        layout.addWidget(self.title)

        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.table.itemChanged.connect(self.validate_table)

        layout.addWidget(self.table, 1)
        self.save_btn = QPushButton("SAVE GRADE RULES")
        self.save_btn.setStyleSheet("background-color:#10b981;font-weight:bold;padding:8px;")

        self.reset_btn = QPushButton("RESTORE DEFAULTS")
        self.reset_btn.setStyleSheet("background-color:#ef4444;font-weight:bold;padding:8px;")

        buttons = QHBoxLayout()
        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.reset_btn)

        layout.addLayout(buttons)

        self.save_btn.clicked.connect(self.save_rules)
        self.reset_btn.clicked.connect(self.reset_defaults)

        EventBus.subscribe(
            "LEVEL_CHANGED",
            self.load_rules
        )

        self.ids = []

        self.load_rules()

        self.load_rules()

    def load_rules(self):

        level = SystemState.get_level()

        self.title.setText(
            f"GRADE RULES ({level.replace('_', '-')})"
        )

        rows = fetch_all("""
            SELECT
                id,
                grade,
                min_mark,
                max_mark,
                points
            FROM grade_rules
            WHERE level=?
            ORDER BY sort_order
        """, (level,))

        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Grade",
            "Minimum",
            "Maximum",
            "Points"
        ])

        self.table.setRowCount(len(rows))

        self.ids = []

        for r, row in enumerate(rows):

            self.ids.append(row[0])

            grade = QTableWidgetItem(str(row[1]))
            grade.setFlags(
                grade.flags() & ~grade.flags().ItemIsEditable
            )

            self.table.setItem(r, 0, grade)
            self.table.setItem(r, 1, QTableWidgetItem(str(row[2])))
            self.table.setItem(r, 2, QTableWidgetItem(str(row[3])))
            self.table.setItem(r, 3, QTableWidgetItem(str(row[4])))


    def save_rules(self):

        updates = []
        ranges = []

        for row, rule_id in enumerate(self.ids):

            try:
                minimum = int(self.table.item(row, 1).text())
                maximum = int(self.table.item(row, 2).text())
                points = int(self.table.item(row, 3).text())
            except (ValueError, AttributeError):
                QMessageBox.warning(
                    self,
                    "Invalid Data",
                    "All values must be numeric."
                )
                return

            grade = self.table.item(row, 0).text()

            if minimum < 0 or maximum > 100:
                QMessageBox.warning(
                    self,
                    "Invalid Marks",
                    f"{grade}: marks must be between 0 and 100."
                )
                return

            if minimum > maximum:
                QMessageBox.warning(
                    self,
                    "Invalid Range",
                    f"{grade}: minimum cannot exceed maximum."
                )
                return

            for other_grade, other_min, other_max in ranges:
                if minimum <= other_max and maximum >= other_min:
                    QMessageBox.warning(
                        self,
                        "Overlapping Grades",
                        f"{grade} overlaps with {other_grade}."
                    )
                    return

            ranges.append((grade, minimum, maximum))

            updates.append((
                minimum,
                maximum,
                points,
                rule_id
            ))

        execute_many("""
            UPDATE grade_rules
            SET
                min_mark=?,
                max_mark=?,
                points=?
            WHERE id=?
        """, updates)

        QMessageBox.information(
            self,
            "Success",
            "Grade rules saved successfully."
        )

        EventBus.emit("GRADE_RULES_CHANGED")


    def reset_defaults(self):

        reply = QMessageBox.question(
            self,
            "Restore Defaults",
            "Restore default grading rules for the current level?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        from database import init_db

        init_db()
        self.load_rules()


    def validate_table(self):

        for row in range(self.table.rowCount()):

            try:
                minimum = int(self.table.item(row,1).text())
                maximum = int(self.table.item(row,2).text())
                points = int(self.table.item(row,3).text())
            except Exception:
                continue

            ok = (
                0 <= minimum <= 100 and
                0 <= maximum <= 100 and
                minimum <= maximum and
                points > 0
            )

            color = "#1f4d2b" if ok else "#6b1f1f"

            for col in (1,2,3):
                self.table.item(row,col).setBackground(QColor(color))

