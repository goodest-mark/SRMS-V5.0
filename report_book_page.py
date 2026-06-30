from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
    QLabel, QGroupBox, QMessageBox, QFileDialog, QFrame
)

from progress_dialog import ProgressDialog
from PySide6.QtCore import Qt, QThread, Signal

from system_state import SystemState
from event_bus import EventBus
from class_utils import get_classes
from ranking_engine import compute_student_scores
from ui_helpers import show_error, show_info
import combo_loaders
import report_card_v5 as report_book_pdf


class ReportBookWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, exam_id, class_name, save_path):
        super().__init__()
        self.exam_id = exam_id
        self.class_name = class_name
        self.save_path = save_path

    def run(self):
        success, message = report_book_pdf.generate_report_book(None, self.exam_id, self.class_name, self.save_path)
        self.finished.emit(success, message)

class ReportBookPage(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        title = QLabel("STUDENT REPORT BOOK ENGINE")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        self.layout.addWidget(title)

        # =========================
        # FILTERS
        # =========================
        filters_group = QGroupBox("Select Class Context")
        filters_layout = QHBoxLayout(filters_group)

        self.year_box = QComboBox()
        self.year_box.currentIndexChanged.connect(self.load_terms)
        
        self.term_box = QComboBox()
        self.term_box.currentIndexChanged.connect(self.load_exams)

        self.exam_box = QComboBox()
        
        self.class_box = QComboBox()
        self.class_box.addItems(get_classes())

        filters_layout.addWidget(QLabel("Year:"))
        filters_layout.addWidget(self.year_box)
        filters_layout.addWidget(QLabel("Term:"))
        filters_layout.addWidget(self.term_box)
        filters_layout.addWidget(QLabel("Exam:"))
        filters_layout.addWidget(self.exam_box)
        filters_layout.addWidget(QLabel("Class:"))
        filters_layout.addWidget(self.class_box)
        filters_layout.addStretch()

        self.layout.addWidget(filters_group)

        # =========================
        # PREVIEW AREA
        # =========================
        self.preview_group = QGroupBox("Class Summary Preview")
        self.preview_layout = QVBoxLayout(self.preview_group)
        
        self.summary_label = QLabel("Select criteria and click Preview...")
        self.summary_label.setStyleSheet("font-size: 14px; line-height: 25px; color: #10b981;")
        self.preview_layout.addWidget(self.summary_label)
        
        self.layout.addWidget(self.preview_group)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 13px; color: #6b7280; margin-bottom: 10px;")
        self.layout.addWidget(self.status_label)

        # =========================
        # ACTIONS
        # =========================
        actions_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("PREVIEW SUMMARY")
        self.preview_btn.clicked.connect(self.update_summary)
        self.preview_btn.setFixedHeight(40)
        self.preview_btn.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold;")
        
        self.generate_btn = QPushButton("GENERATE PDF BOOK")
        self.generate_btn.clicked.connect(self.generate_pdf)
        self.generate_btn.setFixedHeight(40)
        self.generate_btn.setStyleSheet("background-color: #10b981; color: white; font-weight: bold;")

        actions_layout.addWidget(self.preview_btn)
        actions_layout.addWidget(self.generate_btn)
        actions_layout.addStretch()
        
        self.layout.addLayout(actions_layout)
        self.layout.addStretch()

        # Initial Load
        self.load_years()
        EventBus.subscribe("LEVEL_CHANGED", self.refresh_all)

    def refresh_all(self):
        self.load_years()
        combo_loaders.load_classes(self.class_box)

    def load_years(self):
        combo_loaders.load_years(self.year_box)
        self.load_terms()

    def load_terms(self):
        combo_loaders.load_terms(self.term_box, self.year_box.currentData())
        self.load_exams()

    def load_exams(self):
        combo_loaders.load_exams(self.exam_box, self.term_box.currentData())

    def update_summary(self):
        exam_id = self.exam_box.currentData()
        class_name = self.class_box.currentText()
        level = SystemState.get_level()

        if not (exam_id and class_name):
            show_error(self, "Please select all context filters.")
            return

        ranking = compute_student_scores(level, exam_id)
        
        # Filter for class in-memory (No N+1 database queries)
        class_students = [s for s in ranking if s.get('class') == class_name]

        total = len(class_students)
        ready = len([s for s in class_students if s['status'] == "READY"])
        incomplete = total - ready

        summary_text = (
            f"<b>CLASS:</b> {class_name} ({level})<br>"
            f"<b>EXAM:</b> {self.exam_box.currentText()}<br><br>"
            f"<b>Total Students:</b> {total}<br>"
            f"<b>Ready Students:</b> {ready}<br>"
            f"<b>Incomplete Students:</b> {incomplete}"
        )
        self.summary_label.setText(summary_text)

    def generate_pdf(self):
        exam_id = self.exam_box.currentData()
        class_name = self.class_box.currentText()
        
        if not (exam_id and class_name):
            show_error(self, "Please select all context filters.")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Save Report Book", f"Class_Report_Book_{class_name}.pdf", "PDF Files (*.pdf)")
        if not save_path:
            return

        self.preview_btn.setEnabled(False)
        self.generate_btn.setEnabled(False)
        self.status_label.setText("Generating report book. Please wait...")

        self.worker = ReportBookWorker(exam_id, class_name, save_path)
        self.worker.finished.connect(self.on_report_generated)
        self.worker.start()

    def on_report_generated(self, success, message):
        self.preview_btn.setEnabled(True)
        self.generate_btn.setEnabled(True)
        self.status_label.setText("")

        if success:
            show_info(self, message)
        else:
            show_error(self, message)
