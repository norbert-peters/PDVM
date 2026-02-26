"""
PDVM History Value Widget - DATETIME

Type-Widget für DateTime-Felder in Historie-Dialogs.

FUNKTIONALITÄT:
- PdvmDateTimePicker als CellWidget
- Float-Vergleich für Dirty-Tracking
- Picker.save() für committed value

AUTOR: Norbert Peters
DATUM: 27.10.2025
"""

import logging
from PyQt5.QtCore import Qt
from pdvm_history_value_widget_base import PdvmHistoryValueWidgetBase
from pdvm_date_time_picker import PdvmDateTimePicker  # ✅ Korrekter Modul-Name!
from pdvm_datetime import Pdvm_DateTime
from global_gcs import gcs

logger = logging.getLogger(__name__)


class PdvmHistoryValueWidgetDateTime(PdvmHistoryValueWidgetBase):
    """History-Value-Widget für DateTime-Felder"""
    
    def __init__(self, table, field_config, db_instance=None):
        super().__init__(table, field_config, db_instance)
        
        # display_val für Picker
        self.display_val = field_config.get('display_val', 'all')
        
        # Picker-Referenzen speichern (für get_current_value)
        self.pickers = {}  # {row: picker_widget}
    
    def create_value_cell(self, row: int, value: any, abdatum: float) -> None:
        """Erstellt DateTimePicker als CellWidget"""
        # Float-Wert sicherstellen
        if isinstance(value, (int, float)):
            float_value = float(value)
        else:
            try:
                float_value = float(value) if value else None
            except (ValueError, TypeError):
                float_value = None
        
        # DateTimePicker erstellen
        dt = Pdvm_DateTime(gcs.field_value('country'))
        dt.PdvmDateTime = float_value if float_value else 1001.0
        
        picker = PdvmDateTimePicker(
            parent=None,
            pdvm_datetime=dt,
            display=self.display_val  # ✅ KORREKT: 'display' nicht 'display_val'!
        )
        
        # In Tabelle setzen (Spalte 1 = Wert)
        self.table.setCellWidget(row, 1, picker)
        
        # Picker-Referenz speichern
        self.pickers[row] = picker
        
        # Original-Wert speichern
        self.store_original_value(row, abdatum, float_value)
        
        logger.debug(f"    DateTime-Cell erstellt: Row {row}, Value: {float_value}")
    
    def get_current_value(self, row: int) -> float:
        """Holt Float aus DateTimePicker (nach save())"""
        picker = self.pickers.get(row)
        if not picker:
            return None
        
        # Picker committen (wichtig!)
        picker.save()
        
        # Float-Wert zurückgeben
        return picker.pdvm_datetime.PdvmDateTime
    
    def is_value_changed(self, row: int) -> bool:
        """Float-Vergleich"""
        current_value = self.get_current_value(row)
        abdatum, original_value = self.get_original_value(row)
        
        if abdatum is None:
            return False
        
        # Float-Vergleich
        return current_value != original_value
