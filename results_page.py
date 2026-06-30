from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QFrame
)

from progress_dialog import ProgressDialog
import openpyxl
import excel_utils

from class_utils import get_classes
from db_utils import get_cursor, fetch_all, fetch_one, get_exam_context
from event_bus import EventBus
from system_state import SystemState
from ui_helpers import show_error, show_info
import combo_loaders


class MarksDelegate(QStyledItemDelegate):

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        editor.setPlaceholderText("0 - 100")
        editor.setFrame(True)

        editor.textChanged.connect(
            lambda text, field=editor, model=index.model(), cell=index:
            self._handle_text_changed(field, model, cell, text)
        )

        return editor

    def setEditorData(self, editor, index):
        editor.setText(str(index.data() or ""))
        self._set_validation_style(editor, editor.text())

    def setModelData(self, editor, model, index):
        model.setData(
            index,
            editor.text().strip(),
            Qt.ItemDataRole.EditRole,
        )

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect.adjusted(4, 3, -4, -3))

    def _handle_text_changed(self, editor, model, index, text):
        self._set_validation_style(editor, text)
        model.setData(
            index,
            text,
            Qt.ItemDataRole.EditRole,
        )

    @staticmethod
    def _set_validation_style(editor, text):
        value = text.strip()
        valid = not value or (
            value.isdigit()
            and 0 <= int(value) <= 100
        )

        if valid:
            editor.setStyleSheet(
                "QLineEdit {"
                "background-color: #111827;"
                "color: white;"
                "border: 1px solid #334155;"
                "border-radius: 4px;"
                "padding: 4px;"
                "}"
                "QLineEdit:focus {"
                "border: 2px solid #3b82f6;"
                "}"
            )
        else:
            editor.setStyleSheet(
                "QLineEdit {"
                "background-color: #3f1d24;"
                "color: #fecaca;"
                "border: 2px solid #ef4444;"
                "border-radius: 4px;"
                "padding: 4px;"
                "}"
            )


