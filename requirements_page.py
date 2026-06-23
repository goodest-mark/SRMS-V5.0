import openpyxl
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, 
    QLabel, QLineEdit, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QGroupBox, QAbstractItemView
)
from PySide6.QtCore import Qt

from database import connect
from system_state import SystemState
from event_bus import EventBus
from class_utils import get_classes
import excel_utils


class RequirementsPage(QWidget):

    def __init__(self):
        super().__init__()

        self.selected_id = None
        self.layout = QVBoxLayout(self)

        title = QLabel("SCHOOL REQUIREMENTS MODULE")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        self.layout.addWidget(title)

        # =========================
        # FILTERS
        # =========================
        filters_group = QGroupBox("Context Filters")
        filters_layout = QHBoxLayout(filters_group)

        self.year_box = QComboBox()
        self.year_box.currentIndexChanged.connect(self.load_terms)
        self.year_box.currentIndexChanged.connect(self.load_data)

        self.term_box = QComboBox()
        self.term_box.currentIndexChanged.connect(self.load_data)

        self.level_box = QComboBox()
        self.level_box.addItems(["O_LEVEL", "A_LEVEL"])
        self.level_box.setCurrentText(SystemState.get_level())
        self.level_box.currentTextChanged.connect(self.on_level_filter_changed)

        self.class_box = QComboBox()
        self.class_box.currentIndexChanged.connect(self.load_data)

        filters_layout.addWidget(QLabel("Year:"))
        filters_layout.addWidget(self.year_box)
        filters_layout.addWidget(QLabel("Term:"))
        filters_layout.addWidget(self.term_box)
        filters_layout.addWidget(QLabel("Level:"))
        filters_layout.addWidget(self.level_box)
        filters_layout.addWidget(QLabel("Class:"))
        filters_layout.addWidget(self.class_box)
        filters_layout.addStretch()

        self.layout.addWidget(filters_group)

        # =========================
        # FORM
        # =========================
        form_group = QGroupBox("Requirement Item Entry")
        form_layout = QHBoxLayout(form_group)

        self.item_name = QLineEdit()
        self.item_name.setPlaceholderText("Item Name (e.g., Reams of Paper)")

        self.quantity = QLineEdit()
        self.quantity.setPlaceholderText("Quantity (e.g., 2)")

        self.notes = QLineEdit()
        self.notes.setPlaceholderText("Notes (Optional)")

        self.add_btn = QPushButton("ADD")
        self.add_btn.clicked.connect(self.save_item)

        self.update_btn = QPushButton("UPDATE")
        self.update_btn.setEnabled(False)
        self.update_btn.clicked.connect(self.save_item)

        self.delete_btn = QPushButton("DELETE")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_item)

        self.clear_btn = QPushButton("CLEAR")
        self.clear_btn.clicked.connect(self.clear_form)

        form_layout.addWidget(self.item_name)
        form_layout.addWidget(self.quantity)
        form_layout.addWidget(self.notes)
        form_layout.addWidget(self.add_btn)
        form_layout.addWidget(self.update_btn)
        form_layout.addWidget(self.delete_btn)
        form_layout.addWidget(self.clear_btn)

        self.layout.addWidget(form_group)

        # =========================
        # EXCEL ACTIONS
        # =========================
        excel_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("IMPORT")
        self.import_btn.clicked.connect(self.import_excel)
        
        self.export_btn = QPushButton("EXPORT")
        self.export_btn.clicked.connect(self.export_excel)
        
        self.template_btn = QPushButton("TEMPLATE")
        self.template_btn.clicked.connect(self.download_template)

        excel_layout.addStretch()
        excel_layout.addWidget(self.import_btn)
        excel_layout.addWidget(self.export_btn)
        excel_layout.addWidget(self.template_btn)
        
        self.layout.addLayout(excel_layout)

        # =========================
        # TABLE
        # =========================
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Item Name", "Quantity", "Notes"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self.load_selected)
        self.layout.addWidget(self.table)

        # =========================
        # INITIAL LOAD
        # =========================
        self.load_years()
        self.refresh_classes()
        self.load_data()

        EventBus.subscribe("LEVEL_CHANGED", self.on_system_level_changed)

    def on_system_level_changed(self):
        self.level_box.blockSignals(True)
        self.level_box.setCurrentText(SystemState.get_level())
        self.level_box.blockSignals(False)
        self.on_level_filter_changed()

    def on_level_filter_changed(self):
        self.refresh_classes()
        self.load_data()

    def refresh_classes(self):
        self.class_box.blockSignals(True)
        self.class_box.clear()
        
        level = self.level_box.currentText()
        classes_map = {
            "O_LEVEL": ["Form I", "Form II", "Form III", "Form IV"],
            "A_LEVEL": ["Form V", "Form VI"]
        }
        classes = classes_map.get(level, [])
        self.class_box.addItems(["-- All Classes --"] + classes)
        self.class_box.blockSignals(False)

    def load_years(self):
        self.year_box.blockSignals(True)
        self.year_box.clear()
        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT id, year_name FROM academic_years ORDER BY year_name DESC")
        for row in cur.fetchall():
            self.year_box.addItem(row[1], row[0])
        conn.close()
        self.year_box.blockSignals(False)
        self.load_terms()

    def load_terms(self):
        self.term_box.blockSignals(True)
        self.term_box.clear()
        year_id = self.year_box.currentData()
        if year_id:
            conn = connect()
            cur = conn.cursor()
            cur.execute("SELECT id, term_name FROM terms WHERE academic_year_id=? ORDER BY term_name", (year_id,))
            for row in cur.fetchall():
                self.term_box.addItem(row[1], row[0])
            conn.close()
        self.term_box.blockSignals(False)

    def load_data(self):
        year_id = self.year_box.currentData()
        term_id = self.term_box.currentData()
        level = self.level_box.currentText()
        class_name = self.class_box.currentText()

        if not (year_id and term_id):
            self.table.setRowCount(0)
            return

        conn = connect()
        cur = conn.cursor()

        query = "SELECT id, item_name, quantity, notes FROM requirements WHERE academic_year_id=? AND term_id=? AND level=?"
        params = [year_id, term_id, level]

        if class_name != "-- All Classes --":
            query += " AND class_name=?"
            params.append(class_name)
        
        query += " ORDER BY item_name ASC"
        
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        conn.close()

        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(val)))

    def save_item(self):
        item = self.item_name.text().strip()
        qty = self.quantity.text().strip()
        notes = self.notes.text().strip()
        
        year_id = self.year_box.currentData()
        term_id = self.term_box.currentData()
        level = self.level_box.currentText()
        class_name = self.class_box.currentText()

        if not item or not qty or class_name == "-- All Classes --":
            QMessageBox.warning(self, "Error", "Item Name, Quantity and a specific Class are required.")
            return

        conn = connect()
        cur = conn.cursor()

        try:
            if self.selected_id is None:
                cur.execute("""
                    INSERT INTO requirements (academic_year_id, term_id, level, class_name, item_name, quantity, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (year_id, term_id, level, class_name, item, qty, notes))
            else:
                cur.execute("""
                    UPDATE requirements 
                    SET item_name=?, quantity=?, notes=?
                    WHERE id=?
                """, (item, qty, notes, self.selected_id))
            
            conn.commit()
            self.clear_form()
            self.load_data()
            QMessageBox.information(self, "Success", "Requirement saved.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            conn.close()

    def load_selected(self):
        row = self.table.currentRow()
        if row < 0: return

        self.selected_id = int(self.table.item(row, 0).text())
        self.item_name.setText(self.table.item(row, 1).text())
        self.quantity.setText(self.table.item(row, 2).text())
        self.notes.setText(self.table.item(row, 3).text())

        self.add_btn.setEnabled(False)
        self.update_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

    def delete_item(self):
        if not self.selected_id: return
        
        reply = QMessageBox.question(self, "Confirm", "Delete this requirement?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No: return

        conn = connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM requirements WHERE id=?", (self.selected_id,))
        conn.commit()
        conn.close()
        
        self.clear_form()
        self.load_data()

    def clear_form(self):
        self.selected_id = None
        self.item_name.clear()
        self.quantity.clear()
        self.notes.clear()
        self.add_btn.setEnabled(True)
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

    # =========================
    # EXCEL FRAMEWORK
    # =========================

    def download_template(self):
        excel_utils.download_template(
            self, 
            "requirements_template.xlsx",
            "SCHOOL REQUIREMENTS TEMPLATE",
            ["Item Name*", "Quantity*", "Notes"],
            samples=["Reams of Paper", "2", "Urgently needed"]
        )

    def export_excel(self):
        year_id = self.year_box.currentData()
        term_id = self.term_box.currentData()
        level = self.level_box.currentText()
        class_name = self.class_box.currentText()
        
        if not (year_id and term_id):
            QMessageBox.warning(self, "Error", "Select Context first")
            return
            
        conn = connect()
        cur = conn.cursor()
        
        query = "SELECT item_name, quantity, notes FROM requirements WHERE academic_year_id=? AND term_id=? AND level=?"
        params = [year_id, term_id, level]
        if class_name != "-- All Classes --":
            query += " AND class_name=?"
            params.append(class_name)
            
        cur.execute(query, tuple(params))
        data = cur.fetchall()
        conn.close()
        
        excel_utils.export_to_excel(
            self, 
            "school_requirements.xlsx", 
            ["Item Name", "Quantity", "Notes"],
            data
        )

    def import_excel(self):
        year_id = self.year_box.currentData()
        term_id = self.term_box.currentData()
        level = self.level_box.currentText()
        class_name = self.class_box.currentText()
        
        if not (year_id and term_id) or class_name == "-- All Classes --":
            QMessageBox.warning(self, "Error", "Select a specific Context (Year, Term, Class) first")
            return
            
        path = excel_utils.get_import_file(self)
        if not path: return
        
        try:
            wb = openpyxl.load_workbook(path, data_only=True)
            sheet = wb.active
            rows = list(sheet.iter_rows(min_row=12, values_only=True))
            
            conn = connect()
            cur = conn.cursor()
            
            imported = 0
            for row in rows:
                if not row or len(row) < 3 or not row[0]: continue
                
                item = row[0]
                qty = row[1]
                notes = row[2]
                
                try:
                    cur.execute("""
                        INSERT INTO requirements (academic_year_id, term_id, level, class_name, item_name, quantity, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (year_id, term_id, level, class_name, str(item), str(qty), str(notes or "")))
                    imported += 1
                except Exception as e:
                    print(f"[ERROR] Failed to import requirement '{item}': {e}")
                    continue
                    
            conn.commit()
            conn.close()
            
            self.load_data()
            QMessageBox.information(self, "Import Complete", f"Imported {imported} requirement items.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed: {str(e)}")
