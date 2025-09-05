"""
Dialog für Spalteneinstellungen (show, Reihenfolge) für Matrix-View
- Zeigt alle Spalten in aktueller Reihenfolge (je nach Modus)
- Checkbox für show, Buttons für ↑/↓
- Synchronisiert displayOrder/expertOrder
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox, QLabel, QListWidget, QListWidgetItem, QWidget, QMessageBox
from PyQt5.QtCore import Qt
import copy

import logging
logger = logging.getLogger(__name__)

import pdvm_central_systemsteuerung_global
gcs = pdvm_central_systemsteuerung_global.central_systemsteuerung

class ColumnSettingsDialog(QDialog):
    def __init__(self, column_controls, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Spalteneinstellungen")
        self._original_column_controls = column_controls
        # WICHTIG: Deep Copy mit Sicherstellung aller notwendigen Felder
        self.column_controls = []
        for col in column_controls:
            col_copy = copy.deepcopy(col)
            # Stelle sicher, dass alle Order-Felder vorhanden sind
            col_copy['show'] = col_copy.get('show', False)
            col_copy['expertOrder'] = col_copy.get('expertOrder', 999)
            col_copy['displayOrder'] = col_copy.get('displayOrder', 999)
            self.column_controls.append(col_copy)
            
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
        """OK Button: Aktualisiere Order für aktuellen Modus und übernimmt Änderungen"""
        logger.info(f"🔄 Dialog accept - ExpertMode: {gcs.global_expert_mode}")
        logger.info(f"🔄 accept column_controls: {len(self.column_controls)} Spalten")
        
        try:
            if gcs.global_expert_mode:
                # ExpertMode: Alle Spalten nach expertOrder sortieren und Order neu setzen
                all_controls_sorted = sorted(self.column_controls, key=lambda c: c.get('expertOrder', 999))
                for i, c in enumerate(all_controls_sorted):
                    c['expertOrder'] = i
                    logger.debug(f"  {c['name']}: expertOrder={i}")
            else:
                # NormalMode: Nur show==True Spalten nach displayOrder sortieren und Order neu setzen  
                show_controls = [c for c in self.column_controls if c.get('show', False)]
                show_controls_sorted = sorted(show_controls, key=lambda c: c.get('displayOrder', 999))
                
                for i, c in enumerate(show_controls_sorted):
                    c['displayOrder'] = i
                    logger.debug(f"  {c['name']}: displayOrder={i}")
                
                # Versteckte Spalten bekommen hohe displayOrder-Werte
                hidden_controls = [c for c in self.column_controls if not c.get('show', False)]
                for i, c in enumerate(hidden_controls):
                    c['displayOrder'] = 1000 + i
                    
            self.result_controls = self.column_controls
            logger.info("✅ Spalten-Order erfolgreich aktualisiert")
            super().accept()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Accept: {e}")
            super().reject()

    def refresh_list(self):
        """Aktualisiert die Spaltenliste entsprechend dem aktuellen Modus"""
        self.list_widget.clear()
        
        logger.info(f"🔄 Spaltenliste wird aktualisiert - ExpertMode: {gcs.global_expert_mode}")
        logger.info(f"🔄 column_controls: {len(self.column_controls)} Spalten")
        
        try:
            # ZENTRALE PROJEKTION: Verwende dieselbe Logik wie die Tabelle
            from column_projection_helper import get_projected_columns
            projected_columns = get_projected_columns(self.column_controls)
            
            logger.info(f"  Modus: {len(projected_columns)} projizierte Spalten")
            
            # Erstelle Index-Mapping für interne Verarbeitung
            self._indices = []
            for projected_col in projected_columns:
                # Finde Index in self.column_controls
                for i, original_col in enumerate(self.column_controls):
                    if original_col['name'] == projected_col['name']:
                        self._indices.append(i)
                        break
                        
            for idx in self._indices:
                col = self.column_controls[idx]
                item = QListWidgetItem()
                
                if gcs.global_expert_mode:
                    # ExpertMode: Checkbox + Spaltenname
                    widget = QWidget()
                    layout = QHBoxLayout()
                    cb = QCheckBox()
                    cb.setChecked(col.get('show', False))
                    cb.stateChanged.connect(lambda state, c=col: self.toggle_show(c, state))
                    
                    label = QLabel(col.get('spaltenueberschrift', col['name']))
                    label.setAlignment(Qt.AlignLeft)  # Linksbündige Ausrichtung
                    order_label = QLabel(f"[E:{col.get('expertOrder', '?')}]")
                    
                    layout.addWidget(cb)
                    layout.addWidget(label, 1)  # Stretch-Faktor für Label
                    layout.addWidget(order_label)
                    layout.setContentsMargins(0,0,0,0)
                    widget.setLayout(layout)
                    
                    self.list_widget.addItem(item)
                    self.list_widget.setItemWidget(item, widget)
                else:
                    # NormalMode: Nur Spaltenname (alle sind bereits show==True)
                    widget = QWidget()
                    layout = QHBoxLayout()
                    
                    label = QLabel(col.get('spaltenueberschrift', col['name']))
                    label.setAlignment(Qt.AlignLeft)  # Linksbündige Ausrichtung
                    order_label = QLabel(f"[D:{col.get('displayOrder', '?')}]")
                    
                    layout.addWidget(label, 1)  # Stretch-Faktor für Label
                    layout.addWidget(order_label)
                    layout.setContentsMargins(0,0,0,0)
                    widget.setLayout(layout)
                    
                    self.list_widget.addItem(item)
                    self.list_widget.setItemWidget(item, widget)
                    
            self.update_move_buttons()
            logger.info("✅ Spaltenliste erfolgreich aktualisiert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der Spaltenliste: {e}")
            # Fallback: Leere Liste
            self.list_widget.clear()
            self._indices = []

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
        """Tauscht die Order-Werte zwischen zwei Spalten im aktuellen Modus"""
        logger.info(f"🔄 Tausche Position {idx1} <-> {idx2} (ExpertMode: {gcs.global_expert_mode})")
        
        try:
            # idx1, idx2 sind Indizes in self._indices (Sortierung im Dialog)
            i1 = self._indices[idx1]
            i2 = self._indices[idx2]
            
            # Bestimme welches Order-Feld verwendet wird
            if gcs.global_expert_mode:
                key = 'expertOrder'
                # Alle Spalten neu sortieren nach expertOrder
                relevant_controls = self.column_controls
            else:
                key = 'displayOrder'
                # Nur sichtbare Spalten neu sortieren nach displayOrder
                relevant_controls = [c for c in self.column_controls if c.get('show', False)]
                
            logger.info(f"  Verwende {key} für Tausch")
            
            # Stelle sicher, dass beide Spalten das Order-Feld haben
            for i, idx in enumerate([i1, i2]):
                if key not in self.column_controls[idx] or self.column_controls[idx][key] is None:
                    logger.warning(f"  {key} fehlt für Spalte {self.column_controls[idx]['name']}, setze Fallback-Wert")
                    self.column_controls[idx][key] = idx * 10  # Fallback-Wert
            
            # Tausche die Order-Werte
            old_val1 = self.column_controls[i1][key]
            old_val2 = self.column_controls[i2][key] 
            
            self.column_controls[i1][key] = old_val2
            self.column_controls[i2][key] = old_val1
            
            logger.info(f"  {self.column_controls[i1]['name']}: {old_val1} -> {old_val2}")
            logger.info(f"  {self.column_controls[i2]['name']}: {old_val2} -> {old_val1}")
            
            # WICHTIG: Nach dem Tauschen die Order-Werte für alle relevanten Spalten neu nummerieren
            # um saubere aufsteigende Reihenfolge zu gewährleisten
            if gcs.global_expert_mode:
                # ExpertMode: Alle Spalten nach expertOrder sortieren und Order neu setzen
                all_controls_sorted = sorted(self.column_controls, key=lambda c: c.get('expertOrder', 999))
                for i, c in enumerate(all_controls_sorted):
                    c['expertOrder'] = i
            else:
                # NormalMode: Nur show==True Spalten nach displayOrder sortieren und Order neu setzen  
                show_controls = [c for c in self.column_controls if c.get('show', False)]
                show_controls_sorted = sorted(show_controls, key=lambda c: c.get('displayOrder', 999))
                
                for i, c in enumerate(show_controls_sorted):
                    c['displayOrder'] = i
                    
                # Versteckte Spalten bekommen hohe displayOrder-Werte
                hidden_controls = [c for c in self.column_controls if not c.get('show', False)]
                for i, c in enumerate(hidden_controls):
                    c['displayOrder'] = 1000 + i
            
            # Liste neu aufbauen
            self.refresh_list()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Tauschen der Order-Werte: {e}")
            # Bei Fehler: Liste trotzdem neu laden
            self.refresh_list()

    def toggle_show(self, col, state):
        """Schaltet show-Status einer Spalte um (nur im ExpertMode verfügbar)"""
        logger.info(f"🔄 toggle_show für {col['name']}: {bool(state)}")
        
        try:
            col['show'] = bool(state)
            
            # displayOrder-Handling: Nur bei show==True relevante Order zuweisen
            if col['show']:
                # Füge am Ende der sichtbaren Spalten ein
                show_orders = [c.get('displayOrder', -1) for c in self.column_controls 
                              if c.get('show', False) and c is not col]
                new_order = max(show_orders, default=-1) + 1
                col['displayOrder'] = new_order
                logger.info(f"  {col['name']} sichtbar gemacht, displayOrder={new_order}")
            else:
                # Bei versteckten Spalten: Hohe displayOrder-Werte
                col['displayOrder'] = 1000 + len([c for c in self.column_controls if not c.get('show', False)])
                logger.info(f"  {col['name']} versteckt, displayOrder={col['displayOrder']}")
            
            # Liste neu aufbauen - WICHTIG: Nur wenn wir nicht im ExpertMode sind
            # Im ExpertMode bleiben alle Spalten sichtbar, nur die Checkbox ändert sich
            if not gcs.global_expert_mode:
                # Im NormalMode: Liste neu aufbauen, da sich die sichtbaren Spalten geändert haben
                self.refresh_list()
            else:
                # Im ExpertMode: Nur die Order-Labels aktualisieren (da sich displayOrder geändert hat)
                pass  # Die Checkbox ist bereits aktualisiert
            
        except Exception as e:
            logger.error(f"❌ Fehler beim toggle_show: {e}")
            # Bei Fehler: Liste trotzdem neu laden
            self.refresh_list()


