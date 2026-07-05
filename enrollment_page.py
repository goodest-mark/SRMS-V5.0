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
    QFrame,
    QScrollArea,
    QSizePolicy,
    QCheckBox,
)

from progress_dialog import ProgressDialog
from PySide6.QtCore import Qt

from db_utils import get_cursor, fetch_all
from system_state import SystemState
from event_bus import EventBus
from class_utils import get_classes
from ui_helpers import show_error, show_info, get_subject_short_name
import combo_loaders


class EnrollmentPage(QWidget):

    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        root.addWidget(self.scroll_area)

        self.content_widget = QWidget()
        self.scroll_area.setWidget(self.content_widget)

        self.layout = QVBoxLayout(self.content_widget)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(12)

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

        filters_layout.addWidget(QLabel("Year:"))
        filters_layout.addWidget(self.year_box)
        filters_layout.addWidget(QLabel("Term:"))
        filters_layout.addWidget(self.term_box)
        filters_layout.addWidget(QLabel("Class:"))
        filters_layout.addWidget(self.class_box)
        
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
        # MODE / PREVIEW
        # =========================

        mode_layout = QHBoxLayout()
        self.enrollment_mode_checkbox = QCheckBox("Enrollment Mode")
        self.enrollment_mode_checkbox.setChecked(True)
        self.enrollment_mode_checkbox.toggled.connect(self.set_enrollment_mode)
        mode_layout.addWidget(self.enrollment_mode_checkbox)

        self.preview_label = QLabel("Preview mode: changes are disabled until Enrollment Mode is enabled.")
        self.preview_label.setWordWrap(True)
        self.preview_label.setProperty("variant", "muted")
        mode_layout.addWidget(self.preview_label, 1)
        mode_layout.addStretch()
        self.layout.addLayout(mode_layout)

        # =========================
        # TABLE AREA
        # =========================

        self.enrollment_table = QTableWidget()
        self.enrollment_table.setColumnCount(1)
        self.enrollment_table.setHorizontalHeaderLabels(["Student Name"])
        self.enrollment_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.enrollment_table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.enrollment_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.enrollment_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.enrollment_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.enrollment_table.setMinimumHeight(400)
        self.layout.addWidget(QLabel("DYNAMIC ENROLLMENT GRID"))
        self.layout.addWidget(self.enrollment_table)

        # =========================
        # SAVE BUTTON
        # =========================

        action_row = QHBoxLayout()
        action_row.addStretch()

        self.enroll_all_btn = QPushButton("ENROLL ALL")
        self.enroll_all_btn.setFixedHeight(40)
        self.enroll_all_btn.clicked.connect(self.enroll_all)

        self.save_btn = QPushButton("SAVE ENROLLMENTS")
        self.save_btn.setFixedHeight(40)
        self.save_btn.clicked.connect(self.save_enrollments)

        action_row.addWidget(self.enroll_all_btn)
        action_row.addWidget(self.save_btn)
        self.layout.addLayout(action_row)

        # =========================
        # INITIAL LOAD
        # =========================

        EventBus.subscribe("LEVEL_CHANGED", self.on_level_changed)
        
        self.load_years()
        self.set_enrollment_mode(True)

    # =========================
    # EVENT HANDLERS
    # =========================

    def on_level_changed(self):
        combo_loaders.load_classes(self.class_box, placeholder="-- Select Class --")
        self.clear_tables()

    def on_filter_changed(self):
        self.load_enrollment_data()

    def set_enrollment_mode(self, enabled):
        self.enrollment_mode_checkbox.setChecked(enabled)
        self.preview_label.setText(
            "Preview mode: changes are disabled until Enrollment Mode is enabled."
            if not enabled
            else "Enrollment mode is active. You can edit the student subject list."
        )

        self.save_btn.setEnabled(enabled)
        self.enrollment_table.setEnabled(enabled)

    # =========================
    # DATA LOADING
    # =========================

    def _update_table_heights(self):
        self.enrollment_table.resizeRowsToContents()
        height = (
            self.enrollment_table.horizontalHeader().height()
            + self.enrollment_table.verticalHeader().length()
            + self.enrollment_table.frameWidth() * 2
            + 4
        )
        self.enrollment_table.setFixedHeight(max(400, height))

    def load_years(self):
        combo_loaders.load_years(self.year_box)
        self.load_terms()

    def load_terms(self):
        combo_loaders.load_terms(self.term_box, self.year_box.currentData())

    def load_students(self):
        class_name = self.class_box.currentText()
        self.student_list = []
        self.subject_list = []

        if class_name and class_name != "-- Select Class --":
            self.student_list = [
                (row[0], row[1])
                for row in fetch_all(
                    """
                    SELECT admission_no, full_name
                    FROM students
                    WHERE class=? AND level=?
                    ORDER BY full_name
                    """,
                    (class_name, SystemState.get_level()),
                )
            ]

        self.load_enrollment_data()

    def load_enrollment_data(self):
        self.enrollment_table.clear()

        year_id = self.year_box.currentData()
        term_id = self.term_box.currentData()
        class_name = self.class_box.currentText()

        if not (year_id and term_id and class_name and class_name != "-- Select Class --"):
            self.enrollment_table.setRowCount(0)
            self.enrollment_table.setColumnCount(1)
            self.enrollment_table.setHorizontalHeaderLabels(["Student Name"])
            return

        self.subject_list = [
            row[0]
            for row in fetch_all(
                """
                SELECT subject_name
                FROM subjects
                WHERE level=?
                ORDER BY subject_name
                """,
                (SystemState.get_level(),),
            )
        ]

        enrollments = {
            (row[0], row[1])
            for row in fetch_all(
                """
                SELECT e.admission_no, e.subject_name
                FROM enrollments e
                JOIN students s ON s.admission_no = e.admission_no
                WHERE e.academic_year_id=? AND e.term_id=?
                  AND e.class_name=?
                  AND s.level=?
                """,
                (year_id, term_id, class_name, SystemState.get_level()),
            )
        }

        self.enrollment_table.setRowCount(len(self.student_list))
        self.enrollment_table.setColumnCount(len(self.subject_list) + 1)

        headers = ["Student"] + [get_subject_short_name(subject) for subject in self.subject_list]
        self.enrollment_table.setHorizontalHeaderLabels(headers)
        self.enrollment_table.verticalHeader().setVisible(False)

        for row_index, (admission_no, full_name) in enumerate(self.student_list):
            student_item = QTableWidgetItem(full_name)
            student_item.setFlags(student_item.flags() & ~Qt.ItemIsEditable)
            student_item.setData(Qt.UserRole, admission_no)
            student_item.setToolTip(admission_no)
            self.enrollment_table.setItem(row_index, 0, student_item)

            for col_index, subject_name in enumerate(self.subject_list, start=1):
                checkbox = QTableWidgetItem()
                checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                checkbox.setCheckState(
                    Qt.Checked if (admission_no, subject_name) in enrollments else Qt.Unchecked
                )
                checkbox.setData(Qt.UserRole, subject_name)
                self.enrollment_table.setItem(row_index, col_index, checkbox)

        self.enrollment_table.resizeColumnsToContents()
        self.enrollment_table.resizeRowsToContents()

    def clear_tables(self):
        self.enrollment_table.setRowCount(0)

    # =========================
    # SAVE
    # =========================

    def save_enrollments(self):
        year_id = self.year_box.currentData()
        term_id = self.term_box.currentData()
        class_name = self.class_box.currentText()

        if not (year_id and term_id and class_name and class_name != "-- Select Class --"):
            show_error(self, "Please select Year, Term, and Class before saving enrollments.")
            return

        enrolled_subjects = []
        for row_index, (admission_no, _) in enumerate(self.student_list):
            for col_index, subject_name in enumerate(self.subject_list, start=1):
                item = self.enrollment_table.item(row_index, col_index)
                if item is None:
                    continue
                if item.checkState() == Qt.Checked:
                    enrolled_subjects.append((admission_no, subject_name))

        admission_numbers = [student_id for student_id, _ in self.student_list]

        try:
            with get_cursor(commit=True) as cur:
                if admission_numbers:
                    placeholders = ",".join("?" for _ in admission_numbers)
                    cur.execute(f"""
                        DELETE FROM enrollments
                        WHERE academic_year_id=?
                          AND term_id=?
                          AND class_name=?
                          AND admission_no IN ({placeholders})
                    """, (year_id, term_id, class_name, *admission_numbers))

                for admission_no, subject_name in enrolled_subjects:
                    cur.execute("""
                        INSERT OR REPLACE INTO enrollments(admission_no, subject_name, class_name, academic_year_id, term_id)
                        VALUES (?, ?, ?, ?, ?)
                    """, (admission_no, subject_name, class_name, year_id, term_id))

            show_info(self, "Enrollments saved successfully.")

        except Exception:
            QMessageBox.critical(self, "Error", "An unexpected error occurred while saving enrollments.")

        self.load_enrollment_data()

    def enroll_all(self):
        year_id = self.year_box.currentData()
        term_id = self.term_box.currentData()
        class_name = self.class_box.currentText()

        if not (year_id and term_id and class_name and class_name != "-- Select Class --"):
            show_error(self, "Please select Year, Term, and Class before using Enroll All.")
            return

        if not self.student_list or not self.subject_list:
            show_error(self, "No students or subjects found for the selected class.")
            return

        for row_index in range(self.enrollment_table.rowCount()):
            for col_index in range(1, self.enrollment_table.columnCount()):
                item = self.enrollment_table.item(row_index, col_index)
                if item is not None:
                    item.setCheckState(Qt.Checked)

        self.save_enrollments()

    # =========================
    # EXCEL FRAMEWORK
    # =========================

    def download_template(self):
        import excel_utils
        year = self.year_box.currentText().strip() or "SELECTED YEAR"
        term = self.term_box.currentText().strip() or "SELECTED TERM"
        level = self.level_box.currentText().strip() or SystemState.get_level()
        excel_utils.download_template(
            self, 
            "enrollment_template.xlsx",
            f"STUDENT SUBJECT ENROLLMENT FORM - {year} {term}",
            ["Admission No*", "Subject Name*"],
            instructions=[
                f"1. Template generated for Year: {year}, Term: {term}, Level: {level}.",
                "2. Do not modify the column headers in Row 10.",
                "3. Start data entry from Row 12.",
                "4. Admission No must already exist in the system.",
                "5. Subject Name must match the learner's enrolled subject list.",
            ],
            samples=["2024/001", "Mathematics"]
        )

    def export_excel(self):
        import excel_utils
        year_id = self.year_box.currentData()
        term_id = self.term_box.currentData()
        if not (year_id and term_id):
            show_error(self, "Select Year and Term first")
            return
            
        data = fetch_all("""
            SELECT admission_no, subject_name
            FROM enrollments 
            WHERE academic_year_id=? AND term_id=? AND class_name=?
        """, (year_id, term_id, self.class_box.currentText()))
        
        excel_utils.export_to_excel(
            self, 
            "enrollments.xlsx", 
            ["Admission No", "Subject Name"],
            data
        )

    def import_excel(self):
        import excel_utils
        import openpyxl
        year_id = self.year_box.currentData()
        term_id = self.term_box.currentData()
        class_name = self.class_box.currentText()
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
                            INSERT OR REPLACE INTO enrollments (admission_no, subject_name, class_name, academic_year_id, term_id)
                            VALUES (?, ?, ?, ?, ?)
                        """, (adm, subject, class_name, year_id, term_id))
                        imported += 1
                    except Exception as e:
                        print(f"[ERROR] Failed to import enrollment for '{adm}' in '{subject}': {e}")
                        continue
            
            self.load_enrollment_data()
            show_info(self, f"Imported {imported} enrollment records.", title="Import Complete")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", "Import failed. Please check the file format and try again.")
