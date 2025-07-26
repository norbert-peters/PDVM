# pdvm_date_range_filter_dialog_v3.py
"""
DateRange-Filter-Dialog V3 mit korrekter Original/Show-Spalten-Logik
Implementiert Zeitraum- und Standard-Modus mit verbesserter UI
"""

import logging
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QRadioButton, QButtonGroup, QFrame, QLineEdit, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

# Import des V3 Date Pickers
from pdvm_area_date_picker_v3 import PdvmAreaDatePickerV3

logger = logging.getLogger(__name__)

class PdvmDateRangeFilterDialogV3(QDialog):
    """
    DateRange-Filter-Dialog V3 mit Original/Show-Spalten-Unterstützung
    
    Features:
    - Zeitraum-Modus: Von/Bis mit analoger Übertragung
    - Standard-Modus: Einzelne Datumsfelder
    - Original/Show-Spalten-Logik
    - Verbesserte UI mit korrekter Feldgröße
    """
    
    # Signal für Filter-Updates
    filterChanged = pyqtSignal(dict)
    
    def __init__(self, field_name: str, current_state: Optional[Dict] = None, parent=None):
        super().__init__(parent)
        
        self.field_name = field_name
        self.current_state = current_state or {}
        
        self._setup_ui()
        self._load_current_state()
        
        logger.info(f"📅 DateRange-Filter-Dialog V3 für Feld: {field_name}")
    
    def _setup_ui(self):
        """Setup der Dialog-UI"""
        self.setWindowTitle(f"Datumsfilter: {self.field_name}")
        self.setModal(True)
        self.resize(400, 350)
        
        # Haupt-Layout
        layout = QVBoxLayout(self)
        
        # Titel
        title = QLabel(f"Datumsfilter für: {self.field_name}")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        layout.addWidget(separator)
        
        # Filter-Modus Auswahl
        self._setup_mode_selection(layout)
        
        # Date Picker Container
        self.date_picker_container = QVBoxLayout()
        layout.addLayout(self.date_picker_container)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        layout.addWidget(separator2)
        
        # Buttons
        self._setup_buttons(layout)
        
        # Initial Date Picker laden
        self._update_date_picker()
    
    def _setup_mode_selection(self, layout):
        """Setup der Modus-Auswahl"""
        mode_frame = QFrame()
        mode_layout = QVBoxLayout(mode_frame)
        
        # Label
        mode_label = QLabel("Filter-Modus:")
        mode_label.setFont(QFont("Arial", 10, QFont.Bold))
        mode_layout.addWidget(mode_label)
        
        # Radio Buttons
        self.mode_group = QButtonGroup()
        
        self.zeitraum_radio = QRadioButton("Zeitraum-Modus (Von/Bis mit analoger Übertragung)")
        self.standard_radio = QRadioButton("Standard-Modus (Einzelne Datumsfelder)")
        
        self.mode_group.addButton(self.zeitraum_radio, 0)
        self.mode_group.addButton(self.standard_radio, 1)
        
        # Standard: Zeitraum-Modus
        self.zeitraum_radio.setChecked(True)
        
        # Signal-Verbindung
        self.mode_group.buttonClicked.connect(self._on_mode_changed)
        
        mode_layout.addWidget(self.zeitraum_radio)
        mode_layout.addWidget(self.standard_radio)
        
        layout.addWidget(mode_frame)
    
    def _setup_buttons(self, layout):
        """Setup der Dialog-Buttons"""
        button_layout = QHBoxLayout()
        
        # Zurücksetzen Button
        self.reset_button = QPushButton("Zurücksetzen")
        self.reset_button.clicked.connect(self._reset_filter)
        button_layout.addWidget(self.reset_button)
        
        button_layout.addStretch()
        
        # Standard-Buttons
        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.apply_button = QPushButton("Anwenden")
        self.apply_button.clicked.connect(self._apply_filter)
        self.apply_button.setDefault(True)
        button_layout.addWidget(self.apply_button)
        
        layout.addLayout(button_layout)
    
    def _update_date_picker(self):
        """Aktualisiert den Date Picker basierend auf dem Modus"""
        # Alten Date Picker entfernen
        self._clear_date_picker_container()
        
        # Modus bestimmen
        is_zeitraum = self.zeitraum_radio.isChecked()
        
        # Neuen Date Picker erstellen
        self.date_picker = PdvmAreaDatePickerV3(
            field_name=self.field_name,
            zeitraum_mode=is_zeitraum,
            parent=self
        )
        
        # Date Picker hinzufügen
        self.date_picker_container.addWidget(self.date_picker)
        
        logger.info(f"📅 Date Picker aktualisiert - Modus: {'Zeitraum' if is_zeitraum else 'Standard'}")
    
    def _clear_date_picker_container(self):
        """Entfernt alle Widgets aus dem Date Picker Container"""
        while self.date_picker_container.count():
            child = self.date_picker_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def _on_mode_changed(self):
        """Callback wenn sich der Modus ändert"""
        self._update_date_picker()
    
    def _load_current_state(self):
        """Lädt den aktuellen Filter-Zustand"""
        if not self.current_state:
            return
        
        try:
            # Modus laden
            zeitraum_mode = self.current_state.get('zeitraum_mode', True)
            if zeitraum_mode:
                self.zeitraum_radio.setChecked(True)
            else:
                self.standard_radio.setChecked(True)
            
            # Date Picker aktualisieren
            self._update_date_picker()
            
            # Filter-Werte an Date Picker weitergeben
            if hasattr(self, 'date_picker'):
                self.date_picker.load_filter_state(self.current_state)
                
            logger.info(f"📅 Filter-Zustand geladen: {zeitraum_mode=}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Filter-Zustands: {e}")
    
    def _apply_filter(self):
        """Wendet den Filter an"""
        try:
            if not hasattr(self, 'date_picker'):
                logger.warning("⚠️ Kein Date Picker verfügbar")
                return
            
            # Filter-Zustand vom Date Picker holen
            filter_state = self.date_picker.get_filter_state()
            
            # Modus hinzufügen
            filter_state['zeitraum_mode'] = self.zeitraum_radio.isChecked()
            
            # Signal senden
            self.filterChanged.emit(filter_state)
            
            logger.info(f"✅ DateRange-Filter angewendet: {filter_state}")
            
            # Dialog schließen
            self.accept()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anwenden des Filters: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Fehler", f"Fehler beim Anwenden des Filters:\n{str(e)}")
    
    def _reset_filter(self):
        """Setzt den Filter zurück"""
        try:
            if hasattr(self, 'date_picker'):
                self.date_picker.reset_filter()
            
            logger.info("🔄 DateRange-Filter zurückgesetzt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Zurücksetzen des Filters: {e}")
    
    def get_filter_state(self) -> Dict:
        """
        Gibt den aktuellen Filter-Zustand zurück
        
        Returns:
            Dict: Filter-Zustand
        """
        if not hasattr(self, 'date_picker'):
            return {}
        
        filter_state = self.date_picker.get_filter_state()
        filter_state['zeitraum_mode'] = self.zeitraum_radio.isChecked()
        
        return filter_state
