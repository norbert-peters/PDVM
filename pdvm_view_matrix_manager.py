# pdvm_view_matrix_manager.py
"""
PDVM View Matrix Manager - Matrix-Pipeline-Architektur
========================================================

LINEARE PIPELINE:
1. BasisMatrix    - Vollständige Daten aus PdvmCentralDatenbank Instanzen
2. FilterMatrix   - Nach Filter-Anwendung (aktuell: Kopie von BasisMatrix)
3. SortMatrix     - Nach Sortierung/Gruppierung (aktuell: Kopie von FilterMatrix)
4. Projektion     - Anwendung der Projektions-Tabelle (nur sichtbare Spalten)
5. UI Update      - TableWidget wird aus projizierter SortMatrix befüllt

TRACE-SPALTEN für Pipeline-Verfolgung:
- familienname_original
- vorname_show
- geburtsdatum_original
- geburtsdatum_show
- anrede_show

IMPLEMENTIERUNG: Pure Python (keine pandas dependency)
Matrix = Liste von Dictionaries: [{'guid': ..., 'spalte1': ..., 'spalte2': ...}, ...]
"""

import logging
from typing import List, Dict, Any, Optional
from copy import deepcopy

# V3 Filter-System: Einheitlicher Parser
from search_string_parser import get_search_string_parser

# 3-Ebenen Array-Struktur
from pdvm_matrix_constants import (
    WERT, ABDATUM, FORMATIERT,
    create_cell, get_wert, get_abdatum, get_formatiert,
    ensure_array_format, is_empty_cell
)

logger = logging.getLogger(__name__)


