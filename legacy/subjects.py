from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHBoxLayout,
    QAbstractItemView,
    QHeaderView
)

from database import connect
from theme import APP_STYLE
from add_subject import AddSubjectWindow


class SubjectsWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Subject Management")

        self.resize(1000, 600)

        self.setStyleSheet(APP_STYLE)

        layout = QVBoxLayout()

        # =========================
        # TOP BUTTONS
        # =========================

        top = QHBoxLayout()

        self.add_btn = QPushButton(
            "ADD SUBJECT"
        )

        self.add_btn.clicked.connect(
            self.open_add_subject
        )

        self.delete_btn = QPushButton(
            "DELETE SUBJECT"
        )

        self.delete_btn.clicked.connect(
            self.delete_subject
        )

        self.refresh_btn = QPushButton(
            "REFRESH"
        )

        self.refresh_btn.clicked.connect(
            self.load_data
        )

        top.addWidget(self.add_btn)
        top.addWidget(self.delete_btn)
        top.addWidget(self.refresh_btn)

        # =========================
        # TABLE
        # =========================

        self.table = QTableWidget()

        self.table.setColumnCount(4)

        self.table.setHorizontalHeaderLabels([
            "ID",
            "Subject Code",
            "Subject Name",
            "Counted"
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

        self.table.verticalHeader().setDefaultSectionSize(
            40
        )

        self.table.setAlternatingRowColors(True)

        # =========================
        # LAYOUT
        # =========================

        layout.addLayout(top)
        layout.addWidget(self.table)

        self.setLayout(layout)

        self.load_data()

    # =========================
    # OPEN ADD WINDOW
    # =========================

    def open_add_subject(self):

        self.add_window = AddSubjectWindow()
        self.add_window.show()

    # =========================
    # LOAD SUBJECTS
    # =========================

    def load_data(self):

        conn = connect()

        cur = conn.cursor()

        cur.execute("""
        SELECT
            id,
            subject_code,
            subject_name,
            is_counted
        FROM subjects
        ORDER BY subject_name
        """)

        rows = cur.fetchall()

        conn.close()

        self.table.setRowCount(
            len(rows)
        )

        for r, row in enumerate(rows):

            for c, value in enumerate(row):

                self.table.setItem(
                    r,
                    c,
                    QTableWidgetItem(
                        str(value)
                    )
                )

    # =========================
    # DELETE SUBJECT
    # =========================

    def delete_subject(self):

        row = self.table.currentRow()

        if row < 0:

            QMessageBox.warning(
                self,
                "Error",
                "Select Subject First"
            )

            return

        subject_code = self.table.item(
            row,
            1
        ).text()

        reply = QMessageBox.question(
            self,
            "Delete",
            f"Delete {subject_code} ?",
            QMessageBox.Yes |
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:

            conn = connect()

            cur = conn.cursor()

            cur.execute(
                """
                DELETE FROM subjects
                WHERE subject_code=?
                """,
                (subject_code,)
            )

            conn.commit()
            conn.close()

            self.load_data()

            QMessageBox.information(
                self,
                "Success",
                "Subject Deleted"
            )