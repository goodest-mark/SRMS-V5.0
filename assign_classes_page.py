from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
    QCheckBox,
    QGridLayout
)

from db_utils import fetch_all, get_cursor
from class_utils import get_classes
from ui_helpers import show_info


class AssignClassesPage(QWidget):

    def __init__(self):
        super().__init__()

        self.teacher_id = None
        self.checkboxes = []

        root = QVBoxLayout(self)

        header = QHBoxLayout()

        self.back_btn = QPushButton("← Back")

        title = QLabel("ASSIGN CLASSES")
        title.setStyleSheet(
            "font-size:18px;font-weight:bold;"
        )

        header.addWidget(self.back_btn)
        header.addStretch()
        header.addWidget(title)

        root.addLayout(header)

        self.grid = QGridLayout()
        root.addLayout(self.grid)

        self.save_btn = QPushButton(
            "SAVE CLASS ASSIGNMENTS"
        )

        root.addWidget(self.save_btn)

        self.save_btn.clicked.connect(
            self.save_assignments
        )

    def set_teacher(self, teacher_id):

        self.teacher_id = teacher_id
        self.load_classes()

    def load_classes(self):

        while self.grid.count():

            item = self.grid.takeAt(0)

            widget = item.widget()

            if widget:
                widget.deleteLater()

        self.checkboxes.clear()

        classes = get_classes()

        row = 0
        col = 0

        for class_name in classes:

            chk = QCheckBox(class_name)

            self.grid.addWidget(
                chk,
                row,
                col
            )

            self.checkboxes.append(chk)

            col += 1

            if col > 2:
                col = 0
                row += 1

        if not self.teacher_id:
            return

        assigned = {
            row[0]
            for row in fetch_all("""
                SELECT class_name
                FROM teacher_classes
                WHERE teacher_id=?
            """, (self.teacher_id,))
        }

        for chk in self.checkboxes:

            if chk.text() in assigned:
                chk.setChecked(True)

    def save_assignments(self):

        if not self.teacher_id:
            return

        with get_cursor(commit=True) as cur:
            cur.execute("""
                DELETE FROM teacher_classes
                WHERE teacher_id=?
            """, (self.teacher_id,))

            for chk in self.checkboxes:
                if chk.isChecked():
                    cur.execute("""
                        INSERT INTO teacher_classes(
                            teacher_id,
                            class_name
                        )
                        VALUES (?,?)
                    """, (
                        self.teacher_id,
                        chk.text()
                    ))

        show_info(self, "Class assignments saved.")

