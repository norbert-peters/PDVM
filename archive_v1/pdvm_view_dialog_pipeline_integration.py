#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDVM ViewDialog Pipeline Integration
===================================

Erweitert den bestehenden PdvmViewDialog um die neue Data Processing Pipeline.
Diese Erweiterung ersetzt das bisherige Sortierungs-System durch die lineare Pipeline.

INTEGRATION STRATEGY:
- Minimal invasive Änderungen am bestehenden Code
- Pipeline wird parallel zum bestehenden System eingeführt
- Graduelle Migration möglich
- Fallback auf bestehendes System wenn Pipeline nicht verfügbar
"""

import logging
from typing import Optional, Dict, Any
from PyQt5.QtWidgets import QTableWidget

# Logging Setup
logger = logging.getLogger(__name__)

class PdvmViewDialogPipelineExtension:
    """
    Erweitert PdvmViewDialog um Pipeline-Funktionalität
    
    Diese Klasse kann als Mixin oder Extension verwendet werden
    """
    
    def __init__(self, view_dialog):
        """
        Initialisiert die Pipeline-Erweiterung
        
        Args:
            view_dialog: Bestehende PdvmViewDialog Instanz
        """
        self.view_dialog = view_dialog
        self.pipeline_manager = None
        self.pipeline_enabled = False
        
        # Pipeline initialisieren
        self._initialize_pipeline()
        
        logger.info("🔗 ViewDialog Pipeline Extension initialisiert")
    
    def _initialize_pipeline(self):
        """Initialisiert die Pipeline-Integration"""
        try:
            from pdvm_pipeline_integration_manager import create_pipeline_manager
            
            # Pipeline Manager erstellen
            self.pipeline_manager = create_pipeline_manager(self.view_dialog)
            
            # Pipeline mit aktuellen Daten initialisieren
            if hasattr(self.view_dialog, 'display_matrix'):
                self.pipeline_manager.initialize_pipeline()
                self.pipeline_enabled = True
                logger.info("✅ Pipeline erfolgreich initialisiert")
            else:
                logger.warning("⚠️ Keine display_matrix verfügbar - Pipeline wird später initialisiert")
                
        except ImportError as e:
            logger.warning(f"⚠️ Pipeline-Module nicht verfügbar: {e}")
            self.pipeline_enabled = False
        except Exception as e:
            logger.error(f"❌ Pipeline-Initialisierung fehlgeschlagen: {e}")
            self.pipeline_enabled = False
    
    def setup_pipeline_table_integration(self, table_widget: QTableWidget):
        """
        Richtet Pipeline-Integration für eine Tabelle ein
        
        Args:
            table_widget: QTableWidget für Pipeline-Integration
        """
        if not self.pipeline_enabled or not self.pipeline_manager:
            logger.warning("⚠️ Pipeline nicht verfügbar - verwende Standard-System")
            return False
        
        try:
            # Pipeline-basierte Tabellen-Integration
            self.pipeline_manager.setup_table_integration(table_widget)
            logger.info("✅ Pipeline-Tabellen-Integration eingerichtet")
            return True
            
        except Exception as e:
            logger.error(f"❌ Pipeline-Tabellen-Integration fehlgeschlagen: {e}")
            return False
    
    def apply_pipeline_sorting(self, table_widget: QTableWidget, column_key: str, direction: str = 'asc'):
        """
        Wendet Pipeline-basierte Sortierung an
        
        Args:
            table_widget: Zu sortierende Tabelle
            column_key: Control-Key der Spalte
            direction: Sortierrichtung
            
        Returns:
            True wenn Pipeline-Sortierung angewendet wurde, False für Fallback
        """
        if not self.pipeline_enabled or not self.pipeline_manager:
            logger.debug("📋 Pipeline nicht verfügbar - Fallback auf Standard-Sortierung")
            return False
        
        try:
            # Pipeline-basierte Sortierung anwenden
            self.pipeline_manager.apply_sorting(table_widget, column_key, direction)
            logger.info(f"✅ Pipeline-Sortierung angewendet: {column_key} -> {direction}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Pipeline-Sortierung fehlgeschlagen: {e} - Fallback auf Standard")
            return False
    
    def refresh_pipeline_data(self):
        """Aktualisiert Pipeline mit neuen Daten"""
        if not self.pipeline_enabled or not self.pipeline_manager:
            return
        
        try:
            # Pipeline mit aktuellen display_matrix Daten aktualisieren
            if hasattr(self.view_dialog, 'display_matrix'):
                self.pipeline_manager.initialize_pipeline()
                logger.debug("🔄 Pipeline-Daten aktualisiert")
                
        except Exception as e:
            logger.error(f"❌ Pipeline-Daten-Aktualisierung fehlgeschlagen: {e}")
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        Gibt Pipeline-Statistiken zurück
        
        Returns:
            Pipeline-Statistiken oder leeres Dict
        """
        if not self.pipeline_enabled or not self.pipeline_manager:
            return {'pipeline_enabled': False}
        
        try:
            stats = self.pipeline_manager.get_pipeline_stats()
            stats['pipeline_enabled'] = True
            return stats
        except Exception as e:
            logger.error(f"❌ Pipeline-Stats Abruf fehlgeschlagen: {e}")
            return {'pipeline_enabled': False, 'error': str(e)}


