from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView,
    QAbstractItemView,
    QHBoxLayout,
)

from progress_dialog import ProgressDialog

from db_utils import fetch_all, execute_many
from system_state import SystemState
from event_bus import EventBus


class DivisionRulesPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20,20,20,20)
        layout.setSpacing(15)

        self.title = QLabel()
        self.title.setProperty("variant", "accent")

        layout.addWidget(self.title)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        layout.addWidget(self.table, 1)

        buttons = QHBoxLayout()

        self.save_btn = QPushButton("SAVE DIVISION RULES")
        self.reset_btn = QPushButton("RESTORE DEFAULTS")

        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.reset_btn)

        layout.addLayout(buttons)

        self.save_btn.clicked.connect(self.save_rules)
        self.reset_btn.clicked.connect(self.load_rules)

        EventBus.subscribe(
            "LEVEL_CHANGED",
            self.load_rules
        )

        self.ids = []

        self.load_rules()

    def load_rules(self):

        level = SystemState.get_level()

        self.title.setText(
            f"DIVISION RULES ({level.replace('_','-')})"
        )

        rows = fetch_all("""
            SELECT
                id,
                division,
                min_points,
                max_points
            FROM division_rules
            WHERE level=?
            ORDER BY min_points
        """,(level,))

        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            "Division",
            "Min Points",
            "Max Points"
        ])

        self.table.setRowCount(len(rows))

        self.ids=[]

        for r,row in enumerate(rows):

            self.ids.append(row[0])

            div = QTableWidgetItem(row[1])
            div.setFlags(
                div.flags() & ~div.flags().ItemIsEditable
            )

            self.table.setItem(r,0,div)
            self.table.setItem(r,1,QTableWidgetItem(str(row[2])))
            self.table.setItem(r,2,QTableWidgetItem(str(row[3])))

    def save_rules(self):

        updates=[]

        for row,id_ in enumerate(self.ids):

            try:
                mn=int(self.table.item(row,1).text())
                mx=int(self.table.item(row,2).text())
            except ValueError:

                QMessageBox.warning(
                    self,
                    "Invalid",
                    "Points must be numeric."
                )
                return

            if mn>mx:

                QMessageBox.warning(
                    self,
                    "Invalid",
                    "Minimum cannot exceed Maximum."
                )
                return

            updates.append(
                (mn,mx,id_)
            )

        execute_many("""
            UPDATE division_rules
            SET
                min_points=?,
                max_points=?
            WHERE id=?
        """,updates)

        QMessageBox.information(
            self,
            "Saved",
            "Division rules updated."
        )

        EventBus.emit(
            "DIVISION_RULES_CHANGED"
        )
