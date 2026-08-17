import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QMessageBox, QLabel, QFileDialog, QGroupBox,
    QScrollArea, QFrame, QSizePolicy, QCheckBox
)

from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

from db_utils import fetch_one, get_cursor
from security_settings import authorize_action
from event_bus import EventBus

_ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def _is_safe_image_path(path):
    if not path:
        return False
    real_path = os.path.realpath(path)
    ext = os.path.splitext(real_path)[1].lower()
    return ext in _ALLOWED_IMAGE_EXTENSIONS and os.path.isfile(real_path)


class SchoolProfilePage(QWidget):
    def __init__(self):
        super().__init__()
        self.logo_path = ""
        self.stamp_path = ""
        self.head_teacher_signature_path = ""
        self.head_teacher_signature_enabled = QCheckBox("Enabled")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        container = QWidget()
        container.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.MinimumExpanding
        )
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 8, 10, 8)
        container_layout.setSpacing(14)

        # UI Header
        title = QLabel("SCHOOL REGISTRATION & CONFIGURATION")
        title.setProperty("variant", "accent")
        container_layout.addWidget(title)

        # SECTION 1: Identity
        sec1 = QGroupBox("SECTION 1: SCHOOL IDENTITY")
        form1 = QFormLayout(sec1)
        self.school_name = QLineEdit()
        self.school_motto = QLineEdit()
        form1.addRow("School Name:", self.school_name)
        form1.addRow("Motto:", self.school_motto)

        # SECTION 2: Contact
        sec2 = QGroupBox("SECTION 2: CONTACT INFORMATION")
        form2 = QFormLayout(sec2)
        self.school_address = QLineEdit()
        self.school_phone = QLineEdit()
        self.school_email = QLineEdit()
        self.school_website = QLineEdit()
        form2.addRow("Address:", self.school_address)
        form2.addRow("Phone:", self.school_phone)
        form2.addRow("Email:", self.school_email)
        form2.addRow("Website:", self.school_website)

        # SECTION 3: Administration
        sec3 = QGroupBox("SECTION 3: ADMINISTRATION")
        form3 = QFormLayout(sec3)
        self.head_teacher = QLineEdit()
        self.academic_master = QLineEdit()
        self.discipline_master = QLineEdit()
        form3.addRow("Headmaster / Headmistress:", self.head_teacher)
        form3.addRow("Academic Master / Mistress:", self.academic_master)
        form3.addRow("Discipline Master / Mistress:", self.discipline_master)

        # SECTION 4: BRANDING
        sec4 = QGroupBox("SECTION 4: BRANDING")
        form4 = QFormLayout(sec4)
        self.watermark_text = QLineEdit()
        form4.addRow("Watermark Text:", self.watermark_text)

        self.logo_preview, logo_btn = self._build_image_row("No Logo", "UPLOAD LOGO", self.upload_logo)
        form1.addRow("School Logo:", self._wrap_row(self.logo_preview, logo_btn))

        self.stamp_preview, stamp_btn = self._build_image_row("No Stamp", "UPLOAD STAMP", self.upload_stamp)
        form4.addRow("School Stamp:", self._wrap_row(self.stamp_preview, stamp_btn))

        # SECTION 5: HEADMASTER / HEADMISTRESS SIGNATURE (only)
        sec5 = QGroupBox("SECTION 5: SIGNATURES")
        form5 = QFormLayout(sec5)
        self.head_signature_preview, head_sig_btn, self.head_teacher_signature_enabled, head_row = self._build_signature_row(
            "No Signature", "UPLOAD HEADMASTER / HEADMISTRESS SIGNATURE", self.upload_head_signature, self.head_teacher_signature_enabled
        )
        # Removed Academic, Discipline, Class Master signatures
        # Add a note that other signatures are handled on paper
        note_label = QLabel("Note: Academic Master / Mistress, Discipline Master / Mistress, and Class Master / Mistress signatures are handled physically on paper.")
        note_label.setWordWrap(True)
        note_label.setProperty("variant", "muted")
        form5.addRow("Headmaster / Headmistress:", head_row)
        form5.addRow(note_label)

        container_layout.addWidget(sec1)
        container_layout.addWidget(sec2)
        container_layout.addWidget(sec3)
        container_layout.addWidget(sec4)
        container_layout.addWidget(sec5)

        # ACTIONS
        btns_layout = QHBoxLayout()
        self.save_btn = QPushButton("SAVE PROFILE")
        self.update_btn = QPushButton("UPDATE PROFILE")
        self.reset_btn = QPushButton("RESET FORM")

        self.save_btn.clicked.connect(self.save_profile)
        self.update_btn.clicked.connect(self.save_profile)
        self.reset_btn.clicked.connect(self.reset_form)

        btns_layout.addWidget(self.save_btn)
        btns_layout.addWidget(self.update_btn)
        btns_layout.addWidget(self.reset_btn)

        container_layout.addLayout(btns_layout)

        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        self.load()

    def _build_image_row(self, placeholder, button_text, callback):
        preview = QLabel(placeholder)
        preview.setObjectName("ProfilePreview")
        preview.setFixedSize(120, 120)
        preview.setAlignment(Qt.AlignCenter)
        button = QPushButton(button_text)
        button.clicked.connect(callback)
        return preview, button

    def _build_signature_row(self, placeholder, button_text, callback, checkbox):
        preview, button = self._build_image_row(placeholder, button_text, callback)
        row = QHBoxLayout()
        row.addWidget(preview)
        row.addWidget(button)
        row.addWidget(checkbox)
        row.addStretch()
        checkbox.setChecked(False)
        button.setEnabled(False)
        checkbox.toggled.connect(button.setEnabled)
        return preview, button, checkbox, row

    def _wrap_row(self, preview, button):
        row = QHBoxLayout()
        row.addWidget(preview)
        row.addWidget(button)
        row.addStretch()
        return row

    def upload_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Logo", "", "Images (*.png *.jpg *.jpeg)")
        if file_path and _is_safe_image_path(file_path):
            self.logo_path = file_path
            self.show_preview(self.logo_preview, file_path)

    def upload_stamp(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Stamp", "", "Images (*.png *.jpg *.jpeg)")
        if file_path and _is_safe_image_path(file_path):
            self.stamp_path = file_path
            self.show_preview(self.stamp_preview, file_path)

    def upload_head_signature(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Headmaster / Headmistress Signature", "", "Images (*.png *.jpg *.jpeg)")
        if file_path and _is_safe_image_path(file_path):
            self.head_teacher_signature_path = file_path
            self.show_preview(self.head_signature_preview, file_path)

    def show_preview(self, label, path):
        if path and os.path.exists(path):
            pixmap = QPixmap(path).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label.setPixmap(pixmap)
        else:
            label.clear()
            label.setText("No Image")

    def load(self):
        try:
            row = fetch_one("""
                SELECT school_name, school_motto, school_address, school_phone,
                       school_email, school_website, head_teacher, academic_master,
                       discipline_master, school_logo, school_stamp,
                       head_teacher_signature,
                       watermark_text,
                       head_teacher_signature_enabled
                FROM school_profile LIMIT 1
            """)

            if row:
                self.school_name.setText(row[0] or "")
                self.school_motto.setText(row[1] or "")
                self.school_address.setText(row[2] or "")
                self.school_phone.setText(row[3] or "")
                self.school_email.setText(row[4] or "")
                self.school_website.setText(row[5] or "")
                self.head_teacher.setText(row[6] or "")
                self.academic_master.setText(row[7] or "")
                self.discipline_master.setText(row[8] or "")
                self.logo_path = row[9] or ""
                self.stamp_path = row[10] or ""
                self.head_teacher_signature_path = row[11] or ""
                self.watermark_text.setText(row[12] or "CONFIDENTIAL")
                self.head_teacher_signature_enabled.setChecked(bool(row[13]))

                if self.logo_path: self.show_preview(self.logo_preview, self.logo_path)
                if self.stamp_path: self.show_preview(self.stamp_preview, self.stamp_path)
                if self.head_teacher_signature_enabled.isChecked() and self.head_teacher_signature_path:
                    self.show_preview(self.head_signature_preview, self.head_teacher_signature_path)
        except Exception as e:
            print(f"[ERROR] Failed to load school profile: {e}")
            QMessageBox.warning(self, "Load Error", "Could not load school profile data.")

    def save_profile(self):
        if not authorize_action(self, "School Profile Changes"):
            return

        try:
            with get_cursor(commit=True) as cur:
                cur.execute("DELETE FROM school_profile")
                cur.execute("""
                    INSERT INTO school_profile (
                        school_name, school_motto, school_address, school_phone,
                        school_email, school_website, head_teacher, academic_master,
                        discipline_master, school_logo, school_stamp,
                        head_teacher_signature,
                        watermark_text,
                        head_teacher_signature_enabled
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.school_name.text(),
                    self.school_motto.text(),
                    self.school_address.text(),
                    self.school_phone.text(),
                    self.school_email.text(),
                    self.school_website.text(),
                    self.head_teacher.text(),
                    self.academic_master.text(),
                    self.discipline_master.text(),
                    self.logo_path,
                    self.stamp_path,
                    self.head_teacher_signature_path if self.head_teacher_signature_enabled.isChecked() else "",
                    self.watermark_text.text() or "CONFIDENTIAL",
                    1 if self.head_teacher_signature_enabled.isChecked() else 0,
                ))
                cur.execute(
                    "REPLACE INTO system_settings (setting_key, setting_value) VALUES ('setup_complete', '1')"
                )
            QMessageBox.information(self, "Success", "School Profile Configuration Saved.")
            EventBus.emit("SCHOOL_PROFILE_UPDATED")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred while saving the school profile: {e}")

    def reset_form(self):
        self.school_name.clear()
        self.school_motto.clear()
        self.school_address.clear()
        self.school_phone.clear()
        self.school_email.clear()
        self.school_website.clear()
        self.head_teacher.clear()
        self.academic_master.clear()
        self.discipline_master.clear()
        self.logo_path = ""
        self.stamp_path = ""
        self.head_teacher_signature_path = ""
        self.head_teacher_signature_enabled.setChecked(False)
        self.watermark_text.clear()
        self.logo_preview.clear()
        self.logo_preview.setText("No Logo")
        self.stamp_preview.clear()
        self.stamp_preview.setText("No Stamp")
        self.head_signature_preview.clear()
        self.head_signature_preview.setText("No Signature")
