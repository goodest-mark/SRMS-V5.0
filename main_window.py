import os

from PySide6.QtGui import QIcon, QPainter, QColor, QPen
from PySide6.QtCore import (
    QSize, Qt, QPropertyAnimation, QEasingCurve,
    QTimer,
    QParallelAnimationGroup, QRectF, Property, Signal
)

from progress_dialog import ProgressDialog

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

from progress_dialog import ProgressDialog

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class LevelToggleSwitch(QWidget):
    """Custom slide-switch for O-LEVEL / A-LEVEL."""

    toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self._thumb_x = 4.0
        self.setFixedSize(98, 34)
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
from theme import normalize_theme_name, apply_theme as apply_app_theme


def _icon(name):
    """Return a QIcon using an absolute path from assets/icons/."""
    return QIcon(os.path.join(_BASE_DIR, "assets", "icons", name))

from dashboard_home import DashboardHome
from students_page import StudentsPage
from academics_page import AcademicsPage
from exams import ExamsWindow
from results_center import ResultsCenter
from historical_results_page import HistoricalResultsPage
from school_center import SchoolCenter
from settings_page import SettingsPage


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("SRMS V5")

        root = QWidget()
        self.setCentralWidget(root)

        self.main_layout = QVBoxLayout(root)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # =====================================
        # TOP BAR
        # =====================================

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(16, 10, 16, 10)
        top_bar.setSpacing(10)

        # Level toggle - slide switch
        self.level_switch = LevelToggleSwitch()
        current_level = SystemState.get_level()
        self.level_switch.setChecked(
            current_level == "A_LEVEL", animate=False
        )
        self.level_switch.toggled.connect(
            self.toggle_level
        )


        self.current_theme = "Blue"

        # Breadcrumb label
        self.breadcrumb = QLabel("")
        self.breadcrumb.setStyleSheet("""
            font-size: 13px;
            font-weight: 800;
            color: #93C5FD;
            padding: 0 8px;
        """)

        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_students = QPushButton("Students")
        self.btn_academics = QPushButton("Academics")
        self.btn_exams = QPushButton("Exams")
        self.btn_results = QPushButton("Results")
        self.btn_history = QPushButton("History")
        self.btn_school = QPushButton("School")
        self.btn_settings = QPushButton("Settings")

        self.btn_dashboard.setIcon(_icon("dashboard.svg"))
        self.btn_students.setIcon(_icon("students.svg"))
        self.btn_academics.setIcon(_icon("academics.svg"))
        self.btn_exams.setIcon(_icon("exams.svg"))
        self.btn_results.setIcon(_icon("results.svg"))
        self.btn_history.setIcon(_icon("dashboard.svg"))
        self.btn_school.setIcon(_icon("school.svg"))
        self.btn_settings.setIcon(_icon("settings.svg"))

        self.nav_buttons = [
            self.btn_dashboard,
            self.btn_students,
            self.btn_academics,
            self.btn_exams,
            self.btn_results,
            self.btn_history,
            self.btn_school,
            self.btn_settings,
        ]

        self.nav_button_style = """
            QPushButton{
                text-align:center;
                padding:9px 14px;
                border-radius:15px;
                font-weight:900;
                color:#D7E4F5;
                font-size:13px;
                background:transparent;
                border:1px solid transparent;
                min-width: 112px;
            }
            QPushButton:hover{
                color:#FFFFFF;
                background:rgba(59,130,246,0.14);
                border:1px solid rgba(96,165,250,0.28);
            }
        """

        self.nav_button_active_style = """
            QPushButton{
                background:qlineargradient(
                    x1:0,y1:0,x2:1,y2:0,
                    stop:0 #2563EB,
                    stop:1 #60A5FA
                );
                color:#FFFFFF;
                font-weight:900;
                border:1px solid rgba(191,219,254,0.35);
                border-radius:16px;
                padding:10px 16px;
                min-width: 112px;
            }
        """

        self.active_btn = None
        self._nav_labels = {}

        self.top_nav = QHBoxLayout()
        self.top_nav.setSpacing(3)
        self.top_nav.setContentsMargins(8, 6, 8, 6)

        for btn in self.nav_buttons:
            self._nav_labels[btn] = btn.text()
            btn.setCursor(Qt.PointingHandCursor)
            btn.setIconSize(QSize(20,20))
            btn.setMinimumHeight(40)
            btn.setStyleSheet(self.nav_button_style)
            btn.setToolTip(btn.text())
            self.top_nav.addWidget(btn)

        self.top_nav_widget = QWidget()
        self.top_nav_widget.setObjectName("TopNavWidget")
        self.top_nav_widget.setLayout(self.top_nav)
        self.top_nav_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.top_nav_widget.setStyleSheet("""
            QWidget#TopNavWidget{
                background:rgba(2,6,23,0.88);
                border:1px solid rgba(59,130,246,0.18);
                border-radius:20px;
            }
        """)

        top_bar.addWidget(self.top_nav_widget, 1)
        top_bar.addWidget(self.level_switch)

        # =====================================
        # BODY
        # =====================================

        body = QHBoxLayout()
        body.setContentsMargins(0,0,0,0)
        body.setSpacing(16)

        # =====================================
        # STACK
        # =====================================

        self.stack = QStackedWidget()

        self.dashboard = DashboardHome()
        self.students = StudentsPage()
        self.academics = AcademicsPage()
        self.exams = ExamsWindow()
        self.results = ResultsCenter()
        self.history = HistoricalResultsPage()
        self.school = SchoolCenter()
        self.settings = SettingsPage()
        self._startup_warmup_pages = [
            self.students,
            self.academics,
            self.exams,
            self.results,
            self.history,
            self.school,
            self.settings,
        ]
        self._startup_warmup_index = 0
        self._page_last_refreshed = {}

        self.dashboard.open_students.connect(
            lambda: self.switch_page(
                self.students,
                self.btn_students
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

        self.dashboard.open_ranking.connect(
            lambda: (
                self.switch_page(self.history, self.btn_history),
                self.history.show_list()
            )
        )

        self.dashboard.open_readiness.connect(
            lambda: (
                self.switch_page(
                    self.results,
                    self.btn_results
                ),
                self.results.open_readiness()
            )
        )

        self.dashboard.open_history.connect(
            lambda: self.switch_page(
                self.history,
                self.btn_history
            )
        )

        self.dashboard.open_broadsheet.connect(
            lambda: (
                self.switch_page(self.history, self.btn_history),
                self.history.show_list()
            )
        )

        self.dashboard.open_report_book.connect(
            lambda: (
                self.switch_page(self.history, self.btn_history),
                self.history.show_list()
            )
        )

        self.dashboard.open_reports.connect(
            lambda: (
                self.switch_page(self.history, self.btn_history),
                self.history.show_list()
            )
        )

        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.students)
        self.stack.addWidget(self.academics)
        self.stack.addWidget(self.exams)
        self.stack.addWidget(self.results)
        self.stack.addWidget(self.history)
        self.stack.addWidget(self.school)
        self.stack.addWidget(self.settings)

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

        self.btn_history.clicked.connect(
            lambda: self.switch_page(
                self.history,
                self.btn_history
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

        body.addWidget(self.stack)
        body.setStretch(0, 1)

        self.main_layout.addLayout(top_bar)
        self.main_layout.addLayout(body, 1)

        # =====================================
        # EVENTS
        # =====================================

        EventBus.subscribe(
            "OPEN_RESULTS_ENTRY",
            self.open_results_entry
        )
        EventBus.subscribe(
            "THEME_CHANGED",
            self.on_theme_changed
        )

        # =====================================
        # DEFAULT PAGE
        # =====================================

        self.switch_page(
            self.dashboard,
            self.btn_dashboard
        )

        QTimer.singleShot(250, self._warmup_pages)

        # =====================================
        # WINDOW GEOMETRY
        # =====================================
        # Use 95% of the available desktop area so the app does not hide behind
        # the OS panel/title bar on 1366x768 screens.
        available = self.screen().availableGeometry()
        self.resize(
            int(available.width() * 0.95),
            int(available.height() * 0.95)
        )
        self.setMinimumSize(1100, 650)

        qr = self.frameGeometry()
        qr.moveCenter(available.center())
        self.move(qr.topLeft())

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
        if page not in self._page_last_refreshed:
            self._refresh_page(page)
            self._page_last_refreshed[page] = True

    def update_highlight(
        self,
        active_btn
    ):
        for btn in self.nav_buttons:
            if btn == active_btn:
                btn.setStyleSheet(self.nav_button_active_style)
            else:
                btn.setStyleSheet(self.nav_button_style)

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

    def toggle_level(self, is_a_level):
        if is_a_level:
            SystemState.set_level("A_LEVEL")
        else:
            SystemState.set_level("O_LEVEL")
        self.refresh_all()

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

    def open_history_ranking(self, exam_id, class_name):
        self.switch_page(self.history, self.btn_history)
        self.history.activate_ranking(exam_id, class_name)

    def open_history_broadsheet(self, exam_id, class_name):
        self.switch_page(self.history, self.btn_history)
        self.history.activate_broadsheet(exam_id, class_name)

    def open_history_reports(self, exam_id, class_name):
        self.switch_page(self.history, self.btn_history)
        self.history.activate_reports(exam_id, class_name)

    # =====================================
    # REFRESH
    # =====================================

    def refresh_all(self):
        self._refresh_page(self.dashboard)
        self._refresh_page(self.stack.currentWidget())
        current = self.stack.currentWidget()
        if current is not None:
            self._page_last_refreshed[current] = True

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

    def _warmup_pages(self):
        if self._startup_warmup_index >= len(self._startup_warmup_pages):
            return

        page = self._startup_warmup_pages[self._startup_warmup_index]
        self._startup_warmup_index += 1

        try:
            self._refresh_page(page)
        finally:
            self._page_last_refreshed[page] = True
            QTimer.singleShot(250, self._warmup_pages)

    def _apply_theme(self, theme_name="Blue"):
        self.apply_theme(theme_name)

    def on_theme_changed(self, theme_name):
        self.apply_theme(theme_name)

    def apply_theme(self, theme_name="Blue"):
        """Apply the selected application theme."""
        normalized = normalize_theme_name(theme_name)
        self.current_theme = normalized

        app = QApplication.instance()
        if app:
            apply_app_theme(app, normalized)
