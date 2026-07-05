from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QMessageBox
)

from progress_dialog import ProgressDialog

from db_utils import fetch_one, get_cursor
from ui_helpers import show_error, show_info, get_subject_short_name


class SubjectDialog(QDialog):

    def __init__(self, subject_id):
        super().__init__()

        self.subject_id = subject_id

        self.setWindowTitle("Edit Subject")
        self.resize(420, 280)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Subject Name"))

        self.name = QLineEdit()
        layout.addWidget(self.name)

        layout.addWidget(QLabel("Level"))

        self.level = QComboBox()
        self.level.addItems([
            "O_LEVEL",
            "A_LEVEL"
        ])

        self.level.currentTextChanged.connect(
            self.refresh_types
        )

        layout.addWidget(self.level)

        layout.addWidget(QLabel("Subject Type"))

        self.subject_type = QComboBox()
        layout.addWidget(self.subject_type)

        self.save_btn = QPushButton(
            "SAVE CHANGES"
        )

        self.save_btn.clicked.connect(
            self.save_changes
        )

        layout.addWidget(self.save_btn)

        self.setLayout(layout)

        self.load_subject()

    def refresh_types(self):

        self.subject_type.clear()

        if self.level.currentText() == "A_LEVEL":

            self.subject_type.addItems([
                "PRINCIPAL",
                "SUBSIDIARY"
            ])

        else:

            self.subject_type.addItems([
                "COUNTED",
                "NOT_COUNTED"
            ])

    def load_subject(self):

        row = fetch_one("""
            SELECT
                subject_name,
                level,
                subject_type
            FROM subjects
            WHERE id=?
        """, (self.subject_id,))

        if not row:
            return

        self.name.setText(row[0])

        self.level.setCurrentText(row[1])

        self.refresh_types()

        if row[2]:
            self.subject_type.setCurrentText(
                row[2]
            )

    def save_changes(self):

        name = self.name.text().strip()

        if not name:
            show_error(self, "Subject name required")
            return

        try:
            with get_cursor(commit=True) as cur:
                cur.execute("""
                    UPDATE subjects
                    SET
                        subject_name=?,
                        subject_short_name=?,
                        level=?,
                        subject_type=?
                    WHERE id=?
                """, (
                    name,
                    get_subject_short_name(name),
                    self.level.currentText(),
                    self.subject_type.currentText(),
                    self.subject_id
                ))

            show_info(self, "Subject updated")
            self.accept()

        except Exception as e:
            show_error(self, str(e))
