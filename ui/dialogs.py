from PySide6.QtWidgets import QMessageBox

def info(parent,title,text):
    QMessageBox.information(parent,title,text)

def success(parent,text):
    QMessageBox.information(parent,"Success",text)

def warning(parent,text):
    QMessageBox.warning(parent,"Warning",text)

def error(parent,text):
    QMessageBox.critical(parent,"Error",text)

def confirm(parent,text):
    return QMessageBox.question(
        parent,
        "Confirm",
        text,
        QMessageBox.Yes|QMessageBox.No
    )==QMessageBox.Yes
