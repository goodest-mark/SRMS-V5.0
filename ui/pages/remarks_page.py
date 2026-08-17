from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView, QAbstractItemView, QScrollArea, QSizePolicy,
    QFrame, QPushButton, QMessageBox, QProgressBar
)
from db_utils import fetch_all, get_cursor
from system_state import SystemState
from event_bus import EventBus
from ranking_engine import compute_student_scores
from remarks_utils import get_default_remark, get_headteacher_remark, get_academic_master_remark, get_discipline_master_remark
import traceback


class RemarksWorker(QThread):
    # Include the level used to calculate scores so the UI applies defaults
    # against the same context the worker queried.
    finished = Signal(list, dict, str)
    error = Signal(str)

    def __init__(self, exam_id, class_name, level):
        super().__init__()
        self.exam_id = exam_id
        self.class_name = class_name
        self.level = level

    def run(self):
        try:
            query = """
                SELECT 
                    s.admission_no, 
                    s.full_name,
                    er.teacher_remarks,
                    er.headteacher_remarks,
                    er.academic_master_remarks,
                    er.discipline_master_remarks
                FROM students s
                LEFT JOIN exam_remarks er ON s.admission_no = er.admission_no AND er.exam_id = ?
                WHERE s.class = ? AND s.level = ?
                ORDER BY s.full_name
            """
            rows = fetch_all(query, (self.exam_id, self.class_name, self.level))
            scores = compute_student_scores(self.level, self.exam_id, self.class_name)
            score_map = {str(s["admission"]): s for s in scores}
            self.finished.emit(rows, score_map, self.level)
        except Exception as e:
            self.error.emit(f"Failed to load remarks: {e}\n{traceback.format_exc()}")


