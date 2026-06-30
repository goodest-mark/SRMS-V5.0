from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QProgressBar,
    QApplication,
)

from PySide6.QtCore import Qt


class ProgressDialog(QDialog):

    def __init__(self, title="Working..."):
        super().__init__()

        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(450)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        layout = QVBoxLayout(self)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("""
            font-size:18px;
            font-weight:bold;
            color:#60a5fa;
        """)
        layout.addWidget(self.title_label)

        self.status_label = QLabel("Starting...")
        layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p%")
        layout.addWidget(self.progress)

        self.counter_label = QLabel("0 / 0")
        self.counter_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.counter_label)

    def update_progress(self, current, total, message="Working..."):

        total = max(total, 1)

        percent = int((current / total) * 100)

        self.progress.setValue(percent)
        self.status_label.setText(message)
        self.counter_label.setText(f"{current} / {total}")

        QApplication.processEvents()

    def finish(self, message="Completed"):

        self.progress.setValue(100)
        self.status_label.setText(message)
        self.counter_label.setText("")
        QApplication.processEvents()
