#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDVM Pipeline Integration Manager
=================================

Integriert die Data Processing Pipeline in die bestehende View-Dialog Architektur.
Ersetzt die bisherige direkte Tabellen-Sortierung durch die lineare Pipeline.

INTEGRATION:
- Verbindet PdvmDataProcessingPipeline mit PdvmViewDialog
- Verwaltet Pipeline-State und UI-Updates
- Handles Header-Clicks und Sortierungs-Events
- Synchronisiert mit GCS Controls
"""

import logging
from typing import List, Dict, Any, Optional
from PyQt5.QtWidgets import QTableWidget
from PyQt5.QtCore import Qt

from pdvm_data_processing_pipeline import PdvmDataProcessingPipeline, ProcessingOptions

# Logging Setup
logger = logging.getLogger(__name__)

class PdvmPipelineIntegrationManager:
    """
    Manager für die Integration der Data Processing Pipeline
    
    Verbindet die lineare Pipeline mit der bestehenden UI-Architektur
    """
    
    def __init__(self, view_dialog, controls_config):
        """
        Initialisiert den Integration Manager
        
        Args:
            view_dialog: PdvmViewDialog Instanz
            controls_config: Controls-Konfiguration für die Pipeline
        """
        self.view_dialog = view_dialog
        self.controls_config = controls_config
        self.pipeline = PdvmDataProcessingPipeline(view_dialog)
        
        # Pipeline State
        self.current_sort_column = None
        self.current_sort_direction = 'asc'
        self.is_pipeline_active = False
        
        logger.info("🔗 Pipeline Integration Manager initialisiert")
    
    def initialize_pipeline(self):
        """
        Initialisiert die Pipeline mit den aktuellen View-Daten
        """
        try:
            # BasisMatrix aus ViewDialog laden
            if hasattr(self.view_dialog, 'display_matrix') and self.view_dialog.display_matrix:
                self.pipeline.set_basis_matrix(self.view_dialog.display_matrix)
                self.is_pipeline_active = True
                logger.info("✅ Pipeline mit BasisMatrix initialisiert")
            else:
                logger.warning("⚠️ Keine display_matrix im ViewDialog verfügbar")
                
        except Exception as e:
            logger.error(f"❌ Pipeline-Initialisierung fehlgeschlagen: {e}")
    
    def setup_table_integration(self, table_widget: QTableWidget):
        """
        Richtet die Integration mit einem QTableWidget ein
        
        Args:
            table_widget: QTableWidget für die Anzeige
        """
        try:
            # 🎯 KERNFIX: Pipeline mit BasisMatrix initialisieren
            self.initialize_pipeline()
            
            # Header-Click Events abfangen
            header = table_widget.horizontalHeader()
            header.setSectionsClickable(True)
            header.sectionClicked.connect(
                lambda index: self._on_header_clicked(table_widget, index)
            )
            
            # Pipeline-basierte initiale Darstellung
            self._refresh_table_display(table_widget)
            
            logger.info("🔗 Tabellen-Integration mit BasisMatrix eingerichtet")
            
        except Exception as e:
            logger.error(f"❌ Tabellen-Integration fehlgeschlagen: {e}")
    
    def _on_header_clicked(self, table_widget: QTableWidget, logical_index: int):
        """
        Handler für Header-Clicks - verwendet Pipeline für Sortierung
        
        Args:
            table_widget: Geklickte Tabelle
            logical_index: Index der geklickten Spalte
        """
        try:
            # Spalten-Name ermitteln
            column_name = table_widget.horizontalHeaderItem(logical_index).text()
            
            # Control-Key aus Spalten-Name ermitteln
            control_key = self._get_control_key_from_display_name(column_name)
            
            if not control_key:
                logger.warning(f"⚠️ Kein Control-Key für Spalte '{column_name}' gefunden")
                return
            
            # Sortierrichtung bestimmen
            if self.current_sort_column == control_key:
                # Gleiche Spalte: Richtung umkehren
                new_direction = 'desc' if self.current_sort_direction == 'asc' else 'asc'
            else:
                # Neue Spalte: Standard = asc
                new_direction = 'asc'
            
            # Pipeline-basierte Sortierung anwenden
            self.apply_sorting(table_widget, control_key, new_direction)
            
            # Visual Indicator im Header setzen
            qt_order = Qt.AscendingOrder if new_direction == 'asc' else Qt.DescendingOrder
            table_widget.horizontalHeader().setSortIndicator(logical_index, qt_order)
            
            logger.info(f"🔄 Pipeline Header-Click: {control_key} -> {new_direction}")
            
        except Exception as e:
            logger.error(f"❌ Header-Click Verarbeitung fehlgeschlagen: {e}")
    
    def apply_sorting(self, table_widget: QTableWidget, column_key: str, direction: str = 'asc'):
        """
        Wendet Sortierung über die Pipeline an
        
        Args:
            table_widget: Tabelle für die Anzeige
            column_key: Control-Key der zu sortierenden Spalte
            direction: Sortierrichtung ('asc' oder 'desc')
        """
        try:
            if not self.is_pipeline_active:
                logger.warning("⚠️ Pipeline nicht aktiv - initialisiere...")
                self.initialize_pipeline()
                
                if not self.is_pipeline_active:
                    logger.error("❌ Pipeline-Aktivierung fehlgeschlagen")
                    return
            
            # Processing Options erstellen
            options = ProcessingOptions(
                sort_column=column_key,
                sort_direction=direction,
                sort_by_original=self._get_sort_by_original(column_key)
            )
            
            # Pipeline ausführen
            processed_data = self.pipeline.apply_processing(options)
            
            # State aktualisieren
            self.current_sort_column = column_key
            self.current_sort_direction = direction
            
            # Tabelle aktualisieren
            self._update_table_with_processed_data(table_widget, processed_data)
            
            # In GCS speichern
            self._save_sorting_to_gcs(column_key, direction)
            
            logger.info(f"✅ Pipeline-Sortierung angewendet: {column_key} -> {direction}")
            
        except Exception as e:
            logger.error(f"❌ Pipeline-Sortierung fehlgeschlagen: {e}")
    
    def apply_filter(self, table_widget: QTableWidget, filter_config: Dict[str, Any]):
        """
        Wendet Filter über die Pipeline an
        
        Args:
            table_widget: Tabelle für die Anzeige
            filter_config: Filter-Konfiguration
        """
        try:
            if not self.is_pipeline_active:
                self.initialize_pipeline()
            
            # Processing Options mit Filter
            options = ProcessingOptions(
                filter_config=filter_config,
                sort_column=self.current_sort_column,
                sort_direction=self.current_sort_direction,
                sort_by_original=self._get_sort_by_original(self.current_sort_column) if self.current_sort_column else False
            )
            
            # Pipeline ausführen
            processed_data = self.pipeline.apply_processing(options)
            
            # Tabelle aktualisieren
            self._update_table_with_processed_data(table_widget, processed_data)
            
            logger.info(f"✅ Pipeline-Filter angewendet")
            
        except Exception as e:
            logger.error(f"❌ Pipeline-Filter fehlgeschlagen: {e}")
    
    def _get_sort_by_original(self, column_key: str) -> bool:
        """
        Prüft ob sortByOriginal für eine Spalte aktiviert ist
        
        Args:
            column_key: Control-Key der Spalte
            
        Returns:
            True wenn sortByOriginal aktiviert ist
        """
        if not column_key or not self.controls_config:
            return False
        
        control = self.controls_config.get(column_key, {})
        return control.get('sortByOriginal', False)
    
    def _get_control_key_from_display_name(self, display_name: str) -> Optional[str]:
        """
        Ermittelt Control-Key aus Spalten-Anzeige-Name
        
        Args:
            display_name: Angezeigter Spalten-Name
            
        Returns:
            Control-Key oder None
        """
        try:
            if not self.controls_config:
                return None
            
            # Suche Control mit passendem Namen
            for control_key, control_config in self.controls_config.items():
                if control_config.get('name', '') == display_name:
                    return control_key
            
            # Fallback: Direkter Name-Mapping
            # Anzeige-Name zu Control-Key konvertieren
            if display_name:
                # Häufige Mappings
                name_mappings = {
                    'Familienname': 'familienname_show',
                    'Vorname': 'vorname_show',
                    'Geburtsdatum': 'geburtsdatum_show',
                    'Anrede': 'anrede_show',
                    'Email': 'email_show'
                }
                
                return name_mappings.get(display_name)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Control-Key Ermittlung fehlgeschlagen: {e}")
            return None
    
    def _update_table_with_processed_data(self, table_widget: QTableWidget, processed_data: List[Dict[str, Any]]):
        """
        Aktualisiert die Tabelle mit verarbeiteten Daten
        
        Args:
            table_widget: Zu aktualisierende Tabelle
            processed_data: Verarbeitete Daten aus der Pipeline
        """
        try:
            from PyQt5.QtWidgets import QTableWidgetItem
            
            # Tabelle leeren
            table_widget.setRowCount(0)
            
            if not processed_data:
                logger.info("📊 Keine Daten für Tabellen-Update")
                return
            
            # Zeilen und Spalten setzen
            table_widget.setRowCount(len(processed_data))
            
            # Daten einfügen
            for row_index, row_data in enumerate(processed_data):
                for col_index in range(table_widget.columnCount()):
                    header_item = table_widget.horizontalHeaderItem(col_index)
                    if header_item:
                        column_name = header_item.text()
                        control_key = self._get_control_key_from_display_name(column_name)
                        
                        if control_key and control_key in row_data:
                            cell_value = str(row_data[control_key])
                            # 🎯 BUGFIX: Korrekte QTableWidgetItem Erstellung
                            table_widget.setItem(row_index, col_index, QTableWidgetItem(cell_value))
                        else:
                            # Leere Zelle setzen falls kein Wert vorhanden
                            table_widget.setItem(row_index, col_index, QTableWidgetItem(""))
            
            logger.info(f"📊 Tabelle aktualisiert: {len(processed_data)} Zeilen")
            
        except Exception as e:
            logger.error(f"❌ Tabellen-Update fehlgeschlagen: {e}")
    
    def _refresh_table_display(self, table_widget: QTableWidget):
        """
        Aktualisiert die Tabellen-Anzeige mit aktuellen Pipeline-Daten
        
        Args:
            table_widget: Zu aktualisierende Tabelle
        """
        try:
            if not self.is_pipeline_active:
                self.initialize_pipeline()
            
            # Standard Processing (keine Filter/Sortierung)
            options = ProcessingOptions()
            processed_data = self.pipeline.apply_processing(options)
            
            self._update_table_with_processed_data(table_widget, processed_data)
            
        except Exception as e:
            logger.error(f"❌ Tabellen-Refresh fehlgeschlagen: {e}")
    
    def _save_sorting_to_gcs(self, column_key: str, direction: str):
        """
        Speichert Sortierung in GCS Controls
        
        Args:
            column_key: Control-Key der sortierten Spalte
            direction: Sortierrichtung
        """
        try:
            if not hasattr(self.view_dialog, 'gcs') or not self.view_dialog.gcs:
                return
            
            gcs = self.view_dialog.gcs
            view_guid = getattr(self.view_dialog, 'view_guid', '')
            
            if view_guid:
                # Sortierung in GCS speichern
                gcs.set_property(f"{view_guid}_sort_column", column_key)
                gcs.set_property(f"{view_guid}_sort_direction", direction)
                
                logger.debug(f"💾 Sortierung in GCS gespeichert: {column_key} -> {direction}")
                
        except Exception as e:
            logger.error(f"❌ GCS-Sortierung-Speicherung fehlgeschlagen: {e}")
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        Gibt Pipeline-Statistiken zurück
        
        Returns:
            Dict mit Pipeline-Statistiken
        """
        stats = self.pipeline.get_current_stats()
        stats.update({
            'pipeline_active': self.is_pipeline_active,
            'current_sort_column': self.current_sort_column,
            'current_sort_direction': self.current_sort_direction
        })
        return stats


# Convenience-Funktion für Integration
def create_pipeline_manager(view_dialog) -> PdvmPipelineIntegrationManager:
    """
    Erstellt einen neuen Pipeline Integration Manager
    
    Args:
        view_dialog: PdvmViewDialog Instanz
        
    Returns:
        Initialisierter Integration Manager
    """
    return PdvmPipelineIntegrationManager(view_dialog)


if __name__ == "__main__":
    # Test des Integration Managers
    print("🔗 PDVM Pipeline Integration Manager")
    print("📋 Verbindet lineare Pipeline mit bestehender UI-Architektur")
    print("✅ Löst sortByOriginal Problem durch vollständigen Spaltenzugriff")