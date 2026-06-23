from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QAbstractItemView,
    QHeaderView
)

from database import connect


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

        self.table.setColumnCount(4)

        self.table.setHorizontalHeaderLabels([
            "ID",
            "Term",
            "Academic Year",
            "Active"
        ])

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            QHeaderView.Stretch
        )

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

        self.year_box.clear()

        conn = connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT id,
                   year_name
            FROM academic_years
            ORDER BY year_name DESC
        """)

        rows = cur.fetchall()

        conn.close()

        for row in rows:

            self.year_box.addItem(
                row[1],
                row[0]
            )

    # =========================
    # ADD TERM
    # =========================

    def add_term(self):

        if self.year_box.count() == 0:

            QMessageBox.warning(
                self,
                "Error",
                "Create academic year first"
            )

            return

        year_id = self.year_box.currentData()

        term_name = (
            self.term_box.currentText()
        )

        conn = connect()
        cur = conn.cursor()

        try:

            cur.execute("""
                SELECT id
                FROM terms
                WHERE term_name=?
                AND academic_year_id=?
            """, (
                term_name,
                year_id
            ))

            if cur.fetchone():

                QMessageBox.warning(
                    self,
                    "Error",
                    "Term already exists"
                )

                conn.close()

                return

            cur.execute("""
                INSERT INTO terms(
                    term_name,
                    academic_year_id,
                    is_active
                )
                VALUES (?, ?, 0)
            """, (
                term_name,
                year_id
            ))

            conn.commit()

            self.load()

        except Exception as e:

            QMessageBox.warning(
                self,
                "Error",
                str(e)
            )

        conn.close()

    # =========================
    # ACTIVATE TERM
    # =========================

    def activate_term(self):

        row = self.table.currentRow()

        if row < 0:
            return

        term_id = self.table.item(
            row,
            0
        ).text()

        conn = connect()
        cur = conn.cursor()

        try:
            cur.execute("""
                UPDATE terms
                SET is_active=0
            """)

            cur.execute("""
                UPDATE terms
                SET is_active=1
                WHERE id=?
            """, (term_id,))

            conn.commit()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(
                self,
                "Database Error",
                f"Failed to activate term: {e}"
            )
        finally:
            conn.close()

        self.load()

    # =========================
    # LOAD TERMS
    # =========================

    def load(self):

        conn = connect()
        cur = conn.cursor()

        cur.execute("""
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

        rows = cur.fetchall()

        conn.close()

        self.table.setRowCount(
            len(rows)
        )

        for r, row in enumerate(rows):

            active = "YES"

            if row[3] == 0:
                active = "NO"

            self.table.setItem(
                r,
                0,
                QTableWidgetItem(
                    str(row[0])
                )
            )

            self.table.setItem(
                r,
                1,
                QTableWidgetItem(
                    row[1]
                )
            )

            self.table.setItem(
                r,
                2,
                QTableWidgetItem(
                    row[2]
                )
            )

            self.table.setItem(
                r,
                3,
                QTableWidgetItem(
                    active
                )
            )