class RemarksPage(QWidget):
    def __init__(self):
        super().__init__()
        self._needs_refresh = False
        self.history_exam_id = None
        self.history_class_name = None
        self.history_level = None
        self._worker = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        root.addWidget(self.scroll_area, 1)

        content = QWidget()
        self.scroll_area.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.title = QLabel("EXAM REMARKS & NOTES")
        self.title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.title)

        self.context_label = QLabel("Select an exam and class to enter remarks.")
        layout.addWidget(self.context_label)

        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 0)
        self.loading_bar.setFormat("Loading remarks...")
        self.loading_bar.setVisible(False)
        layout.addWidget(self.loading_bar)

        controls = QHBoxLayout()
        self.save_all_btn = QPushButton("SAVE ALL REMARKS")
        self.save_all_btn.setStyleSheet("background-color: #2E7D32; color: white; padding: 8px;")
        self.save_all_btn.clicked.connect(self.save_all)
        controls.addWidget(self.save_all_btn)
        controls.addStretch()
        layout.addLayout(controls)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Admission No", "Name", "Teacher Remarks",
            "Headmaster / Headmistress Remarks", "Academic Master / Mistress Remarks",
            "Discipline Master / Mistress Remarks"
        ])
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)

        layout.addWidget(self.table)
        self.table.itemChanged.connect(self._on_item_changed)

        self._show_placeholder("Select a valid exam and class.")

        EventBus.subscribe("LEVEL_CHANGED", self.refresh_level)
        EventBus.subscribe("RESULTS_UPDATED", self._on_data_changed)
        EventBus.subscribe("STUDENTS_UPDATED", self._on_data_changed)

    def set_history_context(self, exam_id, class_name, level=None):
        self.history_exam_id = exam_id
        self.history_class_name = class_name
        self.history_level = level or SystemState.get_level()

        from db_utils import fetch_one
        row = fetch_one("""
            SELECT e.exam_name, t.term_name, y.year_name
            FROM exams e
            JOIN terms t ON t.id = e.term_id
            JOIN academic_years y ON y.id = t.academic_year_id
            WHERE e.id = ?
        """, (exam_id,))
        if row:
            exam_name, term_name, year_name = row
            self.context_label.setText(
                f"Context: {exam_name} - {term_name} - {year_name} - {class_name}"
            )
        else:
            self.context_label.setText(f"Context: Exam #{exam_id} - {class_name}")

        self.load()

    def clear_history_context(self):
        self.history_exam_id = None
        self.history_class_name = None
        self.history_level = None
        self.context_label.setText("Select an exam and class to enter remarks.")
        self._show_placeholder("Select a valid exam and class.")

    def _show_placeholder(self, message):
        self.table.clearContents()
        self.table.setRowCount(1)
        self.table.setSpan(0, 0, 1, 6)
        item = QTableWidgetItem(message)
        item.setTextAlignment(Qt.AlignCenter)
        item.setFlags(Qt.NoItemFlags)
        self.table.setItem(0, 0, item)
        self._update_table_height()

    def refresh_level(self):
        self.history_level = SystemState.get_level()
        self.load()

    def _on_data_changed(self):
        if self.isVisible():
            self.load()
        else:
            self._needs_refresh = True

    def showEvent(self, event):
        super().showEvent(event)
        if self._needs_refresh:
            self._needs_refresh = False
            self.load()

    def load(self):
        if not self.isVisible():
            self._needs_refresh = True
            return

        exam_id = self.history_exam_id
        class_name = self.history_class_name
        level = self.history_level or SystemState.get_level()

        if not exam_id or not class_name:
            self._show_placeholder("Select a valid exam and class.")
            return

        self.loading_bar.setVisible(True)
        self._show_placeholder("Loading remarks...")

        if self._worker is not None and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait()

        self._worker = RemarksWorker(exam_id, class_name, level)
        self._worker.finished.connect(self._on_data_loaded)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_data_loaded(self, rows, score_map, level):
        self.loading_bar.setVisible(False)
        self.table.clearSpans()

        if not rows:
            self._show_placeholder("No students found for this exam and class.")
            return

        self.table.setRowCount(len(rows))
        self.table.setColumnCount(6)

        self.table.blockSignals(True)
        for i, row in enumerate(rows):
            adm, name, t_rem, h_rem, a_rem, d_rem = row
            adm_str = str(adm)
            stats = score_map.get(adm_str, {})
            avg = stats.get("average", 0)
            div = stats.get("division", "-")

            item = QTableWidgetItem(adm_str)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(i, 0, item)

            item = QTableWidgetItem(str(name))
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(i, 1, item)

            is_new = not (t_rem or h_rem or a_rem or d_rem)
            if not t_rem:
                t_rem = get_default_remark(avg, div, level)
            if not h_rem:
                h_rem = get_headteacher_remark(div)
            if not a_rem:
                a_rem = get_academic_master_remark(div)
            if not d_rem:
                d_rem = get_discipline_master_remark(avg)

            for col, text in [(2, t_rem), (3, h_rem), (4, a_rem), (5, d_rem)]:
                item = QTableWidgetItem(text)
                if is_new:
                    item.setForeground(Qt.gray)
                self.table.setItem(i, col, item)

        self.table.blockSignals(False)
        self._update_table_height()

    def _on_error(self, error_msg):
        self.loading_bar.setVisible(False)
        self._show_placeholder(f"Error: {error_msg.splitlines()[0]}")
        QMessageBox.critical(self, "Error", f"Failed to load remarks:\n{error_msg}")

    def _update_table_height(self):
        self.table.resizeRowsToContents()
        height = (
            self.table.horizontalHeader().height()
            + self.table.verticalHeader().length()
            + self.table.frameWidth() * 2
            + 4
        )
        self.table.setFixedHeight(max(200, height))

    def _on_item_changed(self, item):
        if item.column() in [2, 3, 4, 5]:
            item.setForeground(Qt.black)

    def save_all(self):
        exam_id = self.history_exam_id
        if not exam_id:
            QMessageBox.warning(self, "Missing Context", "No exam selected.")
            return

        # If no rows or only placeholder, skip
        if self.table.rowCount() == 0:
            QMessageBox.information(self, "Info", "No data to save.")
            return

        # Check if the first row is a placeholder
        first_item = self.table.item(0, 0)
        if first_item and first_item.text() in [
            "Select a valid exam and class.",
            "Loading remarks...",
            "No students found for this exam and class.",
            "Error:"
        ]:
            QMessageBox.information(self, "Info", "No data to save.")
            return

        try:
            with get_cursor(commit=True) as cur:
                for i in range(self.table.rowCount()):
                    # Get admission number item – if None, skip this row
                    adm_item = self.table.item(i, 0)
                    if adm_item is None:
                        continue
                    adm = adm_item.text().strip()
                    if not adm:
                        continue  # empty admission number, skip

                    # Get remark items safely
                    t_rem_item = self.table.item(i, 2)
                    h_rem_item = self.table.item(i, 3)
                    a_rem_item = self.table.item(i, 4)
                    d_rem_item = self.table.item(i, 5)

                    t_rem = t_rem_item.text().strip() if t_rem_item else ""
                    h_rem = h_rem_item.text().strip() if h_rem_item else ""
                    a_rem = a_rem_item.text().strip() if a_rem_item else ""
                    d_rem = d_rem_item.text().strip() if d_rem_item else ""

                    cur.execute("""
                        INSERT INTO exam_remarks (admission_no, exam_id, teacher_remarks, headteacher_remarks, academic_master_remarks, discipline_master_remarks)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(admission_no, exam_id) DO UPDATE SET
                            teacher_remarks = excluded.teacher_remarks,
                            headteacher_remarks = excluded.headteacher_remarks,
                            academic_master_remarks = excluded.academic_master_remarks,
                            discipline_master_remarks = excluded.discipline_master_remarks
                    """, (adm, exam_id, t_rem, h_rem, a_rem, d_rem))

            QMessageBox.information(self, "Success", "All remarks saved successfully.")
            self.load()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save remarks: {e}")
