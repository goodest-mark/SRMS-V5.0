import hashlib
import os
import secrets
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QMessageBox,
    QDialog,
    QFrame
)

from progress_dialog import ProgressDialog
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGraphicsBlurEffect

from db_utils import fetch_one, get_cursor


class PasscodeEntryWidget(QWidget):
    def __init__(self, label_text="Passcode"):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(8)
        self.label = QLabel(label_text)
        self.label.setStyleSheet("color: #cbd5e1; font-weight: 600;")
        self.box_layout = QHBoxLayout()
        self.box_layout.setSpacing(8)
        self.digits = []

        for _ in range(6):
            box = QLineEdit()
            box.setFixedSize(40, 40)
            box.setMaxLength(1)
            box.setAlignment(Qt.AlignCenter)
            box.setEchoMode(QLineEdit.Password)
            box.setStyleSheet(
                "background: rgba(255,255,255,0.08); border: 1px solid #334155; color: white; font-size: 18px; border-radius: 8px;"
            )
            box.setValidator(QLineEdit().validator())
            box.textChanged.connect(self._advance)
            self.digits.append(box)
            self.box_layout.addWidget(box)

        self.layout.addWidget(self.label)
        self.layout.addLayout(self.box_layout)

    def _advance(self):
        for i, box in enumerate(self.digits):
            if box.text() and i < len(self.digits) - 1:
                self.digits[i + 1].setFocus()

    def clear(self):
        for box in self.digits:
            box.clear()

    def value(self):
        return "".join(box.text() for box in self.digits)


class PasscodeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Secure Login")
        self.setFixedSize(520, 420)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setStyleSheet("background-color: rgba(15, 23, 42, 0.95); color: white;")

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        self.background_label = QLabel()
        self.background_label.setFixedSize(480, 160)
        self.background_label.setStyleSheet("border-radius: 18px; background: #111827;")
        self.background_label.setAlignment(Qt.AlignCenter)

        blur = QGraphicsBlurEffect(self)
        blur.setBlurRadius(6)
        self.background_label.setGraphicsEffect(blur)

        self.title = QLabel("Enter Admin Passcode")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-size: 22px; font-weight: bold; color: #e2e8f0;")

        self.subtitle = QLabel("Use the six-digit admin passcode to continue.")
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setStyleSheet("color: #94a3b8;")

        self.passcode_entry = PasscodeEntryWidget("Admin Passcode")

        self.message = QLabel("")
        self.message.setAlignment(Qt.AlignCenter)
        self.message.setStyleSheet("color: #fda4af;")

        self.button = QPushButton("Unlock")
        self.button.setFixedHeight(42)
        self.button.setStyleSheet(
            "background-color: #10b981; color: white; font-weight: bold; border-radius: 10px;"
        )
        self.button.clicked.connect(self.handle_submit)

        self.main_layout.addWidget(self.background_label)
        self.main_layout.addWidget(self.title)
        self.main_layout.addWidget(self.subtitle)
        self.main_layout.addWidget(self.passcode_entry)
        self.main_layout.addWidget(self.message)
        self.main_layout.addWidget(self.button)

        self.load_background()

    def load_background(self):
        profile = get_school_profile_from_db()
        path = profile.get('login_background') if profile else None
        if path and os.path.exists(path):
            pixmap = QPixmap(path).scaled(
                self.background_label.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            self.background_label.setPixmap(pixmap)
        else:
            self.background_label.setText("LOGIN BACKGROUND")
            self.background_label.setStyleSheet(
                "border-radius: 18px; background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #111827, stop:1 #0f172a); color: #94a3b8;"
            )

    def handle_submit(self):
        code = self.passcode_entry.value()
        if len(code) != 6:
            self.message.setText("Passcode must be 6 digits.")
            return

        if check_passcode(code):
            self.accept()
        else:
            self.message.setText("Invalid passcode. Try again.")
            self.passcode_entry.clear()


class SecuritySettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: transparent; color: white;")
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        title = QLabel("SECURITY & PASSCODE SETTINGS")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #38bdf8;")
        layout.addWidget(title)

        card = QFrame()
        card.setStyleSheet(
            "background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 18px;"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(20, 20, 20, 20)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #94a3b8;")

        self.current_widget = PasscodeEntryWidget("Current Admin Passcode")
        self.new_widget = PasscodeEntryWidget("New Admin Passcode")
        self.confirm_widget = PasscodeEntryWidget("Confirm New Passcode")

        self.change_button = QPushButton("CHANGE PASSCODE")
        self.change_button.setFixedHeight(42)
        self.change_button.setStyleSheet(
            "background-color: #2563eb; color: white; font-weight: bold; border-radius: 10px;"
        )
        self.change_button.clicked.connect(self.change_passcode)

        card_layout.addWidget(self.status_label)
        card_layout.addWidget(self.current_widget)
        card_layout.addWidget(self.new_widget)
        card_layout.addWidget(self.confirm_widget)
        card_layout.addWidget(self.change_button)

        layout.addWidget(card)
        layout.addStretch(1)

        self.load_status()

    def load_status(self):
        profile = get_school_profile_from_db()
        school_name = profile.get('school_name', 'SRMS V5') if profile else 'SRMS V5'
        self.status_label.setText(
            f"Admin passcode protects school profile, system settings, and critical actions. Current school: {school_name}."
        )

    def change_passcode(self):
        current_code = self.current_widget.value()
        new_code = self.new_widget.value()
        confirm_code = self.confirm_widget.value()

        if len(current_code) != 6 or len(new_code) != 6 or len(confirm_code) != 6:
            QMessageBox.warning(self, "Validation", "All passcode fields must contain 6 digits.")
            return

        if new_code != confirm_code:
            QMessageBox.warning(self, "Validation", "New passcode does not match confirmation.")
            return

        if not check_passcode(current_code):
            QMessageBox.warning(self, "Validation", "Current passcode is incorrect.")
            self.current_widget.clear()
            return

        update_passcode(new_code)
        self.current_widget.clear()
        self.new_widget.clear()
        self.confirm_widget.clear()
        self.load_status()
        QMessageBox.information(self, "Success", "Admin passcode changed successfully.")


def hash_passcode(value, salt=None):
    """Hash a passcode using PBKDF2-HMAC-SHA256 with a random salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", value.encode("utf-8"), salt.encode("utf-8"), iterations=260000)
    return f"{salt}${dk.hex()}"


def get_security_passcode():
    result = fetch_one("SELECT admin_passcode FROM system_security ORDER BY id DESC LIMIT 1")
    return result[0] if result else None


def check_passcode(value):
    saved = get_security_passcode()
    if not saved:
        return False

    if "$" in saved:
        # New PBKDF2 format: salt$hash
        salt, stored_hash = saved.split("$", 1)
        dk = hashlib.pbkdf2_hmac("sha256", value.encode("utf-8"), salt.encode("utf-8"), iterations=260000)
        return secrets.compare_digest(dk.hex(), stored_hash)

    # Legacy SHA-256 format (no salt separator) — verify then upgrade
    legacy_hash = hashlib.sha256(value.encode("utf-8")).hexdigest()
    if secrets.compare_digest(saved, legacy_hash):
        # Auto-upgrade to PBKDF2 on successful login
        update_passcode(value)
        return True

    return False


def update_passcode(value):
    hashed_value = hash_passcode(value)
    with get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE system_security SET admin_passcode=?, last_changed=CURRENT_TIMESTAMP WHERE id=(SELECT id FROM system_security ORDER BY id DESC LIMIT 1)",
            (hashed_value,)
        )


def authorize_action(parent, action_name="Secure Action"):
    dialog = PasscodeDialog(parent)
    dialog.title.setText(f"Authorize: {action_name}")
    dialog.subtitle.setText("Enter the six-digit admin passcode to continue.")
    return dialog.exec() == QDialog.Accepted


def get_school_profile_from_db():
    keys = ['school_name', 'school_address', 'school_phone', 'school_email', 'school_logo', 'head_teacher', 'academic_master', 'watermark_text', 'login_background', 'dashboard_background']
    row = fetch_one(
        "SELECT school_name, school_address, school_phone, school_email, school_logo, head_teacher, academic_master, watermark_text, login_background, dashboard_background FROM school_profile LIMIT 1"
    )
    if not row:
        return {}
    return {keys[i]: row[i] or '' for i in range(len(keys))}
