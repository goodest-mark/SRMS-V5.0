from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QComboBox,
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
from remarks_utils import get_default_remark, get_headteacher_remark, get_developmental_note
import combo_loaders

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

        self.title = QLabel("EXAM REMARKS & DEVELOPMENTAL NOTES")
        self.title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.title)

        self.context_label = QLabel("Select an exam and class to enter remarks.")
        layout.addWidget(self.context_label)

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
            "Admission No",
            "Name",
            "Teacher Remarks",
            "Headteacher Remarks",
            "Developmental Notes",
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
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.table)
        self.table.itemChanged.connect(self._on_item_changed)

        EventBus.subscribe("LEVEL_CHANGED", self.load)

    def set_history_context(self, exam_id, class_name, level=None):
        self.history_exam_id = exam_id
        self.history_class_name = class_name
        self.history_level = level or SystemState.get_level()
        self.context_label.setText(f"Exam: #{exam_id} | Class: {class_name}")
        self.load()

    def showEvent(self, event):
        super().showEvent(event)
        if getattr(self, "_needs_refresh", False):
            self._needs_refresh = False
            self.load()

    def load(self):
        if not self.isVisible():
            self._needs_refresh = True
            return
            
        if not self.history_exam_id or not self.history_class_name:
            self.table.setRowCount(0)
            return

        self.table.blockSignals(True)
        # Fetch students and existing remarks
        query = """
            SELECT 
                s.admission_no, 
                s.full_name,
                er.teacher_remarks,
                er.headteacher_remarks,
                er.developmental_notes
            FROM students s
            LEFT JOIN exam_remarks er ON s.admission_no = er.admission_no AND er.exam_id = ?
            WHERE s.class = ? AND s.level = ?
            ORDER BY s.full_name
        """
        rows = fetch_all(query, (self.history_exam_id, self.history_class_name, self.history_level))

        # Fetch performance data for defaults
        scores = compute_student_scores(self.history_level, self.history_exam_id, self.history_class_name)
        score_map = {str(s["admission"]): s for s in scores}

        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(rows))
        
        for i, row in enumerate(rows):
            adm, name, t_rem, h_rem, dev = row
            adm_str = str(adm)
            
            # Get performance data
            stats = score_map.get(adm_str, {})
            avg = stats.get("average", 0)
            div = stats.get("division", "-")
            
            # Adm & Name (Read-only)
            item_adm = QTableWidgetItem(adm_str)
            item_adm.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(i, 0, item_adm)
            
            item_name = QTableWidgetItem(str(name))
            item_name.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(i, 1, item_name)
            
            # Determine defaults
            is_new = not (t_rem or h_rem or dev)
            if not t_rem:
                t_rem = get_default_remark(avg, div, self.history_level)
            if not h_rem:
                h_rem = get_headteacher_remark(div)
            if not dev:
                dev = get_developmental_note(avg)
            
            # Remarks (Editable)
            item_t = QTableWidgetItem(t_rem)
            item_h = QTableWidgetItem(h_rem)
            item_d = QTableWidgetItem(dev)
            
            if is_new:
                item_t.setForeground(Qt.gray)
                item_h.setForeground(Qt.gray)
                item_d.setForeground(Qt.gray)
            
            self.table.setItem(i, 2, item_t)
            self.table.setItem(i, 3, item_h)
            self.table.setItem(i, 4, item_d)
            
            # Status
            status_text = "Saved" if not is_new else "Default (Editable)"
            item_status = QTableWidgetItem(status_text)
            item_status.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            if is_new:
                item_status.setForeground(Qt.blue)
            else:
                item_status.setForeground(Qt.darkGreen)
            self.table.setItem(i, 5, item_status)

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
        if item.column() in [2, 3, 4]:
            item.setForeground(Qt.black)

    def save_all(self):
        if not self.history_exam_id:
            return

        try:
            with get_cursor(commit=True) as cur:
                for i in range(self.table.rowCount()):
                    adm = self.table.item(i, 0).text()
                    t_rem = self.table.item(i, 2).text().strip()
                    h_rem = self.table.item(i, 3).text().strip()
                    dev = self.table.item(i, 4).text().strip()
                    
                    cur.execute("""
                        INSERT INTO exam_remarks (admission_no, exam_id, teacher_remarks, headteacher_remarks, developmental_notes)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(admission_no, exam_id) DO UPDATE SET
                            teacher_remarks = excluded.teacher_remarks,
                            headteacher_remarks = excluded.headteacher_remarks,
                            developmental_notes = excluded.developmental_notes
                    """, (adm, self.history_exam_id, t_rem, h_rem, dev))
            
            QMessageBox.information(self, "Success", "All remarks saved successfully.")
            self.load()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save remarks: {e}")
