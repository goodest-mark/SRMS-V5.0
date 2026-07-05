#!/bin/bash

FILE="$1"

echo
echo "========== $FILE =========="
echo

echo "Widgets:"
grep -n "QPushButton\|QLineEdit\|QTableWidget\|QComboBox\|QCheckBox\|QTabWidget" "$FILE"

echo
echo "Layouts:"
grep -n "QVBoxLayout\|QHBoxLayout\|QGridLayout\|QFormLayout" "$FILE"

echo
echo "Imports:"
head -30 "$FILE"

echo
echo "Compile:"
python -m py_compile "$FILE" && echo "OK"
