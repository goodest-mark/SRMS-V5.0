from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    Qt,
    QTimer,
    QPoint,
    QParallelAnimationGroup,
)
from PySide6.QtGui import QFont, QIcon, QPixmap, QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app_paths import icon_path


class SplashScreen(QWidget):
    def __init__(self, on_finish, account_email="issatzuberi99@gmail.com"):
        super().__init__()

        self.on_finish = on_finish
        self.account_email = account_email
        self._drag_pos = None
        self._is_maximized = False
        self._normal_geometry = None

        self.setWindowTitle("SRMS V5")
        app_icon = icon_path("icon.jpeg")
        if app_icon.exists():
            self.setWindowIcon(QIcon(str(app_icon)))

        # --- Frameless + transparent so only the rounded card is visible ---
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._apply_main_window_geometry()
        self.setObjectName("SplashRoot")

        # Outer layout leaves margin around the card so the shadow has room to render
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 30, 30, 30)
        root.setSpacing(0)

        # --- Main square card shell ---
        shell = QFrame()
        shell.setObjectName("SplashShell")
        shell.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(80)
        shadow.setXOffset(0)
        shadow.setYOffset(20)
        shadow.setColor(QColor(0, 0, 0, 180))
        shell.setGraphicsEffect(shadow)

        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        # --- Custom title bar ---
        title_bar = QFrame()
        title_bar.setObjectName("SplashTitleBar")
        title_bar.setFixedHeight(44)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(16, 0, 12, 0)
        title_bar_layout.setSpacing(6)
        title_bar_layout.addStretch(1)

        self.min_btn = QPushButton("\u2013")
        self.max_btn = QPushButton("\u25a1")
        self.close_btn = QPushButton("\u2715")
        for btn, name in (
            (self.min_btn, "SplashTitleBtn"),
            (self.max_btn, "SplashTitleBtn"),
            (self.close_btn, "SplashTitleCloseBtn"),
        ):
            btn.setObjectName(name)
            btn.setFixedSize(30, 30)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.min_btn.clicked.connect(self.showMinimized)
        self.max_btn.clicked.connect(self._toggle_maximize)
        self.close_btn.clicked.connect(self.close)

        title_bar_layout.addWidget(self.min_btn)
        title_bar_layout.addWidget(self.max_btn)
        title_bar_layout.addWidget(self.close_btn)

        self._title_bar = title_bar

        # --- Centered content ---
        content = QFrame()
        content.setObjectName("SplashContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(48, 24, 48, 36)
        content_layout.setSpacing(0)
        content_layout.addStretch(2)

        # Title
        title = QLabel("SRMS")
        title.setObjectName("SplashTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label = title

        # Glow underline
        underline = QFrame()
        underline.setObjectName("SplashTitleUnderline")
        underline.setFixedHeight(3)
        underline.setFixedWidth(420)
        underline_row = QHBoxLayout()
        underline_row.addStretch(1)
        underline_row.addWidget(underline)
        underline_row.addStretch(1)

        # Subtitle
        subtitle = QLabel("R e s u l t   M a n a g e m e n t   S y s t e m")
        subtitle.setObjectName("SplashSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        content_layout.addWidget(title)
        content_layout.addSpacing(14)
        content_layout.addLayout(underline_row)
        content_layout.addSpacing(18)
        content_layout.addWidget(subtitle)
        content_layout.addStretch(3)

        # Progress bar (thin flat line)
        self.progress = QProgressBar()
        self.progress.setObjectName("SplashProgress")
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)

        # Loading label with animated ellipsis
        self.loading = QLabel("Initializing")
        self.loading.setObjectName("SplashLoading")
        self.loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_dots = 0
        self._current_loading_text = "Initializing"
        self._loading_timer = QTimer(self)
        self._loading_timer.timeout.connect(self._update_loading_dots)
        self._loading_timer.start(500)

        content_layout.addWidget(self.progress)
        content_layout.addSpacing(14)
        content_layout.addWidget(self.loading)
        content_layout.addStretch(2)

        # Divider
        divider = QFrame()
        divider.setObjectName("SplashDivider")
        divider.setFixedHeight(1)

        # Footer: signed-in account email, small and centered
        footer = QLabel(self.account_email)
        footer.setObjectName("SplashFooterEmail")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        footer_wrap = QVBoxLayout()
        footer_wrap.setSpacing(14)
        footer_wrap.setContentsMargins(48, 0, 48, 24)
        footer_wrap.addWidget(divider)
        footer_wrap.addWidget(footer)

        # --- Assemble shell ---
        shell_layout.addWidget(title_bar)
        shell_layout.addWidget(content, 1)
        shell_layout.addLayout(footer_wrap)

        root.addWidget(shell)

        # --- Stylesheet (premium look, square card) ---
        self.setStyleSheet("""
            * {
                font-family: 'Segoe UI', 'Inter', -apple-system, 'Helvetica Neue', sans-serif;
            }
            QWidget#SplashRoot {
                background: transparent;
            }
            QFrame#SplashShell {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0a0e1a, stop:1 #060810
                );
                border: 1px solid rgba(37, 99, 235, 0.25);
                border-radius: 20px;
            }
            QFrame#SplashTitleBar {
                background: #14151c;
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            }
            QPushButton#SplashTitleBtn {
                background: transparent;
                color: #94a3b8;
                border: none;
                border-radius: 6px;
                font-size: 15px;
                font-weight: 600;
            }
            QPushButton#SplashTitleBtn:hover {
                background: rgba(148, 163, 184, 0.15);
                color: #ffffff;
            }
            QPushButton#SplashTitleCloseBtn {
                background: transparent;
                color: #94a3b8;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton#SplashTitleCloseBtn:hover {
                background: #e81123;
                color: #ffffff;
            }
            QFrame#SplashContent {
                background: transparent;
            }
            QLabel#SplashTitle {
                color: #ffffff;
                font-size: 120px;
                font-weight: 900;
                letter-spacing: 18px;
            }
            QFrame#SplashTitleUnderline {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(37, 99, 235, 0),
                    stop:0.5 rgba(59, 130, 246, 220),
                    stop:1 rgba(37, 99, 235, 0)
                );
                border-radius: 1px;
            }
            QLabel#SplashSubtitle {
                color: #93c5fd;
                font-size: 26px;
                font-weight: 500;
            }
            QProgressBar#SplashProgress {
                background: rgba(148, 163, 184, 0.15);
                border: none;
                border-radius: 3px;
            }
            QProgressBar#SplashProgress::chunk {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563eb, stop:1 #3b82f6
                );
                border-radius: 3px;
            }
            QLabel#SplashLoading {
                color: #7ea6d8;
                font-size: 20px;
                font-weight: 500;
            }
            QFrame#SplashDivider {
                background: rgba(148, 163, 184, 0.15);
            }
            QLabel#SplashFooterEmail {
                color: #64748b;
                font-size: 12px;
                font-weight: 500;
            }
        """)

        # --- State ---
        self._finished = False
        self._stages = [
            (10, "Initializing local data store"),
            (25, "Loading school profile"),
            (40, "Preparing academic modules"),
            (55, "Restoring exam and results services"),
            (70, "Loading ranking and reporting tools"),
            (85, "Applying user interface settings"),
            (95, "Launching SRMS V5"),
        ]

        # --- Progress animation (eased) ---
        # Fill takes 3s, then we hold on the completed screen for a few
        # seconds (see _on_progress_finished) so the user has time to read
        # everything, including the small account email at the bottom.
        self._progress_anim = QPropertyAnimation(self.progress, b"value", self)
        self._progress_anim.setDuration(9000)
        self._progress_anim.setStartValue(0)
        self._progress_anim.setEndValue(100)
        self._progress_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._progress_anim.valueChanged.connect(self._on_progress_value_changed)
        self._progress_anim.finished.connect(self._on_progress_finished)

        # --- Fade in on open ---
        self.setWindowOpacity(0.0)
        self._fade_in = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade_in.setDuration(250)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Start all animations
        QTimer.singleShot(0, self._start)

    def _start(self):
        self._fade_in.start()
        self._progress_anim.start()

    def _apply_main_window_geometry(self):
        """Square splash sized and centered on screen."""
        available = self.screen().availableGeometry()
        width = min(1280, int(available.width() * 0.90))
        height = min(720, int(available.height() * 0.82))
        self.resize(width, height)
        self.setMinimumSize(1100, 640)

        qr = self.frameGeometry()
        qr.moveCenter(available.center())
        self.move(qr.topLeft())

    # --- Draggable frameless window (via custom title bar) ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._title_bar.underMouse():
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def _toggle_maximize(self):
        if self._is_maximized:
            if self._normal_geometry is not None:
                self.setGeometry(self._normal_geometry)
            self._is_maximized = False
        else:
            self._normal_geometry = self.geometry()
            self.setGeometry(self.screen().availableGeometry())
            self._is_maximized = True

    def _update_loading_dots(self):
        if self._finished:
            return
        self._loading_dots = (self._loading_dots + 1) % 4
        dots = '.' * self._loading_dots
        self.loading.setText(self._current_loading_text + dots)

    def _on_progress_value_changed(self, value):
        if self._finished:
            return
        for threshold, message in self._stages:
            if value >= threshold:
                self._current_loading_text = message

    def _on_progress_finished(self):
        if self._finished:
            return
        self._finished = True
        self._loading_timer.stop()
        self.progress.setValue(100)
        self.loading.setText("Launching SRMS V5")

        # Hold the fully-loaded screen on display so the user has time to
        # read the title, subtitle, and footer email before it closes.
        QTimer.singleShot(3000, self._start_exit_animation)

    def _start_exit_animation(self):
        fade_out = QPropertyAnimation(self, b"windowOpacity", self)
        fade_out.setDuration(300)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InCubic)

        self._exit_group = QParallelAnimationGroup(self)
        self._exit_group.addAnimation(fade_out)
        self._exit_group.finished.connect(self._complete)
        self._exit_group.start()

    def _complete(self):
        self.on_finish()
        self.close()
