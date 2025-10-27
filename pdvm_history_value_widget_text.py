"""
PDVM History Value Widget - TEXT

Type-Widget für Text-Felder in Historie-Dialogs.

FUNKTIONALITÄT:
- QTableWidgetItem (editierbar)
- String-Vergleich für Dirty-Tracking

AUTOR: Norbert Peters
DATUM: 27.10.2025
"""

import logging
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtCore import Qt
from pdvm_history_value_widget_base import PdvmHistoryValueWidgetBase

logger = logging.getLogger(__name__)


class PdvmHistoryValueWidgetText(PdvmHistoryValueWidgetBase):
    """History-Value-Widget für Text-Felder"""
    
    def create_value_cell(self, row: int, value: any, abdatum: float) -> None:
        """Erstellt editierbares QTableWidgetItem"""
        # String-Wert sicherstellen
        text_value = str(value) if value is not None else ""
        
        # Editierbares Item erstellen
        value_item = QTableWidgetItem(text_value)
        value_item.setFlags(value_item.flags() | Qt.ItemIsEditable)
        
        # In Tabelle setzen (Spalte 1 = Wert)
        self.table.setItem(row, 1, value_item)
        
        # Original-Wert speichern
        self.store_original_value(row, abdatum, text_value)
        
        logger.debug(f"    Text-Cell erstellt: Row {row}, Value: '{text_value[:30]}...'")
    
    def get_current_value(self, row: int) -> str:
        """Holt Text aus QTableWidgetItem"""
        value_item = self.table.item(row, 1)
        if not value_item:
            return ""
        
        return value_item.text()
    
    def is_value_changed(self, row: int) -> bool:
        """String-Vergleich"""
        current_value = self.get_current_value(row)
        abdatum, original_value = self.get_original_value(row)
        
        if abdatum is None:
            return False
        
        # String-Vergleich
        return str(current_value) != str(original_value)
