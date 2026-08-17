from PySide6.QtGui import QIcon, QPainter, QColor, QPen, QPixmap
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
    QSizePolicy,
    QMenu
)

from app_paths import find_icon_path
from ui.pages.initial_setup_wizard import InitialSetupWizard, needs_initial_setup


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
from theme import (
    normalize_theme_name,
    apply_theme as apply_app_theme,
    get_tokens,
    available_theme_names,
)


def _icon(*names):
    """Return a QIcon using the shared assets/icons path."""
    path = find_icon_path(*names)
    return QIcon(str(path)) if path is not None else QIcon()


def _tinted_icon(icon_name, color, size=18):
    """Render a monochrome icon whose color follows the active theme."""
    source = _icon(icon_name).pixmap(size, size)
    if source.isNull():
        return QIcon()

    tinted = QPixmap(source.size())
    tinted.setDevicePixelRatio(source.devicePixelRatio())
    tinted.fill(Qt.transparent)
    painter = QPainter(tinted)
    painter.drawPixmap(0, 0, source)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(tinted.rect(), QColor(color))
    painter.end()
    return QIcon(tinted)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self._closing = False
        self._setup_mode = needs_initial_setup()

        self.setWindowTitle("SRMS V5")
        self.setWindowIcon(_icon("icon.ico", "icon.png", "icon.jpg", "app_icon.ico", "app_icon.png", "app_icon.jpg"))

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
        self.breadcrumb.setObjectName("BreadcrumbLabel")

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
        self._nav_icon_names = {
            self.btn_dashboard: "dashboard.svg",
            self.btn_students: "students.svg",
            self.btn_academics: "academics.svg",
            self.btn_exams: "exams.svg",
            self.btn_results: "results.svg",
            self.btn_history: "dashboard.svg",
            self.btn_school: "school.svg",
            self.btn_settings: "settings.svg",
        }

        self.nav_button_style, self.nav_button_active_style = self._build_nav_button_styles(
            get_tokens(self.current_theme)
        )

        self.active_btn = None
        self._nav_labels = {}

        self.top_nav = QHBoxLayout()
        self.top_nav.setSpacing(2)
        self.top_nav.setContentsMargins(6, 5, 6, 5)

        for btn in self.nav_buttons:
            self._nav_labels[btn] = btn.text()
            btn.setObjectName("NavButton")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setIconSize(QSize(18, 18))
            btn.setMinimumHeight(34)
            btn.setMaximumHeight(38)
            btn.setMinimumWidth(76)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setStyleSheet(self.nav_button_style)
            btn.setToolTip(btn.text())
            self.top_nav.addWidget(btn)

        self.top_nav_widget = QWidget()
        self.top_nav_widget.setObjectName("TopNavWidget")
        self.top_nav_widget.setAttribute(Qt.WA_StyledBackground, True)
        self.top_nav_widget.setLayout(self.top_nav)
        self.top_nav_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        top_bar.addWidget(self.top_nav_widget, 1)

        # Refresh Button
        self.btn_refresh = QPushButton()
        self.btn_refresh.setObjectName("RefreshButton")
        self.btn_refresh.setAttribute(Qt.WA_StyledBackground, True)
        self.btn_refresh.setIcon(_icon("refresh.svg"))
        self.btn_refresh.setIconSize(QSize(18, 18))
        self.btn_refresh.setFixedSize(34, 34)
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.setToolTip("Refresh system data  •  Right-click to change theme")
        self.btn_refresh.clicked.connect(self.refresh_all)
        self.btn_refresh.setContextMenuPolicy(Qt.CustomContextMenu)
        self.btn_refresh.customContextMenuRequested.connect(self._show_theme_menu)
        top_bar.addWidget(self.btn_refresh)

        # Apply the chrome (nav bar / refresh button / breadcrumb) styling
        # for the current theme now that all the relevant widgets exist.
        self._apply_chrome_styles(get_tokens(self.current_theme))

        top_bar.addWidget(self.level_switch)

        # =====================================
        # BODY
        # =====================================

        body = QHBoxLayout()
        body.setContentsMargins(0,0,0,0)
        body.setSpacing(16)

        # =====================================
        # STACK & SCROLL AREA
        # =====================================

        self.stack = QStackedWidget()
        self.setup_page = InitialSetupWizard()
        self.setup_page.completed.connect(self._on_setup_completed)
        self.stack.addWidget(self.setup_page)

        from ui.pages.dashboard_home import DashboardHome
        self.dashboard = DashboardHome()
        self.students = None
        self.academics = None
        self.exams = None
        self.results = None
        self.history = None
        self.school = None
        self.settings = None

        def create_students_page():
            from students_page import StudentsPage
            return StudentsPage()

        def create_academics_page():
            from academics_page import AcademicsPage
            return AcademicsPage()

        def create_exams_window():
            from exams import ExamsWindow
            return ExamsWindow()

        def create_results_center():
            from results_center import ResultsCenter
            return ResultsCenter()

        def create_history_page():
            from ui.pages.historical_results_page import HistoricalResultsPage
            return HistoricalResultsPage()

        def create_school_center():
            from school_center import SchoolCenter
            return SchoolCenter()

        def create_settings_page():
            from settings_page import SettingsPage
            return SettingsPage()

        self._page_factories = {
            "students": create_students_page,
            "academics": create_academics_page,
            "exams": create_exams_window,
            "results": create_results_center,
            "history": create_history_page,
            "school": create_school_center,
            "settings": create_settings_page,
        }
        self._page_attributes = {
            "students": "students",
            "academics": "academics",
            "exams": "exams",
            "results": "results",
            "history": "history",
            "school": "school",
            "settings": "settings",
        }
        self._page_last_refreshed = {}

        self.dashboard.open_students.connect(
            lambda: self.switch_named_page("students", self.btn_students)
        )

        self.dashboard.open_academics.connect(
            lambda: self.switch_named_page("academics", self.btn_academics)
        )

        self.dashboard.open_exams.connect(
            lambda: self.switch_named_page("exams", self.btn_exams)
        )

        self.dashboard.open_results.connect(
            lambda: self.switch_named_page("results", self.btn_results)
        )

        self.dashboard.open_school.connect(
            lambda: self.switch_named_page("school", self.btn_school)
        )

        self.dashboard.open_ranking.connect(
            lambda: (
                self.switch_named_page("history", self.btn_history),
                self.history.show_list() if self.history else None,
            )
        )

        self.dashboard.open_readiness.connect(
            lambda: (
                self.switch_named_page("results", self.btn_results),
                self.results.open_readiness() if self.results else None,
            )
        )

        self.dashboard.open_history.connect(
            lambda: self.switch_named_page("history", self.btn_history)
        )

        self.dashboard.open_broadsheet.connect(
            lambda: (
                self.switch_named_page("history", self.btn_history),
                self.history.show_list() if self.history else None,
            )
        )

        self.dashboard.open_report_book.connect(
            lambda: (
                self.switch_named_page("history", self.btn_history),
                self.history.show_list() if self.history else None,
            )
        )

        self.dashboard.open_reports.connect(
            lambda: (
                self.switch_named_page("history", self.btn_history),
                self.history.show_list() if self.history else None,
            )
        )

        self.stack.addWidget(self.dashboard)

        # =====================================
        # NAVIGATION
        # =====================================

        self.btn_dashboard.clicked.connect(
            lambda: self.switch_page(self.dashboard, self.btn_dashboard)
        )

        self.btn_students.clicked.connect(
            lambda: self.switch_named_page("students", self.btn_students)
        )

        self.btn_academics.clicked.connect(
            lambda: self.switch_named_page("academics", self.btn_academics)
        )

        self.btn_exams.clicked.connect(
            lambda: self.switch_named_page("exams", self.btn_exams)
        )

        self.btn_results.clicked.connect(
            lambda: self.switch_named_page("results", self.btn_results)
        )

        self.btn_history.clicked.connect(
            lambda: self.switch_named_page("history", self.btn_history)
        )

        self.btn_school.clicked.connect(
            lambda: self.switch_named_page("school", self.btn_school)
        )

        self.btn_settings.clicked.connect(
            lambda: self.switch_named_page("settings", self.btn_settings)
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

        if self._setup_mode:
            self._enter_setup_mode()
            self.switch_page(self.setup_page, None)

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

    def closeEvent(self, event):
        self._closing = True
        super().closeEvent(event)

    # =====================================
    # NAVIGATION
    # =====================================

    def switch_page(
        self,
        page,
        button
    ):
        if page is None:
            return

        is_already_active = (self.stack.currentWidget() == page)

        if self.stack.indexOf(page) == -1:
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)
        self.active_btn = button
        self.update_highlight(button)
        self._update_breadcrumb(button)

        if not is_already_active:
            if page not in self._page_last_refreshed:
                self._refresh_page(page)
                self._page_last_refreshed[page] = True
        else:
            # Re-clicking the active navigation button triggers a refresh
            self._refresh_page(page)

    def switch_named_page(self, page_name, button):
        page = self.ensure_page(page_name)
        self.switch_page(page, button)

    def ensure_page(self, page_name):
        attr_name = self._page_attributes[page_name]
        page = getattr(self, attr_name)
        if page is None:
            try:
                page = self._page_factories[page_name]()
            except Exception as error:
                import traceback
                traceback.print_exc()
                self._log_page_load_failure(page_name, error)
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self,
                    "Failed to open module",
                    f"The '{page_name}' module could not be opened.\n\n"
                    f"{type(error).__name__}: {error}\n\n"
                    "Details were written to srms_error.log next to the app.",
                )
                return None
            setattr(self, attr_name, page)
            if self.stack.indexOf(page) == -1:
                self.stack.addWidget(page)
            self._refresh_page(page)
            self._page_last_refreshed[page] = True
        return page

    @staticmethod
    def _log_page_load_failure(page_name, error):
        """Write the failure to a log file next to the app.

        This matters most in --windowed frozen builds, which have no
        console, so a stderr traceback would otherwise be invisible.
        """
        import traceback
        from datetime import datetime
        try:
            from app_paths import DATA_DIR
            log_path = DATA_DIR / "srms_error.log"
        except Exception:
            from pathlib import Path
            log_path = Path.cwd() / "srms_error.log"
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n[{datetime.now().isoformat()}] Failed to open page '{page_name}'\n")
                traceback.print_exc(file=f)
        except Exception:
            pass

    def update_highlight(
        self,
        active_btn
    ):
        if active_btn is None:
            return
        for btn in self.nav_buttons:
            if btn == active_btn:
                btn.setStyleSheet(self.nav_button_active_style)
            else:
                btn.setStyleSheet(self.nav_button_style)
        self._refresh_theme_icons()

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

        # Ensure the CURRENT page is refreshed immediately.
        # SystemState.set_level emits LEVEL_CHANGED, which many pages handle.
        # But for robustness, we call refresh_all which targets both dashboard and current page.
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
            self.ensure_page("results"),
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
        history = self.ensure_page("history")
        self.switch_page(history, self.btn_history)
        history.refresh_all()
        history.activate_ranking(exam_id, class_name)

    def open_history_broadsheet(self, exam_id, class_name):
        history = self.ensure_page("history")
        self.switch_page(history, self.btn_history)
        history.refresh_all()
        history.activate_broadsheet(exam_id, class_name)

    def open_history_reports(self, exam_id, class_name):
        history = self.ensure_page("history")
        self.switch_page(history, self.btn_history)
        history.refresh_all()
        history.activate_reports(exam_id, class_name)

    # =====================================
    # REFRESH
    # =====================================

    def refresh_all(self):
        self._refresh_page(self.dashboard)
        if getattr(self, "history", None) is not None:
            self._refresh_page(self.history)
        self._refresh_page(self.stack.currentWidget())
        current = self.stack.currentWidget()
        if current is not None:
            self._page_last_refreshed[current] = True

    @staticmethod
    def _refresh_page(page):

        for method_name in (
            "refresh_all",
            "load_dashboard",
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
            self._repolish_all(app)

        # Dashboard icons are cached pixmaps, so unlike stylesheet-driven
        # controls they must be regenerated after a theme switch.
        if hasattr(self, "dashboard"):
            self.dashboard.refresh_theme_assets()

        # The nav bar / refresh button / breadcrumb are drawn with their own
        # widget-level stylesheets (they sit "on top of" the global QSS), so
        # they need to be rebuilt from the new theme's tokens explicitly.
        self._apply_chrome_styles(get_tokens(normalized))

    def _repolish_all(self, app):
        """Force every widget to re-evaluate its stylesheet and repaint.

        A plain app.setStyleSheet() call doesn't reliably invalidate size
        hints or cached QGraphicsDropShadowEffect pixmaps on every widget,
        which is what causes the "ghosting"/overlapping-text artifact where
        a card still shows a faint trace of the previous theme's render
        underneath the new one. Explicitly unpolishing/polishing and
        toggling graphics effects clears those stale caches.
        """
        for w in app.allWidgets():
            w.style().unpolish(w)
            w.style().polish(w)
            effect = w.graphicsEffect()
            if effect is not None:
                effect.setEnabled(False)
                effect.setEnabled(True)
            w.update()

    # =====================================
    # THEME-AWARE CHROME (nav bar / refresh button / breadcrumb)
    # =====================================

    def _build_nav_button_styles(self, tokens):
        """Return (inactive_style, active_style) QSS strings for nav buttons,
        built from the given theme tokens instead of hardcoded colors."""
        inactive_style = f"""
            QPushButton#NavButton{{
                text-align:center;
                padding:7px 9px;
                border-radius:12px;
                font-weight:900;
                color:{tokens['text_soft']};
                font-size:12px;
                background:transparent;
                border:1px solid transparent;
                min-height:22px;
            }}
            QPushButton#NavButton:hover{{
                color:{tokens['text_soft']};
                background:rgba(59,130,246,0.14);
                border:1px solid {tokens['border']};
            }}
        """
        active_style = f"""
            QPushButton#NavButton{{
                background:{tokens['primary']};
                color:#FFFFFF;
                font-weight:900;
                border:1px solid {tokens['border']};
                border-radius:12px;
                padding:7px 9px;
                min-height:22px;
            }}
        """
        return inactive_style, active_style

    def _apply_chrome_styles(self, tokens):
        """Re-style the widgets that carry their own stylesheet (and would
        otherwise stay locked to whatever theme was active at startup)."""
        self.nav_button_style, self.nav_button_active_style = self._build_nav_button_styles(tokens)

        self.top_nav_widget.setStyleSheet(f"""
            QWidget#TopNavWidget{{
                background:{tokens['surface_alt']};
                border:1px solid {tokens['border']};
                border-radius:20px;
            }}
        """)

        self.btn_refresh.setStyleSheet(f"""
            QPushButton#RefreshButton {{
                background: {tokens['surface_alt']};
                border: 1px solid {tokens['border']};
                border-radius: 17px;
                color: {tokens['text_soft']};
            }}
            QPushButton#RefreshButton:hover {{
                background: rgba(59, 130, 246, 0.15);
                border: 1px solid {tokens['primary_2']};
            }}
        """)

        self.breadcrumb.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 800;
            color: {tokens['primary_2']};
            padding: 0 8px;
        """)

        # Re-apply active/inactive styling to whichever nav button is current,
        # since the strings it references were just rebuilt above.
        for btn in self.nav_buttons:
            if btn == self.active_btn:
                btn.setStyleSheet(self.nav_button_active_style)
            else:
                btn.setStyleSheet(self.nav_button_style)
        self._refresh_theme_icons()

    def _refresh_theme_icons(self):
        """Keep chrome icons readable after a theme or active-page change."""
        tokens = get_tokens(self.current_theme)
        inactive_color = tokens["muted"] if tokens.get("is_light") else tokens["text_soft"]
        for button, icon_name in self._nav_icon_names.items():
            color = "#ffffff" if button == self.active_btn else inactive_color
            button.setIcon(_tinted_icon(icon_name, color))
        self.btn_refresh.setIcon(_tinted_icon("refresh.svg", tokens["text_soft"]))

    def _show_theme_menu(self, pos):
        """Right-click menu on the refresh button to switch themes.
        Left-click still refreshes as before; this is purely additive."""
        menu = QMenu(self)
        for name in available_theme_names():
            action = menu.addAction(name)
            action.setCheckable(True)
            action.setChecked(normalize_theme_name(name) == self.current_theme)
            action.triggered.connect(lambda checked=False, n=name: self.apply_theme(n))
        menu.exec(self.btn_refresh.mapToGlobal(pos))

    def _enter_setup_mode(self):
        self.top_nav_widget.setVisible(False)
        self.btn_refresh.setVisible(False)
        self.level_switch.setVisible(False)

    def _exit_setup_mode(self):
        self.top_nav_widget.setVisible(True)
        self.btn_refresh.setVisible(True)
        self.level_switch.setVisible(True)

    def _on_setup_completed(self):
        self._setup_mode = False
        self._exit_setup_mode()
        self.switch_page(self.dashboard, self.btn_dashboard)
        self.refresh_all()
