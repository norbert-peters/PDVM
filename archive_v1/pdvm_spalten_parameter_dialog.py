"""
PDVM Spaltenparameter Dialog - EINFACHE LÖSUNG

Basierend auf der klaren Logik:
1. Controls vom Provider als Basis (show_show/show_order oder show/order)
2. Dialog arbeitet mit display_* Feldern
3. OK schreibt display_* zurück in Controls
4. Provider persistiert und Tabelle wird neu aufgebaut
"""

import logging
from typing import Dict, List, Optional, Any
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QCheckBox,
                             QHeaderView, QAbstractItemView, QMessageBox)
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)

class PdvmSpaltenParameterDialog(QDialog):
    """
    EINFACHER Spaltenparameter Dialog
    
    Logik:
    - Lädt Controls vom Provider 
    - Arbeitet mit display_* Feldern
    - Schreibt bei OK zurück in Provider
    """
    
    def __init__(self, parent=None, mode="normal", daten_manager=None):
        """
        EINFACHE Initialisierung
        
        Args:
            parent: Parent Widget
            mode: "normal" oder "expert"
            daten_manager: PdvmViewDatenManager für Zugriff auf Provider
        """
        super().__init__(parent)
        
        self.mode = mode
        self.daten_manager = daten_manager
        self.working_columns = []
        
        self.setWindowTitle(f"Spaltenparameter ({'Expert' if mode == 'expert' else 'Normal'} Mode)")
        self.setModal(True)
        self.resize(800, 600)
        
        logger.info(f"🔧 Spaltenparameter-Dialog gestartet - Mode: {mode}")
        
        self._load_from_provider()
        self._setup_ui()
        self._populate_table()
        
    def _load_from_provider(self):
        """
        EINFACHE LÖSUNG: Lädt Spalten direkt vom Provider
        Keine komplexen Control-Manager - nur die API die der User wollte
        """
        try:
            # Spalten für aktuellen Mode vom Provider holen - DIREKTE API
            columns = self.daten_manager.get_columns_for_mode(self.mode)
            if not columns:
                logger.warning("⚠️ Keine Spalten vom Provider erhalten")
                self.working_columns = []
                return
            
            logger.info(f"📥 {len(columns)} Spalten vom Provider geladen")
            
            # Working columns vorbereiten - EINFACH
            self.working_columns = []
            for col in columns:
                # Deep copy für sichere Bearbeitung
                display_col = col.copy()
                
                # display_* Felder setzen - VEREINFACHT
                display_col['display_show'] = col.get('show', True)
                display_col['display_order'] = col.get('order', 999) 
                display_col['display_expert'] = col.get('expert', False)
                
                self.working_columns.append(display_col)
            
            # Nach display_order sortieren
            self.working_columns.sort(key=lambda x: x.get('display_order', 999))
            
            logger.info(f"✅ {len(self.working_columns)} Spalten geladen - EINFACHE LÖSUNG")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden vom Provider: {e}")
            self.working_columns = []
    
    def _setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        layout = QVBoxLayout(self)
        
        # Header
        mode_text = "Expert" if self.mode == "expert" else "Normal"
        header_label = QLabel(f"Spaltenparameter - {mode_text} Mode")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(header_label)
        
        # Table
        self.table = QTableWidget()
        self._setup_table_columns()
        layout.addWidget(self.table)
        
        # Bewegungs-Buttons (immer verfügbar)
        button_layout = QHBoxLayout()
        self.btn_up = QPushButton("↑ Nach oben")
        self.btn_down = QPushButton("↓ Nach unten")
        
        self.btn_up.clicked.connect(self._move_up)
        self.btn_down.clicked.connect(self._move_down)
        
        button_layout.addWidget(self.btn_up)
        button_layout.addWidget(self.btn_down)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Dialog Buttons
        dialog_buttons = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Abbrechen")
        
        self.btn_ok.clicked.connect(self._apply_changes)
        self.btn_cancel.clicked.connect(self.reject)
        
        dialog_buttons.addStretch()
        dialog_buttons.addWidget(self.btn_ok)
        dialog_buttons.addWidget(self.btn_cancel)
        
        layout.addLayout(dialog_buttons)
    
    def _setup_table_columns(self):
        """Konfiguriert Tabellenspalten je nach Mode"""
        if self.mode == "normal":
            # Normal-Mode: Name, Caption, Anzeigen, Reihenfolge
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels(["Name", "Caption", "Anzeigen", "Reihenfolge"])
        else:
            # Expert-Mode: Name, Caption, Expert, Anzeigen, Reihenfolge  
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["Name", "Caption", "Expert", "Anzeigen", "Reihenfolge"])
        
        # Table properties
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
    
    def _populate_table(self):
        """Füllt die Tabelle mit den working_columns"""
        if not self.working_columns:
            self.table.setRowCount(0)
            return
            
        self.table.setRowCount(len(self.working_columns))
        
        for row, column in enumerate(self.working_columns):
            self._populate_row(row, column)
    
    def _populate_row(self, row, column):
        """Füllt eine Tabellenzeile"""
        # Name (read-only)
        name_item = QTableWidgetItem(column.get('name', ''))
        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, 0, name_item)
        
        # Caption (read-only) 
        caption = column.get('anzeige', column.get('name', ''))
        caption_item = QTableWidgetItem(caption)
        caption_item.setFlags(caption_item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, 1, caption_item)
        
        col_idx = 2
        
        # Expert checkbox (nur im Expert-Mode)
        if self.mode == "expert":
            expert_item = QTableWidgetItem()
            expert_item.setCheckState(Qt.Checked if column.get('display_expert', False) else Qt.Unchecked)
            self.table.setItem(row, col_idx, expert_item)
            col_idx += 1
        
        # Anzeigen checkbox
        show_item = QTableWidgetItem()
        show_item.setCheckState(Qt.Checked if column.get('display_show', True) else Qt.Unchecked)
        self.table.setItem(row, col_idx, show_item)
        col_idx += 1
        
        # Reihenfolge (read-only, wird durch Buttons geändert)
        order_item = QTableWidgetItem(str(column.get('display_order', row + 1)))
        order_item.setFlags(order_item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, col_idx, order_item)
    
    def _move_up(self):
        """Bewegt ausgewählte Zeile nach oben (nur innerhalb sichtbarer Spalten)"""
        current_row = self.table.currentRow()
        if current_row <= 0:
            return
            
        # Prüfen ob beide Zeilen sichtbar sind (für Bewegung innerhalb des show-Bereichs)
        current_visible = self.working_columns[current_row].get('display_show', False)
        above_visible = self.working_columns[current_row - 1].get('display_show', False)
        
        if current_visible == above_visible:  # Beide sichtbar oder beide unsichtbar
            # Positionen tauschen
            self.working_columns[current_row], self.working_columns[current_row - 1] = \
                self.working_columns[current_row - 1], self.working_columns[current_row]
            
            self._update_display_orders()
            self._populate_table()
            self.table.setCurrentCell(current_row - 1, 0)
    
    def _move_down(self):
        """Bewegt ausgewählte Zeile nach unten (nur innerhalb sichtbarer Spalten)"""
        current_row = self.table.currentRow()
        if current_row >= len(self.working_columns) - 1:
            return
            
        # Prüfen ob beide Zeilen sichtbar sind (für Bewegung innerhalb des show-Bereichs) 
        current_visible = self.working_columns[current_row].get('display_show', False)
        below_visible = self.working_columns[current_row + 1].get('display_show', False)
        
        if current_visible == below_visible:  # Beide sichtbar oder beide unsichtbar
            # Positionen tauschen
            self.working_columns[current_row], self.working_columns[current_row + 1] = \
                self.working_columns[current_row + 1], self.working_columns[current_row]
            
            self._update_display_orders()
            self._populate_table()
            self.table.setCurrentCell(current_row + 1, 0)
    
    def _update_display_orders(self):
        """Aktualisiert display_order basierend auf aktueller Position"""
        for idx, column in enumerate(self.working_columns):
            column['display_order'] = idx + 1
    
    def _apply_changes(self):
        """Übernimmt Änderungen und speichert sie über den Provider"""
        try:
            logger.info(f"💾 Übernehme Spaltenparameter-Änderungen - Mode: {self.mode}")
            
            # Schritt 1: Änderungen aus Tabelle sammeln
            self._collect_table_changes()
            
            # Schritt 2: Automatische Sortierung bei Sichtbarkeitsänderungen
            self._handle_visibility_changes()
            
            # Schritt 3: Zurück in Provider-Controls schreiben
            self._write_back_to_provider()
            
            # Schritt 4: Optional - Daten neu laden (wenn Methode verfügbar)
            if hasattr(self.daten_manager, '_reload_data_after_save'):
                self.daten_manager._reload_data_after_save()
            
            logger.info(f"✅ Spaltenparameter erfolgreich gespeichert - Mode: {self.mode}")
            self.accept()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Spaltenparameter: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern: {e}")
    
    def _collect_table_changes(self):
        """Sammelt Änderungen aus der Tabelle"""
        for row in range(len(self.working_columns)):
            column = self.working_columns[row]
            
            col_idx = 2
            
            # Expert flag (nur im Expert-Mode)
            if self.mode == "expert":
                expert_item = self.table.item(row, col_idx)
                if expert_item:
                    column['display_expert'] = expert_item.checkState() == Qt.Checked
                col_idx += 1
            
            # Show flag
            show_item = self.table.item(row, col_idx)
            if show_item:
                column['display_show'] = show_item.checkState() == Qt.Checked
    
    def _handle_visibility_changes(self):
        """Behandelt automatische Sortierung bei Sichtbarkeitsänderungen"""
        visible_columns = []
        invisible_columns = []
        
        # Spalten nach Sichtbarkeit trennen
        for column in self.working_columns:
            if column.get('display_show', False):
                visible_columns.append(column)
            else:
                invisible_columns.append(column)
        
        # Sichtbare Spalten: Reihenfolge beibehalten, fortlaufend nummerieren
        for idx, column in enumerate(visible_columns):
            column['display_order'] = idx + 1
        
        # Unsichtbare Spalten: An das Ende, fortlaufend nummerieren
        for idx, column in enumerate(invisible_columns):
            column['display_order'] = len(visible_columns) + idx + 1
        
        # Neue Reihenfolge: Sichtbare zuerst, dann unsichtbare
        self.working_columns = visible_columns + invisible_columns
    
    def _write_back_to_provider(self):
        """
        EINFACHE LÖSUNG: Schreibt display_* Werte direkt an Provider zurück
        """
        try:
            # Spalten für Speichern vorbereiten - DIREKTE API
            columns_to_save = []
            
            for display_col in self.working_columns:
                # Kopie für Provider erstellen
                provider_col = display_col.copy()
                
                # display_* Werte in normale Felder übersetzen - VEREINFACHT
                provider_col['show'] = display_col.get('display_show', True)
                provider_col['order'] = display_col.get('display_order', 999)
                
                columns_to_save.append(provider_col)
            
            # Direkt an Provider senden - EINFACHE API
            success = self.daten_manager.save_columns_from_dialog(columns_to_save, self.mode)
            
            if success:
                logger.info(f"💾 {len(columns_to_save)} Spalten erfolgreich gespeichert - EINFACHE LÖSUNG")
            else:
                raise Exception("Provider konnte Spalten nicht speichern")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Zurückschreiben in Provider: {e}")
            raise
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Zurückschreiben in Provider: {e}")
            raise
