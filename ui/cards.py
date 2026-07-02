from PySide6.QtCore import QEasingCurve, QPointF, QPropertyAnimation, Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
)

from ui.fonts import heading, body


class Card(QFrame):
    def __init__(self, title=""):
        super().__init__()
        self.setObjectName("Card")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(18, 18, 18, 18)
        self.layout.setSpacing(8)

        if title:
            self.title = QLabel(title)
            self.title.setFont(heading())
            self.layout.addWidget(self.title)


class StatCard(Card):
    def __init__(self, title, value):
        super().__init__()
        self.title = QLabel(title)
        self.value = QLabel(str(value))
        self.title.setFont(body())
        f = heading()
        f.setPointSize(22)
        f.setBold(True)
        self.value.setFont(f)
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.value)


class PremiumStatCard(QFrame):
    def __init__(self, title, subtitle, icon_path, tone="primary"):
        super().__init__()

        self._shadow_rest = QPointF(0.0, 5.0)
        self._shadow_hover = QPointF(0.0, 10.0)
        self._shadow_anim = None
        self._blur_anim = None

        self.setObjectName("PremiumStatCard")
        self.setProperty("tone", tone)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumHeight(132)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover, True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(False)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setOffset(self._shadow_rest)
        self.setGraphicsEffect(shadow)
        self._shadow = shadow

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 12)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(10)

        icon_box = QFrame()
        icon_box.setObjectName("PremiumStatIcon")
        icon_box.setProperty("tone", tone)
        icon_box.setFixedSize(34, 34)

        icon_layout = QVBoxLayout(icon_box)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setPixmap(QIcon(icon_path).pixmap(18, 18))
        icon_layout.addWidget(icon_label)

        title_stack = QVBoxLayout()
        title_stack.setContentsMargins(0, 0, 0, 0)
        title_stack.setSpacing(1)

        self.title_lbl = QLabel(title)
        self.title_lbl.setObjectName("MetricTitle")
        self.title_lbl.setWordWrap(True)
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setWeight(QFont.Weight.Bold)
        self.title_lbl.setFont(title_font)

        self.subtitle_lbl = QLabel(subtitle)
        self.subtitle_lbl.setObjectName("MetricSubtitle")
        self.subtitle_lbl.setWordWrap(True)
        subtitle_font = QFont()
        subtitle_font.setPointSize(8)
        subtitle_font.setWeight(QFont.Weight.Medium)
        self.subtitle_lbl.setFont(subtitle_font)

        title_stack.addWidget(self.title_lbl)
        title_stack.addWidget(self.subtitle_lbl)

        top_row.addWidget(icon_box, 0, Qt.AlignTop)
        top_row.addLayout(title_stack, 1)

        self.value_lbl = QLabel("0")
        self.value_lbl.setAlignment(Qt.AlignCenter)
        self.value_lbl.setObjectName("MetricValue")
        value_font = QFont()
        value_font.setPointSize(24)
        value_font.setWeight(QFont.Weight.Black)
        self.value_lbl.setFont(value_font)

        accent = QFrame()
        accent.setObjectName("CardAccent")
        accent.setProperty("tone", tone)
        accent.setFixedHeight(4)

        layout.addLayout(top_row)
        layout.addWidget(self.value_lbl)
        layout.addWidget(accent)

    def set_value(self, value):
        self.value_lbl.setText(str(value))

    def enterEvent(self, event):
        self._animate_shadow(self._shadow_hover, 26)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate_shadow(self._shadow_rest, 18)
        super().leaveEvent(event)

    def _animate_shadow(self, offset, blur):
        if self._shadow_anim is not None:
            self._shadow_anim.stop()
        if self._blur_anim is not None:
            self._blur_anim.stop()

        self._shadow_anim = QPropertyAnimation(self._shadow, b"offset", self)
        self._shadow_anim.setDuration(160)
        self._shadow_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._shadow_anim.setStartValue(self._shadow.offset())
        self._shadow_anim.setEndValue(offset)
        self._shadow_anim.start()

        self._blur_anim = QPropertyAnimation(self._shadow, b"blurRadius", self)
        self._blur_anim.setDuration(160)
        self._blur_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._blur_anim.setStartValue(self._shadow.blurRadius())
        self._blur_anim.setEndValue(blur)
        self._blur_anim.start()
