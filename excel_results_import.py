import openpyxl
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, 
    QLabel, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar
)
from PySide6.QtCore import Qt

from database import connect
from system_state import SystemState
from event_bus import EventBus
from class_utils import get_classes


class ExcelResultsImport(QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # =========================
        # HEADER
        # =========================
        title = QLabel("EXCEL RESULTS IMPORT")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
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
        self.file_path_label.setStyleSheet("background: #f0f0f0; padding: 5px; border: 1px solid #ccc; color: #333;")
        
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
        self.progress.setVisible(False)
        self.layout.addWidget(self.progress)

        self.import_btn = QPushButton("PROCESS & SAVE IMPORT")
        self.import_btn.setFixedHeight(45)
        self.import_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
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
        self.exam_box.clear()
        level = SystemState.get_level()
        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT id, exam_name FROM exams WHERE level=? AND status='OPEN' ORDER BY id", (level,))
        for row in cur.fetchall():
            self.exam_box.addItem(row[1], row[0])
        conn.close()

    def load_subjects(self):
        self.subject_box.clear()
        class_name = self.class_box.currentText()
        if class_name == "-- Select Class --": return

        level = SystemState.get_level()
        conn = connect()
        cur = conn.cursor()
        
        # Load only subjects that have enrollments for this class
        cur.execute("""
            SELECT DISTINCT e.subject_name 
            FROM enrollments e
            JOIN students s ON s.admission_no = e.admission_no
            WHERE s.class=? AND s.level=?
            ORDER BY e.subject_name
        """, (class_name, level))
        
        for row in cur.fetchall():
            self.subject_box.addItem(row[0])
        conn.close()

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
            QMessageBox.warning(self, "Error", "Please select Exam, Class, Subject and File first.")
            return

        reply = QMessageBox.question(self, "Confirm", "Start importing results? This will overwrite existing marks.", 
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No: return

        self.log_table.setRowCount(0)
        self.progress.setVisible(True)
        self.progress.setValue(0)

        try:
            wb = openpyxl.load_workbook(self.selected_file, data_only=True)
            sheet = wb.active
            
            rows = list(sheet.iter_rows(min_row=12, values_only=True))
            total_rows = len(rows)
            
            imported = 0
            skipped = 0
            errors = 0

            # Derive Academic context from Exam
            conn = connect()
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT t.id, t.academic_year_id 
                    FROM exams e
                    JOIN terms t ON e.term_id = t.id
                    WHERE e.id = ?
                """, (exam_id,))
                term_res = cur.fetchone()
                if not term_res:
                    QMessageBox.critical(self, "Error", "Invalid Academic Context for selected Exam.")
                    return
                term_id, year_id = term_res

                for idx, row in enumerate(rows):
                    self.progress.setValue(int(((idx + 1) / total_rows) * 100))
                    
                    # Basic row check
                    if not row or len(row) < 2:
                        self.add_log(idx + 1, "Empty or incomplete row", "SKIPPED")
                        skipped += 1
                        continue

                    adm_no = str(row[0]).strip()
                    marks_raw = row[1]

                    if not adm_no or marks_raw is None:
                        self.add_log(idx + 1, f"Missing data: {adm_no} / {marks_raw}", "SKIPPED")
                        skipped += 1
                        continue

                    # Validate numeric marks
                    try:
                        marks = float(marks_raw)
                        if not (0 <= marks <= 100):
                            raise ValueError("Marks out of range (must be 0-100)")
                    except (ValueError, TypeError) as e:
                        self.add_log(idx + 1, f"Invalid Marks for {adm_no}: {marks_raw} ({e})", "ERROR")
                        errors += 1
                        continue

                    # Validate Student & Enrollment
                    cur.execute("""
                        SELECT 1 FROM enrollments 
                        WHERE admission_no=? AND subject_name=? AND academic_year_id=? AND term_id=?
                    """, (adm_no, subject_name, year_id, term_id))
                    
                    if not cur.fetchone():
                        self.add_log(idx + 1, f"{adm_no} not enrolled in {subject_name} this term.", "ERROR")
                        errors += 1
                        continue

                    # Save Results (Update or Insert)
                    cur.execute("""
                        INSERT INTO results (admission_no, subject_name, marks, exam_id)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(admission_no, subject_name, exam_id) 
                        DO UPDATE SET marks = excluded.marks
                    """, (adm_no, subject_name, int(marks), exam_id))
                    
                    imported += 1
                    # self.add_log(idx + 1, f"Imported {adm_no}", "SUCCESS") # Too much noise if table is big

                conn.commit()

                QMessageBox.information(self, "Import Complete", 
                                      f"Summary:\nImported: {imported}\nSkipped: {skipped}\nErrors: {errors}")
                
                EventBus.emit("RESULTS_UPDATED")
            finally:
                conn.close()

        except Exception as e:
            QMessageBox.critical(self, "System Error", f"An unexpected error occurred during import: {e}")
        finally:
            self.progress.setVisible(False)
