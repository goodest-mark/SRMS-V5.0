from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
)

from db_utils import get_cursor, fetch_all
from table_utils import setup_table, populate_table
from ui_helpers import confirm_action, show_error
from event_bus import EventBus
from security_settings import authorize_action
from add_exam import AddExamWindow
from system_state import SystemState

class ExamsWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Examinations")

        self.resize(1000, 650)

        layout = QVBoxLayout()

        top = QHBoxLayout()

        self.add_btn = QPushButton("Add Exam")
        self.add_btn.setObjectName("workflowPrimary")

        self.add_btn.clicked.connect(
            self.open_add
        )

        self.edit_btn = QPushButton("Edit Selected")
        self.edit_btn.setObjectName("workflowSecondary")

        self.edit_btn.clicked.connect(
            self.open_edit
        )

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.setObjectName("workflowDanger")

        self.delete_btn.clicked.connect(
            self.delete_exam
        )

        self.status_btn = QPushButton("Open / Close")
        self.status_btn.setObjectName("workflowSecondary")

        self.status_btn.clicked.connect(
            self.toggle_status
        )

        self.complete_btn = QPushButton("Complete Selected")
        self.complete_btn.setObjectName("workflowWarning")

        self.complete_btn.clicked.connect(
            self.complete_exam
        )

        top.addWidget(self.add_btn)
        top.addWidget(self.edit_btn)
        top.addWidget(self.status_btn)
        top.addWidget(self.complete_btn)
        top.addStretch()
        top.addWidget(self.delete_btn)

        self.table = QTableWidget()
        setup_table(self.table, ["ID", "Exam", "Term", "Year", "Level", "Status"])

        layout.addLayout(top)
        layout.addWidget(self.table)

        self.setLayout(layout)

        self.table.itemSelectionChanged.connect(self._update_action_state)

        EventBus.subscribe(
            "EXAMS_UPDATED",
            self.load_data
        )
        EventBus.subscribe(
            "LEVEL_CHANGED",
            self.load_data
        )

        self.load_data()
        self._update_action_state()

    def open_add(self):

        self.win = AddExamWindow()
        self.win.show()

    def open_edit(self):

        row = self.table.currentRow()
        if row < 0:
            show_error(self, "Select exam first")
            return

        exam_id = self.table.item(row, 0).text()
        self.win = AddExamWindow(exam_id=exam_id)
        self.win.show()

    def load_data(self):

        level = SystemState.get_level()

        rows = fetch_all("""
            SELECT
                e.id,
                e.exam_name,
                t.term_name,
                a.year_name,
                e.level,
                e.status
            FROM exams e
            JOIN terms t ON e.term_id=t.id
            JOIN academic_years a ON t.academic_year_id=a.id
            WHERE e.level=?
              AND e.status != 'COMPLETED'
            ORDER BY e.id DESC
        """, (level,))

        populate_table(self.table, rows)
        self._update_action_state()

    def _update_action_state(self):
        """Keep actions aligned with the selected exam's lifecycle state."""
        row = self.table.currentRow()
        has_selection = row >= 0 and self.table.item(row, 5) is not None
        status = self.table.item(row, 5).text() if has_selection else None

        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        self.status_btn.setEnabled(has_selection and status != "COMPLETED")
        self.complete_btn.setEnabled(has_selection and status != "COMPLETED")

        if status == "OPEN":
            self.status_btn.setText("Close Selected")
        elif status == "CLOSED":
            self.status_btn.setText("Reopen Selected")
        else:
            self.status_btn.setText("Open / Close")

    def delete_exam(self):

        row = self.table.currentRow()

        if row < 0:
            show_error(self, "Select exam first")
            return

        exam_id = self.table.item(row, 0).text()

        if not confirm_action(self, "Delete", "Delete selected exam?"):
            return

        if not authorize_action(self, "Delete Exam"):
            return

        with get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM exams WHERE id=?", (exam_id,))

        EventBus.emit("EXAMS_UPDATED")

    def toggle_status(self):

        row = self.table.currentRow()

        if row < 0:
            return

        if not authorize_action(self, "Toggle Exam Status"):
            return

        exam_id = self.table.item(row, 0).text()
        status = self.table.item(row, 5).text()
        level = self.table.item(row, 4).text()

        if status == "COMPLETED":
            show_error(
                self,
                "Completed exams are read-only. Manage historical results from History."
            )
            return

        new_status = "CLOSED" if status == "OPEN" else "OPEN"

        with get_cursor(commit=True) as cur:
            if new_status == "OPEN":
                cur.execute("""
                    UPDATE exams SET status='CLOSED'
                    WHERE level=? AND id<>? AND status='OPEN'
                """, (level, exam_id))

            cur.execute("""
                UPDATE exams SET status=? WHERE id=?
            """, (new_status, exam_id))

        EventBus.emit("EXAMS_UPDATED")

    def complete_exam(self):

        row = self.table.currentRow()

        if row < 0:
            show_error(self, "Select exam first")
            return

        exam_id = self.table.item(row, 0).text()
        status = self.table.item(row, 5).text()

        if status == "COMPLETED":
            show_error(self, "This exam is already completed.")
            return

        if not confirm_action(
            self,
            "Complete Exam",
            "Save this exam as COMPLETED? Results will become read-only."
        ):
            return

        if not authorize_action(self, "Complete Exam"):
            return

        with get_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE exams SET status='COMPLETED' WHERE id=?
            """, (exam_id,))

        EventBus.emit("EXAMS_UPDATED")
        EventBus.emit("RESULTS_UPDATED")
