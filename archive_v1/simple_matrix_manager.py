"""
SUPER-EINFACHE Matrix-Verwaltung für PDVM
=========================================

Nur 3 einfache Listen - keine pandas, keine Komplexität:
1. BASIS_DATA    - Alle Rohdaten (unveränderlich)
2. FILTERED_DATA - Nach Filterung 
3. SORTED_DATA   - Nach Sortierung

ExpertMode wird nur bei der finalen Tabellen-Darstellung angewendet.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class SimpleMatrixManager:
    """
    Super-einfache 3-Listen-Verwaltung für PDVM
    
    Kein pandas, keine Komplexität - nur Python-Listen
    """
    
    def __init__(self, view_guid: str):
        self.view_guid = view_guid
        logger.info(f"🏗️ SimpleMatrixManager für {view_guid} initialisiert")
        
        # 3 einfache Listen
        self.basis_data = []         # Alle Rohdaten
        self.filtered_data = []      # Nach Filterung  
        self.sorted_data = []        # Nach Sortierung
        
        # Status
        self.has_basis = False
        self.has_filtered = False
        self.has_sorted = False
        
        # Metadaten
        self.columns = []
        self.current_sort_column = None
        self.current_sort_ascending = True
    
    def set_basis_data(self, data: List[Dict[str, Any]], columns: List[str]):
        """Setzt die BASIS-Daten"""
        try:
            logger.info(f"📊 Setze BASIS_DATA: {len(data)} Zeilen, {len(columns)} Spalten")
            
            self.basis_data = data.copy()
            self.columns = columns.copy()
            self.has_basis = True
            
            # Invalidiere nachgelagerte Listen
            self.has_filtered = False
            self.has_sorted = False
            self.filtered_data = []
            self.sorted_data = []
            
            logger.info("✅ BASIS_DATA gesetzt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Setzen der BASIS_DATA: {e}")
            self.has_basis = False
            raise
    
    def apply_filter(self, filter_func: callable = None):
        """Filtert BASIS_DATA → FILTERED_DATA"""
        try:
            if not self.has_basis:
                raise ValueError("BASIS_DATA ist nicht gültig")
            
            logger.info("🔄 Wende Filter an")
            
            if filter_func:
                self.filtered_data = [row for row in self.basis_data if filter_func(row)]
            else:
                # Kein Filter = alle Daten
                self.filtered_data = self.basis_data.copy()
            
            self.has_filtered = True
            
            # Invalidiere SORTED_DATA
            self.has_sorted = False
            self.sorted_data = []
            
            logger.info(f"✅ Filter angewendet: {len(self.filtered_data)} Zeilen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Filtern: {e}")
            self.has_filtered = False
            raise
    
    def apply_sort(self, column: str = None, ascending: bool = True):
        """Sortiert FILTERED_DATA → SORTED_DATA"""
        try:
            if not self.has_filtered:
                raise ValueError("FILTERED_DATA ist nicht gültig")
            
            if column and column in self.columns:
                logger.info(f"🔄 Sortiere nach '{column}' ({'aufsteigend' if ascending else 'absteigend'})")
                
                # Einfache Python-Sortierung
                self.sorted_data = sorted(
                    self.filtered_data,
                    key=lambda x: x.get(column, '') or '',  # None-Werte als leere Strings behandeln
                    reverse=not ascending
                )
                
                self.current_sort_column = column
                self.current_sort_ascending = ascending
            else:
                # Keine Sortierung
                self.sorted_data = self.filtered_data.copy()
                self.current_sort_column = None
            
            self.has_sorted = True
            
            logger.info(f"✅ Sortierung angewendet: {len(self.sorted_data)} Zeilen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Sortieren: {e}")
            self.has_sorted = False
            raise
    
    def get_table_data(self, visible_columns: List[str] = None) -> List[List[str]]:
        """
        Gibt die finale Tabellen-Daten zurück
        ExpertMode wird über visible_columns gesteuert
        """
        if not self.has_sorted:
            return []
        
        # Bestimme welche Spalten angezeigt werden sollen
        if visible_columns:
            columns_to_show = [col for col in visible_columns if col in self.columns]
        else:
            columns_to_show = self.columns
        
        # Konvertiere zu Liste von Listen für Qt-Tabelle
        table_data = []
        for row in self.sorted_data:
            row_data = []
            for col in columns_to_show:
                value = row.get(col, '')
                row_data.append(str(value) if value is not None else "")
            table_data.append(row_data)
        
        return table_data
    
    def get_table_headers(self, visible_columns: List[str] = None) -> List[str]:
        """Gibt die Tabellen-Header zurück"""
        if visible_columns:
            return [col for col in visible_columns if col in self.columns]
        else:
            return self.columns.copy()
    
    def reset_filter(self):
        """Setzt Filter zurück - zeigt alle BASIS-Daten"""
        if self.has_basis:
            self.filtered_data = self.basis_data.copy()
            self.has_filtered = True
            self.has_sorted = False
            self.sorted_data = []
            logger.info("🔄 Filter zurückgesetzt")
    
    def ensure_filtered_data(self):
        """Stellt sicher, dass FILTERED_DATA gültig ist"""
        if not self.has_filtered:
            self.apply_filter()
    
    def ensure_sorted_data(self):
        """Stellt sicher, dass SORTED_DATA gültig ist"""
        if not self.has_sorted:
            self.apply_sort()
    
    def get_row_count(self) -> int:
        """Gibt die Anzahl der sichtbaren Zeilen zurück"""
        if self.has_sorted:
            return len(self.sorted_data)
        elif self.has_filtered:
            return len(self.filtered_data)
        elif self.has_basis:
            return len(self.basis_data)
        return 0
    
    def get_status(self) -> Dict[str, Any]:
        """Gibt den aktuellen Status zurück"""
        return {
            'basis': {
                'valid': self.has_basis,
                'rows': len(self.basis_data) if self.has_basis else 0
            },
            'filtered': {
                'valid': self.has_filtered,
                'rows': len(self.filtered_data) if self.has_filtered else 0
            },
            'sorted': {
                'valid': self.has_sorted,
                'rows': len(self.sorted_data) if self.has_sorted else 0
            }
        }


# Globaler Manager-Cache
_simple_managers = {}

def get_simple_matrix_manager(view_guid: str) -> SimpleMatrixManager:
    """Factory-Funktion für einfache Matrix-Manager"""
    if view_guid not in _simple_managers:
        _simple_managers[view_guid] = SimpleMatrixManager(view_guid)
        logger.info(f"🏗️ Neuer SimpleMatrixManager für {view_guid} erstellt")
    return _simple_managers[view_guid]