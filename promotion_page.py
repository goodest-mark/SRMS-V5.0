from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from backup_utils import create_pre_operation_backup
from class_utils import get_classes
from db_utils import fetch_all, fetch_one, get_cursor
from event_bus import EventBus
from ranking_engine import compute_student_scores
from security_settings import authorize_action
from system_state import SystemState
from ui_helpers import show_error, show_info
import combo_loaders


PROMOTION_MAP = {
    "Form I": "Form II",
    "Form II": "Form III",
    "Form III": "Form IV",
    "Form V": "Form VI",
}


class PromotionPage(QWidget):
    def __init__(self):
        super().__init__()

        self.preview_rows = []

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        title = QLabel("PROMOTION WIZARD")
        title.setProperty("variant", "accent")
        root.addWidget(title)

        filters = QGroupBox("Promotion Context")
        filters_layout = QGridLayout(filters)

        self.exam_box = QComboBox()
        self.class_box = QComboBox()
        self.target_label = QLabel("-")
        self.target_label.setProperty("variant", "success")

        self.preview_btn = QPushButton("Preview")
        self.preview_btn.setObjectName("workflowSecondary")
        self.apply_btn = QPushButton("Apply Promotion")
        self.apply_btn.setObjectName("workflowPrimary")
        self.apply_btn.setEnabled(False)

        filters_layout.addWidget(QLabel("Completed Exam"), 0, 0)
        filters_layout.addWidget(self.exam_box, 0, 1)
        filters_layout.addWidget(QLabel("Current Class"), 0, 2)
        filters_layout.addWidget(self.class_box, 0, 3)
        filters_layout.addWidget(QLabel("Next Class"), 1, 0)
        filters_layout.addWidget(self.target_label, 1, 1)
        filters_layout.addWidget(self.preview_btn, 1, 2)
        filters_layout.addWidget(self.apply_btn, 1, 3)
        root.addWidget(filters)

        self.summary_label = QLabel("Choose a completed exam and class, then preview.")
        self.summary_label.setWordWrap(True)
        self.summary_label.setProperty("variant", "muted")
        root.addWidget(self.summary_label)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Promote",
            "Admission",
            "Student Name",
            "Current Class",
            "Next Class",
            "Average",
            "Status",
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        for column in range(3, 7):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
        root.addWidget(self.table, 1)

        self.exam_box.currentIndexChanged.connect(self.preview)
        self.class_box.currentIndexChanged.connect(self.on_class_changed)
        self.preview_btn.clicked.connect(self.preview)
        self.apply_btn.clicked.connect(self.apply_promotion)

        EventBus.subscribe("LEVEL_CHANGED", self.refresh_all)
        EventBus.subscribe("EXAMS_UPDATED", self.refresh_all)
        EventBus.subscribe("STUDENTS_UPDATED", self.preview)

        self.refresh_all()

    def refresh_all(self):
        combo_loaders.load_completed_exams(self.exam_box)
        self.load_classes()
        self.on_class_changed()

    def load_classes(self):
        current = self.class_box.currentText()
        self.class_box.blockSignals(True)
        self.class_box.clear()
        promotable = [class_name for class_name in get_classes() if class_name in PROMOTION_MAP]
        self.class_box.addItems(promotable)
        if current:
            index = self.class_box.findText(current)
            if index >= 0:
                self.class_box.setCurrentIndex(index)
        self.class_box.blockSignals(False)

    def on_class_changed(self):
        target = PROMOTION_MAP.get(self.class_box.currentText(), "-")
        self.target_label.setText(target)
        self.preview()

    def preview(self):
        exam_id = self.exam_box.currentData()
        class_name = self.class_box.currentText().strip()
        target_class = PROMOTION_MAP.get(class_name)
        level = SystemState.get_level()

        self.preview_rows = []
        self.table.setRowCount(0)
        self.apply_btn.setEnabled(False)

        if exam_id is None or not class_name or not target_class:
            self.summary_label.setText("Choose a completed exam and promotable class.")
            return

        ranking = compute_student_scores(level, exam_id, class_name)
        if ranking:
            rows = [
                row for row in ranking
                if row.get("class") == class_name
            ]
        else:
            rows = self._students_without_results(class_name, level)

        self.preview_rows = rows
        self.table.setRowCount(len(rows))

        for row_index, student in enumerate(rows):
            promote_item = QTableWidgetItem()
            promote_item.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
            )
            promote_item.setCheckState(Qt.Checked)
            self.table.setItem(row_index, 0, promote_item)

            values = [
                student.get("admission", ""),
                student.get("name", ""),
                class_name,
                target_class,
                student.get("average", "-"),
                student.get("status", "NO RESULTS"),
            ]
            for column, value in enumerate(values, start=1):
                item = QTableWidgetItem(str(value))
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                if column in (4, 5, 6):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_index, column, item)

        self.apply_btn.setEnabled(bool(rows))
        self.summary_label.setText(
            f"{len(rows)} student(s) ready for review from {class_name} to {target_class}."
        )

    def _students_without_results(self, class_name, level):
        return [
            {
                "admission": admission_no,
                "name": full_name,
                "class": class_name,
                "average": "-",
                "status": "NO RESULTS",
            }
            for admission_no, full_name in fetch_all(
                """
                SELECT admission_no, full_name
                FROM students
                WHERE class=? AND level=?
                ORDER BY full_name, admission_no
                """,
                (class_name, level),
            )
        ]

    def checked_admissions(self):
        admissions = []
        for row in range(self.table.rowCount()):
            check_item = self.table.item(row, 0)
            admission_item = self.table.item(row, 1)
            if (
                check_item is not None
                and admission_item is not None
                and check_item.checkState() == Qt.Checked
            ):
                admissions.append(admission_item.text())
        return admissions

    # ------------------------------------------------------------------
    # Helper: copy enrollments for a single student
    # ------------------------------------------------------------------
    def _copy_enrollments(self, admission_no, old_class, new_class, year_id, term_id):
        """Copy all subject enrollments from old_class to new_class for a student."""
        with get_cursor(commit=True) as cur:
            # Get subjects the student is enrolled in for old_class, year, term
            cur.execute("""
                SELECT subject_name
                FROM enrollments
                WHERE admission_no = ?
                  AND class_name = ?
                  AND academic_year_id = ?
                  AND term_id = ?
            """, (admission_no, old_class, year_id, term_id))
            subjects = [row[0] for row in cur.fetchall()]

            if not subjects:
                return  # nothing to copy

            # Insert them with the new class (ignore duplicates)
            for subject in subjects:
                cur.execute("""
                    INSERT OR IGNORE INTO enrollments
                        (admission_no, subject_name, class_name, academic_year_id, term_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (admission_no, subject, new_class, year_id, term_id))

    # ------------------------------------------------------------------
    # Apply promotion
    # ------------------------------------------------------------------
    def apply_promotion(self):
        source_class = self.class_box.currentText().strip()
        target_class = PROMOTION_MAP.get(source_class)
        admissions = self.checked_admissions()

        if not target_class:
            show_error(self, "This class has no promotion target.")
            return
        if not admissions:
            show_error(self, "Select at least one student to promote.")
            return

        # Get active term and its academic year
        active_term = fetch_one("SELECT id, academic_year_id FROM terms WHERE is_active=1 LIMIT 1")
        if not active_term:
            show_error(
                self,
                "No active term found. Enrollments cannot be copied.\n"
                "Please set an active term in Academics > Terms and try again.",
                title="Missing Active Term"
            )
            return
        term_id, year_id = active_term

        # Show warning about enrollment copying
        reply = QMessageBox.question(
            self,
            "Apply Promotion",
            f"Promote {len(admissions)} student(s) from {source_class} to {target_class}?\n\n"
            "Their subject enrollments will be automatically copied to the new class "
            "for the active term and academic year.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        if not authorize_action(self, "Apply Promotion"):
            return

        try:
            backup_path = create_pre_operation_backup("promotion")
        except Exception as error:
            show_error(
                self,
                f"Could not create backup. Promotion was cancelled.\n\n{error}",
                title="Backup Failed",
            )
            return

        try:
            with get_cursor(commit=True) as cur:
                # Update student classes
                cur.executemany(
                    """
                    UPDATE students
                    SET class=?
                    WHERE admission_no=? AND class=?
                    """,
                    [
                        (target_class, admission_no, source_class)
                        for admission_no in admissions
                    ],
                )

            # Copy enrollments for each promoted student
            for admission_no in admissions:
                self._copy_enrollments(admission_no, source_class, target_class, year_id, term_id)

        except Exception as error:
            show_error(self, f"Promotion failed:\n{error}")
            return

        EventBus.emit("STUDENTS_UPDATED")
        show_info(
            self,
            f"Promoted {len(admissions)} student(s) and copied their enrollments.\n"
            f"Backup: {backup_path}",
            title="Promotion Complete",
        )
        self.preview()
