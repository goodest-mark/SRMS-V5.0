from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox
)

from db_utils import fetch_one, get_cursor
from event_bus import EventBus
from system_state import SystemState
from ui_helpers import show_error, show_info
from theme import APP_STYLE


class AddExamWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Create Examination")
        self.resize(500, 300)
        self.setStyleSheet(APP_STYLE)

        layout = QVBoxLayout()

        title = QLabel("Create Examination")

        exam_label = QLabel("Exam Name")

        self.exam_name = QLineEdit()
        self.exam_name.setPlaceholderText(
            "e.g Midterm"
        )

        save_btn = QPushButton(
            "SAVE EXAM"
        )

        save_btn.clicked.connect(
            self.save_exam
        )

        layout.addWidget(title)
        layout.addWidget(exam_label)
        layout.addWidget(self.exam_name)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def save_exam(self):

        exam_name = (
            self.exam_name.text()
            .strip()
        )

        if not exam_name:
            show_error(self, "Enter exam name")
            return

        row = fetch_one("""
            SELECT id
            FROM terms
            WHERE is_active=1
            LIMIT 1
        """)

        if not row:
            show_error(self, "No active term")
            return

        term_id = row[0]
        level = SystemState.get_level()

        try:
            with get_cursor(commit=True) as cur:
                cur.execute("""
                    UPDATE exams
                    SET status='CLOSED'
                    WHERE level=?
                      AND status='OPEN'
                """, (level,))

                cur.execute("""
                    INSERT INTO exams(
                        exam_name,
                        term_id,
                        level,
                        status
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    exam_name,
                    term_id,
                    level,
                    "OPEN"
                ))

            EventBus.emit("EXAMS_UPDATED")
            show_info(self, "Exam Saved Successfully")
            self.exam_name.clear()

        except Exception as e:
            show_error(self, str(e))
