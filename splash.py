from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QProgressBar,
    QFrame,
    QHBoxLayout
)

from progress_dialog import ProgressDialog

from PySide6.QtCore import (
    Qt,
    QTimer
)

from progress_dialog import ProgressDialog


class SplashScreen(QWidget):

    def __init__(self, on_finish):
        super().__init__()

        self.on_finish = on_finish

        self.setWindowTitle("SRMS V5")
        self._apply_main_window_geometry()

        self.setStyleSheet("""
        QWidget{
            background:qlineargradient(
                x1:0,y1:0,x2:1,y2:1,
                stop:0 #020617,
                stop:0.5 #081225,
                stop:1 #0f172a
            );
        }

        QLabel{
            background:transparent;
            color:white;
        }

        QFrame#centerCard{
            background:rgba(15,23,42,0.96);
            border:1px solid rgba(255,255,255,0.08);
            border-radius:28px;
        }

        QProgressBar{
            border:none;
            border-radius:10px;
            background:#0b1220;
            min-height:18px;
            max-height:18px;
        }

        QProgressBar::chunk{
            border-radius:10px;
            background:qlineargradient(
                x1:0,y1:0,x2:1,y2:0,
                stop:0 #2563eb,
                stop:1 #60a5fa
            );
        }
        """)

        root = QVBoxLayout(self)
        root.addStretch()

        # =====================================
        # CENTER CARD
        # =====================================

        card_container = QHBoxLayout()

        card_container.addStretch()

        card = QFrame()
        card.setObjectName("centerCard")
        card.setMaximumWidth(900)
        card.setMinimumWidth(620)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(60, 50, 60, 50)

        # =====================================
        # PRODUCT NAME
        # =====================================

        product = QLabel("SRMS")
        product.setAlignment(Qt.AlignCenter)

        product.setStyleSheet("""
            font-size:120px;
            font-weight:900;
            color:white;
            letter-spacing:8px;
        """)

        # =====================================
        # VERSION
        # =====================================

        version = QLabel("BUILD VERSION 5.0")
        version.setAlignment(Qt.AlignCenter)

        version.setStyleSheet("""
            color:#60a5fa;
            font-size:18px;
            font-weight:700;
            letter-spacing:2px;
        """)

        # =====================================
        # SYSTEM NAME
        # =====================================

        system_name = QLabel(
            "School Records Management System"
        )

        system_name.setAlignment(Qt.AlignCenter)

        system_name.setStyleSheet("""
            font-size:28px;
            font-weight:700;
            color:white;
        """)

        # =====================================
        # TAGLINE
        # =====================================

        tagline = QLabel(
            "Smart Academic Records Management Platform"
        )

        tagline.setAlignment(Qt.AlignCenter)

        tagline.setStyleSheet("""
            color:#93c5fd;
            font-size:18px;
            font-weight:600;
        """)

        # =====================================
        # DESCRIPTION
        # =====================================

        description = QLabel(
            "Student Management • Results Processing\n"
            "Report Books • Ranking • Promotion System\n"
            "Academic Analytics • School Administration"
        )

        description.setAlignment(Qt.AlignCenter)

        description.setStyleSheet("""
            color:#cbd5e1;
            font-size:14px;
            line-height:1.6;
        """)

        # =====================================
        # LOADING LABEL
        # =====================================

        self.loading = QLabel(
            "Loading Database Engine..."
        )

        self.loading.setAlignment(Qt.AlignCenter)

        self.loading.setStyleSheet("""
            color:white;
            font-size:15px;
            font-weight:600;
        """)

        # =====================================
        # PROGRESS
        # =====================================

        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)

        # =====================================
        # FOOTER
        # =====================================

        footer = QLabel(
            "Developed By Mark Deals • SRMS V5.0"
        )

        footer.setAlignment(Qt.AlignCenter)

        footer.setStyleSheet("""
            color:#60a5fa;
            font-size:12px;
            font-weight:bold;
            letter-spacing:1px;
        """)

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

        self.timer = QTimer()
        self.timer.timeout.connect(
            self.update_loading
        )

        # ~5 seconds
        self.timer.start(50)


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

        self.value += 1

        self.progress.setValue(self.value)

        if self.value == 10:
            self.loading.setText(
                "Loading Student Records..."
            )

        elif self.value == 25:
            self.loading.setText(
                "Loading Academic Modules..."
            )

        elif self.value == 40:
            self.loading.setText(
                "Loading Examination Center..."
            )

        elif self.value == 55:
            self.loading.setText(
                "Loading Ranking Engine..."
            )

        elif self.value == 70:
            self.loading.setText(
                "Loading Report Generator..."
            )

        elif self.value == 85:
            self.loading.setText(
                "Loading Dashboard Components..."
            )

        elif self.value == 95:
            self.loading.setText(
                "Launching SRMS V5..."
            )

        elif self.value >= 100:

            self.timer.stop()

            self.on_finish()

            self.close()