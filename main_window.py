import os

from PySide6.QtGui import QIcon, QPainter, QColor, QPen
from PySide6.QtCore import (
    QSize, Qt, QPropertyAnimation, QEasingCurve,
    QParallelAnimationGroup, QRectF, Property, Signal
)

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QStackedWidget,
    QSizePolicy
)

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class LevelToggleSwitch(QWidget):
    """Custom slide-switch for O-LEVEL / A-LEVEL."""

    toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self._thumb_x = 4.0
        self.setFixedSize(120, 36)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setToolTip(
            "Slide to switch between O-Level and A-Level"
        )
        self._anim = QPropertyAnimation(self, b"thumb_x")
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.InOutCubic)

    def get_thumb_x(self):
        return self._thumb_x

    def set_thumb_x(self, val):
        self._thumb_x = val
        self.update()

    thumb_x = Property(float, get_thumb_x, set_thumb_x)

    def isChecked(self):
        return self._checked

    def setChecked(self, checked, animate=True):
        self._checked = checked
        end = self.width() - self.height() + 4 if checked else 4.0
        if animate:
            self._anim.stop()
            self._anim.setStartValue(self._thumb_x)
            self._anim.setEndValue(end)
            self._anim.start()
        else:
            self._thumb_x = end
            self.update()

    def mousePressEvent(self, event):
        if not self.isEnabled():
            return
        new_state = not self._checked
        self.setChecked(new_state)
        self.toggled.emit(new_state)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            if not self.isEnabled():
                return
            new_state = not self._checked
            self.setChecked(new_state)
            self.toggled.emit(new_state)
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        r = h / 2

        if self._checked:
            track_color = QColor(109, 40, 217)
            thumb_color = QColor(196, 181, 253)
            left_text = ""
            right_text = "A-LEVEL"
            text_color = QColor(237, 233, 254)
        else:
            track_color = QColor(37, 99, 235)
            thumb_color = QColor(191, 219, 254)
            left_text = "O-LEVEL"
            right_text = ""
            text_color = QColor(219, 234, 254)

        p.setPen(Qt.NoPen)
        p.setBrush(track_color)
        p.drawRoundedRect(QRectF(0, 0, w, h), r, r)

        thumb_d = h - 8
        p.setBrush(thumb_color)
        p.drawEllipse(
            QRectF(self._thumb_x, 4, thumb_d, thumb_d)
        )

        p.setPen(QPen(text_color))
        font = p.font()
        font.setPixelSize(11)
        font.setBold(True)
        p.setFont(font)
        if left_text:
            text_rect = QRectF(
                thumb_d + 8, 0, w - thumb_d - 12, h
            )
            p.drawText(
                text_rect, Qt.AlignCenter, left_text
            )
        if right_text:
            text_rect = QRectF(
                4, 0, w - thumb_d - 12, h
            )
            p.drawText(
                text_rect, Qt.AlignCenter, right_text
            )

        p.end()

from event_bus import EventBus
from system_state import SystemState
from help_guide import HelpGuideDialog
from settings_page import get_setting
from theme import get_theme


def _icon(name):
    """Return a QIcon using an absolute path from assets/icons/."""
    return QIcon(os.path.join(_BASE_DIR, "assets", "icons", name))

