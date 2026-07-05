import os
import re

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QMessageBox, QLabel, QGroupBox, QCheckBox, QComboBox, QScrollArea, QSizePolicy, QTabWidget, QFrame, QGridLayout, QSpinBox
)

from db_utils import fetch_all, execute, execute_many
from event_bus import EventBus
from security_settings import authorize_action
from security_settings import SecuritySettingsPage
from backup_utils import export_backup, import_backup
from theme import available_theme_names, normalize_theme_name

_SAFE_BACKUP_PATH = re.compile(r'^[\w./ \\:-]+$')

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)
        title = QLabel("GLOBAL SYSTEM SETTINGS")
        title.setProperty("variant", "accent")

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        general_tab = QWidget()
        general_outer = QVBoxLayout(general_tab)
        general_outer.setContentsMargins(0, 0, 0, 0)
        general_outer.setSpacing(0)

        general_scroll = QScrollArea()
        general_scroll.setWidgetResizable(True)
        general_scroll.setFrameShape(QFrame.NoFrame)
        general_outer.addWidget(general_scroll, 1)

        general_content = QWidget()
        general_scroll.setWidget(general_content)

        general_layout = QVBoxLayout(general_content)
        general_layout.setContentsMargins(12, 10, 12, 10)
        general_layout.setSpacing(14)
        general_layout.addWidget(title)

        card_grid = QGridLayout()
        card_grid.setContentsMargins(0, 0, 0, 0)
        card_grid.setHorizontalSpacing(16)
        card_grid.setVerticalSpacing(14)
        card_grid.setColumnStretch(0, 1)
        card_grid.setColumnStretch(1, 1)
        card_grid.setRowStretch(0, 1)
        card_grid.setRowStretch(1, 1)
        general_layout.addLayout(card_grid, 1)
        

        # 1. Academic Settings
        acc_group = QGroupBox("ACADEMIC SETTINGS")
        acc_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        acc_form = QFormLayout(acc_group)
        self.o_level_counted = QSpinBox()
        self.o_level_counted.setRange(1, 20)
        self.a_level_principal = QSpinBox()
        self.a_level_principal.setRange(1, 10)
        acc_form.addRow("O-Level Counted Subjects:", self.o_level_counted)
        acc_form.addRow("A-Level Principal Subjects:", self.a_level_principal)
        card_grid.addWidget(acc_group, 0, 0)

        # 2. Report Settings
        rep_group = QGroupBox("REPORT SETTINGS")
        rep_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        rep_vbox = QVBoxLayout(rep_group)
        self.show_logo = QCheckBox("Show School Logo on Reports")
        self.show_watermark = QCheckBox("Show Confidential Watermark")
        self.show_gender_summary = QCheckBox("Show Gender Summary on Broadsheet")
        self.show_subject_ranking = QCheckBox("Show Subject Ranking in Summary")
        self.show_requirements = QCheckBox("Show Requirements Section in Report Books")
        for cb in [self.show_logo, self.show_watermark, self.show_gender_summary, self.show_subject_ranking, self.show_requirements]:
            rep_vbox.addWidget(cb)
        card_grid.addWidget(rep_group, 0, 1)

        # 3. Promotion Settings
        pro_group = QGroupBox("PROMOTION SETTINGS")
        pro_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        pro_vbox = QVBoxLayout(pro_group)
        self.auto_promotion = QCheckBox("Enable Auto Promotion")
        self.confirm_promotion = QCheckBox("Confirm Before Applying Promotion")
        self.auto_backup = QCheckBox("Enable Auto Backup")
        pro_vbox.addWidget(self.auto_promotion)
        pro_vbox.addWidget(self.confirm_promotion)
        pro_vbox.addWidget(self.auto_backup)
        card_grid.addWidget(pro_group, 1, 0)

        # 4. System Settings
        sys_group = QGroupBox("SYSTEM SETTINGS")
        sys_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sys_form = QFormLayout(sys_group)
        self.default_level = QComboBox()
        self.default_level.addItems(["O_LEVEL", "A_LEVEL"])
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(available_theme_names())
        self.backup_folder = QLineEdit()
        sys_form.addRow("Default Startup Level:", self.default_level)
        sys_form.addRow("Theme:", self.theme_combo)
        sys_form.addRow("Backup Folder Path:", self.backup_folder)
        card_grid.addWidget(sys_group, 1, 1)

        # 5. Backup Actions
        backup_group = QGroupBox("BACKUP")
        backup_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        backup_layout = QVBoxLayout(backup_group)
        self.export_backup_btn = QPushButton("EXPORT BACKUP")
        self.import_backup_btn = QPushButton("IMPORT BACKUP")
        self.export_backup_btn.clicked.connect(self.export_backup)
        self.import_backup_btn.clicked.connect(self.import_backup)
        backup_layout.addWidget(QLabel("Backup the full database or restore from a saved backup file."))
        backup_layout.addWidget(self.export_backup_btn)
        backup_layout.addWidget(self.import_backup_btn)
        card_grid.addWidget(backup_group, 2, 0, 1, 2)


        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("SAVE SETTINGS")
        self.save_btn.clicked.connect(self.save_settings)
        
        self.reset_btn = QPushButton("RESTORE DEFAULTS")
        self.reset_btn.clicked.connect(self.restore_defaults)
        
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addStretch(1)
        general_layout.addLayout(btn_layout)

        self.tabs.addTab(general_tab, "General")
        self.tabs.addTab(SecuritySettingsPage(), "Security")

        layout.addWidget(self.tabs, 1)
        self.load_settings()

    def load_settings(self):
        settings = dict(fetch_all("SELECT setting_key, setting_value FROM system_settings"))

        self.o_level_counted.setValue(self._safe_int(settings.get('o_level_counted', '7'), 7))
        self.a_level_principal.setValue(self._safe_int(settings.get('a_level_principal', '3'), 3))
        self.show_logo.setChecked(settings.get('show_logo') == '1')
        self.show_watermark.setChecked(settings.get('show_watermark') == '1')
        self.show_gender_summary.setChecked(settings.get('show_gender_summary') == '1')
        self.show_subject_ranking.setChecked(settings.get('show_subject_ranking') == '1')
        self.show_requirements.setChecked(settings.get('show_requirements') == '1')
        self.auto_promotion.setChecked(settings.get('auto_promotion') == '1')
        self.confirm_promotion.setChecked(settings.get('confirm_promotion') == '1')
        self.auto_backup.setChecked(settings.get('auto_backup') == '1')
        self.default_level.setCurrentText(settings.get('default_level', 'O_LEVEL'))
        self.theme_combo.setCurrentText(normalize_theme_name(settings.get('theme', 'Blue')))
        self.backup_folder.setText(settings.get('backup_folder', './backups'))

    @staticmethod
    def _safe_int(value, default):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def save_settings(self):
        if not authorize_action(self, "System Settings Changes"):
            return

        o_counted = str(self.o_level_counted.value())
        a_principal = str(self.a_level_principal.value())

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
            ('theme', self.theme_combo.currentText()),
            ('default_level', self.default_level.currentText()),
            ('backup_folder', self.backup_folder.text())
        ]
        execute_many("REPLACE INTO system_settings (setting_key, setting_value) VALUES (?, ?)", data)
        EventBus.emit("THEME_CHANGED", self.theme_combo.currentText())
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

    def export_backup(self):
        if not authorize_action(self, "Export Backup"):
            return
        export_backup(self, self.backup_folder.text().strip() or None)

    def import_backup(self):
        reply = QMessageBox.question(
            self,
            "Confirm",
            "Importing a backup will replace the current database contents. Continue?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        if not authorize_action(self, "Import Backup"):
            return
        import_backup(self)


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
