from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
)

from progress_dialog import ProgressDialog


class AcademicsPage(QWidget):

    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(False)
        self.tabs.setUsesScrollButtons(False)

        root.addWidget(self.tabs)

        self._pages = {}
        def create_subjects_page():
            from subjects_page import SubjectsPage
            return SubjectsPage()

        def create_enrollment_page():
            from enrollment_page import EnrollmentPage
            return EnrollmentPage()

        def create_years_page():
            from academic_years import AcademicYearsPage
            return AcademicYearsPage()

        def create_terms_page():
            from terms_page import TermsPage
            return TermsPage()

        self._page_factories = {
            "Subjects": create_subjects_page,
            "Enrollment": create_enrollment_page,
            "Academic Years": create_years_page,
            "Terms": create_terms_page
        }

        # We'll add placeholder widgets and swap them on tab change
        for name in ["Subjects", "Enrollment", "Academic Years", "Terms"]:
            self.tabs.addTab(QWidget(), name)

        self.tabs.currentChanged.connect(self._on_tab_changed)
        self._on_tab_changed(0)

    def _on_tab_changed(self, index):
        if index < 0:
            return
        name = self.tabs.tabText(index)
        if not name or name not in self._page_factories:
            return

        if name not in self._pages:
            self._pages[name] = self._page_factories[name]()
            # Replace the placeholder widget
            self.tabs.blockSignals(True)
            old_widget = self.tabs.widget(index)
            self.tabs.removeTab(index)
            self.tabs.insertTab(index, self._pages[name], name)
            self.tabs.setCurrentIndex(index)
            self.tabs.blockSignals(False)
            
            # Cleanup old widget
            if old_widget:
                old_widget.deleteLater()
        
        self.load()

    def load(self):
        page = self.tabs.currentWidget()
        if page is None:
            return

        for method_name in (
            "refresh_all",
            "load_data",
            "load",
            "load_years",
        ):
            method = getattr(page, method_name, None)
            if callable(method):
                try:
                    method()
                except Exception as e:
                    print(f"[ERROR] Failed to call {method_name}: {e}")
                break
