"""
🔄 PDVM PIPELINE - ZENTRALE LINEARE MATRIX-VERARBEITUNG
========================================================

BENUTZER-ANFORDERUNG (15.10.2025):
"Alle Module in der Pipeline gekapselt, holen sich benötigte Werte aus Matrix und GCS.
Für jeden Ablauf nur EINEN Aufruf, eine Datenquelle, zentral persistent in GCS."

PIPELINE-ARCHITEKTUR (LINEAR):

    START (View-Initialisierung)
      ↓
    [1] BASIS: BasisMatrix aus matrix_manager.basis_matrix laden
              Wird NUR beim Start oder Stichtag-Refresh aktualisiert
      ↓
    [2] FILTER: s_string + s_source aus app_db lesen
               FilterMatrix aus BasisMatrix aufbauen
               Schnellsuche-Feld wird hier gesteuert (initialisiert)
      ↓
    [3] SORT: Sort-Parameter aus app_db lesen
             SortMatrix aus FilterMatrix aufbauen
      ↓
    [4] PROJECT: Projektionstabelle aus GCS lesen
                View aus SortMatrix projizieren
                row_type in versteckter Spalte verfügbar
      ↓
    UI-UPDATE (außerhalb Pipeline)

AUFRUFE:
    pipeline.run('BASIS')   → Kompletter Neustart (BASIS→FILTER→SORT→PROJECT)
    pipeline.run('FILTER')  → Ab Filter neu (FILTER→SORT→PROJECT)
    pipeline.run('SORT')    → Ab Sort neu (SORT→PROJECT)
    pipeline.run('PROJECT') → Nur Projektion neu (PROJECT)

DATENFLUSS:
    BasisMatrix   ← matrix_manager (nur bei START/Stichtag)
    FilterMatrix  ← BasisMatrix + app_db(s_string, s_source)
    SortMatrix    ← FilterMatrix + app_db(sort_config)
    ProjectMatrix ← SortMatrix + GCS(projection_table)

WICHTIG:
- Pipeline ist VOLLSTÄNDIG AUTONOM
- Alle Daten aus Matrix + GCS/app_db
- Manager setzen nur Parameter in app_db → pipeline.run()
- KEINE externe Logik, KEINE Verschachtelungen
"""

import logging
from typing import Dict, List, Any, Optional
from pdvm_central_systemsteuerung import get_gcs

logger = logging.getLogger(__name__)


