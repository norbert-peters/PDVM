"""
PDVM History Value Widget - BASE CLASS

Abstrakte Basis-Klasse für Type-spezifische Value-Widgets in Historie-Dialogs.

ARCHITEKTUR-PRINZIP:
- Einheitliche API für alle IC-Types
- Type-Widget kümmert sich NUR um Wert-Darstellung/-Bearbeitung
- Dialog-Rahmen (Tabelle, Buttons, etc.) bleibt identisch

VERANTWORTLICHKEITEN:
- Widget/Item für Wert-Zelle erstellen
- Aktuellen Wert aus Widget/Item extrahieren
- Dirty-Tracking (Original vs. Aktuell)
- Zusätzliche Spalten definieren (z.B. Name bei ViewTable)

AUTOR: Norbert Peters
DATUM: 27.10.2025
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, List, Tuple, Optional
from PyQt5.QtWidgets import QTableWidget

logger = logging.getLogger(__name__)


class PdvmHistoryValueWidgetBase(ABC):
    """
    Abstrakte Basis-Klasse für History-Value-Widgets
    
    Implementiert Type-spezifische Logik für Historie-Dialogs:
    - Wert-Darstellung (Widget/Item erstellen)
    - Wert-Extraktion (aktuellen Wert holen)
    - Dirty-Tracking (Änderungserkennung)
    - Zusätzliche Spalten (z.B. Name bei ViewTable)
    """
    
    def __init__(self, table: QTableWidget, field_config: dict, db_instance=None):
        """
        Args:
            table: QTableWidget Referenz (für setCellWidget, setItem)
            field_config: Feld-Konfiguration (für Type-spezifische Settings)
            db_instance: DB-Instanz (für ViewTable Name-Lookup etc.)
        """
        self.table = table
        self.field_config = field_config or {}
        self.db_instance = db_instance
        
        # Tracking für Original-Werte
        # Format: {row: (abdatum, original_value)}
        self.original_data = {}
    
    @abstractmethod
    def create_value_cell(self, row: int, value: Any, abdatum: float) -> None:
        """
        Erstellt Widget/Item für Wert-Zelle (Spalte 1).
        
        Args:
            row: Zeilen-Index
            value: Original-Wert aus DB
            abdatum: Abdatum (für Tracking)
            
        Implementierung:
            - Text: QTableWidgetItem (editierbar)
            - DateTime: DateTimePicker als CellWidget
            - Dropdown: QComboBox als CellWidget
            - ViewTable: QTableWidgetItem (nicht editierbar) + Doppelklick-Handler
        """
        pass
    
    @abstractmethod
    def get_current_value(self, row: int) -> Any:
        """
        Extrahiert aktuellen Wert aus Zelle.
        
        Args:
            row: Zeilen-Index
            
        Returns:
            Aktueller Wert (Type-abhängig: str, float, GUID, etc.)
        """
        pass
    
    @abstractmethod
    def is_value_changed(self, row: int) -> bool:
        """
        Prüft ob Wert geändert wurde.
        
        Args:
            row: Zeilen-Index
            
        Returns:
            True wenn geändert, False sonst
        """
        pass
    
    def get_additional_columns(self) -> List[str]:
        """
        Definiert zusätzliche Spalten nach "Wert"-Spalte.
        
        Returns:
            Liste von Spalten-Namen (z.B. ["Name"] für ViewTable)
            
        Standard: Keine zusätzlichen Spalten
        """
        return []
    
    def create_additional_cells(self, row: int, value: Any) -> None:
        """
        Erstellt Items für zusätzliche Spalten.
        
        Args:
            row: Zeilen-Index
            value: Wert aus "Wert"-Spalte (für Lookup etc.)
            
        Standard: Nichts tun (keine zusätzlichen Spalten)
        """
        pass
    
    def update_additional_cells(self, row: int, new_value: Any) -> None:
        """
        Aktualisiert zusätzliche Spalten nach Wertänderung.
        
        Args:
            row: Zeilen-Index
            new_value: Neuer Wert aus "Wert"-Spalte
            
        Beispiel ViewTable: Neuer Name zu neuer GUID anzeigen
        
        Standard: Nichts tun
        """
        pass
    
    def store_original_value(self, row: int, abdatum: float, value: Any) -> None:
        """
        Speichert Original-Wert für Dirty-Tracking.
        
        Args:
            row: Zeilen-Index
            abdatum: Abdatum
            value: Original-Wert
        """
        self.original_data[row] = (abdatum, value)
    
    def get_original_value(self, row: int) -> Tuple[Optional[float], Any]:
        """
        Holt Original-Wert für Vergleich.
        
        Args:
            row: Zeilen-Index
            
        Returns:
            Tuple (abdatum, original_value) oder (None, None)
        """
        return self.original_data.get(row, (None, None))
