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
from event_bus import EventBus
from system_state import SystemState
from db_utils import get_cursor
import os


class GlassCard(QFrame):
    """Modern glassmorphic card for displaying key performance indicators."""

    def __init__(self, title, value="0"):
        super().__init__()

        self.setObjectName("GlassCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(128)
        self.setMaximumHeight(138)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        self.title_lbl = QLabel(title)
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setWordWrap(True)
        self.title_lbl.setObjectName("MetricTitle")
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setWeight(QFont.Weight.Bold)
        self.title_lbl.setFont(title_font)

        self.value_lbl = QLabel(str(value))
        self.value_lbl.setAlignment(Qt.AlignCenter)
        self.value_lbl.setObjectName("MetricValue")
        value_font = QFont()
        value_font.setPointSize(24)
        value_font.setWeight(QFont.Weight.Black)
        self.value_lbl.setFont(value_font)

        accent = QFrame()
        accent.setObjectName("CardAccent")
        accent.setFixedHeight(3)

        layout.addWidget(self.title_lbl)
        layout.addSpacing(2)
        layout.addWidget(self.value_lbl)
        layout.addStretch(1)
        layout.addWidget(accent)

    def set_value(self, value):
        self.value_lbl.setText(str(value))


class GlassButton(QPushButton):
    """Modern glassmorphic button with icon and text for quick actions."""

    def __init__(self, text, icon_path=None):
        super().__init__()
        self.setText(text)
        if icon_path:
            self.setIcon(QIcon(icon_path))

        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(58)
        self.setMaximumHeight(64)
        self.setIconSize(QSize(28, 28))
        
        # Set font
        font = QFont()
        font.setPointSize(11)
        font.setWeight(QFont.Weight.DemiBold)
        self.setFont(font)


def _icon(name):
    """Helper to get icon path."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "assets", "icons", name)


class DashboardHome(QWidget):
    """Modern dashboard home page with KPIs, quick actions, and school information."""

    open_students = Signal()
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

       self.build_ui()

    # Load dashboard immediately
       self.load_dashboard()

    # Refresh automatically when data changes
       EventBus.subscribe("STUDENTS_UPDATED", self.load_dashboard)
       EventBus.subscribe("RESULTS_UPDATED", self.load_dashboard)
       EventBus.subscribe("EXAMS_UPDATED", self.load_dashboard)
       EventBus.subscribe("LEVEL_CHANGED", self.load_dashboard)

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
        header.setMinimumHeight(76)
        header.setMaximumHeight(76)

        layout = QVBoxLayout(header)
        layout.setContentsMargins(22, 10, 22, 10)
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
        title_font.setPointSize(13)
        title_font.setWeight(QFont.Weight.Bold)
        title.setFont(title_font)
        title.setProperty("variant", "accent")
        layout.addWidget(title)

        # KPI Grid container with background
        grid_container = QFrame()
        grid_layout_container = QVBoxLayout(grid_container)
        grid_layout_container.setContentsMargins(14, 14, 14, 14)
        grid_layout_container.setSpacing(0)

        # KPI Grid (3 columns x 3 rows)
        kpi_grid = QGridLayout()
        kpi_grid.setHorizontalSpacing(10)
        kpi_grid.setVerticalSpacing(10)
        kpi_grid.setContentsMargins(0, 0, 0, 0)

        # Create KPI Cards
        self.students_card = GlassCard("Students")
        self.subjects_card = GlassCard("Subjects")
        self.classes_card = GlassCard("Classes")
        self.exams_card = GlassCard("Exams")
        self.results_card = GlassCard("Results")
        self.male_card = GlassCard("Male Students")
        self.female_card = GlassCard("Female Students")
        self.open_exam_card = GlassCard("Open Exams")

        # Layout cards in grid
        cards = [
            (self.students_card, 0, 0),
            (self.subjects_card, 0, 1),
            (self.classes_card, 0, 2),
            (self.exams_card, 0, 3),
            (self.results_card, 1, 0),
            (self.male_card, 1, 1),
            (self.female_card, 1, 2),
            (self.open_exam_card, 1, 3),
        ]

        for card, row, col in cards:
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
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

        # Single quick action only.
        self.history_btn = GlassButton("History", _icon("dashboard.svg"))
        self.history_btn.setMinimumHeight(64)

        history_row = QHBoxLayout()
        history_row.setContentsMargins(0, 0, 0, 0)
        history_row.addStretch(1)
        history_row.addWidget(self.history_btn)
        history_row.addStretch(1)
        layout.addLayout(history_row)

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

            self.students_card.set_value(students)
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
