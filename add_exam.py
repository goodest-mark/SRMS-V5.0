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
    QMessageBox,
    QComboBox,
)

from progress_dialog import ProgressDialog

from db_utils import fetch_one, get_cursor, fetch_all
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
        self.resize(550, 380)
        self.setStyleSheet(APP_STYLE)

        layout = QVBoxLayout()

        title = QLabel("Edit Examination" if self.is_edit_mode else "Create Examination")
        title.setProperty("variant", "accent")

        # ---- Year ----
        year_label = QLabel("Academic Year")
        self.year_box = QComboBox()

        # ---- Term ----
        term_label = QLabel("Term")
        self.term_box = QComboBox()

        # ---- Exam Name ----
        exam_label = QLabel("Exam Name")
        self.exam_name = QLineEdit()
        self.exam_name.setPlaceholderText("e.g Midterm")

        # ---- Holiday ----
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

        # ---- Save button ----
        save_btn = QPushButton("UPDATE EXAM" if self.is_edit_mode else "SAVE EXAM")
        save_btn.clicked.connect(self.save_exam)

        # ---- Layout ----
        layout.addWidget(title)
        layout.addWidget(year_label)
        layout.addWidget(self.year_box)
        layout.addWidget(term_label)
        layout.addWidget(self.term_box)
        layout.addWidget(exam_label)
        layout.addWidget(self.exam_name)
        layout.addWidget(self.has_holiday)
        layout.addWidget(self.holiday_frame)
        layout.addWidget(save_btn)

        self.setLayout(layout)

        # Load years and terms
        self.load_years()
        self.year_box.currentIndexChanged.connect(self.load_terms)

        # If editing, load exam data
        if self.is_edit_mode:
            self._load_exam()

    # ------------------------------------------------------------------
    # Load years & terms
    # ------------------------------------------------------------------
    def load_years(self):
        """Populate the year dropdown."""
        self.year_box.blockSignals(True)
        self.year_box.clear()
        for row in fetch_all("SELECT id, year_name FROM academic_years ORDER BY year_name DESC"):
            self.year_box.addItem(row[1], row[0])
        self.year_box.blockSignals(False)
        self.load_terms()

    def load_terms(self):
        """Populate the term dropdown based on selected year."""
        year_id = self.year_box.currentData()
        self.term_box.blockSignals(True)
        self.term_box.clear()
        if year_id:
            for row in fetch_all(
                "SELECT id, term_name FROM terms WHERE academic_year_id=? ORDER BY term_name",
                (year_id,)
            ):
                self.term_box.addItem(row[1], row[0])
        self.term_box.blockSignals(False)

    # ------------------------------------------------------------------
    # Holiday toggle
    # ------------------------------------------------------------------
    def _toggle_holiday_fields(self, checked):
        self.holiday_frame.setVisible(checked)
        if not checked:
            self.opening_date.clear()
            self.closing_date.clear()

    # ------------------------------------------------------------------
    # Load exam data (edit mode)
    # ------------------------------------------------------------------
    def _load_exam(self):
        row = fetch_one("""
            SELECT e.exam_name, e.it_has_holiday, e.opening_date, e.closing_date,
                   e.term_id, t.academic_year_id
            FROM exams e
            JOIN terms t ON t.id = e.term_id
            WHERE e.id = ?
        """, (self.exam_id,))
        if not row:
            show_error(self, "Selected exam was not found")
            return

        exam_name, has_holiday, opening_date, closing_date, term_id, year_id = row

        # Set exam name
        self.exam_name.setText(exam_name or "")

        # Set year and term
        year_idx = self.year_box.findData(year_id)
        if year_idx >= 0:
            self.year_box.setCurrentIndex(year_idx)
        self.load_terms()
        term_idx = self.term_box.findData(term_id)
        if term_idx >= 0:
            self.term_box.setCurrentIndex(term_idx)

        # Set holiday fields
        self.has_holiday.setChecked(bool(has_holiday))
        self.opening_date.setText(opening_date or "")
        self.closing_date.setText(closing_date or "")
        self.holiday_frame.setVisible(bool(has_holiday))

    # ------------------------------------------------------------------
    # Save exam
    # ------------------------------------------------------------------
    def save_exam(self):
        exam_name = self.exam_name.text().strip()
        if not exam_name:
            show_error(self, "Enter exam name")
            return

        term_id = self.term_box.currentData()
        if not term_id:
            show_error(self, "Please select a valid term.")
            return

        has_holiday = self.has_holiday.isChecked()
        opening_date = self.opening_date.text().strip()
        closing_date = self.closing_date.text().strip()

        if has_holiday and (not opening_date or not closing_date):
            show_error(self, "Enter both opening and closing dates for the holiday break")
            return

        try:
            with get_cursor(commit=True) as cur:
                if self.is_edit_mode:
                    # Update exam: name, term, holiday dates
                    cur.execute("""
                        UPDATE exams
                        SET exam_name=?,
                            term_id=?,
                            it_has_holiday=?,
                            opening_date=?,
                            closing_date=?
                        WHERE id=?
                    """, (
                        exam_name,
                        term_id,
                        1 if has_holiday else 0,
                        opening_date if has_holiday else "",
                        closing_date if has_holiday else "",
                        self.exam_id,
                    ))
                else:
                    # Create new exam: use active term or selected term
                    level = SystemState.get_level()

                    # Close any other open exam for this level
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
            self.close()

        except Exception as e:
            show_error(self, str(e))
