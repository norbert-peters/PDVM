"""
PDVM History Value Widget - VIEWTABLE

Type-Widget für ViewTable-Felder in Historie-Dialogs.

FUNKTIONALITÄT:
- QTableWidgetItem (nicht editierbar) für GUID
- Zusätzliche Spalte "Name" (READ-ONLY)
- Doppelklick öffnet View-Dialog
- Name-Update nach GUID-Änderung

AUTOR: Norbert Peters
DATUM: 27.10.2025
"""

import logging
from typing import List
from PyQt5.QtWidgets import QTableWidgetItem, QDialog, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from pdvm_history_value_widget_base import PdvmHistoryValueWidgetBase
from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)


class PdvmHistoryValueWidgetViewTable(PdvmHistoryValueWidgetBase):
    """History-Value-Widget für ViewTable-Felder"""
    
    def __init__(self, table, field_config, db_instance=None):
        super().__init__(table, field_config, db_instance)
        
        # ViewTable-Config extrahieren
        viewtable_config = field_config.get('viewtable_config', {})
        self.view_guid = viewtable_config.get('guid') or viewtable_config.get('view_guid')
        
        # Tabellen-Name extrahieren (für Name-Lookup)
        self.table_name = field_config.get('table_name')  # Wird vom Dialog übergeben
        
        # DB-Instanz für Name-Lookup (wird lazy erstellt)
        self.viewtable_db = None
    
    def get_additional_columns(self) -> List[str]:
        """ViewTable hat zusätzliche 'Name'-Spalte"""
        return ["Name"]
    
    def create_value_cell(self, row: int, value: any, abdatum: float) -> None:
        """Erstellt nicht-editierbares Item für GUID"""
        # GUID als String
        guid_value = str(value) if value else ""
        
        # Nicht-editierbares Item
        guid_item = QTableWidgetItem(guid_value)
        guid_item.setFlags(guid_item.flags() & ~Qt.ItemIsEditable)
        guid_item.setForeground(QColor('#2c3e50'))
        
        # In Tabelle setzen (Spalte 1 = GUID)
        self.table.setItem(row, 1, guid_item)
        
        # Original-Wert speichern
        self.store_original_value(row, abdatum, guid_value)
        
        logger.debug(f"    ViewTable-Cell erstellt: Row {row}, GUID: {guid_value[:20]}...")
    
    def create_additional_cells(self, row: int, value: any) -> None:
        """Erstellt Name-Spalte (Spalte 2)"""
        guid_value = str(value) if value else ""
        
        # Namen holen
        name = self._get_name_for_guid(guid_value)
        
        # Name-Item (READ-ONLY)
        name_item = QTableWidgetItem(name)
        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
        name_item.setForeground(QColor('#2c3e50'))
        
        # In Tabelle setzen (Spalte 2 = Name)
        self.table.setItem(row, 2, name_item)
        
        logger.debug(f"    ViewTable-Name erstellt: Row {row}, Name: {name}")
    
    def get_current_value(self, row: int) -> str:
        """Holt GUID aus QTableWidgetItem"""
        value_item = self.table.item(row, 1)
        if not value_item:
            return ""
        
        return value_item.text()
    
    def is_value_changed(self, row: int) -> bool:
        """GUID-String-Vergleich"""
        current_value = self.get_current_value(row)
        abdatum, original_value = self.get_original_value(row)
        
        if abdatum is None:
            return False
        
        # String-Vergleich
        return str(current_value) != str(original_value)
    
    def update_additional_cells(self, row: int, new_guid: str) -> None:
        """Aktualisiert Name-Spalte nach GUID-Änderung"""
        # Neuen Namen holen
        new_name = self._get_name_for_guid(new_guid)
        
        # Name-Item aktualisieren
        name_item = self.table.item(row, 2)
        if name_item:
            name_item.setText(new_name)
            logger.debug(f"    ViewTable-Name aktualisiert: Row {row}, Name: {new_name}")
    
    def open_selection_dialog(self, row: int, parent_widget) -> None:
        """
        Öffnet View-Dialog zur GUID-Auswahl (wird von Doppelklick-Handler aufgerufen).
        
        Args:
            row: Zeilen-Index
            parent_widget: Parent-Widget für Dialog
        """
        try:
            # Aktuelle GUID holen
            old_guid = self.get_current_value(row)
            
            logger.info(f"📋 Öffne ViewTable-Auswahl für Zeile {row} (alte GUID: {old_guid[:8] if old_guid else 'None'}...)")
            
            # View-GUID prüfen
            if not self.view_guid:
                QMessageBox.warning(parent_widget, "Fehler", 
                    "Keine View-GUID in ViewTable-Konfiguration gefunden!")
                return
            
            # Dialog öffnen
            from pdvm_input_viewtable_selection_dialog import PdvmInputViewtableSelectionDialog
            
            dialog = PdvmInputViewtableSelectionDialog(
                viewtable_guid=self.view_guid,
                current_guid=old_guid,
                parent=parent_widget
            )
            
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                new_guid = dialog.selected_guid
                
                if new_guid and new_guid != old_guid:
                    logger.info(f"  ✅ Neue GUID gewählt: {new_guid[:8]}...")
                    
                    # GUID-Item aktualisieren
                    guid_item = self.table.item(row, 1)
                    if guid_item:
                        guid_item.setText(str(new_guid))
                    
                    # Name-Spalte aktualisieren
                    self.update_additional_cells(row, new_guid)
                    
                    logger.info(f"  ✅ ViewTable-Zeile {row} aktualisiert")
                else:
                    logger.info("  ℹ️ Keine Änderung (gleiche GUID gewählt)")
            else:
                logger.info("  ℹ️ Auswahl abgebrochen")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Öffnen der ViewTable-Auswahl: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(parent_widget, "Fehler", f"Fehler beim Öffnen der Auswahl:\n{e}")
    
    def _get_name_for_guid(self, guid: str) -> str:
        """
        Holt Namen für GUID aus ViewTable-DB.
        
        Args:
            guid: GUID
            
        Returns:
            Name oder "<Kein Name>"
        """
        if not guid:
            return "<Keine Auswahl>"
        
        # DB-Instanz lazy erstellen
        if not self.viewtable_db:
            self.viewtable_db = self._create_viewtable_db_instance()
        
        if not self.viewtable_db:
            return "<Name nicht verfügbar>"
        
        try:
            name = self.viewtable_db.get_name(guid)
            if not name or name in ('None', 'none', 'NONE'):
                return "<Kein Name>"
            return name
        except Exception as e:
            logger.error(f"❌ Fehler beim Name-Lookup für GUID {guid[:20]}: {e}")
            return "<Fehler beim Laden>"
    
    def _create_viewtable_db_instance(self) -> PdvmCentralDatenbank:
        """
        Erstellt DB-Instanz für ViewTable-Tabelle.
        
        Tabellen-Name kommt aus field_config['table_name'] (wird vom Dialog übergeben).
        
        Returns:
            PdvmCentralDatenbank Instanz oder None
        """
        try:
            if not self.table_name:
                logger.warning("⚠️ Kein table_name in field_config - kann DB-Instanz nicht erstellen")
                return None
            
            # DB-Instanz erstellen (OHNE guid - für Name-Lookup!)
            db_instance = PdvmCentralDatenbank(table_name=self.table_name)
            logger.info(f"✅ ViewTable DB-Instanz erstellt: {self.table_name}")
            return db_instance
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der ViewTable-DB-Instanz: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
