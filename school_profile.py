import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QMessageBox, QLabel, QFileDialog, QGroupBox,
    QScrollArea, QFrame
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

from db_utils import fetch_one, get_cursor
from security_settings import authorize_action

_ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def _is_safe_image_path(path):
    """Validate that the file path points to a real image file (no path traversal)."""
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
        self.login_bg_path = ""
        self.dashboard_bg_path = ""

        layout = QVBoxLayout(self)
        
        # UI Header
        title = QLabel("SCHOOL REGISTRATION & CONFIGURATION")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #3b82f6; margin-bottom: 10px;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        container_layout = QVBoxLayout(container)

        # Styling for Groups
        group_style = "QGroupBox { font-weight: bold; color: #60a5fa; border: 1px solid #334155; border-radius: 8px; margin-top: 15px; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }"

        # SECTION 1: Identity
        sec1 = QGroupBox("SECTION 1: SCHOOL IDENTITY")
        sec1.setStyleSheet(group_style)
        form1 = QFormLayout(sec1)
        self.school_name = QLineEdit()
        self.school_motto = QLineEdit()
        form1.addRow("School Name:", self.school_name)
        form1.addRow("Motto:", self.school_motto)
        
        logo_layout = QHBoxLayout()
        self.logo_preview = QLabel("No Logo")
        self.logo_preview.setFixedSize(120, 120)
        self.logo_preview.setStyleSheet("border: 2px dashed #334155; background: #111827; color: #4b5563;")
        self.logo_preview.setAlignment(Qt.AlignCenter)
        btn_logo = QPushButton("UPLOAD LOGO")
        btn_logo.clicked.connect(self.upload_logo)
        logo_layout.addWidget(self.logo_preview)
        logo_layout.addWidget(btn_logo)
        logo_layout.addStretch()
        form1.addRow("School Logo:", logo_layout)

        # SECTION 2: Contact
        sec2 = QGroupBox("SECTION 2: CONTACT INFORMATION")
        sec2.setStyleSheet(group_style)
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
        sec3.setStyleSheet(group_style)
        form3 = QFormLayout(sec3)
        self.head_teacher = QLineEdit()
        self.academic_master = QLineEdit()
        form3.addRow("Head Teacher:", self.head_teacher)
        form3.addRow("Academic Master:", self.academic_master)
        
        stamp_layout = QHBoxLayout()
        self.stamp_preview = QLabel("No Stamp")
        self.stamp_preview.setFixedSize(120, 120)
        self.stamp_preview.setStyleSheet("border: 2px dashed #334155; background: #111827; color: #4b5563;")
        self.stamp_preview.setAlignment(Qt.AlignCenter)
        btn_stamp = QPushButton("UPLOAD STAMP")
        btn_stamp.clicked.connect(self.upload_stamp)
        stamp_layout.addWidget(self.stamp_preview)
        stamp_layout.addWidget(btn_stamp)
        stamp_layout.addStretch()
        form3.addRow("School Stamp:", stamp_layout)

        # SECTION 4: BRANDING & BACKGROUNDS
        sec4 = QGroupBox("SECTION 4: BRANDING & BACKGROUNDS")
        sec4.setStyleSheet(group_style)
        form4 = QFormLayout(sec4)
        self.watermark_text = QLineEdit()
        form4.addRow("Watermark Text:", self.watermark_text)

        login_bg_layout = QHBoxLayout()
        self.login_bg_preview = QLabel("No Login Background")
        self.login_bg_preview.setFixedSize(120, 120)
        self.login_bg_preview.setStyleSheet("border: 2px dashed #334155; background: #111827; color: #4b5563;")
        self.login_bg_preview.setAlignment(Qt.AlignCenter)
        btn_login_bg = QPushButton("UPLOAD LOGIN BG")
        btn_login_bg.clicked.connect(self.upload_login_background)
        login_bg_layout.addWidget(self.login_bg_preview)
        login_bg_layout.addWidget(btn_login_bg)
        login_bg_layout.addStretch()
        form4.addRow("Login Background:", login_bg_layout)

        dashboard_bg_layout = QHBoxLayout()
        self.dashboard_bg_preview = QLabel("No Dashboard Background")
        self.dashboard_bg_preview.setFixedSize(120, 120)
        self.dashboard_bg_preview.setStyleSheet("border: 2px dashed #334155; background: #111827; color: #4b5563;")
        self.dashboard_bg_preview.setAlignment(Qt.AlignCenter)
        btn_dashboard_bg = QPushButton("UPLOAD DASHBOARD BG")
        btn_dashboard_bg.clicked.connect(self.upload_dashboard_background)
        dashboard_bg_layout.addWidget(self.dashboard_bg_preview)
        dashboard_bg_layout.addWidget(btn_dashboard_bg)
        dashboard_bg_layout.addStretch()
        form4.addRow("Dashboard Background:", dashboard_bg_layout)

        container_layout.addWidget(sec1)
        container_layout.addWidget(sec2)
        container_layout.addWidget(sec3)
        container_layout.addWidget(sec4)
        
        # ACTIONS
        btns_layout = QHBoxLayout()
        self.save_btn = QPushButton("SAVE PROFILE")
        self.update_btn = QPushButton("UPDATE PROFILE")
        self.reset_btn = QPushButton("RESET FORM")
        
        self.save_btn.setStyleSheet("background-color: #10b981;")
        self.update_btn.setStyleSheet("background-color: #3b82f6;")
        self.reset_btn.setStyleSheet("background-color: #ef4444;")
        
        self.save_btn.clicked.connect(self.save_profile)
        self.update_btn.clicked.connect(self.save_profile)
        self.reset_btn.clicked.connect(self.reset_form)
        
        btns_layout.addWidget(self.save_btn)
        btns_layout.addWidget(self.update_btn)
        btns_layout.addWidget(self.reset_btn)
        
        container_layout.addLayout(btns_layout)
        container_layout.addStretch()
        
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        self.load()

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

    def upload_login_background(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Login Background", "", "Images (*.png *.jpg *.jpeg)")
        if file_path and _is_safe_image_path(file_path):
            self.login_bg_path = file_path
            self.show_preview(self.login_bg_preview, file_path)

    def upload_dashboard_background(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Dashboard Background", "", "Images (*.png *.jpg *.jpeg)")
        if file_path and _is_safe_image_path(file_path):
            self.dashboard_bg_path = file_path
            self.show_preview(self.dashboard_bg_preview, file_path)

    def show_preview(self, label, path):
        if path and os.path.exists(path):
            pixmap = QPixmap(path).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label.setPixmap(pixmap)
        else:
            label.setText("No Image")

    def load(self):
        try:
            row = fetch_one("""
                SELECT school_name, school_motto, school_address, school_phone,
                       school_email, school_website, head_teacher, academic_master,
                       school_logo, school_stamp, login_background, dashboard_background,
                       watermark_text
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
                self.logo_path = row[8] or ""
                self.stamp_path = row[9] or ""
                self.login_bg_path = row[10] or ""
                self.dashboard_bg_path = row[11] or ""
                self.watermark_text.setText(row[12] or "CONFIDENTIAL")
                
                if self.logo_path: self.show_preview(self.logo_preview, self.logo_path)
                if self.stamp_path: self.show_preview(self.stamp_preview, self.stamp_path)
                if self.login_bg_path: self.show_preview(self.login_bg_preview, self.login_bg_path)
                if self.dashboard_bg_path: self.show_preview(self.dashboard_bg_preview, self.dashboard_bg_path)
        except Exception as e:
            print(f"[ERROR] Failed to load school profile: {e}")
            QMessageBox.warning(self, "Load Error", f"Could not load school profile data: {e}")

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
                        school_logo, school_stamp, login_background, dashboard_background,
                        watermark_text
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.school_name.text(), self.school_motto.text(), self.school_address.text(),
                    self.school_phone.text(), self.school_email.text(), self.school_website.text(),
                    self.head_teacher.text(), self.academic_master.text(),
                    self.logo_path, self.stamp_path, self.login_bg_path,
                    self.dashboard_bg_path, self.watermark_text.text() or "CONFIDENTIAL"
                ))
            QMessageBox.information(self, "Success", "School Profile Configuration Saved.")
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
        self.logo_path = ""
        self.stamp_path = ""
        self.login_bg_path = ""
        self.dashboard_bg_path = ""
        self.watermark_text.clear()
        self.logo_preview.setText("No Logo")
        self.stamp_preview.setText("No Stamp")
        self.login_bg_preview.setText("No Login Background")
        self.dashboard_bg_preview.setText("No Dashboard Background")