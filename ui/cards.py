from PySide6.QtWidgets import QFrame,QVBoxLayout,QHBoxLayout,QLabel
from ui.fonts import heading,body

class Card(QFrame):

    def __init__(self,title=""):

        super().__init__()

        self.setObjectName("Card")

        self.layout=QVBoxLayout(self)

        self.layout.setContentsMargins(18,18,18,18)

        self.layout.setSpacing(8)

        if title:

            t=QLabel(title)

            t.setFont(heading())

            self.layout.addWidget(t)


class StatCard(Card):

    def __init__(self,title,value):

        super().__init__()

        self.title=QLabel(title)
        self.value=QLabel(str(value))

        self.title.setFont(body())

        f=heading()
        f.setPointSize(22)
        f.setBold(True)

        self.value.setFont(f)

        self.layout.addWidget(self.title)

        self.layout.addWidget(self.value)
