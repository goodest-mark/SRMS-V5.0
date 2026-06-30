from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
    QFrame
)

from progress_dialog import ProgressDialog
from PySide6.QtCore import Qt


class HelpGuideDialog(QDialog):
    """Getting Started guide dialog for new users."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Getting Started Guide")
        self.setMinimumSize(600, 500)
        self.setMaximumSize(800, 700)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QLabel("Welcome to SRMS V5")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            font-size: 22px;
            font-weight: 800;
            padding: 20px;
            color: #2563eb;
        """)
        layout.addWidget(header)

        subtitle = QLabel("Follow these steps to get started")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: #64748b;
            padding-bottom: 10px;
        """)
        layout.addWidget(subtitle)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 10, 30, 20)
        content_layout.setSpacing(16)

        steps = [
            (
                "1. Set Up Your School Profile",
                "Go to School and fill in your school name, address, "
                "phone number, and upload your school logo. This information "
                "appears on all report cards and broadsheets."
            ),
            (
                "2. Add Subjects",
                "Navigate to Academics and add all subjects taught at your "
                "school. Mark each subject as O-Level or A-Level and set "
                "the subject type (Counted/Principal)."
            ),
            (
                "3. Register Students",
                "Go to Students and add your students one by one, or use "
                "the Excel import feature to add many students at once. "
                "Each student needs an admission number, name, and class."
            ),
            (
                "4. Enroll Students in Subjects",
                "After adding students, enroll them in their subjects. "
                "This tells the system which subjects each student takes "
                "so that rankings are calculated correctly."
            ),
            (
                "5. Set Up Exams",
                "Go to Exams and create your examinations (Midterm, "
                "Terminal, Annual). Make sure the exam you want to enter "
                "results for is marked as OPEN."
            ),
            (
                "6. Enter Results",
                "Navigate to Results and enter marks for each subject. "
                "You can type marks manually or import them from an Excel "
                "file. The system will calculate grades automatically."
            ),
            (
                "7. View Rankings & Reports",
                "Once results are entered, the system automatically ranks "
                "students, calculates divisions, and generates report cards. "
                "Go to Results to view rankings, broadsheets, and print reports."
            ),
        ]

        for title, description in steps:
            step_frame = QFrame()
            step_frame.setStyleSheet("""
                QFrame {
                    border: 1px solid rgba(148, 163, 184, 0.2);
                    border-radius: 12px;
                    padding: 8px;
                }
            """)
            step_layout = QVBoxLayout(step_frame)

            title_label = QLabel(title)
            title_label.setStyleSheet("""
                font-size: 16px;
                font-weight: 700;
                border: none;
                padding: 4px 0;
            """)
            title_label.setWordWrap(True)

            desc_label = QLabel(description)
            desc_label.setStyleSheet("""
                font-size: 14px;
                line-height: 1.5;
                border: none;
                padding: 2px 0;
            """)
            desc_label.setWordWrap(True)

            step_layout.addWidget(title_label)
            step_layout.addWidget(desc_label)
            content_layout.addWidget(step_frame)

        # Tips section
        tips_title = QLabel("Quick Tips")
        tips_title.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            padding-top: 10px;
        """)
        content_layout.addWidget(tips_title)

        tips = [
            "Use the O-Level / A-Level switch at the top to toggle between education levels.",
            "Click the sidebar menu icon to collapse or expand the navigation panel.",
            "Use the refresh button (top-right) if data appears outdated.",
            "You can switch between Light and Dark themes in Settings.",
        ]

        for tip in tips:
            tip_label = QLabel(f"  {tip}")
            tip_label.setStyleSheet("font-size: 14px; padding: 4px 0;")
            tip_label.setWordWrap(True)
            content_layout.addWidget(tip_label)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Close button
        close_btn = QPushButton("Got It!")
        close_btn.setFixedHeight(44)
        close_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: 700;
                margin: 12px 30px;
                border-radius: 14px;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
