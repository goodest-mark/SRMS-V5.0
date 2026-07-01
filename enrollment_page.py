from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QFrame
)

from progress_dialog import ProgressDialog
from PySide6.QtCore import Qt

import openpyxl
import excel_utils
from db_utils import get_cursor, fetch_all
from system_state import SystemState
from event_bus import EventBus
from class_utils import get_classes
from ui_helpers import show_error, show_info
import combo_loaders


class EnrollmentPage(QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # =========================
        # FILTERS
        # =========================

        filters_layout = QHBoxLayout()

        # Year
        self.year_box = QComboBox()
        self.year_box.currentIndexChanged.connect(self.load_terms)
        self.year_box.currentIndexChanged.connect(self.on_filter_changed)

        # Term
        self.term_box = QComboBox()
        self.term_box.currentIndexChanged.connect(self.on_filter_changed)

        # Class
        self.class_box = QComboBox()
        self.class_box.addItems(["-- Select Class --"] + get_classes())
        self.class_box.currentIndexChanged.connect(self.load_students)

        # Student
        self.student_box = QComboBox()
        self.student_box.currentIndexChanged.connect(self.load_enrollment_data)

        filters_layout.addWidget(QLabel("Year:"))
        filters_layout.addWidget(self.year_box)
        filters_layout.addWidget(QLabel("Term:"))
        filters_layout.addWidget(self.term_box)
        filters_layout.addWidget(QLabel("Class:"))
        filters_layout.addWidget(self.class_box)
        filters_layout.addWidget(QLabel("Student:"))
        filters_layout.addWidget(self.student_box)
        
        self.import_btn = QPushButton("IMPORT")
        self.import_btn.clicked.connect(self.import_excel)
        
        self.export_btn = QPushButton("EXPORT")
        self.export_btn.clicked.connect(self.export_excel)
        
        self.template_btn = QPushButton("TEMPLATE")
        self.template_btn.clicked.connect(self.download_template)
        
        filters_layout.addWidget(self.import_btn)
        filters_layout.addWidget(self.export_btn)
        filters_layout.addWidget(self.template_btn)
        
        filters_layout.addStretch()

        self.layout.addLayout(filters_layout)

        # =========================
        # TABLES AREA
        # =========================

        tables_layout = QHBoxLayout()

        # LEFT: Available
        left_vbox = QVBoxLayout()
        left_vbox.addWidget(QLabel("AVAILABLE SUBJECTS"))
        self.available_table = QTableWidget()
        self.available_table.setColumnCount(1)
        self.available_table.setHorizontalHeaderLabels(["Subject Name"])
        self.available_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.available_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.available_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        left_vbox.addWidget(self.available_table)
        tables_layout.addLayout(left_vbox, 2)

        # MIDDLE: Buttons
        btns_vbox = QVBoxLayout()
        btns_vbox.addStretch()
        
        self.enroll_one_btn = QPushButton(">")
        self.remove_one_btn = QPushButton("<")
        self.enroll_all_btn = QPushButton("Enroll All")
        self.remove_all_btn = QPushButton("Remove All")
        
        self.enroll_one_btn.clicked.connect(self.enroll_one)
        self.remove_one_btn.clicked.connect(self.remove_one)
        self.enroll_all_btn.clicked.connect(self.enroll_all)
        self.remove_all_btn.clicked.connect(self.remove_all)
        
        btns_vbox.addWidget(self.enroll_one_btn)
        btns_vbox.addWidget(self.remove_one_btn)
        btns_vbox.addSpacing(20)
        btns_vbox.addWidget(self.enroll_all_btn)
        btns_vbox.addWidget(self.remove_all_btn)
        
        btns_vbox.addStretch()
        tables_layout.addLayout(btns_vbox, 0)

        # RIGHT: Enrolled
        right_vbox = QVBoxLayout()
        right_vbox.addWidget(QLabel("ENROLLED SUBJECTS"))
        self.enrolled_table = QTableWidget()
        self.enrolled_table.setColumnCount(1)
        self.enrolled_table.setHorizontalHeaderLabels(["Subject Name"])
        self.enrolled_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.enrolled_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.enrolled_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        right_vbox.addWidget(self.enrolled_table)
        tables_layout.addLayout(right_vbox, 2)

        self.layout.addLayout(tables_layout)

        # =========================
        # SAVE BUTTON
        # =========================

        self.save_btn = QPushButton("SAVE ENROLLMENTS")
        self.save_btn.setFixedHeight(40)
        self.save_btn.clicked.connect(self.save_enrollments)
        self.layout.addWidget(self.save_btn)

        # =========================
        # INITIAL LOAD
        # =========================

        EventBus.subscribe("LEVEL_CHANGED", self.on_level_changed)
        
        self.load_years()

    # =========================
    # EVENT HANDLERS
    # =========================

    def on_level_changed(self):
        combo_loaders.load_classes(self.class_box, placeholder="-- Select Class --")
        self.student_box.clear()
        self.clear_tables()

    def on_filter_changed(self):
        self.load_enrollment_data()

    # =========================
    # DATA LOADING
    # =========================

    def load_years(self):
        combo_loaders.load_years(self.year_box)
        self.load_terms()

    def load_terms(self):
        combo_loaders.load_terms(self.term_box, self.year_box.currentData())

    def load_students(self):
        self.student_box.blockSignals(True)
        self.student_box.clear()
        class_name = self.class_box.currentText()
        
        if class_name and class_name != "-- Select Class --":
            rows = fetch_all("""
                SELECT admission_no, full_name 
                FROM students 
                WHERE class=? AND level=?
                ORDER BY full_name
            """, (class_name, SystemState.get_level()))
            
            for row in rows:
                self.student_box.addItem(f"{row[1]} ({row[0]})", row[0])
        
        self.student_box.blockSignals(False)
        self.load_enrollment_data()

    def load_enrollment_data(self):
        self.clear_tables()
        
        adm_no = self.student_box.currentData()
        year_id = self.year_box.currentData()
        term_id = self.term_box.currentData()
        
        if not (adm_no and year_id and term_id):
            return

        level = SystemState.get_level()
        
        enrolled = [r[0] for r in fetch_all("""
            SELECT subject_name 
            FROM enrollments 
            WHERE admission_no=? AND academic_year_id=? AND term_id=?
            ORDER BY subject_name
        """, (adm_no, year_id, term_id))]
        
        all_subjects = [r[0] for r in fetch_all("""
            SELECT subject_name 
            FROM subjects 
            WHERE level=?
            ORDER BY subject_name
        """, (level,))]
        
        available = [s for s in all_subjects if s not in enrolled]
        
        self.fill_table(self.available_table, available)
        self.fill_table(self.enrolled_table, enrolled)

    def fill_table(self, table, data):
        table.setRowCount(len(data))
        for i, name in enumerate(data):
            table.setItem(i, 0, QTableWidgetItem(name))

    def clear_tables(self):
        self.available_table.setRowCount(0)
        self.enrolled_table.setRowCount(0)

    # =========================
    # ACTIONS
    # =========================

    def enroll_one(self):
        row = self.available_table.currentRow()
        if row < 0: return
        
        subject = self.available_table.item(row, 0).text()
        self.available_table.removeRow(row)
        
        next_row = self.enrolled_table.rowCount()
        self.enrolled_table.insertRow(next_row)
        self.enrolled_table.setItem(next_row, 0, QTableWidgetItem(subject))

    def remove_one(self):
        row = self.enrolled_table.currentRow()
        if row < 0: return
        
        subject = self.enrolled_table.item(row, 0).text()
        self.enrolled_table.removeRow(row)
        
        next_row = self.available_table.rowCount()
        self.available_table.insertRow(next_row)
        self.available_table.setItem(next_row, 0, QTableWidgetItem(subject))

    def enroll_all(self):
        while self.available_table.rowCount() > 0:
            subject = self.available_table.item(0, 0).text()
            self.available_table.removeRow(0)
            
            next_row = self.enrolled_table.rowCount()
            self.enrolled_table.insertRow(next_row)
            self.enrolled_table.setItem(next_row, 0, QTableWidgetItem(subject))

    def remove_all(self):
        while self.enrolled_table.rowCount() > 0:
            subject = self.enrolled_table.item(0, 0).text()
            self.enrolled_table.removeRow(0)
            
            next_row = self.available_table.rowCount()
            self.available_table.insertRow(next_row)
            self.available_table.setItem(next_row, 0, QTableWidgetItem(subject))

    # =========================
    # SAVE
    # =========================

    def save_enrollments(self):
        adm_no = self.student_box.currentData()
        year_id = self.year_box.currentData()
        term_id = self.term_box.currentData()
        
        if not (adm_no and year_id and term_id):
            show_error(self, "Please select all filters correctly.")
            return

        enrolled_subjects = []
        for i in range(self.enrolled_table.rowCount()):
            enrolled_subjects.append(self.enrolled_table.item(i, 0).text())

        try:
            with get_cursor(commit=True) as cur:
                cur.execute("""
                    DELETE FROM enrollments 
                    WHERE admission_no=? AND academic_year_id=? AND term_id=?
                """, (adm_no, year_id, term_id))
                
                for sub in enrolled_subjects:
                    cur.execute("""
                        INSERT INTO enrollments(admission_no, subject_name, academic_year_id, term_id)
                        VALUES (?, ?, ?, ?)
                    """, (adm_no, sub, year_id, term_id))
            
            show_info(self, "Enrollments saved successfully.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", "An unexpected error occurred while saving enrollments.")
        
        self.load_enrollment_data()

    # =========================
    # EXCEL FRAMEWORK
    # =========================

    def download_template(self):
        excel_utils.download_template(
            self, 
            "enrollment_template.xlsx",
            "STUDENT SUBJECT ENROLLMENT FORM",
            ["Admission No*", "Subject Name*"],
            samples=["2024/001", "Mathematics"]
        )

    def export_excel(self):
        year_id = self.year_box.currentData()
        term_id = self.term_box.currentData()
        if not (year_id and term_id):
            show_error(self, "Select Year and Term first")
            return
            
        data = fetch_all("""
            SELECT admission_no, subject_name 
            FROM enrollments 
            WHERE academic_year_id=? AND term_id=?
        """, (year_id, term_id))
        
        excel_utils.export_to_excel(
            self, 
            "enrollments.xlsx", 
            ["Admission No", "Subject Name"],
            data
        )

    def import_excel(self):
        year_id = self.year_box.currentData()
        term_id = self.term_box.currentData()
        if not (year_id and term_id):
            show_error(self, "Select Year and Term first")
            return
            
        path = excel_utils.get_import_file(self)
        if not path: return
        
        try:
            wb = openpyxl.load_workbook(path, data_only=True)
            sheet = wb.active
            rows = list(sheet.iter_rows(min_row=12, values_only=True))
            
            imported = 0
            with get_cursor(commit=True) as cur:
                for row in rows:
                    if not row or len(row) < 2 or not row[0] or not row[1]: continue
                    
                    adm = str(row[0]).strip()
                    subject = str(row[1]).strip()
                    
                    try:
                        cur.execute("SELECT level FROM students WHERE admission_no=?", (adm,))
                        student_res = cur.fetchone()
                        if not student_res:
                            continue

                        student_level = student_res[0]

                        cur.execute("SELECT 1 FROM subjects WHERE subject_name=? AND level=?", (subject, student_level))
                        if not cur.fetchone():
                            continue

                        cur.execute("""
                            INSERT INTO enrollments (admission_no, subject_name, academic_year_id, term_id)
                            VALUES (?, ?, ?, ?)
                            ON CONFLICT(admission_no, subject_name, academic_year_id, term_id) DO NOTHING
                        """, (adm, subject, year_id, term_id))
                        imported += 1
                    except Exception as e:
                        print(f"[ERROR] Failed to import enrollment for '{adm}' in '{subject}': {e}")
                        continue
            
            self.load_enrollment_data()
            show_info(self, f"Imported {imported} enrollment records.", title="Import Complete")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", "Import failed. Please check the file format and try again.")
