from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QAbstractItemView,
    QHeaderView
)

from database import connect


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

        self.table.setColumnCount(3)

        self.table.setHorizontalHeaderLabels([
            "ID",
            "Year",
            "Active"
        ])

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        layout.addLayout(top)
        layout.addWidget(self.table)

        self.setLayout(layout)

        self.load()

    def add_year(self):

        year = self.year_input.text().strip()

        if not year:
            return

        conn = connect()
        cur = conn.cursor()

        try:

            cur.execute("""
                INSERT INTO academic_years(
                    year_name
                )
                VALUES(?)
            """, (year,))

            conn.commit()

            self.year_input.clear()

            self.load()

        except Exception as e:

            QMessageBox.warning(
                self,
                "Error",
                str(e)
            )

        conn.close()

    def activate_year(self):

        row = self.table.currentRow()

        if row < 0:
            return

        year_id = self.table.item(
            row,
            0
        ).text()

        conn = connect()
        cur = conn.cursor()

        try:
            cur.execute("""
                UPDATE academic_years
                SET is_active=0
            """)

            cur.execute("""
                UPDATE academic_years
                SET is_active=1
                WHERE id=?
            """, (year_id,))

            conn.commit()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(
                self,
                "Database Error",
                f"Failed to activate year: {e}"
            )
        finally:
            conn.close()

        self.load()

    def load(self):

        conn = connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                year_name,
                is_active
            FROM academic_years
            ORDER BY id DESC
        """)

        rows = cur.fetchall()

        conn.close()

        self.table.setRowCount(
            len(rows)
        )

        for r, row in enumerate(rows):

            active = "YES"

            if row[2] == 0:
                active = "NO"

            self.table.setItem(
                r, 0,
                QTableWidgetItem(str(row[0]))
            )

            self.table.setItem(
                r, 1,
                QTableWidgetItem(row[1])
            )

            self.table.setItem(
                r, 2,
                QTableWidgetItem(active)
            )