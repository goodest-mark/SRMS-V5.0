from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    Qt,
    QTimer,
    QParallelAnimationGroup,
)
from PySide6.QtGui import QFont, QFontMetrics, QIcon, QPixmap, QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app_paths import icon_path


class SplashScreen(QWidget):
    def __init__(self, on_finish):
        super().__init__()

        self.on_finish = on_finish

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
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(0)

        # --- Main card shell ---
        shell = QFrame()
        shell.setObjectName("SplashShell")
        shell.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(80)
        shadow.setXOffset(0)
        shadow.setYOffset(20)
        shadow.setColor(QColor(0, 0, 0, 180))
        shell.setGraphicsEffect(shadow)

        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(28, 28, 28, 28)
        shell_layout.setSpacing(28)

        # --- Left Brand Panel ---
        left = QFrame()
        left.setObjectName("SplashBrandPanel")
        left.setMinimumWidth(380)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(32, 32, 32, 32)
        left_layout.setSpacing(16)

        # Icon badge with pulse glow
        icon_label = QLabel()
        icon_label.setFixedSize(80, 80)
        icon_label.setObjectName("SplashIconBadge")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_pixmap = QPixmap(str(icon_path("icon.jpeg")))
        if not icon_pixmap.isNull():
            icon_label.setPixmap(
                icon_pixmap.scaled(
                    56, 56,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        self.icon_label = icon_label

        # Badge text (e.g., "SCHOOL RECORDS")
        badge = QLabel("SCHOOL RECORDS MANAGEMENT SYSTEM")
        badge.setObjectName("SplashBadge")
        badge.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Main title – now static
        title = QLabel("SRMS V5")
        title.setObjectName("SplashTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.title_label = title

        # Underline – static, full width
        title_underline = QFrame()
        title_underline.setObjectName("SplashTitleUnderline")
        title_underline.setFixedHeight(4)
        # Compute width based on font metrics
        font = QFont("Segoe UI")
        font.setPixelSize(38)
        font.setWeight(QFont.Weight.Black)
        full_width = QFontMetrics(font).horizontalAdvance("SRMS V5")
        title_underline.setFixedWidth(full_width)
        self._title_underline = title_underline

        # Subtitle
        subtitle = QLabel("School Records Management System")
        subtitle.setObjectName("SplashSubtitle")
        subtitle.setWordWrap(True)

        # Summary
        summary = QLabel(
            "Academic records, results processing, reporting, and school administration in one workspace."
        )
        summary.setObjectName("SplashSummary")
        summary.setWordWrap(True)

        # Chips (tags)
        chips_row = QHBoxLayout()
        chips_row.setSpacing(10)
        for text in ("Students", "Results", "Reports"):
            chip = QLabel(text)
            chip.setObjectName("SplashChip")
            chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chips_row.addWidget(chip)
        chips_row.addStretch(1)

        left_layout.addWidget(icon_label)
        left_layout.addSpacing(4)
        left_layout.addWidget(badge)
        left_layout.addSpacing(2)
        left_layout.addWidget(title)
        left_layout.addWidget(title_underline)
        left_layout.addWidget(subtitle)
        left_layout.addWidget(summary)
        left_layout.addStretch(1)
        left_layout.addLayout(chips_row)

        # --- Right Status Panel ---
        right = QFrame()
        right.setObjectName("SplashStatusPanel")
        right.setMinimumWidth(440)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(32, 32, 32, 32)
        right_layout.setSpacing(16)

        header = QLabel("Starting application")
        header.setObjectName("SplashSectionTitle")

        # Loading label with animated ellipsis
        self.loading = QLabel("Initializing local services")
        self.loading.setObjectName("SplashLoading")
        self.loading.setWordWrap(True)
        self._loading_dots = 0
        self._loading_timer = QTimer(self)
        self._loading_timer.timeout.connect(self._update_loading_dots)
        self._loading_timer.start(500)

        # Progress bar (premium style)
        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p%")

        # Status details grid
        info_grid = QGridLayout()
        info_grid.setHorizontalSpacing(16)
        info_grid.setVerticalSpacing(12)

        details = [
            ("Database", "Preparing local data store"),
            ("Session", "Loading school profile"),
            ("Modules", "Restoring workspace"),
            ("Security", "Applying startup policy"),
        ]
        for row, (label_text, value_text) in enumerate(details):
            label = QLabel(label_text)
            label.setObjectName("SplashInfoLabel")
            value = QLabel(value_text)
            value.setObjectName("SplashInfoValue")
            value.setWordWrap(True)
            info_grid.addWidget(label, row, 0)
            info_grid.addWidget(value, row, 1)

        # Divider
        divider = QFrame()
        divider.setObjectName("SplashDivider")
        divider.setFixedHeight(1)

        # Footer with version and premium badge
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(12)

        footer_left = QLabel("SRMS V5.0.1")
        footer_left.setObjectName("SplashFooter")

        premium_badge = QLabel("PREMIUM")
        premium_badge.setObjectName("SplashPremiumBadge")
        premium_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        footer_layout.addWidget(footer_left)
        footer_layout.addStretch(1)
        footer_layout.addWidget(premium_badge)

        right_layout.addWidget(header)
        right_layout.addWidget(self.loading)
        right_layout.addWidget(self.progress)
        right_layout.addLayout(info_grid)
        right_layout.addStretch(1)
        right_layout.addWidget(divider)
        right_layout.addLayout(footer_layout)

        # --- Assemble shell ---
        shell_layout.addWidget(left, 3)
        shell_layout.addWidget(right, 2)

        root.addStretch(1)
        root.addWidget(shell)
        root.addStretch(1)

        # --- Stylesheet (premium look) ---
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
                    stop:0 #0b1729, stop:1 #09121e
                );
                border: 1px solid rgba(96, 165, 250, 0.25);
                border-radius: 28px;
            }
            QFrame#SplashBrandPanel {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a3a6b, stop:1 #102a4a
                );
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 20px;
            }
            QFrame#SplashStatusPanel {
                background: rgba(8, 16, 32, 0.92);
                border: 1px solid rgba(96, 165, 250, 0.20);
                border-radius: 20px;
            }
            QLabel#SplashIconBadge {
                background: rgba(37, 99, 235, 0.25);
                border: 2px solid rgba(96, 165, 250, 0.5);
                border-radius: 20px;
            }
            QLabel#SplashBadge {
                color: #a5c9ff;
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 1.5px;
            }
            QLabel#SplashTitle {
                color: #ffffff;
                font-size: 38px;
                font-weight: 900;
                letter-spacing: -0.5px;
            }
            QFrame#SplashTitleUnderline {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:0.5 #8b5cf6, stop:1 #22c55e
                );
                border-radius: 2px;
            }
            QLabel#SplashSubtitle {
                color: #dbeafe;
                font-size: 16px;
                font-weight: 700;
            }
            QLabel#SplashSummary {
                color: #94a3b8;
                font-size: 13px;
            }
            QLabel#SplashChip {
                background: rgba(37, 99, 235, 0.18);
                color: #e8f0fe;
                border: 1px solid rgba(96, 165, 250, 0.30);
                border-radius: 999px;
                padding: 6px 14px;
                min-width: 90px;
                font-size: 12px;
                font-weight: 700;
            }
            QLabel#SplashSectionTitle {
                color: #e2e8f0;
                font-size: 18px;
                font-weight: 800;
            }
            QLabel#SplashLoading {
                color: #ffffff;
                font-size: 20px;
                font-weight: 800;
            }
            QLabel#SplashInfoLabel {
                color: #93c5fd;
                font-size: 12px;
                font-weight: 800;
                text-transform: uppercase;
            }
            QLabel#SplashInfoValue {
                color: #e2e8f0;
                font-size: 13px;
                font-weight: 600;
            }
            QFrame#SplashDivider {
                background: rgba(148, 163, 184, 0.15);
            }
            QLabel#SplashFooter {
                color: #94a3b8;
                font-size: 12px;
                font-weight: 700;
            }
            QLabel#SplashPremiumBadge {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f59e0b, stop:1 #f97316
                );
                color: #0f172a;
                border-radius: 999px;
                padding: 4px 14px;
                font-size: 10px;
                font-weight: 900;
                letter-spacing: 0.5px;
            }
            QProgressBar {
                background: rgba(15, 23, 42, 0.92);
                color: #ffffff;
                border: 1px solid rgba(96, 165, 250, 0.20);
                border-radius: 14px;
                text-align: center;
                height: 24px;
                font-weight: 700;
                font-size: 12px;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:0.5 #8b5cf6, stop:1 #2563eb
                );
                border-radius: 12px;
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
        self._progress_anim = QPropertyAnimation(self.progress, b"value", self)
        self._progress_anim.setDuration(3500)
        self._progress_anim.setStartValue(0)
        self._progress_anim.setEndValue(100)
        self._progress_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._progress_anim.valueChanged.connect(self._on_progress_value_changed)
        self._progress_anim.finished.connect(self._on_progress_finished)

        # --- Glow animation on icon badge ---
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(20)
        glow.setColor(QColor(96, 165, 250, 180))
        glow.setXOffset(0)
        glow.setYOffset(0)
        icon_label.setGraphicsEffect(glow)

        self._glow_anim = QPropertyAnimation(glow, b"blurRadius", self)
        self._glow_anim.setDuration(1000)
        self._glow_anim.setLoopCount(-1)
        self._glow_anim.setStartValue(15)
        self._glow_anim.setEndValue(35)
        self._glow_anim.setEasingCurve(QEasingCurve.Type.InOutSine)

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
        self._glow_anim.start()

    def _apply_main_window_geometry(self):
        """Match a clean splash size and centered position."""
        available = self.screen().availableGeometry()
        width = min(1280, int(available.width() * 0.90))
        height = min(720, int(available.height() * 0.82))
        self.resize(width, height)
        self.setMinimumSize(1100, 640)

        qr = self.frameGeometry()
        qr.moveCenter(available.center())
        self.move(qr.topLeft())

    def _update_loading_dots(self):
        if self._finished:
            return
        self._loading_dots = (self._loading_dots + 1) % 4
        if hasattr(self, '_current_loading_text'):
            base = self._current_loading_text
        else:
            base = self.loading.text()
        dots = '.' * self._loading_dots
        self.loading.setText(base + dots)

    def _on_progress_value_changed(self, value):
        if self._finished:
            return
        for threshold, message in self._stages:
            if value >= threshold:
                self._current_loading_text = message
                self.loading.setText(message)  # will be updated by timer

    def _on_progress_finished(self):
        if self._finished:
            return
        self._finished = True
        self._loading_timer.stop()
        self.progress.setValue(100)
        self.loading.setText("Launching SRMS V5")

        QTimer.singleShot(5000, self._start_exit_animation)

    def _start_exit_animation(self):
        fade_out = QPropertyAnimation(self, b"windowOpacity", self)
        fade_out.setDuration(300)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InCubic)

        shell = self.findChild(QFrame, "SplashShell")
        scale_anim = QPropertyAnimation(shell, b"scale", self)
        scale_anim.setDuration(300)
        scale_anim.setStartValue(1.0)
        scale_anim.setEndValue(0.95)
        scale_anim.setEasingCurve(QEasingCurve.Type.InCubic)

        self._exit_group = QParallelAnimationGroup(self)
        self._exit_group.addAnimation(fade_out)
        self._exit_group.addAnimation(scale_anim)
        self._exit_group.finished.connect(self._complete)
        self._exit_group.start()

    def _complete(self):
        self.on_finish()
        self.close()