from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFrame, QStackedWidget, QScrollArea, QSizePolicy,
)

class AcademicsPage(QWidget):

    def __init__(self):
        super().__init__()

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        scroll.setWidget(content)

        root = QVBoxLayout(content)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        # ─── Navigation container (theme‑aware) ──────────────────────
        nav_container = QFrame()
        nav_container.setObjectName("NavContainer")
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(4, 4, 4, 4)
        nav_layout.setSpacing(4)

        self.btn_subjects = QPushButton("Subjects")
        self.btn_enrollment = QPushButton("Enrollment")
        self.btn_academic_years = QPushButton("Academic Years")
        self.btn_terms = QPushButton("Terms")

        self.nav_buttons = [
            self.btn_subjects,
            self.btn_enrollment,
            self.btn_academic_years,
            self.btn_terms,
        ]

        for btn in self.nav_buttons:
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(38)
            btn.setMinimumWidth(110)
            btn.setProperty("variant", "default")
            nav_layout.addWidget(btn)

        root.addWidget(nav_container)

        # ─── Stacked widget (lazy‑load) ──────────────────────────────
        self.stack = QStackedWidget()
        root.addWidget(self.stack)

        self._pages = {}
        self._page_factories = {
            "Subjects": lambda: __import__("subjects_page", fromlist=["SubjectsPage"]).SubjectsPage(),
            "Enrollment": lambda: __import__("enrollment_page", fromlist=["EnrollmentPage"]).EnrollmentPage(),
            "Academic Years": lambda: __import__("academic_years", fromlist=["AcademicYearsPage"]).AcademicYearsPage(),
            "Terms": lambda: __import__("terms_page", fromlist=["TermsPage"]).TermsPage(),
        }

        # Placeholders
        for name in self._page_factories:
            placeholder = QWidget()
            placeholder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.stack.addWidget(placeholder)

        # Connect buttons
        self.btn_subjects.clicked.connect(lambda: self.switch_page(0))
        self.btn_enrollment.clicked.connect(lambda: self.switch_page(1))
        self.btn_academic_years.clicked.connect(lambda: self.switch_page(2))
        self.btn_terms.clicked.connect(lambda: self.switch_page(3))

        # ─── Initial state ────────────────────────────────────────────
        self.switch_page(0)

        # Final layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    # ─── Page switching ──────────────────────────────────────────────
    def switch_page(self, index):
        names = list(self._page_factories.keys())
        if index >= len(names):
            return
        name = names[index]

        # Update button states
        for i, btn in enumerate(self.nav_buttons):
            variant = "accent" if i == index else "default"
            btn.setProperty("variant", variant)
            btn.setChecked(i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Lazy load
        if name not in self._pages:
            page = self._page_factories[name]()
            self._pages[name] = page
            self.stack.blockSignals(True)
            old = self.stack.widget(index)
            self.stack.removeWidget(old)
            old.deleteLater()
            self.stack.insertWidget(index, page)
            self.stack.blockSignals(False)

        self.stack.setCurrentIndex(index)
        self.load_current_page()

    def load_current_page(self):
        page = self.stack.currentWidget()
        if page is None:
            return
        for method_name in ("refresh_all", "load_data", "load", "load_years"):
            method = getattr(page, method_name, None)
            if callable(method):
                try:
                    method()
                except Exception as e:
                    print(f"[ERROR] Failed to call {method_name}: {e}")
                break

    def load(self):
        self.load_current_page()