class PdvmViewMatrixManager:
    """
    Matrix-Pipeline Manager für PDVM Views
    
    Verwaltet die lineare Datenfluss-Pipeline:
    BasisMatrix → FilterMatrix → SortMatrix → Projektion → UI
    """
    
    # Trace-Spalten für Pipeline-Debugging
    TRACE_COLUMNS = [
        'familienname_original',
        'vorname_show', 
        'geburtsdatum_original',
        'geburtsdatum_show',
        'anrede_show'
    ]
    
    def __init__(self, view_guid: str, gcs, controller=None):
        """
        Initialisiere Matrix Manager
        
        Args:
            view_guid: View-GUID
            gcs: Globale Systemsteuerung für Stichtag
            controller: PdvmViewController für Projektions-Zugriff (view-spezifisch!)
        """
        self.view_guid = view_guid
        self.gcs = gcs
        self.controller = controller  # Für Projektions-Abruf
        
        # Die 3 Matrizen der Pipeline (Liste von Dicts)
        self.basis_matrix: Optional[List[Dict[str, Any]]] = None
        self.filter_matrix: Optional[List[Dict[str, Any]]] = None
        self.sort_matrix: Optional[List[Dict[str, Any]]] = None
        
        # Aktuelle Projektions-Tabelle
        self.current_projection_table: Optional[List[str]] = None
        self.current_projection_name: Optional[str] = None  # Für Wiederverwendung nach Sort
        self.current_expert_mode: bool = False  # Für Wiederverwendung nach Sort
        
        # Pipeline-Status
        self.pipeline_initialized = False
        
        logger.info(f"🎯 PdvmViewMatrixManager initialisiert für View: {view_guid}")
    
    def initialize_basis_matrix(self, instances: List[Any], all_controls: Dict[str, Any]):
        """
        SCHRITT 1: BasisMatrix aus PdvmCentralDatenbank Instanzen erstellen
        MIGRIERT von pdvm_view_dialog - BEWÄHRTE ORIGINAL-LOGIK
        
        Args:
            instances: Liste von PdvmCentralDatenbank Instanzen
            all_controls: Alle Control-Konfigurationen (controls_config)
        """
        logger.info("🏗️ === SCHRITT 1: BasisMatrix erstellen (ORIGINAL-LOGIK) ===")
        
        if not instances:
            logger.warning("⚠️ Keine Instanzen für BasisMatrix!")
            self.basis_matrix = []
            return
        
        rows = []
        
        for instance in instances:
            row_data = {}
            
            # === STUFE 1: ORIGINAL-FELDER befüllen - ORIGINAL-LOGIK ===
            logger.info(f"📊 Befülle Original-Felder für Instanz: {instance.guid}")
            
            # SPEZIALFALL: uid_original - GUID des Datensatzes
            if 'uid_original' in all_controls:
                row_data['uid_original'] = instance.guid
                row_data['uid_original_abdatum'] = None
                row_data['uid_original_formatiertes_abdatum'] = None
                logger.info(f"  🔑 uid_original: {instance.guid}")
            else:
                logger.warning("  ⚠️ uid_original nicht in controls_config gefunden")
                row_data['uid_original'] = instance.guid
                row_data['uid_original_abdatum'] = None
                row_data['uid_original_formatiertes_abdatum'] = None
            
            # Sortiere Controls: Basis-Felder vor Zusatzfeldern (date_alter, date_jahr etc.)
            def sort_key(control_key):
                control_config = all_controls.get(control_key, {})
                control_type = control_config.get('type', '')
                if control_type in ['date_alter', 'date_jahr', 'date_monat', 'date_tag']:
                    return 1  # Zusatzfelder später
                else:
                    return 0  # Basis-Felder zuerst
            
            # Original-Controls sammeln (ohne uid_original, da bereits behandelt)
            original_controls = [(k, v) for k, v in all_controls.items() 
                               if v.get('control_type') == 'original' and k != 'uid_original']
            sorted_controls = sorted(original_controls, key=lambda x: sort_key(x[0]))
            
            for control_key, control_config in sorted_controls:
                # SPEZIALFALL: Date-Zusatzfelder werden berechnet
                control_type = control_config.get('type', '')
                if control_type in ['date_alter', 'date_jahr', 'date_monat', 'date_tag']:
                    # Basis-Datumsfeld finden (z.B. geburtsdatum_alter_original → geburtsdatum)
                    base_field = control_key.replace('_original', '').replace('_alter', '').replace('_jahr', '').replace('_monat', '').replace('_tag', '')
                    base_original = f"{base_field}_original"
                    
                    # ✅ ARRAY: Basis-Zelle holen
                    base_cell = row_data.get(base_original, create_cell(None, None, None))
                    base_wert = get_wert(base_cell)
                    
                    calculated_value = ""  # Default
                    
                    if base_wert is not None:
                        try:
                            # Numerischen Wert extrahieren
                            if isinstance(base_wert, (int, float)):
                                numeric_value = float(base_wert)
                            elif isinstance(base_wert, str) and base_wert.replace('.', '').isdigit():
                                numeric_value = float(base_wert)
                            else:
                                numeric_value = None
                            
                            if numeric_value is not None and numeric_value != 1001.0:
                                # Verwende temp_dt_inst für Berechnung
                                dt = self.gcs.temp_dt_inst
                                if dt:
                                    dt.PdvmDateTime = numeric_value
                                    
                                    if control_type == 'date_alter':
                                        # Alter berechnen mit Stichtag
                                        calculated_value = str(dt.calc_alter(self.gcs.stichtag))
                                        logger.debug(f"  📅 Alter berechnet: {numeric_value} → {calculated_value} Jahre")
                                    elif control_type == 'date_jahr':
                                        calculated_value = str(dt.Year)
                                    elif control_type == 'date_monat':
                                        calculated_value = str(dt.Month)
                                    elif control_type == 'date_tag':
                                        calculated_value = str(dt.Day)
                        except Exception as e:
                            calculated_value = ""
                            logger.warning(f"  ⚠️ Fehler bei {control_type} Berechnung: {e}")
                    
                    # ✅ ARRAY: Date-Zusatzfelder haben kein eigenes Abdatum
                    row_data[control_key] = create_cell(calculated_value, None, None)
                    continue
                
                # NORMALFALL: Wert aus Datenbank holen
                feld = control_config.get('feld')
                gruppe = control_config.get('gruppe', 'SYSTEM')
                
                if feld:
                    try:
                        # WERT und ABDATUM aus Datenbank
                        result = instance.get_value(gruppe, feld, self.gcs.st_inst.PdvmDateTime)
                        
                        # Wert und Abdatum extrahieren
                        if isinstance(result, tuple) and len(result) >= 2:
                            wert, abdatum = result[0], result[1]
                        else:
                            wert, abdatum = result, None
                        
                        # EBENE 3: Formatiertes Abdatum erstellen
                        formatiertes_abdatum = self._format_abdatum(abdatum) if abdatum else None
                        
                        # ✅ ARRAY: Alle 3 Ebenen in einem Array speichern
                        row_data[control_key] = create_cell(wert, abdatum, formatiertes_abdatum)
                    
                    except Exception as e:
                        logger.debug(f"❌ Fehler bei {control_key}: {e}")
                        row_data[control_key] = create_cell(None, None, None)
                else:
                    row_data[control_key] = create_cell(None, None, None)
            
            # === STUFE 2: SHOW-FELDER aus ORIGINAL-FELDERN bestücken - ORIGINAL-LOGIK ===
            logger.info("📋 Befülle Show-Felder aus Original-Feldern")
            
            for control_key, control_config in all_controls.items():
                if control_config.get('control_type') == 'show':
                    # Original-Feld finden
                    original_key = control_key.replace('_show', '_original')
                    
                    # SPEZIALFALL: uid_show - ersten 8 Stellen + "..."
                    if control_key == 'uid_show':
                        # ✅ ARRAY: Original-Zelle holen
                        original_cell = row_data.get('uid_original', create_cell(None, None, None))
                        original_guid = get_wert(original_cell)
                        
                        if original_guid and isinstance(original_guid, str) and len(original_guid) >= 8:
                            show_value = f"{original_guid[:8]}..."
                        else:
                            show_value = ""
                        
                        # ✅ ARRAY: uid_show hat kein Abdatum
                        row_data[control_key] = create_cell(show_value, None, None)
                        continue
                    
                    # SPEZIALFALL: Date-Zusatzfelder - Werte aus Original kopieren
                    control_type = control_config.get('type', '')
                    if control_type in ['date_alter', 'date_jahr', 'date_monat', 'date_tag']:
                        # ✅ ARRAY: Calculated Field hat kein Abdatum
                        original_calculated_cell = row_data.get(original_key)
                        if original_calculated_cell is not None:
                            # Falls Original ein Array ist, nur Wert kopieren
                            if isinstance(original_calculated_cell, list):
                                row_data[control_key] = create_cell(original_calculated_cell[WERT], None, None)
                            else:
                                # Legacy: Direkter Wert
                                row_data[control_key] = create_cell(original_calculated_cell, None, None)
                        else:
                            row_data[control_key] = create_cell("", None, None)
                        continue
                    
                    # SPEZIALFALL: Einfache Date-Felder - in lesbares Datum umwandeln
                    if control_type == 'date':
                        # ✅ ARRAY: Original-Zelle holen
                        original_cell = row_data.get(original_key, create_cell(None, None, None))
                        original_wert = get_wert(original_cell)
                        
                        if original_wert is not None and original_wert != 1001.0:
                            try:
                                dt = self.gcs.temp_dt_inst
                                if dt:
                                    dt.PdvmDateTime = float(original_wert)
                                    show_value = dt.Date
                                else:
                                    show_value = str(original_wert)
                            except Exception as e:
                                show_value = str(original_wert)
                                logger.warning(f"  ⚠️ Fehler bei Date-Konvertierung: {e}")
                        else:
                            show_value = ""
                        
                        # ✅ ARRAY: Show-Zelle mit konvertiertem Wert + Original-Abdatum erstellen
                        row_data[control_key] = create_cell(
                            show_value,
                            get_abdatum(original_cell),
                            get_formatiert(original_cell)
                        )
                        continue
                    
                    # NORMALFALL: Wert aus Original kopieren
                    # ✅ ARRAY: Original-Zelle holen
                    original_cell = row_data.get(original_key, create_cell(None, None, None))
                    original_wert = get_wert(original_cell)
                    
                    if original_wert is None:
                        show_value = ""
                    else:
                        # SPEZIALFALL: Dropdown-Felder übersetzen
                        if control_type == 'dropdown':
                            dropdown_config = control_config.get('dropdown', {})
                            dropdown_guid = dropdown_config.get('key', '')
                            dropdown_gruppe = dropdown_config.get('value', '')
                            
                            if dropdown_guid:
                                try:
                                    translated_value = self.gcs.translate_dropdown_value(dropdown_guid, str(original_wert), dropdown_gruppe)
                                    show_value = translated_value
                                except Exception as e:
                                    show_value = str(original_wert)
                                    logger.warning(f"  ⚠️ Dropdown-Übersetzung fehlgeschlagen: {e}")
                            else:
                                show_value = str(original_wert)
                        else:
                            # Normaler Wert kopieren
                            show_value = original_wert
                    
                    # ✅ ARRAY: Show-Zelle mit Show-Wert + Original-Abdatum erstellen
                    row_data[control_key] = create_cell(
                        show_value,
                        get_abdatum(original_cell),
                        get_formatiert(original_cell)
                    )
            
            # DUMMY-CONTROL
            if 'dummy' in all_controls:
                row_data['dummy'] = create_cell('', None, None)
            
            # FILTER: Zeile nur hinzufügen wenn nicht alle Original-Felder leer sind
            if not self._all_original_fields_empty(row_data, all_controls):
                row_data['display'] = True  # Für Filter-System
                rows.append(row_data)
            else:
                logger.debug(f"⚠️ Zeile gefiltert (alle Original-Felder leer): {instance.guid}")
        
        # Speichere als Liste von Dicts
        self.basis_matrix = rows
        
        logger.info(f"✅ BasisMatrix erstellt: {len(self.basis_matrix)} Zeilen (aus {len(instances)} Instanzen)")
        logger.info("🎯 ORIGINAL-LOGIK vollständig migriert!")
        self._trace_matrix("BasisMatrix (NACH Erstellung)", self.basis_matrix)
    
    def _format_abdatum(self, abdatum_value):
        """
        Formatiert einen Abdatum-Wert in lesbares Format
        (ORIGINAL-LOGIK aus pdvm_view_dialog)
        """
        if abdatum_value is None:
            return None
        
        # SPEZIALFALL: Default-Wert 1001.0 (01.01.0001)
        if float(abdatum_value) == 1001.0:
            return "01.01.0001 (Default)"
        
        try:
            # GCS temporäre DateTime-Instanz verwenden
            dt = self.gcs.temp_dt_inst
            if dt is None:
                return f"{abdatum_value} (nicht formatiert)"
            
            dt.PdvmDateTime = float(abdatum_value)
            formatted = dt.FormTimeStamp
            
            return formatted
        except Exception as e:
            logger.debug(f"Fehler bei Abdatum-Formatierung {abdatum_value}: {e}")
            return f"{abdatum_value} (Fehler)"
    
    def apply_filter(self, search_string: str = None, filter_source: str = None):
        """
        SCHRITT 2: FilterMatrix aus BasisMatrix erstellen
        V3 FILTER-SYSTEM RAW-OPTIMIERUNG: Parser nutzt filter_source für Interpretation
        
        Args:
            search_string: RAW User-Eingabe (z.B. "lau") ODER formatierter String
            filter_source: 'schnell' | 'einfach' | 'komplex' | None (für Auto-Detection)
        """
        logger.info(f"🔍 === SCHRITT 2: FilterMatrix erstellen (V3 RAW) - source={filter_source} ===")
        logger.info(f"🔍 search_string = {repr(search_string)}")
        
        if self.basis_matrix is None or not self.basis_matrix:
            logger.error("❌ BasisMatrix nicht vorhanden!")
            self.filter_matrix = []
            return
        
        self._trace_matrix("BasisMatrix (VOR Filter)", self.basis_matrix)
        
        # V3 RAW-OPTIMIERUNG: Parser mit filter_source
        if search_string is None or search_string.strip() == "":
            # Kein Filter = alle Zeilen übernehmen
            self.filter_matrix = deepcopy(self.basis_matrix)
            logger.info(f"📋 🎯 FILTER GELÖSCHT (search_string=None) - alle {len(self.filter_matrix)} Zeilen übernommen")
            logger.info(f"✅ ===== FILTER KOMPLETT ENTFERNT =====")
        else:
            # Parser holen und mit filter_source parsen
            parser = get_search_string_parser()
            filter_func = parser.parse(search_string, filter_source=filter_source)
            
            if not filter_func:
                logger.error(f"❌ Parser konnte search_string nicht verarbeiten: '{search_string}'")
                self.filter_matrix = deepcopy(self.basis_matrix)
            else:
                # Filter-Funktion auf BasisMatrix anwenden
                self.filter_matrix = [
                    row for row in self.basis_matrix
                    if filter_func(row)
                ]
                logger.info(f"✅ Filter angewendet: {len(self.filter_matrix)} von {len(self.basis_matrix)} Zeilen")
        
        # Spaltenanzahl aus erster Zeile ermitteln
        column_count = len(self.filter_matrix[0].keys()) if self.filter_matrix else 0
        logger.info(f"✅ FilterMatrix erstellt: {len(self.filter_matrix)} Zeilen x {column_count} Spalten")
        self._trace_matrix("FilterMatrix (NACH Filter)", self.filter_matrix)
    
    def apply_sort(self, sort_config: Optional[Dict[str, Any]] = None):
        """
        SCHRITT 3: SortMatrix aus FilterMatrix erstellen
        
        Args:
            sort_config: Sort-Konfiguration (aktuell noch nicht implementiert)
        """
        logger.info("🔄 === SCHRITT 3: SortMatrix erstellen ===")
        
        if self.filter_matrix is None:
            logger.error("❌ FilterMatrix nicht vorhanden!")
            return
        
        self._trace_matrix("FilterMatrix (VOR Sortierung)", self.filter_matrix)
        
        if sort_config:
            logger.info(f"  🔧 Sortierung anwenden: {sort_config}")
            # TODO: Sort-Logik implementieren
            # Aktuell: Kopiere FilterMatrix
            self.sort_matrix = deepcopy(self.filter_matrix)
        else:
            logger.info("  ℹ️ Keine Sortierung aktiv - kopiere FilterMatrix")
            self.sort_matrix = deepcopy(self.filter_matrix)
        
        # Spaltenanzahl aus erster Zeile ermitteln
        column_count = len(self.sort_matrix[0].keys()) if self.sort_matrix else 0
        logger.info(f"✅ SortMatrix erstellt: {len(self.sort_matrix)} Zeilen x {column_count} Spalten")
        self._trace_matrix("SortMatrix (NACH Sortierung)", self.sort_matrix)
    
    def apply_projection(self, projection_table_name: str, expert_mode: bool = False) -> List[Dict[str, Any]]:
        """
        SCHRITT 4: Projektion auf SortMatrix anwenden
        
        Args:
            projection_table_name: Name der Projektions-Tabelle (z.B. 'table_standard', 'table_expert')
            expert_mode: Expert Mode aktiv?
        
        Returns:
            Projizierte Matrix mit nur sichtbaren Spalten (Liste von Dicts)
        """
        logger.info("🎨 === SCHRITT 4: Projektion anwenden ===")
        
        if self.sort_matrix is None or not self.sort_matrix:
            logger.error("❌ SortMatrix nicht vorhanden!")
            return []
        
        self._trace_matrix("SortMatrix (VOR Projektion)", self.sort_matrix)
        
        # Hole Projektions-Tabelle vom CONTROLLER (view-spezifisch, nicht persistent!)
        try:
            logger.info(f"  🔍 Hole Projektion vom Controller: {projection_table_name}")
            
            if self.controller and hasattr(self.controller, 'get_projection_table'):
                projection_columns = self.controller.get_projection_table(projection_table_name)
                logger.info(f"  ✅ Projektion vom Controller erhalten: {len(projection_columns)} Spalten")
            else:
                logger.warning(f"⚠️ Kein Controller verfügbar - Fallback auf alle Spalten")
                # Fallback: Alle Spalten (Pure Python - aus erstem Dict)
                projection_columns = list(self.sort_matrix[0].keys()) if self.sort_matrix else []
            
            if not projection_columns:
                logger.warning(f"⚠️ Leere Projektions-Tabelle '{projection_table_name}' - verwende alle Spalten")
                projection_columns = list(self.sort_matrix[0].keys()) if self.sort_matrix else []
            
            logger.info(f"  📋 Projektions-Tabelle: {projection_table_name}")
            logger.info(f"  📊 {len(projection_columns)} Spalten in Projektion")
            logger.info(f"  📋 Spalten: {projection_columns[:5]}{'...' if len(projection_columns) > 5 else ''}")
            
            # Filter nur existierende Spalten (prüfe gegen erste Zeile)
            available_columns = ['guid']  # GUID immer dabei
            if self.sort_matrix:
                first_row_keys = set(self.sort_matrix[0].keys())
                for col in projection_columns:
                    if col in first_row_keys and col != 'guid':
                        available_columns.append(col)
            
            # === PROJEKTION MIT 3-EBENEN ARRAY-STRUKTUR ===
            # ✅ ARRAY: Jede Spalte ist bereits ein Array mit 3 Ebenen - einfach kopieren!
            # 🆕 row_type und uid_original IMMER mitkopieren (auch wenn nicht in Projektion sichtbar)
            projected_matrix = []
            for row in self.sort_matrix:
                projected_row = {}
                
                # IMMER: UID und row_type kopieren (für View-Logik)
                projected_row['uid_original'] = row.get('uid_original')
                projected_row['row_type'] = row.get('row_type')
                
                # Dann sichtbare Spalten projizieren
                for col in available_columns:
                    if col not in ['uid_original', 'row_type']:  # Nicht doppelt kopieren
                        # ✅ ARRAY: Spalte enthält bereits [wert, abdatum, formatiert]
                        projected_row[col] = row.get(col)
                
                projected_matrix.append(projected_row)
            
            logger.info(f"✅ Projektion angewendet: {len(projected_matrix)} Zeilen x {len(available_columns)} Spalten")
            self._trace_matrix("Projizierte Matrix (NACH Projektion)", projected_matrix)
            
            # Speichere für Wiederverwendung nach Sort
            self.current_projection_table = available_columns
            self.current_projection_name = projection_table_name
            self.current_expert_mode = expert_mode
            
            return projected_matrix
            
        except Exception as e:
            logger.error(f"❌ Projektion fehlgeschlagen: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return deepcopy(self.sort_matrix) if self.sort_matrix else []
    
    def reapply_current_projection(self):
        """
        EINFACHE METHODE: Wendet letzte Projektion erneut an
        
        Verwendet für: Nach Sortierung die gleiche Projektion wiederherstellen
        """
        if self.current_projection_name:
            logger.debug(f"🔄 Wende letzte Projektion erneut an: {self.current_projection_name}")
            self.apply_projection(self.current_projection_name, self.current_expert_mode)
        else:
            logger.warning("⚠️ Keine vorherige Projektion vorhanden - überspringe")
    
    def get_projected_data_for_ui(self, expert_mode: bool = False) -> tuple[List[Dict[str, Any]], List[str]]:
        """
        Hole projizierte Daten für UI-Update
        
        Args:
            expert_mode: Expert Mode aktiv?
        
        Returns:
            (Matrix mit projizierten Daten, Liste der Spalten-Keys)
        """
        # Bestimme Projektions-Tabelle
        projection_name = 'table_expert' if expert_mode else 'table_standard'
        
        # Wende Projektion an
        projected_matrix = self.apply_projection(projection_name, expert_mode)
        
        # Spalten-Keys aus current_projection_table (korrekte Reihenfolge!)
        # Diese wurde in apply_projection() gesetzt
        column_keys = [col for col in self.current_projection_table if col != 'guid']
        
        logger.info(f"  🎯 UI-Spalten ({len(column_keys)}): {column_keys[:5]}{'...' if len(column_keys) > 5 else ''}")
        
        return projected_matrix, column_keys
    
    def rebuild_pipeline(self, search_string: Optional[str] = None):
        """
        Pipeline komplett neu durchlaufen - AUTONOM!
        
        🆕 EINFACHE AUTONOME PIPELINE:
        - Lädt s_string DIREKT aus GCS (wenn nicht übergeben)
        - Sort-Config wird IMMER aus GCS geholt (autonom wie Filter!)
        - Keine Konvertierung, keine Komplexität!
        
        Args:
            search_string: Optionaler s_string (für manuelle Filter, überschreibt GCS)
        """
        logger.info("🔄 === PIPELINE REBUILD (AUTONOM) ===")
        
        if self.basis_matrix is None:
            logger.error("❌ BasisMatrix nicht vorhanden - kann Pipeline nicht rebuilden!")
            return
        
        # SCHRITT 2: RAW-OPTIMIERUNG - s_string + s_source aus GCS holen
        filter_source = None
        if search_string is None:
            search_string, filter_source = self._load_search_string_from_gcs()
        
        self.apply_filter(search_string, filter_source=filter_source)
        
        # SCHRITT 3: Sort AUTONOM aus GCS holen und anwenden
        sort_config = self._load_sort_config_from_gcs()
        self.apply_sort(sort_config)
        
        # SCHRITT 4: Projektion erfolgt on-demand in get_projected_data_for_ui()
        
        logger.info("✅ Pipeline rebuild abgeschlossen")
    
    def _load_search_string_from_gcs(self) -> tuple[Optional[str], Optional[str]]:
        """
        RAW-OPTIMIERUNG: Lädt s_string UND s_source aus GCS
        
        Returns:
            (s_string, s_source) - beide für RAW-Interpretation nötig
        """
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs:
                logger.warning("GCS nicht verfügbar - kein Filter")
                return None, None
            
            # RAW-OPTIMIERUNG: Lade BEIDE
            s_string, _ = gcs._app_db.get_value(self.view_guid, 's_string')
            s_source, _ = gcs._app_db.get_value(self.view_guid, 's_source')
            
            if s_string:
                logger.info(f"  RAW s_string aus GCS: '{s_string}' (source={s_source})")
                return s_string, s_source
            else:
                logger.info(f"  Kein s_string in GCS - kein Filter")
                return None, None
                
        except Exception as e:
            logger.error(f"Fehler beim Laden s_string aus GCS: {e}")
            return None, None
    
    def _load_sort_config_from_gcs(self) -> Optional[list]:
        """
        Lädt Sort-Config AUTONOM aus GCS (App-DB)
        
        🆕 AUTONOME SORTIERUNG:
        - Wird bei JEDEM Pipeline-Rebuild aufgerufen
        - Holt Config direkt aus GCS ohne Controller
        - Funktioniert wie autonomes Filter-System
        
        Returns:
            Sort-Config als Liste oder None
        """
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs:
                logger.warning("⚠️ GCS nicht verfügbar - keine Sort-Config")
                return None
            
            # Hole Sort-Config aus App-DB
            sort_config, _ = gcs._app_db.get_value(self.view_guid, 'sort')
            
            if sort_config and isinstance(sort_config, list) and len(sort_config) > 0:
                logger.info(f"  📊 Sort-Config aus GCS geladen: {len(sort_config)} Spalten")
                for idx, cfg in enumerate(sort_config):
                    group_marker = " [GRUPPE]" if cfg.get('is_group') else ""
                    logger.info(f"    {idx+1}. {cfg.get('column_key')} → {cfg.get('direction')}{group_marker}")
                return sort_config
            else:
                logger.info(f"  📋 Keine Sort-Config in GCS - keine Sortierung")
                return None
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Sort-Config aus GCS: {e}")
            return None
    
    def _trace_matrix(self, label: str, matrix: List[Dict[str, Any]], max_rows: int = 4):
        """
        Trace-Ausgabe für Pipeline-Debugging mit 3-EBENEN-STRUKTUR
        
        Zeigt bis zu max_rows Zeilen mit TRACE_COLUMNS inkl. ALLE 3 Ebenen
        
        Args:
            label: Beschreibung der Matrix
            matrix: Matrix zum Tracen (Liste von Dicts)
            max_rows: Maximale Anzahl Zeilen (default: 4)
        """
        if not matrix:
            logger.info(f"  📊 {label}: LEER")
            return
        
        logger.info(f"  📊 {label}: {len(matrix)} Zeilen")
        
        # Filtere nur existierende Trace-Spalten (prüfe gegen erste Zeile)
        first_row_keys = set(matrix[0].keys())
        available_trace_cols = [col for col in self.TRACE_COLUMNS if col in first_row_keys]
        
        if not available_trace_cols:
            logger.info(f"    ⚠️ Keine Trace-Spalten verfügbar")
            return
        
        # Zeige erste max_rows Zeilen mit ALLEN 3 Ebenen
        rows_to_show = matrix[:max_rows]
        
        for idx, row in enumerate(rows_to_show):
            # ✅ ARRAY: GUID korrekt holen (uid_original ist Array, wir brauchen WERT)
            uid_cell = row.get('uid_original', row.get('guid', 'UNKNOWN'))
            guid = get_wert(uid_cell) if isinstance(uid_cell, list) else uid_cell
            logger.info(f"    Zeile {idx}: GUID={str(guid)[:8]}...")
            
            # ✅ ARRAY: Zeige EINE Beispiel-Spalte mit ALLEN 3 Ebenen
            example_col = 'familienname_original'
            if example_col in first_row_keys:
                cell = row.get(example_col)
                if isinstance(cell, list) and len(cell) >= 3:
                    logger.info(f"      📋 {example_col}:")
                    logger.info(f"        EBENE 1 (Wert): {cell[WERT]}")
                    logger.info(f"        EBENE 2 (abdatum): {cell[ABDATUM]}")
                    logger.info(f"        EBENE 3 (formatiert): {cell[FORMATIERT]}")
                else:
                    logger.info(f"      📋 {example_col}: {cell} (Legacy-Format)")
            
            # ✅ ARRAY: Zeige andere Trace-Spalten (nur EBENE 1 für Übersicht)
            row_str = "      📊 Andere Felder: "
            for col in available_trace_cols:
                if col != example_col:
                    cell = row.get(col)
                    wert = get_wert(cell) if isinstance(cell, list) else cell
                    row_str += f"{col}={wert} "
            logger.info(row_str)
    
    def _all_original_fields_empty(self, row_data: Dict[str, Any], all_controls: Dict[str, Any]) -> bool:
        """
        Prüft ob alle Original-Felder einer Zeile leer/None sind
        MIGRIERT von pdvm_view_dialog - ORIGINAL-LOGIK
        
        Args:
            row_data: Die zu prüfende Zeile
            all_controls: controls_config für Feld-Typen
        
        Returns:
            True wenn alle Original-Felder leer, sonst False
        """
        # Sammle alle Original-Felder (control_type == 'original')
        original_fields = [key for key, config in all_controls.items()
                          if config.get('control_type') == 'original']
        
        if not original_fields:
            # Keine Original-Felder gefunden - Zeile behalten
            return False
        
        # Prüfe ob alle Original-Felder leer sind (nur Ebene 1: Wert)
        for field_key in original_fields:
            # SPEZIALFÄLLE: Diese Felder haben immer einen Wert und zählen nicht als "leer"
            if field_key == 'uid_original':
                continue  # uid_original hat immer die GUID
            
            # Date-Zusatzfelder haben immer einen berechneten Wert
            control_config = all_controls.get(field_key, {})
            control_type = control_config.get('type', '')
            if control_type in ['date_alter', 'date_jahr', 'date_monat', 'date_tag']:
                continue  # Diese werden immer berechnet
            
            # ✅ ARRAY: Aus Zelle nur Wert (EBENE 1) prüfen
            cell = row_data.get(field_key)
            value = get_wert(cell) if isinstance(cell, list) else cell
            
            # Feld ist nicht leer wenn es einen Wert hat (nicht None, nicht leerer String, nicht 0 bei Zahlen)
            if value is not None and value != '' and value != 0:
                return False
        
        # Alle relevanten Original-Felder sind leer
        return True
    
    # ============================================================================
    # V3 FILTER-LOGIK: Alte Methoden ENTFERNT - SearchStringParser übernimmt
    # ============================================================================
    # ENTFERNT (7 Methoden):
    # - _apply_unified_search_filter()
    # - _apply_multi_field_filter()
    # - _apply_complex_filter_with_groups()
    # - _check_group()
    # - _check_single_condition()
    # - _apply_single_field_filter()
    # - _apply_global_search_filter()
    # → Alle durch SearchStringParser ersetzt!
    # ============================================================================
    
    
    def apply_search_filter(self, search_text: str, visible_columns: list) -> bool:
        """
        EINFACHE ÖFFENTLICHE METHODE: Wendet Schnellsuche auf BasisMatrix an
        
        Args:
            search_text: Suchtext (aus Suchzeile/Dialog)
            visible_columns: Sichtbare Spalten für Suche
        
        Returns:
            True wenn erfolgreich
        """
        try:
            logger.info(f"🔍 Matrix Manager: Wende Schnellsuche an: '{search_text}'")
            
            if not search_text or not search_text.strip():
                # Leere Suche = alle Zeilen übernehmen
                self.filter_matrix = deepcopy(self.basis_matrix)
                logger.info(f"📋 Leere Suche - alle {len(self.filter_matrix)} Zeilen übernommen")
                
                # Sort + Projection durchlaufen (nutzt persistierte Sort-Config)
                self._apply_persisted_sort()
                return True
            
            # Filter auf sichtbare Spalten anwenden
            search_lower = search_text.lower()
            filtered_rows = []
            
            for row in self.basis_matrix:
                found = False
                for col_key in visible_columns:
                    if col_key in row:
                        # Wert holen (Array oder direkt)
                        cell = row.get(col_key)
                        if isinstance(cell, list) and len(cell) > 0:
                            wert = cell[WERT]
                        else:
                            wert = cell
                        
                        # String-Vergleich
                        value_str = str(wert).lower() if wert is not None else ''
                        if search_lower in value_str:
                            found = True
                            break
                
                if found:
                    filtered_rows.append(row)
            
            self.filter_matrix = filtered_rows
            logger.info(f"✅ Filter angewendet: {len(self.basis_matrix)} → {len(self.filter_matrix)} Zeilen")
            
            # Sort + Projection durchlaufen (nutzt persistierte Sort-Config)
            self._apply_persisted_sort()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Schnellsuche: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def apply_custom_filter(self, filter_func, visible_columns: list = None) -> bool:
        """
        UNIVERSELLE FILTER-METHODE: Wendet beliebige Filter-Funktion auf BasisMatrix an
        
        Args:
            filter_func: Funktion (row_dict) -> bool
            visible_columns: Optionale Liste sichtbarer Spalten (für Projektion)
        
        Returns:
            True wenn erfolgreich
        """
        try:
            logger.info(f"🔍 Matrix Manager: Wende Custom Filter an")
            
            if filter_func is None:
                # Kein Filter = alle Zeilen übernehmen
                self.filter_matrix = deepcopy(self.basis_matrix)
                logger.info(f"📋 Kein Filter - alle {len(self.filter_matrix)} Zeilen übernommen")
            else:
                # Filter-Funktion anwenden
                filtered_rows = []
                for row in self.basis_matrix:
                    try:
                        if filter_func(row):
                            filtered_rows.append(row)
                    except Exception as e:
                        logger.debug(f"Filter-Fehler für Zeile: {e}")
                        continue
                
                self.filter_matrix = filtered_rows
                logger.info(f"✅ Filter angewendet: {len(self.basis_matrix)} → {len(self.filter_matrix)} Zeilen")
            
            # Sort + Projection durchlaufen (nutzt persistierte Sort-Config)
            self._apply_persisted_sort()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Custom Filter: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _apply_persisted_sort(self):
        """
        HELPER: Wendet persistierte Sort-Config an (oder keine Sortierung)
        """
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if gcs:
                sort_config, _ = gcs._app_db.get_value(self.view_guid, 'sort')
                if sort_config:
                    logger.debug(f"📂 Nutze persistierte Sort-Config: {sort_config}")
                    self.apply_sort_config(sort_config)
                else:
                    logger.debug(f"📋 Keine persistierte Sort-Config - keine Sortierung")
                    self.apply_sort_config(None)
            else:
                # Fallback: Keine Sortierung
                self.apply_sort_config(None)
                
        except Exception as e:
            logger.debug(f"Fehler beim Laden persistierter Sort-Config: {e}")
            # Fallback: Keine Sortierung
            self.apply_sort_config(None)
    
    def apply_sort_config(self, sort_config: dict = None) -> bool:
        """
        ZENTRALE SORT-METHODE: FilterMatrix → SortMatrix
        
        Unterstützt Single-Sort UND Multi-Sort!
        Beachtet SortByOriginal aus Controls!
        
        Args:
            sort_config: SINGLE-SORT:
                {
                    'column': 'familienname_show',
                    'direction': 'asc' oder 'desc',
                    'use_original': True
                }
                MULTI-SORT:
                {
                    'columns': [
                        {'column': 'anrede_show', 'direction': 'asc', 'use_original': True},
                        {'column': 'familienname_show', 'direction': 'asc', 'use_original': False}
                    ]
                }
            None = keine Sortierung (Original-Reihenfolge)
        
        Returns:
            True wenn erfolgreich
        """
        try:
            logger.info(f"📊 Matrix Manager: Wende Sortierung an")
            
            if sort_config is None:
                # Keine Sortierung = Filter-Reihenfolge übernehmen
                self.sort_matrix = deepcopy(self.filter_matrix)
                logger.info(f"📋 Keine Sortierung - Filter-Reihenfolge ({len(self.sort_matrix)} Zeilen)")
            
            elif 'columns' in sort_config:
                # MULTI-SORT: Mehrere Spalten
                self._apply_multi_sort(sort_config['columns'])
            
            else:
                # SINGLE-SORT: Eine Spalte
                column_key = sort_config.get('column')
                direction = sort_config.get('direction', 'asc')
                use_original = sort_config.get('use_original', False)
                
                # Bei use_original: _show durch _original ersetzen
                sort_column = column_key
                if use_original and column_key.endswith('_show'):
                    sort_column = column_key.replace('_show', '_original')
                    logger.info(f"🔄 SortByOriginal: Nutze '{sort_column}' statt '{column_key}'")
                
                # Sortier-Funktion
                def get_sort_key(row):
                    """Holt Sortierwert aus Zeile"""
                    if sort_column not in row:
                        return None
                    
                    cell = row[sort_column]
                    
                    # Array-Wert holen (WERT = Index 0)
                    if isinstance(cell, list) and len(cell) > 0:
                        wert = cell[0]  # WERT
                    else:
                        wert = cell
                    
                    # None-Werte ans Ende
                    if wert is None:
                        return (1, '')  # Tuple für stabile Sortierung
                    
                    # Numerische Werte
                    if isinstance(wert, (int, float)):
                        return (0, wert)
                    
                    # String-Werte (lowercase für case-insensitive)
                    return (0, str(wert).lower())
                
                # Sortieren
                reverse = (direction == 'desc')
                sorted_rows = sorted(self.filter_matrix, key=get_sort_key, reverse=reverse)
                
                self.sort_matrix = sorted_rows
                logger.info(f"✅ Sortiert: '{sort_column}' {direction} → {len(self.sort_matrix)} Zeilen")
            
            # Projektion durchlaufen (EINFACH: nutzt letzte Projektion)
            self.reapply_current_projection()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Sortierung: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: Unsortiert übernehmen
            self.sort_matrix = deepcopy(self.filter_matrix)
            self.reapply_current_projection()
            return False
    
    def _apply_multi_sort(self, columns_config: list):
        """
        MULTI-LEVEL SORT: Sortiert nach mehreren Spalten nacheinander
        
        Args:
            columns_config: [
                {'column': 'anrede_show', 'direction': 'asc', 'use_original': True},
                {'column': 'familienname_show', 'direction': 'asc', 'use_original': False}
            ]
        """
        logger.info(f"🔢 Multi-Sort mit {len(columns_config)} Spalten")
        
        # Multi-Level Sort-Key-Funktion
        def get_multi_sort_key(row):
            """Erstellt Tuple mit Werten für alle Sort-Spalten"""
            keys = []
            
            for col_config in columns_config:
                column_key = col_config.get('column')
                use_original = col_config.get('use_original', False)
                direction = col_config.get('direction', 'asc')
                
                # Bei use_original: _show durch _original ersetzen
                sort_column = column_key
                if use_original and column_key.endswith('_show'):
                    sort_column = column_key.replace('_show', '_original')
                
                if sort_column not in row:
                    # Spalte nicht vorhanden → None-Wert
                    if direction == 'desc':
                        keys.append((0, ''))  # Bei DESC: None an Anfang
                    else:
                        keys.append((1, ''))  # Bei ASC: None ans Ende
                    continue
                
                cell = row[sort_column]
                
                # Array-Wert holen (WERT = Index 0)
                if isinstance(cell, list) and len(cell) > 0:
                    wert = cell[0]
                else:
                    wert = cell
                
                # Wert vorbereiten für Sortierung
                if wert is None:
                    if direction == 'desc':
                        key_value = (0, '')  # Bei DESC: None an Anfang
                    else:
                        key_value = (1, '')  # Bei ASC: None ans Ende
                elif isinstance(wert, (int, float)):
                    # Numerisch: Bei DESC negieren
                    if direction == 'desc':
                        key_value = (0, -wert)
                    else:
                        key_value = (0, wert)
                else:
                    # String: Case-insensitive
                    str_value = str(wert).lower()
                    # Bei DESC: Unicode-Trick für Reihenfolge-Umkehr nicht möglich
                    # → Nutze einfach normale Sortierung, später reverse
                    key_value = (0, str_value)
                
                keys.append(key_value)
            
            return tuple(keys)
        
        # Sortieren mit Multi-Key
        # WICHTIG: Wenn ALLE Spalten ASC sind, einfach sortieren
        # Bei gemischten ASC/DESC: Mehrfach sortieren (von hinten nach vorne)
        all_asc = all(c.get('direction', 'asc') == 'asc' for c in columns_config)
        
        if all_asc:
            # Einfach: Alle ASC
            sorted_rows = sorted(self.filter_matrix, key=get_multi_sort_key)
        else:
            # Komplex: Gemischte Richtungen → iterativ sortieren (stabil!)
            sorted_rows = deepcopy(self.filter_matrix)
            
            # Von HINTEN nach VORNE sortieren (Python's stable sort!)
            for col_config in reversed(columns_config):
                column_key = col_config.get('column')
                use_original = col_config.get('use_original', False)
                direction = col_config.get('direction', 'asc')
                
                sort_column = column_key
                if use_original and column_key.endswith('_show'):
                    sort_column = column_key.replace('_show', '_original')
                
                def get_single_key(row):
                    if sort_column not in row:
                        return (1, '')
                    
                    cell = row[sort_column]
                    wert = cell[0] if isinstance(cell, list) and len(cell) > 0 else cell
                    
                    if wert is None:
                        return (1, '')
                    elif isinstance(wert, (int, float)):
                        return (0, wert)
                    else:
                        return (0, str(wert).lower())
                
                reverse = (direction == 'desc')
                sorted_rows = sorted(sorted_rows, key=get_single_key, reverse=reverse)
        
        self.sort_matrix = sorted_rows
        col_names = [c.get('column') for c in columns_config]
        logger.info(f"✅ Multi-Sort: {', '.join(col_names)} → {len(self.sort_matrix)} Zeilen")
    
    def apply_grouping(self, group_columns: list, sort_columns: list = None) -> bool:
        """
        🆕 PHASE 3: GRUPPIERUNG
        
        Gruppiert die Matrix nach mehreren Spalten und fügt Gruppen-Header ein.
        
        Args:
            group_columns: Gruppierungs-Spalten
                [
                    {'column': 'anrede_original', 'direction': 'asc', 'use_original': False},
                    ...
                ]
            sort_columns: Zusätzliche Sortier-Spalten innerhalb der Gruppen
                [
                    {'column': 'familienname_show', 'direction': 'asc', 'use_original': False},
                    ...
                ]
        
        Returns:
            True wenn erfolgreich
        """
        try:
            logger.info(f"📊 Matrix Manager: Wende Gruppierung an")
            logger.info(f"  📊 Gruppen-Spalten: {len(group_columns)}")
            logger.info(f"  🔄 Sort-Spalten: {len(sort_columns) if sort_columns else 0}")
            
            # 1. SORTIEREN: Zuerst nach ALLEN Spalten (Gruppen + Sort)
            all_columns = group_columns + (sort_columns if sort_columns else [])
            logger.info(f"  🔄 Sortiere nach {len(all_columns)} Spalten...")
            self._apply_multi_sort(all_columns)
            
            # 2. GRUPPEN ERKENNEN UND HEADER EINFÜGEN
            logger.info(f"  📊 Erkenne Gruppen und füge Header ein...")
            grouped_data = self._insert_group_headers(self.sort_matrix, group_columns)
            
            # 3. Gruppierte Matrix speichern
            self.sort_matrix = grouped_data
            logger.info(f"✅ Gruppierung angewendet: {len(grouped_data)} Zeilen (mit Headern)")
            
            # 4. Projektion durchlaufen
            self.reapply_current_projection()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Gruppierung: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Fallback: Normale Sortierung
            self._apply_multi_sort(group_columns + (sort_columns if sort_columns else []))
            self.reapply_current_projection()
            return False
    
    def _insert_group_headers(self, sorted_data: list, group_columns: list) -> list:
        """
        Fügt Gruppen-Header-Zeilen in sortierte Daten ein.
        
        🆕 KORRIGIERTE LOGIK:
        1. Header VOR der Gruppe einfügen (mit count=0)
        2. Daten-Zeilen zählen
        3. Bei Gruppenwechsel: Count der AKTUELLEN Gruppe per UID aktualisieren
        
        Args:
            sorted_data: Sortierte Matrix-Daten
            group_columns: Gruppierungs-Spalten Konfiguration
        
        Returns:
            Liste mit Daten-Zeilen UND Gruppen-Header-Zeilen
        """
        if not sorted_data or not group_columns:
            return sorted_data
        
        result = []
        current_group_values = {}  # {column: value} für aktuelle Gruppe
        current_headers = {}  # {level: header_uid} für aktuelle Header-UIDs
        group_counts = {}  # {header_uid: count} für Zählung
        
        for idx, row in enumerate(sorted_data):
            # Prüfe ob Gruppen-Wechsel stattfindet
            group_changed = False
            changed_level = -1
            
            for level, group_col in enumerate(group_columns):
                column_key = group_col.get('column')
                use_original = group_col.get('use_original', False)
                
                # Spalte bestimmen
                sort_column = column_key
                if use_original and column_key.endswith('_show'):
                    sort_column = column_key.replace('_show', '_original')
                
                # Aktuellen Wert holen
                cell = row.get(sort_column)
                current_value = cell[0] if isinstance(cell, list) and len(cell) > 0 else cell
                
                # Vergleich mit vorheriger Gruppe
                if column_key not in current_group_values or current_group_values[column_key] != current_value:
                    group_changed = True
                    changed_level = level
                    current_group_values[column_key] = current_value
                    break
            
            # Bei Gruppen-Wechsel: NEUE Header einfügen
            if group_changed:
                # Neue Header für geänderte Ebene (und alle tieferen)
                for level in range(changed_level, len(group_columns)):
                    group_col = group_columns[level]
                    column_key = group_col.get('column')
                    use_original = group_col.get('use_original', False)
                    
                    sort_column = column_key
                    if use_original and column_key.endswith('_show'):
                        sort_column = column_key.replace('_show', '_original')
                    
                    cell = row.get(sort_column)
                    value = cell[0] if isinstance(cell, list) and len(cell) > 0 else cell
                    current_group_values[column_key] = value
                    
                    # Header erstellen (mit count=0)
                    header = self._create_group_header(
                        column=column_key,
                        value=value,
                        count=0,
                        level=level
                    )
                    result.append(header)
                    
                    # Header-UID merken
                    header_uid = header.get('uid_original')
                    current_headers[level] = header_uid
                    group_counts[header_uid] = 0
            
            # Daten-Zeile hinzufügen
            result.append(row)
            
            # 🔢 Counts für ALLE aktiven Header erhöhen
            for header_uid in current_headers.values():
                if header_uid in group_counts:
                    group_counts[header_uid] += 1
        
        # 🔧 PASS 2: Counts in Header-Zeilen per UID aktualisieren
        for row in result:
            row_type_dict = row.get('row_type', {})
            if isinstance(row_type_dict, dict) and row_type_dict.get('type') == 'group_header':
                header_uid = row.get('uid_original')
                if header_uid in group_counts:
                    # Count per UID aktualisieren
                    row['row_type']['count'] = group_counts[header_uid]
        
        logger.info(f"  ✅ {len(result)} Zeilen erstellt ({len(sorted_data)} Daten + {len(result) - len(sorted_data)} Header)")
        logger.info(f"  📊 {len(group_counts)} Header-Counts aktualisiert")
        return result
    
    def _create_group_header(self, column: str, value, count: int, level: int) -> dict:
        """
        Erstellt eine Gruppen-Header-Zeile mit generierter UID und row_type Dict.
        
        🆕 NEUE ARCHITEKTUR:
        - Jede Header-Zeile bekommt eindeutige UID (GROUP_...)
        - row_type Dict enthält ALLE Metadaten
        - ALLE Spalten aus BasisMatrix werden mit None befüllt
        
        Args:
            column: Spalten-Key
            value: Gruppenwert
            count: Anzahl Zeilen in Gruppe
            level: Verschachtelungs-Ebene (0 = äußerste)
        
        Returns:
            Dict mit Gruppen-Header-Daten + allen Matrix-Spalten (None)
        """
        import uuid
        
        # Generiere eindeutige UID für Header-Zeile
        header_uid = f"GROUP_{column}_{value}_{level}_{uuid.uuid4().hex[:8]}"
        
        # 🆕 row_type Dict mit ALLEN Metadaten
        row_type_data = {
            'type': 'group_header',
            'level': level,
            'column': column,
            'value': str(value) if value is not None else '(Leer)',
            'count': count,
            'collapsed': False,
            'group_id': f"{column}_{value}_{level}"
        }
        
        # Header-Zeile mit UID und row_type
        header = {
            'uid_original': header_uid,
            'row_type': row_type_data
        }
        
        # Alle Spalten aus BasisMatrix mit None befüllen
        # So funktioniert die Projektion auch für Header-Zeilen!
        if self.basis_matrix and len(self.basis_matrix) > 0:
            first_row = self.basis_matrix[0]
            for key in first_row.keys():
                if key not in header:  # UID und row_type nicht überschreiben
                    header[key] = None
        
        return header
    
    def get_projected_columns(self) -> List[str]:
        """
        Gibt die aktuell projizierten Spalten zurück
        
        Returns:
            Liste der Spalten-Keys (ohne 'guid')
        """
        if not self.current_projection_table:
            return []
        
        # Entferne 'guid' aus der Liste
        return [col for col in self.current_projection_table if col != 'guid']
    
    def get_matrix_stats(self) -> Dict[str, Any]:
        """
        Statistik über alle Matrizen
        
        Returns:
            Dict mit Matrix-Größen
        """
        # Pure Python: Spaltenanzahl aus erstem Dict holen
        basis_columns = len(self.basis_matrix[0].keys()) if self.basis_matrix else 0
        
        return {
            'basis_matrix': len(self.basis_matrix) if self.basis_matrix is not None else 0,
            'filter_matrix': len(self.filter_matrix) if self.filter_matrix is not None else 0,
            'sort_matrix': len(self.sort_matrix) if self.sort_matrix is not None else 0,
            'basis_columns': basis_columns,
            'current_projection': len(self.current_projection_table) if self.current_projection_table else 0
        }
