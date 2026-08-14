from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFrame, QStackedWidget, QSizePolicy,
)

from school_profile import SchoolProfilePage
from requirements_page import RequirementsPage
from academic_configuration_page import AcademicConfigurationPage
from promotion_page import PromotionPage


class SchoolCenter(QWidget):

    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        # ─── Navigation container (theme‑aware) ──────────────────────
        nav_container = QFrame()
        nav_container.setObjectName("NavContainer")
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(4, 4, 4, 4)
        nav_layout.setSpacing(4)

        self.btn_profile = QPushButton("School Profile")
        self.btn_requirements = QPushButton("Requirements")
        self.btn_academic_config = QPushButton("Academic Config")
        self.btn_promotion = QPushButton("Promotion")

        self.nav_buttons = [
            self.btn_profile,
            self.btn_requirements,
            self.btn_academic_config,
            self.btn_promotion,
        ]

        for btn in self.nav_buttons:
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(38)
            btn.setMinimumWidth(130)
            btn.setProperty("variant", "default")
            nav_layout.addWidget(btn)

        root.addWidget(nav_container)

        # ─── Stacked widget ──────────────────────────────────────────
        self.stack = QStackedWidget()

        self.profile_page = SchoolProfilePage()
        self.requirements_page = RequirementsPage()
        self.academic_config_page = AcademicConfigurationPage()
        self.promotion_page = PromotionPage()

        self.stack.addWidget(self.profile_page)
        self.stack.addWidget(self.requirements_page)
        self.stack.addWidget(self.academic_config_page)
        self.stack.addWidget(self.promotion_page)

        root.addWidget(self.stack, 1)

        # ─── Connect buttons ─────────────────────────────────────────
        self.btn_profile.clicked.connect(lambda: self.switch_page(0))
        self.btn_requirements.clicked.connect(lambda: self.switch_page(1))
        self.btn_academic_config.clicked.connect(lambda: self.switch_page(2))
        self.btn_promotion.clicked.connect(lambda: self.switch_page(3))

        # ─── Initial state ────────────────────────────────────────────
        self.switch_page(0)

    def switch_page(self, index):
        # Update button states
        for i, btn in enumerate(self.nav_buttons):
            variant = "accent" if i == index else "default"
            btn.setProperty("variant", variant)
            btn.setChecked(i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self.stack.setCurrentIndex(index)
        self.load()

    def load(self):
        page = self.stack.currentWidget()
        if page is None:
            return
        for method_name in ("refresh_all", "load_data", "load"):
            method = getattr(page, method_name, None)
            if callable(method):
                try:
                    method()
                except Exception as e:
                    print(f"[ERROR] Failed to call {method_name}: {e}")
                break

    # ─── Convenience methods for MainWindow ──────────────────────────
    def open_profile(self):
        self.switch_page(0)

    def open_requirements(self):
        self.switch_page(1)

    def open_academic_config(self, tab_index=0):
        self.switch_page(2)
        try:
            self.academic_config_page.tabs.setCurrentIndex(tab_index)
        except Exception:
            pass

    def open_promotion(self):
        self.switch_page(3)