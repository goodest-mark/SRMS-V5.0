import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from ui.pages.main_window import MainWindow


def test_main_window_update_clock_does_not_raise_when_closing():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window._closing = True

    try:
        window.update_clock()
    except Exception as exc:  # pragma: no cover - regression guard
        raise AssertionError(f"update_clock should be safe while closing: {exc}") from exc
    finally:
        app.quit()
