from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QTableWidget,
    QMessageBox,
)

from progress_dialog import ProgressDialog

from db_utils import get_cursor, fetch_all
from table_utils import setup_table, populate_table
from ui_helpers import show_error, load_combo


class TermsPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # =========================
        # TOP BAR
        # =========================

        top = QHBoxLayout()

        self.year_box = QComboBox()

        self.term_box = QComboBox()
        self.term_box.addItems([
            "Term I",
            "Term II"
        ])

        self.add_btn = QPushButton("ADD TERM")
        self.add_btn.clicked.connect(
            self.add_term
        )

        self.activate_btn = QPushButton(
            "SET ACTIVE"
        )

        self.activate_btn.clicked.connect(
            self.activate_term
        )

        top.addWidget(self.year_box)
        top.addWidget(self.term_box)
        top.addWidget(self.add_btn)
        top.addWidget(self.activate_btn)

        # =========================
        # TABLE
        # =========================

        self.table = QTableWidget()
        setup_table(self.table, ["ID", "Term", "Academic Year", "Active"])

        # =========================
        # LAYOUT
        # =========================

        layout.addLayout(top)
        layout.addWidget(self.table)

        self.setLayout(layout)

        self.load_years()
        self.load()

    # =========================
    # LOAD YEARS
    # =========================

    def load_years(self):

        rows = fetch_all("""
            SELECT year_name, id
            FROM academic_years
            ORDER BY year_name DESC
        """)

        load_combo(self.year_box, rows)

    # =========================
    # ADD TERM
    # =========================

    def add_term(self):

        if self.year_box.count() == 0:
            show_error(self, "Create academic year first")
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
                    show_error(self, "Term already exists")
                    return

                cur.execute("""
                    INSERT INTO terms(term_name, academic_year_id, is_active)
                    VALUES (?, ?, 0)
                """, (term_name, year_id))

            self.load()

        except Exception as e:
            show_error(self, str(e))

    # =========================
    # ACTIVATE TERM
    # =========================

    def activate_term(self):

        row = self.table.currentRow()

        if row < 0:
            return

        term_id = self.table.item(row, 0).text()

        try:
            with get_cursor(commit=True) as cur:
                cur.execute("UPDATE terms SET is_active=0")
                cur.execute("""
                    UPDATE terms SET is_active=1 WHERE id=?
                """, (term_id,))
        except Exception as e:
            QMessageBox.critical(
                self,
                "Database Error",
                f"Failed to activate term: {e}"
            )

        self.load()

    # =========================
    # LOAD TERMS
    # =========================

    def load(self):

        rows = fetch_all("""
            SELECT
                t.id,
                t.term_name,
                a.year_name,
                t.is_active
            FROM terms t
            JOIN academic_years a
            ON t.academic_year_id=a.id
            ORDER BY t.id DESC
        """)

        populate_table(
            self.table, rows,
            formatters={3: lambda v: "YES" if v else "NO"}
        )