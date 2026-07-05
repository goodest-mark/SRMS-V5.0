from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QTableWidget,
    QMessageBox,
)

from progress_dialog import ProgressDialog

from db_utils import get_cursor, fetch_all
from table_utils import setup_table, populate_table
from ui_helpers import show_error


class AcademicYearsPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        top = QHBoxLayout()

        self.year_input = QLineEdit()
        self.year_input.setPlaceholderText("Academic Year e.g 2027")

        self.add_btn = QPushButton("ADD YEAR")
        self.add_btn.clicked.connect(self.add_year)

        self.activate_btn = QPushButton("SET ACTIVE")
        self.activate_btn.clicked.connect(self.activate_year)

        top.addWidget(self.year_input)
        top.addWidget(self.add_btn)
        top.addWidget(self.activate_btn)

        self.table = QTableWidget()
        setup_table(self.table, ["ID", "Year", "Active"])

        layout.addLayout(top)
        layout.addWidget(self.table)

        self.setLayout(layout)

        self.load()

    def add_year(self):

        year = self.year_input.text().strip()

        if not year:
            return

        try:
            with get_cursor(commit=True) as cur:
                cur.execute("""
                    INSERT INTO academic_years(
                        year_name
                    )
                    VALUES(?)
                """, (year,))

            self.year_input.clear()
            self.load()

        except Exception as e:
            show_error(self, str(e))

    def activate_year(self):

        row = self.table.currentRow()

        if row < 0:
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
        except Exception as e:
            QMessageBox.critical(
                self,
                "Database Error",
                f"Failed to activate year: {e}"
            )

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