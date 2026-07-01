from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QMessageBox,
    QHBoxLayout,
)

from progress_dialog import ProgressDialog

from db_utils import fetch_all, execute_many
from event_bus import EventBus


class SubjectRequirementsPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20,20,20,20)
        layout.setSpacing(15)

        title = QLabel("SUBJECT REQUIREMENTS")
        title.setProperty("variant", "accent")
        layout.addWidget(title)

        form = QFormLayout()

        self.o_required = QSpinBox()
        self.o_required.setRange(1,20)

        self.o_best = QSpinBox()
        self.o_best.setRange(1,20)

        self.a_required = QSpinBox()
        self.a_required.setRange(1,10)

        self.a_best = QSpinBox()
        self.a_best.setRange(1,10)

        form.addRow("O-Level Required Subjects", self.o_required)
        form.addRow("O-Level Best Of", self.o_best)
        form.addRow("A-Level Required Subjects", self.a_required)
        form.addRow("A-Level Best Of", self.a_best)

        layout.addLayout(form)

        buttons = QHBoxLayout()

        self.save_btn = QPushButton("SAVE")
        self.reset_btn = QPushButton("RESTORE")

        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.reset_btn)

        layout.addStretch()
        layout.addLayout(buttons)

        self.save_btn.clicked.connect(self.save_rules)
        self.reset_btn.clicked.connect(self.load_rules)

        self.load_rules()

    def load_rules(self):

        rows = fetch_all("""
            SELECT
                level,
                required_subjects,
                best_of
            FROM subject_requirements
        """)

        if not rows:
            self.o_required.setValue(7)
            self.o_best.setValue(7)
            self.a_required.setValue(3)
            self.a_best.setValue(3)
            return

        for level, req, best in rows:

            if level == "O_LEVEL":
                self.o_required.setValue(req)
                self.o_best.setValue(best)

            elif level == "A_LEVEL":
                self.a_required.setValue(req)
                self.a_best.setValue(best)

    def save_rules(self):

        execute_many("""
            INSERT INTO subject_requirements (
                required_subjects,
                best_of,
                level
            ) VALUES (?, ?, ?)
            ON CONFLICT(level) DO UPDATE SET
                required_subjects=excluded.required_subjects,
                best_of=excluded.best_of
        """, [
            (
                self.o_required.value(),
                self.o_best.value(),
                "O_LEVEL"
            ),
            (
                self.a_required.value(),
                self.a_best.value(),
                "A_LEVEL"
            )
        ])

        EventBus.emit(
            "SUBJECT_REQUIREMENTS_CHANGED"
        )

        QMessageBox.information(
            self,
            "Saved",
            "Subject requirements updated."
        )