from dashboard_home import DashboardHome
from students_page import StudentsPage
from teachers_module import TeachersModule
from academics_page import AcademicsPage
from exams import ExamsWindow
from results_center import ResultsCenter
from school_center import SchoolCenter
from settings_page import SettingsPage
from security_settings import SecuritySettingsPage


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("SRMS V5")

        root = QWidget()
        self.setCentralWidget(root)

        self.main_layout = QVBoxLayout(root)

        # =====================================
        # TOP BAR
        # =====================================

        top_bar = QHBoxLayout()

        self.title = QLabel("SRMS V5")
        self.title.setStyleSheet("""
            font-size:24px;
            font-weight:bold;
        """)

        # Level toggle - slide switch
        self.level_switch = LevelToggleSwitch()
        current_level = SystemState.get_level()
        self.level_switch.setChecked(
            current_level == "A_LEVEL", animate=False
        )
        self.level_switch.toggled.connect(
            self.toggle_level
        )

        # Help button — SVG icon
        self.help_btn = QPushButton()
        self.help_btn.setIcon(_icon("help.svg"))
        self.help_btn.setIconSize(QSize(22, 22))
        self.help_btn.setToolTip("Getting Started Guide")
        self.help_btn.setFixedSize(42, 42)
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setStyleSheet("""
            QPushButton{
                background:rgba(34,197,94,0.12);
                border:1px solid rgba(34,197,94,0.35);
                border-radius:12px;
            }
            QPushButton:hover{
                background:rgba(34,197,94,0.25);
            }
        """)
        self.help_btn.clicked.connect(self.show_help)

        # Theme toggle button — SVG icon
        self.theme_btn = QPushButton()
        self.theme_btn.setToolTip("Switch between Light and Dark theme")
        self.theme_btn.setIconSize(QSize(22, 22))
        self.theme_btn.setFixedSize(42, 42)
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.current_theme = get_setting('theme', 'Dark')
        self._update_theme_btn()
        self.theme_btn.clicked.connect(self.toggle_theme)

        self.refresh_btn = QPushButton()
        self.refresh_btn.setIcon(_icon("refresh.svg"))
        self.refresh_btn.setToolTip("Refresh")
        self.refresh_btn.setIconSize(QSize(20,20))
        self.refresh_btn.setFixedSize(42,42)
        self.refresh_btn.setStyleSheet("""
            QPushButton{
                background:rgba(255,255,255,0.08);
                border:none;
                border-radius:12px;
                color:#E2E8F0;
            }
            QPushButton:hover{
                background:rgba(255,255,255,0.16);
            }
        """)
        self.refresh_btn.clicked.connect(
            self.refresh_all
        )

        # Breadcrumb label
        self.breadcrumb = QLabel("")
        self.breadcrumb.setStyleSheet("""
            font-size: 13px;
            color: #64748b;
            padding: 0 8px;
        """)

        top_bar.addWidget(self.title)
        top_bar.addWidget(self.breadcrumb)
        top_bar.addStretch()
        top_bar.addWidget(self.help_btn)
        top_bar.addWidget(self.theme_btn)
        top_bar.addWidget(self.level_switch)
        top_bar.addWidget(self.refresh_btn)

        # =====================================
        # BODY
        # =====================================

        body = QHBoxLayout()
        body.setContentsMargins(0,0,0,0)
        body.setSpacing(16)

        # =====================================
        # SIDEBAR
        # =====================================

        
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setFixedWidth(240)
        self.sidebar_widget.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Expanding
        )

        self.sidebar_widget.setStyleSheet("""
        QWidget{
            background:#0F172A;
            border:1px solid rgba(148,163,184,0.15);
            border-radius:22px;
        }
        """)

        self.sidebar_anim_max = QPropertyAnimation(
            self.sidebar_widget,
            b"maximumWidth"
        )
        self.sidebar_anim_max.setDuration(240)
        self.sidebar_anim_max.setEasingCurve(
            QEasingCurve.InOutQuad
        )
        self.sidebar_anim_min = QPropertyAnimation(
            self.sidebar_widget,
            b"minimumWidth"
        )
        self.sidebar_anim_min.setDuration(240)
        self.sidebar_anim_min.setEasingCurve(
            QEasingCurve.InOutQuad
        )

        self.sidebar_anim_group = QParallelAnimationGroup()
        self.sidebar_anim_group.addAnimation(self.sidebar_anim_max)
        self.sidebar_anim_group.addAnimation(self.sidebar_anim_min)

        sidebar = QVBoxLayout(self.sidebar_widget)
        sidebar.setSpacing(10)
        sidebar.setContentsMargins(16,16,16,16)

        self.sidebar_collapsed = False

        self.sidebar_toggle_btn = QPushButton("≡")
        self.sidebar_toggle_btn.setFixedSize(36,36)
        self.sidebar_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.sidebar_toggle_btn.setStyleSheet("""
            QPushButton{
                color:#CBD5E1;
                background:rgba(255,255,255,0.06);
                border:none;
                border-radius:12px;
                font-size:16px;
                font-weight:700;
            }
            QPushButton:hover{
                background:rgba(255,255,255,0.12);
            }
        """)
        self.sidebar_toggle_btn.clicked.connect(self.toggle_sidebar)

        toggle_row = QHBoxLayout()
        toggle_row.addStretch()
        toggle_row.addWidget(self.sidebar_toggle_btn)
        sidebar.addLayout(toggle_row)

        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_students = QPushButton("Students")
        self.btn_teachers = QPushButton("Teachers")
        self.btn_academics = QPushButton("Academics")
        self.btn_exams = QPushButton("Exams")
        self.btn_results = QPushButton("Results")
        self.btn_school = QPushButton("School")
        self.btn_settings = QPushButton("Settings")

        self.btn_security = QPushButton("Security")

        self.btn_dashboard.setIcon(_icon("dashboard.svg"))
        self.btn_students.setIcon(_icon("students.svg"))
        self.btn_teachers.setIcon(_icon("teachers.svg"))
        self.btn_academics.setIcon(_icon("academics.svg"))
        self.btn_exams.setIcon(_icon("exams.svg"))
        self.btn_results.setIcon(_icon("results.svg"))
        self.btn_school.setIcon(_icon("school.svg"))
        self.btn_settings.setIcon(_icon("settings.svg"))
        self.btn_security.setIcon(_icon("security.svg"))


        self.nav_buttons = [
            self.btn_dashboard,
            self.btn_students,
            self.btn_teachers,
            self.btn_academics,
            self.btn_exams,
            self.btn_results,
            self.btn_school,
            self.btn_settings,
            self.btn_security
        ]

        self.sidebar_button_style = """
            QPushButton{
                text-align:left;
                padding:12px 18px 12px 20px;
                border-radius:16px;
                font-weight:700;
                color:#E2E8F0;
                font-size:14px;
                background:transparent;
                border:none;
            }
            QPushButton:hover{
                background:rgba(255,255,255,0.08);
            }
        """

        self.sidebar_button_style_collapsed = """
            QPushButton{
                padding:12px;
                border-radius:16px;
                font-weight:700;
                color:#E2E8F0;
                font-size:14px;
                background:transparent;
                border:none;
            }
            QPushButton:hover{
                background:rgba(255,255,255,0.08);
            }
        """

        self.sidebar_button_active_style = """
            QPushButton{
                background:qlineargradient(
                    x1:0,y1:0,x2:1,y2:0,
                    stop:0 #2563eb,
                    stop:1 #3b82f6
                );
                color:#ffffff;
                font-weight:700;
                border:none;
                border-radius:16px;
                padding:12px 18px 12px 20px;
                text-align:left;
            }
        """

        self.sidebar_button_active_style_collapsed = """
            QPushButton{
                background:qlineargradient(
                    x1:0,y1:0,x2:1,y2:0,
                    stop:0 #2563eb,
                    stop:1 #3b82f6
                );
                color:#ffffff;
                font-weight:700;
                border:none;
                border-radius:16px;
                padding:12px;
                text-align:center;
            }
        """

        self.active_btn = None

        self._nav_labels = {}
        for btn in self.nav_buttons:
            self._nav_labels[btn] = btn.text()
            btn.setCursor(Qt.PointingHandCursor)
            btn.setIconSize(QSize(28,28))
            btn.setMinimumHeight(54)
            btn.setStyleSheet(self.sidebar_button_style)
            btn.setToolTip(btn.text())
            sidebar.addWidget(btn)

        sidebar.addStretch()

        # =====================================
        # STACK
        # =====================================

        self.stack = QStackedWidget()

        self.dashboard = DashboardHome()
        self.students = StudentsPage()
        self.teachers = TeachersModule()
        self.academics = AcademicsPage()
        self.exams = ExamsWindow()
        self.results = ResultsCenter()
        self.school = SchoolCenter()
        self.settings = SettingsPage()
        self.security = SecuritySettingsPage()

        self.dashboard.open_students.connect(
            lambda: self.switch_page(
                self.students,
                self.btn_students
            )
        )

        self.dashboard.open_teachers.connect(
            lambda: self.switch_page(
                self.teachers,
                self.btn_teachers
            )
        )

        self.dashboard.open_exams.connect(
            lambda: self.switch_page(
                self.exams,
                self.btn_exams
            )
        )

        self.dashboard.open_results.connect(
            lambda: self.switch_page(
                self.results,
                self.btn_results
            )
        )

        self.dashboard.open_school.connect(
            lambda: self.switch_page(
                self.school,
                self.btn_school
            )
        )

        self.dashboard.open_reports.connect(
            lambda: (
                self.switch_page(
                    self.results,
                    self.btn_results
                ),
                self.results.open_report_book()
            )
        )


        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.students)
        self.stack.addWidget(self.teachers)
        self.stack.addWidget(self.academics)
        self.stack.addWidget(self.exams)
        self.stack.addWidget(self.results)
        self.stack.addWidget(self.school)
        self.stack.addWidget(self.settings)
        self.stack.addWidget(self.security)

        # =====================================
        # NAVIGATION
        # =====================================

        self.btn_dashboard.clicked.connect(
            lambda: self.switch_page(
                self.dashboard,
                self.btn_dashboard
            )
        )

        self.btn_students.clicked.connect(
            lambda: self.switch_page(
                self.students,
                self.btn_students
            )
        )

        self.btn_teachers.clicked.connect(
            lambda: self.switch_page(
                self.teachers,
                self.btn_teachers
            )
        )

        self.btn_academics.clicked.connect(
            lambda: self.switch_page(
                self.academics,
                self.btn_academics
            )
        )

        self.btn_exams.clicked.connect(
            lambda: self.switch_page(
                self.exams,
                self.btn_exams
            )
        )

        self.btn_results.clicked.connect(
            lambda: self.switch_page(
                self.results,
                self.btn_results
            )
        )

        self.btn_school.clicked.connect(
            lambda: self.switch_page(
                self.school,
                self.btn_school
            )
        )

        self.btn_settings.clicked.connect(
            lambda: self.switch_page(
                self.settings,
                self.btn_settings
            )
        )

        self.btn_security.clicked.connect(
            lambda: self.switch_page(
                self.security,
                self.btn_security
            )
        )

        body.addWidget(self.sidebar_widget)
        body.addWidget(self.stack)
        body.setStretch(0, 0)
        body.setStretch(1, 1)

        self.update_sidebar_state()

        self.main_layout.addLayout(top_bar)
        self.main_layout.addLayout(body)

        # =====================================
        # EVENTS
        # =====================================

        EventBus.subscribe(
            "OPEN_RESULTS_ENTRY",
            self.open_results_entry
        )

        EventBus.subscribe(
            "THEME_CHANGED",
            self._apply_theme
        )

        # =====================================
        # DEFAULT PAGE
        # =====================================

        self.switch_page(
            self.dashboard,
            self.btn_dashboard
        )

        self.refresh_all()

    # =====================================
    # NAVIGATION
    # =====================================

    def switch_page(
        self,
        page,
        button
    ):
        self.stack.setCurrentWidget(page)
        self.active_btn = button
        self.update_highlight(button)
        self._update_breadcrumb(button)

    def update_highlight(
        self,
        active_btn
    ):
        for btn in self.nav_buttons:
            if btn == active_btn:
                style = (
                    self.sidebar_button_active_style_collapsed
                    if self.sidebar_collapsed
                    else self.sidebar_button_active_style
                )
                btn.setStyleSheet(style)
            else:
                btn.setStyleSheet(
                    self.sidebar_button_style_collapsed
                    if self.sidebar_collapsed
                    else self.sidebar_button_style
                )

    # =====================================
    # LEVEL SWITCH
    # =====================================

    def change_level(
        self,
        value
    ):
        SystemState.set_level(value)

    # =====================================
    # SIDEBAR COLLAPSE
    # =====================================

    def toggle_sidebar(self):
        self.sidebar_collapsed = not self.sidebar_collapsed
        self.update_sidebar_state()

    def update_sidebar_state(self):
        if self.sidebar_collapsed:
            target_width = 88
        else:
            target_width = 240

        current_w = self.sidebar_widget.width()

        # Update text/style BEFORE animation so content matches target
        for btn in self.nav_buttons:
            btn.setIconSize(QSize(28, 28))
            if self.sidebar_collapsed:
                btn.setMinimumHeight(54)
                btn.setStyleSheet(self.sidebar_button_style_collapsed)
                btn.setText("")
            else:
                btn.setMinimumHeight(54)
                btn.setStyleSheet(self.sidebar_button_style)
                btn.setText(self._nav_labels.get(btn, btn.toolTip()))

        self.update_highlight(self.active_btn)

        # Animate both min and max width together via group
        self.sidebar_anim_group.stop()
        self.sidebar_anim_max.setStartValue(current_w)
        self.sidebar_anim_max.setEndValue(target_width)
        self.sidebar_anim_min.setStartValue(current_w)
        self.sidebar_anim_min.setEndValue(target_width)
        self.sidebar_anim_group.start()

    def toggle_level(self, is_a_level):
        if is_a_level:
            SystemState.set_level("A_LEVEL")
        else:
            SystemState.set_level("O_LEVEL")
        self.refresh_all()

    def show_help(self):
        """Show the Getting Started guide dialog."""
        dialog = HelpGuideDialog(self)
        dialog.exec()

    def toggle_theme(self):
        """Toggle between Light and Dark themes and persist."""
        if self.current_theme == "Dark":
            self.current_theme = "Light"
        else:
            self.current_theme = "Dark"

        app = QApplication.instance()
        if app:
            app.setStyleSheet(get_theme(self.current_theme))
        self._update_theme_btn()
        self._persist_theme(self.current_theme)

    def _persist_theme(self, theme_name):
        """Save theme choice to system_settings."""
        from db_utils import execute
        try:
            execute(
                "REPLACE INTO system_settings (setting_key, setting_value) VALUES (?, ?)",
                ('theme', theme_name))
        except Exception:
            pass

    def _update_theme_btn(self):
        """Update the theme button icon based on current theme."""
        if self.current_theme == "Dark":
            self.theme_btn.setIcon(_icon("sun.svg"))
            self.theme_btn.setStyleSheet("""
                QPushButton{
                    background:rgba(251,191,36,0.12);
                    border:1px solid rgba(251,191,36,0.35);
                    border-radius:12px;
                }
                QPushButton:hover{
                    background:rgba(251,191,36,0.25);
                }
            """)
        else:
            self.theme_btn.setIcon(_icon("moon.svg"))
            self.theme_btn.setStyleSheet("""
                QPushButton{
                    background:rgba(99,102,241,0.12);
                    border:1px solid rgba(99,102,241,0.35);
                    border-radius:12px;
                }
                QPushButton:hover{
                    background:rgba(99,102,241,0.25);
                }
            """)

    def _update_breadcrumb(self, button):
        """Update breadcrumb based on current page."""
        page_name = self._nav_labels.get(button, "") if button else ""
        if page_name and page_name != "Dashboard":
            self.breadcrumb.setText(f" > {page_name}")
        else:
            self.breadcrumb.setText("")


    # =====================================
    # RESULTS DASHBOARD OPEN
    # =====================================

    def open_results_entry(
        self,
        exam_id,
        class_name,
        subject_name
    ):

        self.switch_page(
            self.results,
            self.btn_results
        )

        try:
            self.results.open_from_dashboard(
                exam_id,
                class_name,
                subject_name
            )
        except Exception as error:
            print(f"[ERROR] MainWindow failed to open results entry: {error}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Navigation Error",
                f"Could not open results entry: {error}",
            )

    # =====================================
    # REFRESH
    # =====================================

    def refresh_all(self):

        for page in [
            self.dashboard,
            self.students,
            self.teachers,
            self.academics,
            self.exams,
            self.results,
            self.school,
            self.settings,
            self.security
        ]:

            self._refresh_page(page)

    @staticmethod
    def _refresh_page(page):

        for method_name in (
            "refresh_all",
            "load_data",
            "load",
            "load_years"
        ):

            method = getattr(
                page,
                method_name,
                None
            )

            if callable(method):

                try:
                    method()
                except Exception as error:
                    print(f"[ERROR] Failed to refresh {type(page).__name__}.{method_name}: {error}")

                break

    def _apply_theme(self, theme_name):
        """Apply theme from settings change event."""
        self.current_theme = theme_name
        app = QApplication.instance()
        if app:
            app.setStyleSheet(get_theme(theme_name))
        self._update_theme_btn()
        self._persist_theme(theme_name)
