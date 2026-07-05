from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel

class EmptyState(QWidget):

    def __init__(self,title,message):

        super().__init__()

        layout=QVBoxLayout(self)

        t=QLabel(title)
        t.setStyleSheet("font-size:18px;font-weight:bold;")

        m=QLabel(message)
        m.setWordWrap(True)

        layout.addStretch()
        layout.addWidget(t)
        layout.addWidget(m)
        layout.addStretch()
