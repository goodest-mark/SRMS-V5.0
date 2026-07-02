def _theme(
    *,
    app_bg,
    surface,
    surface_alt,
    input_bg,
    table_bg_0,
    table_bg_1,
    header_bg,
    text,
    text_soft,
    muted,
    border,
    primary,
    primary_2,
    success,
    warning,
    danger,
    tooltip_bg,
    font_size=15,
    control_padding="10px 14px",
    button_padding="12px 16px",
    control_radius=12,
    button_radius=14,
    table_item_padding=8,
    group_radius=18,
):
    return {
        "app_bg": app_bg,
        "surface": surface,
        "surface_alt": surface_alt,
        "input_bg": input_bg,
        "table_bg_0": table_bg_0,
        "table_bg_1": table_bg_1,
        "header_bg": header_bg,
        "text": text,
        "text_soft": text_soft,
        "muted": muted,
        "border": border,
        "primary": primary,
        "primary_2": primary_2,
        "success": success,
        "warning": warning,
        "danger": danger,
        "tooltip_bg": tooltip_bg,
        "font_size": font_size,
        "control_padding": control_padding,
        "button_padding": button_padding,
        "control_radius": control_radius,
        "button_radius": button_radius,
        "table_item_padding": table_item_padding,
        "group_radius": group_radius,
    }


_THEME_TOKENS = {
    "Blue": _theme(
        app_bg="#081225",
        surface="rgba(15,23,42,0.96)",
        surface_alt="rgba(30,41,59,0.88)",
        input_bg="rgba(15,23,42,0.95)",
        table_bg_0="rgba(2,6,23,0.98)",
        table_bg_1="rgba(15,23,42,0.96)",
        header_bg="#17253c",
        text="#e2e8f0",
        text_soft="#dbeafe",
        muted="#94a3b8",
        border="rgba(59,130,246,0.24)",
        primary="#2563eb",
        primary_2="#3b82f6",
        success="#10b981",
        warning="#f59e0b",
        danger="#ef4444",
        tooltip_bg="#111827",
    ),
    "Professional Dark": _theme(
        app_bg="#020409",
        surface="rgba(6,10,18,0.98)",
        surface_alt="rgba(12,17,28,0.95)",
        input_bg="rgba(8,12,20,0.98)",
        table_bg_0="rgba(2,4,9,1)",
        table_bg_1="rgba(7,12,20,0.99)",
        header_bg="#07101d",
        text="#ffffff",
        text_soft="#f8fbff",
        muted="#b6c3d6",
        border="rgba(96,165,250,0.30)",
        primary="#1d4ed8",
        primary_2="#60a5fa",
        success="#10b981",
        warning="#f59e0b",
        danger="#ef4444",
        tooltip_bg="#020617",
    ),
    "Light": _theme(
        app_bg="#f5f7fb",
        surface="rgba(255,255,255,0.98)",
        surface_alt="rgba(248,250,252,0.94)",
        input_bg="#ffffff",
        table_bg_0="rgba(241,245,249,0.98)",
        table_bg_1="rgba(226,232,240,0.95)",
        header_bg="#e2e8f0",
        text="#0f172a",
        text_soft="#0f172a",
        muted="#64748b",
        border="rgba(37,99,235,0.24)",
        primary="#2563eb",
        primary_2="#60a5fa",
        success="#0ea56f",
        warning="#d97706",
        danger="#dc2626",
        tooltip_bg="#020617",
    ),
    "Accessibility Blue": _theme(
        app_bg="#07101f",
        surface="rgba(14,26,49,0.98)",
        surface_alt="rgba(23,39,71,0.94)",
        input_bg="rgba(9,18,34,0.97)",
        table_bg_0="rgba(4,10,22,0.99)",
        table_bg_1="rgba(9,18,34,0.98)",
        header_bg="#102443",
        text="#f8fbff",
        text_soft="#ffffff",
        muted="#c7d2e2",
        border="rgba(125,211,252,0.38)",
        primary="#0f5bd8",
        primary_2="#38bdf8",
        success="#16a34a",
        warning="#f59e0b",
        danger="#dc2626",
        tooltip_bg="#020617",
        font_size=16,
        control_padding="12px 16px",
        button_padding="13px 18px",
        control_radius=14,
        button_radius=16,
        table_item_padding=10,
        group_radius=20,
    ),
    "Accessibility Dark": _theme(
        app_bg="#02050d",
        surface="rgba(7,12,22,0.98)",
        surface_alt="rgba(15,24,40,0.95)",
        input_bg="rgba(7,12,22,0.98)",
        table_bg_0="rgba(3,7,18,0.99)",
        table_bg_1="rgba(10,16,28,0.98)",
        header_bg="#0b1324",
        text="#f8fafc",
        text_soft="#ffffff",
        muted="#cbd5e1",
        border="rgba(148,163,184,0.35)",
        primary="#2563eb",
        primary_2="#93c5fd",
        success="#22c55e",
        warning="#f59e0b",
        danger="#f87171",
        tooltip_bg="#000000",
        font_size=16,
        control_padding="12px 16px",
        button_padding="13px 18px",
        control_radius=14,
        button_radius=16,
        table_item_padding=10,
        group_radius=20,
    ),
    "High Contrast": _theme(
        app_bg="#000000",
        surface="rgba(0,0,0,1)",
        surface_alt="rgba(24,24,27,1)",
        input_bg="#111111",
        table_bg_0="#000000",
        table_bg_1="#111111",
        header_bg="#0b3ea8",
        text="#ffffff",
        text_soft="#ffffff",
        muted="#e5e7eb",
        border="#2563eb",
        primary="#2563eb",
        primary_2="#60a5fa",
        success="#22c55e",
        warning="#f59e0b",
        danger="#f87171",
        tooltip_bg="#000000",
        font_size=16,
        control_padding="12px 16px",
        button_padding="13px 18px",
        control_radius=0,
        button_radius=0,
        table_item_padding=10,
        group_radius=0,
    ),
}

