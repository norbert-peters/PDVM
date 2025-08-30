"""
Dialog für Spalteneinstellungen (show, Reihenfolge) für Matrix-View
- Zeigt alle Spalten in aktueller Reihenfolge (je nach Modus)
- Checkbox für show, Buttons für ↑/↓
- Synchronisiert displayOrder/expertOrder
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox, QLabel, QListWidget, QListWidgetItem, QWidget, QMessageBox
from PyQt5.QtCore import Qt
import copy

class ColumnSettingsDialog(QDialog):
    def __init__(self, column_controls, mode, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Spalteneinstellungen")
        self._original_column_controls = column_controls
        self.column_controls = copy.deepcopy(column_controls)  # Nur Kopie bearbeiten!
        self.mode = mode  # 'all' oder 'show'
        self.result_controls = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        # 1. Überschrift
        layout.addWidget(QLabel("Spalteneinstellungen:"))
        # 2. Spaltenliste
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)

        # Zentrale Verschiebebuttons (müssen vor refresh_list existieren)
        move_layout = QHBoxLayout()
        self.btn_up = QPushButton("↑")
        self.btn_down = QPushButton("↓")
        move_layout.addWidget(self.btn_up)
        move_layout.addWidget(self.btn_down)
        move_layout.addStretch()

        layout.addWidget(self.list_widget)
        layout.addLayout(move_layout)

        # OK/Abbrechen-Buttons
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Abbrechen")
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_up.clicked.connect(self.move_selected_up)
        self.btn_down.clicked.connect(self.move_selected_down)
        self.list_widget.currentRowChanged.connect(self.update_move_buttons)
        self.refresh_list()


    def accept(self):
        # Nach OK: displayOrder und expertOrder eindeutig und fortlaufend neu vergeben
        show_controls = [c for c in self.column_controls if c.get('show', False)]
        show_controls_sorted = sorted(show_controls, key=lambda c: c.get('displayOrder', 999))
        for i, c in enumerate(show_controls_sorted):
            c['displayOrder'] = i
        all_controls_sorted = sorted(self.column_controls, key=lambda c: c.get('expertOrder', 999))
        for i, c in enumerate(all_controls_sorted):
            c['expertOrder'] = i
        self.result_controls = self.column_controls
        super().accept()

    def refresh_list(self):
        self.list_widget.clear()
        # Sortierung je nach Modus, aber immer Referenz auf column_controls
        if self.mode == 'all':
            indices = sorted(range(len(self.column_controls)), key=lambda i: self.column_controls[i].get('expertOrder', 999))
        else:
            # Initialisiere fehlende displayOrder für show=True-Spalten
            show_indices = [i for i, c in enumerate(self.column_controls) if c.get('show', False)]
            # Vergib fortlaufende displayOrder, falls nicht vorhanden
            next_order = 0
            for i in sorted(show_indices, key=lambda i: self.column_controls[i].get('displayOrder', 999)):
                c = self.column_controls[i]
                if c.get('displayOrder') is None:
                    c['displayOrder'] = next_order
                next_order += 1
            indices = sorted(show_indices, key=lambda i: self.column_controls[i].get('displayOrder', 999))
        self._indices = indices
        for idx in self._indices:
            col = self.column_controls[idx]
            item = QListWidgetItem()
            # 2. Trenne Checkbox und Text, Checkbox nur im 'all'-Modus
            if self.mode == 'all':
                widget = QWidget()
                layout = QHBoxLayout()
                cb = QCheckBox()
                cb.setChecked(col.get('show', False))
                cb.stateChanged.connect(lambda state, c=col: self.toggle_show(c, state))
                label = QLabel(col['name'])
                layout.addWidget(cb)
                layout.addWidget(label)
                layout.addStretch()
                layout.setContentsMargins(0,0,0,0)
                widget.setLayout(layout)
                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, widget)
            else:
                # Nur Text, keine Checkbox im show-Modus
                label = QLabel(col['name'])
                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, label)
        self.update_move_buttons()

    def update_move_buttons(self):
        row = self.list_widget.currentRow()
        self.btn_up.setEnabled(row > 0)
        self.btn_down.setEnabled(row >= 0 and row < self.list_widget.count() - 1)

    def move_selected_up(self):
        row = self.list_widget.currentRow()
        if row > 0:
            self.swap_order(row, row - 1)
            self.list_widget.setCurrentRow(row - 1)

    def move_selected_down(self):
        row = self.list_widget.currentRow()
        if row < self.list_widget.count() - 1:
            self.swap_order(row, row + 1)
            self.list_widget.setCurrentRow(row + 1)

    def swap_order(self, idx1, idx2):
        # idx1, idx2 sind Indizes in self._indices (Sortierung im Dialog)
        i1 = self._indices[idx1]
        i2 = self._indices[idx2]
        if self.mode == 'all':
            key = 'expertOrder'
        else:
            key = 'displayOrder'
        self.column_controls[i1][key], self.column_controls[i2][key] = self.column_controls[i2][key], self.column_controls[i1][key]
        self.refresh_list()

    def toggle_show(self, col, state):
        col['show'] = bool(state)
        # displayOrder-Handling
        if col['show']:
            # Füge am Ende der show-Spalten ein
            show_orders = [c.get('displayOrder', -1) for c in self.column_controls if c.get('show', False) and c is not col]
            col['displayOrder'] = max(show_orders, default=-1) + 1
        else:
            col['displayOrder'] = None
        self.refresh_list()

    def move_up(self, idx):
        # Sortiere nach aktuellem Modus
        if self.mode == 'all':
            key = 'expertOrder'
        else:
            key = 'displayOrder'
        controls = sorted(self.column_controls, key=lambda c: c.get(key, 999))
        if idx > 0:
            controls[idx][key], controls[idx-1][key] = controls[idx-1][key], controls[idx][key]
        self.refresh_list()

    def move_down(self, idx):
        if self.mode == 'all':
            key = 'expertOrder'
        else:
            key = 'displayOrder'
        controls = sorted(self.column_controls, key=lambda c: c.get(key, 999))
        if idx < len(controls)-1:
            controls[idx][key], controls[idx+1][key] = controls[idx+1][key], controls[idx][key]
        self.refresh_list()