def extend_view_dialog_with_pipeline(view_dialog):
    """
    Erweitert einen bestehenden PdvmViewDialog um Pipeline-Funktionalität
    
    Args:
        view_dialog: Bestehende PdvmViewDialog Instanz
        
    Returns:
        ViewDialog mit Pipeline-Extension
    """
    try:
        # Pipeline-Extension hinzufügen
        pipeline_extension = PdvmViewDialogPipelineExtension(view_dialog)
        
        # Extension als Attribut am ViewDialog anhängen
        view_dialog.pipeline_extension = pipeline_extension
        
        # Convenience-Methoden am ViewDialog hinzufügen
        view_dialog.setup_pipeline_table = pipeline_extension.setup_pipeline_table_integration
        view_dialog.apply_pipeline_sorting = pipeline_extension.apply_pipeline_sorting
        view_dialog.refresh_pipeline_data = pipeline_extension.refresh_pipeline_data
        view_dialog.get_pipeline_stats = pipeline_extension.get_pipeline_stats
        
        logger.info("✅ ViewDialog erfolgreich um Pipeline erweitert")
        return view_dialog
        
    except Exception as e:
        logger.error(f"❌ ViewDialog Pipeline-Erweiterung fehlgeschlagen: {e}")
        return view_dialog


# Patch-Funktion für bestehende Sortierungs-Manager
def patch_sorting_manager_with_pipeline(sorting_manager, view_dialog):
    """
    Erweitert einen bestehenden PdvmSortingManager um Pipeline-Funktionalität
    
    Args:
        sorting_manager: Bestehende PdvmSortingManager Instanz
        view_dialog: Zugehörige PdvmViewDialog Instanz
    """
    try:
        # Pipeline-Extension für ViewDialog sicherstellen
        if not hasattr(view_dialog, 'pipeline_extension'):
            extend_view_dialog_with_pipeline(view_dialog)
        
        # Original apply_sorting Methode speichern
        original_apply_sorting = sorting_manager.apply_sorting
        
        def pipeline_enhanced_apply_sorting(table_widget, column_key, direction='asc'):
            """Enhanced apply_sorting mit Pipeline-Support"""
            try:
                # Versuche Pipeline-Sortierung
                if hasattr(view_dialog, 'apply_pipeline_sorting'):
                    pipeline_success = view_dialog.apply_pipeline_sorting(table_widget, column_key, direction)
                    
                    if pipeline_success:
                        # Pipeline erfolgreich - State aktualisieren
                        sorting_manager.current_sort_column = column_key
                        sorting_manager.current_sort_direction = direction
                        logger.info(f"✅ Pipeline-Enhanced Sortierung: {column_key} -> {direction}")
                        return
                
                # Fallback auf Original-Methode
                logger.debug("📋 Fallback auf Original-Sortierung")
                original_apply_sorting(table_widget, column_key, direction)
                
            except Exception as e:
                logger.error(f"❌ Pipeline-Enhanced Sortierung fehlgeschlagen: {e}")
                # Notfall-Fallback
                original_apply_sorting(table_widget, column_key, direction)
        
        # Methode ersetzen
        sorting_manager.apply_sorting = pipeline_enhanced_apply_sorting
        
        logger.info("✅ SortingManager erfolgreich um Pipeline erweitert")
        
    except Exception as e:
        logger.error(f"❌ SortingManager Pipeline-Patch fehlgeschlagen: {e}")


if __name__ == "__main__":
    # Test der Pipeline-Integration
    print("🔗 PDVM ViewDialog Pipeline Integration")
    print("📋 Minimal invasive Erweiterung für bestehende ViewDialogs")
    print("✅ Graduelle Migration mit Fallback-Funktionalität")