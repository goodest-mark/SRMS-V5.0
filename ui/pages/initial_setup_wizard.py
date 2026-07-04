import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from db_utils import fetch_one, get_cursor
from event_bus import EventBus


def _is_safe_image_path(path):
    if not path:
        return False
    real_path = os.path.realpath(path)
    ext = os.path.splitext(real_path)[1].lower()
    return ext in {".png", ".jpg", ".jpeg"} and os.path.isfile(real_path)


def needs_initial_setup():
    profile_row = fetch_one(
        "SELECT school_name FROM school_profile LIMIT 1"
    )
    setup_row = fetch_one(
        "SELECT setting_value FROM system_settings WHERE setting_key='setup_complete'"
    )
    has_school_details = bool(profile_row and str(profile_row[0] or "").strip())
    setup_complete = bool(setup_row and setup_row[0] == "1")
    return (not has_school_details) or (not setup_complete)


class _ImagePicker(QWidget):
    def __init__(self, title, button_text):
        super().__init__()
        self.path = ""

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.preview = QLabel("No Image")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setFixedSize(96, 96)
        self.preview.setObjectName("ProfilePreview")

        self.button = QPushButton(button_text)
        self.button.clicked.connect(lambda: self.pick(title))

        layout.addWidget(self.preview)
        layout.addWidget(self.button)
        layout.addStretch(1)

    def pick(self, title):
        path, _ = QFileDialog.getOpenFileName(
            self,
            title,
            "",
            "Images (*.png *.jpg *.jpeg)",
        )
        if path and _is_safe_image_path(path):
            self.path = path
            pixmap = QPixmap(path).scaled(
                self.preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.preview.setPixmap(pixmap)

    def clear(self):
        self.path = ""
        self.preview.clear()
        self.preview.setText("No Image")


class _SignatureSlot(QWidget):
    def __init__(self, title, button_text):
        super().__init__()
        self.enabled = False
        self.picker = _ImagePicker(title, button_text)
        self.toggle = QCheckBox("Enabled")
        self.toggle.toggled.connect(self._on_toggle)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(self.picker, 1)
        layout.addWidget(self.toggle)

    def _on_toggle(self, checked):
        self.enabled = checked
        self.picker.button.setEnabled(checked)
        if not checked:
            self.picker.clear()

    def set_enabled(self, checked):
        self.toggle.blockSignals(True)
        self.toggle.setChecked(checked)
        self.toggle.blockSignals(False)
        self._on_toggle(checked)


class IdentityPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("SetupSection")

        layout = QFormLayout(self)
        self.school_name = QLineEdit()
        self.school_name.setPlaceholderText("School Name")
        self.school_motto = QLineEdit()
        self.school_address = QLineEdit()
        self.school_phone = QLineEdit()
        self.school_email = QLineEdit()
        self.school_website = QLineEdit()

        layout.addRow("School Name*", self.school_name)
        layout.addRow("Motto", self.school_motto)
        layout.addRow("Address", self.school_address)
        layout.addRow("Phone", self.school_phone)
        layout.addRow("Email", self.school_email)
        layout.addRow("Website", self.school_website)


class StaffPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("SetupSection")

        layout = QFormLayout(self)
        self.head_teacher = QLineEdit()
        self.academic_master = QLineEdit()
        self.discipline_master = QLineEdit()
        self.class_master = QLineEdit()
        self.class_master.setPlaceholderText("Optional. Leave blank if class masters vary by class.")

        layout.addRow("Head Teacher / Head Mistress", self.head_teacher)
        layout.addRow("Academic Master / Mistress", self.academic_master)
        layout.addRow("Discipline Master / Mistress", self.discipline_master)
        layout.addRow("Class Master / Mistress", self.class_master)


class BrandingPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("SetupSection")

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self.logo_picker = _ImagePicker("Select School Logo", "Upload Logo")
        self.stamp_picker = _ImagePicker("Select School Stamp", "Upload Stamp")

        layout.addWidget(QLabel("School Logo"))
        layout.addWidget(self.logo_picker)
        layout.addWidget(QLabel("School Stamp"))
        layout.addWidget(self.stamp_picker)
        layout.addStretch(1)


class SignaturesPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("SetupSection")

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        self.head = _SignatureSlot("Select Head Teacher Signature", "Upload Signature")
        self.academic = _SignatureSlot("Select Academic Master Signature", "Upload Signature")
        self.discipline = _SignatureSlot("Select Discipline Master Signature", "Upload Signature")

        for title, widget in [
            ("Head Teacher / Head Mistress", self.head),
            ("Academic Master / Mistress", self.academic),
            ("Discipline Master / Mistress", self.discipline),
        ]:
            row = QFrame()
            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(6)
            label = QLabel(title)
            label.setProperty("variant", "accent")
            row_layout.addWidget(label)
            row_layout.addWidget(widget)
            layout.addWidget(row)

        class_note = QLabel(
            "Class Master / Mistress is signed physically on the paper report."
        )
        class_note.setWordWrap(True)
        class_note.setProperty("variant", "muted")
        layout.addWidget(class_note)

        layout.addStretch(1)


class DefaultsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("SetupSection")

        layout = QFormLayout(self)

        self.default_level_selector = QComboBox()
        self.default_level_selector.addItems(["O_LEVEL", "A_LEVEL"])

        self.o_level_counted = QSpinBox()
        self.o_level_counted.setRange(1, 20)
        self.o_level_counted.setValue(7)

        self.a_level_principal = QSpinBox()
        self.a_level_principal.setRange(1, 10)
        self.a_level_principal.setValue(3)

        self.show_logo = QCheckBox("Show logo on reports")
        self.show_logo.setChecked(True)
        self.show_watermark = QCheckBox("Show watermark on reports")
        self.show_watermark.setChecked(True)

        layout.addRow("Default Level", self.default_level_selector)
        layout.addRow("O-Level Counted Subjects", self.o_level_counted)
        layout.addRow("A-Level Principal Subjects", self.a_level_principal)
        layout.addRow(self.show_logo)
        layout.addRow(self.show_watermark)


class InitialSetupWizard(QWidget):
    completed = Signal()
    skipped = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("First-Time Setup")
        self.setObjectName("SetupRoot")

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        header = QFrame()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(18, 16, 18, 16)
        header_layout.setSpacing(4)
        title = QLabel("First-Time Setup")
        title.setProperty("variant", "accent")
        subtitle = QLabel("Configure the school profile, branding, and reporting defaults before using the app.")
        subtitle.setWordWrap(True)
        subtitle.setProperty("variant", "muted")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        body = QHBoxLayout()
        body.setSpacing(16)

        self.step_list = QListWidget()
        self.step_list.addItems([
            "School Identity",
            "School Staff",
            "Branding",
            "Signatures",
            "Defaults",
        ])
        self.step_list.setFixedWidth(180)
        self.step_list.currentRowChanged.connect(self._on_step_changed)

        self.stack = QStackedWidget()
        self.identity_page = IdentityPage()
        self.staff_page = StaffPage()
        self.branding_page = BrandingPage()
        self.signatures_page = SignaturesPage()
        self.defaults_page = DefaultsPage()

        for page in (
            self.identity_page,
            self.staff_page,
            self.branding_page,
            self.signatures_page,
            self.defaults_page,
        ):
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setWidget(page)
            self.stack.addWidget(scroll)

        body.addWidget(self.step_list)
        body.addWidget(self.stack, 1)

        footer = QFrame()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(10)

        self.skip_btn = QPushButton("Skip Setup")
        self.back_btn = QPushButton("Back")
        self.next_btn = QPushButton("Next")
        self.finish_btn = QPushButton("Finish")

        self.skip_btn.clicked.connect(self.skip_setup)
        self.back_btn.clicked.connect(self.previous_step)
        self.next_btn.clicked.connect(self.next_step)
        self.finish_btn.clicked.connect(self.finish_setup)

        footer_layout.addWidget(self.skip_btn)
        footer_layout.addStretch(1)
        footer_layout.addWidget(self.back_btn)
        footer_layout.addWidget(self.next_btn)
        footer_layout.addWidget(self.finish_btn)

        root.addWidget(header)
        root.addLayout(body, 1)
        root.addWidget(footer)

        self.step_list.setCurrentRow(0)
        self._refresh_navigation()

    def _on_step_changed(self, index):
        if index < 0:
            return
        self.stack.setCurrentIndex(index)
        self._refresh_navigation()

    def _refresh_navigation(self):
        index = self.step_list.currentRow()
        self.back_btn.setEnabled(index > 0)
        self.next_btn.setEnabled(index < self.stack.count() - 1)
        self.finish_btn.setEnabled(index == self.stack.count() - 1)

    def next_step(self):
        index = self.step_list.currentRow()
        if index < self.stack.count() - 1:
            self.step_list.setCurrentRow(index + 1)

    def previous_step(self):
        index = self.step_list.currentRow()
        if index > 0:
            self.step_list.setCurrentRow(index - 1)

    def skip_setup(self):
        with get_cursor(commit=True) as cur:
            cur.execute(
                "REPLACE INTO system_settings (setting_key, setting_value) VALUES ('setup_complete', '1')"
            )
        EventBus.emit("SCHOOL_PROFILE_UPDATED")
        self.skipped.emit()
        self.completed.emit()

    def finish_setup(self):
        if self._save_setup():
            self.completed.emit()

    def _save_setup(self):
        school_name = self.identity_page.school_name.text().strip()
        if not school_name:
            QMessageBox.warning(
                self,
                "Missing Data",
                "School name is required to complete setup.",
            )
            return False

        try:
            with get_cursor(commit=True) as cur:
                cur.execute("DELETE FROM school_profile")
                cur.execute(
                    """
                    INSERT INTO school_profile (
                        school_name, school_motto, school_address, school_phone,
                        school_email, school_website, head_teacher, academic_master,
                        discipline_master, class_master, school_logo, school_stamp,
                        head_teacher_signature, academic_master_signature,
                        discipline_master_signature, class_master_signature,
                        login_background, dashboard_background, watermark_text,
                        head_teacher_signature_enabled, academic_master_signature_enabled,
                        discipline_master_signature_enabled, class_master_signature_enabled
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        school_name,
                        self.identity_page.school_motto.text().strip(),
                        self.identity_page.school_address.text().strip(),
                        self.identity_page.school_phone.text().strip(),
                        self.identity_page.school_email.text().strip(),
                        self.identity_page.school_website.text().strip(),
                        self.staff_page.head_teacher.text().strip(),
                        self.staff_page.academic_master.text().strip(),
                        self.staff_page.discipline_master.text().strip(),
                        self.staff_page.class_master.text().strip(),
                        self.branding_page.logo_picker.path,
                        self.branding_page.stamp_picker.path,
                        self.signatures_page.head.picker.path if self.signatures_page.head.enabled else "",
                        self.signatures_page.academic.picker.path if self.signatures_page.academic.enabled else "",
                        self.signatures_page.discipline.picker.path if self.signatures_page.discipline.enabled else "",
                        "",
                        "",
                        "",
                        "CONFIDENTIAL",
                        1 if self.signatures_page.head.enabled else 0,
                        1 if self.signatures_page.academic.enabled else 0,
                        1 if self.signatures_page.discipline.enabled else 0,
                        0,
                    ),
                )

                cur.executemany(
                    "REPLACE INTO system_settings (setting_key, setting_value) VALUES (?, ?)",
                    [
                        ("default_level", self.defaults_page.default_level_selector.currentText()),
                        ("o_level_counted", str(self.defaults_page.o_level_counted.value())),
                        ("a_level_principal", str(self.defaults_page.a_level_principal.value())),
                        ("show_logo", "1" if self.defaults_page.show_logo.isChecked() else "0"),
                        ("show_watermark", "1" if self.defaults_page.show_watermark.isChecked() else "0"),
                        ("setup_complete", "1"),
                    ],
                )

            EventBus.emit("SCHOOL_PROFILE_UPDATED")
            EventBus.emit("SETTINGS_UPDATED")
            return True
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Setup Failed",
                f"Could not save setup data:\n{exc}",
            )
            return False
