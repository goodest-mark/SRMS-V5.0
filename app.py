import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from theme_manager import apply_theme

from splash import SplashScreen
from main_window import MainWindow
from database import init_db
from theme import get_theme


def start_app():

    init_db()

    app = QApplication(sys.argv)
    apply_theme(app, "blue")
    from theme_manager import apply_theme
    app.setStyleSheet(get_theme('Current'))

    def show_main():

        global window
        window = MainWindow()
        window.show()

    splash = SplashScreen(on_finish=show_main)
    splash.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    start_app()