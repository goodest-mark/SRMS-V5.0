from PySide6.QtWidgets import QPushButton
from ui.fonts import button
from ui.metrics import BUTTON_HEIGHT

from ui.buttons import PrimaryButton
def PrimaryButton(text):
    b=PrimaryButton(text)
    b.setFont(button())
    b.setMinimumHeight(BUTTON_HEIGHT)
    return b
