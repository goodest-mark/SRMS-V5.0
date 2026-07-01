from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QProgressBar,
    QFrame,
    QHBoxLayout
)

from PySide6.QtCore import (
    Qt,
    QTimer
)


class SplashScreen(QWidget):

    def __init__(self, on_finish):
        super().__init__()

        self.on_finish = on_finish

        self.setWindowTitle("SRMS V5")
        self._apply_main_window_geometry()

        root = QVBoxLayout(self)
        root.addStretch()

        # =====================================
        # CENTER CARD
        # =====================================

        card_container = QHBoxLayout()

        card_container.addStretch()

        card = QFrame()
        card.setObjectName("centerCard")
        card.setObjectName("SplashCard")
        card.setMaximumWidth(900)
        card.setMinimumWidth(620)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(60, 50, 60, 50)

        # =====================================
        # PRODUCT NAME
        # =====================================

        product = QLabel("SRMS")
        product.setAlignment(Qt.AlignCenter)
        product.setProperty("variant", "accent")

        # =====================================
        # VERSION
        # =====================================

        version = QLabel("BUILD VERSION 5.0")
        version.setAlignment(Qt.AlignCenter)
        version.setProperty("variant", "accent")

        # =====================================
        # SYSTEM NAME
        # =====================================

        system_name = QLabel(
            "School Records Management System"
        )

        system_name.setAlignment(Qt.AlignCenter)
        system_name.setProperty("variant", "accent")

        # =====================================
        # TAGLINE
        # =====================================

        tagline = QLabel(
            "Smart Academic Records Management Platform"
        )

        tagline.setAlignment(Qt.AlignCenter)
        tagline.setProperty("variant", "muted")

        # =====================================
        # DESCRIPTION
        # =====================================

        description = QLabel(
            "Student Management • Results Processing\n"
            "Report Books • Ranking • Promotion System\n"
            "Academic Analytics • School Administration"
        )

        description.setAlignment(Qt.AlignCenter)
        description.setProperty("variant", "muted")

        # =====================================
        # LOADING LABEL
        # =====================================

        self.loading = QLabel(
            "Loading Database Engine..."
        )

        self.loading.setAlignment(Qt.AlignCenter)
        self.loading.setProperty("variant", "accent")

        # =====================================
        # PROGRESS
        # =====================================

        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p%")

        # =====================================
        # FOOTER
        # =====================================

        footer = QLabel(
            "Developed By Mark Deals • SRMS V5.0"
        )

        footer.setAlignment(Qt.AlignCenter)
        footer.setProperty("variant", "accent")

        # =====================================
        # BUILD CARD
        # =====================================

        card_layout.addWidget(product)
        card_layout.addWidget(version)

        card_layout.addSpacing(10)

        card_layout.addWidget(system_name)

        card_layout.addSpacing(10)

        card_layout.addWidget(tagline)

        card_layout.addSpacing(15)

        card_layout.addWidget(description)

        card_layout.addSpacing(30)

        card_layout.addWidget(self.loading)

        card_layout.addSpacing(10)

        card_layout.addWidget(self.progress)

        card_layout.addSpacing(25)

        card_layout.addWidget(footer)

        card_container.addWidget(card)
        card_container.addStretch()

        root.addLayout(card_container)

        root.addStretch()

        # =====================================
        # LOADING ENGINE
        # =====================================

        self.value = 0
        self._finished = False
        self._stages = [
            (10, "Loading database engine..."),
            (25, "Loading student records..."),
            (40, "Loading academic modules..."),
            (55, "Loading examination center..."),
            (70, "Loading ranking engine..."),
            (85, "Loading reports and exports..."),
            (95, "Launching SRMS V5..."),
        ]

        self.timer = QTimer()
        self.timer.timeout.connect(
            self.update_loading
        )

        # Slightly longer splash to let startup work settle.
        self.timer.start(75)


    def _apply_main_window_geometry(self):
        """Match the main window's startup size and centered position."""
        available = self.screen().availableGeometry()
        self.resize(
            int(available.width() * 0.95),
            int(available.height() * 0.95)
        )
        self.setMinimumSize(1100, 650)

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
