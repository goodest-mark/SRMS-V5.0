import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsBlurEffect,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from db_utils import fetch_one


def get_school_profile_from_db():
    keys = [
        "school_name",
        "school_address",
        "school_phone",
        "school_email",
        "school_logo",
        "head_teacher",
        "academic_master",
        "watermark_text",
        "login_background",
        "dashboard_background",
    ]
    row = fetch_one(
        "SELECT school_name, school_address, school_phone, school_email, school_logo, head_teacher, academic_master, watermark_text, login_background, dashboard_background FROM school_profile LIMIT 1"
    )
    if not row:
        return {}
    return {keys[i]: row[i] or "" for i in range(len(keys))}


class SecuritySettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("SECURITY CONFIRMATION")
        title.setProperty("variant", "accent")
        layout.addWidget(title)

        card = QFrame()
        card.setObjectName("SecurityCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(12)

        self.info = QLabel(
            "Protected actions use a simple Yes / No confirmation."
        )
        self.info.setWordWrap(True)
        self.info.setProperty("variant", "muted")

        self.test_button = QPushButton("TEST CONFIRMATION")
        self.test_button.setFixedHeight(42)
        self.test_button.clicked.connect(self.test_prompt)

        card_layout.addWidget(self.info)
        card_layout.addWidget(self.test_button)
        layout.addWidget(card)
        layout.addStretch(1)

    def test_prompt(self):
        reply = QMessageBox.question(
            self,
            "Confirm",
            "Use Yes to allow the protected action.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "Confirmed", "Yes selected.")
        else:
            QMessageBox.information(self, "Cancelled", "No selected.")


class SecurityConfirmationDialog(QDialog):
    def __init__(self, parent=None, action_name="Secure Action"):
        super().__init__(parent)
        self.setWindowTitle("Secure Confirmation")
        self.setFixedSize(520, 360)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        self.background = QLabel()
        self.background.setObjectName("SecurityBackground")
        self.background.setFixedHeight(130)
        self.background.setAlignment(Qt.AlignCenter)
        blur = QGraphicsBlurEffect(self)
        blur.setBlurRadius(6)
        self.background.setGraphicsEffect(blur)

        self.title = QLabel(f"Authorize: {action_name}")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setProperty("variant", "accent")

        self.subtitle = QLabel("Choose Yes to continue or No to cancel.")
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setProperty("variant", "muted")

        self.message = QLabel("")
        self.message.setAlignment(Qt.AlignCenter)
        self.message.setProperty("variant", "danger")

        self.yes_button = QPushButton("YES")
        self.no_button = QPushButton("NO")
        self.yes_button.setFixedHeight(42)
        self.no_button.setFixedHeight(42)
        self.yes_button.clicked.connect(self.accept)
        self.no_button.clicked.connect(self.reject)

        buttons = QVBoxLayout()
        buttons.addWidget(self.yes_button)
        buttons.addWidget(self.no_button)

        layout.addWidget(self.background)
        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)
        layout.addWidget(self.message)
        layout.addLayout(buttons)

        self.load_background()

    def load_background(self):
        profile = get_school_profile_from_db()
        path = profile.get("login_background") if profile else None
        if path and os.path.exists(path):
            pixmap = QPixmap(path).scaled(
                self.background.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation,
            )
            self.background.setPixmap(pixmap)
        else:
            self.background.setText("CONFIRMATION")


def authorize_action(parent, action_name="Secure Action"):
    dialog = SecurityConfirmationDialog(parent, action_name)
    return dialog.exec() == QDialog.Accepted
