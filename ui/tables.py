from PySide6.QtWidgets import QTableWidget,QHeaderView
from ui.fonts import table
from ui.metrics import TABLE_ROW_HEIGHT

from ui.tables import Table
def Table():
    t=Table()
    t.setFont(table())
    t.setAlternatingRowColors(True)
    t.setSortingEnabled(True)
    t.verticalHeader().setDefaultSectionSize(TABLE_ROW_HEIGHT)
    t.horizontalHeader().setStretchLastSection(True)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    return t
