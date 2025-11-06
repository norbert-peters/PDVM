"""
PDVM History Value Widget - DROPDOWN

Type-Widget für Dropdown-Felder in Historie-Dialogs.

FUNKTIONALITÄT:
- QComboBox als CellWidget
- Key-Vergleich für Dirty-Tracking (itemData)
- Dropdown-Config aus field_config

AUTOR: Norbert Peters
DATUM: 27.10.2025
"""

import logging
from PyQt5.QtWidgets import QComboBox
from pdvm_history_value_widget_base import PdvmHistoryValueWidgetBase

logger = logging.getLogger(__name__)


class PdvmHistoryValueWidgetDropdown(PdvmHistoryValueWidgetBase):
    """History-Value-Widget für Dropdown-Felder"""
    
    def __init__(self, table, field_config, db_instance=None):
        super().__init__(table, field_config, db_instance)
        
        # Dropdown-Config extrahieren
        dropdown_config = field_config.get('dropdown_config', {})
        self.dropdown_table = dropdown_config.get('table', '')
        self.dropdown_key = dropdown_config.get('key', '')
        self.dropdown_value = dropdown_config.get('value', '')
        
        # Key-to-Display Mapping laden (EINMALIG bei Init!)
        self.key_to_display = {}
        self._load_dropdown_options()
        
        # Combo-Referenzen speichern
        self.combos = {}  # {row: combo_widget}
    
    def _load_dropdown_options(self):
        """
        Lädt Dropdown-Optionen aus DB (EINMALIG!).
        
        Dropdown-Config Format:
        {
            'table': 'benutzerstamm',
            'key': 'gender',
            'value': 'gender'
        }
        
        Lädt JSON-Feld mit {key: display_text} Mapping.
        """
        if not (self.dropdown_table and self.dropdown_key and self.dropdown_value):
            logger.warning("    ⚠️ Unvollständige Dropdown-Config")
            return
        
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            from pdvm_central_systemsteuerung import get_gcs
            import json
            
            gcs = get_gcs()
            if not gcs:
                logger.error("    ❌ GCS nicht verfügbar!")
                return
            
            # Dropdown-Daten direkt aus GCS holen
            dropdown_options = gcs.get_dropdown_options(self.dropdown_key, self.dropdown_value)
            
            if dropdown_options:
                # Mapping speichern: {key: display_text}
                self.key_to_display = dropdown_options.copy()
                logger.info(f"    ✅ {len(self.key_to_display)} Dropdown-Optionen geladen: {list(self.key_to_display.keys())}")
            else:
                logger.warning(f"    ⚠️ Keine Dropdown-Daten für {self.dropdown_table}.{self.dropdown_value}")
                
        except Exception as e:
            logger.error(f"    ❌ Fehler beim Laden der Dropdown-Optionen: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def create_value_cell(self, row: int, value: any, abdatum: float) -> None:
        """
        Erstellt QComboBox als CellWidget mit allen Dropdown-Optionen.
        
        Args:
            row: Zeile in Tabelle
            value: KEY (z.B. 'm', 'w') - wird in DB gespeichert
            abdatum: Zeitstempel
        """
        # QComboBox erstellen
        combo = QComboBox()
        
        # Items hinzufügen (Display-Text sichtbar, Key als userData)
        if self.key_to_display:
            for key, display_text in self.key_to_display.items():
                combo.addItem(display_text, key)  # Display sichtbar, Key als itemData
        else:
            # Fallback: Nur aktuellen Wert (wenn keine Optionen geladen)
            if value:
                combo.addItem(str(value), value)
        
        # Aktuellen Wert selektieren (KEY-basiert!)
        if value is not None:
            for i in range(combo.count()):
                if combo.itemData(i) == value:
                    combo.setCurrentIndex(i)
                    break
        
        # In Tabelle setzen (Spalte 1 = Wert)
        self.table.setCellWidget(row, 1, combo)
        
        # Combo-Referenz speichern
        self.combos[row] = combo
        
        # Original-Wert speichern (KEY, nicht Display!)
        self.store_original_value(row, abdatum, value)
        
        logger.debug(f"    Dropdown-Cell erstellt: Row {row}, Key: {value}, Display: {self.key_to_display.get(value, value)}")
    
    def get_current_value(self, row: int) -> any:
        """Holt Key aus QComboBox (itemData)"""
        combo = self.combos.get(row)
        if not combo:
            return None
        
        idx = combo.currentIndex()
        if idx < 0:
            return None
        
        # KEY zurückgeben (nicht Display!)
        return combo.itemData(idx)
    
    def is_value_changed(self, row: int) -> bool:
        """Key-Vergleich"""
        current_value = self.get_current_value(row)
        abdatum, original_value = self.get_original_value(row)
        
        if abdatum is None:
            return False
        
        # Key-Vergleich
        return current_value != original_value
