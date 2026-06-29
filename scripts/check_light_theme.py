"""Quick check: instantiate MainWindow with Light theme (offscreen).
Exits with 0 on success, non-zero on exception.
"""
import sys
import os
from PySide6.QtWidgets import QApplication

# Ensure project root is importable when running this script directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db
from theme import get_theme
from main_window import MainWindow


def main():
    init_db()
    app = QApplication([])
    app.setStyleSheet(get_theme('Light'))
    try:
        w = MainWindow()
        w.show()
        w.close()
        print('Light theme UI constructed successfully')
    except Exception as e:
        print('ERROR', e)
        raise

if __name__ == '__main__':
    main()
