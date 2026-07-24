from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QTableWidget,
    QMessageBox,
    QAbstractItemView,
    QInputDialog,
)
from PySide6.QtCore import Qt

from db_utils import get_cursor, fetch_all, fetch_one
from table_utils import setup_table, populate_table
from ui_helpers import show_error, show_info, confirm_action
from backup_utils import create_pre_operation_backup
from event_bus import EventBus
from security_settings import authorize_action


class AcademicYearsPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # Top: Add new year
        top = QHBoxLayout()
        self.year_input = QLineEdit()
        self.year_input.setPlaceholderText("Academic Year e.g 2027")
        self.add_btn = QPushButton("ADD YEAR")
        self.add_btn.clicked.connect(self.add_year)

        top.addWidget(self.year_input)
        top.addWidget(self.add_btn)
        top.addStretch()

        layout.addLayout(top)

        # Table
        self.table = QTableWidget()
        setup_table(self.table, ["ID", "Year", "Active"])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_year)

        layout.addWidget(self.table)

        # Action buttons row
        actions = QHBoxLayout()
        self.activate_btn = QPushButton("SET ACTIVE")
        self.activate_btn.clicked.connect(self.activate_year)
        self.deactivate_btn = QPushButton("SET INACTIVE")
        self.deactivate_btn.clicked.connect(self.deactivate_year)
        self.edit_btn = QPushButton("EDIT NAME")
        self.edit_btn.clicked.connect(self.edit_year)
        self.delete_btn = QPushButton("DELETE (Archive)")
        self.delete_btn.clicked.connect(self.delete_year)

        actions.addWidget(self.activate_btn)
        actions.addWidget(self.deactivate_btn)
        actions.addWidget(self.edit_btn)
        actions.addWidget(self.delete_btn)
        actions.addStretch()
        layout.addLayout(actions)

        self.setLayout(layout)

        self.load()

    def load(self):
        rows = fetch_all("""
            SELECT id, year_name, is_active
            FROM academic_years
            ORDER BY id DESC
        """)
        populate_table(
            self.table, rows,
            formatters={2: lambda v: "YES" if v else "NO"}
        )

    def add_year(self):
        year = self.year_input.text().strip()
        if not year:
            show_error(self, "Enter a year name.")
            return

        try:
            with get_cursor(commit=True) as cur:
                cur.execute("""
                    INSERT INTO academic_years (year_name)
                    VALUES (?)
                """, (year,))
            self.year_input.clear()
            self.load()
            EventBus.emit("EXAMS_UPDATED")
        except Exception as e:
            show_error(self, str(e))

    def edit_year(self):
        row = self.table.currentRow()
        if row < 0:
            show_error(self, "Select a year first.")
            return

        year_id = self.table.item(row, 0).text()
        current_name = self.table.item(row, 1).text()

        new_name, ok = QInputDialog.getText(
            self, "Edit Year", "New year name:",
            text=current_name
        )
        if ok and new_name.strip():
            try:
                with get_cursor(commit=True) as cur:
                    cur.execute("""
                        UPDATE academic_years
                        SET year_name=?
                        WHERE id=?
                    """, (new_name.strip(), year_id))
                self.load()
                EventBus.emit("EXAMS_UPDATED")
            except Exception as e:
                show_error(self, str(e))

    def activate_year(self):
        row = self.table.currentRow()
        if row < 0:
            show_error(self, "Select a year first.")
            return
        year_id = self.table.item(row, 0).text()

        try:
            with get_cursor(commit=True) as cur:
                cur.execute("UPDATE academic_years SET is_active=0")
                cur.execute("""
                    UPDATE academic_years
                    SET is_active=1
                    WHERE id=?
                """, (year_id,))
            self.load()
            EventBus.emit("EXAMS_UPDATED")
        except Exception as e:
            show_error(self, str(e))

    def deactivate_year(self):
        row = self.table.currentRow()
        if row < 0:
            show_error(self, "Select a year first.")
            return
        year_id = self.table.item(row, 0).text()

        # Check if it's currently active
        row_data = fetch_one("SELECT is_active FROM academic_years WHERE id=?", (year_id,))
        if row_data and row_data[0] == 1:
            if not confirm_action(
                self,
                "Deactivate Active Year",
                "This year is currently active. Deactivating it will hide it from most dropdowns.\n"
                "Do you want to continue?"
            ):
                return

        try:
            with get_cursor(commit=True) as cur:
                cur.execute("""
                    UPDATE academic_years
                    SET is_active=0
                    WHERE id=?
                """, (year_id,))
            self.load()
            EventBus.emit("EXAMS_UPDATED")
        except Exception as e:
            show_error(self, str(e))

    def delete_year(self):
        row = self.table.currentRow()
        if row < 0:
            show_error(self, "Select a year first.")
            return

        year_id = self.table.item(row, 0).text()
        year_name = self.table.item(row, 1).text()

        # Check if it's active
        row_data = fetch_one("SELECT is_active FROM academic_years WHERE id=?", (year_id,))
        if row_data and row_data[0] == 1:
            show_error(self, "Cannot delete the active year. Please deactivate it first.")
            return

        # Count associated data
        count_data = fetch_one("""
            SELECT COUNT(*) FROM terms WHERE academic_year_id=?
        """, (year_id,))
        term_count = count_data[0] if count_data else 0

        if term_count > 0:
            msg = (
                f"Deleting year '{year_name}' will permanently remove {term_count} term(s) "
                "and all their associated exams, results, and enrollments.\n\n"
                "This action is irreversible. A backup will be created first."
            )
            if not confirm_action(self, "Confirm Deletion", msg):
                return

        if not authorize_action(self, "Delete Academic Year"):
            return

        try:
            backup_path = create_pre_operation_backup("delete_year")
        except Exception as e:
            show_error(self, f"Backup failed. Deletion cancelled.\n\n{e}")
            return

        try:
            with get_cursor(commit=True) as cur:
                cur.execute("DELETE FROM terms WHERE academic_year_id=?", (year_id,))
                cur.execute("DELETE FROM academic_years WHERE id=?", (year_id,))
            self.load()
            EventBus.emit("EXAMS_UPDATED")
            show_info(
                self,
                f"Year '{year_name}' and all its associated data have been removed.\n"
                f"Backup saved: {backup_path}",
                title="Deletion Complete"
            )
        except Exception as e:
            show_error(self, f"Deletion failed: {e}")
