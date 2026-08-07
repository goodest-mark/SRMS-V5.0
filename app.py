import sys
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app_paths import find_icon_path
from ui.pages.splash import SplashScreen
from ui.pages.main_window import MainWindow
from database import init_db
from settings_page import get_setting
from theme import apply_theme, normalize_theme_name
from backup_utils import create_startup_auto_backup


def start_app():
    # ``init_db`` uses the single writable database location from app_paths.
    init_db()
    try:
        create_startup_auto_backup()
    except Exception as error:
        # A failed automatic backup must not stop staff from opening SRMS.
        print(f"[BACKUP] Automatic backup failed: {error}")

    app = QApplication(sys.argv)
    app_icon_path = find_icon_path(
        "icon.ico",
        "icon.png",
        "icon.jpg",
        "app_icon.ico",
        "app_icon.png",
        "app_icon.jpg",
    )
    if app_icon_path is not None:
        app.setWindowIcon(QIcon(str(app_icon_path)))
    saved_theme = normalize_theme_name(get_setting("theme", "Blue"))
    apply_theme(app, saved_theme)

    def show_main():
        global window
        window = MainWindow()
        window.show()

    splash = SplashScreen(on_finish=show_main)
    splash.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    start_app()
