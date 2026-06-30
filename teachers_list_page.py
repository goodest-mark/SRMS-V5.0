from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QTableWidget,
    QMessageBox,
    QComboBox,
    QFileDialog
)

from progress_dialog import ProgressDialog


import pandas as pd

from db_utils import get_cursor, fetch_all
from table_utils import setup_table, populate_table
from ui_helpers import show_error, show_info
from database import connect
from system_state import SystemState
from event_bus import EventBus


class TeachersListPage(QWidget):

    def __init__(self):
        super().__init__()

        self.selected_teacher_id = None

        layout = QVBoxLayout(self)

        title = QLabel("TEACHERS MANAGEMENT")
        title.setStyleSheet("""
            font-size:18px;
            font-weight:bold;
        """)
        layout.addWidget(title)

        form = QHBoxLayout()

        self.teacher_no = QLineEdit()
        self.teacher_no.setPlaceholderText("Teacher No")

        self.full_name = QLineEdit()
        self.full_name.setPlaceholderText("Full Name")

        self.gender = QComboBox()
        self.gender.addItems(["Male", "Female"])

        self.phone = QLineEdit()
        self.phone.setPlaceholderText("Phone")

        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")

        self.save_btn = QPushButton("SAVE")
        self.save_btn.clicked.connect(self.save_teacher)

        self.clear_btn = QPushButton("CLEAR")
        self.clear_btn.clicked.connect(self.clear_form)

        form.addWidget(self.teacher_no)
        form.addWidget(self.full_name)
        form.addWidget(self.gender)
        form.addWidget(self.phone)
        form.addWidget(self.email)
        form.addWidget(self.save_btn)
        form.addWidget(self.clear_btn)

        layout.addLayout(form)

        action_bar = QHBoxLayout()

        self.import_btn = QPushButton("IMPORT EXCEL")
        self.template_btn = QPushButton("EXPORT TEMPLATE")
        self.export_btn = QPushButton("EXPORT TEACHERS")
        self.refresh_btn = QPushButton("REFRESH")

        self.import_btn.clicked.connect(self.import_excel)
        self.template_btn.clicked.connect(self.export_template)
        self.export_btn.clicked.connect(self.export_teachers)
        self.refresh_btn.clicked.connect(self.load)

        action_bar.addWidget(self.import_btn)
        action_bar.addWidget(self.template_btn)
        action_bar.addWidget(self.export_btn)
        action_bar.addWidget(self.refresh_btn)

        layout.addLayout(action_bar)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search teacher...")
        self.search.textChanged.connect(self.load)

        layout.addWidget(self.search)

        self.table = QTableWidget()
        setup_table(self.table, [
            "ID", "Teacher No", "Full Name",
            "Gender", "Phone", "Email", "Status"
        ])
        self.table.doubleClicked.connect(self.load_selected)

        layout.addWidget(self.table)

        EventBus.subscribe(
            "TEACHERS_UPDATED",
            self.load
        )

        EventBus.subscribe(
            "LEVEL_CHANGED",
            self.load
        )

        self.load()

    def load(self):

        search = self.search.text().strip()

        if search:
            rows = fetch_all("""
                SELECT id, teacher_no, full_name, gender, phone, email, status
                FROM teachers
                WHERE teacher_no LIKE ? OR full_name LIKE ?
                ORDER BY id DESC
            """, (f"%{search}%", f"%{search}%"))
        else:
            rows = fetch_all("""
                SELECT id, teacher_no, full_name, gender, phone, email, status
                FROM teachers
                ORDER BY id DESC
            """)

        populate_table(self.table, rows)

    def save_teacher(self):

        teacher_no = self.teacher_no.text().strip()
        full_name = self.full_name.text().strip()
        gender = self.gender.currentText()
        phone = self.phone.text().strip()
        email = self.email.text().strip()

        if not teacher_no or not full_name:
            show_error(self, "Teacher No and Name required")
            return

        level = SystemState.get_level()

        try:
            with get_cursor(commit=True) as cur:
                if self.selected_teacher_id:
                    cur.execute("""
                        UPDATE teachers
                        SET teacher_no=?, full_name=?, gender=?, phone=?, email=?
                        WHERE id=?
                    """, (teacher_no, full_name, gender, phone, email, self.selected_teacher_id))
                else:
                    cur.execute("""
                        INSERT INTO teachers(teacher_no, full_name, gender, phone, email, status, level)
                        VALUES(?,?,?,?,?,?,?)
                    """, (teacher_no, full_name, gender, phone, email, "ACTIVE", level))

            EventBus.emit("TEACHERS_UPDATED")
            self.clear_form()

        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))

    def export_template(self):

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Template", "teachers_template.xlsx", "Excel Files (*.xlsx)"
        )

        if not path:
            return

        df = pd.DataFrame([{
            "Teacher No": "T001",
            "Full Name": "Ali Salum",
            "Gender": "Male",
            "Phone": "0712345678",
            "Email": "ali@example.com"
        }])

        df.to_excel(path, index=False)
        show_info(self, "Template exported successfully.")

    def export_teachers(self):

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Teachers", "teachers_export.xlsx", "Excel Files (*.xlsx)"
        )

        if not path:
            return

        conn = connect()
        df = pd.read_sql_query("""
            SELECT teacher_no, full_name, gender, phone, email, status, level
            FROM teachers
        """, conn)
        conn.close()

        df.to_excel(path, index=False)
        show_info(self, "Teachers exported successfully.")

    def import_excel(self):

        path, _ = QFileDialog.getOpenFileName(
            self, "Import Teachers", "", "Excel Files (*.xlsx)"
        )

        if not path:
            return

        try:
            df = pd.read_excel(path)
            level = SystemState.get_level()

            with get_cursor(commit=True) as cur:
                for _, row in df.iterrows():
                    teacher_no = str(row.get("Teacher No", "")).strip()
                    full_name = str(row.get("Full Name", "")).strip()
                    gender = str(row.get("Gender", "")).strip()
                    phone = str(row.get("Phone", "")).strip()
                    email = str(row.get("Email", "")).strip()

                    if not teacher_no or not full_name:
                        continue

                    cur.execute("""
                        INSERT OR IGNORE INTO teachers(
                            teacher_no, full_name, gender, phone, email, status, level
                        ) VALUES(?,?,?,?,?,?,?)
                    """, (teacher_no, full_name, gender, phone, email, "ACTIVE", level))

            self.load()
            show_info(self, "Teachers imported successfully.")

        except Exception as error:
            QMessageBox.critical(self, "Import Error", str(error))

    def load_selected(self):
        row = self.table.currentRow()

        if row < 0:
            return

        self.selected_teacher_id = int(
            self.table.item(row, 0).text()
        )

        self.teacher_no.setText(
            self.table.item(row, 1).text()
        )

        self.full_name.setText(
            self.table.item(row, 2).text()
        )

        self.gender.setCurrentText(
            self.table.item(row, 3).text()
        )

        self.phone.setText(
            self.table.item(row, 4).text()
        )

        self.email.setText(
            self.table.item(row, 5).text()
        )

        self.save_btn.setText("UPDATE")

    def clear_form(self):

        self.selected_teacher_id = None

        self.teacher_no.clear()
        self.full_name.clear()
        self.phone.clear()
        self.email.clear()

        self.gender.setCurrentIndex(0)

        self.save_btn.setText("SAVE")
