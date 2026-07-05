from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGridLayout,
    QSizePolicy
)

from PySide6.QtGui import QIcon, QFont
from app_paths import icon_path
from event_bus import EventBus
from system_state import SystemState
from db_utils import get_cursor
from ui.cards import PremiumStatCard

class GlassButton(QPushButton):
    """Modern glassmorphic button with icon and text for quick actions."""

    def __init__(self, text, icon_path=None):
        super().__init__()
        self.setText(text)
        if icon_path:
            self.setIcon(QIcon(icon_path))

        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(48)
        self.setMaximumHeight(58)
        self.setIconSize(QSize(22, 22))
        
        # Set font
        font = QFont()
        font.setPointSize(10)
        font.setWeight(QFont.Weight.Bold)
        self.setFont(font)


def _icon(name):
    """Helper to get a shared icon path."""
    path = icon_path(name)
    return str(path) if path.exists() else ""


class DashboardHome(QWidget):
    """Modern dashboard home page with KPIs, quick actions, and school information."""

    open_students = Signal()
    open_academics = Signal()
    open_exams = Signal()
    open_results = Signal()
    open_school = Signal()
    open_reports = Signal()
    open_ranking = Signal()
    open_readiness = Signal()
    open_history = Signal()
    open_broadsheet = Signal()
    open_report_book = Signal()

  

    def __init__(self):
       super().__init__()
       self._needs_refresh = False
       self.build_ui()

    # Load dashboard immediately
       self.load_dashboard()

    # Refresh automatically when data changes
       EventBus.subscribe("STUDENTS_UPDATED", self.load_dashboard)
       EventBus.subscribe("SUBJECTS_UPDATED", self.load_dashboard)
       EventBus.subscribe("RESULTS_UPDATED", self.load_dashboard)
       EventBus.subscribe("EXAMS_UPDATED", self.load_dashboard)
       EventBus.subscribe("LEVEL_CHANGED", self.load_dashboard)
       EventBus.subscribe("SCHOOL_PROFILE_UPDATED", self.load_dashboard)

    def build_ui(self):
        """Build the complete dashboard UI with improved layout and styling."""
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Main layout with reduced margins for better space usage
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        # ====== HEADER SECTION ======
        header = self._build_header()
        root.addWidget(header)

        # ====== MAIN CONTENT AREA ======
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Left: KPI Cards
        kpi_section = self._build_kpi_section()
        content_layout.addWidget(kpi_section, 3)

        # Right: Quick Actions & School Info
        right_panel = self._build_right_panel()
        content_layout.addWidget(right_panel, 2)

        root.addLayout(content_layout, 1)

    def _build_header(self):
        """Build the compact, modern header section."""
        header = QFrame()
        header.setObjectName("HeaderFrame")
        header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        header.setMinimumHeight(78)

        layout = QVBoxLayout(header)
        layout.setContentsMargins(22, 10, 22, 8)
        layout.setSpacing(3)

        # School Name
        self.school_lbl = QLabel("Loading School...")
        self.school_lbl.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(17)
        font.setWeight(QFont.Weight.Bold)
        self.school_lbl.setFont(font)
        self.school_lbl.setProperty("variant", "accent")

        # Subtitle
        subtitle = QLabel("School Results Management System")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(9)
        subtitle.setFont(subtitle_font)
        subtitle.setProperty("variant", "muted")

        # Active Exam
        self.exam_lbl = QLabel("Loading Exam...")
        self.exam_lbl.setAlignment(Qt.AlignCenter)
        exam_font = QFont()
        exam_font.setPointSize(9)
        exam_font.setWeight(QFont.Weight.DemiBold)
        self.exam_lbl.setFont(exam_font)
        self.exam_lbl.setProperty("variant", "success")

        layout.addWidget(self.school_lbl, alignment=Qt.AlignCenter)
        layout.addWidget(subtitle, alignment=Qt.AlignCenter)
        layout.addWidget(self.exam_lbl, alignment=Qt.AlignCenter)

        return header

    def _build_kpi_section(self):
        """Build the left panel with KPI cards."""
        container = QFrame()
        container.setObjectName("KPIContainer")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(9)

        # Section Title - Bold and prominent
        title = QLabel("Key Performance Indicators")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setWeight(QFont.Weight.Bold)
        title.setFont(title_font)
        title.setProperty("variant", "accent")
        layout.addWidget(title)

        # KPI Grid container with background
        grid_container = QFrame()
        grid_layout_container = QVBoxLayout(grid_container)
        grid_layout_container.setContentsMargins(10, 10, 10, 10)
        grid_layout_container.setSpacing(0)

        # KPI Grid (3 columns x 3 rows)
        kpi_grid = QGridLayout()
        kpi_grid.setHorizontalSpacing(8)
        kpi_grid.setVerticalSpacing(8)
        kpi_grid.setContentsMargins(0, 0, 0, 0)

        # Create KPI Cards
        self.students_card = PremiumStatCard(
            "Students",
            "Registered learners",
            _icon("students.svg"),
            "primary"
        )
        self.subjects_card = PremiumStatCard(
            "Subjects",
            "Configured subjects",
            _icon("academics.svg"),
            "secondary"
        )
        self.classes_card = PremiumStatCard(
            "Classes",
            "Active class groups",
            _icon("school.svg"),
            "success"
        )
        self.exams_card = PremiumStatCard(
            "Exams",
            "Tracked assessments",
            _icon("exams.svg"),
            "warning"
        )
        self.results_card = PremiumStatCard(
            "Results",
            "Stored result entries",
            _icon("results.svg"),
            "success"
        )
        self.male_card = PremiumStatCard(
            "Male Students",
            "Learners marked male",
            _icon("students.svg"),
            "primary"
        )
        self.female_card = PremiumStatCard(
            "Female Students",
            "Learners marked female",
            _icon("students.svg"),
            "danger"
        )
        self.completed_exam_card = PremiumStatCard(
            "Completed Exams",
            "Archived exam records",
            _icon("exams.svg"),
            "secondary"
        )

        # Layout cards in grid
        cards = [
            (self.students_card, 0, 0),
            (self.subjects_card, 0, 1),
            (self.classes_card, 0, 2),
            (self.exams_card, 0, 3),
            (self.results_card, 1, 0),
            (self.male_card, 1, 1),
            (self.female_card, 1, 2),
            (self.completed_exam_card, 1, 3),
        ]

        for card, row, col in cards:
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            kpi_grid.addWidget(card, row, col)

        for i in range(4):
            kpi_grid.setColumnStretch(i, 1)

        grid_layout_container.addLayout(kpi_grid)
        layout.addWidget(grid_container, 1)

        return container

    def _build_right_panel(self):
        """Build the right panel with quick actions and school info."""
        container = QFrame()

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # ====== QUICK ACTIONS ======
        quick_panel = self._build_quick_actions()
        layout.addWidget(quick_panel, 0)

        # ====== SCHOOL INFORMATION ======
        school_panel = self._build_school_info()
        layout.addWidget(school_panel, 0)
        layout.addStretch(1)

        return container

    def _build_quick_actions(self):
        """Build the quick actions panel with button grid."""
        panel = QFrame()
        panel.setObjectName("QuickActionsPanel")
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Section Title - Bold and prominent
        title = QLabel("Quick Actions")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setWeight(QFont.Weight.Bold)
        title.setFont(title_font)
        title.setProperty("variant", "accent")
        layout.addWidget(title)

        self.add_student_btn = GlassButton("Add Student", _icon("students.svg"))
        self.add_exam_btn = GlassButton("Add Exam", _icon("exams.svg"))
        self.school_btn = GlassButton("School", _icon("school.svg"))
        self.subjects_btn = GlassButton("Subjects", _icon("academics.svg"))
        self.history_btn = GlassButton("History", _icon("dashboard.svg"))

        button_grid = QGridLayout()
        button_grid.setContentsMargins(0, 0, 0, 0)
        button_grid.setHorizontalSpacing(8)
        button_grid.setVerticalSpacing(8)

        button_grid.addWidget(self.add_student_btn, 0, 0)
        button_grid.addWidget(self.add_exam_btn, 0, 1)
        button_grid.addWidget(self.school_btn, 0, 2)
        button_grid.addWidget(self.subjects_btn, 1, 0)
        button_grid.addWidget(self.history_btn, 1, 1)

        for i in range(3):
            button_grid.setColumnStretch(i, 1)

        layout.addLayout(button_grid)

        self.add_student_btn.clicked.connect(self.open_students.emit)
        self.add_exam_btn.clicked.connect(self.open_exams.emit)
        self.school_btn.clicked.connect(self.open_school.emit)
        self.subjects_btn.clicked.connect(self.open_academics.emit)
        self.history_btn.clicked.connect(self.open_history.emit)

        return panel

    def _build_school_info(self):
        """Build the school information panel."""
        panel = QFrame()
        panel.setObjectName("SchoolInfoPanel")
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        panel.setMinimumHeight(205)
        panel.setMaximumHeight(245)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # Section Title - Bold and prominent
        title = QLabel("School Information")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setWeight(QFont.Weight.Bold)
        title.setFont(title_font)
        title.setProperty("variant", "accent")
        layout.addWidget(title)

        # Info Label - Centered when empty
        self.school_info_lbl = QLabel("Loading...")
        self.school_info_lbl.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.school_info_lbl.setWordWrap(True)
        info_font = QFont()
        info_font.setPointSize(10)
        self.school_info_lbl.setFont(info_font)
        self.school_info_lbl.setProperty("variant", "muted")
        layout.addWidget(self.school_info_lbl)
        layout.addStretch()

        return panel

    # =====================================
    # DATABASE LOADER
    # =====================================

    def load_dashboard(self):
        if not self.isVisible():
            self._needs_refresh = True
            return

        try:
            with get_cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM students")
                students = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM subjects")
                subjects = cur.fetchone()[0]

                cur.execute("SELECT COUNT(DISTINCT class) FROM students")
                classes = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM exams WHERE status != 'COMPLETED'")
                exams = cur.fetchone()[0]

                cur.execute("""
                    SELECT COUNT(*) FROM results r
                    JOIN exams e ON r.exam_id = e.id
                    WHERE e.status != 'COMPLETED'
                """)
                results = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM students WHERE gender='Male'")
                males = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM students WHERE gender='Female'")
                females = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM exams WHERE status='COMPLETED'")
                completed_exams = cur.fetchone()[0]

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
                current_level = SystemState.get_level()

                cur.execute("""
                SELECT exam_name
                FROM exams
                WHERE status='OPEN'
    
                  AND level=?
                  ORDER BY id DESC
                  LIMIT 1
                """, (current_level,))


                exam = cur.fetchone()
                if exam:
                    self.exam_lbl.setText(f"Active Exam: {exam[0]}")
                else:
                    self.exam_lbl.setText("No Active Exam")

            self.students_card.set_value(students)
            self.subjects_card.set_value(subjects)
            self.classes_card.set_value(classes)
            self.exams_card.set_value(exams)
            self.results_card.set_value(results)
            self.male_card.set_value(males)
            self.female_card.set_value(females)
            self.completed_exam_card.set_value(completed_exams)

        except Exception as error:
            print(f"[ERROR] Dashboard failed to load: {error}")
            self.school_lbl.setText("Dashboard Error")
            self.exam_lbl.setText(f"Could not load data: {error}")

    def showEvent(self, event):
        super().showEvent(event)
        if self._needs_refresh:
            self._needs_refresh = False
            self.load_dashboard()
