# clean_matrix_manager.py
# NEUE ULTRA-EINFACHE 3-MATRIX ARCHITEKTUR ohne pandas
# Nur Python-Listen, komplett linear, mit Debug-Ausgabe

import logging
logger = logging.getLogger(__name__)

class CleanMatrixManager:
    """
    NEUE ULTRA-EINFACHE 3-MATRIX ARCHITEKTUR
    
    - BASIS_MATRIX: Alle Rohdaten (nur bei Start/Stichtag)
    - FILTERED_MATRIX: Nach Filter (nur bei Filter-Änderung) 
    - SORTED_MATRIX: Nach Sortierung (nur bei Sort-Änderung)
    
    KRITISCH: Jede Matrix hat ALLE Daten-Spalten!
    """
    
    def __init__(self, view_guid):
        self.view_guid = view_guid
        
        # Die 3 separaten Matrixen
        self.basis_matrix = []       # Liste von Dictionaries
        self.filtered_matrix = []    # Liste von Dictionaries 
        self.sorted_matrix = []      # Liste von Dictionaries
        
        self.columns = []            # Alle verfügbaren Spalten
        
        logger.info(f"🏗️ CleanMatrixManager für {view_guid} erstellt")
    
    def set_basis_data(self, data, columns):
        """
        Setzt BASIS_MATRIX - nur bei Start oder Stichtag-Wechsel
        """
        self.basis_matrix = data.copy() if data else []
        self.columns = columns.copy() if columns else []
        
        logger.info(f"📊 BASIS_MATRIX gesetzt: {len(self.basis_matrix)} Zeilen, {len(self.columns)} Spalten")
        
        # DEBUG: BASIS_MATRIX ausgeben
        self._debug_matrix("BASIS", self.basis_matrix)
        
        # Initialisiere andere Matrixen mit BASIS
        self.filtered_matrix = self.basis_matrix.copy()
        self.sorted_matrix = self.basis_matrix.copy()
    
    def apply_filter(self, filter_criteria=None):
        """
        Wendet Filter auf BASIS_MATRIX an → FILTERED_MATRIX
        Nur diese Matrix wird geloggt (linear!)
        """
        logger.info("🔍 Wende Filter an...")
        
        if not filter_criteria:
            # Kein Filter = alle Daten
            self.filtered_matrix = self.basis_matrix.copy()
        else:
            # TODO: Filter-Logik implementieren
            self.filtered_matrix = self.basis_matrix.copy()
        
        logger.info(f"✅ Filter angewendet: {len(self.filtered_matrix)} Zeilen")
        
        # DEBUG: Nur FILTERED_MATRIX ausgeben (linear!)
        self._debug_matrix("FILTERED", self.filtered_matrix)
        
        # Sortierte Matrix zurücksetzen auf gefilterte Daten
        self.sorted_matrix = self.filtered_matrix.copy()
    
    def apply_sort(self, sort_column=None, ascending=True):
        """
        Sortiert FILTERED_MATRIX → SORTED_MATRIX
        Nur diese Matrix wird geloggt (linear!)
        """
        logger.info(f"🔀 Sortiere nach: {sort_column} ({'asc' if ascending else 'desc'})")
        
        if not sort_column or sort_column not in self.columns:
            # Keine Sortierung
            self.sorted_matrix = self.filtered_matrix.copy()
        else:
            # Sortiere FILTERED_MATRIX
            try:
                self.sorted_matrix = sorted(
                    self.filtered_matrix,
                    key=lambda row: str(row.get(sort_column, '')),
                    reverse=not ascending
                )
                logger.info(f"✅ Sortierung nach '{sort_column}' angewendet")
            except Exception as e:
                logger.error(f"❌ Sortier-Fehler: {e}")
                self.sorted_matrix = self.filtered_matrix.copy()
        
        # DEBUG: Nur SORTED_MATRIX ausgeben (linear!)
        self._debug_matrix("SORTED", self.sorted_matrix)
    
    def get_final_data(self):
        """
        Liefert die finale SORTED_MATRIX für die View
        """
        return self.sorted_matrix.copy()
    
    def get_status(self):
        """
        Status-Info für Debugging
        """
        return {
            'view_guid': self.view_guid,
            'basis': {'rows': len(self.basis_matrix), 'columns': len(self.columns)},
            'filtered': {'rows': len(self.filtered_matrix)},
            'sorted': {'rows': len(self.sorted_matrix)},
            'columns': self.columns[:5]  # Erste 5 Spalten als Beispiel
        }
    
    def _debug_matrix(self, matrix_name, matrix_data):
        """
        Debug-Ausgabe einer Matrix mit kritischen Spalten
        """
        debug_columns = ['uid_original', 'vorname_original', 'vorname_show', 'geburtsdatum_original', 'geburtsdatum_show']
        
        logger.info(f"🔍 DEBUG {matrix_name}_MATRIX ({len(matrix_data)} Zeilen):")
        
        if not matrix_data:
            logger.info(f"   📝 {matrix_name}_MATRIX ist leer")
            return
        
        # Header
        available_columns = [col for col in debug_columns if col in self.columns]
        if not available_columns:
            logger.info(f"   📝 {matrix_name}_MATRIX: Debug-Spalten nicht verfügbar")
            return
        
        logger.info(f"   📋 Debug-Spalten: {' | '.join(available_columns)}")
        
        # Erste 3 Zeilen als Beispiel
        for i, row in enumerate(matrix_data[:3]):
            debug_values = []
            for col in available_columns:
                value = row.get(col, 'N/A')
                # Kürze lange Werte
                if isinstance(value, str) and len(value) > 20:
                    value = value[:17] + "..."
                debug_values.append(str(value))
            
            logger.info(f"   📄 Zeile {i+1}: {' | '.join(debug_values)}")
        
        if len(matrix_data) > 3:
            logger.info(f"   📝 ... und {len(matrix_data) - 3} weitere Zeilen")

    def debug_current_matrices(self, action_name="Unbekannt"):
        """
        🎯 NEUE DEBUG-METHODE: Zeigt alle 3 Matrizen mit Überschrift
        Kann von überall aufgerufen werden
        """
        logger.info(f"🎯 === MATRIX DEBUG nach: {action_name} ===")
        
        # BASIS_MATRIX
        logger.info(f"🔍 BASIS_MATRIX (Variable: self.basis_matrix):")
        if self.basis_matrix:
            self._debug_matrix("BASIS", self.basis_matrix)
        else:
            logger.info(f"   📝 BASIS_MATRIX ist leer")
        
        # FILTERED_MATRIX
        logger.info(f"🔍 FILTERED_MATRIX (Variable: self.filtered_matrix):")
        if self.filtered_matrix:
            self._debug_matrix("FILTERED", self.filtered_matrix)
        else:
            logger.info(f"   📝 FILTERED_MATRIX ist leer")
        
        # SORTED_MATRIX
        logger.info(f"🔍 SORTED_MATRIX (Variable: self.sorted_matrix):")
        if self.sorted_matrix:
            self._debug_matrix("SORTED", self.sorted_matrix)
        else:
            logger.info(f"   📝 SORTED_MATRIX ist leer")
        
        logger.info(f"🎯 === ENDE MATRIX DEBUG ===")
    
    def _debug_matrix(self, matrix_name, matrix_data):
        """
        Debug-Ausgabe einer Matrix mit kritischen Spalten
        """
        debug_columns = ['uid_original', 'vorname_original', 'vorname_show', 'geburtsdatum_original', 'geburtsdatum_show']
        
        logger.info(f"🔍 DEBUG {matrix_name}_MATRIX ({len(matrix_data)} Zeilen):")
        
        if not matrix_data:
            logger.info(f"   📝 {matrix_name}_MATRIX ist leer")
            return
        
        # Header
        available_columns = [col for col in debug_columns if col in self.columns]
        if not available_columns:
            logger.info(f"   📝 {matrix_name}_MATRIX: Debug-Spalten nicht verfügbar")
            return
        
        logger.info(f"   📋 Debug-Spalten: {' | '.join(available_columns)}")
        
        # Erste 3 Zeilen als Beispiel
        for i, row in enumerate(matrix_data[:3]):
            debug_values = []
            for col in available_columns:
                value = row.get(col, 'N/A')
                # Kürze lange Werte
                if isinstance(value, str) and len(value) > 20:
                    value = value[:17] + "..."
                debug_values.append(str(value))
            
            logger.info(f"   📄 Zeile {i+1}: {' | '.join(debug_values)}")
        
        if len(matrix_data) > 3:
            logger.info(f"   📝 ... und {len(matrix_data) - 3} weitere Zeilen")


# Factory Function
_matrix_managers = {}

def get_clean_matrix_manager(view_guid):
    """
    Factory für CleanMatrixManager - ein Manager pro View
    """
    if view_guid not in _matrix_managers:
        _matrix_managers[view_guid] = CleanMatrixManager(view_guid)
        logger.info(f"🏗️ Neuer CleanMatrixManager für {view_guid} erstellt")
    else:
        logger.info(f"♻️ CleanMatrixManager für {view_guid} wiederverwendet")
    
    return _matrix_managers[view_guid]

def reset_matrix_managers():
    """
    Alle Matrix-Manager zurücksetzen
    """
    global _matrix_managers
    _matrix_managers.clear()
    logger.info("🔄 Alle Matrix-Manager zurückgesetzt")