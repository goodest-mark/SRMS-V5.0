from PySide6.QtWidgets import QPushButton

from ui.fonts import button
from ui.metrics import BUTTON_HEIGHT


def PrimaryButton(text):
    b = QPushButton(text)
    b.setFont(button())
    b.setMinimumHeight(BUTTON_HEIGHT)
    return b
