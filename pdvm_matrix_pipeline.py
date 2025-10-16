#!/usr/bin/env python3
"""
PDVM Matrix Pipeline - Vollständige lineare Datenverarbeitungs-Pipeline

ARCHITEKTUR (User-Vorgabe):
1. BasisMatrix: ALLE Spalten, ALLE 3 Ebenen, ALLE Records aus DB
2. FilterMatrix: Filter auf BasisMatrix anwenden → FilterMatrix (ALLE Spalten behalten!)
3. SortMatrix: Sortierung auf FilterMatrix anwenden → SortMatrix (ALLE Spalten behalten!)
4. Projektion: ERST HIER Reduktion auf sichtbare Spalten
5. View: Anzeige der projizierten Daten

WICHTIG:
- Bis zur Projektion: IMMER vollständige Matrix mit ALLEN Spalten
- 3-Ebenen-Struktur: {key}, {key}__abdatum, {key}__formatiert
- Bei Stichtag-Wechsel: BasisMatrix neu befüllen, Pipeline komplett durchlaufen
- Bei Spalten-Änderung: Nur Projektion neu, SortMatrix bleibt unverändert
"""

import logging
from typing import Dict, List, Any, Optional
from copy import deepcopy

logger = logging.getLogger(__name__)


class MatrixBase:
    """Basis-Klasse für alle Matrix-Typen"""
    
    def __init__(self, matrix_type: str):
        self.matrix_type = matrix_type
        self.data: List[Dict[str, Any]] = []  # Liste von Row-Dicts
        self.columns: List[str] = []  # Alle Spaltennamen (inkl. __abdatum, __formatiert)
        
    def get_row_count(self) -> int:
        """Anzahl der Zeilen"""
        return len(self.data)
    
    def get_column_count(self) -> int:
        """Anzahl der Spalten"""
        return len(self.columns)
    
    def get_row(self, index: int) -> Optional[Dict[str, Any]]:
        """Holt eine Zeile nach Index"""
        if 0 <= index < len(self.data):
            return self.data[index]
        return None
    
    def get_value(self, row_index: int, column_name: str) -> Any:
        """Holt einen Wert"""
        row = self.get_row(row_index)
        if row:
            return row.get(column_name)
        return None
    
    def log_sample(self, row_count: int = 3, field_name: str = 'familienname'):
        """Loggt Beispiel-Daten mit 3-Ebenen-Struktur - INTELLIGENT für alle Matrix-Typen"""
        logger.info(f"📊 === {self.matrix_type} ({len(self.data)} Zeilen, {len(self.columns)} Spalten) ===")
        
        for i in range(min(row_count, len(self.data))):
            row = self.data[i]
            
            # UID: Versuche uid_original oder uid_show
            uid = row.get('uid_original', row.get('uid_show', 'UNBEKANNT'))
            
            # Zeige 3 Ebenen für das Beispiel-Feld
            # Suche INTELLIGENTLY: Welche Keys hat diese Matrix tatsächlich?
            original_key = f"{field_name}_original"
            show_key = f"{field_name}_show"
            
            # Prüfe welche Keys verfügbar sind (priorisiere _original, dann _show)
            test_keys = [original_key, show_key]
            for key in test_keys:
                if key in row:
                    wert = row.get(key, '')
                    abdatum = row.get(f"{key}_abdatum", None)  # ORIGINAL SUFFIX!
                    formatiert = row.get(f"{key}_formatiertes_abdatum", None)  # ORIGINAL SUFFIX!
                    logger.info(f"  Row {i} ({uid}): {key}")
                    logger.info(f"    EBENE 1: {wert}")
                    logger.info(f"    EBENE 2 (abdatum): {abdatum}")
                    logger.info(f"    EBENE 3 (formatiert): {formatiert}")


