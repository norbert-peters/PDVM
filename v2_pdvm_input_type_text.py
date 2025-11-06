"""
PDVM Input-Type TEXT

VERANTWORTLICHKEITEN:
- QLineEdit Widget erstellen
- String-Werte laden/speichern
- Dirty-Tracking mit textChanged Signal
- Orange Rahmen bei Änderungen

AUTOR: Norbert Peters
DATUM: 24.10.2025
"""

import logging
from PyQt5.QtWidgets import QLineEdit, QWidget
from v2_pdvm_input_type_base import PdvmInputTypeBase  # ✅ V2-Version!

logger = logging.getLogger(__name__)


class PdvmInputTypeText(PdvmInputTypeBase):
    """Input-Type für Text (default)"""
    
    def create_widget(self) -> QWidget:
        """Erstellt QLineEdit Widget"""
        self.widget = QLineEdit()
        
        # Breite: FEST 400px
        self.widget.setFixedWidth(400)
        
        # Styling
        if self.read_only:
            self.widget.setReadOnly(True)
            self.widget.setStyleSheet("""
                QLineEdit {
                    background-color: #ecf0f1;
                    border: 1px solid #bdc3c7;
                    border-radius: 3px;
                    padding: 5px;
                    color: #7f8c8d;
                }
            """)
        else:
            self.widget.setStyleSheet("""
                QLineEdit {
                    background-color: white;
                    border: 1px solid #3498db;
                    border-radius: 3px;
                    padding: 5px;
                    color: #2c3e50;
                }
            """)
            # Change-Handler
            self.widget.textChanged.connect(self._on_value_changed)
        
        return self.widget
    
    def load_value(self, stichtag: float) -> tuple:
        """Lädt String-Wert aus DB"""
        if not self.db_instance:
            return (None, None)
        
        try:
            wert, abdatum = self.db_instance.get_value(
                self.gruppe,
                self.feld,
                stichtag
            )
            
            # String direkt übernehmen
            self.original_value = wert
            self.current_value = wert
            self.abdatum_wert = abdatum
            
            logger.debug(f"    📊 TEXT geladen: wert={str(wert)[:30]}")
            return (wert, abdatum)
            
        except Exception as e:
            logger.error(f"    ❌ TEXT-Fehler beim Laden: {e}")
            return (None, None)
    
    def update_display(self):
        """Aktualisiert QLineEdit mit current_value"""
        if not self.widget:
            return
        
        display_value = str(self.current_value) if self.current_value is not None else ""
        self.widget.blockSignals(True)
        self.widget.setText(display_value)
        self.widget.blockSignals(False)
    
    def get_current_value(self):
        """Gibt aktuellen String zurück"""
        return self.current_value
    
    def _on_value_changed(self, text):
        """Handler für textChanged Signal"""
        self.current_value = text
        self._is_dirty = (self.current_value != self.original_value)
        
        # Dirty-Styling
        if self._is_dirty:
            self.widget.setStyleSheet("""
                QLineEdit {
                    background-color: #fff9e6;
                    border: 2px solid #f39c12;
                    border-radius: 3px;
                    padding: 5px;
                    color: #2c3e50;
                }
            """)
        else:
            self.widget.setStyleSheet("""
                QLineEdit {
                    background-color: white;
                    border: 1px solid #3498db;
                    border-radius: 3px;
                    padding: 5px;
                    color: #2c3e50;
                }
            """)
