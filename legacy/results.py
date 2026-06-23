from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QAbstractItemView,
    QHeaderView
)

import sqlite3

from database import connect
from theme import APP_STYLE
from grade_utils import get_grade, get_points


class ResultsWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Results Engine")

        self.resize(1200, 700)

        self.setStyleSheet(APP_STYLE)

        layout = QVBoxLayout()

        # =========================
        # TOP
        # =========================

        top = QHBoxLayout()

        self.exam_box = QComboBox()
        self.load_exams()

        self.student_box = QComboBox()
        self.load_students()

        load_btn = QPushButton("LOAD")
        load_btn.clicked.connect(self.load_subjects)

        calc_btn = QPushButton("CALCULATE")
        calc_btn.clicked.connect(self.calculate_results)

        top.addWidget(QLabel("Exam"))
        top.addWidget(self.exam_box)

        top.addWidget(QLabel("Student"))
        top.addWidget(self.student_box)

        top.addWidget(load_btn)
        top.addWidget(calc_btn)

        # =========================
        # TABLE
        # =========================

        self.table = QTableWidget()
        self.table.setColumnCount(4)

        self.table.setHorizontalHeaderLabels([
            "Subject",
            "Marks",
            "Grade",
            "Points"
        ])

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        # =========================
        # SUMMARY LABEL
        # =========================

        self.summary = QLabel("Summary will appear here...")

        # =========================
        # LAYOUT
        # =========================

        layout.addLayout(top)
        layout.addWidget(self.table)
        layout.addWidget(self.summary)

        self.setLayout(layout)

    # =========================
    # LOAD EXAMS
    # =========================

    def load_exams(self):

        with connect() as conn:
            cur = conn.cursor()

            cur.execute("""
            SELECT id, exam_name || ' - ' || term || ' - ' || year
            FROM exams
            ORDER BY id DESC
            """)

            self.exams = cur.fetchall()

        self.exam_box.clear()

        for e in self.exams:
            self.exam_box.addItem(e[1], e[0])

    # =========================
    # LOAD STUDENTS
    # =========================

    def load_students(self):

        with connect() as conn:
            cur = conn.cursor()

            cur.execute("""
            SELECT admission_no, full_name
            FROM students
            ORDER BY full_name
            """)

            self.students = cur.fetchall()

        self.student_box.clear()

        for s in self.students:
            self.student_box.addItem(f"{s[0]} - {s[1]}", s[0])

    # =========================
    # LOAD SUBJECTS (COUNTED ONLY)
    # =========================

    def load_subjects(self):

        conn = sqlite3.connect("srms.db")
        cur = conn.cursor()

        cur.execute("""
        SELECT subject_code, subject_name
        FROM subjects
        WHERE is_counted='Yes'
        """)

        rows = cur.fetchall()
        conn.close()

        self.table.setRowCount(len(rows))

        for r, row in enumerate(rows):

            self.table.setItem(r, 0, QTableWidgetItem(row[0] + " - " + row[1]))
            self.table.setItem(r, 1, QTableWidgetItem(""))
            self.table.setItem(r, 2, QTableWidgetItem(""))
            self.table.setItem(r, 3, QTableWidgetItem(""))

    # =========================
    # CALCULATE RESULTS
    # =========================

    def calculate_results(self):

        total = 0
        count = 0

        for row in range(self.table.rowCount()):

            marks_item = self.table.item(row, 1)

            if not marks_item:
                continue

            try:
                marks = float(marks_item.text())

            except (ValueError, TypeError):
                continue

            grade = get_grade(marks)
            points = get_points(grade)

            self.table.setItem(row, 2, QTableWidgetItem(grade))
            self.table.setItem(row, 3, QTableWidgetItem(str(points)))

            total += marks
            count += 1

        if count == 0:
            self.summary.setText("No marks entered")
            return

        avg = total / count

        final_grade = get_grade(avg)

        self.summary.setText(
            f"TOTAL: {total} | AVERAGE: {avg:.2f} | FINAL GRADE: {final_grade}"
        )