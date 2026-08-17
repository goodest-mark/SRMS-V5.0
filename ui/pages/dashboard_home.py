from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QSizePolicy, QGraphicsDropShadowEffect,
)
from PySide6.QtGui import QIcon, QColor, QPixmap, QPainter

from app_paths import icon_path
from event_bus import EventBus
from system_state import SystemState
from db_utils import get_cursor
from theme import get_tokens

PLACEHOLDER = "\u2014"


def _icon(name):
    path = icon_path(name)
    return str(path) if path.exists() else ""


def _themed_icon_pixmap(icon_file, size):
    pixmap = QIcon(icon_file).pixmap(size, size)
    if pixmap.isNull():
        return pixmap
    tokens = get_tokens()
    if not tokens.get("is_light"):
        return pixmap
    tinted = QPixmap(pixmap.size())
    tinted.setDevicePixelRatio(pixmap.devicePixelRatio())
    tinted.fill(Qt.transparent)
    painter = QPainter(tinted)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(tinted.rect(), QColor(tokens["primary"]))
    painter.end()
    return tinted


def _soft_shadow(blur=24, y=6, alpha=70):
    effect = QGraphicsDropShadowEffect()
    effect.setBlurRadius(blur)
    effect.setOffset(0, y)
    effect.setColor(QColor(0, 0, 0, alpha))
    return effect


def _label(text, object_name, word_wrap=False):
    lbl = QLabel(text)
    lbl.setObjectName(object_name)
    lbl.setWordWrap(word_wrap)
    return lbl


# ============================================================
# STAT CARD – no subtitle
# ============================================================
class StatCard(QFrame):
    def __init__(self, title, icon_file, tone="primary"):
        super().__init__()
        self.setObjectName("PremiumStatCard")
        self.setProperty("tone", tone)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # The dashboard grid has two rows above Quick Actions.  A fixed card
        # height prevents the grid from consuming the column's spare height
        # and visually running into the panel below it.
        self.setFixedHeight(120)
        self.setGraphicsEffect(_soft_shadow())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(8)

        # Keep the title and icon together so the metric has a clear reading
        # order, with the value claiming the remaining vertical space.
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(10)

        icon_badge = QFrame()
        icon_badge.setObjectName("PremiumStatIcon")
        icon_badge.setFixedSize(40, 40)
        icon_badge.setAttribute(Qt.WA_StyledBackground, True)
        icon_row = QHBoxLayout(icon_badge)
        icon_row.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent;")
        if icon_file:
            icon_lbl.setPixmap(_themed_icon_pixmap(icon_file, 18))
        icon_row.addWidget(icon_lbl)
        self._icon_file = icon_file
        self._icon_label = icon_lbl

        self.title_lbl = _label(title, "MetricTitle")
        top_row.addWidget(icon_badge)
        top_row.addWidget(self.title_lbl)
        top_row.addStretch()
        layout.addLayout(top_row)

        self.value_lbl = _label(PLACEHOLDER, "MetricValue")
        self.value_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_lbl, 1)

        # Accent underline
        underline = QFrame()
        underline.setObjectName("CardAccent")
        underline.setAttribute(Qt.WA_StyledBackground, True)
        underline.setFixedHeight(3)
        layout.addWidget(underline)

    def set_value(self, value):
        self.value_lbl.setText(str(value))

    def refresh_theme_icon(self):
        if self._icon_file:
            self._icon_label.setPixmap(_themed_icon_pixmap(self._icon_file, 18))


# ============================================================
# INFO ROW – keeps value on same line
# ============================================================
class InfoRow(QFrame):
    def __init__(self, icon_file, label):
        super().__init__()
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent; border: none;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)

        icon_badge = QFrame()
        icon_badge.setObjectName("IconBadge")
        icon_badge.setFixedSize(30, 30)
        icon_badge.setAttribute(Qt.WA_StyledBackground, True)
        icon_badge.setStyleSheet(icon_badge.styleSheet() + "border-radius: 15px;")
        icon_row = QHBoxLayout(icon_badge)
        icon_row.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent;")
        if icon_file:
            icon_lbl.setPixmap(_themed_icon_pixmap(icon_file, 14))
        icon_row.addWidget(icon_lbl)
        self._icon_file = icon_file
        self._icon_label = icon_lbl
        layout.addWidget(icon_badge)

        label_lbl = _label(label, "LegendLabel", word_wrap=True)
        label_lbl.setFixedWidth(190)
        layout.addWidget(label_lbl)

        layout.addStretch()

        self.value_lbl = _label(PLACEHOLDER, "LegendValue")
        self.value_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.value_lbl.setWordWrap(True)
        self.value_lbl.setMinimumWidth(0)
        self.value_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.value_lbl, 1)

    def set_value(self, text, tone=None):
        text = str(text)
        self.value_lbl.setText(text)
        self.value_lbl.setToolTip("")
        if tone:
            tokens = get_tokens()
            self.value_lbl.setStyleSheet(f"color: {tokens[tone]}; font-size:13px; font-weight:850; background: transparent;")
        else:
            self.value_lbl.setStyleSheet("")

    def refresh_theme_icon(self):
        if self._icon_file:
            self._icon_label.setPixmap(_themed_icon_pixmap(self._icon_file, 14))