_ALIASES = {
    "Current": "Blue",
    "Dark": "Professional Dark",
    "Light": "Light",
    "Mono Blue": "Light",
    "Dusk": "Accessibility Dark",
    "Black & White": "High Contrast",
    "Black White Blue": "Accessibility Blue",
}


def normalize_theme_name(theme_name):
    return _ALIASES.get(theme_name, theme_name if theme_name in _THEME_TOKENS else "Blue")


def available_theme_names():
    return list(_THEME_TOKENS.keys())


def _build(tokens):
    return f"""
/* =========================================
   SRMS GLOBAL THEME
========================================= */

QWidget{{
    background:{tokens['app_bg']};
    color:{tokens['text']};
    font-family:Inter,Segoe UI,Arial;
    font-size:{tokens['font_size']}px;
    font-weight:600;
}}

QLabel{{
    color:{tokens['text']};
    background:transparent;
    font-weight:650;
}}

QLabel[variant="muted"]{{
    color:{tokens['muted']};
}}

QLabel[variant="accent"]{{
    color:{tokens['primary_2']};
}}

QLabel[variant="success"]{{
    color:{tokens['success']};
}}

QLabel[variant="danger"]{{
    color:{tokens['danger']};
}}

QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox{{
    background:{tokens['input_bg']};
    border:1px solid {tokens['border']};
    border-radius:{tokens['control_radius']}px;
    padding:{tokens['control_padding']};
    color:{tokens['text']};
    min-height:22px;
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus{{
    border:1px solid {tokens['primary_2']};
}}

QComboBox{{
    background:{tokens['input_bg']};
    border:1px solid {tokens['border']};
    border-radius:{tokens['control_radius']}px;
    padding:{tokens['control_padding']};
    color:{tokens['text']};
    min-height:22px;
}}

QComboBox:hover{{
    border:1px solid {tokens['primary_2']};
}}

QComboBox::drop-down{{
    border:none;
    width:28px;
}}

QComboBox QAbstractItemView{{
    background:{tokens['table_bg_1']};
    color:{tokens['text_soft']};
    border:1px solid {tokens['border']};
    selection-background-color:{tokens['primary']};
    selection-color:white;
}}

QPushButton{{
    background:qlineargradient(
        x1:0,y1:0,x2:1,y2:1,
        stop:0 {tokens['primary_2']},
        stop:1 {tokens['primary']}
    );
    border:none;
    border-radius:{tokens['button_radius']}px;
    color:white;
    font-weight:850;
    padding:{tokens['button_padding']};
    min-height:22px;
}}

QPushButton:hover{{
    background:qlineargradient(
        x1:0,y1:0,x2:1,y2:1,
        stop:0 #60a5fa,
        stop:1 {tokens['primary_2']}
    );
}}

QPushButton:pressed{{
    background:#1e40af;
}}

QTableWidget, QTableView, QListWidget, QTreeWidget{{
    background:qlineargradient(
        x1:0,y1:0,x2:1,y2:1,
        stop:0 {tokens['table_bg_0']},
        stop:1 {tokens['table_bg_1']}
    );
    color:{tokens['text_soft']};
    alternate-background-color:{tokens['surface_alt']};
    border:1px solid {tokens['border']};
    border-radius:16px;
    gridline-color:rgba(148,163,184,0.18);
    selection-background-color:{tokens['primary']};
    selection-color:white;
}}

QTableWidget::item, QTableView::item, QListWidget::item, QTreeWidget::item{{
    color:{tokens['text_soft']};
    padding:{tokens['table_item_padding']}px;
}}

QHeaderView::section{{
    background:{tokens['header_bg']};
    color:{tokens['text_soft']};
    border:none;
    padding:10px;
    font-weight:900;
}}

QGroupBox, QFrame#GlassCard, QFrame#HeaderFrame, QFrame#QuickActionsPanel, QFrame#SchoolInfoPanel{{
    background:qlineargradient(
        x1:0,y1:0,x2:1,y2:1,
        stop:0 {tokens['surface']},
        stop:1 {tokens['surface_alt']}
    );
    border:1px solid rgba(148,163,184,0.28);
    border-radius:{tokens['group_radius']}px;
    color:{tokens['text_soft']};
    margin-top:14px;
    padding-top:12px;
}}

QFrame#GlassCard QLabel#MetricTitle,
QFrame#PremiumStatCard QLabel#MetricTitle{{
    color:{tokens['muted']};
    font-weight:900;
}}

QFrame#GlassCard QLabel#MetricSubtitle,
QFrame#PremiumStatCard QLabel#MetricSubtitle{{
    color:{tokens['muted']};
}}

QFrame#GlassCard QLabel#MetricValue,
QFrame#PremiumStatCard QLabel#MetricValue{{
    color:{tokens['text_soft']};
    font-weight:900;
}}

QFrame#PremiumStatCard{{
    background:qlineargradient(
        x1:0,y1:0,x2:1,y2:1,
        stop:0 {tokens['surface']},
        stop:1 {tokens['surface_alt']}
    );
    border:1px solid rgba(148,163,184,0.22);
    border-radius:{tokens['group_radius']}px;
    color:{tokens['text_soft']};
    margin:2px;
}}

QFrame#PremiumStatCard:hover{{
    border:1px solid rgba(96,165,250,0.48);
}}

QFrame#PremiumStatCard QFrame#PremiumStatIcon{{
    background:rgba(148,163,184,0.14);
    border:1px solid rgba(148,163,184,0.24);
    border-radius:12px;
}}

QFrame#PremiumStatCard QFrame#CardAccent{{
    background:{tokens['primary']};
    border-radius:2px;
}}

QFrame#PremiumStatCard[tone="primary"] QFrame#PremiumStatIcon,
QFrame#PremiumStatCard[tone="primary"] QFrame#CardAccent{{
    background:qlineargradient(
        x1:0,y1:0,x2:1,y2:0,
        stop:0 {tokens['primary_2']},
        stop:1 {tokens['primary']}
    );
}}

QFrame#PremiumStatCard[tone="secondary"] QFrame#PremiumStatIcon,
QFrame#PremiumStatCard[tone="secondary"] QFrame#CardAccent{{
    background:qlineargradient(
        x1:0,y1:0,x2:1,y2:0,
        stop:0 {tokens['primary_2']},
        stop:1 {tokens['primary']}
    );
}}

QFrame#PremiumStatCard[tone="success"] QFrame#PremiumStatIcon,
QFrame#PremiumStatCard[tone="success"] QFrame#CardAccent{{
    background:qlineargradient(
        x1:0,y1:0,x2:1,y2:0,
        stop:0 {tokens['success']},
        stop:1 {tokens['primary_2']}
    );
}}

QFrame#PremiumStatCard[tone="warning"] QFrame#PremiumStatIcon,
QFrame#PremiumStatCard[tone="warning"] QFrame#CardAccent{{
    background:qlineargradient(
        x1:0,y1:0,x2:1,y2:0,
        stop:0 {tokens['warning']},
        stop:1 {tokens['primary_2']}
    );
}}

QFrame#PremiumStatCard[tone="danger"] QFrame#PremiumStatIcon,
QFrame#PremiumStatCard[tone="danger"] QFrame#CardAccent{{
    background:qlineargradient(
        x1:0,y1:0,x2:1,y2:0,
        stop:0 {tokens['danger']},
        stop:1 {tokens['warning']}
    );
}}

QFrame#BroadsheetCard{{
    background:qlineargradient(
        x1:0,y1:0,x2:1,y2:1,
        stop:0 {tokens['surface']},
        stop:1 {tokens['surface_alt']}
    );
    border:1px solid {tokens['border']};
    border-radius:{tokens['group_radius']}px;
    color:{tokens['text_soft']};
}}

QFrame#HelpStep, QFrame#SplashCard{{
    background:qlineargradient(
        x1:0,y1:0,x2:1,y2:1,
        stop:0 {tokens['surface']},
        stop:1 {tokens['surface_alt']}
    );
    border:1px solid {tokens['border']};
    border-radius:{tokens['group_radius']}px;
    color:{tokens['text_soft']};
}}

QFrame#SecurityCard,
QLabel#SecurityBackground{{
    background:qlineargradient(
        x1:0,y1:0,x2:1,y2:1,
        stop:0 {tokens['surface']},
        stop:1 {tokens['surface_alt']}
    );
    border:1px solid {tokens['border']};
    border-radius:{tokens['group_radius']}px;
    color:{tokens['text_soft']};
}}

QLineEdit#SecurityAnswerEntry{{
    background:{tokens['input_bg']};
    border:1px solid {tokens['border']};
    border-radius:{tokens['control_radius']}px;
    color:{tokens['text_soft']};
    font-size:18px;
    letter-spacing:6px;
    min-height:42px;
}}

QLabel#ProfilePreview{{
    background:{tokens['input_bg']};
    border:2px dashed {tokens['border']};
    color:{tokens['muted']};
    border-radius:{tokens['control_radius']}px;
}}

QGroupBox::title{{
    color:{tokens['primary_2']};
    font-weight:900;
    subcontrol-origin:margin;
    subcontrol-position:top left;
    left:14px;
    padding:0 8px;
    background:{tokens['app_bg']};
}}

QTabWidget::pane{{
    border:1px solid {tokens['border']};
    border-radius:12px;
}}

QTabBar::tab{{
    background:{tokens['surface_alt']};
    color:{tokens['text_soft']};
    padding:10px 16px;
    border-top-left-radius:10px;
    border-top-right-radius:10px;
    font-weight:800;
}}

QTabBar::tab:selected{{
    background:{tokens['primary']};
    color:white;
}}

QProgressBar{{
    background:{tokens['table_bg_1']};
    color:white;
    border:1px solid {tokens['border']};
    border-radius:10px;
    min-height:20px;
    text-align:center;
    font-weight:800;
}}

QProgressBar::chunk{{
    background:qlineargradient(
        x1:0,y1:0,x2:1,y2:0,
        stop:0 {tokens['primary_2']},
        stop:1 {tokens['primary']}
    );
    border-radius:9px;
}}

QScrollBar:vertical{{
    width:10px;
    background:transparent;
}}

QScrollBar::handle:vertical{{
    background:{tokens['primary']};
    border-radius:5px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical{{
    height:0;
}}

QScrollBar:horizontal{{
    height:10px;
    background:transparent;
}}

QScrollBar::handle:horizontal{{
    background:{tokens['primary']};
    border-radius:5px;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal{{
    width:0;
}}

QMessageBox{{
    background:{tokens['surface']};
    color:{tokens['text_soft']};
}}

QToolTip{{
    background:{tokens['tooltip_bg']};
    color:{tokens['text_soft']};
    border:1px solid {tokens['border']};
    padding:6px;
    border-radius:8px;
}}
"""


def get_theme(theme_name):
    """Return the stylesheet for the selected SRMS theme."""
    return _build(_THEME_TOKENS[normalize_theme_name(theme_name)])


def apply_theme(app, theme_name):
    app.setStyleSheet(get_theme(theme_name))


# Backward-compatible constants used by older modules.
DARK_STYLE = get_theme("Blue")
LIGHT_STYLE = get_theme("Light")
APP_STYLE = DARK_STYLE
