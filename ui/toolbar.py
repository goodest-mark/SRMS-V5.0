from PySide6.QtWidgets import QWidget,QHBoxLayout

class Toolbar(QWidget):

    def __init__(self):

        super().__init__()

        self.layout=QHBoxLayout(self)

        self.layout.setContentsMargins(0,0,0,0)

        self.layout.setSpacing(8)

    def add(self,w):

        self.layout.addWidget(w)
