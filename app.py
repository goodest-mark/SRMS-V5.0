import sys
import os
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app_paths import icon_path
from ui.pages.splash import SplashScreen
from ui.pages.main_window import MainWindow
from database import init_db
from settings_page import get_setting
from theme import apply_theme, normalize_theme_name


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def start_app():
    # Use resource_path to locate the database in both dev and bundled modes
    db_path = resource_path("database.db")
    init_db(db_path)  # Make sure init_db() accepts a db_path argument (see note below)

    app = QApplication(sys.argv)
    app_icon_path = icon_path("icon.ico")
    if app_icon_path.exists():
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