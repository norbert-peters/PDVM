"""
PDVM VIEW MATRIX INTEGRATION
============================

Integration des 4-Schichten MatrixManagers in den ViewManager:

1. MatrixManager verwaltet Schichten 1-3 (alle Spalten)
2. ViewManager verwaltet Schicht 4 (Projektion) 
3. Vollständige Linearität zwischen den Schichten
4. Automatische Synchronisation bei Änderungen

USAGE PATTERN:
--------------
```python
# 1. MatrixManager initialisieren
matrix_manager = get_matrix_manager(view_guid, gcs)

# 2. Basis-Daten setzen
matrix_manager.set_basis_matrix(raw_data, all_columns)

# 3. Filter anwenden
matrix_manager.apply_filter(filter_config)

# 4. Sortierung anwenden  
matrix_manager.apply_sorting(sort_config)

# 5. Projizierte Darstellung für View
display_data = matrix_manager.get_display_matrix()
projected_data = view_manager.apply_projection(display_data, projection_config)
```
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from pdvm_matrix_manager import get_matrix_manager, PdvmMatrixManager

logger = logging.getLogger(__name__)

class PdvmViewMatrixIntegration:
    """
    INTEGRATION DES MATRIX-MANAGERS IN VIEW-SYSTEM
    
    Verbindet den 4-Schichten MatrixManager mit dem bestehenden View-System:
    - Automatische Matrix-Synchronisation
    - Projektions-Anwendung auf DISPLAY_MATRIX
    - Event-basierte Updates zwischen Schichten
    """
    
    def __init__(self, view_dialog):
        self.view_dialog = view_dialog
        self.view_guid = getattr(view_dialog, 'view_guid', 'unknown')
        
        # GCS-Instanz holen
        from pdvm_central_systemsteuerung import get_gcs
        self.gcs = get_gcs()
        
        if not self.gcs:
            raise RuntimeError("GCS nicht verfügbar für MatrixIntegration")
        
        # Matrix-Manager initialisieren
        self.matrix_manager = get_matrix_manager(self.view_guid, self.gcs)
        
        logger.info(f"🔗 ViewMatrixIntegration für {self.view_guid} initialisiert")
    
    # ==========================================
    # SCHICHT 1-3: MATRIX MANAGER DELEGATION  
    # ==========================================
    
    def initialize_with_data(self, raw_data: List[Dict[str, Any]], all_columns: List[str]):
        """
        INITIALIZATION: Setze Basis-Daten und initialisiere alle Schichten
        
        Args:
            raw_data: Rohdaten aus Datenbank (alle Zeilen, alle Spalten)
            all_columns: Alle verfügbaren Spalten-Namen
        """
        logger.info(f"🚀 Initialisiere Matrix mit {len(raw_data)} Zeilen, {len(all_columns)} Spalten")
        
        try:
            # SCHICHT 1: Basis-Matrix setzen
            self.matrix_manager.set_basis_matrix(raw_data, all_columns)
            
            # SCHICHT 2: Initial ohne Filter (alle Daten)
            self.matrix_manager.clear_filter()
            
            # SCHICHT 3: Initial ohne Sortierung/Gruppierung
            self.matrix_manager.clear_display_modifications()
            
            # SCHICHT 4: Projizierte Darstellung aktualisieren
            self._update_view_projection()
            
            logger.info("✅ Matrix vollständig initialisiert")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Matrix-Initialisierung: {e}")
            return False
    
    def apply_filter_linear(self, filter_config: Dict[str, Any]):
        """
        FILTER: Linear auf Schicht 1→2, invalidiert Schicht 3+4
        
        Args:
            filter_config: Filter-Konfiguration
        """
        logger.info("🔍 Wende linearen Filter an")
        
        try:
            # SCHICHT 2: Filter anwenden (BASIS_MATRIX → FILTER_MATRIX)
            success = self.matrix_manager.apply_filter(filter_config)
            
            if success:
                # SCHICHT 3: Display-Modifikationen zurücksetzen (FILTER_MATRIX → DISPLAY_MATRIX)
                self.matrix_manager.clear_display_modifications()
                
                # SCHICHT 4: View-Projektion aktualisieren
                self._update_view_projection()
                
                logger.info("✅ Linearer Filter erfolgreich angewendet")
            else:
                logger.error("❌ Filter-Anwendung fehlgeschlagen")
                
        except Exception as e:
            logger.error(f"❌ Fehler bei linearem Filter: {e}")
    
    def apply_sorting_linear(self, sort_config: Dict[str, Any]):
        """
        SORTING: Linear auf Schicht 2→3, aktualisiert Schicht 4
        
        Args:
            sort_config: Sortier-Konfiguration
        """
        logger.info("🔄 Wende lineare Sortierung an")
        
        try:
            # SCHICHT 3: Sortierung anwenden (FILTER_MATRIX → DISPLAY_MATRIX)
            success = self.matrix_manager.apply_sorting(sort_config)
            
            if success:
                # SCHICHT 4: View-Projektion aktualisieren
                self._update_view_projection()
                
                logger.info("✅ Lineare Sortierung erfolgreich angewendet")
            else:
                logger.error("❌ Sortierung fehlgeschlagen")
                
        except Exception as e:
            logger.error(f"❌ Fehler bei linearer Sortierung: {e}")
    
    def apply_grouping_linear(self, group_config: Dict[str, Any]):
        """
        GROUPING: Linear auf Schicht 2→3, aktualisiert Schicht 4
        
        Args:
            group_config: Gruppierungs-Konfiguration
        """
        logger.info("📊 Wende lineare Gruppierung an")
        
        try:
            # SCHICHT 3: Gruppierung anwenden (FILTER_MATRIX → DISPLAY_MATRIX)
            success = self.matrix_manager.apply_grouping(group_config)
            
            if success:
                # SCHICHT 4: View-Projektion aktualisieren
                self._update_view_projection()
                
                logger.info("✅ Lineare Gruppierung erfolgreich angewendet")
            else:
                logger.error("❌ Gruppierung fehlgeschlagen")
                
        except Exception as e:
            logger.error(f"❌ Fehler bei linearer Gruppierung: {e}")
    
    # ==========================================
    # SCHICHT 4: VIEW-PROJEKTION
    # ==========================================
    
    def _update_view_projection(self):
        """
        SCHICHT 4: Wendet Projektion auf DISPLAY_MATRIX an → View-Darstellung
        
        Diese Methode:
        1. Holt DISPLAY_MATRIX (alle Spalten, gefiltert/sortiert)
        2. Wendet aktuelle Spalten-Projektion an
        3. Aktualisiert die View-Tabelle
        """
        logger.debug("🎯 Aktualisiere View-Projektion...")
        
        try:
            # DISPLAY_MATRIX holen (alle Spalten)
            display_data = self.matrix_manager.get_display_matrix()
            
            if not display_data:
                logger.info("ℹ️ Keine Display-Daten für Projektion verfügbar")
                self._clear_view_table()
                return
            
            # Aktuelle Spalten-Projektion holen
            projected_columns = self._get_current_projection()
            
            if not projected_columns:
                logger.warning("⚠️ Keine Spalten-Projektion verfügbar")
                return
            
            # Projektion anwenden: Nur projizierte Spalten extrahieren
            projected_data = []
            for row in display_data:
                projected_row = {}
                for column in projected_columns:
                    projected_row[column] = row.get(column, '')
                projected_data.append(projected_row)
            
            # View-Tabelle aktualisieren
            self._update_table_widget(projected_data, projected_columns)
            
            logger.debug(f"✅ View-Projektion: {len(projected_data)} Zeilen, {len(projected_columns)} Spalten")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei View-Projektion: {e}")
    
    def _get_current_projection(self) -> List[str]:
        """
        Holt aktuelle Spalten-Projektion aus LinearProjectionManager
        
        Returns:
            Liste der sichtbaren Spalten-Namen
        """
        try:
            # LinearProjectionManager verwenden für konsistente Projektion
            from linear_projection_manager import get_projection_manager
            projection_manager = get_projection_manager(self.view_guid, self.gcs)
            
            # Table-Projektion holen (abhängig von ExpertMode)
            table_projection = projection_manager.get_table_projection()
            
            logger.debug(f"📋 Aktuelle Projektion: {len(table_projection)} Spalten")
            return table_projection
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Holen der Projektion: {e}")
            return []
    
    def _update_table_widget(self, projected_data: List[Dict[str, Any]], columns: List[str]):
        """
        Aktualisiert das QTableWidget mit projizierten Daten
        
        Args:
            projected_data: Projizierte Daten (nur sichtbare Spalten)
            columns: Spalten-Namen in korrekter Reihenfolge
        """
        try:
            if not hasattr(self.view_dialog, 'display') or not hasattr(self.view_dialog.display, 'table'):
                logger.warning("⚠️ Keine View-Tabelle verfügbar")
                return
            
            table = self.view_dialog.display.table
            
            # Tabelle zurücksetzen
            table.setRowCount(0)
            table.setColumnCount(len(columns))
            
            # Header setzen mit korrekten Spalten-Namen
            self._set_table_headers(table, columns)
            
            # Daten einfügen
            table.setRowCount(len(projected_data))
            
            for row_idx, row_data in enumerate(projected_data):
                for col_idx, column in enumerate(columns):
                    value = row_data.get(column, '')
                    
                    # QTableWidgetItem erstellen
                    from PyQt5.QtWidgets import QTableWidgetItem
                    item = QTableWidgetItem(str(value))
                    table.setItem(row_idx, col_idx, item)
            
            logger.debug(f"📊 Tabelle aktualisiert: {len(projected_data)} Zeilen × {len(columns)} Spalten")
            
            # Legacy display_matrix für Kompatibilität setzen
            self._update_legacy_display_matrix(projected_data)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der Tabelle: {e}")
    
    def _set_table_headers(self, table, columns: List[str]):
        """
        Setzt die Tabellen-Header mit korrekten Spalten-Überschriften
        
        Args:
            table: QTableWidget
            columns: Spalten-Namen
        """
        try:
            # Controls für Display-Namen holen
            controls_config = getattr(self.view_dialog, 'controls_config', {})
            
            headers = []
            for column in columns:
                # Display-Name aus Controls holen
                control_data = controls_config.get(column, {})
                display_name = control_data.get('spaltenueberschrift', column)
                headers.append(str(display_name))
            
            table.setHorizontalHeaderLabels(headers)
            logger.debug(f"📋 Header gesetzt: {headers}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Setzen der Header: {e}")
            # Fallback: Verwende Spalten-Namen
            table.setHorizontalHeaderLabels(columns)
    
    def _update_legacy_display_matrix(self, projected_data: List[Dict[str, Any]]):
        """
        Aktualisiert die Legacy display_matrix für Rückwärts-Kompatibilität
        
        Args:
            projected_data: Projizierte Daten
        """
        try:
            # Legacy display_matrix setzen (für bestehende Funktionen)
            if hasattr(self.view_dialog, 'display_matrix'):
                # Erweitere um display=True für Sichtbarkeit
                legacy_matrix = []
                for row in projected_data:
                    legacy_row = row.copy()
                    legacy_row['display'] = True  # Alle projizierten Zeilen sind sichtbar
                    legacy_matrix.append(legacy_row)
                
                self.view_dialog.display_matrix = legacy_matrix
                logger.debug(f"🔄 Legacy display_matrix aktualisiert: {len(legacy_matrix)} Zeilen")
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Legacy-Matrix Update: {e}")
    
    def _clear_view_table(self):
        """Leert die View-Tabelle"""
        try:
            if hasattr(self.view_dialog, 'display') and hasattr(self.view_dialog.display, 'table'):
                self.view_dialog.display.table.setRowCount(0)
                logger.debug("🗑️ View-Tabelle geleert")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Leeren der Tabelle: {e}")
    
    # ==========================================
    # EVENT HANDLERS FÜR BESTEHENDE SYSTEME
    # ==========================================
    
    def handle_expert_mode_change(self):
        """
        Event-Handler für ExpertMode-Wechsel
        
        Aktualisiert nur Schicht 4 (Projektion), Daten bleiben unverändert
        """
        logger.info("🔬 ExpertMode-Wechsel - aktualisiere Projektion")
        
        try:
            # Nur Projektion neu berechnen, Daten-Schichten bleiben unverändert
            self._update_view_projection()
            
            logger.info("✅ ExpertMode-Wechsel abgeschlossen")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei ExpertMode-Wechsel: {e}")
    
    def handle_column_visibility_change(self):
        """
        Event-Handler für Spalten-Sichtbarkeits-Änderungen
        
        Aktualisiert nur Schicht 4 (Projektion)
        """
        logger.info("👁️ Spalten-Sichtbarkeit geändert - aktualisiere Projektion")
        
        try:
            # ProjectionManager aktualisieren
            from linear_projection_manager import get_projection_manager
            projection_manager = get_projection_manager(self.view_guid, self.gcs)
            projection_manager.handle_expert_mode_change()  # Neuberechnung
            
            # View-Projektion aktualisieren
            self._update_view_projection()
            
            logger.info("✅ Spalten-Sichtbarkeit aktualisiert")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Spalten-Sichtbarkeit: {e}")
    
    # ==========================================
    # DEBUGGING & STATUS
    # ==========================================
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Gibt detaillierten Status der Integration zurück"""
        matrix_status = self.matrix_manager.get_status_summary()
        
        return {
            'view_guid': self.view_guid,
            'matrix_manager': matrix_status,
            'integration': {
                'view_dialog_available': hasattr(self, 'view_dialog'),
                'table_widget_available': (hasattr(self.view_dialog, 'display') and 
                                         hasattr(self.view_dialog.display, 'table')),
                'gcs_available': self.gcs is not None
            }
        }
    
    def debug_matrix_flow(self):
        """Debug-Ausgabe des kompletten Matrix-Flows"""
        logger.info("🔍 DEBUG: Matrix-Flow Analyse")
        logger.info("="*50)
        
        status = self.get_integration_status()
        matrix_status = status['matrix_manager']
        
        logger.info(f"View: {self.view_guid}")
        logger.info(f"Spalten: {matrix_status['columns_count']}")
        
        for layer_name, layer_info in matrix_status['layers'].items():
            valid_str = "✅" if layer_info['valid'] else "❌"
            logger.info(f"  {layer_name.upper()}: {valid_str} {layer_info['rows']} Zeilen")
        
        # Aktuelle Projektion
        try:
            projection = self._get_current_projection()
            logger.info(f"  PROJECTION: {len(projection)} Spalten → {projection[:5]}...")
        except:
            logger.info(f"  PROJECTION: ❌ Nicht verfügbar")
        
        logger.info("="*50)


