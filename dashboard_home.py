from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGridLayout
)

from db_utils import get_cursor


class GlassCard(QFrame):

    def __init__(self, title, value="0"):
        super().__init__()

        self.setObjectName("GlassCard")

        layout = QVBoxLayout(self)

        self.value_lbl = QLabel(str(value))
        self.value_lbl.setAlignment(Qt.AlignCenter)

        self.title_lbl = QLabel(title)
        self.title_lbl.setAlignment(Qt.AlignCenter)

        self.value_lbl.setStyleSheet("""
            font-size:32px;
            font-weight:800;
            color:white;
            background:transparent;
            border:none;
        """)

        self.title_lbl.setStyleSheet("""
            font-size:13px;
            color:#94a3b8;
            background:transparent;
            border:none;
        """)

        layout.addStretch()
        layout.addWidget(self.value_lbl)
        layout.addWidget(self.title_lbl)
        layout.addStretch()

        self.setStyleSheet("""
        QFrame#GlassCard{
            background:rgba(15,23,42,0.92);
            border:1px solid rgba(255,255,255,0.08);
            border-radius:22px;
        }
        """)

    def set_value(self, value):
        self.value_lbl.setText(str(value))



class DashboardHome(QWidget):

    open_students = Signal()
    open_teachers = Signal()
    open_exams = Signal()
    open_results = Signal()
    open_school = Signal()
    open_reports = Signal()


    def __init__(self):
        super().__init__()

        self.build_ui()

    def build_ui(self):

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(20,20,20,20)
        self.root.setSpacing(15)

        # =====================================
        # HERO SECTION
        # =====================================

        self.hero = QFrame()

        self.hero.setStyleSheet("""
        QFrame{
            background:qlineargradient(
                x1:0,y1:0,x2:1,y2:1,
                stop:0 rgba(15,23,42,0.98),
                stop:1 rgba(30,41,59,0.98)
            );

            border:1px solid rgba(255,255,255,0.06);
            border-radius:28px;
        }
        """)

        self.hero_layout = QVBoxLayout(self.hero)

        self.school_lbl = QLabel("Loading School...")
        self.school_lbl.setAlignment(Qt.AlignCenter)

        self.school_lbl.setStyleSheet("""
            font-size:32px;
            font-weight:800;
            color:white;
            background:transparent;
            border:none;
        """)

        self.subtitle_lbl = QLabel(
            "School Report Management System"
        )

        self.subtitle_lbl.setAlignment(
            Qt.AlignCenter
        )

        self.subtitle_lbl.setStyleSheet("""
            color:#cbd5e1;
            font-size:14px;
            background:transparent;
            border:none;
        """)

        self.exam_lbl = QLabel(
            "Loading Exam..."
        )

        self.exam_lbl.setAlignment(
            Qt.AlignCenter
        )

        self.exam_lbl.setStyleSheet("""
            color:#10b981;
            font-size:14px;
            font-weight:700;
            background:transparent;
            border:none;
        """)

        self.footer_lbl = QLabel(
            "Powered by Mark Deals"
        )

        self.footer_lbl.setAlignment(
            Qt.AlignCenter
        )

        self.footer_lbl.setStyleSheet("""
            color:#94a3b8;
            font-size:12px;
            background:transparent;
            border:none;
        """)

        self.hero_layout.addWidget(
            self.school_lbl
        )

        self.hero_layout.addWidget(
            self.subtitle_lbl
        )

        self.hero_layout.addWidget(
            self.exam_lbl
        )

        self.hero_layout.addWidget(
            self.footer_lbl
        )

        self.root.addWidget(
            self.hero
        )

        # =====================================
        # KPI CARDS
        # =====================================

        self.kpi_grid = QGridLayout()
        self.kpi_grid.setHorizontalSpacing(15)
        self.kpi_grid.setVerticalSpacing(15)

        self.students_card = GlassCard("Students")
        self.teachers_card = GlassCard("Teachers")
        self.subjects_card = GlassCard("Subjects")

        self.classes_card = GlassCard("Classes")
        self.exams_card = GlassCard("Exams")
        self.results_card = GlassCard("Results")

        self.kpi_grid.addWidget(
            self.students_card, 0, 0
        )

        self.kpi_grid.addWidget(
            self.teachers_card, 0, 1
        )

        self.kpi_grid.addWidget(
            self.subjects_card, 0, 2
        )

        self.kpi_grid.addWidget(
            self.classes_card, 1, 0
        )

        self.kpi_grid.addWidget(
            self.exams_card, 1, 1
        )

        self.kpi_grid.addWidget(
            self.results_card, 1, 2
        )

        self.root.addLayout(
            self.kpi_grid
        )

        # =====================================
        # ANALYTICS ROW
        # =====================================

        self.analytics = QHBoxLayout()

        self.male_card = GlassCard(
            "Male Students"
        )

        self.female_card = GlassCard(
            "Female Students"
        )

        self.open_exam_card = GlassCard(
            "Open Exams"
        )

        self.analytics.addWidget(
            self.male_card
        )

        self.analytics.addWidget(
            self.female_card
        )

        self.analytics.addWidget(
            self.open_exam_card
        )

        self.root.addLayout(
            self.analytics
        )


        # =====================================
        # LOWER SECTION
        # =====================================

        self.lower_row = QHBoxLayout()

        self.school_panel = QFrame()
        self.school_panel.setStyleSheet("""
        QFrame{
            background:rgba(15,23,42,0.92);
            border:1px solid rgba(255,255,255,0.08);
            border-radius:22px;
        }
        """)

        school_layout = QVBoxLayout(
            self.school_panel
        )

        self.school_info_title = QLabel(
            "School Information"
        )

        self.school_info_title.setStyleSheet("""
            font-size:18px;
            font-weight:700;
            color:white;
            background:transparent;
            border:none;
        """)

        self.school_info_lbl = QLabel(
            "Loading..."
        )

        self.school_info_lbl.setWordWrap(True)

        self.school_info_lbl.setStyleSheet("""
            color:#cbd5e1;
            background:transparent;
            border:none;
            padding:5px;
        """)

        school_layout.addWidget(
            self.school_info_title
        )

        school_layout.addWidget(
            self.school_info_lbl
        )

        self.quick_panel = QFrame()

        self.quick_panel.setStyleSheet("""
        QFrame{
            background:rgba(15,23,42,0.92);
            border:1px solid rgba(255,255,255,0.08);
            border-radius:22px;
        }
        """)

        quick_layout = QGridLayout(
            self.quick_panel
        )

        self.student_btn = QPushButton("New Student")
        self.teachers_btn = QPushButton("Teachers")
        self.exams_btn = QPushButton("Exams")
        self.results_btn = QPushButton("Results")
        self.school_btn = QPushButton("School")
        self.reports_btn = QPushButton("Reports")

        buttons = [
            self.student_btn,
            self.teachers_btn,
            self.exams_btn,
            self.results_btn,
            self.school_btn,
            self.reports_btn
        ]

        for i, btn in enumerate(buttons):

            btn.setMinimumHeight(55)

            quick_layout.addWidget(
                btn,
                i // 2,
                i % 2
            )

        self.lower_row.addWidget(
            self.school_panel,
            2
        )

        self.lower_row.addWidget(
            self.quick_panel,
            3
        )

        self.student_btn.clicked.connect(
            self.open_students.emit
        )

        self.teachers_btn.clicked.connect(
            self.open_teachers.emit
        )

        self.exams_btn.clicked.connect(
            self.open_exams.emit
        )

        self.results_btn.clicked.connect(
            self.open_results.emit
        )

        self.school_btn.clicked.connect(
            self.open_school.emit
        )

        self.reports_btn.clicked.connect(
            self.open_reports.emit
        )


        self.root.addLayout(
            self.lower_row
        )

        self.load_dashboard()

    # =====================================
    # DATABASE LOADER
    # =====================================

    def load_dashboard(self):

        try:
            with get_cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM students")
                students = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM teachers")
                teachers = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM subjects")
                subjects = cur.fetchone()[0]

                cur.execute("SELECT COUNT(DISTINCT class) FROM students")
                classes = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM exams")
                exams = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM results")
                results = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM students WHERE gender='Male'")
                males = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM students WHERE gender='Female'")
                females = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM exams WHERE status='OPEN'")
                open_exams = cur.fetchone()[0]

                cur.execute("""
                    SELECT school_name, head_teacher, academic_master, school_phone, school_email
                    FROM school_profile LIMIT 1
                """)
                row = cur.fetchone()

                if row:
                    school_name, head, academic, phone, email = row
                    self.school_lbl.setText(school_name)
                    self.school_info_lbl.setText(
                        f"Head Teacher: {head}\n\n"
                        f"Academic Master: {academic}\n\n"
                        f"Phone: {phone}\n\n"
                        f"Email: {email}"
                    )

                cur.execute("SELECT exam_name FROM exams WHERE status='OPEN' LIMIT 1")
                exam = cur.fetchone()
                if exam:
                    self.exam_lbl.setText(f"Active Exam: {exam[0]}")

            self.students_card.set_value(students)
            self.teachers_card.set_value(teachers)
            self.subjects_card.set_value(subjects)
            self.classes_card.set_value(classes)
            self.exams_card.set_value(exams)
            self.results_card.set_value(results)
            self.male_card.set_value(males)
            self.female_card.set_value(females)
            self.open_exam_card.set_value(open_exams)

        except Exception as error:
            print(f"[ERROR] Dashboard failed to load: {error}")
            self.school_lbl.setText("Dashboard Error")
            self.exam_lbl.setText(f"Could not load data: {error}")

