# ----------------------------------------------------------------------------
# BROADSHEET – All-in-One Scrollable View
# No internal filters – uses context from central filter bar.
# ----------------------------------------------------------------------------
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from PySide6.QtCore import (
    Qt, QThread, QObject, Signal, Slot
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QGridLayout,
    QGroupBox, QAbstractItemView, QScrollArea, QFrame, QSizePolicy,
    QApplication
)

from db_utils import fetch_all, fetch_one
from system_state import SystemState
from event_bus import EventBus
from settings_page import get_setting
from security_settings import get_school_profile_from_db
from ui_helpers import show_error, get_subject_short_name
from table_utils import setup_table
from class_utils import get_classes
from ranking_engine import compute_student_scores
import broadsheet_export
from ui.cards import PremiumStatCard
from app_paths import icon_path

_logger = logging.getLogger(__name__)

PASS_MARK = 50
TOP_BOTTOM_COUNT = 10


# ---------- DTO ----------
@dataclass
class BroadsheetData:
    subjects: List[str]
    subject_headers: List[str]
    rows: List[Dict[str, Any]]
    meta: Dict[str, Any]
    class_performance: Dict[str, Any]
    gender_summary: Dict[str, int]
    division_summary: Dict[str, int]
    top_students: List[Dict[str, Any]]
    bottom_students: List[Dict[str, Any]]
    subject_performance: Dict[str, Dict[str, float]]
    subject_ranking: List[Tuple[str, Dict[str, float]]]
    best_subject: Optional[str]
    worst_subject: Optional[str]
    max_avg: float
    min_avg: float
    settings: Dict[str, bool]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for compatibility with broadsheet_export functions."""
        return {
            'subjects': self.subjects,
            'subject_headers': self.subject_headers,
            'rows': self.rows,
            'meta': self.meta,
            'class_performance': self.class_performance,
            'gender_summary': self.gender_summary,
            'division_summary': self.division_summary,
            'top_students': self.top_students,
            'bottom_students': self.bottom_students,
            'subject_performance': self.subject_performance,
            'subject_ranking': self.subject_ranking,
            'best_subject': self.best_subject,
            'worst_subject': self.worst_subject,
            'max_avg': self.max_avg,
            'min_avg': self.min_avg,
            'settings': self.settings,
        }


# ---------- SERVICE ----------
class BroadsheetService:
    def __init__(self, fetch_all_fn, fetch_one_fn, get_setting_fn,
                 get_school_profile_fn, get_classes_fn, compute_scores_fn, get_level_fn):
        self._fetch_all = fetch_all_fn
        self._fetch_one = fetch_one_fn
        self._get_setting = get_setting_fn
        self._get_school_profile = get_school_profile_fn
        self._get_classes = get_classes_fn
        self._compute_scores = compute_scores_fn
        self._get_level = get_level_fn

    def fetch_data(self, exam_id: Optional[int], class_name: str,
                   year_id: Optional[int], term_id: Optional[int],
                   level: Optional[str]) -> BroadsheetData:
        if not exam_id or not class_name:
            raise ValueError("Exam ID and class name are required.")
        if level is None:
            level = self._get_level()

        ranking_summary = self._compute_scores(level, exam_id, class_name)
        ranking_summary = [s for s in ranking_summary if s.get('class') == class_name]
        if not ranking_summary:
            raise ValueError("No students found.")
        ranking_summary = self._assign_class_positions(ranking_summary)

        if year_id is None or term_id is None:
            row = self._fetch_one(
                "SELECT t.academic_year_id, e.term_id FROM exams e JOIN terms t ON t.id = e.term_id WHERE e.id = ?",
                (exam_id,))
            if not row:
                raise ValueError("Exam not found.")
            year_id, term_id = row[0], row[1]

        admissions = [s['admission'] for s in ranking_summary]
        subjects = self._fetch_subjects(admissions, year_id, term_id, class_name)
        subject_headers = [get_subject_short_name(sub) for sub in subjects]
        marks_map = self._fetch_marks(exam_id)
        rows = self._build_rows(ranking_summary, subjects, marks_map)

        class_perf = self._compute_class_performance(ranking_summary)
        gender_summary = self._compute_gender_summary(ranking_summary)
        division_summary = self._compute_division_summary(ranking_summary)
        top_students, bottom_students = self._compute_top_bottom(ranking_summary)
        subject_perf = self._compute_subject_performance(rows, subjects)
        subject_ranking = sorted(subject_perf.items(), key=lambda item: item[1]['average'], reverse=True)
        best_sub = subject_ranking[0][0] if subject_ranking else None
        worst_sub = subject_ranking[-1][0] if subject_ranking else None
        max_avg = subject_ranking[0][1]['average'] if subject_ranking else 0.0
        min_avg = subject_ranking[-1][1]['average'] if subject_ranking else 0.0

        context_row = self._fetch_one(
            """
            SELECT e.exam_name, t.term_name, y.year_name
            FROM exams e
            JOIN terms t ON t.id = e.term_id
            JOIN academic_years y ON y.id = t.academic_year_id
            WHERE e.id = ?
            """,
            (exam_id,),
        )
        exam_name, term_name, year_name = context_row or (
            f"Exam #{exam_id}", "-", "-"
        )
        school_profile = self._get_school_profile()
        meta = {
            'year': year_name, 'term': term_name, 'exam': exam_name,
            'class': class_name, 'level': level,
            'school_profile': school_profile,
            'generated_date': datetime.now().strftime("%A, %d %B %Y %I:%M %p")
        }
        settings = {
            'show_gender_summary': self._get_setting('show_gender_summary', '1') == '1',
            'show_subject_ranking': self._get_setting('show_subject_ranking', '1') == '1',
            'show_logo': self._get_setting('show_logo', '1') == '1',
            'show_watermark': self._get_setting('show_watermark', '1') == '1',
        }

        return BroadsheetData(
            subjects=subjects, subject_headers=subject_headers, rows=rows,
            meta=meta, class_performance=class_perf, gender_summary=gender_summary,
            division_summary=division_summary, top_students=top_students,
            bottom_students=bottom_students, subject_performance=subject_perf,
            subject_ranking=subject_ranking, best_subject=best_sub,
            worst_subject=worst_sub, max_avg=max_avg, min_avg=min_avg,
            settings=settings
        )

    @staticmethod
    def _assign_class_positions(students):
        sorted_students = sorted(students, key=lambda x: (
            -float(x.get('average', 0)), -float(x.get('total_marks', 0)), x.get('admission', '')))
        for idx, s in enumerate(sorted_students, 1):
            s['class_position'] = idx
        return sorted_students

    def _fetch_subjects(self, admissions, year_id, term_id, class_name):
        if not admissions:
            return []
        placeholders = ",".join("?" for _ in admissions)
        params = tuple(admissions + [year_id, term_id])
        rows = self._fetch_all(
            f"""
            SELECT DISTINCT subject_name
            FROM enrollments
            WHERE admission_no IN ({placeholders})
              AND academic_year_id = ?
              AND term_id = ?
              AND (class_name = ? OR class_name IS NULL OR class_name = '')
            ORDER BY subject_name
            """,
            tuple(admissions + [year_id, term_id, class_name]))
        return [row[0] for row in rows]

    def _fetch_marks(self, exam_id):
        marks_map = {}
        rows = self._fetch_all("SELECT admission_no, subject_name, marks FROM results WHERE exam_id = ?", (exam_id,))
        for adm, sub, marks in rows:
            marks_map.setdefault(adm, {})[sub] = marks
        return marks_map

    def _build_rows(self, ranking_summary, subjects, marks_map):
        rows = []
        for s in ranking_summary:
            row = {
                'Position': s.get('class_position', s.get('position', 0)),
                'Admission No': s['admission'], 'Student Name': s['name'],
                'Gender': s.get('gender', '-'), 'marks': {},
                'Total': 0, 'Average': s.get('average', 0),
                'Points': s.get('points', 0), 'Division': s.get('division', '0')
            }
            total = 0
            student_marks = marks_map.get(s['admission'], {})
            for sub in subjects:
                mark = student_marks.get(sub, "-")
                row['marks'][sub] = mark
                if isinstance(mark, (int, float)):
                    total += mark
            row['Total'] = total
            rows.append(row)
        return rows

    def _compute_class_performance(self, ranking_summary):
        total = len(ranking_summary)
        ready = [s for s in ranking_summary if s.get('status') == 'READY']
        averages = [s.get('average', 0) for s in ready if isinstance(s.get('average'), (int, float))]
        class_avg = round(sum(averages) / len(averages), 2) if averages else 0.0
        high_avg = max(averages) if averages else 0.0
        low_avg = min(averages) if averages else 0.0
        pass_count = sum(1 for s in ranking_summary if s.get('division') in ('I', 'II', 'III', 'IV'))
        fail_count = total - pass_count
        pass_rate = round((pass_count / total) * 100, 2) if total else 0.0
        fail_rate = round((fail_count / total) * 100, 2) if total else 0.0
        return {'total_students': total, 'class_average': class_avg, 'highest_average': high_avg,
                'lowest_average': low_avg, 'pass_count': pass_count, 'fail_count': fail_count,
                'pass_rate': pass_rate, 'fail_rate': fail_rate}

    def _compute_gender_summary(self, ranking_summary):
        male = sum(1 for s in ranking_summary if s.get('gender') == 'Male')
        female = sum(1 for s in ranking_summary if s.get('gender') == 'Female')
        return {'Male': male, 'Female': female, 'Total': male + female}

    def _compute_division_summary(self, ranking_summary):
        counts = {"I": 0, "II": 0, "III": 0, "IV": 0, "0": 0, "Incomplete": 0}
        for s in ranking_summary:
            div = str(s.get('division', '0'))
            if s.get('status') == 'INCOMPLETE':
                counts['Incomplete'] += 1
            elif div in counts:
                counts[div] += 1
            else:
                counts['0'] += 1
        return counts

    def _compute_top_bottom(self, ranking_summary):
        ready = [s for s in ranking_summary if s.get('status') == 'READY']
        top = ready[:TOP_BOTTOM_COUNT]
        bottom = sorted(ready, key=lambda x: x.get('average', 0))[:TOP_BOTTOM_COUNT]
        return top, bottom

    def _compute_subject_performance(self, rows, subjects):
        perf = {}
        for sub in subjects:
            total, count, passes, fails = 0, 0, 0, 0
            for row in rows:
                mark = row['marks'].get(sub)
                if isinstance(mark, (int, float)):
                    total += mark
                    count += 1
                    if mark >= PASS_MARK:
                        passes += 1
                    else:
                        fails += 1
            avg = round(total / count, 2) if count else 0.0
            perf[sub] = {'average': avg, 'passes': passes, 'fails': fails}
        return perf


# ---------- WORKER ----------
class BroadsheetWorker(QObject):
    data_ready = Signal(BroadsheetData)
    error = Signal(str)

    def __init__(self, service, filters):
        super().__init__()
        self._service = service
        self._filters = filters

    @Slot()
    def run(self):
        try:
            data = self._service.fetch_data(
                exam_id=self._filters.get('exam_id'),
                class_name=self._filters.get('class_name'),
                year_id=self._filters.get('year_id'),
                term_id=self._filters.get('term_id'),
                level=self._filters.get('level'),
            )
            self.data_ready.emit(data)
        except Exception as e:
            self.error.emit(str(e))


# ---------- SCROLLABLE BROADSHEET (PURE CONTENT) ----------
class BroadsheetPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history_level = None
        self.context = None
        self.data: Optional[BroadsheetData] = None
        self._service = BroadsheetService(
            fetch_all_fn=fetch_all, fetch_one_fn=fetch_one,
            get_setting_fn=get_setting, get_school_profile_fn=get_school_profile_from_db,
            get_classes_fn=get_classes, compute_scores_fn=compute_student_scores,
            get_level_fn=SystemState.get_level,
        )
        self._thread = None
        self._worker = None
        self._loading = False

        # ─── Main layout ────────────────────────────────────────────
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        root_layout.addWidget(self.scroll)

        self.content = QWidget()
        self.scroll.setWidget(self.content)

        self.main_layout = QVBoxLayout(self.content)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # ─── Context label & actions ──────────────────────────────
        top_bar = QHBoxLayout()
        self.context_label = QLabel("No context set.")
        self.context_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        top_bar.addWidget(self.context_label)
        top_bar.addStretch()

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self._load_data)
        top_bar.addWidget(self.refresh_btn)

        self.excel_btn = QPushButton("📊 Export Excel")
        self.excel_btn.clicked.connect(self._export_excel)
        self.excel_btn.setEnabled(False)
        top_bar.addWidget(self.excel_btn)

        self.pdf_btn = QPushButton("📄 Export PDF")
        self.pdf_btn.clicked.connect(self._export_pdf)
        self.pdf_btn.setEnabled(False)
        top_bar.addWidget(self.pdf_btn)

        self.main_layout.addLayout(top_bar)

        # ─── Cards (2 rows of 4) ──────────────────────────────────
        self.cards_container = QWidget()
        self.cards_grid = QGridLayout(self.cards_container)
        self.cards_grid.setContentsMargins(0, 5, 0, 5)
        self.cards_grid.setSpacing(10)

        metric_keys = [
            ("total_students", "Total Students", "students.svg", "primary"),
            ("class_avg", "Class Average", "results.svg", "success"),
            ("pass_rate", "Pass Rate", "results.svg", "secondary"),
            ("fail_rate", "Fail Rate", "results.svg", "danger"),
            ("high_avg", "Highest Average", "academics.svg", "secondary"),
            ("low_avg", "Lowest Average", "school.svg", "warning"),
            ("best_sub", "Best Subject", "academics.svg", "success"),
            ("worst_sub", "Worst Subject", "results.svg", "warning"),
        ]
        self._card_widgets = {}
        for idx, (key, label, icon, accent) in enumerate(metric_keys):
            card = PremiumStatCard(label, "", str(icon_path(icon)), accent)
            self._card_widgets[key] = card.value_lbl
            self.cards_grid.addWidget(card, idx // 4, idx % 4)

        self.main_layout.addWidget(self.cards_container)

        # ─── Summary panels (Gender, Division, Performance) ──────
        summary_panels = QHBoxLayout()
        summary_panels.setSpacing(15)

        # Gender
        gender_group = QGroupBox("Gender Summary")
        gender_layout = QVBoxLayout(gender_group)
        self.gender_table = QTableWidget()
        setup_table(self.gender_table, ["Gender", "Count"])
        self.gender_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.gender_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.gender_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        gender_layout.addWidget(self.gender_table)
        gender_group.setMinimumWidth(220)
        gender_group.setMaximumWidth(280)
        summary_panels.addWidget(gender_group)

        # Division
        div_group = QGroupBox("Division Summary")
        div_layout = QVBoxLayout(div_group)
        self.division_table = QTableWidget()
        setup_table(self.division_table, ["Division", "Students"])
        self.division_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.division_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.division_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        div_layout.addWidget(self.division_table)
        div_group.setMinimumWidth(220)
        div_group.setMaximumWidth(280)
        summary_panels.addWidget(div_group)

        # Performance stats
        perf_group = QGroupBox("Performance Summary")
        perf_layout = QGridLayout(perf_group)
        self.p_students = QLabel("Students: -")
        self.p_avg = QLabel("Class Avg: -")
        self.p_high = QLabel("Highest: -")
        self.p_low = QLabel("Lowest: -")
        perf_layout.addWidget(self.p_students, 0, 0)
        perf_layout.addWidget(self.p_avg, 0, 1)
        perf_layout.addWidget(self.p_high, 1, 0)
        perf_layout.addWidget(self.p_low, 1, 1)
        perf_group.setMinimumWidth(340)
        perf_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        summary_panels.addWidget(perf_group, 1)

        self.main_layout.addLayout(summary_panels)

        # ─── Top 10 ──────────────────────────────────────────────────
        self.top_group = QGroupBox("Top 10 Students")
        top_layout = QVBoxLayout(self.top_group)
        self.top_table = QTableWidget()
        setup_table(self.top_table, ["Pos", "Adm No", "Name", "Avg", "Div"])
        self.top_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.top_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.top_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        top_layout.addWidget(self.top_table)
        self.main_layout.addWidget(self.top_group)

        # ─── Bottom 10 ──────────────────────────────────────────────
        self.bottom_group = QGroupBox("Bottom 10 Students")
        bottom_layout = QVBoxLayout(self.bottom_group)
        self.bottom_table = QTableWidget()
        setup_table(self.bottom_table, ["Pos", "Adm No", "Name", "Avg", "Div"])
        self.bottom_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.bottom_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.bottom_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        bottom_layout.addWidget(self.bottom_table)
        self.main_layout.addWidget(self.bottom_group)

        # ─── Subject Performance ────────────────────────────────────
        self.subject_group = QGroupBox("Subject Performance Analysis")
        subject_layout = QVBoxLayout(self.subject_group)
        self.subject_table = QTableWidget()
        setup_table(self.subject_table, ["Rank", "Subject", "Average", "Passes", "Fails"])
        self.subject_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.subject_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.subject_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        subject_layout.addWidget(self.subject_table)
        self.main_layout.addWidget(self.subject_group)

        # ─── Full Broadsheet ────────────────────────────────────────
        self.full_group = QGroupBox("Full Broadsheet Table")
        full_layout = QVBoxLayout(self.full_group)
        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        full_layout.addWidget(self.table)
        self.main_layout.addWidget(self.full_group)

        # ─── Footer ──────────────────────────────────────────────────
        self.footer = QLabel("Ready.")
        self.main_layout.addWidget(self.footer)

        # ─── Events ──────────────────────────────────────────────────
        EventBus.subscribe("LEVEL_CHANGED", self._on_level_changed)
        EventBus.subscribe("RESULTS_UPDATED", self._on_data_changed)
        EventBus.subscribe("STUDENTS_UPDATED", self._on_data_changed)

    # ─── Context setters ─────────────────────────────────────────────
    def set_history_context(self, exam_id, class_name, level=None):
        self.history_level = level
        if not exam_id or not class_name:
            self.footer.setText("Invalid context.")
            return
        row = fetch_one(
            "SELECT t.academic_year_id, e.term_id FROM exams e JOIN terms t ON e.term_id = t.id WHERE e.id = ?",
            (exam_id,))
        year_id = row[0] if row else None
        term_id = row[1] if row else None
        self.context = {
            'exam_id': exam_id, 'class_name': class_name,
            'year_id': year_id, 'term_id': term_id,
            'level': level or SystemState.get_level()
        }
        # Set context label
        exam_row = fetch_one(
            "SELECT e.exam_name, t.term_name, y.year_name FROM exams e JOIN terms t ON e.term_id = t.id JOIN academic_years y ON y.id = t.academic_year_id WHERE e.id = ?",
            (exam_id,))
        if exam_row:
            exam_name, term_name, year_name = exam_row
            self.context_label.setText(f"{exam_name} – {term_name} – {year_name} – {class_name}")
        else:
            self.context_label.setText(f"Exam #{exam_id} – {class_name}")
        self._load_data()

    def clear_history_context(self):
        self.history_level = None
        self.context = None
        self.context_label.setText("No context set.")
        self.data = None
        self.footer.setText("Cleared.")
        # Clear all tables
        for widget in [self.table, self.gender_table, self.division_table,
                       self.top_table, self.bottom_table, self.subject_table]:
            widget.setRowCount(0)
            self._set_placeholder(widget)
        for key in self._card_widgets:
            self._card_widgets[key].setText("-")
        self.p_students.setText("Students: -")
        self.p_avg.setText("Class Avg: -")
        self.p_high.setText("Highest: -")
        self.p_low.setText("Lowest: -")
        self.excel_btn.setEnabled(False)
        self.pdf_btn.setEnabled(False)

    def _set_placeholder(self, table: QTableWidget):
        """Show a placeholder row when table is empty."""
        if table.rowCount() == 0:
            # The full broadsheet has no headers until a context is loaded.
            # A QTableView span must cover at least one column.
            if table.columnCount() == 0:
                table.setColumnCount(1)
            table.setRowCount(1)
            item = QTableWidgetItem("No data available.")
            item.setTextAlignment(Qt.AlignCenter)
            table.setSpan(0, 0, 1, table.columnCount())
            table.setItem(0, 0, item)
            # Make it look disabled
            item.setFlags(Qt.NoItemFlags)

    # ─── Data loading ────────────────────────────────────────────────
    def _load_data(self):
        if not self.context or self._loading:
            return
        self._loading = True
        self.refresh_btn.setEnabled(False)
        self.excel_btn.setEnabled(False)
        self.pdf_btn.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)

        # Clean up previous thread
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait()
            self._thread = None
            self._worker = None

        self._thread = QThread()
        self._worker = BroadsheetWorker(self._service, self.context)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.data_ready.connect(self._on_data_ready)
        self._worker.error.connect(self._on_error)
        # The worker performs one fetch. Always stop its thread afterwards so
        # page changes or application shutdown cannot destroy a live QThread.
        self._worker.data_ready.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._worker.data_ready.connect(self._worker.deleteLater)
        self._worker.error.connect(self._worker.deleteLater)
        # Keep the QThread wrapper alive while it remains in self._thread.
        # The next reload (or page teardown) releases it after it has stopped.
        # Calling deleteLater here leaves a stale Python reference and causes
        # "Internal C++ object ... already deleted" on a subsequent reload.
        self._thread.start()

    @Slot(BroadsheetData)
    def _on_data_ready(self, data):
        self._loading = False
        self.refresh_btn.setEnabled(True)
        self.excel_btn.setEnabled(True)
        self.pdf_btn.setEnabled(True)
        QApplication.restoreOverrideCursor()
        self.data = data
        self._populate_ui(data)
        self.footer.setText("Data loaded successfully.")

    @Slot(str)
    def _on_error(self, msg):
        self._loading = False
        self.refresh_btn.setEnabled(True)
        self.excel_btn.setEnabled(False)
        self.pdf_btn.setEnabled(False)
        QApplication.restoreOverrideCursor()
        self.footer.setText(f"Error: {msg}")
        show_error(self, f"Failed to load data:\n{msg}", title="Data Error")

    # ─── UI population ──────────────────────────────────────────────
    def _populate_ui(self, data: BroadsheetData):
        # Cards
        p = data.class_performance
        self._card_widgets['total_students'].setText(str(p['total_students']))
        self._card_widgets['class_avg'].setText(f"{p['class_average']:.2f}%")
        self._card_widgets['pass_rate'].setText(f"{p['pass_rate']:.2f}%")
        self._card_widgets['fail_rate'].setText(f"{p['fail_rate']:.2f}%")
        self._card_widgets['high_avg'].setText(f"{p['highest_average']:.2f}%")
        self._card_widgets['low_avg'].setText(f"{p['lowest_average']:.2f}%")
        self._card_widgets['best_sub'].setText(get_subject_short_name(data.best_subject) if data.best_subject else "-")
        self._card_widgets['worst_sub'].setText(get_subject_short_name(data.worst_subject) if data.worst_subject else "-")

        # Performance stats
        self.p_students.setText(f"Students: {p['total_students']}")
        self.p_avg.setText(f"Class Avg: {p['class_average']:.2f}%")
        self.p_high.setText(f"Highest: {p['highest_average']:.2f}%")
        self.p_low.setText(f"Lowest: {p['lowest_average']:.2f}%")

        # Gender
        self._populate_table(self.gender_table,
                            [["Male", data.gender_summary['Male']],
                             ["Female", data.gender_summary['Female']],
                             ["Total", data.gender_summary['Total']]],
                            ["Gender", "Count"])

        # Division
        div_rows = [[div, str(count)] for div, count in data.division_summary.items() if count > 0]
        self._populate_table(self.division_table, div_rows, ["Division", "Students"])

        # Top 10
        top_rows = [[str(s.get('position', idx+1)), s.get('admission', ''), s.get('name', ''),
                     f"{s.get('average', 0):.2f}", str(s.get('division', '-'))]
                    for idx, s in enumerate(data.top_students)]
        self._populate_table(self.top_table, top_rows, ["Pos", "Adm No", "Name", "Avg", "Div"])

        # Bottom 10
        bottom_rows = [[str(s.get('position', idx+1)), s.get('admission', ''), s.get('name', ''),
                        f"{s.get('average', 0):.2f}", str(s.get('division', '-'))]
                       for idx, s in enumerate(data.bottom_students)]
        self._populate_table(self.bottom_table, bottom_rows, ["Pos", "Adm No", "Name", "Avg", "Div"])

        # Subject Performance
        subject_rows = []
        for rank, (sub, stats) in enumerate(data.subject_ranking, 1):
            subject_rows.append([str(rank), get_subject_short_name(sub),
                                 f"{stats['average']:.2f}", str(stats['passes']), str(stats['fails'])])
        self._populate_table(self.subject_table, subject_rows, ["Rank", "Subject", "Average", "Passes", "Fails"])

        # Full Broadsheet
        subjects = data.subjects
        rows = data.rows
        headers = ["Pos", "Adm No", "Name", "Sex"] + data.subject_headers + ["Total", "Avg", "Pts", "Div"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(rows))
        for r_idx, r in enumerate(rows):
            self.table.setItem(r_idx, 0, QTableWidgetItem(str(r['Position'])))
            self.table.setItem(r_idx, 1, QTableWidgetItem(r['Admission No']))
            self.table.setItem(r_idx, 2, QTableWidgetItem(r['Student Name']))
            self.table.setItem(r_idx, 3, QTableWidgetItem(r['Gender']))
            col = 4
            for sub in subjects:
                self.table.setItem(r_idx, col, QTableWidgetItem(str(r['marks'].get(sub, "-"))))
                col += 1
            self.table.setItem(r_idx, col, QTableWidgetItem(str(r['Total'])))
            self.table.setItem(r_idx, col + 1, QTableWidgetItem(str(r['Average'])))
            self.table.setItem(r_idx, col + 2, QTableWidgetItem(str(r['Points'])))
            self.table.setItem(r_idx, col + 3, QTableWidgetItem(str(r['Division'])))
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        # Adjust table heights (so they don't scroll internally)
        for table in [self.table, self.gender_table, self.division_table,
                      self.top_table, self.bottom_table, self.subject_table]:
            self._adjust_table_height(table)

    def _populate_table(self, table: QTableWidget, rows: List[List], headers: List[str]):
        table.clearContents()
        table.setRowCount(0)
        if not rows:
            table.setRowCount(1)
            item = QTableWidgetItem("No data available.")
            item.setTextAlignment(Qt.AlignCenter)
            table.setSpan(0, 0, 1, table.columnCount())
            table.setItem(0, 0, item)
            item.setFlags(Qt.NoItemFlags)
            return
        table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                if j == 0:
                    item.setTextAlignment(Qt.AlignCenter)
                table.setItem(i, j, item)

    def _adjust_table_height(self, table: QTableWidget):
        if table.rowCount() == 0:
            table.setMinimumHeight(50)
            return
        header_h = table.horizontalHeader().height()
        row_h = table.verticalHeader().defaultSectionSize() if table.verticalHeader() else 20
        total_h = header_h + (table.rowCount() * row_h) + 8
        max_h = 600  # limit to avoid too tall
        final_h = min(total_h, max_h)
        table.setMinimumHeight(final_h)
        table.setMaximumHeight(final_h)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    # ─── Export methods ──────────────────────────────────────────────
    def _export_excel(self):
        if not self.data:
            show_error(self, "No data to export.", title="No Data")
            return
        # Convert dataclass to dict
        data_dict = self.data.to_dict()
        broadsheet_export.to_excel(self, data_dict)

    def _export_pdf(self):
        if not self.data:
            show_error(self, "No data to export.", title="No Data")
            return
        data_dict = self.data.to_dict()
        broadsheet_export.to_pdf(self, data_dict)

    # ─── Event handlers ──────────────────────────────────────────────
    def _on_level_changed(self):
        if self.context:
            self.context['level'] = SystemState.get_level()
            self._load_data()

    def _on_data_changed(self):
        if self.context and self.isVisible():
            self._load_data()

    def showEvent(self, event):
        super().showEvent(event)
        if self.context and not self.data and not self._loading:
            self._load_data()

    def closeEvent(self, event):
        # Clean up thread on close
        if self._thread is not None and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait()
        super().closeEvent(event)
