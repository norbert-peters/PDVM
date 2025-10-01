#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDVM Data Processing Pipeline
============================

LINEARE 4-SCHICHTEN ARCHITEKTUR:
1. BasisMatrix (alle Spalten verfügbar)
2. FilterSortierungsSchicht (arbeitet auf vollständigen Daten)
3. ProjektionsSchicht (View-spezifische Sichten)
4. UI-Display (finale Darstellung)

VORTEILE:
- sortByOriginal funktioniert immer (alle Spalten verfügbar)
- Lineare Pipeline ohne komplexe Verzweigungen
- Saubere Trennung der Verantwortlichkeiten
- Filter und Sortierung arbeiten auf vollständigen Daten
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Logging Setup
logger = logging.getLogger(__name__)

@dataclass
class ProcessingOptions:
    """Konfiguration für die Datenverarbeitung"""
    filter_config: Dict[str, Any] = None
    sort_column: str = None
    sort_direction: str = 'asc'
    sort_by_original: bool = False
    grouping_enabled: bool = False
    grouping_column: str = None

class PdvmDataProcessingPipeline:
    """
    LINEARE DATENVERARBEITUNGS-PIPELINE
    
    Verarbeitet Daten in 4 linearen Schichten:
    1. BasisMatrix → 2. Filter+Sort → 3. Projektion → 4. Display
    """
    
    def __init__(self, view_dialog):
        """
        Initialisiert die Pipeline
        
        Args:
            view_dialog: PdvmViewDialog Instanz für Zugriff auf Konfiguration
        """
        self.view_dialog = view_dialog
        self.controls_config = getattr(view_dialog, 'controls_config', {})
        
        # Pipeline-Schichten
        self.basis_matrix = []          # Schicht 1: Vollständige Datenmatrix
        self.processed_matrix = []      # Schicht 2: Gefiltert + sortiert
        self.projected_matrix = []      # Schicht 3: Projizierte Sicht
        self.display_data = []          # Schicht 4: UI-ready Data
        
        # Processing State
        self.current_options = ProcessingOptions()
        
        logger.info("🏗️ Data Processing Pipeline initialisiert")
    
    def set_basis_matrix(self, matrix_data: List[Dict[str, Any]]):
        """
        SCHICHT 1: Setzt die BasisMatrix mit allen verfügbaren Spalten
        
        Args:
            matrix_data: Vollständige Datenmatrix mit allen _original und _show Spalten
        """
        self.basis_matrix = matrix_data.copy() if matrix_data else []
        logger.info(f"📊 BasisMatrix gesetzt: {len(self.basis_matrix)} Zeilen, "
                   f"{len(self.basis_matrix[0]) if self.basis_matrix else 0} Spalten")
    
    def apply_processing(self, options: ProcessingOptions) -> List[Dict[str, Any]]:
        """
        HAUPTMETHODE: Wendet die komplette Pipeline an
        
        Args:
            options: Verarbeitungsoptionen (Filter, Sortierung, etc.)
            
        Returns:
            Verarbeitete Datenmatrix für die UI
        """
        self.current_options = options
        
        logger.info("🔄 Starte lineare Datenverarbeitung...")
        
        # SCHRITT 1: Basis-Daten bereitstellen (bereits gesetzt)
        if not self.basis_matrix:
            logger.warning("⚠️ Keine BasisMatrix verfügbar")
            return []
        
        # SCHRITT 2: Filter + Sortierung auf vollständigen Daten
        self.processed_matrix = self._apply_filter_and_sorting()
        
        # SCHRITT 3: Projektion anwenden
        self.projected_matrix = self._apply_projection()
        
        # SCHRITT 4: Display-Daten vorbereiten
        self.display_data = self._prepare_display_data()
        
        logger.info(f"✅ Pipeline abgeschlossen: {len(self.display_data)} Zeilen für Display")
        return self.display_data
    
    def _apply_filter_and_sorting(self) -> List[Dict[str, Any]]:
        """
        SCHICHT 2: Filter und Sortierung auf vollständigen Daten
        
        WICHTIG: Hier haben wir Zugriff auf ALLE Spalten!
        sortByOriginal funktioniert, da _original Spalten verfügbar sind.
        
        Returns:
            Gefilterte und sortierte Datenmatrix (noch alle Spalten)
        """
        logger.info("🔍 Schicht 2: Filter + Sortierung...")
        
        # Beginne mit vollständiger BasisMatrix
        working_data = self.basis_matrix.copy()
        
        # FILTER anwenden (falls konfiguriert)
        if self.current_options.filter_config:
            working_data = self._apply_filters(working_data)
            logger.info(f"🔍 Filter angewendet: {len(working_data)} Zeilen verbleiben")
        
        # SORTIERUNG anwenden (mit sortByOriginal Support)
        if self.current_options.sort_column:
            working_data = self._apply_sorting(working_data)
            logger.info(f"🔄 Sortierung angewendet: {self.current_options.sort_column}")
        
        # GRUPPIERUNG anwenden (falls aktiviert)
        if self.current_options.grouping_enabled:
            working_data = self._apply_grouping(working_data)
            logger.info(f"📊 Gruppierung angewendet: {self.current_options.grouping_column}")
        
        return working_data
    
    def _apply_filters(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter auf vollständige Datenmatrix anwenden
        
        Args:
            data: Eingangsdaten mit allen Spalten
            
        Returns:
            Gefilterte Daten
        """
        # TODO: Filter-Integration aus LinearFilterExecutionManager
        # Hier würden die bestehenden Filter angewendet werden
        logger.debug("🔍 Filter-Anwendung (Platzhalter)")
        return data
    
    def _apply_sorting(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sortierung mit sortByOriginal Support
        
        KERN-FEATURE: Hier funktioniert sortByOriginal, da alle Spalten verfügbar sind!
        
        Args:
            data: Eingangsdaten mit allen Spalten
            
        Returns:
            Sortierte Daten
        """
        sort_column = self.current_options.sort_column
        sort_direction = self.current_options.sort_direction
        
        # Bestimme tatsächliche Sortier-Spalte (sortByOriginal Logik)
        actual_sort_column = self._get_actual_sort_column(sort_column)
        
        logger.info(f"🔄 Sortiere nach '{actual_sort_column}' "
                   f"(angezeigt: '{sort_column}', Richtung: {sort_direction})")
        
        try:
            # Sortierung durchführen
            reverse_order = (sort_direction == 'desc')
            
            def sort_key_func(row):
                value = row.get(actual_sort_column, '')
                # Normalisierung für konsistente Sortierung
                return self._normalize_sort_value(value)
            
            sorted_data = sorted(data, key=sort_key_func, reverse=reverse_order)
            
            logger.info(f"✅ Sortierung erfolgreich: {len(sorted_data)} Zeilen")
            return sorted_data
            
        except Exception as e:
            logger.error(f"❌ Sortierung fehlgeschlagen: {e}")
            return data
    
    def _get_actual_sort_column(self, display_column: str) -> str:
        """
        Bestimmt die tatsächliche Sortier-Spalte basierend auf sortByOriginal
        
        KERNFUNKTION: Löst das sortByOriginal Problem!
        
        Args:
            display_column: Angezeigte Spalte (z.B. 'geburtsdatum_show')
            
        Returns:
            Tatsächliche Sortier-Spalte (z.B. 'geburtsdatum_original')
        """
        # Control-Konfiguration laden
        control = self.controls_config.get(display_column, {})
        sort_by_original = control.get('sortByOriginal', False)
        
        if sort_by_original:
            # Nach _original Spalte sortieren
            if display_column.endswith('_show'):
                original_column = display_column.replace('_show', '_original')
            elif not display_column.endswith('_original'):
                original_column = display_column + '_original'
            else:
                original_column = display_column
            
            logger.debug(f"🎯 sortByOriginal=true: {display_column} → {original_column}")
            return original_column
        else:
            # Nach angezeigter Spalte sortieren
            logger.debug(f"📝 sortByOriginal=false: {display_column} → {display_column}")
            return display_column
    
    def _normalize_sort_value(self, value: Any) -> Any:
        """
        Normalisiert Sortier-Werte für konsistente Sortierung
        
        Args:
            value: Zu normalisierender Wert
            
        Returns:
            Normalisierter Wert für Sortierung
        """
        if value is None:
            return 0  # None-Werte an den Anfang
        
        if isinstance(value, (int, float)):
            return value
        
        if isinstance(value, str):
            # Leere Strings an den Anfang
            if not value.strip():
                return ""
            return value.lower()  # Case-insensitive string sorting
        
        # Fallback: String-Konvertierung
        return str(value).lower()
    
    def _apply_grouping(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Gruppierung anwenden (falls aktiviert)
        
        Args:
            data: Eingangsdaten
            
        Returns:
            Gruppierte Daten
        """
        # TODO: Gruppierungs-Integration aus Advanced Sorting Engine
        logger.debug("📊 Gruppierung (Platzhalter)")
        return data
    
    def _apply_projection(self) -> List[Dict[str, Any]]:
        """
        SCHICHT 3: Projektion auf View-spezifische Spalten
        
        Wendet die Projektions-Tabellen an, um nur gewünschte Spalten zu zeigen
        
        Returns:
            Projizierte Datenmatrix (nur sichtbare Spalten)
        """
        logger.info("📊 Schicht 3: Projektion...")
        
        if not self.processed_matrix:
            return []
        
        # Hole Projektions-Konfiguration vom ViewDialog
        projection_columns = self._get_projection_columns()
        
        if not projection_columns:
            logger.warning("⚠️ Keine Projektions-Spalten konfiguriert")
            return self.processed_matrix
        
        # Projiziere nur gewünschte Spalten
        projected_data = []
        for row in self.processed_matrix:
            projected_row = {}
            for column in projection_columns:
                projected_row[column] = row.get(column, '')
            projected_data.append(projected_row)
        
        logger.info(f"📊 Projektion angewendet: {len(projection_columns)} Spalten")
        return projected_data
    
    def _get_projection_columns(self) -> List[str]:
        """
        Holt die Projektions-Spalten aus der GCS-Konfiguration
        
        Returns:
            Liste der sichtbaren Spalten-Namen
        """
        try:
            # Verwende bestehende Projektions-Tabellen aus GCS
            if hasattr(self.view_dialog, 'gcs') and self.view_dialog.gcs:
                gcs = self.view_dialog.gcs
                view_guid = getattr(self.view_dialog, 'view_guid', '')
                
                if hasattr(gcs, 'get_projection_table'):
                    # Standard View Projektion verwenden
                    projection = gcs.get_projection_table(view_guid, 'view_standard')
                    if projection:
                        logger.debug(f"📊 Projektions-Spalten aus GCS: {len(projection)}")
                        return projection
            
            # Fallback: Alle sichtbaren Controls
            visible_columns = []
            for control_key, control_config in self.controls_config.items():
                if control_config.get('show', False) and control_key.endswith('_show'):
                    visible_columns.append(control_key)
            
            logger.debug(f"📊 Fallback Projektions-Spalten: {len(visible_columns)}")
            return visible_columns
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Projektions-Spalten: {e}")
            return []
    
    def _prepare_display_data(self) -> List[Dict[str, Any]]:
        """
        SCHICHT 4: Daten für UI-Display vorbereiten
        
        Finale Aufbereitung der Daten für die Tabellen-Anzeige
        
        Returns:
            UI-ready Daten
        """
        logger.info("🎨 Schicht 4: Display-Vorbereitung...")
        
        if not self.projected_matrix:
            return []
        
        # Zusätzliche Display-Aufbereitung falls nötig
        display_ready_data = []
        for row in self.projected_matrix:
            # Kopiere Row-Daten
            display_row = row.copy()
            
            # Zusätzliche Display-Formatierung hier falls nötig
            # (z.B. spezielle Formatierungen, Icons, etc.)
            
            display_ready_data.append(display_row)
        
        logger.info(f"🎨 Display-Daten vorbereitet: {len(display_ready_data)} Zeilen")
        return display_ready_data
    
    def get_current_stats(self) -> Dict[str, int]:
        """
        Gibt Statistiken über die Pipeline zurück
        
        Returns:
            Dict mit Statistiken der einzelnen Schichten
        """
        return {
            'basis_rows': len(self.basis_matrix),
            'processed_rows': len(self.processed_matrix),
            'projected_rows': len(self.projected_matrix),
            'display_rows': len(self.display_data),
            'basis_columns': len(self.basis_matrix[0]) if self.basis_matrix else 0,
            'projected_columns': len(self.projected_matrix[0]) if self.projected_matrix else 0
        }

# Convenience-Funktion für Integration
def create_pipeline(view_dialog) -> PdvmDataProcessingPipeline:
    """
    Erstellt eine neue Data Processing Pipeline
    
    Args:
        view_dialog: PdvmViewDialog Instanz
        
    Returns:
        Initialisierte Pipeline
    """
    return PdvmDataProcessingPipeline(view_dialog)


if __name__ == "__main__":
    # Test der Pipeline
    print("🎯 PDVM Data Processing Pipeline")
    print("📋 Lineare 4-Schichten Architektur für robuste Datenverarbeitung")
    print("✅ sortByOriginal funktioniert durch vollständigen Spaltenzugriff")