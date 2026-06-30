from PySide6.QtWidgets import QLineEdit
from ui.metrics import INPUT_HEIGHT

from ui.searchbar import SearchBar
def SearchBar():
    e=SearchBar()
    e.setPlaceholderText("Search...")
    e.setMinimumHeight(INPUT_HEIGHT)
    return e
