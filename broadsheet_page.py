from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, 
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QGridLayout,
    QMessageBox, QGroupBox, QAbstractItemView, QFileDialog, QScrollArea
)
from PySide6.QtCore import Qt

from db_utils import fetch_all, fetch_one
from system_state import SystemState
from event_bus import EventBus
from settings_page import get_setting
from security_settings import get_school_profile_from_db
from grade_utils import get_grade, get_points
from ui_helpers import show_error, show_info
from table_utils import setup_table
import combo_loaders

from PySide6.QtWidgets import QFrame
from class_utils import get_classes
from ranking_engine import compute_student_scores
import broadsheet_export
from datetime import datetime

class BroadsheetPage(QWidget):
    def __init__(self):
        super().__init__()
        self.all_broadsheet_data = None # To store computed data for export
        self.layout = QVBoxLayout(self)
        
        title = QLabel("ACADEMIC BROADSHEET MODULE")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        self.layout.addWidget(title)

        # =========================
        # FILTERS
        # =========================
        filters_group = QGroupBox("Context Filters")
        filters_layout = QHBoxLayout(filters_group)

        self.year_box = QComboBox()
        self.year_box.currentIndexChanged.connect(self.load_terms)
        
        self.term_box = QComboBox()
        self.term_box.currentIndexChanged.connect(self.load_exams)

        self.exam_box = QComboBox()
        
        self.class_box = QComboBox()
        self.class_box.addItems(get_classes())

        filters_layout.addWidget(QLabel("Year:"))
        filters_layout.addWidget(self.year_box)
        filters_layout.addWidget(QLabel("Term:"))
        filters_layout.addWidget(self.term_box)
        filters_layout.addWidget(QLabel("Exam:"))
        filters_layout.addWidget(self.exam_box)
        filters_layout.addWidget(QLabel("Class:"))
        filters_layout.addWidget(self.class_box)
        filters_layout.addStretch()

        self.layout.addWidget(filters_group)

        # =========================
        # ACTIONS
        # =========================
        actions_layout = QHBoxLayout()

        self.preview_btn = QPushButton("PREVIEW")
        self.preview_btn.clicked.connect(self.preview_broadsheet)
        self.preview_btn.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold; min-width: 120px;")
        
        self.excel_btn = QPushButton("EXPORT EXCEL")
        self.excel_btn.clicked.connect(self.export_excel)
        
        self.pdf_btn = QPushButton("EXPORT PDF")
        self.pdf_btn.clicked.connect(self.export_pdf)

        actions_layout.addWidget(self.preview_btn)
        actions_layout.addWidget(self.excel_btn)
        actions_layout.addWidget(self.pdf_btn)
        actions_layout.addStretch()
        
        self.layout.addLayout(actions_layout)

        # =========================
        # ANALYTICS & SUMMARIES (Scrollable Area)
        # ======================================================================
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)
        
        self.card_style = """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(30, 41, 59, 0.8), stop:1 rgba(15, 23, 42, 0.9));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 20px;
            }
            QLabel { background: transparent; }
        """

        # SECTION 2 - EXECUTIVE ANALYTICS CARDS
        self.cards_container = QWidget()
        self.cards_grid = QGridLayout(self.cards_container)
        self.cards_grid.setContentsMargins(0, 10, 0, 10)
        self.cards_grid.setSpacing(15)
        
        self.card_widgets = {}
        metrics = [
            ("Total Students", "total_students"), ("Class Average", "class_avg"), 
            ("Pass Rate", "pass_rate"), ("Fail Rate", "fail_rate"),
            ("Highest Average", "high_avg"), ("Lowest Average", "low_avg"),
            ("Best Subject", "best_sub"), ("Worst Subject", "worst_sub")
        ]
        
        for i, (label, key) in enumerate(metrics):
            frame = QFrame()
            frame.setStyleSheet(self.card_style)
            flay = QVBoxLayout(frame)
            val_lbl = QLabel("-")
            val_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #3b82f6;")
            lab_lbl = QLabel(label.upper())
            lab_lbl.setStyleSheet("font-size: 10px; color: #94a3b8; font-weight: bold;")
            flay.addWidget(val_lbl, 0, Qt.AlignCenter)
            flay.addWidget(lab_lbl, 0, Qt.AlignCenter)
            self.card_widgets[key] = val_lbl
            self.cards_grid.addWidget(frame, i // 4, i % 4)
            
        self.scroll_layout.addWidget(self.cards_container)

        # SECTION 3 - SUMMARY PANELS (Row of 3)
        summary_panels_layout = QHBoxLayout()
        
        # Panel A: Gender
        self.gender_summary_group = QGroupBox("Gender Summary")
        gender_summary_layout = QVBoxLayout(self.gender_summary_group)
        self.gender_table = QTableWidget()
        setup_table(self.gender_table, ["Gender", "Count"])
        gender_summary_layout.addWidget(self.gender_table)
        summary_panels_layout.addWidget(self.gender_summary_group)

        # Panel B: Division
        self.division_summary_group = QGroupBox("Division Summary")
        division_summary_layout = QVBoxLayout(self.division_summary_group)
        self.division_table = QTableWidget()
        setup_table(self.division_table, ["Division", "Students"])
        division_summary_layout.addWidget(self.division_table)
        summary_panels_layout.addWidget(self.division_summary_group)

        # Panel C: Performance Stats (Compact)
        self.perf_stats_group = QGroupBox("Performance Summary")
        perf_stats_layout = QGridLayout(self.perf_stats_group)
        self.p_students = QLabel("Students: -")
        self.p_avg = QLabel("Class Avg: -")
        self.p_high = QLabel("Highest: -")
        self.p_low = QLabel("Lowest: -")
        perf_stats_layout.addWidget(self.p_students, 0, 0)
        perf_stats_layout.addWidget(self.p_avg, 0, 1)
        perf_stats_layout.addWidget(self.p_high, 1, 0)
        perf_stats_layout.addWidget(self.p_low, 1, 1)
        summary_panels_layout.addWidget(self.perf_stats_group)

        self.scroll_layout.addLayout(summary_panels_layout)

        # 4. TOP 10 STUDENTS
        self.top_students_group = QGroupBox("Top 10 Students")
        top_students_layout = QVBoxLayout(self.top_students_group)
        self.top_students_table = QTableWidget()
        setup_table(self.top_students_table, ["Pos", "Adm No", "Name", "Avg", "Div"])
        top_students_layout.addWidget(self.top_students_table)
        self.scroll_layout.addWidget(self.top_students_group)

        # 5. BOTTOM 10 STUDENTS
        self.bottom_students_group = QGroupBox("Bottom 10 Students")
        bottom_students_layout = QVBoxLayout(self.bottom_students_group)
        self.bottom_students_table = QTableWidget()
        setup_table(self.bottom_students_table, ["Pos", "Adm No", "Name", "Avg", "Div"])
        bottom_students_layout.addWidget(self.bottom_students_table)
        self.scroll_layout.addWidget(self.bottom_students_group)

        # 6. SUBJECT PERFORMANCE ANALYSIS
        self.subject_perf_group = QGroupBox("Subject Performance Analysis")
        subject_perf_layout = QVBoxLayout(self.subject_perf_group)
        self.subject_perf_table = QTableWidget()
        setup_table(self.subject_perf_table, ["Subject", "Average", "Passes", "Fails"])
        subject_perf_layout.addWidget(self.subject_perf_table)
        self.scroll_layout.addWidget(self.subject_perf_group)

        # 7. FULL BROADSHEET
        self.full_broadsheet_group = QGroupBox("Full Broadsheet Table")
        full_broadsheet_layout = QVBoxLayout(self.full_broadsheet_group)
        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        full_broadsheet_layout.addWidget(self.table)
        self.scroll_layout.addWidget(self.full_broadsheet_group)

        # =========================
        # FOOTER SUMMARY
        # =========================
        self.footer = QLabel("Ready to preview...")
        self.footer.setStyleSheet("background: #1f2937; color: #10b981; padding: 10px; font-weight: bold; border-radius: 4px;")
        self.layout.addWidget(self.footer)

        # Initial Load
        self.load_years()
        EventBus.subscribe("LEVEL_CHANGED", self.refresh_all)

    def refresh_all(self):
        self.load_years()
        combo_loaders.load_classes(self.class_box)

    def load_years(self):
        combo_loaders.load_years(self.year_box)
        self.load_terms()

    def load_terms(self):
        combo_loaders.load_terms(self.term_box, self.year_box.currentData())
        self.load_exams()

    def load_exams(self):
        combo_loaders.load_exams(self.exam_box, self.term_box.currentData())

    def get_broadsheet_data(self):
        # This method is now responsible for gathering ALL data needed for UI and export
        exam_id = self.exam_box.currentData()
        class_name = self.class_box.currentText()
        level = SystemState.get_level()

        if not (exam_id and class_name):
            return None # Return early if essential filters are missing

        # 1. Get Ranking Summary (Position, Points, Division)
        ranking_summary = compute_student_scores(level, exam_id)
        # Filter ranking by class in-memory (No N+1 queries)
        ranking_summary = [s for s in ranking_summary if s.get('class') == class_name]
        
        if not ranking_summary:
            return None # No students in this class for the selected exam

        # 2. Get all enrolled subjects for this class/term
        year_row = fetch_one("""
            SELECT academic_year_id FROM terms WHERE id = (SELECT term_id FROM exams WHERE id=?)
        """, (exam_id,))
        if not year_row:
            return None
        year_id = year_row[0]
        term_id = self.term_box.currentData()

        subjects = [r[0] for r in fetch_all("""
            SELECT DISTINCT e.subject_name 
            FROM enrollments e
            JOIN students s ON e.admission_no = s.admission_no
            WHERE s.class = ? AND e.academic_year_id = ? AND e.term_id = ?
            ORDER BY e.subject_name
        """, (class_name, year_id, term_id))]

        # 3. Get all marks for these students/exam
        results_raw = fetch_all("""
            SELECT admission_no, subject_name, marks
            FROM results
            WHERE exam_id = ?
        """, (exam_id,))
        
        marks_map = {}
        for adm, sub, marks in results_raw:
            if adm not in marks_map: marks_map[adm] = {}
            marks_map[adm][sub] = marks

        # 4. Assemble final rows
        rows = []
        for s in ranking_summary:
            # Ensure 'marks' is initialized for each student
            row_data = {
                'Position': s['position'],
                'Admission No': s['admission'],
                'Student Name': s['name'],
                'Gender': s.get('gender', '-'),
                'marks': {},
                'Total': 0,
                'Average': s['average'],
                'Points': s['points'],
                'Division': s['division']
            } # Initialize marks dict
            
            student_total_marks = 0
            student_subject_count = 0
            for sub in subjects:
                m = marks_map.get(s['admission'], {}).get(sub, "-")
                row_data['marks'][sub] = m
                if isinstance(m, int):
                    student_total_marks += m
                    student_subject_count += 1
            
            row_data['Total'] = student_total_marks
            rows.append(row_data)

        # ======================================================================
        # NEW CALCULATIONS FOR ANALYTICS & SUMMARIES
        # ======================================================================
        
        # Filter for READY students for calculations that require valid scores
        ready_students = [s for s in ranking_summary if s['status'] == 'READY']
        
        # 1. Class Performance Analysis
        total_students_in_class = len(ranking_summary)
        class_averages = [s['average'] for s in ready_students]
        
        class_performance = {
            'total_students': total_students_in_class,
            'class_average': round(sum(class_averages) / len(class_averages), 2) if class_averages else 0,
            'highest_average': max(class_averages) if class_averages else 0,
            'lowest_average': min(class_averages) if class_averages else 0,
            'pass_count': sum(1 for s in ranking_summary if s['division'] in ['I', 'II', 'III', 'IV']),
            'fail_count': sum(1 for s in ranking_summary if s['division'] == '0' or s['status'] == 'INCOMPLETE'),
            'pass_rate': 0,
            'fail_rate': 0
        }
        if total_students_in_class > 0:
            class_performance['pass_rate'] = round((class_performance['pass_count'] / total_students_in_class) * 100, 2)
            class_performance['fail_rate'] = round((class_performance['fail_count'] / total_students_in_class) * 100, 2)

        # 2. Gender Summary
        male_count = sum(1 for s in ranking_summary if s['gender'] == 'Male')
        female_count = sum(1 for s in ranking_summary if s['gender'] == 'Female')
        gender_summary = {
            'Male': male_count,
            'Female': female_count,
            'Total': male_count + female_count
        }

        # 3. Division Summary (reuse div_counts from broadsheet table logic)
        div_counts = {"I": 0, "II": 0, "III": 0, "IV": 0, "0": 0, "Incomplete": 0}
        for s in ranking_summary:
            div = str(s['division'])
            if s['status'] == 'INCOMPLETE':
                div_counts['Incomplete'] += 1
            elif div in div_counts:
                div_counts[div] += 1
            else: # Handle any other unexpected division values
                pass 
        division_summary = div_counts

        # 4. Top 10 Students
        top_students = []
        if ready_students:
            # ready_students retains ranking order; take first 10
            top_students = ready_students[:min(10, len(ready_students))]

        # 5. Bottom 10 Students
        bottom_students = []
        if ready_students:
            # Determine bottom performers by lowest average
            bottom_students = sorted(ready_students, key=lambda x: x.get('average', 0))[:min(10, len(ready_students))]

        # 6. Subject Performance Analysis & 7. Subject Ranking
        subject_performance = {}
        for sub in subjects:
            total_marks_for_sub = 0
            count_for_sub = 0
            passes_for_sub = 0
            fails_for_sub = 0
            for student_row in rows:
                mark = student_row['marks'].get(sub)
                if isinstance(mark, int):
                    total_marks_for_sub += mark
                    count_for_sub += 1
                    if mark >= 50: # Assuming 50 is a pass mark for individual subjects
                        passes_for_sub += 1
                    else:
                        fails_for_sub += 1
            
            avg_for_sub = round(total_marks_for_sub / count_for_sub, 2) if count_for_sub > 0 else 0
            subject_performance[sub] = {'average': avg_for_sub, 'passes': passes_for_sub, 'fails': fails_for_sub}
        
        # Find best/worst subject
        best_subject = max(subject_performance, key=lambda s: subject_performance[s]['average']) if subject_performance else None
        worst_subject = min(subject_performance, key=lambda s: subject_performance[s]['average']) if subject_performance else None
        
        subject_ranking = sorted(subject_performance.items(), key=lambda item: item[1]['average'], reverse=True)

        # Compute max/min averages for return metadata
        if subject_performance:
            max_avg = subject_performance[best_subject]['average'] if best_subject else 0
            min_avg = subject_performance[worst_subject]['average'] if worst_subject else 0
            subject_ranking = sorted(subject_performance.items(), key=lambda item: item[1]['average'], reverse=True)
        else:
            max_avg, min_avg = 0, 0
            subject_ranking = []

        return {
            'subjects': subjects,
            'rows': rows,
            'meta': {
                'year': self.year_box.currentText(),
                'term': self.term_box.currentText(),
                'exam': self.exam_box.currentText(),
                'class': class_name,
                'level': level,
                'school_profile': get_school_profile_from_db(), # Fetch school profile
                'generated_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Actual generated date
            },
            'class_performance': class_performance,
            'gender_summary': gender_summary,
            'division_summary': division_summary,
            'top_students': top_students,
            'bottom_students': bottom_students,
            'subject_performance': subject_performance,
            'subject_ranking': subject_ranking,
            # Add best/worst subject info directly to data for easier access in export
            'best_subject': best_subject,
            'worst_subject': worst_subject,
            'max_avg': max_avg, 'min_avg': min_avg,
            'settings': { # Fetch relevant settings
                'show_gender_summary': get_setting('show_gender_summary', '1') == '1',
                'show_subject_ranking': get_setting('show_subject_ranking', '1') == '1',
                'show_logo': get_setting('show_logo', '1') == '1',
                'show_watermark': get_setting('show_watermark', '1') == '1',
            }
        }
        
    def preview_broadsheet(self):
        self.all_broadsheet_data = self.get_broadsheet_data() # Store data for export
        data = self.all_broadsheet_data
        if not data:
            show_error(self, "No results found for the selected criteria.", title="No Data")
            return

        subjects = data['subjects']
        rows = data['rows']
        
        # Build Table
        headers = ["Pos", "Adm No", "Name", "Sex"] + subjects + ["Total", "Avg", "Pts", "Div"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(rows))

        for r_idx, r in enumerate(rows):
            self.table.setItem(r_idx, 0, QTableWidgetItem(str(r['Position'])))
            self.table.setItem(r_idx, 1, QTableWidgetItem(r['Admission No']))
            self.table.setItem(r_idx, 2, QTableWidgetItem(r['Student Name']))
            self.table.setItem(r_idx, 3, QTableWidgetItem(r['Gender']))
            
            col_offset = 4
            for s_idx, sub in enumerate(subjects):
                val = r['marks'][sub]
                self.table.setItem(r_idx, col_offset + s_idx, QTableWidgetItem(str(val)))
            
            end_offset = col_offset + len(subjects)
            self.table.setItem(r_idx, end_offset, QTableWidgetItem(str(r['Total'])))
            self.table.setItem(r_idx, end_offset + 1, QTableWidgetItem(str(r['Average'])))
            self.table.setItem(r_idx, end_offset + 2, QTableWidgetItem(str(r['Points'])))
            self.table.setItem(r_idx, end_offset + 3, QTableWidgetItem(str(r['Division'])))

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # Update Footer (Class Average is now from class_performance)
        class_avg = data['class_performance']['class_average']
        summary_text = (
            f"Students: {data['class_performance']['total_students']} | "
            f"Div I: {data['division_summary']['I']} | Div II: {data['division_summary']['II']} | Div III: {data['division_summary']['III']} | "
            f"Div IV: {data['division_summary']['IV']} | Div 0: {data['division_summary']['0']} | Incomplete: {data['division_summary']['Incomplete']} | "
            f"Class Average: {class_avg}%"
        )
        self.footer.setText(summary_text)

        # Update new analytics sections
        self._update_class_performance_ui(data['class_performance'])
        self._update_gender_summary_ui(data['gender_summary'], data['settings']['show_gender_summary'])
        self._update_division_summary_ui(data['division_summary'])
        self._update_top_bottom_students_ui(data['top_students'], data['bottom_students'])
        self._update_subject_performance_ui(data['subject_performance'])

        # Expand tables to show all rows (disable internal scrolling)
        self._expand_tables([
            self.table,
            self.gender_table,
            self.division_table,
            self.top_students_table,
            self.bottom_students_table,
            self.subject_perf_table
        ])

    def _expand_tables(self, tables):
        """Set table heights so all rows are visible and disable internal scrollbars."""
        for t in tables:
            # Disable internal scrollbars
            t.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            t.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

            header_h = t.horizontalHeader().height() if t.horizontalHeader() else 0
            # If no rows, still show one row height
            rows = t.rowCount()
            row_h = t.verticalHeader().defaultSectionSize() if t.verticalHeader() else 20
            total_h = header_h + max(1, rows) * row_h + 8
            # Cap very large heights to avoid runaway windows, allow scroll area/window to handle if needed
            max_allowed = 800 if t == self.table else 400
            total_h = min(total_h, max_allowed)
            if t == self.table: t.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            t.setMinimumHeight(total_h)
            t.setMaximumHeight(total_h)

    def _update_class_performance_ui(self, class_performance):
        self.card_widgets['total_students'].setText(str(class_performance['total_students']))
        self.card_widgets['class_avg'].setText(f"{class_performance['class_average']}%")
        self.card_widgets['pass_rate'].setText(f"{class_performance['pass_rate']}%")
        self.card_widgets['fail_rate'].setText(f"{class_performance['fail_rate']}%")
        self.card_widgets['high_avg'].setText(f"{class_performance['highest_average']}%")
        self.card_widgets['low_avg'].setText(f"{class_performance['lowest_average']}%")
        
        self.p_students.setText(f"Students: {class_performance['total_students']}")
        self.p_avg.setText(f"Class Avg: {class_performance['class_average']}%")
        self.p_high.setText(f"Highest: {class_performance['highest_average']}%")
        self.p_low.setText(f"Lowest: {class_performance['lowest_average']}%")

    def _update_gender_summary_ui(self, gender_summary, show_gender_summary):
        self.gender_summary_group.setVisible(show_gender_summary)
        if not show_gender_summary: return

        self.gender_table.setRowCount(3)
        self.gender_table.setItem(0, 0, QTableWidgetItem("Male"))
        self.gender_table.setItem(0, 1, QTableWidgetItem(str(gender_summary['Male'])))
        self.gender_table.setItem(1, 0, QTableWidgetItem("Female"))
        self.gender_table.setItem(1, 1, QTableWidgetItem(str(gender_summary['Female'])))
        self.gender_table.setItem(2, 0, QTableWidgetItem("Total"))
        self.gender_table.setItem(2, 1, QTableWidgetItem(str(gender_summary['Total'])))
        self.gender_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def _update_division_summary_ui(self, division_summary):
        self.division_table.setRowCount(len(division_summary))
        for r_idx, (div, count) in enumerate(division_summary.items()):
            self.division_table.setItem(r_idx, 0, QTableWidgetItem(div))
            self.division_table.setItem(r_idx, 1, QTableWidgetItem(str(count)))
        self.division_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def _update_top_bottom_students_ui(self, top_students, bottom_students):
        # Top 10
        self.top_students_table.setRowCount(len(top_students))
        for r_idx, s in enumerate(top_students):
            self.top_students_table.setItem(r_idx, 0, QTableWidgetItem(str(s['position'])))
            self.top_students_table.setItem(r_idx, 1, QTableWidgetItem(s['admission']))
            self.top_students_table.setItem(r_idx, 2, QTableWidgetItem(s['name']))
            self.top_students_table.setItem(r_idx, 3, QTableWidgetItem(str(s['average'])))
            self.top_students_table.setItem(r_idx, 4, QTableWidgetItem(str(s['division'] if s['division'] else '-')))
        self.top_students_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.top_students_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch) # Name column

        # Bottom 10
        self.bottom_students_table.setRowCount(len(bottom_students))
        for r_idx, s in enumerate(bottom_students):
            self.bottom_students_table.setItem(r_idx, 0, QTableWidgetItem(str(s['position'])))
            self.bottom_students_table.setItem(r_idx, 1, QTableWidgetItem(s['admission']))
            self.bottom_students_table.setItem(r_idx, 2, QTableWidgetItem(s['name']))
            self.bottom_students_table.setItem(r_idx, 3, QTableWidgetItem(str(s['average'])))
            self.bottom_students_table.setItem(r_idx, 4, QTableWidgetItem(str(s['division'] if s['division'] else '-')))
        self.bottom_students_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.bottom_students_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch) # Name column

    def _update_subject_performance_ui(self, subject_performance):
        self.subject_perf_table.setRowCount(len(subject_performance))
        ranking = sorted(subject_performance.items(), key=lambda it: it[1]['average'], reverse=True)

        for r_idx, (sub_name, stats) in enumerate(ranking):
            self.subject_perf_table.setItem(r_idx, 0, QTableWidgetItem(str(r_idx+1)))
            self.subject_perf_table.setItem(r_idx, 1, QTableWidgetItem(sub_name))
            self.subject_perf_table.setItem(r_idx, 2, QTableWidgetItem(str(stats['average'])))
            self.subject_perf_table.setItem(r_idx, 3, QTableWidgetItem(str(stats['passes'])))
            self.subject_perf_table.setItem(r_idx, 4, QTableWidgetItem(str(stats['fails'])))
            
        if ranking:
            self.card_widgets['best_sub'].setText(ranking[0][0][:10])
            self.card_widgets['best_sub'].setToolTip(ranking[0][0])
            self.card_widgets['worst_sub'].setText(ranking[-1][0][:10])
            self.card_widgets['worst_sub'].setToolTip(ranking[-1][0])

        self.subject_perf_table.setColumnCount(5)
        self.subject_perf_table.setHorizontalHeaderLabels(["Rank", "Subject", "Average", "Passes", "Fails"])
        self.subject_perf_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def export_excel(self):
        if not self.all_broadsheet_data:
            show_error(self, "Please preview the broadsheet first.", title="No Data")
            return
        broadsheet_export.to_excel(self, self.all_broadsheet_data)

    def export_pdf(self):
        if not self.all_broadsheet_data:
            show_error(self, "Please preview the broadsheet first.", title="No Data")
            return
        broadsheet_export.to_pdf(self, self.all_broadsheet_data)
