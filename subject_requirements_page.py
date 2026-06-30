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

        title = QLabel("SUBJECT REQUIREMENTS")
        title.setStyleSheet("""
            font-size:22px;
            font-weight:bold;
            color:#60a5fa;
            padding:8px;
        """)
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

        self.save_btn.setStyleSheet(
            "background:#10b981;font-weight:bold;padding:8px;"
        )

        self.reset_btn.setStyleSheet(
            "background:#ef4444;font-weight:bold;padding:8px;"
        )

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

        for level, req, best in rows:

            if level == "O_LEVEL":
                self.o_required.setValue(req)
                self.o_best.setValue(best)

            elif level == "A_LEVEL":
                self.a_required.setValue(req)
                self.a_best.setValue(best)

    def save_rules(self):

        execute_many("""
            UPDATE subject_requirements
            SET
                required_subjects=?,
                best_of=?
            WHERE level=?
        """,[
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

