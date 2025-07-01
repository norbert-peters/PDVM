# pdvm_object_search_widget.py
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableView, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem


class PdvmObjectSearchWidget(QDialog):
    recordSelected = pyqtSignal(dict)  # gibt z. B. GUID + HIST zurück

    def __init__(self, table_data, columns, hist=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Datensatz auswählen")
        self.resize(700, 400)

        self.columns = columns
        self.hist = hist
        self.table_data = table_data  # Liste von Dicts [{...}]
        self.filtered_data = list(self.table_data)  # Start = alle Daten

        self.filters = [QLineEdit() for _ in columns]
        self.table_view = QTableView()
        self.model = QStandardItemModel()

        self.selected_row = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Suchfelder
        filter_layout = QHBoxLayout()
        for i, col in enumerate(self.columns):
            filter_edit = self.filters[i]
            filter_edit.setPlaceholderText(f"Suche {col}")
            filter_edit.textChanged.connect(self.apply_filters)
            filter_layout.addWidget(filter_edit)
        layout.addLayout(filter_layout)

        # Tabelle
        self.table_view.setModel(self.model)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.clicked.connect(self.row_selected)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_view)

        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("Übernehmen")
        self.ok_button.clicked.connect(self.accept_selection)
        self.ok_button.setEnabled(False)
        cancel_button = QPushButton("Abbrechen")
        cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.populate_table()

    def apply_filters(self):
        self.filtered_data = []
        for row in self.table_data:
            match = True
            for i, col in enumerate(self.columns):
                value = str(row.get(col, "")).lower()
                if self.filters[i].text().lower() not in value:
                    match = False
                    break
            if match:
                self.filtered_data.append(row)
        self.populate_table()

    def populate_table(self):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(self.columns)
        for row in self.filtered_data:
            items = [QStandardItem(str(row.get(col, ""))) for col in self.columns]
            for item in items:
                item.setEditable(False)
            self.model.appendRow(items)
        self.ok_button.setEnabled(False)

    def row_selected(self, index):
        row_index = index.row()
        if row_index < len(self.filtered_data):
            self.selected_row = self.filtered_data[row_index]
            self.ok_button.setEnabled(True)

    def accept_selection(self):
        if self.selected_row:
            result = {
                "GUID": self.selected_row.get("GUID"),
                "HIST": self.selected_row.get("HIST", None) if self.hist else None
            }
            self.recordSelected.emit(result)
            self.accept()
        else:
            QMessageBox.warning(self, "Keine Auswahl", "Bitte wählen Sie einen Datensatz aus.")
