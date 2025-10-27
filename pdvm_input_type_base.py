"""
PDVM Input-Type BASE CLASS

ARCHITEKTUR:
- Jeder Input-Type ist eine autonome Klasse
- Kennt sein eigenes Widget (QLineEdit, DateTimePicker, QComboBox, etc.)
- Verwaltet eigenen Wert, Dirty-Status, Styling
- Control delegiert nur an Type

AUTOR: Norbert Peters
DATUM: 24.10.2025
VERSION: 1.0 (Type-basierte Architektur)
"""

import logging
from abc import ABC, abstractmethod
from PyQt5.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class PdvmInputTypeBase(ABC):
    """
    Basis-Klasse für alle Input-Types
    
    VERANTWORTLICHKEITEN:
    - Widget erstellen (type-spezifisch)
    - Wert laden (type-spezifisch)
    - Wert anzeigen (type-spezifisch)
    - Änderungen tracken (type-spezifisch)
    - Wert speichern (type-spezifisch)
    
    JEDER TYPE IMPLEMENTIERT:
    - create_widget() → Erstellt QLineEdit/DateTimePicker/QComboBox/etc.
    - load_value() → Lädt Wert aus DB und konvertiert
    - update_display() → Aktualisiert Widget-Anzeige
    - get_current_value() → Gibt aktuellen Wert zurück (für save)
    - is_dirty() → Prüft ob geändert
    """
    
    def __init__(self, parent: QWidget, control_config: dict):
        """
        Args:
            parent: Parent-Widget (PdvmInputControl)
            control_config: Dict mit allen Konfigurations-Daten:
                - db_instance: Datenbank-Instanz
                - gruppe: Gruppenname
                - feld: Feldname
                - read_only: Read-Only Status
                - field_config: Type-spezifische Config
        """
        self.parent = parent
        self.config = control_config
        
        # Extrahiere häufig verwendete Werte
        self.db_instance = control_config.get('db_instance')
        self.gruppe = control_config.get('gruppe')
        self.feld = control_config.get('feld')
        self.read_only = control_config.get('read_only', False)
        self.field_config = control_config.get('field_config', {})
        
        # Widget (wird von Subclass erstellt)
        self.widget = None
        
        # Werte
        self.original_value = None
        self.current_value = None
        self.abdatum_wert = None
        
        # Dirty-Flag
        self._is_dirty = False
    
    def get_target_width(self) -> int:
        """
        Gibt Ziel-Breite des Widgets zurück (für Layout-Spacer)
        
        Returns:
            int: Breite in Pixel (Default: 400px)
        """
        return 400  # Default: Standard-Breite
    
    @abstractmethod
    def create_widget(self) -> QWidget:
        """
        Erstellt type-spezifisches Widget
        
        Returns:
            QWidget (QLineEdit, DateTimePicker, QComboBox, etc.)
        """
        pass
    
    @abstractmethod
    def load_value(self, stichtag: float) -> tuple:
        """
        Lädt Wert aus DB und konvertiert type-spezifisch
        
        Args:
            stichtag: Stichtag für historische Abfrage
        
        Returns:
            (wert, abdatum) tuple
        """
        pass
    
    @abstractmethod
    def update_display(self):
        """
        Aktualisiert Widget-Anzeige mit current_value
        """
        pass
    
    @abstractmethod
    def get_current_value(self):
        """
        Gibt aktuellen Wert zurück (für save)
        
        Returns:
            Aktueller Wert (type-spezifisch formatiert)
        """
        pass
    
    def is_dirty(self) -> bool:
        """
        Prüft ob Wert geändert wurde
        
        Returns:
            True wenn geändert, False sonst
        """
        return self._is_dirty
    
    def set_read_only(self, read_only: bool):
        """
        Setzt Read-Only Status (type-spezifisch überschreibbar)
        
        Args:
            read_only: True für read-only, False für editierbar
        """
        self.read_only = read_only
        if self.widget:
            self.widget.setEnabled(not read_only)
