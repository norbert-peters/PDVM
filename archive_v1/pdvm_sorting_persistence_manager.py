#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDVM Sortierung Persistenz Manager
Verwaltet die Sortierrichtung persistent über ViewManager-Integration
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PdvmSortingPersistenceManager:
    """
    Manager für persistente Sortierrichtung-Verwaltung
    
    ARCHITEKTUR:
    - Speichert Sortierrichtung in ViewManager central_systemsteuerung
    - Lädt Sortierung beim Widget-Start
    - Synchronisiert mit ColumnControl wenn verfügbar
    """
    
    def __init__(self, view_manager, view_guid: str):
        """
        Initialisiert den Persistenz-Manager
        
        Args:
            view_manager: ViewManager-Instanz mit central_systemsteuerung
            view_guid: GUID der View für eindeutige Speicherung
        """
        self.view_manager = view_manager
        self.view_guid = view_guid
        self.current_sort_column = None
        self.current_sort_direction = 'asc'
        
        # Gespeicherte Sortierung laden
        self._load_saved_sorting()
        
    def _load_saved_sorting(self):
        """Lädt die gespeicherte Sortierung aus der Systemsteuerung"""
        try:
            if not self.view_manager or not hasattr(self.view_manager, 'central_systemsteuerung'):
                logger.warning("⚠️ Keine central_systemsteuerung verfügbar für Sortier-Persistenz")
                return
                
            # Sortierte Spalte laden
            sort_column_data = self.view_manager.central_systemsteuerung.get_value(
                gruppe=self.view_guid,
                feld="current_sort_column",
                ab_zeit=None
            )
            
            # Sortierrichtung laden
            sort_direction_data = self.view_manager.central_systemsteuerung.get_value(
                gruppe=self.view_guid,
                feld="current_sort_direction", 
                ab_zeit=None
            )
            
            if sort_column_data:
                self.current_sort_column = sort_column_data.get("wert")
                logger.info(f"📊 Gespeicherte Sortier-Spalte geladen: {self.current_sort_column}")
                
            if sort_direction_data:
                self.current_sort_direction = sort_direction_data.get("wert", 'asc')
                logger.info(f"📊 Gespeicherte Sortier-Richtung geladen: {self.current_sort_direction}")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der gespeicherten Sortierung: {e}")
    
    def save_sort_settings(self, column_name: str, direction: str):
        """
        Speichert die aktuelle Sortierung
        
        Args:
            column_name: Name der sortierten Spalte
            direction: Sortierrichtung ('asc' oder 'desc')
        """
        try:
            self.current_sort_column = column_name
            self.current_sort_direction = direction
            
            if not self.view_manager or not hasattr(self.view_manager, 'central_systemsteuerung'):
                logger.warning("⚠️ central_systemsteuerung nicht verfügbar - Sortierung nicht persistent")
                return False
            
            # Sortierte Spalte speichern
            self.view_manager.central_systemsteuerung.set_value(
                gruppe=self.view_guid,
                feld="current_sort_column",
                wert=column_name,
                ab_zeit=1001.0
            )
            
            # Sortierrichtung speichern
            self.view_manager.central_systemsteuerung.set_value(
                gruppe=self.view_guid,
                feld="current_sort_direction",
                wert=direction,
                ab_zeit=1001.0
            )
            
            # Änderungen persistieren
            self.view_manager.central_systemsteuerung.save_values()
            
            logger.info(f"💾 Sortierung gespeichert: {column_name} -> {direction}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Sortierung: {e}")
            return False
    
    def get_sort_settings(self) -> Dict[str, str]:
        """
        Gibt die aktuellen Sortier-Einstellungen zurück
        
        Returns:
            Dict mit 'column' und 'direction'
        """
        return {
            'column': self.current_sort_column,
            'direction': self.current_sort_direction
        }
    
    def apply_saved_sorting_to_table(self, table_widget, current_columns: list):
        """
        Wendet die gespeicherte Sortierung auf die Tabelle an
        
        Args:
            table_widget: QTableWidget-Instanz
            current_columns: Liste der aktuellen Spalten-Namen
        """
        try:
            if not self.current_sort_column or self.current_sort_column not in current_columns:
                logger.debug("📊 Keine gültige gespeicherte Sortierung gefunden")
                return
            
            # Spalten-Index finden
            column_index = current_columns.index(self.current_sort_column)
            
            # Qt-Sortierrichtung konvertieren
            from PyQt5.QtCore import Qt
            qt_order = Qt.AscendingOrder if self.current_sort_direction == 'asc' else Qt.DescendingOrder
            
            # Sortierung anwenden
            table_widget.sortItems(column_index, qt_order)
            
            # Sortier-Indikator im Header setzen
            header = table_widget.horizontalHeader()
            header.setSortIndicator(column_index, qt_order)
            
            logger.info(f"🔄 Gespeicherte Sortierung angewendet: {self.current_sort_column} ({self.current_sort_direction})")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anwenden der gespeicherten Sortierung: {e}")
    
    def sync_with_column_control(self, data_controller):
        """
        Synchronisiert die Sortierung mit dem ColumnControl-System (falls verfügbar)
        
        Args:
            data_controller: DataController mit ColumnControl
        """
        try:
            if not data_controller or not hasattr(data_controller, 'column_control'):
                return
            
            if not self.current_sort_column:
                return
                
            # Prüfe ob Spalte im ColumnControl existiert
            sort_info = data_controller.column_control.get_column_sort_info(self.current_sort_column)
            if sort_info:
                # Synchronisiere mit ColumnControl
                data_controller.column_control.update_sort_settings(
                    self.current_sort_column, 
                    sort_direction=self.current_sort_direction
                )
                
                logger.debug(f"🔄 Sortierung mit ColumnControl synchronisiert: {self.current_sort_column}")
                
        except Exception as e:
            logger.error(f"❌ Fehler bei ColumnControl-Synchronisation: {e}")


if __name__ == "__main__":
    print("📊 PDVM Sortierung Persistenz Manager")
    print("Funktionen:")
    print("- Persistente Sortierrichtung über ViewManager")
    print("- Automatisches Laden beim Widget-Start")
    print("- Synchronisation mit ColumnControl")
    print("- Spalten-übergreifende Persistenz")
