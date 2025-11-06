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
    [3] SORT: sort aus app_db lesen (Single/Multi/Gruppierung)
             SortMatrix aus FilterMatrix aufbauen
             Nutzt Matrix Manager für Sortierung
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
        
        # Die 5 Matrizen (Pipeline-Stufen)
        self.matrix_base = []      # BASIS: Vom matrix_manager übernehmen
        self.matrix_filter = []    # FILTER: Gefilterte Daten
        self.matrix_sort = []      # SORT: Sortierte Daten (mit Gruppen-Headern)
        self.matrix_sum = []       # SUMMEN: Sort + Summen-Zeile am Ende
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
        'SUMMEN': (3, '_apply_sums'),
        'PROJECT': (4, '_apply_projection'),
    }
    
    def run(self, status: str):
        """
        Pipeline ab Status ausführen bis PROJECT
        
        Args:
            status: Start-Status ('BASIS', 'FILTER', 'SORT', 'SUMMEN', 'PROJECT')
        
        AUFRUFE:
            pipeline.run('BASIS')   → Kompletter Start (BASIS→FILTER→SORT→SUMMEN→PROJECT)
            pipeline.run('FILTER')  → Ab Filter (FILTER→SORT→SUMMEN→PROJECT)
            pipeline.run('SORT')    → Ab Sort (SORT→SUMMEN→PROJECT)
            pipeline.run('SUMMEN')  → Ab Summen (SUMMEN→PROJECT)
            pipeline.run('PROJECT') → Nur Projektion (PROJECT)
        
        VERWENDUNG:
            View-Start: run('BASIS')        ← Lädt BasisMatrix neu
            Schnellsuche: run('FILTER')     ← BasisMatrix bleibt, Filter neu
            Sort-Dialog: run('SORT')        ← Filter bleibt, Sort neu
            Summen-Reset: run('SUMMEN')     ← Sort bleibt, Summen neu
            Spalten-Dialog: run('PROJECT')  ← Summen bleiben, Projektion neu
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
            ('SUMMEN', self._apply_sums),  # ← NEU: Summen-Zeile einfügen
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
        logger.info(f"📊 BASIS({len(self.matrix_base)}) → FILTER({len(self.matrix_filter)}) → SORT({len(self.matrix_sort)}) → SUMMEN({len(self.matrix_sum)}) → PROJECT({len(self.matrix_project)})")
    
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
            from pdvm_search_string_parser import get_search_string_parser
            
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
        
        ANALOG ZU FILTER-SYSTEM:
        - sg_string: Sort-Konfiguration (dict oder list)
        - sg_source: 'einfach' (Header-Klick) | 'multi' (Dialog) | None (keine Sortierung)
        
        DATENQUELLEN:
        - Input: self.matrix_filter (FilterMatrix)
        - Parameter: app_db.get_value(view_guid, 'sg_string') - Aktive Sortierung
        - Parameter: app_db.get_value(view_guid, 'sg_source') - Sortier-Quelle
        - Output: self.matrix_sort (SortMatrix)
        
        SORT-CONFIG Formate:
        - Einfach: {'column': 'familienname_show', 'direction': 'asc'}
        - Multi: {'columns': [{'column_key': 'anrede_show', 'direction': 'asc', 'is_group': False}, ...]}
        """
        logger.info("🔄 === SORT: SortMatrix aus FilterMatrix aufbauen ===")
        
        # ANALOG ZU FILTER: sg_string und sg_source aus app_db lesen
        sg_string, _ = self.gcs._app_db.get_value(self.view_guid, 'sg_string')
        sg_source, _ = self.gcs._app_db.get_value(self.view_guid, 'sg_source')
        
        if not sg_string or not sg_source:
            # Keine Sortierung → FilterMatrix übernehmen
            self.matrix_sort = self.matrix_filter.copy()
            logger.info(f"✅ KEIN SORT: {len(self.matrix_sort)} Zeilen übernommen (Original-Reihenfolge)")
            return
        
        logger.info(f"📊 SORT AKTIV: source={sg_source}")
        
        # Sortierung anwenden via Matrix Manager
        if self.matrix_manager:
            logger.info(f"📊 Sort-Config gefunden (source={sg_source}) - wende Sortierung an...")
            
            # Matrix Manager braucht FilterMatrix
            self.matrix_manager.filter_matrix = self.matrix_filter
            
            # Typ der Sortierung basierend auf sg_source
            if sg_source == 'einfach':
                # EINFACH: Header-Klick → Single-Sort
                # sg_string: {'column': 'familienname_show', 'direction': 'asc'}
                logger.info(f"  📋 Typ: SINGLE-SORT (Header-Klick, Spalte: {sg_string.get('column')})")
                
                # In Matrix Manager Format konvertieren
                sort_config = {
                    'type': 'single_sort',
                    'column': sg_string.get('column'),
                    'direction': sg_string.get('direction', 'asc'),
                    'use_original': sg_string.get('use_original', False)
                }
                self.matrix_manager.apply_sort_config(sort_config)
                
            elif sg_source == 'multi':
                # MULTI: Dialog → Advanced-Sort oder Gruppierung
                # sg_string kann sein:
                # - [{'column_key': 'x', 'direction': 'asc', 'is_group': False}, ...] → Liste (Advanced-Dialog)
                # - {'columns': [...]} → Dict mit 'columns' Key
                # - {'type': 'grouping', 'group_columns': [...]} → Gruppierung
                
                if isinstance(sg_string, list):
                    # LISTE: Advanced-Sort-Dialog Format
                    # → Muss in Matrix Manager Format konvertiert werden
                    logger.info(f"  📋 Typ: ADVANCED-SORT (Liste, {len(sg_string)} Spalten)")
                    
                    # Prüfe ob Gruppierung (is_group=True) enthalten ist
                    has_groups = any(item.get('is_group', False) for item in sg_string)
                    
                    if has_groups:
                        # GRUPPIERUNG: Spalten mit is_group=True trennen
                        group_columns = [
                            {
                                'column': item.get('column_key', item.get('column')),
                                'direction': item.get('direction', 'asc')
                            }
                            for item in sg_string if item.get('is_group', False)
                        ]
                        sort_columns = [
                            {
                                'column': item.get('column_key', item.get('column')),
                                'direction': item.get('direction', 'asc')
                            }
                            for item in sg_string if not item.get('is_group', False)
                        ]
                        
                        logger.info(f"  📂 Erkannt: GRUPPIERUNG ({len(group_columns)} Gruppen, {len(sort_columns)} Sort-Spalten)")
                        self.matrix_manager.apply_grouping(
                            group_columns=group_columns,
                            sort_columns=sort_columns
                        )
                    else:
                        # MULTI-SORT ohne Gruppierung
                        # Liste → Dict mit 'columns' Key konvertieren
                        converted_config = {
                            'columns': [
                                {
                                    'column': item.get('column_key', item.get('column')),
                                    'direction': item.get('direction', 'asc'),
                                    'use_original': item.get('use_original', False)
                                }
                                for item in sg_string
                            ]
                        }
                        logger.info(f"  📋 Multi-Sort ohne Gruppierung: {len(sg_string)} Spalten")
                        self.matrix_manager.apply_sort_config(converted_config)
                
                elif isinstance(sg_string, dict):
                    if sg_string.get('type') == 'grouping':
                        # GRUPPIERUNG (altes Format)
                        logger.info(f"  📂 Typ: GRUPPIERUNG (Dict, {len(sg_string.get('group_columns', []))} Gruppen-Spalten)")
                        self.matrix_manager.apply_grouping(
                            group_columns=sg_string['group_columns'],
                            sort_columns=sg_string.get('sort_columns', [])
                        )
                    elif 'columns' in sg_string:
                        # MULTI-SORT mit 'columns' Key
                        logger.info(f"  📋 Typ: MULTI-SORT (Dict, {len(sg_string['columns'])} Spalten)")
                        self.matrix_manager.apply_sort_config(sg_string)
                    else:
                        logger.warning(f"⚠️ Unbekanntes sg_string Format (dict ohne 'columns' oder 'type'): {sg_string}")
                        self.matrix_sort = self.matrix_filter.copy()
                        return
                else:
                    logger.warning(f"⚠️ sg_string ist weder List noch Dict: {type(sg_string)}")
                    self.matrix_sort = self.matrix_filter.copy()
                    return
            else:
                logger.warning(f"⚠️ Unbekannte sg_source: {sg_source}")
                self.matrix_sort = self.matrix_filter.copy()
                return
            
            # Sortierte Matrix aus Matrix Manager holen
            self.matrix_sort = self.matrix_manager.sort_matrix
            logger.info(f"✅ SORT ANGEWENDET: {len(self.matrix_sort)} Zeilen sortiert")
        else:
            # Fallback: Keine Sortierung möglich
            logger.warning("⚠️ Matrix Manager nicht verfügbar - keine Sortierung möglich")
            self.matrix_sort = self.matrix_filter.copy()
            logger.info(f"⚠️ {len(self.matrix_sort)} Zeilen unsortiert übernommen")
    
    def _apply_sums(self):
        """
        SUMMEN: Summen-Zeile an SortMatrix anfügen
        
        Input: self.matrix_sort (mit oder ohne Gruppen-Header)
        Parameter: sum_columns aus app_db
        Output: self.matrix_sum (matrix_sort + Summen-Zeile am Ende)
        
        BEISPIEL:
        - sum_columns = ['geburtsdatum_jahr_show', 'alter_show']
        - Iteriert durch matrix_sort, überspringt Gruppen-Header
        - Summiert numerische Werte
        - Fügt Summen-Zeile mit row_type='sum_row' am Ende an
        """
        logger.info("🧮 === SUMMEN: Gesamtsummen berechnen ===")
        
        # 🆕 sum_string + sum_source aus app_db holen (analog zu s_string/sg_string)
        sum_string, _ = self.gcs._app_db.get_value(self.view_guid, 'sum_string')
        sum_source, _ = self.gcs._app_db.get_value(self.view_guid, 'sum_source')
        
        if not sum_source or not sum_string:
            # Keine Summen konfiguriert → matrix_sort 1:1 übernehmen
            self.matrix_sum = self.matrix_sort.copy()
            logger.info("ℹ️ Keine Summen konfiguriert (sum_source=None) - matrix_sort übernommen")
            return
        
        if not isinstance(sum_string, list) or len(sum_string) == 0:
            # sum_string leer → matrix_sort 1:1 übernehmen
            self.matrix_sum = self.matrix_sort.copy()
            logger.info("ℹ️ sum_string leer - matrix_sort übernommen")
            return
        
        sum_columns = sum_string  # Alias für Kompatibilität
        
        logger.info(f"📋 Summen-Konfiguration:")
        logger.info(f"  sum_source: '{sum_source}'")
        logger.info(f"  sum_string: {len(sum_columns)} Spalten")
        logger.info(f"  Σ {', '.join(sum_columns)}")
        
        # 🔍 DEBUG: Prüfe ob Gruppen-Header group_sums haben
        group_header_count = 0
        for row in self.matrix_sort:
            row_type = row.get('row_type', {})
            if isinstance(row_type, dict) and row_type.get('type') == 'group_header':
                group_header_count += 1
                group_sums = row_type.get('group_sums', {})
                if group_sums:
                    logger.info(f"  ✅ Gruppen-Header '{row_type.get('value')}' hat group_sums: {group_sums}")
                else:
                    logger.warning(f"  ⚠️ Gruppen-Header '{row_type.get('value')}' OHNE group_sums!")
        
        if group_header_count > 0:
            logger.info(f"  📊 {group_header_count} Gruppen-Header in matrix_sort gefunden")
        
        # Summen berechnen
        sums = {}
        has_floats = {}  # 🆕 Track ob Float-Werte dabei waren
        data_row_count = 0
        
        # Initialisiere Float-Tracking
        for col in sum_columns:
            has_floats[col] = False
        
        for row in self.matrix_sort:
            # Gruppen-Header überspringen
            row_type = row.get('row_type', {})
            if isinstance(row_type, dict) and row_type.get('type') == 'group_header':
                logger.debug(f"  ⏭️ Überspringe Gruppen-Header: {row_type.get('value')}")
                continue
            
            data_row_count += 1
            
            # Durch alle Summen-Spalten iterieren
            for col in sum_columns:
                cell = row.get(col)
                
                # WICHTIG: 3-Ebenen-Struktur → Wert ist Liste [original, abdatum, formatiert]
                if isinstance(cell, list) and len(cell) > 0:
                    value = cell[0]  # EBENE 1: Original-Wert
                else:
                    value = cell
                
                # 🔧 String-zu-Zahl Konvertierung (falls value String ist)
                if isinstance(value, str):
                    try:
                        # Prüfe ob String Dezimaltrennzeichen enthält
                        if '.' in value or ',' in value:
                            value = float(value.replace(',', '.'))
                            has_floats[col] = True
                            logger.debug(f"    {col}: '{cell[0]}' (String mit Dezimal) → {value} (Float)")
                        else:
                            # Ganzzahl-String → versuche int, fallback float
                            try:
                                value = int(value)
                                logger.debug(f"    {col}: '{cell[0]}' (String) → {value} (Int)")
                            except ValueError:
                                value = float(value)
                                has_floats[col] = True
                                logger.debug(f"    {col}: '{cell[0]}' (String) → {value} (Float)")
                    except (ValueError, TypeError):
                        # Nicht konvertierbar → überspringen
                        logger.debug(f"    {col}: '{value}' nicht konvertierbar, überspringe")
                        continue
                
                # Float-Detection: Original war bereits Float
                elif isinstance(value, float):
                    # Prüfe ob Float tatsächlich Nachkommastellen hat
                    if value % 1 != 0:  # Hat Nachkommastellen
                        has_floats[col] = True
                
                # Nur numerische Werte aufsummieren
                if isinstance(value, (int, float)):
                    sums[col] = sums.get(col, 0) + value
                    logger.debug(f"    {col}: {value} (Summe bisher: {sums[col]})")
        
        logger.info(f"✅ {data_row_count} Daten-Zeilen summiert")
        
        # 🔢 Konvertiere Summen zu Integer, falls keine Floats dabei waren
        final_sums = {}
        for col in sum_columns:
            sum_value = sums.get(col, 0)
            
            # Prüfe ob Float-Werte dabei waren
            if not has_floats.get(col, False) and isinstance(sum_value, float):
                # Keine Floats dabei + Summe hat keine Nachkommastellen → Integer
                if sum_value % 1 == 0:
                    final_sums[col] = int(sum_value)
                    logger.info(f"  {col}: {sum_value} (Float) → {int(sum_value)} (Int)")
                else:
                    final_sums[col] = sum_value
                    logger.info(f"  {col}: {sum_value} (Float mit Nachkommastellen)")
            else:
                final_sums[col] = sum_value
                logger.info(f"  {col}: {sum_value}")
        
        # Summen-Zeile erstellen
        sum_row = {
            'uid_original': 'SUM_ROW',  # Eindeutiger Marker
            'row_type': {
                'type': 'sum_row',
                'label': 'Summe',
                'columns': sum_columns,
                'row_count': data_row_count
            }
        }
        
        # Summen eintragen (3-Ebenen-Struktur!)
        for col in sum_columns:
            sum_value = final_sums.get(col, 0)
            # EBENE 1: Summe, EBENE 2+3: None (keine AB-Daten für Summen-Zeile)
            sum_row[col] = [sum_value, None, None]
        
        # Alle anderen Spalten mit leerem Wert befüllen (für Konsistenz)
        if len(self.matrix_sort) > 0:
            first_row = self.matrix_sort[0]
            for key in first_row.keys():
                if key not in sum_row and key not in ['uid_original', 'row_type']:
                    sum_row[key] = [None, None, None]  # 3-Ebenen-Struktur
        
        # matrix_sum = matrix_sort + Summen-Zeile
        self.matrix_sum = self.matrix_sort.copy()
        self.matrix_sum.append(sum_row)
        
        logger.info(f"✅ SUMMEN: {len(self.matrix_sort)} → {len(self.matrix_sum)} Zeilen (Summen-Zeile eingefügt)")
    
    def _apply_projection(self):
        """
        PROJECT: View aus SumMatrix projizieren
        
        DATENQUELLEN:
        - Input: self.matrix_sum (SumMatrix - Sort + Summen-Zeile)
        - Parameter: GCS (expert_mode → projection_table Index 0 oder 5)
        - Output: self.matrix_project (View-Matrix)
        
        WICHTIG:
        - row_type bleibt in versteckter Spalte erhalten
        - Projektionstabelle wird aus GCS basierend auf expert_mode geholt
        - Summen-Zeile wird durchgelassen (row_type='sum_row')
        """
        logger.info("📊 === PROJECT: View aus SumMatrix projizieren ===")
        
        # ✅ Projektionstabelle DIREKT aus GCS basierend auf expert_mode
        expert_mode = self.gcs.expert_mode if self.gcs else False
        projection_index = 5 if expert_mode else 0
        
        projection_table = self.gcs.get_projection_table(self.view_guid, projection_index)
        
        if projection_table and isinstance(projection_table, list):
            logger.info(f"📊 GCS-Projektion[{projection_index}]: {len(projection_table)} Spalten (Expert={expert_mode})")
            self.visible_columns = projection_table
        else:
            # Fallback: Alle _show Spalten
            self.visible_columns = [col for col in sorted(self.all_columns) if '_show' in col]
            logger.info(f"📊 FALLBACK: {len(self.visible_columns)} _show Spalten")
        
        # Projektion aufbauen: Nur definierte Spalten + row_type
        self.matrix_project = []
        for row in self.matrix_sum:  # ✅ GEÄNDERT: Von matrix_sum statt matrix_sort lesen
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
