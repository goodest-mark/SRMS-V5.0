import os
import re

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QMessageBox, QLabel, QGroupBox, QCheckBox, QComboBox, QScrollArea
)
from db_utils import fetch_all, execute, execute_many
from security_settings import authorize_action
from event_bus import EventBus

_SAFE_BACKUP_PATH = re.compile(r'^[\w./ \\:-]+$')

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        title = QLabel("GLOBAL SYSTEM SETTINGS")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #3b82f6; margin-bottom: 10px;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.container_layout = QVBoxLayout(container)

        # Styling
        group_style = "QGroupBox { font-weight: bold; color: #60a5fa; border: 1px solid #334155; border-radius: 8px; margin-top: 15px; padding: 15px; }"

        # 1. Academic Settings
        acc_group = QGroupBox("ACADEMIC SETTINGS")
        acc_group.setStyleSheet(group_style)
        acc_form = QFormLayout(acc_group)
        self.o_level_counted = QLineEdit()
        self.a_level_principal = QLineEdit()
        acc_form.addRow("O-Level Counted Subjects:", self.o_level_counted)
        acc_form.addRow("A-Level Principal Subjects:", self.a_level_principal)
        self.container_layout.addWidget(acc_group)

        # 2. Report Settings
        rep_group = QGroupBox("REPORT SETTINGS")
        rep_group.setStyleSheet(group_style)
        rep_vbox = QVBoxLayout(rep_group)
        self.show_logo = QCheckBox("Show School Logo on Reports")
        self.show_watermark = QCheckBox("Show Confidential Watermark")
        self.show_gender_summary = QCheckBox("Show Gender Summary on Broadsheet")
        self.show_subject_ranking = QCheckBox("Show Subject Ranking in Summary")
        self.show_requirements = QCheckBox("Show Requirements Section in Report Books")
        for cb in [self.show_logo, self.show_watermark, self.show_gender_summary, self.show_subject_ranking, self.show_requirements]:
            rep_vbox.addWidget(cb)
        self.container_layout.addWidget(rep_group)

        # 3. Promotion Settings
        pro_group = QGroupBox("PROMOTION SETTINGS")
        pro_group.setStyleSheet(group_style)
        pro_vbox = QVBoxLayout(pro_group)
        self.auto_promotion = QCheckBox("Enable Auto Promotion")
        self.confirm_promotion = QCheckBox("Confirm Before Applying Promotion")
        self.auto_backup = QCheckBox("Enable Auto Backup")
        pro_vbox.addWidget(self.auto_promotion)
        pro_vbox.addWidget(self.confirm_promotion)
        pro_vbox.addWidget(self.auto_backup)
        self.container_layout.addWidget(pro_group)

        # 4. System Settings
        sys_group = QGroupBox("SYSTEM SETTINGS")
        sys_group.setStyleSheet(group_style)
        sys_form = QFormLayout(sys_group)
        self.theme = QComboBox()
        self.theme.addItems(["Dark", "Light"])
        self.theme.currentTextChanged.connect(self._on_theme_changed)
        self.default_level = QComboBox()
        self.default_level.addItems(["O_LEVEL", "A_LEVEL"])
        self.backup_folder = QLineEdit()
        sys_form.addRow("System Theme:", self.theme)
        sys_form.addRow("Default Startup Level:", self.default_level)
        sys_form.addRow("Backup Folder Path:", self.backup_folder)
        self.container_layout.addWidget(sys_group)

        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("SAVE SETTINGS")
        self.save_btn.setStyleSheet("background-color: #10b981;")
        self.save_btn.clicked.connect(self.save_settings)
        
        self.reset_btn = QPushButton("RESTORE DEFAULTS")
        self.reset_btn.setStyleSheet("background-color: #ef4444;")
        self.reset_btn.clicked.connect(self.restore_defaults)
        
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.reset_btn)
        self.container_layout.addLayout(btn_layout)

        scroll.setWidget(container)
        # ensure the container's size reflects its contents so the scroll area
        # can provide scrollbars that reach the bottom-most widgets
        container.adjustSize()
        scroll.setWidgetResizable(False)
        layout.addWidget(scroll)
        self.load_settings()

    def load_settings(self):
        settings = dict(fetch_all("SELECT setting_key, setting_value FROM system_settings"))

        self.o_level_counted.setText(settings.get('o_level_counted', '7'))
        self.a_level_principal.setText(settings.get('a_level_principal', '3'))
        self.show_logo.setChecked(settings.get('show_logo') == '1')
        self.show_watermark.setChecked(settings.get('show_watermark') == '1')
        self.show_gender_summary.setChecked(settings.get('show_gender_summary') == '1')
        self.show_subject_ranking.setChecked(settings.get('show_subject_ranking') == '1')
        self.show_requirements.setChecked(settings.get('show_requirements') == '1')
        self.auto_promotion.setChecked(settings.get('auto_promotion') == '1')
        self.confirm_promotion.setChecked(settings.get('confirm_promotion') == '1')
        self.auto_backup.setChecked(settings.get('auto_backup') == '1')
        saved_theme = settings.get('theme', 'Dark')
        if self.theme.findText(saved_theme) == -1:
            saved_theme = 'Dark'
        self.theme.setCurrentText(saved_theme)
        self.default_level.setCurrentText(settings.get('default_level', 'O_LEVEL'))
        self.backup_folder.setText(settings.get('backup_folder', './backups'))

    def save_settings(self):
        if not authorize_action(self, "System Settings Changes"):
            return

        # Validate numeric inputs
        o_counted = self.o_level_counted.text().strip()
        a_principal = self.a_level_principal.text().strip()

        if not o_counted.isdigit() or not (1 <= int(o_counted) <= 20):
            QMessageBox.warning(self, "Validation Error", "O-Level Counted Subjects must be a number between 1 and 20.")
            return
        if not a_principal.isdigit() or not (1 <= int(a_principal) <= 10):
            QMessageBox.warning(self, "Validation Error", "A-Level Principal Subjects must be a number between 1 and 10.")
            return

        backup_path = self.backup_folder.text().strip()
        if backup_path:
            normalized = os.path.normpath(backup_path)
            if not _SAFE_BACKUP_PATH.match(normalized) or '..' in normalized.split(os.sep):
                QMessageBox.warning(self, "Validation Error", "Backup folder path contains invalid characters or traversal sequences.")
                return

        data = [
            ('o_level_counted', o_counted),
            ('a_level_principal', a_principal),
            ('show_logo', '1' if self.show_logo.isChecked() else '0'),
            ('show_watermark', '1' if self.show_watermark.isChecked() else '0'),
            ('show_gender_summary', '1' if self.show_gender_summary.isChecked() else '0'),
            ('show_subject_ranking', '1' if self.show_subject_ranking.isChecked() else '0'),
            ('show_requirements', '1' if self.show_requirements.isChecked() else '0'),
            ('auto_promotion', '1' if self.auto_promotion.isChecked() else '0'),
            ('confirm_promotion', '1' if self.confirm_promotion.isChecked() else '0'),
            ('auto_backup', '1' if self.auto_backup.isChecked() else '0'),
            ('theme', self.theme.currentText()),
            ('default_level', self.default_level.currentText()),
            ('backup_folder', self.backup_folder.text())
        ]
        execute_many("REPLACE INTO system_settings (setting_key, setting_value) VALUES (?, ?)", data)
        QMessageBox.information(self, "Success", "Global settings updated successfully.")

    def restore_defaults(self):
        reply = QMessageBox.question(self, "Confirm", "Restore all settings to factory defaults?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if not authorize_action(self, "System Settings Changes"):
                return

            execute("DELETE FROM system_settings")
            from database import init_db
            init_db()
            self.load_settings()

    def _on_theme_changed(self, theme_name):
        """Apply theme change immediately via EventBus."""
        EventBus.emit("THEME_CHANGED", theme_name)


def get_setting(key, default=None):
    from db_utils import fetch_one
    try:
        res = fetch_one("SELECT setting_value FROM system_settings WHERE setting_key=?", (key,))
        return res[0] if res else default
    except Exception as e:
        print(f"[ERROR] Failed to read setting '{key}': {e}")
        return default


def get_int_setting(key, default):
    """Return an integer system setting, falling back to *default* on any error."""
    raw = get_setting(key, str(default))
    try:
        return int(raw)
    except (ValueError, TypeError):
        return default