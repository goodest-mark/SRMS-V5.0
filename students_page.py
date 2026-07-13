from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QTextEdit,
    QScrollArea,
    QFrame,
    QSizePolicy,
    QStackedWidget,
)

import sqlite3

from class_utils import get_classes, get_level_for_class
from db_utils import get_cursor, fetch_all
from event_bus import EventBus
from system_state import SystemState
from security_settings import authorize_action
from progress_dialog import ProgressDialog


class StudentsPage(QWidget):

    def __init__(self):
        super().__init__()
        self._needs_refresh = False
        self.selected_id = None
        self.selected_admission_no = None
        self.reports_selected_admission = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        root.addWidget(self.scroll_area)

        self.content_widget = QWidget()
        self.scroll_area.setWidget(self.content_widget)

        main_layout = QVBoxLayout(self.content_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # =====================================================
        # TOP NAVIGATION BUTTONS (always visible)
        # =====================================================
        nav_layout = QHBoxLayout()
        self.btn_students = QPushButton("STUDENTS")
        self.btn_students.setObjectName("navButton")
        self.btn_registration = QPushButton("REGISTRATION")
        self.btn_registration.setObjectName("navButton")
        self.btn_reports = QPushButton("REPORTS")
        self.btn_reports.setObjectName("navButton")
        self.btn_students.setProperty("variant", "accent")
        self.btn_registration.setProperty("variant", "default")
        self.btn_reports.setProperty("variant", "default")

        self.btn_students.clicked.connect(lambda: self.switch_page(0))
        self.btn_registration.clicked.connect(lambda: self.switch_page(1))
        self.btn_reports.clicked.connect(lambda: self.switch_page(2))

        nav_layout.addWidget(self.btn_students)
        nav_layout.addWidget(self.btn_registration)
        nav_layout.addWidget(self.btn_reports)
        nav_layout.addStretch()

        main_layout.addLayout(nav_layout)

        # =====================================================
        # STACKED WIDGET (3 pages)
        # =====================================================
        self.stacked_widget = QStackedWidget()

        # ---- Page 0: Students (List) ----
        self.list_page = QWidget()
        list_layout = QVBoxLayout(self.list_page)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(12)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search student...")
        self.search.textChanged.connect(self.load_list)
        list_layout.addWidget(self.search)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID",
            "Admission No",
            "Exam No",
            "Full Name",
            "Gender",
            "Class",
            "Stream",
            "Level",
        ])
        self.table.setColumnHidden(0, True)   # ID
        self.table.setColumnHidden(7, True)   # Level

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self.on_student_double_clicked)

        header = self.table.horizontalHeader()
        for col in range(self.table.columnCount()):
            if col == 3:  # Full Name
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
            else:
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        list_layout.addWidget(self.table)
        self.stacked_widget.addWidget(self.list_page)

        # ---- Page 1: Registration ----
        self.register_page = QWidget()
        register_layout = QVBoxLayout(self.register_page)
        register_layout.setContentsMargins(0, 0, 0, 0)
        register_layout.setSpacing(12)

        # Form fields
        form_layout = QHBoxLayout()
        self.adm = QLineEdit()
        self.adm.setPlaceholderText("Admission No *")
        self.exam_no = QLineEdit()
        self.exam_no.setPlaceholderText("Exam No (Optional)")
        self.name = QLineEdit()
        self.name.setPlaceholderText("Full Name *")
        self.gender = QComboBox()
        self.gender.addItems(["Male", "Female"])
        self.class_box = QComboBox()
        self.class_box.setPlaceholderText("Select Class *")
        self.stream = QLineEdit()
        self.stream.setPlaceholderText("Stream (Optional)")

        form_layout.addWidget(self.adm)
        form_layout.addWidget(self.exam_no)
        form_layout.addWidget(self.name)
        form_layout.addWidget(self.gender)
        form_layout.addWidget(self.class_box)
        form_layout.addWidget(self.stream)
        register_layout.addLayout(form_layout)

        self.comment = QTextEdit()
        self.comment.setPlaceholderText("Comments / Remarks")
        self.comment.setFixedHeight(70)
        register_layout.addWidget(self.comment)

        # Action buttons
        action_layout = QHBoxLayout()
        self.save_btn = QPushButton("SAVE")
        self.save_btn.clicked.connect(self.save_student)
        self.delete_btn = QPushButton("DELETE")
        self.delete_btn.clicked.connect(self.delete_student)
        self.delete_btn.setEnabled(False)
        self.import_btn = QPushButton("IMPORT")
        self.import_btn.clicked.connect(self.import_excel)
        self.export_btn = QPushButton("EXPORT")
        self.export_btn.clicked.connect(self.export_excel)
        self.template_btn = QPushButton("TEMPLATE")
        self.template_btn.clicked.connect(self.download_template)

        action_layout.addWidget(self.save_btn)
        action_layout.addWidget(self.delete_btn)
        action_layout.addWidget(self.import_btn)
        action_layout.addWidget(self.export_btn)
        action_layout.addWidget(self.template_btn)
        action_layout.addStretch()
        register_layout.addLayout(action_layout)

        self.stacked_widget.addWidget(self.register_page)

        # ---- Page 2: Reports ----
        self.reports_page = QWidget()
        reports_page_layout = QVBoxLayout(self.reports_page)
        reports_page_layout.setContentsMargins(0, 0, 0, 0)
        reports_page_layout.setSpacing(12)

        # Search bar for finding a student
        self.reports_search = QLineEdit()
        self.reports_search.setPlaceholderText("Search student by Admission No, Name, or Class...")
        self.reports_search.textChanged.connect(self.load_reports_search)
        reports_page_layout.addWidget(self.reports_search)

        # Student selection table
        self.reports_student_table = QTableWidget()
        self.reports_student_table.setColumnCount(4)
        self.reports_student_table.setHorizontalHeaderLabels([
            "ID",
            "Admission No",
            "Full Name",
            "Class",
        ])
        self.reports_student_table.setColumnHidden(0, True)
        self.reports_student_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.reports_student_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.reports_student_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.reports_student_table.verticalHeader().setVisible(False)
        self.reports_student_table.setMaximumHeight(150)
        self.reports_student_table.itemSelectionChanged.connect(
            self.on_reports_student_selected
        )
        header = self.reports_student_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.reports_student_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.reports_student_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        reports_page_layout.addWidget(self.reports_student_table)

        # Reports table for the selected student
        reports_page_layout.addWidget(QLabel("Available Exam Reports:"))
        self.reports_table_page = QTableWidget()
        self.reports_table_page.setColumnCount(7)
        self.reports_table_page.setHorizontalHeaderLabels([
            "Exam ID",
            "Exam",
            "Term",
            "Year",
            "Status",
            "Subjects",
            "Average",
        ])
        self.reports_table_page.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.reports_table_page.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.reports_table_page.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.reports_table_page.verticalHeader().setVisible(False)
        self.reports_table_page.setMaximumHeight(170)
        self.reports_table_page.setColumnHidden(0, True)
        header = self.reports_table_page.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)
        self.reports_table_page.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.reports_table_page.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.reports_table_page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.reports_table_page.setMinimumHeight(120)
        self.reports_table_page.itemSelectionChanged.connect(
            self.update_reports_page_actions
        )
        self.reports_table_page.doubleClicked.connect(
            self.view_selected_exam_report_page
        )
        reports_page_layout.addWidget(self.reports_table_page)

        # Action buttons for reports page
        reports_actions = QHBoxLayout()
        self.view_report_page_btn = QPushButton("VIEW REPORT")
        self.download_report_page_btn = QPushButton("DOWNLOAD REPORT")
        self.view_report_page_btn.clicked.connect(self.view_selected_exam_report_page)
        self.download_report_page_btn.clicked.connect(self.download_selected_exam_report_page)
        self.view_report_page_btn.setEnabled(False)
        self.download_report_page_btn.setEnabled(False)

        reports_actions.addStretch()
        reports_actions.addWidget(self.view_report_page_btn)
        reports_actions.addWidget(self.download_report_page_btn)
        reports_page_layout.addLayout(reports_actions)

        self.stacked_widget.addWidget(self.reports_page)

        main_layout.addWidget(self.stacked_widget)

        # =====================================================
        # INITIALISE
        # =====================================================
        self.refresh_classes()
        self.load_list()
        self.switch_page(0)  # Start with Students page

        # Event bus subscriptions
        EventBus.subscribe("STUDENTS_UPDATED", self.on_students_updated)
        EventBus.subscribe("LEVEL_CHANGED", self.on_level_changed)

    # =====================================================
    # PAGE SWITCHING
    # =====================================================

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        # Update button styles
        for btn in (self.btn_students, self.btn_registration, self.btn_reports):
            btn.setProperty("variant", "default")
        if index == 0:
            self.btn_students.setProperty("variant", "accent")
        elif index == 1:
            self.btn_registration.setProperty("variant", "accent")
        else:
            self.btn_reports.setProperty("variant", "accent")
        # Force style refresh
        for btn in (self.btn_students, self.btn_registration, self.btn_reports):
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # =====================================================
    # EVENT HANDLERS
    # =====================================================

    def on_level_changed(self):
        if not self.isVisible():
            self._needs_refresh = True
            return
        self.clear_form()
        self.refresh_classes()
        self.load_list()

    def on_students_updated(self):
        self.load_list()
        self.load_reports_search()

    def showEvent(self, event):
        super().showEvent(event)
        if getattr(self, "_needs_refresh", False):
            self._needs_refresh = False
            self.on_level_changed()

    # =====================================================
    # PAGE 0: STUDENTS (LIST)
    # =====================================================

    def refresh_classes(self):
        current_class = self.class_box.currentText()
        classes = get_classes()
        self.class_box.clear()
        self.class_box.addItems(classes)
        index = self.class_box.findText(current_class)
        if index >= 0:
            self.class_box.setCurrentIndex(index)
        elif self.class_box.count() > 0:
            self.class_box.setCurrentIndex(0)

    def load_list(self):
        level = SystemState.get_level()
        search_text = self.search.text().strip()

        if search_text:
            pattern = f"%{search_text}%"
            rows = fetch_all("""
                SELECT id, admission_no, exam_no, full_name, gender, class, stream, level
                FROM students
                WHERE level=?
                  AND (
                      admission_no LIKE ?
                      OR COALESCE(exam_no, '') LIKE ?
                      OR full_name LIKE ?
                      OR class LIKE ?
                      OR COALESCE(stream, '') LIKE ?
                  )
                ORDER BY id DESC
            """, (level, pattern, pattern, pattern, pattern, pattern))
        else:
            rows = fetch_all("""
                SELECT id, admission_no, exam_no, full_name, gender, class, stream, level
                FROM students
                WHERE level=?
                ORDER BY id DESC
            """, (level,))

        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column, value in enumerate(row):
                text = "" if value is None else str(value)
                item = QTableWidgetItem(text)
                item.setToolTip(text)
                self.table.setItem(row_index, column, item)

    def on_student_double_clicked(self):
        row = self.table.currentRow()
        if row < 0:
            return
        # Load the selected student into the registration form and switch to registration page
        self.selected_id = int(self.table.item(row, 0).text())
        self.selected_admission_no = self.table.item(row, 1).text()
        self.adm.setText(self.selected_admission_no)
        self.exam_no.setText(self.table.item(row, 2).text())
        self.name.setText(self.table.item(row, 3).text())

        gender = self.table.item(row, 4).text()
        gender_index = self.gender.findText(gender)
        if gender_index >= 0:
            self.gender.setCurrentIndex(gender_index)

        class_name = self.table.item(row, 5).text()
        class_index = self.class_box.findText(class_name)
        if class_index >= 0:
            self.class_box.setCurrentIndex(class_index)

        self.stream.setText(self.table.item(row, 6).text())

        with get_cursor() as cur:
            cur.execute("SELECT comments FROM students WHERE id=?", (self.selected_id,))
            comments_row = cur.fetchone()
            self.comment.setText(comments_row[0] if comments_row and comments_row[0] else "")

        self.save_btn.setText("UPDATE")
        self.delete_btn.setEnabled(True)
        self.switch_page(1)  # Go to registration page

    # =====================================================
    # PAGE 1: REGISTRATION
    # =====================================================

    def save_student(self):
        admission_no = self.adm.text().strip()
        exam_no = self.exam_no.text().strip()
        full_name = self.name.text().strip()
        gender = self.gender.currentText().strip()
        class_name = self.class_box.currentText().strip()
        stream = self.stream.text().strip()
        level = SystemState.get_level()

        if not admission_no or not full_name or not class_name:
            QMessageBox.warning(
                self, "Required Fields",
                "Admission number, full name and class are required.",
            )
            return

        comment = self.comment.toPlainText().strip()
        try:
            with get_cursor(commit=True) as cur:
                if self.selected_id is None:
                    cur.execute("""
                        INSERT INTO students (admission_no, exam_no, full_name, gender, class, stream, level, comments)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (admission_no, exam_no, full_name, gender, class_name, stream, level, comment))
                else:
                    cur.execute("""
                        UPDATE students
                        SET admission_no=?, exam_no=?, full_name=?, gender=?, class=?, stream=?, level=?, comments=?
                        WHERE id=?
                    """, (admission_no, exam_no, full_name, gender, class_name, stream, level, comment, self.selected_id))

        except sqlite3.IntegrityError:
            QMessageBox.warning(
                self,
                "Duplicate Admission Number",
                "That admission number is already registered.",
            )
            return
        except Exception as e:
            QMessageBox.critical(
                self,
                "Database Error",
                f"An unexpected error occurred while saving the student record: {e}",
            )
            return

        self.clear_form()
        EventBus.emit("STUDENTS_UPDATED")

    def delete_student(self):
        if self.selected_id is None:
            QMessageBox.warning(
                self, "Delete Student",
                "Select a student before deleting.",
            )
            return

        answer = QMessageBox.question(
            self, "Delete Student",
            "Are you sure you want to delete this student?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        if not authorize_action(self, "Delete Student"):
            return

        try:
            with get_cursor(commit=True) as cur:
                cur.execute("DELETE FROM students WHERE id=?", (self.selected_id,))
        except Exception as e:
            QMessageBox.critical(
                self,
                "Database Error",
                f"An unexpected error occurred while deleting the student record: {e}",
            )
            return

        self.clear_form()
        EventBus.emit("STUDENTS_UPDATED")

    def clear_form(self):
        self.selected_id = None
        self.selected_admission_no = None

        self.adm.clear()
        self.exam_no.clear()
        self.name.clear()
        self.stream.clear()
        self.comment.clear()
        self.gender.setCurrentIndex(0)

        if self.class_box.count() > 0:
            self.class_box.setCurrentIndex(0)

        self.save_btn.setText("SAVE")
        self.delete_btn.setEnabled(False)
        self.switch_page(0)  # Return to list page after clearing

    # =====================================================
    # PAGE 2: REPORTS
    # =====================================================

    def load_reports_search(self):
        level = SystemState.get_level()
        search_text = self.reports_search.text().strip()

        if search_text:
            pattern = f"%{search_text}%"
            rows = fetch_all("""
                SELECT id, admission_no, full_name, class
                FROM students
                WHERE level=?
                  AND (
                      admission_no LIKE ?
                      OR full_name LIKE ?
                      OR class LIKE ?
                  )
                ORDER BY full_name
                LIMIT 20
            """, (level, pattern, pattern, pattern))
        else:
            rows = fetch_all("""
                SELECT id, admission_no, full_name, class
                FROM students
                WHERE level=?
                ORDER BY full_name
                LIMIT 20
            """, (level,))

        self.reports_student_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column, value in enumerate(row):
                text = "" if value is None else str(value)
                item = QTableWidgetItem(text)
                item.setToolTip(text)
                self.reports_student_table.setItem(row_index, column, item)

        if self.reports_student_table.rowCount() == 0:
            self.reports_table_page.setRowCount(0)
            self.view_report_page_btn.setEnabled(False)
            self.download_report_page_btn.setEnabled(False)
            self.reports_selected_admission = None

    def on_reports_student_selected(self):
        row = self.reports_student_table.currentRow()
        if row < 0:
            return
        admission_no = self.reports_student_table.item(row, 1).text()
        self.reports_selected_admission = admission_no
        self.load_reports_for_student(admission_no)

    def load_reports_for_student(self, admission_no):
        from report_card_v5 import list_student_report_exams
        level = SystemState.get_level()
        self.reports_table_page.setRowCount(0)
        self.view_report_page_btn.setEnabled(False)
        self.download_report_page_btn.setEnabled(False)

        if not admission_no:
            return

        rows = list_student_report_exams(admission_no, level)

        self.reports_table_page.setRowCount(len(rows))
        for row_index, report in enumerate(rows):
            values = (
                report["exam_id"],
                report["exam_name"],
                report["term_name"],
                report["year_name"],
                report["status"],
                report["subject_count"],
                report["average"],
            )
            for column, value in enumerate(values):
                text = "" if value is None else str(value)
                item = QTableWidgetItem(text)
                item.setToolTip(text)
                self.reports_table_page.setItem(row_index, column, item)

        self._update_table_height(self.reports_table_page)

        if rows:
            self.reports_table_page.selectRow(0)
        else:
            self.reports_table_page.setRowCount(0)

    def _update_table_height(self, table):
        table.resizeRowsToContents()
        height = (
            table.horizontalHeader().height()
            + table.verticalHeader().length()
            + table.frameWidth() * 2
            + 4
        )
        table.setFixedHeight(height)

    def current_report_exam_id_page(self):
        row = self.reports_table_page.currentRow()
        if row < 0:
            return None
        item = self.reports_table_page.item(row, 0)
        if item is None:
            return None
        try:
            return int(item.text())
        except ValueError:
            return None

    def update_reports_page_actions(self):
        has_report = self.current_report_exam_id_page() is not None
        self.view_report_page_btn.setEnabled(has_report)
        self.download_report_page_btn.setEnabled(has_report)

    def current_report_label_page(self):
        row = self.reports_table_page.currentRow()
        if row < 0:
            return "report"
        parts = []
        for column in (1, 2, 3):
            item = self.reports_table_page.item(row, column)
            if item and item.text().strip():
                parts.append(item.text().strip())
        label = "_".join(parts) or "report"
        return "".join(
            ch if ch.isalnum() or ch in ("_", "-") else "_"
            for ch in label
        )

    def view_selected_exam_report_page(self):
        exam_id = self.current_report_exam_id_page()
        if exam_id is None or not self.reports_selected_admission:
            return
        self.selected_admission_no = self.reports_selected_admission
        self.generate_report_for_exam(exam_id, open_after=True)

    def download_selected_exam_report_page(self):
        exam_id = self.current_report_exam_id_page()
        if exam_id is None or not self.reports_selected_admission:
            return

        safe_adm = "".join(
            ch if ch.isalnum() or ch in ("_", "-") else "_"
            for ch in self.reports_selected_admission
        )
        default_name = f"{safe_adm}_{self.current_report_label_page()}.pdf"
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Student Report",
            default_name,
            "PDF Files (*.pdf)",
        )
        if not save_path:
            return
        if not save_path.lower().endswith(".pdf"):
            save_path += ".pdf"
        self.selected_admission_no = self.reports_selected_admission
        self.generate_report_for_exam(exam_id, save_path=save_path, open_after=False)

    # =====================================================
    # SHARED REPORT GENERATION
    # =====================================================

    def generate_report_for_exam(self, exam_id, save_path=None, open_after=False):
        from report_card_v5 import generate_student_report_card
        if not self.selected_admission_no:
            return

        level = SystemState.get_level()

        self._report_progress = ProgressDialog("Generating Report Card")
        self._report_progress.show()
        success, result = generate_student_report_card(
            self,
            self.selected_admission_no,
            level,
            save_path=save_path,
            exam_id=exam_id,
            progress_callback=lambda percent, message: self._report_progress.update_progress(percent, 100, message),
        )
        self._report_progress.finish("Done")
        self._report_progress.close()
        self._report_progress = None

        if not success:
            QMessageBox.information(self, "Report Card", result)
            return

        if open_after:
            opened = QDesktopServices.openUrl(QUrl.fromLocalFile(result))
            if not opened:
                QMessageBox.warning(
                    self,
                    "Report Card",
                    f"Report generated at {result}, but the system viewer could not be opened.",
                )
        else:
            QMessageBox.information(
                self,
                "Report Card",
                f"Report saved to {result}",
            )

    # =====================================================
    # EXCEL FRAMEWORK (shared)
    # =====================================================

    def download_template(self):
        import excel_utils
        level = SystemState.get_level()
        excel_utils.download_template(
            self,
            "students_template.xlsx",
            "STUDENT REGISTRATION FORM",
            ["Admission No*", "Exam No", "Full Name*", "Gender*", "Class*", "Stream", "Level", "Comments"],
            instructions=[
                "1. Do not change the column headers in Row 10.",
                "2. Start student data entry from Row 12.",
                "3. Admission No is required for every student.",
                "4. Exam No is optional.",
                f"5. Use the current level: {level}.",
            ],
            samples=["2024/001", "EX/2024/001", "John Doe", "Male", "Form I", "A", SystemState.get_level(), "Good progress"]
        )

    def export_excel(self):
        import excel_utils
        level = SystemState.get_level()
        data = fetch_all("SELECT admission_no, exam_no, full_name, gender, class, stream, comments FROM students WHERE level=?", (level,))

        excel_utils.export_to_excel(
            self,
            f"students_{level}.xlsx",
            ["Admission No", "Exam No", "Full Name", "Gender", "Class", "Stream", "Comments"],
            data
        )

    def import_excel(self):
        import excel_utils
        import openpyxl
        path = excel_utils.get_import_file(self)
        if not path:
            return

        try:
            wb = openpyxl.load_workbook(path, data_only=True)
            sheet = wb.active
            rows = list(sheet.iter_rows(min_row=12, values_only=True))

            imported = 0
            updated = 0
            rejected = 0
            redirected = 0

            with get_cursor(commit=True) as cur:
                for row in rows:
                    if not row or not row[0]:
                        continue

                    if len(row) < 7:
                        rejected += 1
                        continue

                    adm = str(row[0]).strip()
                    if len(row) >= 8:
                        exam_no = str(row[1] or "").strip()
                        name = str(row[2] or "").strip()
                        gender = str(row[3] or "").strip()
                        cls = str(row[4] or "").strip()
                        stream = str(row[5] or "").strip()
                        level_excel = str(row[6] or "").strip().upper()
                        comment = str(row[7] or "").strip()
                    else:
                        exam_no = ""
                        name = str(row[1] or "").strip()
                        gender = str(row[2] or "").strip()
                        cls = str(row[3] or "").strip()
                        stream = str(row[4] or "").strip()
                        level_excel = str(row[5] or "").strip().upper()
                        comment = str(row[6] or "").strip()

                    if not name or not cls:
                        rejected += 1
                        continue

                    resolved_level = get_level_for_class(cls)
                    if resolved_level is None:
                        rejected += 1
                        continue
                    if level_excel and level_excel != resolved_level:
                        redirected += 1
                    level_excel = resolved_level

                    try:
                        cur.execute("SELECT 1 FROM students WHERE admission_no=?", (adm,))
                        exists = cur.fetchone()

                        cur.execute("""
                            INSERT INTO students (admission_no, exam_no, full_name, gender, class, stream, level, comments)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(admission_no) DO UPDATE SET
                                exam_no=excluded.exam_no,
                                full_name=excluded.full_name,
                                gender=excluded.gender,
                                class=excluded.class,
                                stream=excluded.stream,
                                level=excluded.level,
                                comments=excluded.comments
                        """, (adm, exam_no, name, gender, cls, stream, level_excel, comment))

                        if exists:
                            updated += 1
                        else:
                            imported += 1
                    except Exception as e:
                        print(f"[ERROR] Failed to import student '{adm}': {e}")
                        rejected += 1
                        continue

            self.load_list()
            self.load_reports_search()
            EventBus.emit("STUDENTS_UPDATED")
            QMessageBox.information(self, "Import Complete",
                                  f"Operation Summary:\n"
                                  f"- New Students Imported: {imported}\n"
                                  f"- Existing Records Updated: {updated}\n"
                                  f"- Rows Redirected to Actual Level: {redirected}\n"
                                  f"- Records Rejected (Invalid Data): {rejected}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed: {e}")
