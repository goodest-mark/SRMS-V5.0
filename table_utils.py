"""Shared QTableWidget utilities to eliminate repeated table setup/population boilerplate."""

from PySide6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView,
)

from progress_dialog import ProgressDialog


def setup_table(table, headers, stretch=True):
    """Configure a QTableWidget with standard read-only, row-selection behavior.

    Args:
        table: QTableWidget instance
        headers: list of column header strings
        stretch: if True, stretch columns to fill width
    """
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    if stretch:
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)


def populate_table(table, rows, formatters=None):
    """Fill a QTableWidget from a list of row tuples.

    Args:
        table: QTableWidget instance
        rows: list of tuples (one per row)
        formatters: optional dict mapping column index to a callable
                    that transforms the raw value into a display string.
                    Example: {2: lambda v: "YES" if v else "NO"}
    """
    table.setRowCount(len(rows))
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            if formatters and c in formatters:
                display = formatters[c](value)
            else:
                display = str(value) if value is not None else ""
            table.setItem(r, c, QTableWidgetItem(display))
