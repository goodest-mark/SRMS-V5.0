from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QTableWidget,
    QMessageBox,
    QAbstractItemView,
    QLabel,
    QInputDialog,
)
from PySide6.QtCore import Qt

from db_utils import get_cursor, fetch_all, fetch_one
from table_utils import setup_table, populate_table
from ui_helpers import show_error, show_info, confirm_action, load_combo
from backup_utils import create_pre_operation_backup
from event_bus import EventBus
from security_settings import authorize_action


class TermsPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # Top: Year selector + Add term
        top = QHBoxLayout()
        self.year_box = QComboBox()
        self.year_box.currentIndexChanged.connect(self.load)

        self.term_box = QComboBox()
        self.term_box.addItems(["Term I", "Term II"])

        self.add_btn = QPushButton("ADD TERM")
        self.add_btn.clicked.connect(self.add_term)

        top.addWidget(QLabel("Academic Year:"))
        top.addWidget(self.year_box)
        top.addWidget(QLabel("Term:"))
        top.addWidget(self.term_box)
        top.addWidget(self.add_btn)
        top.addStretch()

        layout.addLayout(top)

        # Table
        self.table = QTableWidget()
        setup_table(self.table, ["ID", "Term", "Academic Year", "Active"])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_term)

        layout.addWidget(self.table)

        # Actions
        actions = QHBoxLayout()
        self.activate_btn = QPushButton("SET ACTIVE")
        self.activate_btn.clicked.connect(self.activate_term)
        self.deactivate_btn = QPushButton("SET INACTIVE")
        self.deactivate_btn.clicked.connect(self.deactivate_term)
        self.edit_btn = QPushButton("EDIT NAME")
        self.edit_btn.clicked.connect(self.edit_term)
        self.delete_btn = QPushButton("DELETE (Archive)")
        self.delete_btn.clicked.connect(self.delete_term)

        actions.addWidget(self.activate_btn)
        actions.addWidget(self.deactivate_btn)
        actions.addWidget(self.edit_btn)
        actions.addWidget(self.delete_btn)
        actions.addStretch()
        layout.addLayout(actions)

        self.setLayout(layout)

        self.load_years()
        self.load()

    def load_years(self):
        rows = fetch_all("""
            SELECT year_name, id
            FROM academic_years
            ORDER BY year_name DESC
        """)
        load_combo(self.year_box, rows)

    def load(self):
        year_id = self.year_box.currentData()

        rows = fetch_all("""
            SELECT t.id, t.term_name, a.year_name, t.is_active
            FROM terms t
            JOIN academic_years a ON t.academic_year_id=a.id
            ORDER BY t.id DESC
        """)

        populate_table(
            self.table, rows,
            formatters={3: lambda v: "YES" if v else "NO"}
        )

    def add_term(self):
        if self.year_box.count() == 0:
            show_error(self, "Create academic year first.")
            return

        year_id = self.year_box.currentData()
        term_name = self.term_box.currentText()

        try:
            with get_cursor(commit=True) as cur:
                cur.execute("""
                    SELECT id FROM terms
                    WHERE term_name=? AND academic_year_id=?
                """, (term_name, year_id))
                if cur.fetchone():
                    show_error(self, "Term already exists for this year.")
                    return

                cur.execute("""
                    INSERT INTO terms(term_name, academic_year_id, is_active)
                    VALUES (?, ?, 0)
                """, (term_name, year_id))
            self.load()
            EventBus.emit("EXAMS_UPDATED")
        except Exception as e:
            show_error(self, str(e))

    def edit_term(self):
        row = self.table.currentRow()
        if row < 0:
            show_error(self, "Select a term first.")
            return

        term_id = self.table.item(row, 0).text()
        current_name = self.table.item(row, 1).text()

        new_name, ok = QInputDialog.getText(
            self, "Edit Term", "New term name:",
            text=current_name
        )
        if ok and new_name.strip():
            try:
                with get_cursor(commit=True) as cur:
                    cur.execute("""
                        UPDATE terms
                        SET term_name=?
                        WHERE id=?
                    """, (new_name.strip(), term_id))
                self.load()
                EventBus.emit("EXAMS_UPDATED")
            except Exception as e:
                show_error(self, str(e))

    def activate_term(self):
        row = self.table.currentRow()
        if row < 0:
            show_error(self, "Select a term first.")
            return
        term_id = self.table.item(row, 0).text()

        try:
            with get_cursor(commit=True) as cur:
                cur.execute("UPDATE terms SET is_active=0")
                cur.execute("""
                    UPDATE terms SET is_active=1 WHERE id=?
                """, (term_id,))
            self.load()
            EventBus.emit("EXAMS_UPDATED")
        except Exception as e:
            show_error(self, str(e))

    def deactivate_term(self):
        row = self.table.currentRow()
        if row < 0:
            show_error(self, "Select a term first.")
            return
        term_id = self.table.item(row, 0).text()

        # Check if active
        row_data = fetch_one("SELECT is_active FROM terms WHERE id=?", (term_id,))
        if row_data and row_data[0] == 1:
            if not confirm_action(
                self,
                "Deactivate Active Term",
                "This term is currently active. Deactivating it will hide it from most dropdowns.\n"
                "Do you want to continue?"
            ):
                return

        try:
            with get_cursor(commit=True) as cur:
                cur.execute("""
                    UPDATE terms SET is_active=0 WHERE id=?
                """, (term_id,))
            self.load()
            EventBus.emit("EXAMS_UPDATED")
        except Exception as e:
            show_error(self, str(e))

    def delete_term(self):
        row = self.table.currentRow()
        if row < 0:
            show_error(self, "Select a term first.")
            return

        term_id = self.table.item(row, 0).text()
        term_name = self.table.item(row, 1).text()

        # Check if active
        row_data = fetch_one("SELECT is_active FROM terms WHERE id=?", (term_id,))
        if row_data and row_data[0] == 1:
            show_error(self, "Cannot delete the active term. Please deactivate it first.")
            return

        # Count associated exams
        count_data = fetch_one("""
            SELECT COUNT(*) FROM exams WHERE term_id=?
        """, (term_id,))
        exam_count = count_data[0] if count_data else 0

        if exam_count > 0:
            msg = (
                f"Deleting term '{term_name}' will permanently remove {exam_count} exam(s) "
                "and all their associated results and enrollments.\n\n"
                "This action is irreversible. A backup will be created first."
            )
            if not confirm_action(self, "Confirm Deletion", msg):
                return

        if not authorize_action(self, "Delete Term"):
            return

        try:
            backup_path = create_pre_operation_backup("delete_term")
        except Exception as e:
            show_error(self, f"Backup failed. Deletion cancelled.\n\n{e}")
            return

        try:
            with get_cursor(commit=True) as cur:
                cur.execute("DELETE FROM terms WHERE id=?", (term_id,))
            self.load()
            EventBus.emit("EXAMS_UPDATED")
            show_info(
                self,
                f"Term '{term_name}' and all associated data have been removed.\n"
                f"Backup saved: {backup_path}",
                title="Deletion Complete"
            )
        except Exception as e:
            show_error(self, f"Deletion failed: {e}")
