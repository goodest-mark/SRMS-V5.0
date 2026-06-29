from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (
    QWidget,
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGridLayout,
    QSizePolicy,
    QLayout,
    QScrollArea
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
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(145)
        self.setMaximumHeight(165)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(0)

        # Value Label - Large and prominent
        self.value_lbl = QLabel(str(value))
        self.value_lbl.setAlignment(Qt.AlignCenter)
        value_font = QFont()
        value_font.setPointSize(56)
        value_font.setWeight(QFont.Weight.Black)
        self.value_lbl.setFont(value_font)
        self.value_lbl.setStyleSheet("""
            color: #f1f5f9;
            background: transparent;
            border: none;
        """)

        # Title Label - Subtle
        self.title_lbl = QLabel(title)
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setWordWrap(True)
        title_font = QFont()
        title_font.setPointSize(11)
        self.title_lbl.setFont(title_font)
        self.title_lbl.setStyleSheet("""
            color: #94a3b8;
            background: transparent;
            border: none;
        """)

        layout.addStretch(1)
        layout.addWidget(self.value_lbl, alignment=Qt.AlignCenter)
        layout.addSpacing(4)
        layout.addWidget(self.title_lbl, alignment=Qt.AlignCenter)
        layout.addStretch(1)

        # Enhanced glass card styling with better contrast
        self.setStyleSheet("""
            QFrame#GlassCard {
                background: rgba(51, 65, 85, 0.4);
                border: 1px solid rgba(100, 116, 139, 0.35);
                border-radius: 16px;
            }
            QFrame#GlassCard:hover {
                background: rgba(51, 65, 85, 0.55);
                border: 1px solid rgba(100, 116, 139, 0.55);
            }
        """)


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
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(95)
        self.setMaximumHeight(115)
        self.setIconSize(QSize(38, 38))
        
        # Set font
        font = QFont()
        font.setPointSize(15)
        font.setWeight(QFont.Weight.DemiBold)
        self.setFont(font)
        
        self.setStyleSheet("""
            QPushButton {
                background: rgba(51, 65, 85, 0.4);
                border: 1px solid rgba(100, 116, 139, 0.35);
                border-radius: 16px;
                color: #f1f5f9;
                padding: 10px 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(51, 65, 85, 0.65);
                border: 1px solid rgba(100, 116, 139, 0.55);
            }
            QPushButton:pressed {
                background: rgba(51, 65, 85, 0.55);
            }
        """)


def _icon(name):
    """Helper to get icon path."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "assets", "icons", name)


class DashboardHome(QWidget):
    """Modern dashboard home page with KPIs, quick actions, and school information."""

    open_students = Signal()
    open_teachers = Signal()
    open_exams = Signal()
    open_results = Signal()
    open_school = Signal()
    open_reports = Signal()

  

    def __init__(self):
       super().__init__()

       self.build_ui()

    # Load dashboard immediately
       self.load_dashboard()

    # Refresh automatically when data changes
       EventBus.subscribe("STUDENTS_UPDATED", self.load_dashboard)
       EventBus.subscribe("TEACHERS_UPDATED", self.load_dashboard)
       EventBus.subscribe("RESULTS_UPDATED", self.load_dashboard)
       EventBus.subscribe("EXAMS_UPDATED", self.load_dashboard)
       EventBus.subscribe("LEVEL_CHANGED", self.load_dashboard)    

    def build_ui(self):
        """Build the complete dashboard UI with improved layout and styling."""
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Main layout with reduced margins for better space usage
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        # ====== HEADER SECTION ======
        header = self._build_header()
        root.addWidget(header)

        # ====== MAIN CONTENT AREA ======
        content_layout = QHBoxLayout()
        content_layout.setSpacing(14)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Left: KPI Cards
        kpi_section = self._build_kpi_section()
        content_layout.addWidget(kpi_section, 3)

        # Right: Quick Actions & School Info
        right_panel = self._build_right_panel()
        content_layout.addWidget(right_panel, 2)

        root.addLayout(content_layout, 0)
        root.addStretch()

    def _build_header(self):
        """Build the compact, modern header section."""
        header = QFrame()
        header.setObjectName("HeaderFrame")
        header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        header.setMinimumHeight(85)
        header.setMaximumHeight(85)

        header.setStyleSheet("""
            QFrame#HeaderFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(15, 23, 42, 0.95),
                    stop:1 rgba(30, 41, 59, 0.9)
                );
                border: 1px solid rgba(100, 116, 139, 0.3);
                border-radius: 16px;
            }
        """)

        layout = QVBoxLayout(header)
        layout.setContentsMargins(24, 12, 24, 12)
        layout.setSpacing(3)

        # School Name
        self.school_lbl = QLabel("Loading School...")
        self.school_lbl.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(20)
        font.setWeight(QFont.Weight.Bold)
        self.school_lbl.setFont(font)
        self.school_lbl.setStyleSheet("color: #f1f5f9; background: transparent;")

        # Subtitle
        subtitle = QLabel("School Results Management System")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(9)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet("color: #cbd5e1; background: transparent;")

        # Active Exam
        self.exam_lbl = QLabel("Loading Exam...")
        self.exam_lbl.setAlignment(Qt.AlignCenter)
        exam_font = QFont()
        exam_font.setPointSize(9)
        exam_font.setWeight(QFont.Weight.DemiBold)
        self.exam_lbl.setFont(exam_font)
        self.exam_lbl.setStyleSheet("color: #10b981; background: transparent;")

        layout.addWidget(self.school_lbl, alignment=Qt.AlignCenter)
        layout.addWidget(subtitle, alignment=Qt.AlignCenter)
        layout.addWidget(self.exam_lbl, alignment=Qt.AlignCenter)

        return header

    def _build_kpi_section(self):
        """Build the left panel with KPI cards."""
        container = QFrame()
        container.setObjectName("KPIContainer")
        container.setStyleSheet("""
            QFrame#KPIContainer {
                background: transparent;
                border: none;
            }
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Section Title - Bold and prominent
        title = QLabel("Key Performance Indicators")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setWeight(QFont.Weight.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #f1f5f9; background: transparent;")
        layout.addWidget(title)

        # KPI Grid container with background
        grid_container = QFrame()
        grid_container.setStyleSheet("""
            QFrame {
                background: rgba(30, 41, 59, 0.4);
                border: 1px solid rgba(100, 116, 139, 0.25);
                border-radius: 16px;
            }
        """)
        grid_layout_container = QVBoxLayout(grid_container)
        grid_layout_container.setContentsMargins(14, 14, 14, 14)
        grid_layout_container.setSpacing(0)

        # KPI Grid (3 columns x 3 rows)
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(12)
        kpi_grid.setContentsMargins(0, 0, 0, 0)

        # Create KPI Cards
        self.students_card = GlassCard("Students")
        self.teachers_card = GlassCard("Teachers")
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
            (self.teachers_card, 0, 1),
            (self.subjects_card, 0, 2),
            (self.classes_card, 1, 0),
            (self.exams_card, 1, 1),
            (self.results_card, 1, 2),
            (self.male_card, 2, 0),
            (self.female_card, 2, 1),
            (self.open_exam_card, 2, 2),
        ]

        for card, row, col in cards:
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            kpi_grid.addWidget(card, row, col)

        # Set equal column and row stretching
        for i in range(3):
            kpi_grid.setColumnStretch(i, 1)
            kpi_grid.setRowStretch(i, 1)

        grid_layout_container.addLayout(kpi_grid)
        layout.addWidget(grid_container, 1)

        return container

    def _build_right_panel(self):
        """Build the right panel with quick actions and school info."""
        container = QFrame()
        container.setStyleSheet("background: transparent; border: none;")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # ====== QUICK ACTIONS ======
        quick_panel = self._build_quick_actions()
        layout.addWidget(quick_panel, 0)

        # ====== SCHOOL INFORMATION ======
        school_panel = self._build_school_info()
        layout.addWidget(school_panel, 1)

        return container

    def _build_quick_actions(self):
        """Build the quick actions panel with button grid."""
        panel = QFrame()
        panel.setObjectName("QuickActionsPanel")
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        panel.setStyleSheet("""
            QFrame#QuickActionsPanel {
                background: rgba(30, 41, 59, 0.4);
                border: 1px solid rgba(100, 116, 139, 0.25);
                border-radius: 16px;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(9)

        # Section Title - Bold and prominent
        title = QLabel("Quick Actions")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setWeight(QFont.Weight.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #f1f5f9; background: transparent;")
        layout.addWidget(title)

        # Button Grid (3 columns x 2 rows)
        button_grid = QGridLayout()
        button_grid.setSpacing(9)
        button_grid.setContentsMargins(0, 0, 0, 0)

        # Create buttons
        self.student_btn = GlassButton("New Student", _icon("students.svg"))
        self.teachers_btn = GlassButton("Teachers", _icon("teachers.svg"))
        self.exams_btn = GlassButton("Exams", _icon("exams.svg"))
        self.results_btn = GlassButton("Results", _icon("results.svg"))
        self.school_btn = GlassButton("School", _icon("school.svg"))
        self.reports_btn = GlassButton("Reports", _icon("dashboard.svg"))

        # Layout buttons in 3-column grid
        buttons = [
            (self.student_btn, 0, 0),
            (self.teachers_btn, 0, 1),
            (self.exams_btn, 0, 2),
            (self.results_btn, 1, 0),
            (self.school_btn, 1, 1),
            (self.reports_btn, 1, 2),
        ]

        for btn, row, col in buttons:
            button_grid.addWidget(btn, row, col)

        # Set equal column stretching
        for i in range(3):
            button_grid.setColumnStretch(i, 1)

        layout.addLayout(button_grid)

        # Connect button signals
        self.student_btn.clicked.connect(self.open_students.emit)
        self.teachers_btn.clicked.connect(self.open_teachers.emit)
        self.exams_btn.clicked.connect(self.open_exams.emit)
        self.results_btn.clicked.connect(self.open_results.emit)
        self.school_btn.clicked.connect(self.open_school.emit)
        self.reports_btn.clicked.connect(self.open_reports.emit)

        return panel

    def _build_school_info(self):
        """Build the school information panel."""
        panel = QFrame()
        panel.setObjectName("SchoolInfoPanel")
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        panel.setMinimumHeight(140)
        panel.setStyleSheet("""
            QFrame#SchoolInfoPanel {
                background: rgba(30, 41, 59, 0.4);
                border: 1px solid rgba(100, 116, 139, 0.25);
                border-radius: 16px;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # Section Title - Bold and prominent
        title = QLabel("School Information")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setWeight(QFont.Weight.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #f1f5f9; background: transparent;")
        layout.addWidget(title)

        # Info Label - Centered when empty
        self.school_info_lbl = QLabel("Loading...")
        self.school_info_lbl.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.school_info_lbl.setWordWrap(True)
        info_font = QFont()
        info_font.setPointSize(10)
        self.school_info_lbl.setFont(info_font)
        self.school_info_lbl.setStyleSheet("""
            color: #cbd5e1;
            background: transparent;
            border: none;
            line-height: 1.5;
        """)
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
            self.teachers_card.set_value(teachers)
            self.subjects_card.set_value(subjects)
            self.classes_card.set_value(classes)
            self.exams_card.set_value(exams)
            self.results_card.set_value(results)
            self.male_card.set_value(males)
            self.female_card.set_value(females)
            self.open_exam_card.set_value(open_exams)
            # self.open_exam_card.set_value(open_exams) # This card was removed from view


        except Exception as error:
            print(f"[ERROR] Dashboard failed to load: {error}")
            self.school_lbl.setText("Dashboard Error")
            self.exam_lbl.setText(f"Could not load data: {error}")