# ============================================================
# ACTION TILE
# ============================================================
class ActionTile(QPushButton):
    def __init__(self, icon_file, label):
        super().__init__()
        self.setObjectName("navButton")
        self.setProperty("variant", "default")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(64)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 14, 8)
        layout.setSpacing(12)

        icon_badge = QFrame()
        icon_badge.setObjectName("IconBadge")
        icon_badge.setFixedSize(38, 38)
        icon_badge.setAttribute(Qt.WA_StyledBackground, True)
        icon_row = QHBoxLayout(icon_badge)
        icon_row.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent;")
        if icon_file:
            icon_lbl.setPixmap(_themed_icon_pixmap(icon_file, 18))
        icon_row.addWidget(icon_lbl)
        self._icon_file = icon_file
        self._icon_label = icon_lbl
        layout.addWidget(icon_badge)

        layout.addWidget(_label(label, "ChecklistLabel"))
        layout.addStretch()

        chevron = QLabel("\u203a")
        chevron.setObjectName("LegendLabel")
        layout.addWidget(chevron)

    def refresh_theme_icon(self):
        if self._icon_file:
            self._icon_label.setPixmap(_themed_icon_pixmap(self._icon_file, 18))


# ============================================================
# MAIN DASHBOARD
# ============================================================
class DashboardHome(QWidget):
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
        self.load_dashboard()

        EventBus.subscribe("STUDENTS_UPDATED", self.load_dashboard)
        EventBus.subscribe("SUBJECTS_UPDATED", self.load_dashboard)
        EventBus.subscribe("RESULTS_UPDATED", self.load_dashboard)
        EventBus.subscribe("EXAMS_UPDATED", self.load_dashboard)
        EventBus.subscribe("LEVEL_CHANGED", self.load_dashboard)
        EventBus.subscribe("SCHOOL_PROFILE_UPDATED", self.load_dashboard)
        EventBus.subscribe("THEME_CHANGED", self.refresh_theme_assets)

    def build_ui(self):
        self.setObjectName("SRMSDashboardRoot")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(16)

        # Header
        header = QHBoxLayout()
        header.addWidget(_label("Dashboard", "PageTitle"))
        header.addStretch()
        self.greeting_label = QLabel("Hi, Admin!")
        self.greeting_label.setObjectName("PageSubtitle")
        self.greeting_label.setStyleSheet("font-size: 16px; font-weight: 600;")
        header.addWidget(self.greeting_label)
        root.addLayout(header)

        root.addWidget(_label("Welcome to School Results Management System", "PageSubtitle"))

        # Main content
        content_row = QHBoxLayout()
        content_row.setSpacing(18)
        root.addLayout(content_row, 1)

        # Left column
        left_col = QVBoxLayout()
        left_col.setSpacing(14)
        content_row.addLayout(left_col, 3)

        stat_grid = QGridLayout()
        stat_grid.setHorizontalSpacing(24)
        stat_grid.setVerticalSpacing(24)

        self.students_card = StatCard("Students", _icon("students.svg"), tone="primary")
        self.subjects_card = StatCard("Subjects", _icon("academics.svg"), tone="secondary")
        self.classes_card = StatCard("Classes", _icon("school.svg"), tone="success")
        self.exams_card = StatCard("Exams", _icon("exams.svg"), tone="warning")

        cards = [self.students_card, self.subjects_card, self.classes_card, self.exams_card]
        for i, card in enumerate(cards):
            row = i // 2
            col = i % 2
            stat_grid.addWidget(card, row, col)
            stat_grid.setColumnStretch(col, 1)

        left_col.addLayout(stat_grid)
        # Keep the lower stat cards visually distinct from the action panel.
        left_col.addSpacing(12)
        left_col.addWidget(self._build_quick_actions())

        # Right column
        right_col = QVBoxLayout()
        right_col.setSpacing(14)
        content_row.addLayout(right_col, 2)

        right_col.addWidget(self._build_school_info())
        right_col.addStretch()

        # Footer
        root.addWidget(_label(
            "\u00a9 2026 School Results Management System. All rights reserved.",
            "FooterNote",
        ), 0, Qt.AlignHCenter)

    def _build_quick_actions(self):
        panel = QFrame()
        panel.setObjectName("QuickActionsPanel")
        panel.setAttribute(Qt.WA_StyledBackground, True)
        panel.setGraphicsEffect(_soft_shadow())

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 6, 20, 18)
        layout.setSpacing(10)

        layout.addWidget(_label("Quick Actions", "SectionTitle"))

        self.add_student_btn = ActionTile(_icon("students.svg"), "Add Student")
        self.add_exam_btn = ActionTile(_icon("exams.svg"), "Add Exam")
        self.subjects_btn = ActionTile(_icon("academics.svg"), "Subjects")
        self.history_btn = ActionTile(_icon("dashboard.svg"), "History")

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        grid.addWidget(self.add_student_btn, 0, 0)
        grid.addWidget(self.add_exam_btn, 0, 1)
        grid.addWidget(self.subjects_btn, 1, 0)
        grid.addWidget(self.history_btn, 1, 1)
        layout.addLayout(grid)

        self.add_student_btn.clicked.connect(self.open_students.emit)
        self.add_exam_btn.clicked.connect(self.open_exams.emit)
        self.subjects_btn.clicked.connect(self.open_academics.emit)
        self.history_btn.clicked.connect(self.open_history.emit)

        return panel

    def _build_school_info(self):
        panel = QFrame()
        panel.setObjectName("SchoolInfoPanel")
        panel.setAttribute(Qt.WA_StyledBackground, True)
        panel.setGraphicsEffect(_soft_shadow())

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 6, 20, 12)
        layout.setSpacing(2)

        layout.addWidget(_label("School Information", "SectionTitle"))
        layout.addSpacing(6)

        # Rows – no "System"
        self.row_school_name = InfoRow(_icon("school.svg"), "School Name")
        self.row_head_teacher = InfoRow(_icon("user.svg"), "Headmaster / Headmistress")
        self.row_academic_master = InfoRow(_icon("academics.svg"), "Academic Master / Mistress")
        self.row_active_exam = InfoRow(_icon("exams.svg"), "Active Exam")
        self.row_academic_year = InfoRow(_icon("calendar.svg"), "Academic Year")
        self.row_school_level = InfoRow(_icon("students.svg"), "School Level")
        self.row_location = InfoRow(_icon("location.svg"), "Location")

        for row in [self.row_school_name, self.row_head_teacher, self.row_academic_master,
                    self.row_active_exam, self.row_academic_year, self.row_school_level, self.row_location]:
            layout.addWidget(row)

        return panel

    def refresh_theme_assets(self, *_):
        """Regenerate raster icon pixmaps after the application theme changes."""
        for card in (self.students_card, self.subjects_card, self.classes_card, self.exams_card):
            card.refresh_theme_icon()
        for row in (
            self.row_school_name, self.row_head_teacher, self.row_academic_master,
            self.row_active_exam, self.row_academic_year, self.row_school_level,
            self.row_location,
        ):
            row.refresh_theme_icon()
        for action in (self.add_student_btn, self.add_exam_btn, self.subjects_btn, self.history_btn):
            action.refresh_theme_icon()
        self.load_dashboard()

    # ------------------------------------------------------------
    # DATA LOADER
    # ------------------------------------------------------------
    def load_dashboard(self):
        if not self.isVisible():
            self._needs_refresh = True
            return

        try:
            with get_cursor() as cur:
                # Counts
                cur.execute("SELECT COUNT(*) FROM students")
                students = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM subjects")
                subjects = cur.fetchone()[0]

                cur.execute("SELECT COUNT(DISTINCT class) FROM students")
                classes = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM exams WHERE status != 'COMPLETED'")
                open_exams = cur.fetchone()[0]

                # School profile – includes head_teacher, academic_master
                cur.execute("""
                    SELECT school_name, head_teacher, academic_master, school_phone, school_email
                    FROM school_profile LIMIT 1
                """)
                row = cur.fetchone()
                if row:
                    self.row_school_name.set_value(row[0] or "N/A")
                    self.row_head_teacher.set_value(row[1] or "N/A")
                    self.row_academic_master.set_value(row[2] or "N/A")
                else:
                    self.row_school_name.set_value("N/A")
                    self.row_head_teacher.set_value("N/A")
                    self.row_academic_master.set_value("N/A")

                # Active exam
                current_level = SystemState.get_level()
                cur.execute("""
                    SELECT exam_name FROM exams
                    WHERE status='OPEN' AND level=?
                    ORDER BY id DESC LIMIT 1
                """, (current_level,))
                exam = cur.fetchone()
                if exam:
                    self.row_active_exam.set_value(exam[0], tone="success")
                else:
                    self.row_active_exam.set_value("No Active Exam")

                # School level
                self.row_school_level.set_value(current_level or "N/A")

                # Academic Year – placeholder
                self.row_academic_year.set_value("2026")

                # Location – placeholder
                self.row_location.set_value("N/A")

                # Update stat cards
                self.students_card.set_value(students)
                self.subjects_card.set_value(subjects)
                self.classes_card.set_value(classes)
                self.exams_card.set_value(open_exams)

        except Exception as error:
            print(f"[ERROR] Dashboard failed to load: {error}")

    def showEvent(self, event):
        super().showEvent(event)
        if self._needs_refresh:
            self._needs_refresh = False
            self.load_dashboard()
