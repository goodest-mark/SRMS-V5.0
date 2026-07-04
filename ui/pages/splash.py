from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QFrame,
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
        app_icon = icon_path("icon.ico")
        if app_icon.exists():
            self.setWindowIcon(QIcon(str(app_icon)))

        self._apply_main_window_geometry()
        self.setObjectName("SplashRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        shell = QFrame()
        shell.setObjectName("SplashShell")
        shell.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(28, 28, 28, 28)
        shell_layout.setSpacing(24)

        left = QFrame()
        left.setObjectName("SplashBrandPanel")
        left.setMinimumWidth(360)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(28, 28, 28, 28)
        left_layout.setSpacing(14)

        badge = QLabel("SCHOOL RECORDS MANAGEMENT SYSTEM")
        badge.setObjectName("SplashBadge")
        badge.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        icon_label = QLabel()
        icon_label.setFixedSize(112, 112)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        icon_pixmap = QPixmap(str(icon_path("app_icon.png")))
        if not icon_pixmap.isNull():
            icon_label.setPixmap(
                icon_pixmap.scaled(
                    112,
                    112,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        title = QLabel("SRMS V5")
        title.setObjectName("SplashTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        subtitle = QLabel("School Records Management System")
        subtitle.setObjectName("SplashSubtitle")
        subtitle.setWordWrap(True)

        summary = QLabel(
            "Academic records, results processing, reporting, and school administration in one workspace."
        )
        summary.setObjectName("SplashSummary")
        summary.setWordWrap(True)

        chips_row = QHBoxLayout()
        chips_row.setSpacing(8)
        for text in ("Students", "Results", "Reports"):
            chip = QLabel(text)
            chip.setObjectName("SplashChip")
            chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chips_row.addWidget(chip)
        chips_row.addStretch(1)

        left_layout.addWidget(badge)
        left_layout.addSpacing(6)
        left_layout.addWidget(icon_label)
        left_layout.addSpacing(6)
        left_layout.addWidget(title)
        left_layout.addWidget(subtitle)
        left_layout.addWidget(summary)
        left_layout.addStretch(1)
        left_layout.addLayout(chips_row)

        right = QFrame()
        right.setObjectName("SplashStatusPanel")
        right.setMinimumWidth(420)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(28, 28, 28, 28)
        right_layout.setSpacing(14)

        header = QLabel("Starting application")
        header.setObjectName("SplashSectionTitle")

        self.loading = QLabel("Initializing local services...")
        self.loading.setObjectName("SplashLoading")
        self.loading.setWordWrap(True)

        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p%")

        info_grid = QGridLayout()
        info_grid.setHorizontalSpacing(12)
        info_grid.setVerticalSpacing(10)

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

        footer = QLabel("SRMS V5.0")
        footer.setObjectName("SplashFooter")

        right_layout.addWidget(header)
        right_layout.addWidget(self.loading)
        right_layout.addWidget(self.progress)
        right_layout.addLayout(info_grid)
        right_layout.addStretch(1)
        right_layout.addWidget(footer, alignment=Qt.AlignmentFlag.AlignLeft)

        shell_layout.addWidget(left, 3)
        shell_layout.addWidget(right, 2)

        root.addStretch(1)
        root.addWidget(shell)
        root.addStretch(1)

        self.setStyleSheet(
            """
            QWidget#SplashRoot {
                background: #07111f;
            }
            QFrame#SplashShell {
                background: #0c1729;
                border: 1px solid rgba(96, 165, 250, 0.22);
                border-radius: 22px;
            }
            QFrame#SplashBrandPanel {
                background: #10203a;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 18px;
            }
            QFrame#SplashStatusPanel {
                background: rgba(3, 8, 18, 0.94);
                border: 1px solid rgba(96, 165, 250, 0.18);
                border-radius: 18px;
            }
            QLabel#SplashBadge {
                color: #93c5fd;
                font-size: 10px;
                font-weight: 800;
            }
            QLabel#SplashTitle {
                color: #ffffff;
                font-size: 34px;
                font-weight: 900;
            }
            QLabel#SplashSubtitle {
                color: #dbeafe;
                font-size: 15px;
                font-weight: 700;
            }
            QLabel#SplashSummary {
                color: #cbd5e1;
                font-size: 12px;
            }
            QLabel#SplashChip {
                background: rgba(37, 99, 235, 0.16);
                color: #eff6ff;
                border: 1px solid rgba(96, 165, 250, 0.25);
                border-radius: 999px;
                padding: 6px 12px;
                min-width: 84px;
                font-size: 11px;
                font-weight: 700;
            }
            QLabel#SplashSectionTitle {
                color: #e2e8f0;
                font-size: 16px;
                font-weight: 800;
            }
            QLabel#SplashLoading {
                color: #ffffff;
                font-size: 18px;
                font-weight: 800;
            }
            QLabel#SplashInfoLabel {
                color: #93c5fd;
                font-size: 11px;
                font-weight: 800;
            }
            QLabel#SplashInfoValue {
                color: #e2e8f0;
                font-size: 11px;
                font-weight: 650;
            }
            QLabel#SplashFooter {
                color: #94a3b8;
                font-size: 11px;
                font-weight: 700;
            }
            QProgressBar {
                background: rgba(15, 23, 42, 0.92);
                color: #ffffff;
                border: 1px solid rgba(96, 165, 250, 0.18);
                border-radius: 10px;
                text-align: center;
                height: 18px;
                font-weight: 700;
            }
            QProgressBar::chunk {
                background: #2563eb;
                border-radius: 9px;
            }
            """
        )

        self.value = 0
        self._finished = False
        self._stages = [
            (10, "Initializing local data store..."),
            (25, "Loading school profile..."),
            (40, "Preparing academic modules..."),
            (55, "Restoring exam and results services..."),
            (70, "Loading ranking and reporting tools..."),
            (85, "Applying user interface settings..."),
            (95, "Launching SRMS V5..."),
        ]

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_loading)
        self.timer.start(75)

    def _apply_main_window_geometry(self):
        """Match a clean splash size and centered position."""
        available = self.screen().availableGeometry()
        width = min(1280, int(available.width() * 0.90))
        height = min(720, int(available.height() * 0.82))
        self.resize(width, height)
        self.setMinimumSize(1080, 620)

        qr = self.frameGeometry()
        qr.moveCenter(available.center())
        self.move(qr.topLeft())

    def update_loading(self):
        if self._finished:
            return

        self.value = min(self.value + 2, 100)
        self.progress.setValue(self.value)

        for threshold, message in self._stages:
            if self.value >= threshold:
                self.loading.setText(message)

        if self.value >= 100:
            self._finished = True
            self.timer.stop()
            self.progress.setValue(100)
            self.loading.setText("Launching SRMS V5...")
            self.on_finish()
            self.close()
