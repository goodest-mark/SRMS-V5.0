from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QScrollArea, QWidget,
    QGridLayout, QGroupBox, QAbstractItemView
)

from progress_dialog import ProgressDialog
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtCore import Qt

from db_utils import fetch_one, fetch_all
from ranking_engine import compute_student_scores
from grade_utils import get_grade, get_points


class StudentProfile(QDialog):

    def __init__(self, admission_no, level):
        super().__init__()

        self.admission_no = admission_no
        self.level = level

        self.setWindowTitle(f"Student Profile - {admission_no}")
        self.resize(1100, 850)

        self.setStyleSheet("""
        QDialog{background:#081225;color:#e2e8f0;}
        QGroupBox{
            background:#0f172a;
            border:1px solid #1e293b;
            border-radius:18px;
            margin-top:12px;
            padding-top:14px;
            color:#60a5fa;
            font-weight:bold;
        }
        QGroupBox::title{
            left:12px;
            padding:0 6px;
        }
        QTableWidget{
            background:#0b1427;
            border:1px solid #1e293b;
            border-radius:12px;
        }
        QHeaderView::section{
            background:#17253c;
            color:white;
            border:none;
            padding:8px;
        }
        QLabel{background:transparent;}
        """)

        root = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        self.content_layout = QVBoxLayout(container)

        scroll.setWidget(container)
        root.addWidget(scroll)

        self.load_data()
        self.build_ui()

    def load_data(self):
        self.basic_info = fetch_one("""
            SELECT admission_no, full_name, gender, class, stream, level
            FROM students
            WHERE admission_no=?
        """, (self.admission_no,))

        self.results = fetch_all("""
            SELECT r.subject_name, e.exam_name, r.marks
            FROM results r
            JOIN exams e ON e.id=r.exam_id
            WHERE r.admission_no=? AND e.level=?
            ORDER BY e.id DESC
        """, (self.admission_no, self.level))

        ranking = compute_student_scores(self.level)
        self.rank_info = next(
            (x for x in ranking if x["admission"] == self.admission_no),
            None
        )

    def stat_card(self, title, value):
        card = QFrame()
        card.setStyleSheet("""
        QFrame{
            background:#0f172a;
            border:1px solid #1e293b;
            border-radius:16px;
        }""")
        lay = QVBoxLayout(card)

        v = QLabel(str(value))
        v.setAlignment(Qt.AlignCenter)
        v.setStyleSheet("font-size:24px;font-weight:bold;color:#3b82f6;")

        t = QLabel(title)
        t.setAlignment(Qt.AlignCenter)
        t.setStyleSheet("color:#cbd5e1;")

        lay.addWidget(v)
        lay.addWidget(t)
        return card

    def build_ui(self):

        if not self.basic_info:
            self.content_layout.addWidget(QLabel("Student not found"))
            return

        adm, name, gender, cls, stream, level = self.basic_info

        header = QFrame()
        header.setStyleSheet("""
        QFrame{
            background:#0f172a;
            border:1px solid #1e293b;
            border-radius:20px;
        }""")

        h = QHBoxLayout(header)

        photo = QLabel("PHOTO")
        photo.setFixedSize(140,140)
        photo.setAlignment(Qt.AlignCenter)
        photo.setStyleSheet("""
        background:#17253c;
        border-radius:70px;
        font-weight:bold;
        """)

        h.addWidget(photo)

        info = QVBoxLayout()
        info.addWidget(QLabel(f"<h2>{name}</h2>"))
        info.addWidget(QLabel(f"Admission: {adm}"))
        info.addWidget(QLabel(f"Class: {cls} {stream or ''}"))
        info.addWidget(QLabel(f"Gender: {gender}"))
        info.addWidget(QLabel(f"Level: {level}"))

        h.addLayout(info)
        h.addStretch()

        self.content_layout.addWidget(header)

        summary = QHBoxLayout()

        if self.rank_info:
            summary.addWidget(self.stat_card("Average", self.rank_info.get("average", "-")))
            summary.addWidget(self.stat_card("Points", self.rank_info.get("points", "-")))
            summary.addWidget(self.stat_card("Division", self.rank_info.get("division", "-")))
            summary.addWidget(self.stat_card("Position", self.rank_info.get("position", "-")))
            summary.addWidget(self.stat_card("Status", self.rank_info.get("status", "-")))

        self.content_layout.addLayout(summary)

        group = QGroupBox("Results History")
        g = QVBoxLayout(group)

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(
            ["Subject", "Exam", "Marks", "Grade", "Points"]
        )
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        table.setRowCount(len(self.results))

        valid_marks = []

        for row, (subject, exam, marks) in enumerate(self.results):

            marks = 0 if marks is None else marks
            grade = get_grade(marks, level=self.level)
            points = get_points(grade, level=self.level)

            valid_marks.append((subject, marks, grade, points))

            table.setItem(row, 0, QTableWidgetItem(str(subject)))
            table.setItem(row, 1, QTableWidgetItem(str(exam)))
            table.setItem(row, 2, QTableWidgetItem(str(marks)))

            gi = QTableWidgetItem(grade)

            colors = {
                "A":"#22c55e",
                "B":"#06b6d4",
                "C":"#facc15",
                "D":"#fb923c",
                "E":"#a78bfa",
                "S":"#f97316",
                "F":"#ef4444"
            }

            gi.setForeground(QColor(colors.get(grade, "#ffffff")))
            table.setItem(row, 3, gi)
            table.setItem(row, 4, QTableWidgetItem(str(points)))

        g.addWidget(table)
        self.content_layout.addWidget(group)

        analysis = QGroupBox("Performance Analysis")
        ag = QGridLayout(analysis)

        if valid_marks:
            highest = max(valid_marks, key=lambda x: x[1])
            lowest = min(valid_marks, key=lambda x: x[1])

            ag.addWidget(QLabel("Highest Subject"), 0, 0)
            ag.addWidget(QLabel(f"{highest[0]} ({highest[1]}%)"), 0, 1)

            ag.addWidget(QLabel("Lowest Subject"), 1, 0)
            ag.addWidget(QLabel(f"{lowest[0]} ({lowest[1]}%)"), 1, 1)

        self.content_layout.addWidget(analysis)
