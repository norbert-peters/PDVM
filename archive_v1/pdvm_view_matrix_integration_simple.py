import logging
from typing import Optional

logger = logging.getLogger(__name__)

class PdvmViewMatrixIntegrationSimple:
    """
    Vereinfachte Matrix-Integration für ViewDialog
    
    Verwaltet nur 3 Matrizen:
    - BASIS: Alle Rohdaten
    - FILTERED: Nach Filterung
    - SORTED: Nach Sortierung
    
    ExpertMode wird nur bei der finalen Projektion angewendet.
    """
    
    def __init__(self, view_guid: str, view_dialog):
        self.view_guid = view_guid
        self.view_dialog = view_dialog
        self.matrix_manager = None
        
        logger.info(f"🔗 ViewMatrixIntegration für {view_guid} initialisiert")
    
    def set_matrix_manager(self, matrix_manager):
        """Setzt den Matrix-Manager"""
        self.matrix_manager = matrix_manager
        logger.info("✅ MatrixManager in Integration gesetzt")
    
    def refresh_table_from_matrix(self, expert_mode: bool = False):
        """
        Aktualisiert die Tabelle basierend auf den Matrix-Daten
        ExpertMode bestimmt nur die Spalten-Projektion
        """
        if not self.matrix_manager:
            logger.warning("⚠️ Kein MatrixManager verfügbar")
            return
        
        try:
            # Stelle sicher, dass alle Matrizen gültig sind
            self.matrix_manager.ensure_filtered_matrix()
            self.matrix_manager.ensure_sorted_matrix()
            
            # Hole die Projektions-Tabellen
            if hasattr(self.view_dialog, 'linear_projection') and self.view_dialog.linear_projection:
                if expert_mode:
                    visible_columns = self.view_dialog.linear_projection.table_expert
                else:
                    visible_columns = self.view_dialog.linear_projection.table_standard
                
                # Hole Daten und Header
                data = self.matrix_manager.get_display_data(expert_mode, visible_columns)
                headers = self.matrix_manager.get_column_headers(expert_mode, visible_columns)
                
                # Aktualisiere die Tabelle
                if hasattr(self.view_dialog, 'display') and self.view_dialog.display:
                    self._update_table_widget(data, headers)
                    logger.info(f"✅ Tabelle aktualisiert: {len(data)} Zeilen, {len(headers)} Spalten")
                else:
                    logger.warning("⚠️ Display-Widget nicht verfügbar")
            else:
                logger.warning("⚠️ Linear-Projektion nicht verfügbar")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der Tabelle: {e}")
    
    def _update_table_widget(self, data, headers):
        """Aktualisiert das Qt-Tabellen-Widget"""
        try:
            table = self.view_dialog.display.table
            
            # Setze Header
            table.setColumnCount(len(headers))
            table.setHorizontalHeaderLabels(headers)
            
            # Setze Daten
            table.setRowCount(len(data))
            
            for row_idx, row_data in enumerate(data):
                for col_idx, cell_value in enumerate(row_data):
                    from PyQt5.QtWidgets import QTableWidgetItem
                    item = QTableWidgetItem(str(cell_value))
                    table.setItem(row_idx, col_idx, item)
            
            logger.info(f"✅ Qt-Tabelle aktualisiert: {len(data)} x {len(headers)}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Qt-Tabellen-Update: {e}")
    
    def apply_filter(self, filter_func: callable = None):
        """Wendet Filter über Matrix-Manager an"""
        if self.matrix_manager:
            self.matrix_manager.apply_filter(filter_func)
    
    def apply_sort(self, column: str, ascending: bool = True):
        """Wendet Sortierung über Matrix-Manager an"""
        if self.matrix_manager:
            self.matrix_manager.apply_sort(column, ascending)
    
    def reset_filter(self):
        """Setzt Filter zurück"""
        if self.matrix_manager:
            self.matrix_manager.reset_filter()


def integrate_simple_matrix_manager(view_dialog, view_guid: str):
    """
    Factory-Funktion für einfache Matrix-Integration
    """
    try:
        from pdvm_matrix_manager_simple import get_matrix_manager
        
        # Hole Matrix-Manager
        matrix_manager = get_matrix_manager(view_guid)
        
        # Erstelle Integration
        integration = PdvmViewMatrixIntegrationSimple(view_guid, view_dialog)
        integration.set_matrix_manager(matrix_manager)
        
        logger.info(f"✅ Einfache Matrix-Integration für {view_guid} erstellt")
        return integration
        
    except Exception as e:
        logger.error(f"❌ Fehler bei einfacher Matrix-Integration: {e}")
        return None