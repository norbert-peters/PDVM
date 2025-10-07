# clean_matrix_integration.py
# INTEGRATION DES CLEAN MATRIX MANAGERS - KEIN FALLBACK!

import logging
from PyQt5.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)

class CleanMatrixIntegration:
    """
    Integration des CleanMatrixManager in ViewDialog
    
    REGEL: Kein Fallback! Ohne Matrix-Manager läuft nichts!
    """
    
    def __init__(self, view_dialog, view_guid):
        self.view_dialog = view_dialog
        self.view_guid = view_guid
        self.matrix_manager = None
        
        # Matrix-Manager MUSS verfügbar sein
        self._initialize_required_matrix_manager()
    
    def _initialize_required_matrix_manager(self):
        """
        Initialisiert Matrix-Manager - KEIN FALLBACK!
        """
        try:
            from clean_matrix_manager import get_clean_matrix_manager
            self.matrix_manager = get_clean_matrix_manager(self.view_guid)
            
            if not self.matrix_manager:
                raise RuntimeError("CleanMatrixManager konnte nicht erstellt werden!")
            
            logger.info("✅ CleanMatrixManager ERFORDERLICH und verfügbar")
            
        except Exception as e:
            error_msg = f"❌ KRITISCHER FEHLER: Matrix-Manager nicht verfügbar!\n{e}\n\nView kann nicht ohne Matrix-Manager funktionieren!"
            logger.error(error_msg)
            
            # Zeige Fehler und beende
            QMessageBox.critical(None, "Matrix-Manager Fehler", error_msg)
            raise RuntimeError("Matrix-Manager ist ERFORDERLICH!")
    
    def initialize_basis_matrix(self, data, columns):
        """
        Initialisiert BASIS_MATRIX - nur bei Start/Stichtag
        """
        if not self.matrix_manager:
            raise RuntimeError("Matrix-Manager nicht verfügbar!")
        
        logger.info("🏗️ Initialisiere BASIS_MATRIX...")
        self.matrix_manager.set_basis_data(data, columns)
        logger.info("✅ BASIS_MATRIX initialisiert")
    
    def apply_filter(self, filter_criteria=None):
        """
        Wendet Filter an - nur FILTERED_MATRIX wird geloggt
        """
        if not self.matrix_manager:
            raise RuntimeError("Matrix-Manager nicht verfügbar!")
        
        self.matrix_manager.apply_filter(filter_criteria)
    
    def apply_sort(self, sort_column, ascending=True):
        """
        Wendet Sortierung an - nur SORTED_MATRIX wird geloggt
        """
        if not self.matrix_manager:
            raise RuntimeError("Matrix-Manager nicht verfügbar!")
        
        # 🎯 SORTIERUNG DURCHFÜHREN
        sort_direction = "aufsteigend" if ascending else "absteigend"
        logger.info(f"📊 === SORTIERUNG START: '{sort_column}' ({sort_direction}) ===")
        
        self.matrix_manager.apply_sort(sort_column, ascending)
        
        # 🎯 MATRIX DEBUG NACH SORTIERUNG
        self._debug_sorted_matrix_after_sort(sort_column, sort_direction)
        
        logger.info(f"📊 === SORTIERUNG ENDE ===")
    
    def apply_sorting_linear(self, sort_config):
        """
        🎯 HAUPT-SORTIER-METHODE: Wird vom matrix_aware_sorting_manager aufgerufen
        
        Args:
            sort_config: Dict mit 'column', 'direction', 'source'
        """
        if not self.matrix_manager:
            raise RuntimeError("Matrix-Manager nicht verfügbar!")
        
        column = sort_config.get('column')
        direction = sort_config.get('direction', 'asc')
        source = sort_config.get('source', 'unknown')
        
        # Konvertiere zu ascending boolean
        ascending = (direction.lower() == 'asc')
        
        logger.info(f"🎯 === LINEAR SORTIERUNG von {source}: '{column}' ({direction}) ===")
        
        # Führe Sortierung durch (das wird die Debug-Ausgabe triggern)
        self.apply_sort(column, ascending)
        
        # Tabelle aktualisieren
        self.refresh_table_from_matrix()
        
        logger.info(f"🎯 === LINEAR SORTIERUNG FERTIG ===")
    
    def _debug_sorted_matrix_after_sort(self, sort_column, sort_direction):
        """
        Debug-Ausgabe der SORTED_MATRIX nach Sortierung
        """
        try:
            sorted_data = self.matrix_manager.sorted_matrix
            columns = self.matrix_manager.columns
            
            logger.info(f"🔍 SORTED_MATRIX Debug nach Sortierung:")
            logger.info(f"   📋 Spalte: {sort_column} ({sort_direction})")
            
            if not sorted_data:
                logger.info(f"   📝 SORTED_MATRIX ist leer")
                return
            
            # Debug-Spalten
            debug_columns = ['uid_original', 'vorname_original', 'vorname_show', 'geburtsdatum_original', 'geburtsdatum_show']
            available_columns = [col for col in debug_columns if col in columns]
            
            if not available_columns:
                logger.info(f"   📝 Debug-Spalten nicht verfügbar")
                logger.info(f"   📝 Verfügbare Spalten: {list(columns)[:5]}...")
                return
            
            logger.info(f"   📋 {len(sorted_data)} Zeilen - Debug-Spalten: {' | '.join(available_columns)}")
            
            # Erste 3 Zeilen nach Sortierung
            for i, row in enumerate(sorted_data[:3]):
                debug_values = []
                for col in available_columns:
                    value = row.get(col, 'N/A')
                    # Kürze lange Werte
                    if isinstance(value, str) and len(value) > 20:
                        value = value[:17] + "..."
                    debug_values.append(str(value))
                
                logger.info(f"   📄 Zeile {i+1}: {' | '.join(debug_values)}")
            
            if len(sorted_data) > 3:
                logger.info(f"   📝 ... und {len(sorted_data) - 3} weitere Zeilen")
                
        except Exception as e:
            logger.error(f"❌ Fehler bei SORTED_MATRIX Debug: {e}")
    
    def get_current_data(self):
        """
        Liefert aktuelle finale Daten für Tabellen-Anzeige
        """
        if not self.matrix_manager:
            raise RuntimeError("Matrix-Manager nicht verfügbar!")
        
        return self.matrix_manager.get_final_data()
    
    def refresh_table_from_matrix(self, expert_mode=None):
        """
        Aktualisiert Tabelle basierend auf Matrix-Daten
        """
        try:
            # Hole aktuelle Matrix-Daten
            current_data = self.get_current_data()
            
            if not current_data:
                logger.warning("⚠️ Keine Matrix-Daten für Tabellen-Refresh verfügbar")
                return
            
            # Bestimme Spalten basierend auf ExpertMode
            if expert_mode is not None:
                columns = self._get_expert_columns() if expert_mode else self._get_standard_columns()
            else:
                # Verwende GCS ExpertMode
                from pdvm_central_systemsteuerung import get_gcs
                gcs = get_gcs()
                columns = self._get_expert_columns() if gcs.expert_mode else self._get_standard_columns()
            
            # Projiziere Tabelle
            self._project_table_clean(current_data, columns)
            
            logger.info("✅ Tabelle aus Matrix-Daten aktualisiert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Matrix-Tabellen-Refresh: {e}")
            raise
    
    def _project_table_clean(self, data, columns):
        """
        Projiziert Tabelle mit exakter Spalten-Daten-Zuordnung
        """
        logger.info(f"📊 Projiziere {len(data)} Zeilen mit {len(columns)} Spalten")
        logger.info(f"📋 Spalten: {columns}")
        
        # Setze Tabellen-Struktur
        table = self.view_dialog.table_widget
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.setRowCount(len(data))
        
        # Fülle Daten - exakt passend zu Spalten
        from PyQt5.QtWidgets import QTableWidgetItem
        
        for row_idx, row_data in enumerate(data):
            for col_idx, column in enumerate(columns):
                # Hole exakten Wert für diese Spalte
                value = row_data.get(column, '')
                
                # Erstelle Table-Item
                item = QTableWidgetItem(str(value))
                table.setItem(row_idx, col_idx, item)
        
        logger.info("✅ Tabellen-Projektion abgeschlossen")
    
    def _get_expert_columns(self):
        """ExpertMode Spalten"""
        return ['familienname', 'vorname', 'strasse', 'geburtsjahr', 'alter', 'telefon', 'email']
    
    def _get_standard_columns(self):
        """Standard Spalten"""
        return ['familienname', 'vorname', 'strasse']
    
    def get_status(self):
        """
        Matrix-Status für Debugging
        """
        if not self.matrix_manager:
            return {'error': 'Matrix-Manager nicht verfügbar'}
        
        return self.matrix_manager.get_status()


def integrate_clean_matrix_manager(view_dialog, view_guid):
    """
    Factory für CleanMatrixIntegration
    """
    try:
        integration = CleanMatrixIntegration(view_dialog, view_guid)
        logger.info(f"✅ CleanMatrixIntegration für {view_guid} erstellt")
        return integration
    
    except Exception as e:
        logger.error(f"❌ CleanMatrixIntegration für {view_guid} fehlgeschlagen: {e}")
        raise