class PdvmPipeline:
    """
    Lineare Pipeline für Matrix-Verarbeitung
    
    Pipeline-Schritte werden in FESTER REIHENFOLGE ausgeführt
    Alle Schritte in steps[] Matrix für einfache sequenzielle Ausführung
    """
    
    def __init__(self, view_guid: str, matrix_manager):
        """
        Args:
            view_guid: Eindeutige View-GUID
            matrix_manager: Matrix Manager mit basis_matrix (bereits befüllt)
        """
        self.view_guid = view_guid
        self.matrix_manager = matrix_manager
        self.gcs = get_gcs()
        
        # Die 4 Matrizen (direkt aus matrix_manager)
        self.matrix_base = []      # BASIS: Vom matrix_manager übernehmen
        self.matrix_filter = []    # FILTER: Gefilterte Daten
        self.matrix_sort = []      # SORT: Sortierte Daten
        self.matrix_project = []   # PROJECT: Projizierte Daten (nur sichtbare Spalten)
        
        # Metadaten
        self.all_columns = set()   # Alle Spalten
        self.visible_columns = []  # Nur sichtbare Spalten
        
        # Steuerungsinformationen für UI
        self.current_search_text = None  # Aktueller Suchtext für Schnellsuche-Feld
        
        logger.info(f"🔄 Pipeline erstellt für View: {view_guid[:20]}...")
    
    # Pipeline-Definition: Status → (Index, Methode)
    PIPELINE_STEPS = {
        'BASIS': (0, '_build_basis_matrix'),
        'FILTER': (1, '_apply_filter'),
        'SORT': (2, '_apply_sort'),
        'PROJECT': (3, '_apply_projection'),
    }
    
    def run(self, status: str):
        """
        Pipeline ab Status ausführen bis PROJECT
        
        Args:
            status: Start-Status ('BASIS', 'FILTER', 'SORT', 'PROJECT')
        
        AUFRUFE:
            pipeline.run('BASIS')   → Kompletter Start (BASIS→FILTER→SORT→PROJECT)
            pipeline.run('FILTER')  → Ab Filter (FILTER→SORT→PROJECT)
            pipeline.run('SORT')    → Ab Sort (SORT→PROJECT)
            pipeline.run('PROJECT') → Nur Projektion (PROJECT)
        
        VERWENDUNG:
            View-Start: run('BASIS')        ← Lädt BasisMatrix neu
            Schnellsuche: run('FILTER')     ← BasisMatrix bleibt, Filter neu
            Sort-Dialog: run('SORT')        ← Filter bleibt, Sort neu
            Spalten-Dialog: run('PROJECT')  ← Sort bleibt, Projektion neu
        """
        # Status-Index und Methode ermitteln
        if status not in self.PIPELINE_STEPS:
            logger.error(f"❌ Ungültiger Status: {status}")
            raise ValueError(f"Ungültiger Pipeline-Status: {status}")
        
        start_index, _ = self.PIPELINE_STEPS[status]
        logger.info(f"🔄 === PIPELINE START ab '{status}' (Index {start_index}) ===")
        
        # Alle Schritte als Liste (für sequenzielle Ausführung)
        steps = [
            ('BASIS', self._build_basis_matrix),
            ('FILTER', self._apply_filter),
            ('SORT', self._apply_sort),
            ('PROJECT', self._apply_projection),
        ]
        
        # Sequenzielle Ausführung ab start_index
        for i in range(start_index, len(steps)):
            step_name, step_method = steps[i]
            logger.info(f"🔄 Schritt {i+1}/{len(steps)}: {step_name}")
            
            try:
                step_method()
                logger.info(f"✅ {step_name} abgeschlossen")
            except Exception as e:
                logger.error(f"❌ Fehler in {step_name}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                raise
        
        logger.info(f"🎯 === PIPELINE FERTIG ===")
        logger.info(f"📊 BASIS({len(self.matrix_base)}) → FILTER({len(self.matrix_filter)}) → SORT({len(self.matrix_sort)}) → PROJECT({len(self.matrix_project)})")
    
    # ============================================================
    # PIPELINE-SCHRITTE (Jeder ist UNABHÄNGIG und EINFACH)
    # ============================================================
    
    def _build_basis_matrix(self):
        """
        BASIS: BasisMatrix aus matrix_manager übernehmen
        
        WICHTIG: Matrix Manager hat IMMER die aktuelle BasisMatrix!
        """
        logger.info("📊 BASIS: BasisMatrix übernehmen")
        
        # IMMER aktuelle BasisMatrix aus matrix_manager holen
        if hasattr(self.matrix_manager, 'basis_matrix') and self.matrix_manager.basis_matrix:
            self.matrix_base = self.matrix_manager.basis_matrix.copy()
            # Spalten aus erster Zeile extrahieren
            if self.matrix_base:
                self.all_columns = set(self.matrix_base[0].keys())
            else:
                self.all_columns = set()
            logger.info(f"📊 {len(self.matrix_base)} Zeilen, {len(self.all_columns)} Spalten")
        else:
            logger.error("❌ matrix_manager.basis_matrix ist leer!")
            self.matrix_base = []
            self.all_columns = set()
    
    def _apply_filter(self):
        """
        FILTER: FilterMatrix aus BasisMatrix aufbauen
        
        DATENQUELLEN:
        - Input: self.matrix_base (BasisMatrix)
        - Parameter: app_db (s_string, s_source)
        - Output: self.matrix_filter (FilterMatrix)
        
        STEUERUNG SCHNELLSUCHE-FELD:
        - s_string aus app_db lesen
        - Wenn vorhanden → Feld initialisieren mit Wert
        - Wenn leer/None → Feld leeren
        """
        logger.info("🔍 === FILTER: FilterMatrix aus BasisMatrix aufbauen ===")
        
        # Parameter aus app_db lesen
        s_string, _ = self.gcs._app_db.get_value(self.view_guid, 's_string')
        s_source, _ = self.gcs._app_db.get_value(self.view_guid, 's_source')
        
        logger.info(f"📋 Parameter: s_string='{s_string}', s_source='{s_source}'")
        
        # Schnellsuche-Feld steuern
        if s_string and s_string.strip():
            logger.info(f"🔍 Schnellsuche aktiv: '{s_string}'")
            self.current_search_text = s_string  # Für UI-Update speichern
        else:
            logger.info("📋 Schnellsuche inaktiv: Feld wird geleert")
            self.current_search_text = None  # Feld soll geleert werden
            s_string = None  # Sicherstellen dass None
        
        # FilterMatrix aufbauen
        if s_string is None:
            # Kein Filter → komplette BasisMatrix übernehmen
            self.matrix_filter = self.matrix_base.copy()
            logger.info(f"✅ KEIN FILTER: {len(self.matrix_filter)} Zeilen übernommen")
        else:
            # Filter anwenden: Verwende SearchStringParser für strukturierte Auswertung
            from search_string_parser import get_search_string_parser
            
            parser = get_search_string_parser()
            filter_func = parser.parse(s_string, s_source)
            
            if filter_func is None:
                # Parser konnte String nicht parsen → keine Filterung
                logger.warning(f"⚠️ Parser konnte s_string nicht parsen: '{s_string}'")
                self.matrix_filter = self.matrix_base.copy()
            else:
                # DEBUG: Zeige verfügbare Felder in erster Zeile
                if self.matrix_base:
                    first_row_keys = list(self.matrix_base[0].keys())
                    logger.info(f"🔍 DEBUG: Verfügbare Felder in Matrix: {first_row_keys[:10]}...")
                
                # Filter-Funktion auf alle Zeilen anwenden
                self.matrix_filter = []
                filtered_count = 0
                for row in self.matrix_base:
                    if filter_func(row):
                        self.matrix_filter.append(row)
                        filtered_count += 1
                
                logger.info(f"✅ FILTER AKTIV: '{s_string}' (source={s_source}) → {len(self.matrix_filter)} von {len(self.matrix_base)} Zeilen")
                
                # DEBUG: Zeige warum Zeilen gefiltert wurden
                if filtered_count == 0:
                    logger.warning(f"⚠️ KEIN ERGEBNIS - Filter hat keine Zeilen gefunden!")
                    if self.matrix_base:
                        logger.info(f"🔍 DEBUG: Erste Zeile Werte: familienname_show={self.matrix_base[0].get('familienname_show', 'N/A')}, vorname_show={self.matrix_base[0].get('vorname_show', 'N/A')}")
    
    def _apply_sort(self):
        """
        SORT: SortMatrix aus FilterMatrix aufbauen
        
        DATENQUELLEN:
        - Input: self.matrix_filter (FilterMatrix)
        - Parameter: app_db (sort_column, sort_reverse)
        - Output: self.matrix_sort (SortMatrix)
        
        TODO: Sort-Parameter aus app_db lesen und anwenden
        """
        logger.info("🔄 === SORT: SortMatrix aus FilterMatrix aufbauen ===")
        
        # Parameter aus app_db lesen
        sort_column, _ = self.gcs._app_db.get_value(self.view_guid, 'sort_column')
        sort_reverse, _ = self.gcs._app_db.get_value(self.view_guid, 'sort_reverse')
        
        if sort_column:
            logger.info(f"� Sort-Parameter: column='{sort_column}', reverse={sort_reverse}")
            # TODO: Sortierung implementieren
            self.matrix_sort = self.matrix_filter.copy()
            logger.info(f"⚠️ SORT TODO - {len(self.matrix_sort)} Zeilen (unsortiert)")
        else:
            # Keine Sortierung → FilterMatrix übernehmen
            self.matrix_sort = self.matrix_filter.copy()
            logger.info(f"✅ KEIN SORT: {len(self.matrix_sort)} Zeilen übernommen")
    
    def _apply_projection(self):
        """
        PROJECT: View aus SortMatrix projizieren
        
        DATENQUELLEN:
        - Input: self.matrix_sort (SortMatrix)
        - Parameter: GCS (projection_table)
        - Output: self.matrix_project (View-Matrix)
        
        WICHTIG:
        - row_type bleibt in versteckter Spalte erhalten
        - Projektionstabelle definiert sichtbare Spalten
        """
        logger.info("📊 === PROJECT: View aus SortMatrix projizieren ===")
        
        # Projektionstabelle aus GCS holen
        projection_table, _ = self.gcs._app_db.get_value(self.view_guid, 'projection_table')
        
        if projection_table and isinstance(projection_table, list):
            logger.info(f"📊 Projektionstabelle: {len(projection_table)} Spalten")
            self.visible_columns = projection_table
        else:
            # Fallback: Alle _show Spalten
            self.visible_columns = [col for col in sorted(self.all_columns) if '_show' in col]
            logger.info(f"📊 FALLBACK: {len(self.visible_columns)} _show Spalten")
        
        # Projektion aufbauen: Nur definierte Spalten + row_type
        self.matrix_project = []
        for row in self.matrix_sort:
            projected_row = {}
            
            # Sichtbare Spalten
            for col in self.visible_columns:
                projected_row[col] = row.get(col, '')
            
            # row_type IMMER mitnehmen (versteckt)
            if 'row_type' in row:
                projected_row['row_type'] = row['row_type']
            
            self.matrix_project.append(projected_row)
        
        logger.info(f"✅ PROJECT: {len(self.matrix_project)} Zeilen, {len(self.visible_columns)} Spalten projiziert")
    
    # ============================================================
    # GETTER für UI
    # ============================================================
    
    def get_projected_data(self) -> tuple[List[Dict], List[str]]:
        """
        Gibt projizierte Daten für UI zurück
        
        Returns:
            (matrix_project, visible_columns)
        """
        return self.matrix_project, self.visible_columns
    
    def get_search_text(self) -> Optional[str]:
        """
        Gibt aktuellen Suchtext für Schnellsuche-Feld zurück
        
        Returns:
            Suchtext oder None (Feld soll geleert werden)
        """
        return self.current_search_text


# ============================================================
# FACTORY FUNCTION
# ============================================================

_pipelines: Dict[str, PdvmPipeline] = {}


def get_pipeline(view_guid: str, matrix_manager) -> PdvmPipeline:
    """
    Factory-Funktion für Pipeline (Singleton pro View)
    
    Args:
        view_guid: Eindeutige View-GUID
        matrix_manager: Matrix Manager mit BasisMatrix
        
    Returns:
        PdvmPipeline-Instanz
    """
    if view_guid not in _pipelines:
        _pipelines[view_guid] = PdvmPipeline(view_guid, matrix_manager)
        logger.info(f"✅ Pipeline erstellt für View: {view_guid[:20]}...")
    
    return _pipelines[view_guid]
