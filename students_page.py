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
from db_utils import get_cursor, fetch_all, fetch_one
from event_bus import EventBus
from system_state import SystemState
from security_settings import authorize_action
from progress_dialog import ProgressDialog
from grade_utils import get_grade, get_points
from ranking_engine import compute_student_scores
from remarks_utils import get_default_remark, get_headteacher_remark, get_academic_master_remark, get_discipline_master_remark


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
        # TOP NAVIGATION BUTTONS
        # =====================================================
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(0, 0, 0, 12)

        nav_container = QFrame()
        nav_container.setObjectName("studentsNavContainer")
        nav_container_layout = QHBoxLayout(nav_container)
        nav_container_layout.setContentsMargins(4, 4, 4, 4)
        nav_container_layout.setSpacing(4)

        self.btn_students = QPushButton("STUDENTS")
        self.btn_students.setObjectName("navButton")
        self.btn_registration = QPushButton("REGISTRATION")
        self.btn_registration.setObjectName("navButton")
        self.btn_reports = QPushButton("REPORTS")
        self.btn_reports.setObjectName("navButton")
        for btn in (self.btn_students, self.btn_registration, self.btn_reports):
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(38)
            btn.setMinimumWidth(130)
            nav_container_layout.addWidget(btn)
        self.btn_students.setProperty("variant", "accent")
        self.btn_registration.setProperty("variant", "default")
        self.btn_reports.setProperty("variant", "default")

        nav_container.setStyleSheet("""
            QFrame#studentsNavContainer {
                background-color: #EEF1F6;
                border-radius: 12px;
            }
            QFrame#studentsNavContainer QPushButton#navButton {
                background-color: transparent;
                border: none;
                border-radius: 9px;
                padding: 8px 18px;
                font-weight: 600;
                font-size: 12px;
                color: #5B6472;
            }
            QFrame#studentsNavContainer QPushButton#navButton:hover {
                background-color: #E0E4EC;
                color: #1E293B;
            }
            QFrame#studentsNavContainer QPushButton#navButton[variant="accent"] {
                background-color: #1E3A8A;
                color: #FFFFFF;
            }
            QFrame#studentsNavContainer QPushButton#navButton[variant="accent"]:hover {
                background-color: #1E3A8A;
            }
        """)

        self.btn_students.clicked.connect(lambda: self.switch_page(0))
        self.btn_registration.clicked.connect(lambda: self.switch_page(1))
        self.btn_reports.clicked.connect(lambda: self.switch_page(2))

        nav_layout.addWidget(nav_container)
        nav_layout.addStretch()

        main_layout.addLayout(nav_layout)

        # =====================================================
        # STACKED WIDGET
        # =====================================================
        self.stacked_widget = QStackedWidget()

        # ---- Page 0: Students (List) ----
        self.list_page = QWidget()
        list_layout = QVBoxLayout(self.list_page)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(12)

        list_top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search student...")
        self.search.textChanged.connect(self.load_list)
        list_top.addWidget(self.search)

        self.delete_selected_btn = QPushButton("Delete Selected")
        self.delete_selected_btn.setObjectName("workflowDanger")
        self.delete_selected_btn.clicked.connect(self.delete_selected_students)
        self.delete_selected_btn.setEnabled(False)
        list_top.addWidget(self.delete_selected_btn)
        list_layout.addLayout(list_top)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Admission No", "Exam No", "Full Name",
            "Gender", "Class", "Stream", "Level"
        ])
        self.table.setColumnHidden(0, True)   # ID
        self.table.setColumnHidden(7, True)   # Level

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self.on_student_double_clicked)
        self.table.itemSelectionChanged.connect(self.update_delete_selected_button)

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

        action_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Student")
        self.save_btn.setObjectName("workflowPrimary")
        self.save_btn.clicked.connect(self.save_student)
        self.delete_btn = QPushButton("Delete Student")
        self.delete_btn.setObjectName("workflowDanger")
        self.delete_btn.clicked.connect(self.delete_student)
        self.delete_btn.setEnabled(False)
        self.import_btn = QPushButton("Import Excel")
        self.import_btn.setObjectName("workflowSecondary")
        self.import_btn.clicked.connect(self.import_excel)
        self.export_btn = QPushButton("Export Excel")
        self.export_btn.setObjectName("workflowSecondary")
        self.export_btn.clicked.connect(self.export_excel)
        self.template_btn = QPushButton("Download Template")
        self.template_btn.setObjectName("workflowSecondary")
        self.template_btn.clicked.connect(self.download_template)

        action_layout.addWidget(self.template_btn)
        action_layout.addWidget(self.import_btn)
        action_layout.addWidget(self.export_btn)
        action_layout.addWidget(self.save_btn)
        action_layout.addWidget(self.delete_btn)
        action_layout.addStretch()
        register_layout.addLayout(action_layout)

        self.stacked_widget.addWidget(self.register_page)

        # ---- Page 2: Reports ----
        self.reports_page = QWidget()
        reports_page_layout = QVBoxLayout(self.reports_page)
        reports_page_layout.setContentsMargins(0, 0, 0, 0)
        reports_page_layout.setSpacing(16)

        # Search
        search_label = QLabel("Find a Student")
        search_label.setProperty("variant", "accent")
        search_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        reports_page_layout.addWidget(search_label)

        self.reports_search = QLineEdit()
        self.reports_search.setPlaceholderText("Search by Admission No, Name, or Class...")
        self.reports_search.textChanged.connect(self.load_reports_search)
        reports_page_layout.addWidget(self.reports_search)

        # Student selection table
        student_list_label = QLabel("Select a Student")
        student_list_label.setProperty("variant", "accent")
        student_list_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        reports_page_layout.addWidget(student_list_label)

        self.reports_student_table = QTableWidget()
        self.reports_student_table.setColumnCount(4)
        self.reports_student_table.setHorizontalHeaderLabels(["ID", "Admission No", "Full Name", "Class"])
        self.reports_student_table.setColumnHidden(0, True)
        self.reports_student_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.reports_student_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.reports_student_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.reports_student_table.verticalHeader().setVisible(False)
        self.reports_student_table.itemSelectionChanged.connect(self.on_reports_student_selected)
        header = self.reports_student_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.reports_student_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.reports_student_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.reports_student_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        reports_page_layout.addWidget(self.reports_student_table)

        # Reports list
        reports_list_label = QLabel("Available Exam Reports")
        reports_list_label.setProperty("variant", "accent")
        reports_list_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        reports_page_layout.addWidget(reports_list_label)

        self.reports_table_page = QTableWidget()
        self.reports_table_page.setColumnCount(7)
        self.reports_table_page.setHorizontalHeaderLabels([
            "Exam ID", "Exam", "Term", "Year", "Status", "Subjects", "Average"
        ])
        self.reports_table_page.setColumnHidden(0, True)
        self.reports_table_page.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.reports_table_page.setSelectionMode(QAbstractItemView.SingleSelection)
        self.reports_table_page.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.reports_table_page.verticalHeader().setVisible(False)
        self.reports_table_page.itemSelectionChanged.connect(self.update_reports_page_actions)
        self.reports_table_page.doubleClicked.connect(self.view_selected_exam_report_page)
        header = self.reports_table_page.horizontalHeader()
        for col in range(1, 7):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)
        self.reports_table_page.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.reports_table_page.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.reports_table_page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        reports_page_layout.addWidget(self.reports_table_page)

        # Action buttons
        reports_actions = QHBoxLayout()
        self.view_report_page_btn = QPushButton("View Report")
        self.view_report_page_btn.setObjectName("workflowPrimary")
        self.download_report_page_btn = QPushButton("Download Report")
        self.download_report_page_btn.setObjectName("workflowSecondary")
        self.preview_marks_btn = QPushButton("Preview Marks")
        self.preview_marks_btn.setObjectName("workflowSecondary")
        self.view_report_page_btn.clicked.connect(self.view_selected_exam_report_page)
        self.download_report_page_btn.clicked.connect(self.download_selected_exam_report_page)
        self.preview_marks_btn.clicked.connect(self.preview_selected_exam_marks)
        self.view_report_page_btn.setEnabled(False)
        self.download_report_page_btn.setEnabled(False)
        self.preview_marks_btn.setEnabled(False)

        reports_actions.addStretch()
        reports_actions.addWidget(self.view_report_page_btn)
        reports_actions.addWidget(self.download_report_page_btn)
        reports_actions.addWidget(self.preview_marks_btn)
        reports_page_layout.addLayout(reports_actions)

        # Preview frame (hidden by default)
        self.preview_frame = QFrame()
        self.preview_frame.setObjectName("PreviewCard")
        self.preview_frame.setStyleSheet("""
            QFrame#PreviewCard {
                background: rgba(0,0,0,0.03);
                border: 1px solid rgba(148,163,184,0.2);
                border-radius: 10px;
                padding: 10px;
            }
        """)
        self.preview_layout = QVBoxLayout(self.preview_frame)
        self.preview_layout.setContentsMargins(12, 12, 12, 12)
        self.preview_layout.setSpacing(10)

        self.preview_frame.setVisible(False)
        reports_page_layout.addWidget(self.preview_frame)

        reports_page_layout.addStretch()

        self.stacked_widget.addWidget(self.reports_page)

        main_layout.addWidget(self.stacked_widget)

        # =====================================================
        # INITIALISE
        # =====================================================
        self.refresh_classes()
        self.load_list()
        self.switch_page(0)

        EventBus.subscribe("STUDENTS_UPDATED", self.on_students_updated)
        EventBus.subscribe("LEVEL_CHANGED", self.on_level_changed)

    # =====================================================
    # PAGE SWITCHING
    # =====================================================

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        for btn in (self.btn_students, self.btn_registration, self.btn_reports):
            btn.setProperty("variant", "default")
            btn.setChecked(False)
        if index == 0:
            self.btn_students.setProperty("variant", "accent")
            self.btn_students.setChecked(True)
        elif index == 1:
            self.btn_registration.setProperty("variant", "accent")
            self.btn_registration.setChecked(True)
        else:
            self.btn_reports.setProperty("variant", "accent")
            self.btn_reports.setChecked(True)
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
        self.class_box.addItems(["-- Select Class --"] + classes)
        index = self.class_box.findText(current_class)
        if index > 0:
            self.class_box.setCurrentIndex(index)
        else:
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
                  AND class<>?
                  AND (
                      admission_no LIKE ? OR COALESCE(exam_no, '') LIKE ?
                      OR full_name LIKE ? OR class LIKE ? OR COALESCE(stream, '') LIKE ?
                  )
                ORDER BY id DESC
            """, (level, "Graduated", pattern, pattern, pattern, pattern, pattern))
        else:
            rows = fetch_all("""
                SELECT id, admission_no, exam_no, full_name, gender, class, stream, level
                FROM students
                WHERE level=? AND class<>?
                ORDER BY id DESC
            """, (level, "Graduated"))
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column, value in enumerate(row):
                text = "" if value is None else str(value)
                item = QTableWidgetItem(text)
                item.setToolTip(text)
                self.table.setItem(row_index, column, item)
        self.update_delete_selected_button()

    def on_student_double_clicked(self):
        row = self.table.currentRow()
        if row < 0:
            return
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

        self.save_btn.setText("Update Student")
        self.delete_btn.setEnabled(True)
        self.switch_page(1)

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

        if not admission_no or not full_name or not class_name or class_name == "-- Select Class --":
            QMessageBox.warning(self, "Required Fields", "Admission number, full name and class are required.")
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
            QMessageBox.warning(self, "Duplicate Admission Number", "That admission number is already registered.")
            return
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An unexpected error occurred while saving the student record: {e}")
            return

        self.clear_form()
        EventBus.emit("STUDENTS_UPDATED")

    def delete_student(self):
        if self.selected_id is None:
            QMessageBox.warning(self, "Delete Student", "Select a student before deleting.")
            return
        student_name = self.name.text().strip() or "this student"
        answer = QMessageBox.question(self, "Delete Student", f"Are you sure you want to delete '{student_name}'?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        if not authorize_action(self, "Delete Student"):
            return
        try:
            with get_cursor(commit=True) as cur:
                cur.execute("DELETE FROM students WHERE id=?", (self.selected_id,))
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An unexpected error occurred while deleting the student record: {e}")
            return
        self.clear_form()
        EventBus.emit("STUDENTS_UPDATED")

    def update_delete_selected_button(self):
        count = len(self.table.selectionModel().selectedRows())
        self.delete_selected_btn.setEnabled(count > 0)
        self.delete_selected_btn.setText(f"Delete Selected ({count})" if count > 0 else "Delete Selected")

    def delete_selected_students(self):
        selected_rows = sorted(set(idx.row() for idx in self.table.selectionModel().selectedRows()))
        if not selected_rows:
            QMessageBox.warning(self, "Delete Students", "Select at least one student to delete.")
            return

        students = []
        for row in selected_rows:
            id_item = self.table.item(row, 0)
            name_item = self.table.item(row, 3)
            if id_item is None:
                continue
            try:
                sid = int(id_item.text())
            except ValueError:
                continue
            students.append((sid, name_item.text() if name_item else "(unnamed)"))
        if not students:
            return

        count = len(students)
        if count == 1:
            message = f"Are you sure you want to delete '{students[0][1]}'?"
        else:
            preview = ", ".join(name for _, name in students[:5])
            if count > 5:
                preview += f", and {count - 5} more"
            message = f"Are you sure you want to delete {count} students?\n\n{preview}"
        answer = QMessageBox.question(self, "Delete Students", message, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        if not authorize_action(self, "Delete Student" if count == 1 else f"Delete {count} Students"):
            return

        ids = [sid for sid, _ in students]
        try:
            with get_cursor(commit=True) as cur:
                cur.executemany("DELETE FROM students WHERE id=?", [(sid,) for sid in ids])
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An unexpected error occurred while deleting student records: {e}")
            return

        if self.selected_id in ids:
            self.clear_form()
        # load_list()/load_reports_search() run via the STUDENTS_UPDATED
        # subscription below (see on_students_updated) — calling them here
        # too would refresh both twice for no benefit.
        EventBus.emit("STUDENTS_UPDATED")
        QMessageBox.information(self, "Delete Students", f"Deleted {count} student(s).")

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
        self.save_btn.setText("Save Student")
        self.delete_btn.setEnabled(False)
        self.switch_page(0)

    # =====================================================
    # PAGE 2: REPORTS
    # =====================================================

    def hide_preview(self):
        """Hide the preview frame and clear its content."""
        self.preview_frame.setVisible(False)
        self.clear_preview_layout()

    def load_reports_search(self):
        level = SystemState.get_level()
        search_text = self.reports_search.text().strip()
        if search_text:
            pattern = f"%{search_text}%"
            rows = fetch_all("""
                SELECT id, admission_no, full_name, class
                FROM students WHERE level=?
                AND (admission_no LIKE ? OR full_name LIKE ? OR class LIKE ?)
                ORDER BY full_name LIMIT 50
            """, (level, pattern, pattern, pattern))
        else:
            rows = fetch_all("""
                SELECT id, admission_no, full_name, class
                FROM students WHERE level=? ORDER BY full_name LIMIT 50
            """, (level,))
        self.reports_student_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column, value in enumerate(row):
                text = "" if value is None else str(value)
                item = QTableWidgetItem(text)
                item.setToolTip(text)
                self.reports_student_table.setItem(row_index, column, item)
        self.reports_table_page.setRowCount(0)
        self.hide_preview()
        self.reports_selected_admission = None
        self.view_report_page_btn.setEnabled(False)
        self.download_report_page_btn.setEnabled(False)
        self.preview_marks_btn.setEnabled(False)

    def on_reports_student_selected(self):
        row = self.reports_student_table.currentRow()
        if row < 0:
            return
        admission_no = self.reports_student_table.item(row, 1).text()
        self.reports_selected_admission = admission_no
        self.load_reports_for_student(admission_no)
        self.hide_preview()

    def load_reports_for_student(self, admission_no):
        from report_card_v5 import list_student_report_exams
        level = SystemState.get_level()
        self.reports_table_page.setRowCount(0)
        self.view_report_page_btn.setEnabled(False)
        self.download_report_page_btn.setEnabled(False)
        self.preview_marks_btn.setEnabled(False)
        self.hide_preview()

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
        self.reports_table_page.resizeRowsToContents()
        if rows:
            self.reports_table_page.selectRow(0)

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
        self.preview_marks_btn.setEnabled(has_report)

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
        return "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in label)

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
        safe_adm = "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in self.reports_selected_admission)
        default_name = f"{safe_adm}_{self.current_report_label_page()}.pdf"
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Student Report", default_name, "PDF Files (*.pdf)")
        if not save_path:
            return
        if not save_path.lower().endswith(".pdf"):
            save_path += ".pdf"
        self.selected_admission_no = self.reports_selected_admission
        self.generate_report_for_exam(exam_id, save_path=save_path, open_after=False)

    # =====================================================
    # FULL REPORT CARD PREVIEW (no signatures)
    # =====================================================

    def preview_selected_exam_marks(self):
        exam_id = self.current_report_exam_id_page()
        admission_no = self.reports_selected_admission

        if exam_id is None or not admission_no:
            return

        level = SystemState.get_level()

        # ---- Student details ----
        student = fetch_one("""
            SELECT full_name, class, stream, gender, level
            FROM students WHERE admission_no=?
        """, (admission_no,))
        if not student:
            return
        full_name, class_name, stream, gender, student_level = student
        gender_display = "M" if gender and gender.lower().startswith("m") else "F" if gender else "-"

        # ---- Get the historical class for this exam (fix for dash issue) ----
        hist_class = fetch_one("""
            SELECT DISTINCT class_name
            FROM results
            WHERE admission_no = ? AND exam_id = ? AND class_name IS NOT NULL AND class_name != ''
        """, (admission_no, exam_id))
        if hist_class and hist_class[0]:
            class_for_ranking = hist_class[0]
        else:
            class_for_ranking = class_name

        # ---- Exam details ----
        exam_info = fetch_one("""
            SELECT e.exam_name, t.term_name, y.year_name, e.status
            FROM exams e
            JOIN terms t ON e.term_id = t.id
            JOIN academic_years y ON t.academic_year_id = y.id
            WHERE e.id = ?
        """, (exam_id,))
        if not exam_info:
            return
        exam_name, term_name, year_name, status = exam_info

        # ---- Ranking (using historical class) ----
        ranking = compute_student_scores(level, exam_id, class_for_ranking)
        student_rank = "-"
        student_division = "-"
        student_points = "-"
        for r in ranking:
            if r.get('admission') == admission_no:
                student_rank = r.get('position', '-')
                student_division = r.get('division', '-')
                student_points = r.get('points', '-')
                break

        # ---- Subject results and average (computed directly) ----
        results = fetch_all("""
            SELECT r.subject_name, r.marks, s.subject_short_name
            FROM results r
            LEFT JOIN subjects s ON s.subject_name = r.subject_name AND s.level = ?
            WHERE r.admission_no = ? AND r.exam_id = ?
            ORDER BY r.subject_name
        """, (level, admission_no, exam_id))

        total_marks = 0
        subject_count = 0
        for _, marks, _ in results:
            total_marks += marks
            subject_count += 1
        student_avg = round(total_marks / subject_count, 2) if subject_count > 0 else 0

        # ---- Comments ----
        remarks = fetch_one("""
            SELECT teacher_remarks, headteacher_remarks, academic_master_remarks, discipline_master_remarks
            FROM exam_remarks
            WHERE admission_no = ? AND exam_id = ?
        """, (admission_no, exam_id))
        if remarks:
            teacher_rem, head_rem, academic_rem, discipline_rem = remarks
        else:
            teacher_rem = head_rem = academic_rem = discipline_rem = None

        if teacher_rem is None:
            teacher_rem = get_default_remark(student_avg, student_division if student_division != '-' else '0', level)
        if head_rem is None:
            head_rem = get_headteacher_remark(student_division)
        if academic_rem is None:
            academic_rem = get_academic_master_remark(student_division)
        if discipline_rem is None:
            discipline_rem = get_discipline_master_remark(student_avg)

        # ---- Requirements ----
        term_info = fetch_one("""
            SELECT t.id, t.academic_year_id
            FROM terms t
            JOIN exams e ON e.term_id = t.id
            WHERE e.id = ?
        """, (exam_id,))
        term_id = term_info[0] if term_info else None
        year_id = term_info[1] if term_info else None

        req_rows = []
        if term_id and year_id:
            req_rows = fetch_all("""
                SELECT item_name, quantity
                FROM requirements
                WHERE academic_year_id = ? AND term_id = ? AND level = ?
                  AND (class_name = ? OR class_name = '-- All Classes --')
                ORDER BY item_name
            """, (year_id, term_id, level, class_for_ranking))

        # ---- Build preview ----
        self.clear_preview_layout()

        # Header
        header = QLabel("📄 REPORT CARD PREVIEW")
        header.setProperty("variant", "accent")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.preview_layout.addWidget(header)

        # Student Profile
        profile_text = (
            f"<b>Student:</b> {full_name} &nbsp;|&nbsp; "
            f"<b>Admission:</b> {admission_no} &nbsp;|&nbsp; "
            f"<b>Gender:</b> {gender_display} &nbsp;|&nbsp; "
            f"<b>Class:</b> {class_name} &nbsp;|&nbsp; "
            f"<b>Stream:</b> {stream or '-'} &nbsp;|&nbsp; "
            f"<b>Level:</b> {student_level} &nbsp;|&nbsp; "
            f"<b>Exam:</b> {exam_name} ({status}) &nbsp;|&nbsp; "
            f"<b>Term:</b> {term_name} &nbsp;|&nbsp; "
            f"<b>Year:</b> {year_name}"
        )
        profile_label = QLabel(profile_text)
        profile_label.setWordWrap(True)
        profile_label.setStyleSheet("padding: 8px; background: rgba(0,0,0,0.04); border-radius: 6px; font-size: 12px;")
        self.preview_layout.addWidget(profile_label)

        # Academic Summary
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(20)
        summary_layout.addWidget(QLabel(f"<b>Rank:</b> {student_rank}"))
        summary_layout.addWidget(QLabel(f"<b>Division:</b> {student_division if student_division else '-'}"))
        summary_layout.addWidget(QLabel(f"<b>Points:</b> {student_points if student_points else '-'}"))
        summary_layout.addWidget(QLabel(f"<b>Average:</b> {student_avg}%"))
        summary_layout.addStretch()
        self.preview_layout.addLayout(summary_layout)

        # Subject Performance
        subject_label = QLabel("Subject Performance")
        subject_label.setStyleSheet("font-weight: bold; margin-top: 6px; font-size: 13px;")
        self.preview_layout.addWidget(subject_label)

        preview_table = QTableWidget()
        preview_table.setColumnCount(3)
        preview_table.setHorizontalHeaderLabels(["Subject", "Marks", "Grade"])
        preview_table.verticalHeader().setVisible(False)
        preview_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        preview_table.setAlternatingRowColors(True)
        preview_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        preview_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        preview_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        if results:
            preview_table.setRowCount(len(results))
            for i, (subject, marks, short_name) in enumerate(results):
                display_name = short_name or subject
                grade = get_grade(marks, level=level)
                preview_table.setItem(i, 0, QTableWidgetItem(display_name))
                preview_table.setItem(i, 1, QTableWidgetItem(str(marks)))
                preview_table.setItem(i, 2, QTableWidgetItem(grade))

            # Total row
            preview_table.setRowCount(len(results) + 1)
            total_row = len(results)
            preview_table.setItem(total_row, 0, QTableWidgetItem("TOTAL"))
            preview_table.setItem(total_row, 1, QTableWidgetItem(str(total_marks)))
            preview_table.setItem(total_row, 2, QTableWidgetItem(f"{student_avg:.2f}%"))
            for col in range(3):
                item = preview_table.item(total_row, col)
                if item:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
        else:
            preview_table.setRowCount(1)
            preview_table.setItem(0, 0, QTableWidgetItem("No marks recorded for this exam."))
            preview_table.setSpan(0, 0, 1, 3)

        preview_table.resizeColumnsToContents()
        preview_table.resizeRowsToContents()
        preview_table.setFixedHeight(
            preview_table.rowHeight(0) * (preview_table.rowCount() + 1) +
            preview_table.horizontalHeader().height() + 10
        )
        self.preview_layout.addWidget(preview_table)

        # ---- Requirements (instead of signatures) ----
        if req_rows:
            req_label = QLabel("Requirements")
            req_label.setStyleSheet("font-weight: bold; margin-top: 6px; font-size: 13px;")
            self.preview_layout.addWidget(req_label)

            req_table = QTableWidget()
            req_table.setColumnCount(2)
            req_table.setHorizontalHeaderLabels(["Item", "Quantity"])
            req_table.verticalHeader().setVisible(False)
            req_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            req_table.setAlternatingRowColors(True)
            req_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            req_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            req_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

            req_table.setRowCount(len(req_rows))
            for i, (item, qty) in enumerate(req_rows):
                req_table.setItem(i, 0, QTableWidgetItem(item))
                req_table.setItem(i, 1, QTableWidgetItem(str(qty)))

            req_table.resizeColumnsToContents()
            req_table.resizeRowsToContents()
            req_table.setFixedHeight(
                req_table.rowHeight(0) * (len(req_rows) + 1) +
                req_table.horizontalHeader().height() + 10
            )
            self.preview_layout.addWidget(req_table)

        # ---- Comments ----
        comments_label = QLabel("Comments")
        comments_label.setStyleSheet("font-weight: bold; margin-top: 6px; font-size: 13px;")
        self.preview_layout.addWidget(comments_label)

        comments_data = [
            ("Class Teacher", teacher_rem or "______________________________________________"),
            ("Academic Master", academic_rem or "______________________________________________"),
            ("Head Teacher", head_rem or "______________________________________________"),
            ("Discipline Master", discipline_rem or "______________________________________________"),
        ]
        comments_table = QTableWidget()
        comments_table.setColumnCount(2)
        comments_table.setHorizontalHeaderLabels(["Role", "Remark"])
        comments_table.verticalHeader().setVisible(False)
        comments_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        comments_table.setAlternatingRowColors(True)
        comments_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        comments_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        comments_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        comments_table.setRowCount(len(comments_data))
        for i, (role, remark) in enumerate(comments_data):
            comments_table.setItem(i, 0, QTableWidgetItem(role))
            comments_table.setItem(i, 1, QTableWidgetItem(remark))
        comments_table.resizeColumnsToContents()
        comments_table.resizeRowsToContents()
        comments_table.setFixedHeight(
            comments_table.rowHeight(0) * (len(comments_data) + 1) +
            comments_table.horizontalHeader().height() + 10
        )
        self.preview_layout.addWidget(comments_table)

        # ---- No signatures section ----

        self.preview_frame.setVisible(True)

    def clear_preview_layout(self):
        """Robustly remove all widgets from the preview layout."""
        while self.preview_layout.count():
            item = self.preview_layout.takeAt(0)
            if item.widget():
                widget = item.widget()
                widget.setParent(None)
                widget.deleteLater()
            elif item.layout():
                # If it's a layout, clear it recursively
                self._clear_layout(item.layout())
        # Also remove any direct children of the preview frame (just in case)
        for child in self.preview_frame.children():
            if isinstance(child, QWidget):
                child.setParent(None)
                child.deleteLater()

    def _clear_layout(self, layout):
        """Recursively clear a layout."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                widget = item.widget()
                widget.setParent(None)
                widget.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

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
                QMessageBox.warning(self, "Report Card", f"Report generated at {result}, but the system viewer could not be opened.")
        else:
            QMessageBox.information(self, "Report Card", f"Report saved to {result}")

    # =====================================================
    # EXCEL FRAMEWORK
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
        excel_utils.export_to_excel(self, f"students_{level}.xlsx", ["Admission No", "Exam No", "Full Name", "Gender", "Class", "Stream", "Comments"], data)

    def import_excel(self):
        import excel_utils
        import openpyxl
        path = excel_utils.get_import_file(self)
        if not path:
            return
        try:
            wb = openpyxl.load_workbook(path, data_only=True)
            sheet = wb.active
            data_start_row = excel_utils.find_data_start_row(sheet)
            if data_start_row is None:
                raise ValueError(
                    "Could not detect the template's header row. Please use a "
                    "template downloaded from this system, and don't remove "
                    "the 'INSTRUCTIONS:' block or reorder rows."
                )
            rows = list(sheet.iter_rows(min_row=data_start_row, values_only=True))
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
            # load_list()/load_reports_search() run via the STUDENTS_UPDATED
            # subscription (see on_students_updated) — calling them here too
            # would refresh both twice for no benefit.
            EventBus.emit("STUDENTS_UPDATED")
            QMessageBox.information(self, "Import Complete",
                                  f"Operation Summary:\n- New Students Imported: {imported}\n- Existing Records Updated: {updated}\n- Rows Redirected to Actual Level: {redirected}\n- Records Rejected (Invalid Data): {rejected}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed: {e}")