from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
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
)

import sqlite3

from class_utils import get_classes
from database import connect
from event_bus import EventBus
from system_state import SystemState
import openpyxl
import excel_utils
from student_profile import StudentProfile


class StudentsPage(QWidget):

    def __init__(self):
        super().__init__()

        self.selected_id = None

        layout = QVBoxLayout(self)

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

        self.save_btn = QPushButton("SAVE")
        self.save_btn.clicked.connect(self.save_student)

        self.delete_btn = QPushButton("DELETE")
        self.delete_btn.clicked.connect(self.delete_student)
        self.delete_btn.setEnabled(False)

        self.clear_btn = QPushButton("CLEAR")
        self.clear_btn.clicked.connect(self.clear_form)

        self.import_btn = QPushButton("IMPORT")
        self.import_btn.clicked.connect(self.import_excel)
        
        self.export_btn = QPushButton("EXPORT")
        self.export_btn.clicked.connect(self.export_excel)
        
        self.template_btn = QPushButton("TEMPLATE")
        self.template_btn.clicked.connect(self.download_template)

        self.view_profile_btn = QPushButton("VIEW PROFILE")
        self.view_profile_btn.clicked.connect(self.view_profile)
        self.view_profile_btn.setEnabled(False)
        self.view_profile_btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")

        form.addWidget(self.adm)
        form.addWidget(self.name)
        form.addWidget(self.gender)
        form.addWidget(self.class_box)
        form.addWidget(self.stream)
        form.addWidget(self.save_btn)
        form.addWidget(self.delete_btn)
        form.addWidget(self.view_profile_btn)
        form.addWidget(self.clear_btn)
        form.addWidget(self.import_btn)
        form.addWidget(self.export_btn)
        form.addWidget(self.template_btn)

        layout.addLayout(form)

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
        self.table.doubleClicked.connect(self.load_selected)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        header.setStretchLastSection(True)

        layout.addWidget(self.table)

        EventBus.subscribe("STUDENTS_UPDATED", self.load)
        EventBus.subscribe("LEVEL_CHANGED", self.on_level_changed)

        self.refresh_classes()
        self.load()

    def on_level_changed(self):
        self.clear_form()
        self.refresh_classes()
        self.load()

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
        conn = connect()

        try:
            cur = conn.cursor()
            level = SystemState.get_level()
            search_text = self.search.text().strip()

            if search_text:
                pattern = f"%{search_text}%"
                cur.execute("""
                    SELECT id,
                           admission_no,
                           full_name,
                           gender,
                           class,
                           stream,
                           level
                    FROM students
                    WHERE level=?
                      AND (
                          admission_no LIKE ?
                          OR full_name LIKE ?
                          OR class LIKE ?
                          OR COALESCE(stream, '') LIKE ?
                      )
                    ORDER BY id DESC
                """, (
                    level,
                    pattern,
                    pattern,
                    pattern,
                    pattern,
                ))
            else:
                cur.execute("""
                    SELECT id,
                           admission_no,
                           full_name,
                           gender,
                           class,
                           stream,
                           level
                    FROM students
                    WHERE level=?
                    ORDER BY id DESC
                """, (level,))

            rows = cur.fetchall()
        finally:
            conn.close()

        self.table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            for column, value in enumerate(row):
                text = "" if value is None else str(value)
                item = QTableWidgetItem(text)
                item.setToolTip(text)
                self.table.setItem(row_index, column, item)

    def save_student(self):
        admission_no = self.adm.text().strip()
        full_name = self.name.text().strip()
        gender = self.gender.currentText().strip()
        class_name = self.class_box.currentText().strip()
        stream = self.stream.text().strip()
        level = SystemState.get_level()

        if not admission_no or not full_name or not class_name:
            QMessageBox.warning(
                self,
                "Required Fields",
                "Admission number, full name and class are required.",
            )
            return

        conn = connect()

        try:
            cur = conn.cursor()

            if self.selected_id is None:
                cur.execute("""
                    INSERT INTO students (
                        admission_no,
                        full_name,
                        gender,
                        class,
                        stream,
                        level
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    admission_no,
                    full_name,
                    gender,
                    class_name,
                    stream,
                    level,
                ))
            else:
                cur.execute("""
                    UPDATE students
                    SET admission_no=?,
                        full_name=?,
                        gender=?,
                        class=?,
                        stream=?,
                        level=?
                    WHERE id=?
                """, (
                    admission_no,
                    full_name,
                    gender,
                    class_name,
                    stream,
                    level,
                    self.selected_id,
                ))

            conn.commit()

        except sqlite3.IntegrityError:
            QMessageBox.warning(
                self,
                "Duplicate Admission Number",
                "That admission number is already registered.",
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                "Database Error",
                str(error),
            )
            return
        finally:
            conn.close()

        self.clear_form()
        EventBus.emit("STUDENTS_UPDATED")

    def load_selected(self):
        row = self.table.currentRow()

        if row < 0:
            return

        self.selected_id = int(self.table.item(row, 0).text())
        self.adm.setText(self.table.item(row, 1).text())
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

        self.save_btn.setText("UPDATE")
        self.delete_btn.setEnabled(True)
        self.view_profile_btn.setEnabled(True)

    def view_profile(self):
        if self.selected_id is None:
            return
            
        row = self.table.currentRow()
        admission_no = self.table.item(row, 1).text()
        level = SystemState.get_level()
        
        dlg = StudentProfile(admission_no, level)
        dlg.exec()

    def delete_student(self):
        if self.selected_id is None:
            QMessageBox.warning(
                self,
                "Delete Student",
                "Double-click a student before deleting.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Delete Student",
            "Are you sure you want to delete this student?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        conn = connect()

        try:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM students WHERE id=?",
                (self.selected_id,),
            )
            conn.commit()
        except Exception as error:
            QMessageBox.critical(
                self,
                "Database Error",
                str(error),
            )
            return
        finally:
            conn.close()

        self.clear_form()
        EventBus.emit("STUDENTS_UPDATED")

    def clear_form(self):
        self.selected_id = None

        self.adm.clear()
        self.name.clear()
        self.stream.clear()
        self.gender.setCurrentIndex(0)

        if self.class_box.count() > 0:
            self.class_box.setCurrentIndex(0)

        self.table.clearSelection()
        self.save_btn.setText("SAVE")
        self.delete_btn.setEnabled(False)
        self.view_profile_btn.setEnabled(False)

    # =========================
    # EXCEL FRAMEWORK
    # =========================

    def download_template(self):
        excel_utils.download_template(
            self, 
            "students_template.xlsx",
            "STUDENT REGISTRATION FORM",
            ["Admission No*", "Full Name*", "Gender*", "Class*", "Stream", "Level"],
            samples=["2024/001", "John Doe", "Male", "Form I", "A", SystemState.get_level()]
        )

    def export_excel(self):
        conn = connect()
        cur = conn.cursor()
        level = SystemState.get_level()
        cur.execute("SELECT admission_no, full_name, gender, class, stream FROM students WHERE level=?", (level,))
        data = cur.fetchall()
        conn.close()
        
        excel_utils.export_to_excel(
            self, 
            f"students_{level}.xlsx", 
            ["Admission No", "Full Name", "Gender", "Class", "Stream"],
            data
        )

    def import_excel(self):
        path = excel_utils.get_import_file(self)
        if not path: return
        
        try:
            wb = openpyxl.load_workbook(path, data_only=True)
            sheet = wb.active
            rows = list(sheet.iter_rows(min_row=12, values_only=True))
            
            conn = connect()
            cur = conn.cursor()

            imported = 0
            updated = 0
            rejected = 0

            o_classes = ["Form I", "Form II", "Form III", "Form IV"]
            a_classes = ["Form V", "Form VI"]

            for row in rows:
                # Skip empty rows or rows missing admission number
                if not row or not row[0]:
                    continue

                # Ensure row has enough columns
                if len(row) < 6:
                    rejected += 1
                    continue

                adm = str(row[0]).strip()
                name = str(row[1] or "").strip()
                gender = str(row[2] or "").strip()
                cls = str(row[3] or "").strip()
                stream = str(row[4] or "").strip()
                level_excel = str(row[5] or "").strip().upper()

                # Validate Required Fields
                if not name or not cls or not level_excel:
                    rejected += 1
                    continue

                # Validate Level vs Class Combination
                is_valid = False
                if level_excel == "O_LEVEL" and cls in o_classes:
                    is_valid = True
                elif level_excel == "A_LEVEL" and cls in a_classes:
                    is_valid = True

                if not is_valid:
                    rejected += 1
                    continue
                
                try:
                    # Check if student exists for summary counting
                    cur.execute("SELECT 1 FROM students WHERE admission_no=?", (adm,))
                    exists = cur.fetchone()

                    cur.execute("""
                        INSERT INTO students (admission_no, full_name, gender, class, stream, level)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(admission_no) DO UPDATE SET
                            full_name=excluded.full_name,
                            gender=excluded.gender,
                            class=excluded.class,
                            stream=excluded.stream,
                            level=excluded.level
                    """, (adm, name, gender, cls, stream, level_excel))
                    
                    if exists:
                        updated += 1
                    else:
                        imported += 1
                except Exception as e:
                    print(f"[ERROR] Failed to import student '{adm}': {e}")
                    rejected += 1
                    continue
                    
            conn.commit()
            conn.close()
            
            self.load()
            EventBus.emit("STUDENTS_UPDATED")
            QMessageBox.information(self, "Import Complete", 
                                  f"Operation Summary:\n"
                                  f"- New Students Imported: {imported}\n"
                                  f"- Existing Records Updated: {updated}\n"
                                  f"- Records Rejected (Invalid Data): {rejected}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed: {str(e)}")