class BasisMatrix(MatrixBase):
    """
    BasisMatrix: ALLE Spalten, ALLE 3 Ebenen, ALLE Records
    Direkt aus DB geladen mit Stichtag
    """
    
    def __init__(self):
        super().__init__("BasisMatrix")
        
    def build_from_column_control(self, column_control, all_columns: List[str]):
        """
        Baut BasisMatrix aus Column Control auf
        
        Args:
            column_control: ColumnControl Instanz mit set_row_data/get_row_data
            all_columns: Liste ALLER Spaltennamen (inkl. _abdatum, _formatiertes_abdatum)
        """
        logger.info("🔨 === BAUE BASISMATRIX aus Column Control ===")
        
        self.columns = all_columns
        self.data = []
        
        # Alle GUIDs durchgehen
        for guid in column_control.row_guids:
            row_data = column_control.get_row_data(guid)
            self.data.append(row_data)
        
        # DEBUG: Zeige Keys der ersten Zeile
        if self.data:
            first_row_keys = list(self.data[0].keys())
            familienname_keys = [k for k in first_row_keys if 'familienname' in k.lower()]
            logger.info(f"🔍 Erste Zeile hat {len(first_row_keys)} Keys")
            logger.info(f"🔍 Familienname-Keys: {familienname_keys}")
        
        logger.info(f"✅ BasisMatrix erstellt: {len(self.data)} Zeilen, {len(self.columns)} Spalten")
        self.log_sample(row_count=1)


class FilterMatrix(MatrixBase):
    """
    FilterMatrix: Filter auf BasisMatrix anwenden
    WICHTIG: ALLE Spalten bleiben erhalten!
    """
    
    def __init__(self):
        super().__init__("FilterMatrix")
        
    def build_from_basis(self, basis_matrix: BasisMatrix, filter_func=None):
        """
        Baut FilterMatrix aus BasisMatrix
        
        Args:
            basis_matrix: Quell-BasisMatrix
            filter_func: Optional - Filterfunktion (row_dict) -> bool
        """
        logger.info("🔨 === BAUE FILTERMATRIX aus BasisMatrix ===")
        
        # ALLE Spalten übernehmen
        self.columns = basis_matrix.columns.copy()
        
        # Filter anwenden (wenn vorhanden)
        if filter_func:
            self.data = [row for row in basis_matrix.data if filter_func(row)]
            logger.info(f"🔍 Filter angewendet: {len(basis_matrix.data)} → {len(self.data)} Zeilen")
        else:
            # Kein Filter: Alle Zeilen übernehmen (Deep Copy für Unabhängigkeit)
            self.data = deepcopy(basis_matrix.data)
            logger.info(f"✅ Kein Filter: {len(self.data)} Zeilen übernommen")
        
        logger.info(f"✅ FilterMatrix erstellt: {len(self.data)} Zeilen, {len(self.columns)} Spalten")
        self.log_sample(row_count=1)


class SortMatrix(MatrixBase):
    """
    SortMatrix: Sortierung auf FilterMatrix anwenden
    WICHTIG: ALLE Spalten bleiben erhalten!
    Quelle für Projektion
    """
    
    def __init__(self):
        super().__init__("SortMatrix")
        
    def build_from_filter(self, filter_matrix: FilterMatrix, sort_column: str = None, reverse: bool = False):
        """
        Baut SortMatrix aus FilterMatrix
        
        Args:
            filter_matrix: Quell-FilterMatrix
            sort_column: Spalte zum Sortieren (ohne __abdatum/__formatiert)
            reverse: Absteigend sortieren
        """
        logger.info("🔨 === BAUE SORTMATRIX aus FilterMatrix ===")
        
        # ALLE Spalten übernehmen
        self.columns = filter_matrix.columns.copy()
        
        # Daten kopieren
        self.data = deepcopy(filter_matrix.data)
        
        # Sortierung anwenden
        if sort_column and sort_column in self.columns:
            logger.info(f"📊 Sortiere nach: {sort_column} (reverse={reverse})")
            
            def sort_key(row):
                value = row.get(sort_column, '')
                # None-Werte ans Ende
                if value is None:
                    return ('', '')  # Leerer String am Ende
                return (0, value)  # Normale Werte zuerst
            
            self.data.sort(key=sort_key, reverse=reverse)
            logger.info(f"✅ Sortierung abgeschlossen")
        else:
            logger.info(f"✅ Keine Sortierung: {len(self.data)} Zeilen unverändert")
        
        logger.info(f"✅ SortMatrix erstellt: {len(self.data)} Zeilen, {len(self.columns)} Spalten")
        self.log_sample(row_count=1)


