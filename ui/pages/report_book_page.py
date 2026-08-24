from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGroupBox, QFileDialog, QProgressBar
)
from PySide6.QtCore import QThread, Signal

from system_state import SystemState
from event_bus import EventBus
from ranking_engine import compute_student_scores
from ui_helpers import show_error, show_info, confirm_action
from db_utils import fetch_one
import report_card_v5 as report_book_pdf


class ReportBookWorker(QThread):
    finished = Signal(bool, str)
    progress = Signal(int, str)

    def __init__(self, exam_id, class_name, save_path, stream=None):
        super().__init__()
        self.exam_id = exam_id
        self.class_name = class_name
        self.save_path = save_path
        self.stream = stream

    def run(self):
        success, message = report_book_pdf.generate_report_book(
            None,
            self.exam_id,
            self.class_name,
            self.save_path,
            progress_callback=lambda percent, msg: self.progress.emit(percent, msg),
            stream=self.stream,
        )
        self.finished.emit(success, message)


class ReportBookPage(QWidget):
    def __init__(self):
        super().__init__()
        self.history_exam_id = None
        self.history_class_name = None
        self.history_level = None
        self.history_stream = None

        layout = QVBoxLayout(self)

        title = QLabel("STUDENT REPORT BOOK ENGINE")
        layout.addWidget(title)

        self.context_label = QLabel("")
        layout.addWidget(self.context_label)

        self.preview_group = QGroupBox("Class Summary Preview")
        preview_layout = QVBoxLayout(self.preview_group)
        self.summary_label = QLabel("Select criteria and click Preview...")
        preview_layout.addWidget(self.summary_label)
        layout.addWidget(self.preview_group)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        actions_layout = QHBoxLayout()
        self.preview_btn = QPushButton("PREVIEW SUMMARY")
        self.preview_btn.clicked.connect(self.update_summary)
        self.generate_btn = QPushButton("GENERATE PDF BOOK")
        self.generate_btn.clicked.connect(self.generate_pdf)
        actions_layout.addWidget(self.preview_btn)
        actions_layout.addWidget(self.generate_btn)
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        layout.addStretch()

        EventBus.subscribe("LEVEL_CHANGED", self.refresh_all)
        EventBus.subscribe("RESULTS_UPDATED", self.refresh_all)
        EventBus.subscribe("STUDENTS_UPDATED", self.refresh_all)
        EventBus.subscribe("SUBJECT_REQUIREMENTS_CHANGED", self.refresh_all)
        EventBus.subscribe("GRADE_RULES_CHANGED", self.refresh_all)
        EventBus.subscribe("DIVISION_RULES_CHANGED", self.refresh_all)

    def set_history_context(self, exam_id, class_name, level=None, stream=None):
        self.history_exam_id = exam_id
        self.history_class_name = class_name
        self.history_level = level or SystemState.get_level()
        self.history_stream = stream
        self.context_label.setText(f"{class_name} – Exam #{exam_id}" + (f" – {stream}" if stream else ""))
        self.update_summary()

    def clear_history_context(self):
        self.history_exam_id = None
        self.history_class_name = None
        self.history_level = None
        self.history_stream = None
        self.context_label.setText("")
        self.summary_label.setText("Select criteria and click Preview...")

    def update_summary(self, manual=False):
        exam_id = self.history_exam_id
        class_name = self.history_class_name
        level = self.history_level or SystemState.get_level()

        if not (exam_id and class_name):
            if manual:
                show_error(self, "Please select all context filters.")
            self.summary_label.setText("Select criteria and click Preview...")
            return

        ranking = compute_student_scores(level, exam_id, class_name, self.history_stream)
        class_students = [s for s in ranking if s.get('class') == class_name]
        total = len(class_students)
        ready = len([s for s in class_students if s.get('status') == "READY"])
        incomplete = total - ready

        summary_text = (
            f"<b>CLASS:</b> {class_name}" + (f" – {self.history_stream}" if self.history_stream else "") + f" ({level})<br>"
            f"<b>Total Students:</b> {total}<br>"
            f"<b>Ready:</b> {ready} | <b>Incomplete:</b> {incomplete}"
        )
        self.summary_label.setText(summary_text)

    def generate_pdf(self):
        exam_id = self.history_exam_id
        class_name = self.history_class_name

        if not (exam_id and class_name):
            show_error(self, "Please select all context filters.")
            return

        status_row = fetch_one("SELECT status FROM exams WHERE id=?", (exam_id,))
        exam_status = status_row[0] if status_row else None
        if exam_status and exam_status != "COMPLETED":
            if not confirm_action(self, "Non‑Completed Exam",
                                  f"This exam is {exam_status}. Continue anyway?"):
                return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Report Book",
            f"Class_Report_Book_{class_name}.pdf",
            "PDF Files (*.pdf)"
        )
        if not save_path:
            return

        self.preview_btn.setEnabled(False)
        self.generate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.worker = ReportBookWorker(exam_id, class_name, save_path, self.history_stream)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, percent, message):
        self.progress_bar.setValue(percent)
        self.status_label.setText(f"{message} ({percent}%)")

    def _on_finished(self, success, message):
        self.preview_btn.setEnabled(True)
        self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("")
        if success:
            show_info(self, message)
        else:
            show_error(self, message)

    def refresh_all(self):
        self.update_summary()
