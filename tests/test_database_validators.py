"""Unit tests for database.py validator functions (_validate_identifier, _validate_definition)."""
import pytest
from database import _validate_identifier, _validate_definition


class TestValidateIdentifier:
    def test_valid_simple_name(self):
        assert _validate_identifier("column_name") == "column_name"

    def test_valid_starts_with_underscore(self):
        assert _validate_identifier("_private") == "_private"

    def test_valid_with_numbers(self):
        assert _validate_identifier("col123") == "col123"

    def test_valid_uppercase(self):
        assert _validate_identifier("MyTable") == "MyTable"

    def test_invalid_starts_with_number(self):
        with pytest.raises(ValueError, match="Unsafe SQL identifier"):
            _validate_identifier("123col")

    def test_invalid_contains_space(self):
        with pytest.raises(ValueError, match="Unsafe SQL identifier"):
            _validate_identifier("my column")

    def test_invalid_contains_semicolon(self):
        with pytest.raises(ValueError, match="Unsafe SQL identifier"):
            _validate_identifier("col;DROP")

    def test_invalid_contains_dash(self):
        with pytest.raises(ValueError, match="Unsafe SQL identifier"):
            _validate_identifier("my-column")

    def test_invalid_empty_string(self):
        with pytest.raises(ValueError, match="Unsafe SQL identifier"):
            _validate_identifier("")

    def test_invalid_sql_injection_attempt(self):
        with pytest.raises(ValueError, match="Unsafe SQL identifier"):
            _validate_identifier("col; DROP TABLE users--")


class TestValidateDefinition:
    def test_valid_text_type(self):
        assert _validate_definition("TEXT") == "TEXT"

    def test_valid_with_default(self):
        assert _validate_definition('TEXT DEFAULT "value"') == 'TEXT DEFAULT "value"'

    def test_valid_integer(self):
        assert _validate_definition("INTEGER") == "INTEGER"

    def test_invalid_contains_semicolon(self):
        with pytest.raises(ValueError, match="Unsafe column definition"):
            _validate_definition("TEXT; DROP TABLE")

    def test_invalid_contains_parentheses(self):
        with pytest.raises(ValueError, match="Unsafe column definition"):
            _validate_definition("TEXT DEFAULT (SELECT 1)")

    def test_invalid_contains_numbers(self):
        with pytest.raises(ValueError, match="Unsafe column definition"):
            _validate_definition("VARCHAR(255)")

    def test_invalid_contains_equals(self):
        with pytest.raises(ValueError, match="Unsafe column definition"):
            _validate_definition("TEXT DEFAULT=something")

    def test_valid_empty_string(self):
        with pytest.raises(ValueError, match="Unsafe column definition"):
            _validate_definition("")