class ResultsPage(QWidget):

    def __init__(self):
        super().__init__()

        self.loading_table = False
        self.exam_read_only = False

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        title = QLabel("RESULTS ENTRY V4.1")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: white;"
        )
        layout.addWidget(title)

        # =====================================
        # FILTERS
        # =====================================
        filters_group = QGroupBox("Selection Filters")
        filters_layout = QHBoxLayout(filters_group)

        self.exam = QComboBox()
        self.exam.setMinimumWidth(180)
        self.exam.setPlaceholderText("Select Exam")

        self.class_box = QComboBox()
        self.class_box.setMinimumWidth(150)
        self.class_box.setPlaceholderText("Select Class")

        self.subject = QComboBox()
        self.subject.setMinimumWidth(220)
        self.subject.setPlaceholderText("Select Subject")

        self.refresh_top_btn = QPushButton("REFRESH")
        self.refresh_top_btn.clicked.connect(self.refresh_all)

        filters_layout.addWidget(QLabel("Exam"))
        filters_layout.addWidget(self.exam)
        filters_layout.addWidget(QLabel("Class"))
        filters_layout.addWidget(self.class_box)
        filters_layout.addWidget(QLabel("Subject"))
        filters_layout.addWidget(self.subject)
        filters_layout.addWidget(self.refresh_top_btn)

        layout.addWidget(filters_group)

        # =====================================
        # TOP SUMMARY (V4.1)
        # =====================================
        summary_group = QGroupBox("Progress Summary")
        summary_layout = QGridLayout(summary_group)

        self.expected_value = QLabel("0")
        self.entered_value = QLabel("0")
        self.missing_value = QLabel("0")
        self.completion_value = QLabel("0.00%")

        summary_labels = (
            self.expected_value,
            self.entered_value,
            self.missing_value,
            self.completion_value,
        )

        for label in summary_labels:
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #3b82f6;"
            )

        summary_layout.addWidget(QLabel("Expected Students"), 0, 0)
        summary_layout.addWidget(QLabel("Entered Marks"), 0, 1)
        summary_layout.addWidget(QLabel("Missing Marks"), 0, 2)
        summary_layout.addWidget(QLabel("Completion %"), 0, 3)
        summary_layout.addWidget(self.expected_value, 1, 0)
        summary_layout.addWidget(self.entered_value, 1, 1)
        summary_layout.addWidget(self.missing_value, 1, 2)
        summary_layout.addWidget(self.completion_value, 1, 3)

        layout.addWidget(summary_group)

        # =====================================
        # MARKS TABLE
        # =====================================
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            "Admission No",
            "Student Name",
            "Marks",
        ])
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.AllEditTriggers
        )
        self.table.setItemDelegateForColumn(2, MarksDelegate(self.table))
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.itemChanged.connect(self.update_summary)

        self.lock_label = QLabel("")
        self.lock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lock_label.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #facc15;"
            "background: rgba(250, 204, 21, 0.10);"
            "border: 1px solid rgba(250, 204, 21, 0.30);"
            "border-radius: 8px; padding: 8px;"
        )
        self.lock_label.hide()

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )
        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.Interactive,
        )
        self.table.setColumnWidth(2, 160)

        layout.addWidget(self.lock_label)
        layout.addWidget(self.table, 1)

        # =====================================
        # BOTTOM BUTTONS
        # =====================================
        buttons = QHBoxLayout()
        buttons.addStretch()

        self.save_btn = QPushButton("SAVE ALL RESULTS")
        self.save_btn.setFixedHeight(40)
        self.save_btn.setStyleSheet("background-color: #10b981; color: white; font-weight: bold;")
        self.save_btn.clicked.connect(self.save_all)

        self.import_btn = QPushButton("IMPORT EXCEL")
        self.import_btn.clicked.connect(self.import_excel)
        
        self.template_btn = QPushButton("DOWNLOAD TEMPLATE")
        self.template_btn.clicked.connect(self.download_template)

        buttons.addWidget(self.import_btn)
        buttons.addWidget(self.template_btn)
        buttons.addWidget(self.save_btn)
        layout.addLayout(buttons)

        # Connect events
        self.exam.currentIndexChanged.connect(self.load_subjects)
        self.class_box.currentIndexChanged.connect(self.load_subjects)
        self.subject.currentIndexChanged.connect(self.load_students)

        EventBus.subscribe("LEVEL_CHANGED", self.on_level_changed)
        EventBus.subscribe("STUDENTS_UPDATED", self.refresh_all)
        EventBus.subscribe("EXAMS_UPDATED", self.refresh_all)
        EventBus.subscribe(
            "OPEN_RESULTS_ENTRY",
            self.open_from_dashboard,
        )

        self.refresh_all()

    def on_level_changed(self):
        self.refresh_all()

    def load(self):
        self.refresh_all()

    def open_from_dashboard(
        self,
        exam_id,
        class_name,
        subject_name,
    ):
        self.load_exams()
        self.load_classes()

        exam_index = self.exam.findData(exam_id)
        class_index = self.class_box.findText(class_name)

        if exam_index < 0 or class_index < 0:
            self._clear_table()
            return

        self.exam.blockSignals(True)
        self.class_box.blockSignals(True)
        try:
            self.exam.setCurrentIndex(exam_index)
            self.class_box.setCurrentIndex(class_index)
        finally:
            self.exam.blockSignals(False)
            self.class_box.blockSignals(False)

        self.load_subjects()
        
        # Match subject name by stripping percentage if needed
        for i in range(self.subject.count()):
            item_text = self.subject.itemText(i)
            base_name = item_text.split(" (")[0]
            if base_name == subject_name:
                self.subject.setCurrentIndex(i)
                return

        self._clear_table()

    def refresh_all(self):
        self.load_exams()
        self.load_classes()
        self.load_subjects()

    def load_exams(self):
        combo_loaders.load_results_exams(self.exam)

    def load_classes(self):
        combo_loaders.load_classes(self.class_box)

    def load_subjects(self):
        exam_id = self.exam.currentData()
        class_name = self.class_box.currentText().strip()
        level = SystemState.get_level()

        if not class_name or exam_id is None:
            self.subject.clear()
            self._clear_table()
            return

        current_subject_full = self.subject.currentText()
        current_subject_base = current_subject_full.split(" (")[0]

        context = get_exam_context(exam_id)
        if not context:
            self.subject.clear()
            self._clear_table()
            return
            
        year_id, term_id = context

        rows = fetch_all("""
            SELECT 
                e.subject_name,
                COUNT(DISTINCT e.admission_no) as expected,
                (SELECT COUNT(*) FROM results r 
                 JOIN students s2 ON s2.admission_no = r.admission_no
                 WHERE r.subject_name = e.subject_name 
                   AND r.exam_id = ?
                   AND s2.class = ?
                   AND s2.level = ?) as entered
            FROM enrollments e
            JOIN students s ON s.admission_no = e.admission_no
            WHERE s.class=? AND s.level=?
              AND e.academic_year_id=? AND e.term_id=?
            GROUP BY e.subject_name
            ORDER BY e.subject_name
        """, (exam_id, class_name, level, class_name, level, year_id, term_id))

        self.subject.blockSignals(True)
        self.subject.clear()

        for name, expected, entered in rows:
            perc = (entered / expected * 100) if expected > 0 else 0
            display_name = f"{name} ({perc:.0f}%)"
            self.subject.addItem(display_name, name)

        # Restore selection
        for i in range(self.subject.count()):
            if self.subject.itemData(i) == current_subject_base:
                self.subject.setCurrentIndex(i)
                break
        else:
            if self.subject.count() > 0:
                self.subject.setCurrentIndex(0)
            else:
                self._clear_table()

        self.subject.blockSignals(False)
        self.load_students()

    def load_students(self):
        exam_id = self.exam.currentData()
        class_name = self.class_box.currentText().strip()
        subject_name = self.subject.currentData()
        level = SystemState.get_level()

        if exam_id is None or not class_name or not subject_name:
            self._clear_table()
            return

        self._update_exam_lock_state()

        context = get_exam_context(exam_id)
        if not context:
            self._clear_table()
            return
            
        year_id, term_id = context

        rows = fetch_all("""
            SELECT
                s.admission_no,
                s.full_name,
                r.marks
            FROM enrollments e
            JOIN students s ON s.admission_no = e.admission_no
            LEFT JOIN results r ON r.admission_no = s.admission_no
                AND r.subject_name = e.subject_name
                AND r.exam_id = ?
            WHERE
                e.subject_name = ?
            AND s.class = ?
            AND s.level = ?
            AND e.academic_year_id = ?
            AND e.term_id = ?
            ORDER BY s.full_name
        """, (exam_id, subject_name, class_name, level, year_id, term_id))

        self.loading_table = True
        self.table.setRowCount(len(rows))

        read_only_flags = (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
        )
        marks_flags = read_only_flags
        if not self.exam_read_only:
            marks_flags |= Qt.ItemFlag.ItemIsEditable

        for row_index, (admission_no, full_name, marks) in enumerate(rows):
            admission_item = QTableWidgetItem(admission_no)
            admission_item.setFlags(read_only_flags)

            name_item = QTableWidgetItem(full_name or "")
            name_item.setFlags(read_only_flags)

            marks_item = QTableWidgetItem(
                "" if marks is None else str(marks)
            )
            marks_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            marks_item.setFlags(marks_flags)

            self.table.setItem(row_index, 0, admission_item)
            self.table.setItem(row_index, 1, name_item)
            self.table.setItem(row_index, 2, marks_item)
            if self.exam_read_only:
                self.table.closePersistentEditor(marks_item)
            else:
                self.table.openPersistentEditor(marks_item)

        self.loading_table = False
        self.update_summary()

    def save_all(self):
        exam_id = self.exam.currentData()
        subject_name = self.subject.currentData()

        if exam_id is None or not subject_name:
            show_error(self, "Select an exam, class and subject.", title="Missing Filters")
            return

        if self._is_selected_exam_completed():
            show_error(
                self,
                "This exam is completed and read-only. Reopen it from Exams if edits are required.",
                title="Completed Exam"
            )
            return

        marks_to_save = []
        invalid_rows = []

        for row in range(self.table.rowCount()):
            admission_item = self.table.item(row, 0)
            marks_item = self.table.item(row, 2)

            if admission_item is None: continue

            marks_text = marks_item.text().strip() if marks_item is not None else ""
            if not marks_text: continue

            try:
                marks = int(marks_text)
                if not (0 <= marks <= 100): raise ValueError()
            except ValueError:
                invalid_rows.append(row + 1)
                continue

            marks_to_save.append((admission_item.text(), marks))

        if invalid_rows:
            show_error(self, f"Check row(s): {', '.join(map(str, invalid_rows))}", title="Invalid Marks")
            return

        try:
            with get_cursor(commit=True) as cur:
                for admission_no, marks in marks_to_save:
                    cur.execute("""
                        INSERT INTO results (admission_no, subject_name, marks, exam_id)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(admission_no, subject_name, exam_id)
                        DO UPDATE SET marks = excluded.marks
                    """, (admission_no, subject_name, marks, exam_id))
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An unexpected error occurred while saving results: {e}")
            return

        # V4.1: Automatically refresh subject completion
        self.load_subjects()
        EventBus.emit("RESULTS_UPDATED")

        show_info(self, "Results Saved Successfully")

    def update_summary(self, _item=None):
        if self.loading_table:
            return

        expected = self.table.rowCount()
        entered = 0

        for row in range(expected):
            item = self.table.item(row, 2)
            text = item.text().strip() if item is not None else ""
            if text: entered += 1

        missing = expected - entered
        completion = (entered / expected * 100) if expected else 0

        self.expected_value.setText(str(expected))
        self.entered_value.setText(str(entered))
        self.missing_value.setText(str(missing))
        self.completion_value.setText(f"{completion:.2f}%")

    # =========================
    # EXCEL FRAMEWORK
    # =========================

    def download_template(self):
        excel_utils.download_template(
            self, 
            "marks_template.xlsx",
            "EXAMINATION MARKS ENTRY FORM",
            ["Admission No*", "Marks (0-100)*"],
            samples=["2024/001", "85"]
        )

    def import_excel(self):
        exam_id = self.exam.currentData()
        subject_name = self.subject.currentData()
        
        if not (exam_id and subject_name):
            show_error(self, "Select Exam and Subject first")
            return

        if self._is_selected_exam_completed():
            show_error(
                self,
                "This exam is completed and read-only. Reopen it from Exams before importing marks.",
                title="Completed Exam"
            )
            return
            
        path = excel_utils.get_import_file(self)
        if not path: return
        
        try:
            wb = openpyxl.load_workbook(path, data_only=True)
            sheet = wb.active
            rows = list(sheet.iter_rows(min_row=12, values_only=True))
            
            context = get_exam_context(exam_id)
            if not context:
                raise ValueError("Selected exam does not exist.")
            year_id, term_id = context
            
            imported = 0
            with get_cursor(commit=True) as cur:
                for row in rows:
                    if not row or not row[0] or row[1] is None: continue
                    adm, marks = row

                    cur.execute("""
                        SELECT 1 FROM enrollments
                        WHERE admission_no=? AND subject_name=? AND academic_year_id=? AND term_id=?
                    """, (str(adm), subject_name, year_id, term_id))

                    if cur.fetchone():
                        try:
                            cur.execute("""
                                INSERT INTO results (admission_no, subject_name, marks, exam_id)
                                VALUES (?, ?, ?, ?)
                                ON CONFLICT(admission_no, subject_name, exam_id) DO UPDATE SET
                                    marks=excluded.marks
                            """, (str(adm), subject_name, int(marks), exam_id))
                            imported += 1
                        except Exception as e:
                            print(f"[ERROR] Failed to import result for '{adm}': {e}")
                            continue
            
            self.load_students()
            self.load_subjects()
            EventBus.emit("RESULTS_UPDATED")
            QMessageBox.information(self, "Import Complete", f"Imported {imported} marks.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed: {e}")


    def _is_selected_exam_completed(self):
        exam_id = self.exam.currentData()
        if exam_id is None:
            return False

        row = fetch_one(
            "SELECT status FROM exams WHERE id=?",
            (exam_id,),
        )
        return bool(row and row[0] == "COMPLETED")

    def _update_exam_lock_state(self):
        self.exam_read_only = self._is_selected_exam_completed()
        self.save_btn.setEnabled(not self.exam_read_only)
        self.import_btn.setEnabled(not self.exam_read_only)

        if self.exam_read_only:
            self.lock_label.setText(
                "COMPLETED EXAM - read-only results. Reopen from Exams to edit."
            )
            self.lock_label.show()
            self.table.setEditTriggers(
                QAbstractItemView.EditTrigger.NoEditTriggers
            )
        else:
            self.lock_label.hide()
            self.table.setEditTriggers(
                QAbstractItemView.EditTrigger.AllEditTriggers
            )

    def _clear_table(self):
        self._update_exam_lock_state()
        self.loading_table = True
        self.table.setRowCount(0)
        self.loading_table = False
        self.update_summary()
