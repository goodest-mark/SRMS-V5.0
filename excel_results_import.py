import openpyxl
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, 
    QLabel, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QApplication
)

from progress_dialog import ProgressDialog
from PySide6.QtCore import Qt

from database import connect
from db_utils import fetch_all, fetch_one, get_cursor, get_exam_context
from system_state import SystemState
from event_bus import EventBus
from class_utils import get_classes
from ui_helpers import show_error, show_info, confirm_action
import combo_loaders


class ExcelResultsImport(QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # =========================
        # HEADER
        # =========================
        title = QLabel("EXCEL RESULTS IMPORT")
        title.setProperty("variant", "accent")
        self.layout.addWidget(title)

        # =========================
        # FILTERS / SELECTION
        # =========================
        filter_layout = QHBoxLayout()

        self.exam_box = QComboBox()
        self.exam_box.setPlaceholderText("Select Exam")
        self.exam_box.setMinimumWidth(200)

        self.class_box = QComboBox()
        self.class_box.addItems(["-- Select Class --"] + get_classes())
        self.class_box.currentIndexChanged.connect(self.load_subjects)

        self.subject_box = QComboBox()
        self.subject_box.setPlaceholderText("Select Subject")
        self.subject_box.setMinimumWidth(200)

        filter_layout.addWidget(QLabel("Exam:"))
        filter_layout.addWidget(self.exam_box)
        filter_layout.addWidget(QLabel("Class:"))
        filter_layout.addWidget(self.class_box)
        filter_layout.addWidget(QLabel("Subject:"))
        filter_layout.addWidget(self.subject_box)
        filter_layout.addStretch()

        self.layout.addLayout(filter_layout)

        # =========================
        # FILE BROWSER AREA
        # =========================
        file_layout = QHBoxLayout()
        
        self.file_path_label = QLabel("No file selected...")
        self.file_path_label.setProperty("variant", "muted")
        
        self.browse_btn = QPushButton("BROWSE EXCEL")
        self.browse_btn.clicked.connect(self.browse_file)
        
        file_layout.addWidget(self.file_path_label, 1)
        file_layout.addWidget(self.browse_btn)
        
        self.layout.addLayout(file_layout)

        # =========================
        # PREVIEW / LOG TABLE
        # =========================
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(3)
        self.log_table.setHorizontalHeaderLabels(["Row", "Detail", "Status"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.log_table)

        # =========================
        # ACTION BUTTONS
        # =========================
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setFormat("%p%")
        self.progress.setVisible(False)
        self.layout.addWidget(self.progress)

        self.import_btn = QPushButton("PROCESS & SAVE IMPORT")
        self.import_btn.setFixedHeight(45)
        self.import_btn.setProperty("variant", "success")
        self.import_btn.clicked.connect(self.process_import)
        self.layout.addWidget(self.import_btn)

        # =========================
        # INITIAL LOAD
        # =========================
        self.selected_file = None
        EventBus.subscribe("LEVEL_CHANGED", self.refresh_all)
        self.refresh_all()

    def refresh_all(self):
        self.load_exams()
        self.class_box.setCurrentIndex(0)
        self.subject_box.clear()
        self.file_path_label.setText("No file selected...")
        self.selected_file = None
        self.log_table.setRowCount(0)

    def load_exams(self):
        combo_loaders.load_open_exams(self.exam_box)

    def load_subjects(self):
        self.subject_box.clear()
        class_name = self.class_box.currentText()
        if class_name == "-- Select Class --": return

        level = SystemState.get_level()
        for row in fetch_all("""
            SELECT DISTINCT e.subject_name 
            FROM enrollments e
            WHERE UPPER(TRIM(e.class_name)) = UPPER(TRIM(?))
            ORDER BY e.subject_name
        """, (class_name,)):
            self.subject_box.addItem(row[0])

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Excel File", "", "Excel Files (*.xlsx *.xls)")
        if file_path:
            self.selected_file = file_path
            self.file_path_label.setText(file_path)

    def add_log(self, row, detail, status):
        r = self.log_table.rowCount()
        self.log_table.insertRow(r)
        self.log_table.setItem(r, 0, QTableWidgetItem(str(row)))
        self.log_table.setItem(r, 1, QTableWidgetItem(detail))
        
        status_item = QTableWidgetItem(status)
        if status == "SUCCESS": status_item.setForeground(Qt.darkGreen)
        elif status == "SKIPPED": status_item.setForeground(Qt.darkYellow)
        else: status_item.setForeground(Qt.red)
        
        self.log_table.setItem(r, 2, status_item)
        self.log_table.scrollToBottom()

    def process_import(self):
        exam_id = self.exam_box.currentData()
        subject_name = self.subject_box.currentText()
        class_name = self.class_box.currentText()

        if not exam_id or not subject_name or class_name == "-- Select Class --" or not self.selected_file:
            show_error(self, "Please select Exam, Class, Subject and File first.")
            return

        if not confirm_action(self, "Confirm", "Start importing results? This will overwrite existing marks."):
            return

        if self._is_selected_exam_completed():
            show_error(
                self,
                "This exam is completed and read-only. Archived exams cannot accept new imports.",
                title="Completed Exam"
            )
            return

        self.log_table.setRowCount(0)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.progress.setFormat("Importing... %p%")
        self.import_btn.setEnabled(False)
        QApplication.processEvents()

        conn = None

        try:
            wb = openpyxl.load_workbook(self.selected_file, data_only=True, read_only=True)
            sheet = wb.active
            rows = list(sheet.iter_rows(min_row=12, values_only=True))
            total_rows = max(len(rows), 1)

            imported = 0
            skipped = 0
            errors = 0

            context = get_exam_context(exam_id)
            if not context:
                show_error(self, "Invalid Academic Context for selected Exam.")
                return

            year_id, term_id = context
            conn = connect()
            cur = conn.cursor()

            for idx, row in enumerate(rows, start=1):
                if idx == 1 or idx == len(rows) or idx % 10 == 0:
                    self.progress.setValue(int((idx / total_rows) * 100))
                    QApplication.processEvents()

                if not row or len(row) < 2:
                    self.add_log(idx, "Empty or incomplete row", "SKIPPED")
                    skipped += 1
                    continue

                adm_no = str(row[0]).strip() if row[0] is not None else ""
                marks_raw = row[1]

                if not adm_no or marks_raw is None:
                    self.add_log(idx, f"Missing data: {adm_no} / {marks_raw}", "SKIPPED")
                    skipped += 1
                    continue

                try:
                    marks = float(marks_raw)
                    if not (0 <= marks <= 100):
                        raise ValueError("Marks out of range (must be 0-100)")
                except (ValueError, TypeError) as error:
                    self.add_log(idx, f"Invalid Marks for {adm_no}: {marks_raw} ({error})", "ERROR")
                    errors += 1
                    continue

                cur.execute("""
                    SELECT 1 FROM enrollments
                    WHERE admission_no=?
                      AND subject_name=?
                      AND class_name=?
                      AND academic_year_id=?
                      AND term_id=?
                """, (adm_no, subject_name, class_name, year_id, term_id))

                if not cur.fetchone():
                    self.add_log(idx, f"{adm_no} not enrolled in {subject_name} this term.", "ERROR")
                    errors += 1
                    continue

                cur.execute("""
                    INSERT INTO results (admission_no, subject_name, marks, exam_id, class_name)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(admission_no, subject_name, exam_id)
                    DO UPDATE SET marks = excluded.marks,
                                  class_name = excluded.class_name
                """, (adm_no, subject_name, int(marks), exam_id, class_name))

                imported += 1

            conn.commit()
            self.progress.setValue(100)
            QApplication.processEvents()

            show_info(
                self,
                f"Summary:\nImported: {imported}\nSkipped: {skipped}\nErrors: {errors}",
                title="Import Complete"
            )
            EventBus.emit("RESULTS_UPDATED")

        except Exception as error:
            if conn:
                conn.rollback()
            print(f"[ERROR] Excel import failed: {error}")
            show_error(self, "An unexpected error occurred during import. Please verify the file format.", title="System Error")
        finally:
            if conn:
                conn.close()
            self.import_btn.setEnabled(True)
            self.progress.setVisible(False)

    def _is_selected_exam_completed(self):
        exam_id = self.exam_box.currentData()
        if exam_id is None:
            return False

        row = fetch_one("SELECT status FROM exams WHERE id=?", (exam_id,))
        return bool(row and row[0] == "COMPLETED")
