from PySide6.QtGui import QFont
FONT="Segoe UI"

def title():
    f=QFont(FONT,18);f.setBold(True);return f
def heading():
    f=QFont(FONT,15);f.setBold(True);return f
def body():
    return QFont(FONT,11)
def button():
    f=QFont(FONT,11);f.setBold(True);return f
def table():
    return QFont(FONT,11)
