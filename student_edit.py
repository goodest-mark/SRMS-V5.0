from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QTextEdit,
    QPushButton, QComboBox, QMessageBox
)

from progress_dialog import ProgressDialog
from db_utils import execute
from ui_helpers import show_info


class EditStudentWindow(QWidget):

    def __init__(self, student_data, refresh_callback):
        super().__init__()

        self.student_data = student_data
        self.refresh_callback = refresh_callback

        self.setWindowTitle("Edit Student")
        self.resize(400, 400)

        layout = QVBoxLayout()

        # DATA FIELDS
        self.admission = QLineEdit()
        self.admission.setText(student_data[1])
        self.admission.setReadOnly(True)

        self.exam_no = QLineEdit()
        self.exam_no.setText(student_data[2] if len(student_data) > 2 and student_data[2] else "")
        self.exam_no.setPlaceholderText("Exam No (Optional)")

        self.name = QLineEdit()
        self.name.setText(student_data[3])

        self.gender = QComboBox()
        self.gender.addItems(["Male", "Female"])
        self.gender.setCurrentText(student_data[4])

        self.class_box = QComboBox()
        self.class_box.addItems([
            "Form I", "Form II", "Form III",
            "Form IV", "Form V", "Form VI"
        ])
        self.class_box.setCurrentText(student_data[5])

        self.stream = QLineEdit()
        self.stream.setText(student_data[6])

        self.comment = QTextEdit()
        self.comment.setPlaceholderText("Comments / Remarks")
        self.comment.setPlainText(student_data[7] if len(student_data) > 7 and student_data[7] else "")

        self.btn = QPushButton("UPDATE")
        self.btn.clicked.connect(self.update_student)

        layout.addWidget(self.admission)
        layout.addWidget(self.exam_no)
        layout.addWidget(self.name)
        layout.addWidget(self.gender)
        layout.addWidget(self.class_box)
        layout.addWidget(self.stream)
        layout.addWidget(self.comment)
        layout.addWidget(self.btn)

        self.setLayout(layout)

    def update_student(self):
        execute("""
            UPDATE students
            SET exam_no=?, full_name=?, gender=?, class=?, stream=?, comments=?
            WHERE admission_no=?
        """, (
            self.exam_no.text(),
            self.name.text(),
            self.gender.currentText(),
            self.class_box.currentText(),
            self.stream.text(),
            self.comment.toPlainText(),
            self.admission.text()
        ))

        self.refresh_callback()

        show_info(self, "Student Updated")
        self.close()
