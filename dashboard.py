from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHBoxLayout,
    QAbstractItemView,
    QHeaderView
)

from progress_dialog import ProgressDialog

from PySide6.QtCore import Qt

from db_utils import fetch_all, fetch_one, execute
from ui_helpers import show_error, confirm_action

# Legacy / unused module imports mocked to prevent ImportError
AddStudentWindow = None
SubjectsWindow = None
ExamsWindow = None
ResultsWindow = None

from theme import APP_STYLE


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("SRMS V5 - Dashboard")

        self.resize(1200, 700)

        self.setStyleSheet(APP_STYLE)

        # =========================
        # CENTRAL WIDGET
        # =========================

        self.central = QWidget()
        self.layout = QVBoxLayout()

        # =========================
        # TOP BAR
        # =========================

        top = QHBoxLayout()

        self.add_btn = QPushButton("ADD STUDENT")
        self.add_btn.clicked.connect(self.open_add)

        self.subject_btn = QPushButton("SUBJECTS")
        self.subject_btn.clicked.connect(self.open_subjects)

        self.exam_btn = QPushButton("EXAMS")
        self.exam_btn.clicked.connect(self.open_exams)

        self.results_btn = QPushButton("RESULTS")
        self.results_btn.clicked.connect(self.open_results)

        self.refresh_btn = QPushButton("REFRESH")
        self.refresh_btn.clicked.connect(self.load_data)

        self.delete_btn = QPushButton("DELETE")
        self.delete_btn.clicked.connect(self.delete_student)

        # ADD TO TOP BAR
        top.addWidget(self.add_btn)
        top.addWidget(self.subject_btn)
        top.addWidget(self.exam_btn)
        top.addWidget(self.results_btn)
        top.addWidget(self.refresh_btn)
        top.addWidget(self.delete_btn)

        # =========================
        # SEARCH
        # =========================

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search student...")
        self.search.textChanged.connect(self.load_data)

        # =========================
        # TABLE
        # =========================

        self.table = QTableWidget()

        self.table.setColumnCount(7)

        self.table.setHorizontalHeaderLabels([
            "ID",
            "Admission No",
            "Exam No",
            "Full Name",
            "Gender",
            "Class",
            "Stream"
        ])

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.table.setWordWrap(False)

        self.table.setTextElideMode(Qt.ElideNone)

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.table.verticalHeader().setDefaultSectionSize(40)

        self.table.setAlternatingRowColors(True)

        self.table.cellDoubleClicked.connect(
            self.open_edit
        )

        # =========================
        # LAYOUT
        # =========================

        self.layout.addLayout(top)
        self.layout.addWidget(self.search)
        self.layout.addWidget(self.table)

        self.central.setLayout(self.layout)

        self.setCentralWidget(self.central)

        self.load_data()

    # =========================
    # LOAD STUDENTS
    # =========================

    def load_data(self):
        text = self.search.text()

        if text:
            rows = fetch_all("""
                SELECT id, admission_no, exam_no, full_name, gender, class, stream
                FROM students
                WHERE full_name LIKE ? OR admission_no LIKE ?
                ORDER BY id DESC
            """, (f"%{text}%", f"%{text}%"))
        else:
            rows = fetch_all("""
                SELECT id, admission_no, exam_no, full_name, gender, class, stream
                FROM students
                ORDER BY id DESC
            """)

        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(value)))

    # =========================
    # ADD STUDENT
    # =========================

    def open_add(self):
        self.win = AddStudentWindow()
        self.win.show()

    # =========================
    # SUBJECTS
    # =========================

    def open_subjects(self):
        self.sub_win = SubjectsWindow()
        self.sub_win.show()

    # =========================
    # EXAMS
    # =========================

    def open_exams(self):
        self.exam_win = ExamsWindow()
        self.exam_win.show()

    # =========================
    # RESULTS
    # =========================

    def open_results(self):
        self.res_win = ResultsWindow()
        self.res_win.show()

    # =========================
    # EDIT STUDENT
    # =========================

    def open_edit(self, row, col):

        admission = self.table.item(row, 1).text()

        student = fetch_one("""
            SELECT id, admission_no, exam_no, full_name, gender, class, stream, comments
            FROM students
            WHERE admission_no=?
        """, (admission,))

        if student:
            self.edit_win = EditStudentWindow(student, self.load_data)
            self.edit_win.show()

    # =========================
    # DELETE STUDENT
    # =========================

    def delete_student(self):

        row = self.table.currentRow()

        if row < 0:
            show_error(self, "Select student first")
            return

        admission = self.table.item(row, 1).text()

        if confirm_action(self, "Delete", f"Delete {admission}?"):
            execute("DELETE FROM students WHERE admission_no=?", (admission,))
            self.load_data()
