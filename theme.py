DARK_STYLE = """

/* =========================================
   GLOBAL
========================================= */

QWidget{
    background:#081225;
    color:#e2e8f0;
    font-family:Inter,Segoe UI,Arial;
    font-size:15px;
}

/* =========================================
   LABELS
========================================= */

QLabel{
    color:#dbeafe;
    background:transparent;
}

/* =========================================
   LINE EDIT
========================================= */

QLineEdit{
    background:rgba(15,23,42,0.95);
    border:1px solid #1e3a5f;
    border-radius:12px;
    padding:10px 14px;
    color:white;
    min-height:22px;
}

QLineEdit:focus{
    border:1px solid #3b82f6;
}

/* =========================================
   COMBO
========================================= */

QComboBox{
    background:rgba(15,23,42,0.95);
    border:1px solid #1e3a5f;
    border-radius:12px;
    padding:10px 14px;
    color:white;
    min-height:22px;
}

QComboBox:hover{
    border:1px solid #3b82f6;
}

QComboBox::drop-down{
    border:none;
    width:28px;
}

QComboBox QAbstractItemView{
    background:#0f172a;
    color:white;
    border:1px solid #334155;
    selection-background-color:#2563eb;
}

/* =========================================
   BUTTONS
========================================= */

QPushButton{
    background:qlineargradient(
        x1:0,y1:0,x2:1,y2:1,
        stop:0 #2563eb,
        stop:1 #1d4ed8
    );

    border:none;
    border-radius:14px;

    color:white;
    font-weight:600;

    padding:12px 16px;

    min-height:22px;
}

QPushButton:hover{
    background:qlineargradient(
        x1:0,y1:0,x2:1,y2:1,
        stop:0 #3b82f6,
        stop:1 #2563eb
    );
}

QPushButton:pressed{
    background:#1e40af;
}

/* =========================================
   TABLES
========================================= */

QTableWidget{
    background:#0b1427;
    border:1px solid #1e293b;
    border-radius:14px;

    color:white;
    gridline-color:#1e293b;

    selection-background-color:#2563eb;
}

QTableWidget::item{
    padding:8px;
}

QTableWidget::item:selected{
    background:#2563eb;
}

/* =========================================
   TABLE HEADERS
========================================= */

QHeaderView::section{
    background:#17253c;
    color:white;

    border:none;

    padding:10px;

    font-weight:700;
}

/* =========================================
   SCROLLBARS
========================================= */

QScrollBar:vertical{
    width:10px;
    background:transparent;
}

QScrollBar::handle:vertical{
    background:#2563eb;
    border-radius:5px;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical{
    height:0;
}

QScrollBar:horizontal{
    height:10px;
    background:transparent;
}

QScrollBar::handle:horizontal{
    background:#2563eb;
    border-radius:5px;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal{
    width:0;
}

/* =========================================
   MESSAGE BOX
========================================= */

QMessageBox{
    background:#0f172a;
}

/* =========================================
   TOOLTIP
========================================= */

QToolTip{
    background:#111827;
    color:white;
    border:1px solid #334155;
    padding:6px;
    border-radius:8px;
}

"""


LIGHT_STYLE = """

/* =========================================
   GLOBAL
========================================= */

QWidget{
    background:#eef2f6;
    color:#111827;
    font-family:Inter,Segoe UI,Arial;
    font-size:15px;
}

/* =========================================
   LABELS
========================================= */

QLabel{
    color:#1e293b;
    background:transparent;
}

/* =========================================
   LINE EDIT
========================================= */

QLineEdit{
    background:#f5f7f9;
    border:1px solid #d1d9df;
    border-radius:12px;
    padding:10px 14px;
    color:#111827;
    min-height:22px;
}

QLineEdit:focus{
    border:1px solid #2563eb;
}

/* =========================================
   COMBO
========================================= */

QComboBox{
    background:#f5f7f9;
    border:1px solid #d1d9df;
    border-radius:12px;
    padding:10px 14px;
    color:#111827;
    min-height:22px;
}

QComboBox:hover{
    border:1px solid #2563eb;
}

QComboBox::drop-down{
    border:none;
    width:28px;
}

QComboBox QAbstractItemView{
    background:#f1f5f8;
    color:#111827;
    border:1px solid #e6eef3;
    selection-background-color:#e6eef8;
    selection-color:#0f172a;
}

/* =========================================
   BUTTONS
========================================= */

QPushButton{
    background:qlineargradient(
        x1:0,y1:0,x2:1,y2:1,
        stop:0 #2563eb,
        stop:1 #1d4ed8
    );

    border:none;
    border-radius:14px;

    color:white;
    font-weight:600;

    padding:12px 16px;

    min-height:22px;
}

QPushButton:hover{
    background:qlineargradient(
        x1:0,y1:0,x2:1,y2:1,
        stop:0 #3b82f6,
        stop:1 #2563eb
    );
}

QPushButton:pressed{
    background:#1e40af;
}

/* =========================================
   TABLES
========================================= */

QTableWidget{
    background:#f7fbfc;
    border:1px solid #e6eef3;
    border-radius:14px;

    color:#111827;
    gridline-color:#e6eef3;

    selection-background-color:#e6eef8;
    selection-color:#0f172a;
}

QTableWidget::item{
    padding:8px;
}

QTableWidget::item:selected{
    background:#e6eef8;
    color:#0f172a;
}

/* =========================================
   TABLE HEADERS
========================================= */

QHeaderView::section{
    background:#eef4f7;
    color:#111827;

    border:none;

    padding:10px;

    font-weight:700;
}

/* =========================================
   SCROLLBARS
========================================= */

QScrollBar:vertical{
    width:10px;
    background:transparent;
}

QScrollBar::handle:vertical{
    background:#b7d6f8;
    border-radius:5px;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical{
    height:0;
}

QScrollBar:horizontal{
    height:10px;
    background:transparent;
}

QScrollBar::handle:horizontal{
    background:#b7d6f8;
    border-radius:5px;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal{
    width:0;
}

/* =========================================
   MESSAGE BOX
========================================= */

QMessageBox{
    background:#f7fbfc;
}

/* =========================================
   TOOLTIP
========================================= */

QToolTip{
    background:#f1f5f8;
    color:#0f172a;
    border:1px solid #e6eef3;
    padding:6px;
    border-radius:8px;
}

"""

# Default to dark theme for backward compatibility
APP_STYLE = DARK_STYLE


def get_theme(theme_name):
    """Return the stylesheet for the given theme name."""
    if theme_name == "Light":
        return LIGHT_STYLE
    return DARK_STYLE
