"""
Prototyp: Matrix-basierter ViewWidget und DatenManager
- Basistabelle bleibt immer vollständig (alle Spalten, alle Zeilen)
- Projektion (Anzeige) wird dynamisch aus ColumnControls erzeugt
- Zwei Modi: 'all' (alle Spalten), 'show' (nur show=True)
- Einfach testbar und erweiterbar
"""

import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem

logger = logging.getLogger(__name__)


class PdvmViewDatenManagerMatrix:
    def __init__(self, base_matrix, column_controls, abdatum_matrix=None):
        """
        base_matrix: List[List[Any]]
            - Erste Zeile: Spaltennamen
            - Weitere Zeilen: Daten
        column_controls: List[dict]
            - Dicts mit Attributen: name, show, order, etc.
        abdatum_matrix: List[List[Any]]
            - Gleiche Struktur wie base_matrix (außer Kopfzeile), enthält zu jedem Wert das abdatum
        """
        self.base_matrix = base_matrix
        self.column_controls = column_controls
        self.abdatum_matrix = abdatum_matrix

    def get_projection(self, mode='show'):
        import pprint
        headers = self.base_matrix[0]
        data_rows = self.base_matrix[1:]
        abdatum_rows = self.abdatum_matrix if self.abdatum_matrix is not None else None
        if mode == 'all':
            # Sortiere nach expertOrder
            controls_sorted = sorted(self.column_controls, key=lambda c: c.get('expertOrder', 999))
            col_names = [c['name'] for c in controls_sorted]
            col_indices = [headers.index(name) for name in col_names if name in headers]
            proj_headers = [headers[i] for i in col_indices]
            print("[DEBUG] get_projection (all): Reihenfolge nach expertOrder:")
            pprint.pprint(col_names)
        else:
            # Sortiere nach displayOrder
            controls_sorted = sorted([c for c in self.column_controls if c.get('show', False)], key=lambda c: c.get('displayOrder', 999))
            col_names = [c['name'] for c in controls_sorted]
            col_indices = [headers.index(name) for name in col_names if name in headers]
            proj_headers = [headers[i] for i in col_indices]
            print("[DEBUG] get_projection (show): Reihenfolge nach displayOrder:")
            pprint.pprint(col_names)
        proj_data = [[row[i] for i in col_indices] for row in data_rows]
        proj_abdatum = None
        if abdatum_rows is not None:
            proj_abdatum = [[row[i] for i in col_indices] for row in abdatum_rows]
        return proj_headers, proj_data, proj_abdatum


class PdvmViewWidgetMatrix(QWidget):
    def __init__(self, daten_manager: PdvmViewDatenManagerMatrix, mode='show', parent=None):
        super().__init__(parent)
        self.daten_manager = daten_manager
        self.mode = mode
        self.table = QTableWidget()
        from PyQt5.QtWidgets import QPushButton, QHBoxLayout
        layout = QVBoxLayout()
        # Modus-Schalter
        btn_layout = QHBoxLayout()
        self.btn_mode = QPushButton(f"Modus: {self.mode}")
        self.btn_mode.clicked.connect(self.toggle_mode)
        btn_layout.addWidget(self.btn_mode)
        # Spalten-Einstellungen
        self.btn_settings = QPushButton("Spalten-Einstellungen ...")
        self.btn_settings.clicked.connect(self.open_column_settings)
        btn_layout.addWidget(self.btn_settings)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.reload()

    def toggle_mode(self):
        self.mode = 'all' if self.mode == 'show' else 'show'
        self.btn_mode.setText(f"Modus: {self.mode}")
        self.reload()

    def open_column_settings(self):
        from pdvm_view_column_settings_dialog import ColumnSettingsDialog
        dlg = ColumnSettingsDialog(self.daten_manager.column_controls, self.mode, self)
        if dlg.exec_() and dlg.result_controls is not None:
            # Übernehme die geänderten Controls und baue Tabelle neu
            self.daten_manager.column_controls.clear()
            self.daten_manager.column_controls.extend(dlg.result_controls)
            self.reload()

    def reload(self):
        # Komplettes TableWidget ersetzen (wie Widget-Neuaufbau)
        from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
        headers, data, abdatum = self.daten_manager.get_projection(self.mode)
        old_table = self.table
        self.table = QTableWidget()
        self.table.setRowCount(len(data))
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels([str(h) for h in headers])
        for row_idx, row in enumerate(data):
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                if abdatum is not None:
                    ab_value = abdatum[row_idx][col_idx]
                    if ab_value is not None:
                        item.setToolTip(f"abdatum: {ab_value}")
                self.table.setItem(row_idx, col_idx, item)
        self.table.resizeColumnsToContents()
        # Altes TableWidget im Layout ersetzen
        layout = self.layout()
        layout.removeWidget(old_table)
        old_table.setParent(None)
        layout.addWidget(self.table)
        logger.info(f"Matrix-View geladen: {len(data)} Zeilen, {len(headers)} Spalten im Modus '{self.mode}'")
