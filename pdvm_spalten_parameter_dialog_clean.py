"""
PDVM Spaltenparameter Dialog

Separates Fenster für die Verwaltung der Spaltenparameter.
Unterschiedliche Funktionalität für Normal-Mode und Expert-Mode.

Normal-Mode:
- Nur expert=false Spalten anzeigen
- show_show aktivieren/deaktivieren
- Reihenfolge mit Auf/Ab Buttons ändern
- show_order wird automatisch angepasst

Expert-Mode:
- Alle Spalten anzeigen
- expert Flag ändern
- show und order ändern
- Vollständige Kontrolle über alle Parameter
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
    Dialog für Spaltenparameter-Verwaltung
    
    Unterstützt Normal-Mode und Expert-Mode mit unterschiedlichen Funktionalitäten.
    """
    
    def __init__(self, parent=None, mode="normal", controls=None, provider=None, daten_manager=None, user_guid=None, view_config=None):
        """
        Initialisiert den Spaltenparameter Dialog
        
        Args:
            parent: Parent Widget
            mode: "normal" oder "expert"
            controls: Control-Struktur mit Spalten-Definitionen
            provider: PdvmValueViewProvider Instanz für Speicherung
            daten_manager: PdvmViewDatenManager Instanz für direkten Zugriff
            user_guid: User GUID für Systemsteuerung
            view_config: View-Konfiguration
        """
        super().__init__(parent)
        
        # Store parameters
        self.mode = mode
        self.controls = controls or {}
        self.provider = provider
        self.daten_manager = daten_manager
        self.user_guid = user_guid
        self.view_config = view_config
        
        # Working copy of columns
        self.working_columns = []
        
        self.setWindowTitle(f"Spaltenparameter ({'Expert' if mode == 'expert' else 'Normal'} Mode)")
        self.setModal(True)
        self.resize(800, 600)
        
        logger.info(f"🔧 Spaltenparameter-Dialog initialisiert - Mode: {mode}")
        
        self._init_data()
        self._setup_ui()
        self._load_data()
        
    def _init_data(self):
        """Initialisiert die Arbeitsdaten"""
        # Extract columns from controls
        if not self.controls or 'columns' not in self.controls:
            logger.warning("⚠️ Keine Spalten-Definitionen in controls gefunden")
            self.working_columns = []
            return
            
        all_columns = self.controls['columns']
        
        if self.mode == "normal":
            # Im Normal-Mode nur expert=false Spalten anzeigen
            self.working_columns = [col.copy() for col in all_columns if not col.get('expert', False)]
            logger.info(f"📊 Normal-Mode: {len(self.working_columns)} Spalten geladen")
        else:
            # Im Expert-Mode alle Spalten anzeigen
            self.working_columns = [col.copy() for col in all_columns]
            logger.info(f"🔧 Expert-Mode: {len(self.working_columns)} Spalten geladen")
    
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
        self._setup_table()
        layout.addWidget(self.table)
        
        # Buttons für Normal-Mode
        if self.mode == "normal":
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
        self.btn_cancel.clicked.connect(self._on_cancel)
        
        dialog_buttons.addStretch()
        dialog_buttons.addWidget(self.btn_ok)
        dialog_buttons.addWidget(self.btn_cancel)
        
        layout.addLayout(dialog_buttons)
        
        logger.info(f"✅ UI aufgebaut - Mode: {self.mode}")
    
    def _setup_table(self):
        """Konfiguriert die Tabelle je nach Mode"""
        if self.mode == "normal":
            # Normal-Mode: name, caption, show, order
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels(["Name", "Caption", "Anzeigen", "Reihenfolge"])
            column_widths = [150, 200, 80, 100]
        else:
            # Expert-Mode: name, caption, expert, show, order
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["Name", "Caption", "Expert", "Anzeigen", "Reihenfolge"])
            column_widths = [150, 200, 80, 80, 100]
        
        # Column widths
        for i, width in enumerate(column_widths):
            self.table.setColumnWidth(i, width)
        
        # Table properties
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
    
    def _load_data(self):
        """Lädt die Daten in die Tabelle"""
        if not self.working_columns:
            logger.warning("⚠️ Keine Spalten zum Laden vorhanden")
            return
            
        # Sort by show_order for initial display
        sorted_columns = sorted(self.working_columns, key=lambda x: x.get('show_order', 999))
        self.working_columns = sorted_columns
        
        self.table.setRowCount(len(self.working_columns))
        
        for row, column in enumerate(self.working_columns):
            self._populate_row(row, column)
        
        logger.info(f"📊 {len(self.working_columns)} Spalten in Tabelle geladen")
    
    def _populate_row(self, row, column):
        """Füllt eine Tabellenzeile mit Spaltendaten"""
        # Name (read-only)
        name_item = QTableWidgetItem(column.get('name', ''))
        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, 0, name_item)
        
        # Caption (read-only)
        caption_item = QTableWidgetItem(column.get('caption', ''))
        caption_item.setFlags(caption_item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, 1, caption_item)
        
        col_index = 2
        
        # Expert checkbox (nur im Expert-Mode)
        if self.mode == "expert":
            expert_item = QTableWidgetItem()
            expert_item.setCheckState(Qt.Checked if column.get('expert', False) else Qt.Unchecked)
            self.table.setItem(row, col_index, expert_item)
            col_index += 1
        
        # Show checkbox
        show_item = QTableWidgetItem()
        show_item.setCheckState(Qt.Checked if column.get('show', True) else Qt.Unchecked)
        self.table.setItem(row, col_index, show_item)
        col_index += 1
        
        # Order (nur im Expert-Mode editierbar)
        order_item = QTableWidgetItem(str(column.get('show_order', 0)))
        if self.mode == "normal":
            order_item.setFlags(order_item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, col_index, order_item)
    
    def _move_up(self):
        """Bewegt ausgewählte Zeile nach oben (Normal-Mode)"""
        current_row = self.table.currentRow()
        if current_row > 0:
            self._swap_rows(current_row, current_row - 1)
            self.table.setCurrentCell(current_row - 1, 0)
            self._update_order_display()
    
    def _move_down(self):
        """Bewegt ausgewählte Zeile nach unten (Normal-Mode)"""
        current_row = self.table.currentRow()
        if current_row < self.table.rowCount() - 1:
            self._swap_rows(current_row, current_row + 1)
            self.table.setCurrentCell(current_row + 1, 0)
            self._update_order_display()
    
    def _swap_rows(self, row1, row2):
        """Vertauscht zwei Zeilen in working_columns und Tabelle"""
        # Swap in working data
        self.working_columns[row1], self.working_columns[row2] = self.working_columns[row2], self.working_columns[row1]
        
        # Update table display
        self._populate_row(row1, self.working_columns[row1])
        self._populate_row(row2, self.working_columns[row2])
    
    def _update_order_display(self):
        """Aktualisiert die Order-Anzeige nach Positionsänderungen (Normal-Mode)"""
        for row in range(len(self.working_columns)):
            order_item = self.table.item(row, 3)  # Order ist Spalte 3 im Normal-Mode
            if order_item:
                order_item.setText(str(row + 1))
                self.working_columns[row]['show_order'] = row + 1
    
    def _update_display(self):
        """Aktualisiert die Tabellen-Anzeige"""
        for row, column in enumerate(self.working_columns):
            self._populate_row(row, column)
    
    def _on_cancel(self):
        """Explizite Cancel-Behandlung"""
        logger.info(f"🔄 Spaltenparameter-Dialog abgebrochen - Mode: {self.mode}")
        self.reject()
    
    def _apply_changes(self):
        """Übernimmt die Änderungen und speichert sie"""
        logger.info(f"💾 _apply_changes aufgerufen - Mode: {self.mode}")
        try:
            if not self.provider or not self.user_guid or not self.view_config:
                error_msg = f"Fehlende Parameter: provider={self.provider is not None}, user_guid={self.user_guid is not None}, view_config={self.view_config is not None}"
                logger.error(f"❌ {error_msg}")
                QMessageBox.warning(self, "Fehler", "Fehlende Parameter für das Speichern der Änderungen.")
                return
            
            logger.info(f"💾 Alle Parameter vorhanden, starte Speicherung...")
            
            # Im Expert-Mode: Order aus Tabelle übernehmen
            if self.mode == "expert":
                logger.info(f"💾 Expert-Mode: Übernehme Order aus Tabelle...")
                self._update_order_from_table()
            
            # Änderungen an den Provider weiterleiten
            logger.info(f"💾 Speichere über Provider...")
            success = self._save_to_provider()
            
            if success:
                logger.info(f"✅ Spaltenparameter erfolgreich gespeichert - Mode: {self.mode}")
                self.accept()
            else:
                logger.error(f"❌ Speichern fehlgeschlagen")
                QMessageBox.critical(self, "Fehler", "Fehler beim Speichern der Spaltenparameter.")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Übernehmen der Änderungen: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern: {e}")
    
    def _update_order_from_table(self):
        """Übernimmt Order-Werte aus der Tabelle (Expert-Mode)"""
        for row in range(len(self.working_columns)):
            order_item = self.table.item(row, 4)  # Order ist Spalte 4 im Expert-Mode
            if order_item:
                try:
                    order_value = int(order_item.text())
                    self.working_columns[row]['show_order'] = order_value
                except (ValueError, TypeError):
                    logger.warning(f"⚠️ Ungültiger Order-Wert in Zeile {row}: {order_item.text()}")
    
    def _save_to_provider(self) -> bool:
        """Speichert die Änderungen über den Provider"""
        try:
            logger.info(f"💾 Sammle Änderungen aus Tabelle...")
            
            # Collect changes from table
            for row in range(len(self.working_columns)):
                column = self.working_columns[row]
                
                col_index = 2
                
                # Expert flag (nur im Expert-Mode)
                if self.mode == "expert":
                    expert_item = self.table.item(row, col_index)
                    if expert_item:
                        column['expert'] = expert_item.checkState() == Qt.Checked
                    col_index += 1
                
                # Show flag
                show_item = self.table.item(row, col_index)
                if show_item:
                    column['show'] = show_item.checkState() == Qt.Checked
                col_index += 1
                
                # Order (bereits durch _update_order_from_table übernommen im Expert-Mode)
                if self.mode == "normal":
                    # Im Normal-Mode ist show_order bereits durch Position gesetzt
                    pass
            
            logger.info(f"💾 Rufe provider.save_spalten_parameter auf...")
            
            # Save via provider
            success = self.provider.save_spalten_parameter(
                user_guid=self.user_guid,
                view_config=self.view_config,
                columns=self.working_columns
            )
            
            if success:
                logger.info(f"✅ Provider-Speicherung erfolgreich")
                # Trigger data reload if daten_manager available
                if self.daten_manager:
                    logger.info(f"🔄 Triggere Datenaktualisierung...")
                    self.daten_manager._reload_data_after_save()
                return True
            else:
                logger.error(f"❌ Provider-Speicherung fehlgeschlagen")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern über Provider: {e}")
            import traceback
            traceback.print_exc()
            return False
