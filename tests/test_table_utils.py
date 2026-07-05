"""Unit tests for table_utils module."""
import pytest
from unittest.mock import MagicMock, patch, call
from table_utils import setup_table, populate_table


class TestSetupTable:
    def test_sets_column_count(self):
        table = MagicMock()
        headers = ["ID", "Name", "Status"]
        setup_table(table, headers)
        table.setColumnCount.assert_called_once_with(3)

    def test_sets_header_labels(self):
        table = MagicMock()
        headers = ["ID", "Name", "Status"]
        setup_table(table, headers)
        table.setHorizontalHeaderLabels.assert_called_once_with(headers)

    def test_sets_selection_behavior(self):
        table = MagicMock()
        from PySide6.QtWidgets import QAbstractItemView
        setup_table(table, ["A", "B"])
        table.setSelectionBehavior.assert_called_once_with(QAbstractItemView.SelectRows)

    def test_sets_edit_triggers(self):
        table = MagicMock()
        from PySide6.QtWidgets import QAbstractItemView
        setup_table(table, ["A", "B"])
        table.setEditTriggers.assert_called_once_with(QAbstractItemView.NoEditTriggers)

    def test_stretch_mode_enabled_by_default(self):
        table = MagicMock()
        header_mock = MagicMock()
        table.horizontalHeader.return_value = header_mock
        from PySide6.QtWidgets import QHeaderView
        setup_table(table, ["A", "B"])
        header_mock.setSectionResizeMode.assert_called_once_with(QHeaderView.Stretch)

    def test_stretch_mode_disabled(self):
        table = MagicMock()
        setup_table(table, ["A", "B"], stretch=False)
        table.horizontalHeader.assert_not_called()


class TestPopulateTable:
    def test_sets_row_count(self):
        table = MagicMock()
        rows = [(1, "Alice"), (2, "Bob")]
        populate_table(table, rows)
        table.setRowCount.assert_called_once_with(2)

    def test_empty_rows(self):
        table = MagicMock()
        populate_table(table, [])
        table.setRowCount.assert_called_once_with(0)

    @patch("table_utils.QTableWidgetItem")
    def test_populates_cells(self, mock_item):
        table = MagicMock()
        rows = [(1, "Alice")]
        populate_table(table, rows)
        assert table.setItem.call_count == 2
        mock_item.assert_any_call("1")
        mock_item.assert_any_call("Alice")

    @patch("table_utils.QTableWidgetItem")
    def test_none_value_becomes_empty_string(self, mock_item):
        table = MagicMock()
        rows = [(None,)]
        populate_table(table, rows)
        mock_item.assert_called_with("")

    @patch("table_utils.QTableWidgetItem")
    def test_formatters_applied(self, mock_item):
        table = MagicMock()
        rows = [(1, True)]
        formatters = {1: lambda v: "YES" if v else "NO"}
        populate_table(table, rows, formatters=formatters)
        mock_item.assert_any_call("YES")

    @patch("table_utils.QTableWidgetItem")
    def test_formatters_only_apply_to_specified_columns(self, mock_item):
        table = MagicMock()
        rows = [(42, False)]
        formatters = {1: lambda v: "YES" if v else "NO"}
        populate_table(table, rows, formatters=formatters)
        mock_item.assert_any_call("42")
        mock_item.assert_any_call("NO")
