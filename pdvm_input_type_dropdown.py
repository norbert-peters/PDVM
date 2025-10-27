"""
PDVM Input-Type DROPDOWN

VERANTWORTLICHKEITEN:
- QComboBox Widget erstellen
- Dropdown-Daten aus separater DB-Instanz laden
- Key→Display-Text Mapping
- Dirty-Tracking mit currentIndexChanged Signal

AUTOR: Norbert Peters
DATUM: 24.10.2025
"""

import logging
import json
from PyQt5.QtWidgets import QComboBox, QWidget
from pdvm_input_type_base import PdvmInputTypeBase
from pdvm_central_datenbank import PdvmCentralDatenbank
from global_gcs import gcs

logger = logging.getLogger(__name__)


class PdvmInputTypeDropdown(PdvmInputTypeBase):
    """Input-Type für Dropdown (Auswahllisten)"""
    
    def __init__(self, parent: QWidget, control_config: dict):
        super().__init__(parent, control_config)
        
        # Dropdown-spezifische Config
        self.dropdown_config = self.field_config.get('dropdown_config', {})
        self.dropdown_instance = None
        self.dropdown_items = {}  # {display_text: key}
        self.calculated_width = 500  # Default
        
        # Dropdown-Instanz initialisieren
        self._init_dropdown_instance()
    
    def get_target_width(self) -> int:
        """Gibt berechnete Dropdown-Breite zurück"""
        return self.calculated_width
    
    def _init_dropdown_instance(self):
        """Initialisiert Dropdown-Instanz und lädt Items"""
        if not self.dropdown_config:
            logger.error("    ❌ DROPDOWN: Keine dropdown_config")
            return
        
        table = self.dropdown_config.get('table', '')
        key = self.dropdown_config.get('key', '')
        value = self.dropdown_config.get('value', '')
        
        if not table or not key or not value:
            logger.error("    ❌ DROPDOWN: Unvollständige Config")
            return
        
        # Instanz erstellen
        try:
            self.dropdown_instance = PdvmCentralDatenbank(table, key)
            logger.debug(f"    🔽 DROPDOWN-Instanz: {table}_{key[:8]}...")
        except Exception as e:
            logger.error(f"    ❌ DROPDOWN-Instanz-Fehler: {e}")
            return
        
        # Language aus GCS
        try:
            language = gcs._u_db.get_static_value(gcs.user_guid, 'language')
            if not language:
                language = 'de-de'
        except Exception as e:
            logger.error(f"    ❌ Language-Fehler: {e}")
            language = 'de-de'
        
        # Items laden
        try:
            json_data = self.dropdown_instance.get_static_value(value, language)
            
            if not json_data:
                logger.warning(f"    ⚠️ Keine Dropdown-Daten für {value}/{language}")
                return
            
            # JSON parsen
            dropdown_dict = json.loads(json_data) if isinstance(json_data, str) else json_data
            
            for item_key, display_text in dropdown_dict.items():
                if item_key and display_text:
                    self.dropdown_items[display_text] = item_key
            
            logger.info(f"    🔽 Dropdown geladen: {len(self.dropdown_items)} Items")
            
        except Exception as e:
            logger.error(f"    ❌ Dropdown-Items-Fehler: {e}")
    
    def create_widget(self) -> QWidget:
        """Erstellt QComboBox Widget"""
        self.widget = QComboBox()
        
        # Items hinzufügen
        max_text_length = 0
        for display_text in sorted(self.dropdown_items.keys()):
            self.widget.addItem(display_text, self.dropdown_items[display_text])
            max_text_length = max(max_text_length, len(display_text))
        
        # Breite basierend auf längstem Text
        # Faustformel: 8 Pixel pro Zeichen + 40 Pixel für Dropdown-Pfeil + Padding
        estimated_width = min(max(max_text_length * 8 + 40, 150), 400)
        self.calculated_width = estimated_width  # Speichern für get_target_width()
        
        # FEST auf berechnete Breite setzen (nicht min/max!)
        self.widget.setFixedWidth(estimated_width)
        
        # Styling
        if self.read_only:
            self.widget.setEnabled(False)
            self.widget.setStyleSheet("""
                QComboBox {
                    background-color: #ecf0f1;
                    border: 1px solid #bdc3c7;
                    border-radius: 3px;
                    padding: 5px;
                    color: #7f8c8d;
                }
            """)
        else:
            self.widget.setStyleSheet("""
                QComboBox {
                    background-color: white;
                    border: 1px solid #3498db;
                    border-radius: 3px;
                    padding: 5px;
                    color: #2c3e50;
                }
            """)
            # Change-Handler
            self.widget.currentIndexChanged.connect(self._on_value_changed)
        
        return self.widget
    
    def load_value(self, stichtag: float) -> tuple:
        """Lädt Key-Wert aus DB"""
        if not self.db_instance:
            return (None, None)
        
        try:
            wert, abdatum = self.db_instance.get_value(
                self.gruppe,
                self.feld,
                stichtag
            )
            
            # Key direkt übernehmen (z.B. "m", "w", "d")
            self.original_value = wert
            self.current_value = wert
            self.abdatum_wert = abdatum
            
            logger.debug(f"    📊 DROPDOWN geladen: key={wert}")
            return (wert, abdatum)
            
        except Exception as e:
            logger.error(f"    ❌ DROPDOWN-Fehler beim Laden: {e}")
            return (None, None)
    
    def update_display(self):
        """Setzt ComboBox auf richtigen Index basierend auf current_value (key)"""
        if not self.widget or not self.current_value:
            return
        
        # Finde Index des Items mit diesem Key
        for i in range(self.widget.count()):
            if self.widget.itemData(i) == self.current_value:
                self.widget.blockSignals(True)
                self.widget.setCurrentIndex(i)
                self.widget.blockSignals(False)
                break
    
    def get_current_value(self):
        """Gibt aktuellen Key zurück (z.B. "m")"""
        return self.current_value
    
    def _on_value_changed(self, index):
        """Handler für currentIndexChanged Signal"""
        if index < 0:
            return
        
        # Key aus itemData holen
        self.current_value = self.widget.itemData(index)
        self._is_dirty = (self.current_value != self.original_value)
        
        # Dirty-Styling
        if self._is_dirty:
            self.widget.setStyleSheet("""
                QComboBox {
                    background-color: #fff9e6;
                    border: 2px solid #f39c12;
                    border-radius: 3px;
                    padding: 5px;
                    color: #2c3e50;
                }
            """)
        else:
            self.widget.setStyleSheet("""
                QComboBox {
                    background-color: white;
                    border: 1px solid #3498db;
                    border-radius: 3px;
                    padding: 5px;
                    color: #2c3e50;
                }
            """)
