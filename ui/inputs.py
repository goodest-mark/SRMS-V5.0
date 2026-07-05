from PySide6.QtWidgets import QLineEdit
from ui.metrics import INPUT_HEIGHT

from ui.searchbar import SearchBar
def LineEdit():
    e=SearchBar()
    e.setMinimumHeight(INPUT_HEIGHT)
    return e
