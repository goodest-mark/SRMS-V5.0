from PySide6.QtWidgets import QWidget,QVBoxLayout,QProgressBar,QLabel

class LoadingWidget(QWidget):

    def __init__(self,text="Loading..."):

        super().__init__()

        layout=QVBoxLayout(self)

        self.label=QLabel(text)

        self.progress=QProgressBar()

        self.progress.setRange(0,0)

        layout.addStretch()
        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        layout.addStretch()

    def setText(self,text):
        self.label.setText(text)
