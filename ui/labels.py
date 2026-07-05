from PySide6.QtWidgets import QLabel
from ui.fonts import title,heading,body

def Title(text):
    l=QLabel(text)
    l.setFont(title())
    return l

def Heading(text):
    l=QLabel(text)
    l.setFont(heading())
    return l

def Text(text):
    l=QLabel(text)
    l.setFont(body())
    return l