class ProjectionMatrix(MatrixBase):
    """
    ProjectionMatrix: Reduktion auf sichtbare Spalten
    ERST HIER wird auf ausgewählte Spalten reduziert
    """
    
    def __init__(self):
        super().__init__("ProjectionMatrix")
        
    def build_from_sort(self, sort_matrix: SortMatrix, visible_columns: List[str]):
        """
        Baut Projektion aus SortMatrix
        
        Args:
            sort_matrix: Quell-SortMatrix (ALLE Spalten)
            visible_columns: Liste der sichtbaren Spalten (z.B. nur _show Spalten)
        """
        logger.info("🔨 === BAUE PROJEKTION aus SortMatrix ===")
        logger.info(f"📋 Sichtbare Spalten: {len(visible_columns)}")
        
        # NUR sichtbare Spalten
        self.columns = visible_columns.copy()
        
        # Für jede Spalte ALLE 3 Ebenen einbeziehen - ORIGINAL SUFFIX!
        all_projection_keys = []
        for col in visible_columns:
            all_projection_keys.append(col)
            all_projection_keys.append(f"{col}_abdatum")  # ORIGINAL SUFFIX!
            all_projection_keys.append(f"{col}_formatiertes_abdatum")  # ORIGINAL SUFFIX!
        
        # Zeilen projizieren
        self.data = []
        for row in sort_matrix.data:
            projected_row = {}
            for key in all_projection_keys:
                if key in row:
                    projected_row[key] = row[key]
            self.data.append(projected_row)
        
        logger.info(f"✅ Projektion erstellt: {len(self.data)} Zeilen, {len(self.columns)} Basis-Spalten")
        logger.info(f"   (= {len(all_projection_keys)} Keys total inkl. _abdatum/_formatiertes_abdatum)")
        self.log_sample(row_count=1)


