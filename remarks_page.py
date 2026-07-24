from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QHeaderView,
    QAbstractItemView,
    QScrollArea,
    QSizePolicy,
    QFrame,
    QPushButton,
    QMessageBox,
)
from PySide6.QtCore import Qt
from db_utils import fetch_all, get_cursor
from system_state import SystemState
from event_bus import EventBus
from ranking_engine import compute_student_scores
from remarks_utils import get_default_remark, get_headteacher_remark, get_academic_master_remark, get_discipline_master_remark


class RemarksPage(QWidget):
    def __init__(self):
        super().__init__()
        self._needs_refresh = False
        self.history_exam_id = None
        self.history_class_name = None
        self.history_level = None

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

        # =========================
        # SAVE BUTTON
        # =========================
        controls = QHBoxLayout()
        self.save_all_btn = QPushButton("SAVE ALL REMARKS")
        self.save_all_btn.setStyleSheet("background-color: #2E7D32; color: white; padding: 8px;")
        self.save_all_btn.clicked.connect(self.save_all)
        controls.addWidget(self.save_all_btn)
        controls.addStretch()
        layout.addLayout(controls)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Admission No",
            "Name",
            "Teacher Remarks",
            "Headteacher Remarks",
            "Academic Master Remarks",
            "Discipline Master Remarks",
            "Status"
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
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)

        layout.addWidget(self.table)
        self.table.itemChanged.connect(self._on_item_changed)

        EventBus.subscribe("LEVEL_CHANGED", self.refresh_level)

        # Load initially (will show empty)
        self.load()

    def refresh_level(self):
        self.history_level = SystemState.get_level()
        self.load()

    # ------------------------------------------------------------------
    # Public context setters (called by central filter)
    # ------------------------------------------------------------------
    def set_history_context(self, exam_id, class_name, level=None):
        self.history_exam_id = exam_id
        self.history_class_name = class_name
        self.history_level = level or SystemState.get_level()

        # Get exam details for label
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
        self.table.setRowCount(0)

    def showEvent(self, event):
        super().showEvent(event)
        if self._needs_refresh:
            self._needs_refresh = False
            self.load()

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------
    def load(self):
        if not self.isVisible():
            self._needs_refresh = True
            return

        exam_id = self.history_exam_id
        class_name = self.history_class_name
        level = self.history_level or SystemState.get_level()

        if not exam_id or not class_name:
            self.table.setRowCount(0)
            return

        self.table.blockSignals(True)
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
        rows = fetch_all(query, (exam_id, class_name, level))

        # Fetch performance data for defaults
        scores = compute_student_scores(level, exam_id, class_name)
        score_map = {str(s["admission"]): s for s in scores}

        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(rows))

        for i, row in enumerate(rows):
            adm, name, t_rem, h_rem, a_rem, d_rem = row
            adm_str = str(adm)

            stats = score_map.get(adm_str, {})
            avg = stats.get("average", 0)
            div = stats.get("division", "-")

            item_adm = QTableWidgetItem(adm_str)
            item_adm.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(i, 0, item_adm)

            item_name = QTableWidgetItem(str(name))
            item_name.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(i, 1, item_name)

            is_new = not (t_rem or h_rem or a_rem or d_rem)
            if not t_rem:
                t_rem = get_default_remark(avg, div, level)
            if not h_rem:
                h_rem = get_headteacher_remark(div)
            if not a_rem:
                a_rem = get_academic_master_remark(div)
            if not d_rem:
                d_rem = get_discipline_master_remark(avg)

            item_t = QTableWidgetItem(t_rem)
            item_h = QTableWidgetItem(h_rem)
            item_a = QTableWidgetItem(a_rem)
            item_d = QTableWidgetItem(d_rem)

            if is_new:
                item_t.setForeground(Qt.gray)
                item_h.setForeground(Qt.gray)
                item_a.setForeground(Qt.gray)
                item_d.setForeground(Qt.gray)

            self.table.setItem(i, 2, item_t)
            self.table.setItem(i, 3, item_h)
            self.table.setItem(i, 4, item_a)
            self.table.setItem(i, 5, item_d)

            status_text = "Saved" if not is_new else "Default (Editable)"
            item_status = QTableWidgetItem(status_text)
            item_status.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            if is_new:
                item_status.setForeground(Qt.blue)
            else:
                item_status.setForeground(Qt.darkGreen)
            self.table.setItem(i, 6, item_status)

        self.table.setUpdatesEnabled(True)
        self.table.blockSignals(False)
        self._update_table_height()

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

        try:
            with get_cursor(commit=True) as cur:
                for i in range(self.table.rowCount()):
                    adm = self.table.item(i, 0).text()
                    t_rem = self.table.item(i, 2).text().strip()
                    h_rem = self.table.item(i, 3).text().strip()
                    a_rem = self.table.item(i, 4).text().strip()
                    d_rem = self.table.item(i, 5).text().strip()

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