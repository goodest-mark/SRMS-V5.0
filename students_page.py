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
)

import sqlite3

from class_utils import get_classes
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

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        root.addWidget(self.scroll_area)

        self.content_widget = QWidget()
        self.scroll_area.setWidget(self.content_widget)

        layout = QVBoxLayout(self.content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("STUDENTS MODULE")
        layout.addWidget(title)

        form = QHBoxLayout()

        self.adm = QLineEdit()
        self.adm.setPlaceholderText("Admission No *")

        self.name = QLineEdit()
        self.name.setPlaceholderText("Full Name *")

        self.gender = QComboBox()
        self.gender.addItems(["Male", "Female"])

        self.class_box = QComboBox()
        self.class_box.setPlaceholderText("Select Class *")

        self.stream = QLineEdit()
        self.stream.setPlaceholderText("Stream (Optional)")

        self.comment = QTextEdit()
        self.comment.setPlaceholderText("Comments / Remarks")
        self.comment.setFixedHeight(70)

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

        form.addWidget(self.adm)
        form.addWidget(self.name)
        form.addWidget(self.gender)
        form.addWidget(self.class_box)
        form.addWidget(self.stream)
        form.addWidget(self.save_btn)
        form.addWidget(self.delete_btn)
        form.addWidget(self.import_btn)
        form.addWidget(self.export_btn)
        form.addWidget(self.template_btn)

        layout.addLayout(form)
        layout.addWidget(self.comment)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search student...")
        self.search.textChanged.connect(self.load)
        layout.addWidget(self.search)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID",
            "Admission No",
            "Full Name",
            "Gender",
            "Class",
            "Stream",
            "Level",
        ])
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
        self.table.itemSelectionChanged.connect(self.on_student_selection_changed)
        self.table.doubleClicked.connect(self.on_student_double_clicked)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        header.setStretchLastSection(True)

        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout.addWidget(self.table)

        reports_group = QGroupBox("Student Reports")
        reports_layout = QVBoxLayout(reports_group)

        report_actions = QHBoxLayout()
        self.reports_title = QLabel("Select a student to view available exam reports.")
        self.reports_title.setProperty("variant", "muted")
        self.view_report_btn = QPushButton("VIEW REPORT")
        self.download_report_btn = QPushButton("DOWNLOAD REPORT")
        self.view_report_btn.clicked.connect(self.view_selected_exam_report)
        self.download_report_btn.clicked.connect(self.download_selected_exam_report)
        self.view_report_btn.setEnabled(False)
        self.download_report_btn.setEnabled(False)

        report_actions.addWidget(self.reports_title, 1)
        report_actions.addWidget(self.view_report_btn)
        report_actions.addWidget(self.download_report_btn)
        reports_layout.addLayout(report_actions)

        self.reports_table = QTableWidget()
        self.reports_table.setColumnCount(7)
        self.reports_table.setHorizontalHeaderLabels([
            "Exam ID",
            "Exam",
            "Term",
            "Year",
            "Status",
            "Subjects",
            "Average",
        ])
        self.reports_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.reports_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.reports_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.reports_table.setMaximumHeight(170)
        self.reports_table.verticalHeader().setVisible(False)
        self.reports_table.itemSelectionChanged.connect(
            self.update_report_actions
        )
        self.reports_table.doubleClicked.connect(
            self.view_selected_exam_report
        )
        self.reports_table.setColumnHidden(0, True)
        reports_header = self.reports_table.horizontalHeader()
        reports_header.setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        reports_header.setStretchLastSection(True)
        
        self.reports_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.reports_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.reports_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.reports_table.setMinimumHeight(120)

        reports_layout.addWidget(self.reports_table)

        layout.addWidget(reports_group)

        EventBus.subscribe("STUDENTS_UPDATED", self.load)
        EventBus.subscribe("LEVEL_CHANGED", self.on_level_changed)

        self.refresh_classes()
        self.load()

    def on_level_changed(self):
        if not self.isVisible():
            self._needs_refresh = True
            return
        self.clear_form()
        self.refresh_classes()
        self.load()

    def showEvent(self, event):
        super().showEvent(event)
        if getattr(self, "_needs_refresh", False):
            self._needs_refresh = False
            self.on_level_changed()

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

    def load(self):
        level = SystemState.get_level()
        search_text = self.search.text().strip()

        if search_text:
            pattern = f"%{search_text}%"
            rows = fetch_all("""
                SELECT id, admission_no, full_name, gender, class, stream, level
                FROM students
                WHERE level=?
                  AND (
                      admission_no LIKE ?
                      OR full_name LIKE ?
                      OR class LIKE ?
                      OR COALESCE(stream, '') LIKE ?
                  )
                ORDER BY id DESC
            """, (level, pattern, pattern, pattern, pattern))
        else:
            rows = fetch_all("""
                SELECT id, admission_no, full_name, gender, class, stream, level
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

        self._update_table_height(self.table)

        if self.selected_admission_no:
            self.load_student_reports(self.selected_admission_no)

    def save_student(self):
        admission_no = self.adm.text().strip()
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
                        INSERT INTO students (admission_no, full_name, gender, class, stream, level, comments)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (admission_no, full_name, gender, class_name, stream, level, comment))
                else:
                    cur.execute("""
                        UPDATE students
                        SET admission_no=?, full_name=?, gender=?, class=?, stream=?, level=?, comments=?
                        WHERE id=?
                    """, (admission_no, full_name, gender, class_name, stream, level, comment, self.selected_id))

        except sqlite3.IntegrityError:
            QMessageBox.warning(
                self,
                "Duplicate Admission Number",
                "That admission number is already registered.",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Database Error",
                f"An unexpected error occurred while saving the student record: {e}",
            )
            return

        self.clear_form()
        EventBus.emit("STUDENTS_UPDATED")

    def load_selected(self):
        row = self.table.currentRow()

        if row < 0:
            return

        self.selected_id = int(self.table.item(row, 0).text())
        self.selected_admission_no = self.table.item(row, 1).text()
        self.adm.setText(self.selected_admission_no)
        self.name.setText(self.table.item(row, 2).text())

        gender = self.table.item(row, 3).text()
        gender_index = self.gender.findText(gender)
        if gender_index >= 0:
            self.gender.setCurrentIndex(gender_index)

        class_name = self.table.item(row, 4).text()
        class_index = self.class_box.findText(class_name)
        if class_index >= 0:
            self.class_box.setCurrentIndex(class_index)

        self.stream.setText(self.table.item(row, 5).text())

        with get_cursor() as cur:
            cur.execute("SELECT comments FROM students WHERE id=?", (self.selected_id,))
            comments_row = cur.fetchone()
            self.comment.setText(comments_row[0] if comments_row and comments_row[0] else "")

        self.save_btn.setText("UPDATE")
        self.delete_btn.setEnabled(True)
        self.load_student_reports(self.selected_admission_no)

    def on_student_selection_changed(self):
        if self.table.currentRow() < 0 or not self.table.selectedItems():
            return
        self.load_selected()

    def on_student_double_clicked(self):
        self.load_selected()
        self.load_student_reports(self.selected_admission_no)

    def open_selected_report_card(self):
        self.load_selected()
        self.view_selected_exam_report()

    def load_student_reports(self, admission_no=None):
        from report_card_v5 import list_student_report_exams
        admission_no = admission_no or self.selected_admission_no
        level = SystemState.get_level()
        self.reports_table.setRowCount(0)
        self.update_report_actions()

        if not admission_no:
            self.reports_title.setText("Select a student to view available exam reports.")
            return

        rows = list_student_report_exams(admission_no, level)

        self.reports_table.setRowCount(len(rows))
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
                self.reports_table.setItem(row_index, column, item)

        self._update_table_height(self.reports_table)

        if rows:
            self.reports_table.selectRow(0)
            self.reports_title.setText(
                f"{len(rows)} exam report(s) available for {admission_no}."
            )
        else:
            self.reports_title.setText(
                f"No exam reports found for {admission_no}."
            )

        self.update_report_actions()

    def _update_table_height(self, table):
        table.resizeRowsToContents()
        height = (
            table.horizontalHeader().height()
            + table.verticalHeader().length()
            + table.frameWidth() * 2
            + 4
        )
        table.setFixedHeight(height)

    def update_report_actions(self):
        has_report = self.current_report_exam_id() is not None
        self.view_report_btn.setEnabled(has_report)
        self.download_report_btn.setEnabled(has_report)

    def current_report_exam_id(self):
        row = self.reports_table.currentRow()
        if row < 0:
            return None
        item = self.reports_table.item(row, 0)
        if item is None:
            return None
        try:
            return int(item.text())
        except ValueError:
            return None

    def current_report_label(self):
        row = self.reports_table.currentRow()
        if row < 0:
            return "report"
        parts = []
        for column in (1, 2, 3):
            item = self.reports_table.item(row, column)
            if item and item.text().strip():
                parts.append(item.text().strip())
        label = "_".join(parts) or "report"
        return "".join(
            ch if ch.isalnum() or ch in ("_", "-") else "_"
            for ch in label
        )

    def view_selected_exam_report(self):
        exam_id = self.current_report_exam_id()
        if exam_id is None:
            return
        self.generate_report_for_exam(exam_id, open_after=True)

    def download_selected_exam_report(self):
        exam_id = self.current_report_exam_id()
        if exam_id is None or not self.selected_admission_no:
            return

        safe_adm = "".join(
            ch if ch.isalnum() or ch in ("_", "-") else "_"
            for ch in self.selected_admission_no
        )
        default_name = f"{safe_adm}_{self.current_report_label()}.pdf"
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
        self.generate_report_for_exam(exam_id, save_path=save_path, open_after=False)

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

    def view_report_card(self):
        if self.selected_id is None:
            return

        row = self.table.currentRow()
        if row < 0:
            return

        admission_item = self.table.item(row, 1)
        if admission_item is None:
            return

        admission_no = admission_item.text().strip()
        level = SystemState.get_level()

        self.selected_admission_no = admission_no
        exam_id = self.current_report_exam_id()
        if exam_id is None:
            self.load_student_reports(admission_no)
            exam_id = self.current_report_exam_id()
        if exam_id is not None:
            self.generate_report_for_exam(exam_id, open_after=True)

    def delete_student(self):
        if self.selected_id is None:
            QMessageBox.warning(
                self, "Delete Student",
                "Double-click a student before deleting.",
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
        self.name.clear()
        self.stream.clear()
        self.comment.clear()
        self.gender.setCurrentIndex(0)

        if self.class_box.count() > 0:
            self.class_box.setCurrentIndex(0)

        self.table.clearSelection()
        self.reports_table.setRowCount(0)
        self.reports_title.setText("Select a student to view available exam reports.")
        self.update_report_actions()
        self.save_btn.setText("SAVE")
        self.delete_btn.setEnabled(False)
    # =========================
    # EXCEL FRAMEWORK
    # =========================

    def download_template(self):
        import excel_utils
        excel_utils.download_template(
            self, 
            "students_template.xlsx",
            "STUDENT REGISTRATION FORM",
            ["Admission No*", "Full Name*", "Gender*", "Class*", "Stream", "Level", "Comments"],
            samples=["2024/001", "John Doe", "Male", "Form I", "A", SystemState.get_level(), "Good progress"]
        )

    def export_excel(self):
        import excel_utils
        level = SystemState.get_level()
        data = fetch_all("SELECT admission_no, full_name, gender, class, stream, comments FROM students WHERE level=?", (level,))
        
        excel_utils.export_to_excel(
            self, 
            f"students_{level}.xlsx", 
            ["Admission No", "Full Name", "Gender", "Class", "Stream", "Comments"],
            data
        )

    def import_excel(self):
        import excel_utils
        import openpyxl
        path = excel_utils.get_import_file(self)
        if not path: return
        
        try:
            wb = openpyxl.load_workbook(path, data_only=True)
            sheet = wb.active
            rows = list(sheet.iter_rows(min_row=12, values_only=True))

            imported = 0
            updated = 0
            rejected = 0

            o_classes = ["Form I", "Form II", "Form III", "Form IV"]
            a_classes = ["Form V", "Form VI"]

            with get_cursor(commit=True) as cur:
                for row in rows:
                    if not row or not row[0]:
                        continue

                    if len(row) < 7:
                        rejected += 1
                        continue

                    adm = str(row[0]).strip()
                    name = str(row[1] or "").strip()
                    gender = str(row[2] or "").strip()
                    cls = str(row[3] or "").strip()
                    stream = str(row[4] or "").strip()
                    level_excel = str(row[5] or "").strip().upper()
                    comment = str(row[6] or "").strip()

                    if not name or not cls or not level_excel:
                        rejected += 1
                        continue

                    is_valid = False
                    if level_excel == "O_LEVEL" and cls in o_classes:
                        is_valid = True
                    elif level_excel == "A_LEVEL" and cls in a_classes:
                        is_valid = True

                    if not is_valid:
                        rejected += 1
                        continue
                    
                    try:
                        cur.execute("SELECT 1 FROM students WHERE admission_no=?", (adm,))
                        exists = cur.fetchone()

                        cur.execute("""
                            INSERT INTO students (admission_no, full_name, gender, class, stream, level, comments)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(admission_no) DO UPDATE SET
                                full_name=excluded.full_name,
                                gender=excluded.gender,
                                class=excluded.class,
                                stream=excluded.stream,
                                level=excluded.level,
                                comments=excluded.comments
                        """, (adm, name, gender, cls, stream, level_excel, comment))
                        
                        if exists:
                            updated += 1
                        else:
                            imported += 1
                    except Exception as e:
                        print(f"[ERROR] Failed to import student '{adm}': {e}")
                        rejected += 1
                        continue
            
            self.load()
            EventBus.emit("STUDENTS_UPDATED")
            QMessageBox.information(self, "Import Complete", 
                                  f"Operation Summary:\n"
                                  f"- New Students Imported: {imported}\n"
                                  f"- Existing Records Updated: {updated}\n"
                                  f"- Records Rejected (Invalid Data): {rejected}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed: {e}")
