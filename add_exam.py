from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QCheckBox,
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox
)

from progress_dialog import ProgressDialog

from db_utils import fetch_one, get_cursor
from event_bus import EventBus
from system_state import SystemState
from ui_helpers import show_error, show_info
from theme import APP_STYLE


class AddExamWindow(QWidget):

    def __init__(self, exam_id=None):
        super().__init__()

        self.exam_id = exam_id
        self.is_edit_mode = exam_id is not None

        self.setWindowTitle("Edit Examination" if self.is_edit_mode else "Create Examination")
        self.resize(500, 300)
        self.setStyleSheet(APP_STYLE)

        layout = QVBoxLayout()

        title = QLabel("Edit Examination" if self.is_edit_mode else "Create Examination")

        exam_label = QLabel("Exam Name")

        self.exam_name = QLineEdit()
        self.exam_name.setPlaceholderText(
            "e.g Midterm"
        )

        self.has_holiday = QCheckBox("This exam includes a holiday break")
        self.has_holiday.toggled.connect(self._toggle_holiday_fields)

        self.holiday_frame = QFrame()
        holiday_form = QFormLayout(self.holiday_frame)
        self.opening_date = QLineEdit()
        self.opening_date.setPlaceholderText("YYYY-MM-DD")
        self.closing_date = QLineEdit()
        self.closing_date.setPlaceholderText("YYYY-MM-DD")
        holiday_form.addRow("Opening Date", self.opening_date)
        holiday_form.addRow("Closing Date", self.closing_date)
        self.holiday_frame.setVisible(False)

        save_btn = QPushButton("UPDATE EXAM" if self.is_edit_mode else "SAVE EXAM")

        save_btn.clicked.connect(
            self.save_exam
        )

        layout.addWidget(title)
        layout.addWidget(exam_label)
        layout.addWidget(self.exam_name)
        layout.addWidget(self.has_holiday)
        layout.addWidget(self.holiday_frame)
        layout.addWidget(save_btn)

        self.setLayout(layout)

        if self.is_edit_mode:
            self._load_exam()

    def _toggle_holiday_fields(self, checked):
        self.holiday_frame.setVisible(checked)
        if not checked:
            self.opening_date.clear()
            self.closing_date.clear()

    def _load_exam(self):
        row = fetch_one(
            """
            SELECT exam_name, it_has_holiday, opening_date, closing_date
            FROM exams
            WHERE id=?
            """,
            (self.exam_id,),
        )
        if not row:
            show_error(self, "Selected exam was not found")
            return

        self.exam_name.setText(row[0] or "")
        has_holiday = bool(row[1])
        self.has_holiday.setChecked(has_holiday)
        self.opening_date.setText(row[2] or "")
        self.closing_date.setText(row[3] or "")
        self.holiday_frame.setVisible(has_holiday)

    def save_exam(self):

        exam_name = (
            self.exam_name.text()
            .strip()
        )

        if not exam_name:
            show_error(self, "Enter exam name")
            return

        has_holiday = self.has_holiday.isChecked()
        opening_date = self.opening_date.text().strip()
        closing_date = self.closing_date.text().strip()

        if has_holiday and (not opening_date or not closing_date):
            show_error(self, "Enter both opening and closing dates for the holiday break")
            return

        if not self.is_edit_mode:
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
        else:
            row = fetch_one("""
                SELECT term_id, level, status
                FROM exams
                WHERE id=?
            """, (self.exam_id,))
            if not row:
                show_error(self, "Selected exam was not found")
                return
            term_id, level, _current_status = row

        try:
            with get_cursor(commit=True) as cur:
                if self.is_edit_mode:
                    cur.execute("""
                        UPDATE exams
                        SET exam_name=?,
                            it_has_holiday=?,
                            opening_date=?,
                            closing_date=?
                        WHERE id=?
                    """, (
                        exam_name,
                        1 if has_holiday else 0,
                        opening_date if has_holiday else "",
                        closing_date if has_holiday else "",
                        self.exam_id,
                    ))
                else:
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
                            it_has_holiday,
                            opening_date,
                            closing_date,
                            status
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        exam_name,
                        term_id,
                        level,
                        1 if has_holiday else 0,
                        opening_date if has_holiday else "",
                        closing_date if has_holiday else "",
                        "OPEN"
                    ))

            EventBus.emit("EXAMS_UPDATED")
            show_info(self, "Exam Updated Successfully" if self.is_edit_mode else "Exam Saved Successfully")
            self.exam_name.clear()

        except Exception as e:
            show_error(self, str(e))
