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
from class_utils import GRADUATED_CLASS, get_classes
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
    "Form IV": GRADUATED_CLASS,
    "Form V": "Form VI",
    "Form VI": GRADUATED_CLASS,
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

        ranking = compute_student_scores(level, exam_id, class_name) or []
        ranked_by_admission = {
            row.get("admission"): row
            for row in ranking
            if row.get("class") == class_name
        }

        # Always start from the full class roster, not just the ranking
        # output. compute_student_scores() only returns students who have
        # at least some results -- a student with none simply isn't in that
        # list. Merging against the full roster here means a no-results
        # student is shown and flagged instead of silently disappearing
        # from the promotion table.
        all_students = fetch_all(
            """
            SELECT admission_no, full_name
            FROM students
            WHERE class=? AND level=?
            ORDER BY full_name, admission_no
            """,
            (class_name, level),
        )

        rows = []
        for admission_no, full_name in all_students:
            ranked = ranked_by_admission.get(admission_no)
            if ranked:
                rows.append(ranked)
            else:
                rows.append({
                    "admission": admission_no,
                    "name": full_name,
                    "class": class_name,
                    "average": "-",
                    "status": "NO RESULTS",
                })

        self.preview_rows = rows
        self.table.setRowCount(len(rows))

        for row_index, student in enumerate(rows):
            promote_item = QTableWidgetItem()
            promote_item.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
            )
            # Students with no results are unchecked by default so office
            # staff must explicitly opt them into promotion after reviewing
            # why they have no results, rather than sweeping them along
            # with everyone else by accident.
            has_results = student.get("status", "NO RESULTS") != "NO RESULTS"
            promote_item.setCheckState(Qt.Checked if has_results else Qt.Unchecked)
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
        no_results_count = sum(1 for r in rows if r.get("status") == "NO RESULTS")
        summary = f"{len(rows)} student(s) ready for review from {class_name} to {target_class}."
        if no_results_count:
            summary += f" {no_results_count} have NO RESULTS and are unchecked by default."
        self.summary_label.setText(summary)

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
    def _copy_enrollments(self, cur, admission_no, old_class, new_class, year_id, term_id):
        """Move this student's ACTIVE-term subject enrollments from
        old_class to new_class.

        This used to INSERT new rows for new_class while leaving the
        old_class rows for the same term/year untouched -- so a promoted
        student ended up enrolled in BOTH classes at once for the active
        term, and showed up in Results Entry under both. Updating
        class_name in place instead means there is only ever one
        enrollment row per (student, subject, year, term); it always
        reflects the class the student is actually in right now.

        Enrollment rows for OTHER (past, already-completed) terms are left
        completely alone -- those are historical records tied to
        already-issued results and must keep showing the class the student
        was actually in at the time those results were entered.

        `OR IGNORE` guards the rare case where a matching (new_class,
        subject, year, term) row already exists for some other reason --
        the update is skipped for that one subject rather than raising a
        uniqueness error and aborting the whole promotion.
        """
        cur.execute("""
            UPDATE OR IGNORE enrollments
            SET class_name = ?
            WHERE admission_no = ?
              AND class_name = ?
              AND academic_year_id = ?
              AND term_id = ?
        """, (new_class, admission_no, old_class, year_id, term_id))

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

        is_graduation = target_class == GRADUATED_CLASS
        term_id = year_id = None
        if not is_graduation:
            # Get active term and its academic year for enrollment copying
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

        # Show warning about promotion or graduation
        if is_graduation:
            message = (
                f"Graduate {len(admissions)} student(s) from {source_class}?\n\n"
                "Graduated students will be moved to the Graduated class and "
                "their current enrollments will not be copied."
            )
            dialog_title = "Apply Graduation"
        else:
            message = (
                f"Promote {len(admissions)} student(s) from {source_class} to {target_class}?\n\n"
                "Their subject enrollments will be automatically copied to the new class "
                "for the active term and academic year."
            )
            dialog_title = "Apply Promotion"

        reply = QMessageBox.question(
            self,
            dialog_title,
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        if not authorize_action(self, dialog_title):
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
            # Single transaction: student class updates AND every student's
            # enrollment copy all happen on the same cursor. If anything
            # fails partway (e.g. student #47 of 60), get_cursor's context
            # manager rolls back the ENTIRE batch -- no student ends up
            # promoted without their enrollments copied, and no partial
            # state is ever committed.
            with get_cursor(commit=True) as cur:
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

                if not is_graduation:
                    for admission_no in admissions:
                        self._copy_enrollments(cur, admission_no, source_class, target_class, year_id, term_id)

        except Exception as error:
            show_error(
                self,
                f"Promotion failed and was fully rolled back -- no students were "
                f"changed:\n{error}",
            )
            return

        EventBus.emit("STUDENTS_UPDATED")
        if is_graduation:
            show_info(
                self,
                f"Graduated {len(admissions)} student(s).\n"
                f"Backup: {backup_path}",
                title="Graduation Complete",
            )
        else:
            show_info(
                self,
                f"Promoted {len(admissions)} student(s) and copied their enrollments.\n"
                f"Backup: {backup_path}",
                title="Promotion Complete",
            )
        self.preview()