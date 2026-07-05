from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel
from ui.fonts import title
from ui.metrics import *

class Page(QWidget):
    def __init__(self,text=""):
        super().__init__()
        self.layout=QVBoxLayout(self)
        self.layout.setContentsMargins(MARGIN,MARGIN,MARGIN,MARGIN)
        self.layout.setSpacing(SPACING)
        if text:
            lbl=QLabel(text)
            lbl.setFont(title())
            self.layout.addWidget(lbl)
