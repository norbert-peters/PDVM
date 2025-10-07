"""
PDVM SORTING MANAGER - Matrix-Manager Integration
===============================================

Erweitert den bestehenden PdvmSortingManager um MatrixManager-Unterstützung:
- Header-Click und Dialog-Sort verwenden gleiche Datenquelle
- Lineare Pipeline: DISPLAY_MATRIX → Sortierung → VIEW_PROJECTION
- Konsistente Daten-Spalten Zuordnung

REPARIERT:
- Geburtsjahr steht nicht mehr unter Vorname-Header
- Dialog-Sortierung funktioniert wie Header-Sortierung
- Alle Sortier-Operationen arbeiten auf DISPLAY_MATRIX
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MatrixAwareSortingManager:
    """
    Matrix-bewusster Sorting-Manager
    
    Erweitert bestehende Sorting-Manager um MatrixManager-Integration
    """
    
    def __init__(self, view_dialog, gcs_instance):
        self.view_dialog = view_dialog
        self.gcs = gcs_instance
        self.matrix_integration = None
        
        logger.info("🔄 Matrix-bewusster Sorting-Manager initialisiert")
    
    def set_matrix_integration(self, matrix_integration):
        """
        Verknüpft den Sorting-Manager mit dem MatrixManager
        
        Args:
            matrix_integration: PdvmViewMatrixIntegration Instanz
        """
        self.matrix_integration = matrix_integration
        logger.info("🔗 Sorting-Manager mit Matrix-Manager verknüpft")
    
    def handle_header_click_sorting(self, column_index: int, sort_order):
        """
        Header-Click Sortierung über MatrixManager
        
        Args:
            column_index: Index der geklickten Spalte
            sort_order: Qt.SortOrder (AscendingOrder/DescendingOrder)
        """
        try:
            if not self.matrix_integration:
                logger.warning("⚠️ Matrix-Integration nicht verfügbar - verwende Legacy-Sortierung")
                return False
            
            # Spalten-Name aus aktueller Projektion ermitteln
            column_name = self._get_column_name_by_index(column_index)
            if not column_name:
                logger.error(f"❌ Spalten-Name für Index {column_index} nicht gefunden")
                return False
            
            # Sortier-Konfiguration erstellen
            direction = 'asc' if sort_order == 0 else 'desc'  # Qt.AscendingOrder = 0
            sort_config = {
                'column': column_name,
                'direction': direction,
                'source': 'header_click'
            }
            
            logger.info(f"🔄 Header-Click Sortierung: {column_name} ({direction})")
            
            # Über MatrixManager sortieren
            self.matrix_integration.apply_sorting_linear(sort_config)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Header-Click Sortierung: {e}")
            return False
    
    def handle_dialog_sorting(self, column_name: str, direction: str):
        """
        Dialog-Sortierung über MatrixManager
        
        Args:
            column_name: Name der zu sortierenden Spalte
            direction: Sortierrichtung ('asc'/'desc')
        """
        try:
            if not self.matrix_integration:
                logger.warning("⚠️ Matrix-Integration nicht verfügbar - verwende Legacy-Sortierung")
                return False
            
            # Sortier-Konfiguration erstellen
            sort_config = {
                'column': column_name,
                'direction': direction,
                'source': 'dialog'
            }
            
            logger.info(f"🔄 Dialog-Sortierung: {column_name} ({direction})")
            
            # Über MatrixManager sortieren
            self.matrix_integration.apply_sorting_linear(sort_config)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Dialog-Sortierung: {e}")
            return False
    
    def _get_column_name_by_index(self, column_index: int) -> Optional[str]:
        """
        Ermittelt Spalten-Name anhand des Tabellen-Index
        
        Args:
            column_index: Index der Spalte in der Tabelle
            
        Returns:
            Spalten-Name oder None
        """
        try:
            if not self.matrix_integration:
                return None
            
            # Aktuelle Projektion holen
            projection = self.matrix_integration._get_current_projection()
            
            if column_index < len(projection):
                return projection[column_index]
            
            logger.warning(f"⚠️ Spalten-Index {column_index} außerhalb der Projektion ({len(projection)} Spalten)")
            return None
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Ermitteln des Spalten-Namens: {e}")
            return None
    
    def clear_sorting(self):
        """Sortierung zurücksetzen"""
        try:
            if self.matrix_integration:
                # MatrixManager: Zurück zu unsortierten FILTER_MATRIX Daten
                self.matrix_integration.matrix_manager.clear_display_modifications()
                self.matrix_integration._update_view_projection()
                logger.info("✅ Sortierung über MatrixManager zurückgesetzt")
            else:
                logger.warning("⚠️ Matrix-Integration nicht verfügbar für Reset")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Zurücksetzen der Sortierung: {e}")
    
    def get_sortable_columns(self):
        """
        Gibt sortierbare Spalten zurück
        
        Returns:
            Liste von (column_key, display_name) Tupeln
        """
        try:
            if not self.matrix_integration:
                return []
            
            # Projektierte Spalten verwenden
            projection = self.matrix_integration._get_current_projection()
            
            # Display-Namen aus Controls holen
            controls_config = getattr(self.view_dialog, 'controls_config', {})
            
            result = []
            for column_key in projection:
                control_data = controls_config.get(column_key, {})
                display_name = control_data.get('spaltenueberschrift', column_key)
                result.append((column_key, str(display_name)))
            
            logger.debug(f"📊 {len(result)} sortierbare Spalten verfügbar")
            return result
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der sortierbaren Spalten: {e}")
            return []


def extend_sorting_manager_with_matrix(sorting_manager, matrix_integration):
    """
    Erweitert einen bestehenden PdvmSortingManager um MatrixManager-Funktionalität
    
    Args:
        sorting_manager: Bestehender PdvmSortingManager
        matrix_integration: PdvmViewMatrixIntegration Instanz
    """
    try:
        # Matrix-bewusste Erweiterung hinzufügen
        sorting_manager.matrix_aware = MatrixAwareSortingManager(
            sorting_manager.view_dialog, 
            sorting_manager.gcs if hasattr(sorting_manager, 'gcs') else None
        )
        
        sorting_manager.matrix_aware.set_matrix_integration(matrix_integration)
        
        # Original-Methoden erweitern
        _patch_sorting_methods(sorting_manager)
        
        logger.info("✅ PdvmSortingManager erfolgreich um MatrixManager-Funktionalität erweitert")
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Erweitern des SortingManagers: {e}")


def _patch_sorting_methods(sorting_manager):
    """
    Erweitert bestehende Sortier-Methoden um MatrixManager-Support
    
    Args:
        sorting_manager: PdvmSortingManager Instanz
    """
    
    # Original-Methoden sichern
    original_on_header_clicked = getattr(sorting_manager, '_on_header_clicked', None)
    original_apply_advanced_sorting = getattr(sorting_manager, 'apply_advanced_sorting', None)
    
    def _enhanced_on_header_clicked(logical_index, sort_order):
        """Erweiterte Header-Click Behandlung mit MatrixManager"""
        try:
            # Matrix-Manager Sortierung versuchen
            if (hasattr(sorting_manager, 'matrix_aware') and 
                sorting_manager.matrix_aware.handle_header_click_sorting(logical_index, sort_order)):
                logger.info("✅ Header-Click über MatrixManager verarbeitet")
                return
        except Exception as e:
            logger.error(f"❌ MatrixManager Header-Click Fehler: {e}")
        
        # Fallback: Original-Methode
        if original_on_header_clicked:
            original_on_header_clicked(logical_index, sort_order)
        else:
            logger.warning("⚠️ Keine Original _on_header_clicked Methode verfügbar")
    
    def _enhanced_apply_advanced_sorting(engine, group_config):
        """Erweiterte Dialog-Sortierung mit MatrixManager"""
        try:
            # Sortier-Konfiguration aus Engine extrahieren
            if hasattr(engine, 'sort_levels') and engine.sort_levels:
                first_level = engine.sort_levels[0]
                column_name = first_level.get('column')
                direction = first_level.get('direction', 'asc')
                
                # Matrix-Manager Sortierung versuchen
                if (hasattr(sorting_manager, 'matrix_aware') and 
                    sorting_manager.matrix_aware.handle_dialog_sorting(column_name, direction)):
                    logger.info("✅ Dialog-Sortierung über MatrixManager verarbeitet")
                    return True
        except Exception as e:
            logger.error(f"❌ MatrixManager Dialog-Sortierung Fehler: {e}")
        
        # Fallback: Original-Methode
        if original_apply_advanced_sorting:
            return original_apply_advanced_sorting(engine, group_config)
        else:
            logger.warning("⚠️ Keine Original apply_advanced_sorting Methode verfügbar")
            return False
    
    # Methoden überschreiben
    sorting_manager._on_header_clicked = _enhanced_on_header_clicked
    sorting_manager.apply_advanced_sorting = _enhanced_apply_advanced_sorting
    
    logger.info("🔧 Sorting-Manager Methoden erfolgreich erweitert")