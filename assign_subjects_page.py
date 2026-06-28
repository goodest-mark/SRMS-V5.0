from PySide6.QtWidgets import (
QWidget,
QVBoxLayout,
QHBoxLayout,
QListWidget,
QPushButton,
QLabel
)

from db_utils import fetch_all, get_cursor

class AssignSubjectsPage(QWidget):
    def __init__(self):
        super().__init__()

        self.teacher_id = None

        root = QVBoxLayout(self)

        # =====================================
        # HEADER
        # =====================================

        header = QHBoxLayout()

        self.back_btn = QPushButton("← Back")

        title = QLabel("ASSIGN SUBJECTS")
        title.setStyleSheet(
            "font-size:18px;font-weight:bold;"
        )

        header.addWidget(self.back_btn)
        header.addStretch()
        header.addWidget(title)

        root.addLayout(header)

        # =====================================
        # BODY
        # =====================================

        body = QHBoxLayout()

        self.available_subjects = QListWidget()
        self.assigned_subjects = QListWidget()

        controls = QVBoxLayout()

        self.assign_btn = QPushButton(">")
        self.remove_btn = QPushButton("<")

        controls.addStretch()
        controls.addWidget(self.assign_btn)
        controls.addWidget(self.remove_btn)
        controls.addStretch()

        body.addWidget(self.available_subjects)
        body.addLayout(controls)
        body.addWidget(self.assigned_subjects)

        root.addLayout(body)

        self.assign_btn.clicked.connect(self.assign_subject)
        self.remove_btn.clicked.connect(self.remove_subject)

    def set_teacher(self, teacher_id):
        self.teacher_id = teacher_id
        self.load_data()

    def load_data(self):
        if not self.teacher_id:
            return

        self.available_subjects.clear()
        self.assigned_subjects.clear()

        all_subjects = [
            row[0]
            for row in fetch_all("""
                SELECT subject_name
                FROM subjects
                ORDER BY subject_name
            """)
        ]

        assigned = [
            row[0]
            for row in fetch_all("""
                SELECT subject_name
                FROM teacher_subjects
                WHERE teacher_id=?
            """, (self.teacher_id,))
        ]

        for subject in all_subjects:
            if subject in assigned:
                self.assigned_subjects.addItem(subject)
            else:
                self.available_subjects.addItem(subject)

    def assign_subject(self):
        item = self.available_subjects.currentItem()
        if not item:
            return

        subject = item.text()

        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT OR IGNORE INTO teacher_subjects(
                    teacher_id, subject_name
                ) VALUES (?,?)
            """, (self.teacher_id, subject))

        self.load_data()

    def remove_subject(self):
        item = self.assigned_subjects.currentItem()
        if not item:
            return

        subject = item.text()

        with get_cursor(commit=True) as cur:
            cur.execute("""
                DELETE FROM teacher_subjects
                WHERE teacher_id=? AND subject_name=?
            """, (self.teacher_id, subject))

        self.load_data()