class MatrixPipeline:
    """
    Vollständige Matrix-Pipeline Manager
    
    Verwaltet: BasisMatrix → FilterMatrix → SortMatrix → Projektion
    """
    
    def __init__(self, view_guid: str):
        self.view_guid = view_guid
        
        # Pipeline-Stufen (PERSISTENT!)
        self.basis_matrix: Optional[BasisMatrix] = None
        self.filter_matrix: Optional[FilterMatrix] = None
        self.sort_matrix: Optional[SortMatrix] = None
        self.projection_matrix: Optional[ProjectionMatrix] = None
        
        # Pipeline-Parameter
        self.filter_func = None
        self.sort_column = None
        self.sort_reverse = False
        self.visible_columns = []
        
        logger.info(f"🚀 MatrixPipeline initialisiert für View: {view_guid}")
    
    def build_basis_matrix(self, column_control, all_columns: List[str]):
        """SCHRITT 1: BasisMatrix aus Column Control erstellen"""
        self.basis_matrix = BasisMatrix()
        self.basis_matrix.build_from_column_control(column_control, all_columns)
        return self.basis_matrix
    
    def apply_filter(self, filter_func=None):
        """SCHRITT 2: Filter auf BasisMatrix anwenden → FilterMatrix"""
        if not self.basis_matrix:
            logger.error("❌ Keine BasisMatrix vorhanden!")
            return None
        
        self.filter_func = filter_func
        self.filter_matrix = FilterMatrix()
        self.filter_matrix.build_from_basis(self.basis_matrix, filter_func)
        return self.filter_matrix
    
    def apply_sort(self, sort_column: str = None, reverse: bool = False):
        """SCHRITT 3: Sortierung auf FilterMatrix anwenden → SortMatrix"""
        if not self.filter_matrix:
            logger.error("❌ Keine FilterMatrix vorhanden!")
            return None
        
        self.sort_column = sort_column
        self.sort_reverse = reverse
        self.sort_matrix = SortMatrix()
        self.sort_matrix.build_from_filter(self.filter_matrix, sort_column, reverse)
        return self.sort_matrix
    
    def project(self, visible_columns: List[str]):
        """SCHRITT 4: Projektion auf sichtbare Spalten"""
        if not self.sort_matrix:
            logger.error("❌ Keine SortMatrix vorhanden!")
            return None
        
        self.visible_columns = visible_columns
        self.projection_matrix = ProjectionMatrix()
        self.projection_matrix.build_from_sort(self.sort_matrix, visible_columns)
        return self.projection_matrix
    
    def rebuild_from_basis(self):
        """
        Pipeline ab BasisMatrix neu durchlaufen
        Nutzt gespeicherte Parameter (filter_func, sort_column, visible_columns)
        
        USAGE: Nach Stichtag-Wechsel - BasisMatrix ist bereits neu befüllt
        """
        logger.info("🔄 === REBUILD PIPELINE ab BasisMatrix ===")
        
        if not self.basis_matrix:
            logger.error("❌ Keine BasisMatrix vorhanden!")
            return False
        
        # FilterMatrix neu
        self.apply_filter(self.filter_func)
        
        # SortMatrix neu
        self.apply_sort(self.sort_column, self.sort_reverse)
        
        # Projektion neu
        self.project(self.visible_columns)
        
        logger.info("✅ Pipeline komplett neu durchlaufen")
        return True
    
    def reproject_only(self, new_visible_columns: List[str]):
        """
        NUR Projektion neu (bei Spalten-Änderung)
        SortMatrix bleibt unverändert
        
        USAGE: Spalten hinzufügen/entfernen, Reihenfolge ändern
        """
        logger.info("🔄 === REPROJECT: Nur Projektion neu ===")
        
        if not self.sort_matrix:
            logger.error("❌ Keine SortMatrix vorhanden!")
            return False
        
        self.project(new_visible_columns)
        logger.info("✅ Projektion aktualisiert")
        return True
    
    def get_projection_data(self) -> List[Dict[str, Any]]:
        """Holt Daten der Projektion für View"""
        if self.projection_matrix:
            return self.projection_matrix.data
        return []
    
    def get_projection_columns(self) -> List[str]:
        """Holt Spalten der Projektion"""
        if self.projection_matrix:
            return self.projection_matrix.columns
        return []
    
    def log_pipeline_status(self):
        """Loggt Status aller Pipeline-Stufen"""
        logger.info("📊 === PIPELINE STATUS ===")
        
        if self.basis_matrix:
            logger.info(f"  ✅ BasisMatrix: {self.basis_matrix.get_row_count()} Zeilen")
        else:
            logger.info(f"  ❌ BasisMatrix: Nicht vorhanden")
        
        if self.filter_matrix:
            logger.info(f"  ✅ FilterMatrix: {self.filter_matrix.get_row_count()} Zeilen")
        else:
            logger.info(f"  ❌ FilterMatrix: Nicht vorhanden")
        
        if self.sort_matrix:
            logger.info(f"  ✅ SortMatrix: {self.sort_matrix.get_row_count()} Zeilen")
        else:
            logger.info(f"  ❌ SortMatrix: Nicht vorhanden")
        
        if self.projection_matrix:
            logger.info(f"  ✅ Projektion: {self.projection_matrix.get_row_count()} Zeilen, {len(self.projection_matrix.columns)} Spalten")
        else:
            logger.info(f"  ❌ Projektion: Nicht vorhanden")


# === GLOBAL REGISTRY für Pipeline-Instanzen ===
_pipeline_registry: Dict[str, MatrixPipeline] = {}


def get_matrix_pipeline(view_guid: str) -> MatrixPipeline:
    """
    Holt oder erstellt Pipeline für View
    
    Args:
        view_guid: View GUID
        
    Returns:
        MatrixPipeline Instanz (PERSISTENT)
    """
    if view_guid not in _pipeline_registry:
        _pipeline_registry[view_guid] = MatrixPipeline(view_guid)
        logger.info(f"✨ Neue MatrixPipeline erstellt für: {view_guid}")
    
    return _pipeline_registry[view_guid]


def clear_pipeline(view_guid: str):
    """Entfernt Pipeline aus Registry"""
    if view_guid in _pipeline_registry:
        del _pipeline_registry[view_guid]
        logger.info(f"🗑️ Pipeline entfernt: {view_guid}")
