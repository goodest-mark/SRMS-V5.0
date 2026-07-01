from PySide6.QtWidgets import QLineEdit

from ui.metrics import INPUT_HEIGHT


def SearchBar():
    e = QLineEdit()
    e.setPlaceholderText("Search...")
    e.setMinimumHeight(INPUT_HEIGHT)
    return e
