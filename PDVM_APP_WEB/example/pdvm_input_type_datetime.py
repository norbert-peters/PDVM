"""
PDVM Input-Type DATETIME

VERANTWORTLICHKEITEN:
- PdvmDateTimePicker Widget erstellen
- Pdvm_DateTime Werte laden/speichern
- Dirty-Tracking mit valueChanged Signal
- Orange Rahmen bei Änderungen (über Picker)

AUTOR: Norbert Peters
DATUM: 24.10.2025
"""

import logging
from PyQt5.QtWidgets import QWidget
from pdvm_input_type_base import PdvmInputTypeBase  # ✅ V2-Version!
from pdvm_date_time_picker import PdvmDateTimePicker
from pdvm_datetime import Pdvm_DateTime
# ✅ V2: GCS wird vom Control durchgereicht (self.control.gcs)

logger = logging.getLogger(__name__)


class PdvmInputTypeDatetime(PdvmInputTypeBase):
    """Input-Type für Datum/Zeit"""
    
    def __init__(self, parent: QWidget, control_config: dict):
        super().__init__(parent, control_config)
        
        # Pdvm_DateTime Instanz für Wert
        self.value_dt = Pdvm_DateTime(self.control.gcs.field_value('country'))
        
        # Display-Mode bestimmt Breite
        self.display_mode = self.field_config.get('display_val', 'all')
    
    def get_target_width(self) -> int:
        """Gibt Ziel-Breite basierend auf Display-Mode zurück"""
        if self.display_mode == 'only_time':
            return 180
        elif self.display_mode == 'only_date':
            return 220
        else:  # 'all'
            return 400
    
    def create_widget(self) -> QWidget:
        """Erstellt PdvmDateTimePicker Widget"""
        self.widget = PdvmDateTimePicker(
            parent=self.parent,
            pdvm_datetime=self.value_dt,
            display=self.display_mode
        )
        
        # Breite basierend auf Display-Mode (FEST, nicht max!)
        if self.display_mode == 'only_time':
            self.widget.setFixedWidth(180)  # Zeit: "HH:MM:SS" + Jetzt/00:00
        elif self.display_mode == 'only_date':
            self.widget.setFixedWidth(220)  # Datum: "DD.MM.YYYY" + Jetzt
        else:  # 'all'
            self.widget.setFixedWidth(400)  # Datum + Zeit + Buttons
        
        # Read-Only Status
        if self.read_only:
            self.widget.setEnabled(False)
        else:
            # Signal für Dirty-Tracking
            self.widget.valueChanged.connect(self._on_value_changed)
        
        return self.widget
    
    def load_value(self, stichtag: float) -> tuple:
        """Lädt DateTime-Wert aus DB"""
        if not self.db_instance:
            return (None, None)
        
        try:
            wert, abdatum = self.db_instance.get_value(
                self.gruppe,
                self.feld,
                stichtag
            )
            
            # Float in Pdvm_DateTime setzen
            if wert is not None:
                self.value_dt.PdvmDateTime = float(wert)
            
            self.original_value = wert
            self.current_value = wert
            self.abdatum_wert = abdatum
            
            logger.debug(f"    📊 DATETIME geladen: wert={wert}")
            return (wert, abdatum)
            
        except Exception as e:
            logger.error(f"    ❌ DATETIME-Fehler beim Laden: {e}")
            return (None, None)
    
    def update_display(self):
        """Aktualisiert DateTimePicker Display"""
        if self.widget:
            self.widget.update_display()
    
    def get_current_value(self):
        """Gibt aktuellen DateTime-Float zurück"""
        # Picker committen falls dirty
        if self.widget and self.widget.is_dirty():
            self.widget.save()
            self.current_value = self.value_dt.PdvmDateTime
        
        return self.current_value
    
    def is_dirty(self) -> bool:
        """Prüft ob Picker dirty ist"""
        if self.widget:
            return self.widget.is_dirty()
        return False
    
    def _on_value_changed(self):
        """Handler für valueChanged Signal vom Picker"""
        # Picker stylt sich selbst - wir müssen nur wissen dass er dirty ist
        self._is_dirty = True

