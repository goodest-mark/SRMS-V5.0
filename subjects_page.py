from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QComboBox,
    QMessageBox,
    QScrollArea,
    QFrame,
    QSizePolicy,
)

from PySide6.QtCore import Qt

from progress_dialog import ProgressDialog
import openpyxl
import excel_utils

from academic_rules import allowed_subject_types
from db_utils import get_cursor, fetch_all
from table_utils import setup_table, populate_table
from ui_helpers import confirm_action, show_error, get_subject_short_name
from system_state import SystemState
from event_bus import EventBus
from subject_dialog import SubjectDialog
from security_settings import authorize_action


class SubjectsPage(QWidget):

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
        setup_table(self.table, ["ID", "Subject", "Level", "Type"])
        self.table.doubleClicked.connect(self.edit_subject)
        
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

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
        self.subject_type.addItems(
        allowed_subject_types(SystemState.get_level())
        )        

    # =====================
    # LOAD
    # =====================

    def load(self):

        level = SystemState.get_level()
        search = self.search.text().strip()

        if search:
            rows = fetch_all("""
                SELECT id, subject_name, level, subject_type
                FROM subjects
                WHERE level=? AND subject_name LIKE ?
                ORDER BY subject_name
            """, (level, f"%{search}%"))
        else:
            rows = fetch_all("""
                SELECT id, subject_name, level, subject_type
                FROM subjects
                WHERE level=?
                ORDER BY subject_name
            """, (level,))

        populate_table(self.table, rows)
        self._update_table_height()

    def _update_table_height(self):
        self.table.resizeRowsToContents()
        height = (
            self.table.horizontalHeader().height()
            + self.table.verticalHeader().length()
            + self.table.frameWidth() * 2
            + 4
        )
        self.table.setFixedHeight(height)

    # =====================
    # ADD SUBJECT
    # =====================

    def add_subject(self):

        name = self.name.text().strip()

        if not name:
            show_error(self, "Enter subject name")
            return

        try:
            with get_cursor(commit=True) as cur:
                cur.execute("""
                    INSERT INTO subjects(subject_name, subject_short_name, level, subject_type)
                    VALUES (?, ?, ?, ?)
                """, (name, get_subject_short_name(name), SystemState.get_level(), self.subject_type.currentText()))

            self.name.clear()
            self.load()
            EventBus.emit("SUBJECTS_UPDATED")

        except Exception as e:
            show_error(self, str(e))

    # =====================
    # DELETE
    # =====================

    def delete_subject(self):

        row = self.table.currentRow()

        if row < 0:
            return

        subject_id = self.table.item(row, 0).text()

        if not confirm_action(self, "Delete", "Delete selected subject?"):
            return

        if not authorize_action(self, "Delete Subject"):
            return

        with get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM subjects WHERE id=?", (subject_id,))

        self.load()
        EventBus.emit("SUBJECTS_UPDATED")

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
            EventBus.emit("SUBJECTS_UPDATED")

    # =====================
    # EXCEL FRAMEWORK
    # =====================

    def download_template(self):
        level = SystemState.get_level()
        excel_utils.download_template(
            self, 
            "subjects_template.xlsx",
            f"SUBJECT REGISTRATION FORM - {level}",
            ["Subject Name*", "Subject Type*", "Level"],
            instructions=[
                f"1. Template generated for Level: {level}.",
                "2. Do not modify the column headers in Row 10.",
                "3. Start data entry from Row 12.",
                "4. Subject Type should be COUNTED, PRINCIPAL, or another configured type.",
                "5. Level must match the selected system level on the page.",
            ],
            samples=["Mathematics", "COUNTED", SystemState.get_level()]
        )

    def export_excel(self):
        level = SystemState.get_level()
        data = fetch_all("SELECT subject_name, subject_type FROM subjects WHERE level=?", (level,))
        
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
            level = SystemState.get_level()
            
            imported = 0
            with get_cursor(commit=True) as cur:
                for row in rows:
                    if not row or len(row) < 2 or not row[0]: continue
                    
                    name = row[0]
                    stype = row[1]
                    
                    try:
                        cur.execute("""
                            INSERT INTO subjects (subject_name, subject_short_name, level, subject_type)
                            VALUES (?, ?, ?, ?)
                            ON CONFLICT(subject_name, level) DO UPDATE SET
                                subject_type=excluded.subject_type,
                                subject_short_name=excluded.subject_short_name
                        """, (str(name), get_subject_short_name(str(name)), level, str(stype)))
                        imported += 1
                    except Exception as e:
                        print(f"[ERROR] Failed to import subject '{name}': {e}")
                        continue
            
            self.load()
            EventBus.emit("SUBJECTS_UPDATED")
            QMessageBox.information(self, "Import Complete", f"Imported {imported} subjects.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", "Import failed. Please check the file format and try again.")
