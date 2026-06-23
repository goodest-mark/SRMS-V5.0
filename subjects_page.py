from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QComboBox,
    QMessageBox,
    QHeaderView,
    QAbstractItemView
)
import openpyxl
import excel_utils

from database import connect
from system_state import SystemState
from event_bus import EventBus
from subject_dialog import SubjectDialog


class SubjectsPage(QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # =====================
        # FORM
        # =====================

        form = QHBoxLayout()

        self.name = QLineEdit()
        self.name.setPlaceholderText(
            "Subject Name"
        )

        self.subject_type = QComboBox()

        self.save_btn = QPushButton(
            "ADD SUBJECT"
        )

        self.save_btn.clicked.connect(
            self.add_subject
        )

        self.delete_btn = QPushButton(
            "DELETE"
        )

        self.delete_btn.clicked.connect(
            self.delete_subject
        )

        self.import_btn = QPushButton("IMPORT")
        self.import_btn.clicked.connect(self.import_excel)
        
        self.export_btn = QPushButton("EXPORT")
        self.export_btn.clicked.connect(self.export_excel)
        
        self.template_btn = QPushButton("TEMPLATE")
        self.template_btn.clicked.connect(self.download_template)

        form.addWidget(self.name)
        form.addWidget(self.subject_type)
        form.addWidget(self.save_btn)
        form.addWidget(self.delete_btn)
        form.addWidget(self.import_btn)
        form.addWidget(self.export_btn)
        form.addWidget(self.template_btn)

        self.layout.addLayout(form)

        # =====================
        # SEARCH
        # =====================

        self.search = QLineEdit()

        self.search.setPlaceholderText(
            "Search subject..."
        )

        self.search.textChanged.connect(
            self.load
        )

        self.layout.addWidget(
            self.search
        )

        # =====================
        # TABLE
        # =====================

        self.table = QTableWidget()

        self.table.setColumnCount(4)

        self.table.setHorizontalHeaderLabels([
            "ID",
            "Subject",
            "Level",
            "Type"
        ])

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.table.doubleClicked.connect(
            self.edit_subject
        )

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.layout.addWidget(
            self.table
        )

        EventBus.subscribe(
            "LEVEL_CHANGED",
            self.on_level_changed
        )

        self.refresh_subject_types()
        self.load()

    # =====================
    # LEVEL CHANGE
    # =====================

    def on_level_changed(self):

        self.refresh_subject_types()
        self.load()

    # =====================
    # SUBJECT TYPES
    # =====================

    def refresh_subject_types(self):

        self.subject_type.clear()

        if SystemState.get_level() == "A_LEVEL":

            self.subject_type.addItems([
                "PRINCIPAL",
                "SUBSIDIARY"
            ])

        else:

            self.subject_type.addItems([
                "COUNTED",
                "NOT_COUNTED"
            ])

    # =====================
    # LOAD
    # =====================

    def load(self):

        conn = connect()
        cur = conn.cursor()

        level = SystemState.get_level()

        search = (
            self.search.text()
            .strip()
        )

        if search:

            cur.execute("""
                SELECT
                    id,
                    subject_name,
                    level,
                    subject_type
                FROM subjects
                WHERE level=?
                AND subject_name LIKE ?
                ORDER BY subject_name
            """, (
                level,
                f"%{search}%"
            ))

        else:

            cur.execute("""
                SELECT
                    id,
                    subject_name,
                    level,
                    subject_type
                FROM subjects
                WHERE level=?
                ORDER BY subject_name
            """, (
                level,
            ))

        rows = cur.fetchall()

        conn.close()

        self.table.setRowCount(
            len(rows)
        )

        for r, row in enumerate(rows):

            for c, value in enumerate(row):

                item = QTableWidgetItem(
                    str(value)
                )

                self.table.setItem(
                    r,
                    c,
                    item
                )

    # =====================
    # ADD SUBJECT
    # =====================

    def add_subject(self):

        name = (
            self.name.text()
            .strip()
        )

        if not name:

            QMessageBox.warning(
                self,
                "Error",
                "Enter subject name"
            )

            return

        conn = connect()
        cur = conn.cursor()

        try:

            cur.execute("""
                INSERT INTO subjects(
                    subject_name,
                    level,
                    subject_type
                )
                VALUES (?, ?, ?)
            """, (
                name,
                SystemState.get_level(),
                self.subject_type.currentText()
            ))

            conn.commit()

            self.name.clear()

            self.load()

        except Exception as e:

            QMessageBox.warning(
                self,
                "Error",
                str(e)
            )

        conn.close()

    # =====================
    # DELETE
    # =====================

    def delete_subject(self):

        row = self.table.currentRow()

        if row < 0:
            return

        subject_id = self.table.item(
            row,
            0
        ).text()

        reply = QMessageBox.question(
            self,
            "Delete",
            "Delete selected subject?",
            QMessageBox.Yes |
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        conn = connect()
        cur = conn.cursor()

        cur.execute("""
            DELETE FROM subjects
            WHERE id=?
        """, (
            subject_id,
        ))

        conn.commit()
        conn.close()

        self.load()

    # =====================
    # EDIT
    # =====================

    def edit_subject(self):

        row = self.table.currentRow()

        if row < 0:
            return

        subject_id = int(
            self.table.item(
                row,
                0
            ).text()
        )

        dlg = SubjectDialog(
            subject_id
        )

        if dlg.exec():
            self.load()

    # =====================
    # EXCEL FRAMEWORK
    # =====================

    def download_template(self):
        excel_utils.download_template(
            self, 
            "subjects_template.xlsx",
            "SUBJECT REGISTRATION FORM",
            ["Subject Name*", "Subject Type*", "Level"],
            samples=["Mathematics", "COUNTED", SystemState.get_level()]
        )

    def export_excel(self):
        conn = connect()
        cur = conn.cursor()
        level = SystemState.get_level()
        cur.execute("SELECT subject_name, subject_type FROM subjects WHERE level=?", (level,))
        data = cur.fetchall()
        conn.close()
        
        excel_utils.export_to_excel(
            self, 
            f"subjects_{level}.xlsx", 
            ["Subject Name", "Subject Type"],
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
            level = SystemState.get_level()
            
            imported = 0
            for row in rows:
                if not row or len(row) < 2 or not row[0]: continue
                
                name = row[0]
                stype = row[1]
                
                try:
                    cur.execute("""
                        INSERT INTO subjects (subject_name, level, subject_type)
                        VALUES (?, ?, ?)
                        ON CONFLICT(subject_name, level) DO UPDATE SET
                            subject_type=excluded.subject_type
                    """, (str(name), level, str(stype)))
                    imported += 1
                except Exception as e:
                    print(f"[ERROR] Failed to import subject '{name}': {e}")
                    continue
                    
            conn.commit()
            conn.close()
            
            self.load()
            QMessageBox.information(self, "Import Complete", f"Imported {imported} subjects.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed: {str(e)}")
