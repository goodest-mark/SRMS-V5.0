from PySide6.QtWidgets import QLabel

class StatusLabel(QLabel):

    def ready(self):
        self.setText("Ready")

    def busy(self,text):
        self.setText(text)