# ==========================================
# FACTORY & INTEGRATION HELPERS
# ==========================================

def integrate_matrix_manager(view_dialog) -> PdvmViewMatrixIntegration:
    """
    Integriert den MatrixManager in einen ViewDialog
    
    Args:
        view_dialog: ViewDialog-Instanz
        
    Returns:
        PdvmViewMatrixIntegration Instanz
    """
    try:
        integration = PdvmViewMatrixIntegration(view_dialog)
        
        # Integration in ViewDialog speichern
        view_dialog.matrix_integration = integration
        
        logger.info(f"✅ MatrixManager erfolgreich in ViewDialog integriert")
        return integration
        
    except Exception as e:
        logger.error(f"❌ Fehler bei MatrixManager-Integration: {e}")
        raise

def replace_legacy_display_matrix(view_dialog, raw_data: List[Dict[str, Any]], all_columns: List[str]):
    """
    Ersetzt das Legacy display_matrix System durch den neuen MatrixManager
    
    Args:
        view_dialog: ViewDialog-Instanz
        raw_data: Rohdaten aus Datenbank
        all_columns: Alle verfügbaren Spalten
    """
    try:
        # MatrixManager integrieren falls noch nicht geschehen
        if not hasattr(view_dialog, 'matrix_integration'):
            integrate_matrix_manager(view_dialog)
        
        # Initialisierung mit neuen Daten
        view_dialog.matrix_integration.initialize_with_data(raw_data, all_columns)
        
        logger.info("✅ Legacy display_matrix erfolgreich durch MatrixManager ersetzt")
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Ersetzen des Legacy-Systems: {e}")
        raise