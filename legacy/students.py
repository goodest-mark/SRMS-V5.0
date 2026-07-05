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
QLabel,
QHeaderView
)

from progress_dialog import ProgressDialog

from database import connect
from system_state import SystemState
from event_bus import EventBus
from class_utils import get_classes

class StudentsPage(QWidget):

 def __init__(self):
    super().__init__()

    self.selected_id = None

    self.layout = QVBoxLayout()
    self.setLayout(self.layout)

    # HEADER
    self.title = QLabel("STUDENTS MODULE")
    self.layout.addWidget(self.title)

    # FORM
    form = QHBoxLayout()

    self.adm = QLineEdit()
    self.adm.setPlaceholderText("Admission No")

    self.name = QLineEdit()
    self.name.setPlaceholderText("Full Name")

    self.gender = QComboBox()
    self.gender.addItems(["Male", "Female"])

    self.class_box = QComboBox()
    self.class_box.addItems(get_classes())

    self.stream = QLineEdit()
    self.stream.setPlaceholderText("Stream (optional)")

    self.save_btn = QPushButton("SAVE")
    self.save_btn.clicked.connect(self.save_student)

    self.clear_btn = QPushButton("CLEAR")
    self.clear_btn.clicked.connect(self.clear_form)

    form.addWidget(self.adm)
    form.addWidget(self.name)
    form.addWidget(self.gender)
    form.addWidget(self.class_box)
    form.addWidget(self.stream)
    form.addWidget(self.save_btn)
    form.addWidget(self.clear_btn)

    self.layout.addLayout(form)

    # SEARCH
    self.search = QLineEdit()
    self.search.setPlaceholderText("Search student...")
    self.search.textChanged.connect(self.load)

    self.layout.addWidget(self.search)

    # TABLE
    self.table = QTableWidget()
    self.table.setColumnCount(5)

    self.table.setHorizontalHeaderLabels([
        "ID",
        "Admission",
        "Name",
        "Gender",
        "Class"
    ])

    self.table.doubleClicked.connect(self.load_selected)

    header = self.table.horizontalHeader()
    header.setSectionResizeMode(
        QHeaderView.ResizeMode.ResizeToContents
    )
    header.setStretchLastSection(True)

    self.layout.addWidget(self.table)

    # EVENTS
    EventBus.subscribe(
        "STUDENTS_UPDATED",
        self.load
    )

    EventBus.subscribe(
        "LEVEL_CHANGED",
        self.on_level_changed
    )

    self.load()

def on_level_changed(self):
    self.refresh_classes()
    self.clear_form()
    self.load()

def refresh_classes(self):

    current = self.class_box.currentText()

    self.class_box.clear()
    self.class_box.addItems(get_classes())

    index = self.class_box.findText(current)

    if index >= 0:
        self.class_box.setCurrentIndex(index)

def load(self):
    pass

def save_student(self):
    pass

def load_selected(self):
    pass

def clear_form(self):

    self.selected_id = None

    self.adm.clear()
    self.name.clear()
    self.stream.clear()

    self.gender.setCurrentIndex(0)

    if self.class_box.count() > 0:
        self.class_box.setCurrentIndex(0)

    self.save_btn.setText("SAVE")
