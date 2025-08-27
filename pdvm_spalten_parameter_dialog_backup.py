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
- show und order ände    de        logger.info(f"💾 _apply_changes aufgerufen - Mode: {self.mode}")
        
        try:ply_changes(self):
        """Übernimmt die Änderungen und speichert sie"""
        logger.info(f"💾 _apply_changes aufgerufen - Mode: {self.mode}")
        
        try:   logger.info(f"💾 _apply_changes aufgerufen - Mode: {self.mode}")Vollständige Kontrolle über alle Parameter
"""

import logging
from typing import Dict, List, Optional, Any
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QCheckBox,
                             QHeaderView, QAbstractItemView, QMessageBox, QApplication)
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
        
        self.mode = mode
        self.controls = controls
        self.provider = provider
        self.daten_manager = daten_manager
        self.user_guid = user_guid
        self.view_config = view_config
        
        # Arbeits-Kopie der Spalten-Daten
        self.working_columns = []
        self._prepare_working_data()
        
        self.setWindowTitle(f"Spaltenparameter - {mode.title()}-Mode")
        self.setModal(True)
        self.resize(800, 600)
        
        self._setup_ui()
        self._load_data()
        
        logger.info(f"🔧 Spaltenparameter Dialog geöffnet - Mode: {mode}")
    
    def _get_columns_from_provider(self):
        """Fallback: Holt Spalten direkt vom Provider wenn Controls nicht funktioniert"""
        try:
            logger.info("📥 Fallback: Lade Spalten direkt vom Provider...")
            
            # Provider direkt nutzen um Spalten zu laden
            # Verwende die gleiche Methode wie im ViewManager
            data_result = self.provider.get_value_view(
                view_guid=self.view_config['view_guid'],
                user_guid=self.user_guid,
                frame_guid=self.frame_guid,
                stichtag=self.view_config.get('stichtag'),
                mode=self.mode
            )
            
            logger.debug(f"[_get_columns_from_provider] Provider data_result: {type(data_result)}")
            
            if data_result and hasattr(data_result, 'controls') and data_result.controls:
                logger.info(f"📥 Provider lieferte Controls mit {len(data_result.controls.columns)} Spalten")
                
                # Controls vom Provider verarbeiten
                for idx, column in enumerate(data_result.controls.columns):
                    col_dict = {
                        'name': getattr(column, 'name', str(column)),
                        'visible': getattr(column, 'show_show', getattr(column, 'visible', True)),
                        'order': getattr(column, 'show_order', getattr(column, 'order', idx + 1)),
                        'expert': getattr(column, 'expert', False)
                    }
                    self.working_columns.append(col_dict)
                    logger.debug(f"[_get_columns_from_provider] Column {idx}: {col_dict}")
                
                # Im Normal-Mode filtern
                if self.mode == "normal":
                    original_count = len(self.working_columns)
                    self.working_columns = [
                        col for col in self.working_columns 
                        if not col.get('expert', False) and col.get('name', '') != 'dummy'
                    ]
                    logger.info(f"📥 Normal-Mode Filter: {original_count} → {len(self.working_columns)} Spalten")
                
                logger.info(f"✅ Fallback erfolgreich: {len(self.working_columns)} Spalten geladen")
            else:
                logger.error("❌ Provider lieferte keine brauchbaren Controls")
                # Notfall-Fallback: Leere Struktur
                self.working_columns = []
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Spalten vom Provider: {e}")
            self.working_columns = []

    def _prepare_working_data(self):
        """
        EINFACHE Datenaufbereitung: Direkt die Controls vom DatenManager verwenden
        """
        logger.info(f"🔧 _prepare_working_data gestartet - Mode: {self.mode}")
        
        try:
            # Dialog-Controls vom DatenManager holen (mit display_* Feldern)
            current_controls = self.daten_manager.get_current_controls(for_dialog=True)
            
            if not current_controls or not hasattr(current_controls, 'columns'):
                logger.error("❌ Keine gültigen Controls vom DatenManager erhalten")
                self.working_columns = []
                return
            
            logger.info(f"✅ Controls erhalten: {len(current_controls.columns)} Spalten")
            
            # Controls DIREKT verwenden - Dialog arbeitet mit display_* Feldern!
            self.working_columns = []
            
            for idx, column in enumerate(current_controls.columns):
                # Dialog arbeitet mit display_* Feldern für einheitliche Handhabung
                col_dict = {
                    'name': column.get('name', f'Spalte_{idx}'),
                    'anzeige': column.get('anzeige', column.get('name', f'Spalte_{idx}')),
                    'visible': column.get('display_show', True),  # Dialog verwendet display_show
                    'order': column.get('display_order', idx + 1),  # Dialog verwendet display_order
                    'expert': column.get('expert', False),
                    'type': column.get('type', 'unknown'),
                    # Zusatz-Info für Debug
                    'show_show': column.get('show_show', True),  # Normal-Mode Original
                    'show': column.get('show', True),  # Expert-Mode Original
                    'show_order': column.get('show_order', idx + 1),  # Normal-Mode Original Order
                    'order_original': column.get('order', idx + 1),  # Expert-Mode Original Order
                }
                self.working_columns.append(col_dict)
                
                logger.debug(f"[_prepare_working_data] Spalte {idx}: {col_dict['name']} - show={col_dict['visible']} - display_order={col_dict['order']} - show_order={col_dict['show_order']} - expert={col_dict['expert']}")
            
            # Im Normal-Mode nur expert=false Spalten (ohne dummy)
            if self.mode == "normal":
                original_count = len(self.working_columns)
                self.working_columns = [
                    col for col in self.working_columns 
                    if not col.get('expert', False) and col.get('name', '') != 'dummy'
                ]
                logger.info(f"📋 Normal-Mode Filter: {original_count} → {len(self.working_columns)} Spalten")
            
            # Nach display_order sortieren (Dialog-Einheitlichkeit)
            self.working_columns.sort(key=lambda x: x.get('order', 999))
            logger.info(f"📋 Spalten nach display_order sortiert")
            
            logger.info(f"✅ {len(self.working_columns)} Spalten für {self.mode}-Mode vorbereitet")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Vorbereiten der Daten: {e}")
            self.working_columns = []
    
    def _setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel(f"Spaltenparameter - {self.mode.title()}-Mode")
        header_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(header_label)
        
        # Info-Text je nach Mode
        if self.mode == "normal":
            info_text = "Aktivieren/Deaktivieren Sie die Spalten und ändern Sie die Reihenfolge."
        else:
            info_text = "Vollständige Kontrolle über alle Spalten, Expert-Flags und Reihenfolge."
        
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: #666; margin: 5px 10px;")
        layout.addWidget(info_label)
        
        # Tabelle
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.table)
        
        # Button-Layout
        button_layout = QHBoxLayout()
        
        # Reihenfolge-Buttons
        self.btn_up = QPushButton("▲ Nach oben")
        self.btn_down = QPushButton("▼ Nach unten")
        self.btn_up.clicked.connect(self._move_up)
        self.btn_down.clicked.connect(self._move_down)
        
        button_layout.addWidget(self.btn_up)
        button_layout.addWidget(self.btn_down)
        button_layout.addStretch()
        
        # Dialog-Buttons
        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_ok.clicked.connect(self._apply_changes)
        self.btn_cancel.clicked.connect(self._on_cancel)
        
        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(button_layout)
        
        # Tabelle konfigurieren
        self._setup_table()
    
    def _setup_table(self):
        """Konfiguriert die Tabelle je nach Mode"""
        if self.mode == "normal":
            # Normal-Mode: Spalte, Anzeige, Sichtbar, Reihenfolge
            headers = ["Spalte", "Anzeige", "Sichtbar", "Reihenfolge"]
            self.table.setColumnCount(4)
        else:
            # Expert-Mode: Spalte, Anzeige, Expert, Sichtbar, Order, Reihenfolge
            headers = ["Spalte", "Anzeige", "Expert", "Sichtbar", "Order", "Reihenfolge"]
            self.table.setColumnCount(6)
        
        self.table.setHorizontalHeaderLabels(headers)
        
        # Spalten-Breiten
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Spalte
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Anzeige
        
        if self.mode == "expert":
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Expert
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Sichtbar
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Order
            header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Reihenfolge
        else:
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Sichtbar
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Reihenfolge
    
    def _load_data(self):
        """Lädt die Spalten-Daten in die Tabelle"""
        # Sortierung je nach Mode
        if self.mode == "normal":
            # Normal-Mode: nach show_order sortieren
            sorted_columns = sorted(self.working_columns, key=lambda x: x.get('show_order', 999))
        else:
            # Expert-Mode: nach order, dann show sortieren
            sorted_columns = sorted(self.working_columns, key=lambda x: (x.get('order', 0), not x.get('show', False)))
        
        self.working_columns = sorted_columns
        self.table.setRowCount(len(sorted_columns))
        
        for row, column in enumerate(sorted_columns):
            self._populate_row(row, column)
        
        logger.info(f"📊 Tabelle geladen: {len(sorted_columns)} Spalten")
    
    def _populate_row(self, row, column):
        """Füllt eine Tabellenzeile mit Spalten-Daten"""
        col_idx = 0
        
        # Spaltenname
        name_item = QTableWidgetItem(column.get('name', ''))
        name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.table.setItem(row, col_idx, name_item)
        col_idx += 1
        
        # Anzeige
        anzeige_item = QTableWidgetItem(column.get('anzeige', ''))
        anzeige_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.table.setItem(row, col_idx, anzeige_item)
        col_idx += 1
        
        # Expert-Flag (nur im Expert-Mode)
        if self.mode == "expert":
            expert_checkbox = QCheckBox()
            expert_checkbox.setChecked(column.get('expert', False))
            expert_checkbox.stateChanged.connect(lambda state, r=row: self._on_expert_changed(r, state))
            self.table.setCellWidget(row, col_idx, expert_checkbox)
            col_idx += 1
        
        # Sichtbar (show_show im Normal-Mode, show im Expert-Mode)
        show_checkbox = QCheckBox()
        if self.mode == "normal":
            # Normal-Mode: verwende 'visible' (wird von show_show gesteuert)
            show_checkbox.setChecked(column.get('visible', True))
            show_checkbox.stateChanged.connect(lambda state, r=row: self._on_show_show_changed(r, state))
        else:
            # Expert-Mode: verwende 'visible' (wird von show gesteuert)
            show_checkbox.setChecked(column.get('visible', True))
            show_checkbox.stateChanged.connect(lambda state, r=row: self._on_show_changed(r, state))
        self.table.setCellWidget(row, col_idx, show_checkbox)
        col_idx += 1
        
        # Order (nur im Expert-Mode)
        if self.mode == "expert":
            order_item = QTableWidgetItem(str(column.get('order', 0)))
            order_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
            self.table.setItem(row, col_idx, order_item)
            col_idx += 1
        
        # Aktuelle Reihenfolge
        if self.mode == "normal":
            reihenfolge_item = QTableWidgetItem(str(column.get('order', 0)))  # order ist die display_order!
        else:
            reihenfolge_item = QTableWidgetItem(str(row + 1))
        reihenfolge_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.table.setItem(row, col_idx, reihenfolge_item)
    
    def _on_show_show_changed(self, row, state):
        """Behandelt Änderungen der show_show Checkbox im Normal-Mode"""
        if row < len(self.working_columns):
            is_checked = state == Qt.Checked
            # WICHTIG: Im Normal-Mode ändern wir 'visible' 
            self.working_columns[row]['visible'] = is_checked
            
            # Reihenfolge anpassen
            self._reorder_normal_mode()
            self._refresh_table()
            
            logger.debug(f"🔄 visible (show_show) geändert für Spalte {self.working_columns[row].get('name', '')}: {is_checked}")
    
    def _on_show_changed(self, row, state):
        """Behandelt Änderungen der show Checkbox im Expert-Mode"""
        if row < len(self.working_columns):
            is_checked = state == Qt.Checked
            # WICHTIG: Im Expert-Mode ändern wir 'visible' 
            self.working_columns[row]['visible'] = is_checked
            
            logger.debug(f"🔄 visible (show) geändert für Spalte {self.working_columns[row].get('name', '')}: {is_checked}")
    
    def _on_expert_changed(self, row, state):
        """Behandelt Änderungen der Expert Checkbox im Expert-Mode"""
        if row < len(self.working_columns):
            is_checked = state == Qt.Checked
            self.working_columns[row]['expert'] = is_checked
            
            # WICHTIG: expert-Änderung auch in original_column übertragen
            original_col = self.working_columns[row].get('original_column')
            if original_col is not None:
                original_col['expert'] = is_checked
            
            logger.debug(f"🔄 expert geändert für Spalte {self.working_columns[row].get('name', '')}: {is_checked}")
    
    def _reorder_normal_mode(self):
        """Ordnet Spalten im Normal-Mode neu: erst visible=true, dann false"""
        visible_true = [col for col in self.working_columns if col.get('visible', False)]
        visible_false = [col for col in self.working_columns if not col.get('visible', False)]
        
        # Neue Reihenfolge
        self.working_columns = visible_true + visible_false
        
        # order neu setzen (entspricht show_order)
        for i, col in enumerate(self.working_columns):
            col['order'] = i + 1
    
    def _move_up(self):
        """Bewegt die ausgewählte Spalte nach oben"""
        current_row = self.table.currentRow()
        if current_row > 0:
            # Spalten in der Liste tauschen
            self.working_columns[current_row], self.working_columns[current_row - 1] = \
                self.working_columns[current_row - 1], self.working_columns[current_row]
            
            # order anpassen (entspricht show_order)
            if self.mode == "normal":
                for i, col in enumerate(self.working_columns):
                    col['order'] = i + 1
            
            self._refresh_table()
            self.table.selectRow(current_row - 1)
            
            logger.debug(f"📈 Spalte nach oben bewegt: Row {current_row} → {current_row - 1}")
    
    def _move_down(self):
        """Bewegt die ausgewählte Spalte nach unten"""
        current_row = self.table.currentRow()
        if current_row < len(self.working_columns) - 1:
            # Spalten in der Liste tauschen
            self.working_columns[current_row], self.working_columns[current_row + 1] = \
                self.working_columns[current_row + 1], self.working_columns[current_row]
            
            # order anpassen (entspricht show_order)
            if self.mode == "normal":
                for i, col in enumerate(self.working_columns):
                    col['order'] = i + 1
            
            self._refresh_table()
            self.table.selectRow(current_row + 1)
            
            logger.debug(f"📉 Spalte nach unten bewegt: Row {current_row} → {current_row + 1}")
    
    def _refresh_table(self):
        """Aktualisiert die Tabellen-Anzeige"""
        for row, column in enumerate(self.working_columns):
            self._populate_row(row, column)
    
    def _on_cancel(self):
        """Explizite Cancel-Behandlung mit Debug-Logs"""
        logger.info(f"🔄 Spaltenparameter-Dialog abgebrochen - Mode: {self.mode}")
        self.reject()
    
    def _apply_changes(self):
        """Übernimmt die Änderungen und speichert sie"""
        logger.info(f"� CRITICAL: _apply_changes wurde aufgerufen! - Mode: {self.mode}")
        logger.info(f"🚀 CRITICAL: Thread: {QApplication.instance().thread()}")
        logger.info(f"🚀 CRITICAL: Button sender: {self.sender()}")
        
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
                    self.working_columns[row]['order'] = order_value
                except (ValueError, TypeError):
                    logger.warning(f"⚠️ Ungültiger Order-Wert in Zeile {row}: {order_item.text()}")
    
    def _save_to_provider(self):
        """
        EINFACHE Speicher-Methode: Direkt über den DatenManager
        Aktualisiert auch die display_order in den Original-Controls
        """
        try:
            logger.info(f"💾 Speichere über DatenManager - Mode: {self.mode}")
            logger.info(f"💾 Zu speichern: {len(self.working_columns)} Spalten")
            
            # WICHTIG: ALLE Änderungen in Original-Controls übertragen
            self._update_controls_with_changes()
            
            # DIREKT über den DatenManager speichern
            if hasattr(self.daten_manager, 'save_column_configuration'):
                success = self.daten_manager.save_column_configuration(self.working_columns, self.mode)
                
                if success:
                    logger.info(f"✅ Erfolgreich über DatenManager gespeichert")
                    return True
                else:
                    logger.error(f"❌ DatenManager konnte nicht speichern")
                    return False
            else:
                logger.error(f"❌ DatenManager hat keine save_column_configuration Methode")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
            return False
    
    def _update_controls_with_changes(self):
        """Überträgt ALLE Änderungen aus working_columns zurück in die Original-Controls"""
        try:
            # Durch alle bearbeiteten Spalten gehen
            for working_col in self.working_columns:
                col_name = working_col.get('name')
                new_order = working_col.get('order', 1)
                new_visible = working_col.get('visible', True)
                new_expert = working_col.get('expert', False)
                
                # Im Original-Control die Werte setzen
                original_col = working_col.get('original_column')
                if original_col is not None:
                    # WICHTIG: Sowohl display_order als auch show übertragen!
                    original_col['display_order'] = new_order
                    original_col['show'] = new_visible  # Das ist der wichtige Teil!
                    original_col['expert'] = new_expert  # Expert-Flag auch
                    
                    # Zusätzlich: show_order für Legacy-Kompatibilität
                    original_col['show_order'] = new_order
                    
                    logger.debug(f"🔄 {col_name}: display_order={new_order}, show={new_visible}, expert={new_expert}")
                    
            logger.info(f"✅ ALLE Änderungen in {len(self.working_columns)} Controls übertragen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der Controls: {e}")
    
    def get_updated_columns(self):
        """Gibt die aktualisierten Spalten-Daten zurück"""
        return self.working_columns.copy()
