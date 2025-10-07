"""
PDVM MATRIX MANAGER - Ultra-Linear Matrix-System
===============================================

LINEARER ABLAUF (KEINE KOMPLEXITÄT):
1. BASIS-Matrix (matrix_base) - Wird einmalig vom ViewManager übernommen
2. FILTER-Matrix (matrix_filter) - Filter wird auf matrix_base angewendet
3. SORT-Matrix (matrix_sort) - Sortierung wird auf matrix_filter angewendet
4. PROJEKTION - Erfolgt aus matrix_sort im ViewManager

HIERARCHIE:
matrix_base → matrix_filter → matrix_sort → Projektion

DEBUG-AUSGABE:
- Bei Filter: matrix_base + matrix_filter (erste 3 Zeilen)
- Bei Sortierung: matrix_filter + matrix_sort (erste 3 Zeilen)
"""

import logging
import traceback
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class PdvmMatrixManager:
    """
    ULTRA-LINEARER Matrix-Manager für View-Daten
    
    KEINE INTEGRATION - DIREKTE IMPLEMENTIERUNG!
    """
    
    def __init__(self, view_guid: str):
        self.view_guid = view_guid
        self.gcs = None
        self.controls = None
        
        # DIE 3 MATRIZEN (Hierarchie)
        self.matrix_base = []      # BASIS: Vom ViewManager übernommen
        self.matrix_filter = []    # FILTER: Filter auf matrix_base
        self.matrix_sort = []      # SORT: Sortierung auf matrix_filter
        
        # Spalten-Info
        self.columns = set()
        
        # Aktueller Status
        self.current_filter = None
        self.current_sort_column = None
        self.current_sort_ascending = True
        
        logger.info(f"🏗️ PdvmMatrixManager erstellt für View: {view_guid}")
    
    def initialize_with_gcs(self):
        """
        Initialisierung mit GCS - Zugriff auf Controls
        """
        try:
            from pdvm_central_systemsteuerung import get_gcs
            self.gcs = get_gcs()
            
            if not self.gcs:
                raise RuntimeError("GCS nicht verfügbar für MatrixManager!")
            
            # Controls laden (falls verfügbar)
            # TODO: Controls aus GCS laden
            
            logger.info(f"✅ MatrixManager mit GCS initialisiert")
            
        except Exception as e:
            logger.error(f"❌ MatrixManager GCS-Initialisierung fehlgeschlagen: {e}")
            raise
    
    def set_basis_matrix(self, data: List[Dict], columns: set):
        """
        BASIS-MATRIX setzen (vom ViewManager)
        
        Args:
            data: Liste von Datenzeilen (Dicts)
            columns: Set aller verfügbaren Spalten
        """
        try:
            logger.info(f"📊 === BASIS-MATRIX SETZEN ===")
            
            self.matrix_base = data.copy()
            self.columns = columns.copy()
            
            logger.info(f"📊 BASIS-Matrix gesetzt: {len(self.matrix_base)} Zeilen, {len(self.columns)} Spalten")
            
            # Initial: matrix_filter = matrix_base
            self.matrix_filter = self.matrix_base.copy()
            
            # Initial: matrix_sort = matrix_filter (noch keine Sortierung)
            self.matrix_sort = self.matrix_filter.copy()
            
            logger.info(f"✅ Alle Matrizen initial gesetzt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Setzen der BASIS-Matrix: {e}")
            raise
    
    def apply_filter(self, search_string: str = None):
        """
        EINHEITLICHER FILTER anwenden: matrix_base → matrix_filter
        Nur noch ein Parameter: search_string (vereinfachte Architektur)
        
        Args:
            search_string: Einheitlicher Filter-String (z.B. 'familienname_show:ma AND vorname_show:au')
        """
        try:
            logger.info(f"🔍 === FILTER ANWENDEN ===")
            logger.info(f"🔧 Search-String: {search_string}")
            
            if not self.matrix_base:
                logger.warning("⚠️ Keine BASIS-Matrix verfügbar")
                return False

            # DEBUG: matrix_base (vor Filter)
            self._debug_matrix("BASIS", self.matrix_base)
            
            # EINHEITLICHER FILTER ANWENDEN
            if search_string is None or search_string.strip() == "":
                # Kein Filter = alle Zeilen übernehmen
                self.matrix_filter = self.matrix_base.copy()
                logger.info(f"📋 Kein Filter - alle {len(self.matrix_filter)} Zeilen übernommen")
                success = True
            else:
                # Einheitlicher Search-String Filter anwenden
                success = self._apply_unified_search_filter(search_string)
                
            if not success:
                logger.error("❌ Filter-Anwendung fehlgeschlagen - verwende BASIS-Matrix")
                self.matrix_filter = self.matrix_base.copy()
                return False
            
            # DEBUG: matrix_filter (nach Filter)
            self._debug_matrix("FILTER", self.matrix_filter)
            logger.info(f"✅ Filter-Prozess abgeschlossen")
            
            # SCHRITT 2: FILTER → SORT  
            logger.info(f"🔄 === SCHRITT 2: FILTER → SORT ===")
            # DEBUG: FILTER-Matrix (QUELLE für Sortierung)
            self._debug_matrix("FILTER_PRE_SORT", self.matrix_filter)
            
            # Sortierung anwenden (automatisch nach jedem Filter)
            if self.current_sort_column:
                # Explizite Sortierung
                try:
                    self.matrix_sort = sorted(
                        self.matrix_filter,
                        key=lambda row: row.get(self.current_sort_column, ''),
                        reverse=not self.current_sort_ascending
                    )
                    direction = "aufsteigend" if self.current_sort_ascending else "absteigend"
                    logger.info(f"🔄 Sortiert nach '{self.current_sort_column}' ({direction}): {len(self.matrix_sort)} Zeilen")
                except Exception as sort_error:
                    logger.error(f"❌ Sortier-Fehler: {sort_error}")
                    self.matrix_sort = self.matrix_filter.copy()
            else:
                # Keine Sortierung: matrix_sort = matrix_filter
                self.matrix_sort = self.matrix_filter.copy()
                logger.info(f"📋 Keine Sortierung - {len(self.matrix_sort)} Zeilen übernommen")
            
            # DEBUG: SORT-Matrix (ZIEL nach Sortierung)
            self._debug_matrix("SORT", self.matrix_sort)
            logger.info(f"✅ Sortier-Prozess abgeschlossen")
            
            logger.info(f"🎯 === MATRIX-PIPELINE ABGESCHLOSSEN ===")
            logger.info(f"📊 Pipeline: BASIS({len(self.matrix_base)}) → FILTER({len(self.matrix_filter)}) → SORT({len(self.matrix_sort)})")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Filter-Prozess: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def apply_sort(self, sort_column: str = None, ascending: bool = True):
        """
        SORTIERUNG anwenden: matrix_filter → matrix_sort
        
        Args:
            sort_column: Spalte zum Sortieren (None = keine Sortierung)
            ascending: Aufsteigend oder absteigend
        """
        try:
            logger.info(f"🔄 === SORTIERUNG ANWENDEN ===")
            
            if not self.matrix_filter:
                logger.warning("⚠️ Keine FILTER-Matrix verfügbar")
                return
            
            # Sortierung speichern
            self.current_sort_column = sort_column
            self.current_sort_ascending = ascending
            
            # DEBUG: matrix_filter (vor Sortierung)
            self._debug_matrix("FILTER", self.matrix_filter)
            
            # SORTIERUNG ANWENDEN
            logger.info(f"🔄 === SORTIERUNG ANWENDEN ===")
            if sort_column is None or sort_column not in self.columns:
                # Keine Sortierung = Filter-Matrix übernehmen
                self.matrix_sort = self.matrix_filter.copy()
                logger.info(f"📋 Keine Sortierung - {len(self.matrix_sort)} Zeilen übernommen")
            else:
                # Sortierung durchführen
                try:
                    self.matrix_sort = sorted(
                        self.matrix_filter,
                        key=lambda row: row.get(sort_column, ''),
                        reverse=not ascending
                    )
                    direction = "aufsteigend" if ascending else "absteigend"
                    logger.info(f"🔄 Sortiert nach '{sort_column}' ({direction}): {len(self.matrix_sort)} Zeilen")
                except Exception as sort_error:
                    logger.error(f"❌ Sortier-Fehler: {sort_error}")
                    self.matrix_sort = self.matrix_filter.copy()
            
            # DEBUG: matrix_sort (nach Sortierung) - IMMER ANZEIGEN
            self._debug_matrix("SORT", self.matrix_sort)
            
            logger.info(f"✅ Sortier-Prozess abgeschlossen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Sortier-Prozess: {e}")
            raise
    
    def _apply_sort_to_filter(self):
        """
        Interne Sortierung nach Filter-Änderung - MIT MATRIX-DEBUG
        """
        logger.info(f"🔄 === INTERNE SORTIERUNG ===")
        # DEBUG: FILTER-Matrix (QUELLE für Sortierung)
        self._debug_matrix("FILTER_PRE_SORT", self.matrix_filter)
        
        if self.current_sort_column:
            # Explizite Sortierung
            try:
                self.matrix_sort = sorted(
                    self.matrix_filter,
                    key=lambda row: row.get(self.current_sort_column, ''),
                    reverse=not self.current_sort_ascending
                )
                direction = "aufsteigend" if self.current_sort_ascending else "absteigend"
                logger.info(f"🔄 Sortiert nach '{self.current_sort_column}' ({direction}): {len(self.matrix_sort)} Zeilen")
            except Exception as sort_error:
                logger.error(f"❌ Sortier-Fehler: {sort_error}")
                self.matrix_sort = self.matrix_filter.copy()
        else:
            # Keine Sortierung: matrix_sort = matrix_filter
            self.matrix_sort = self.matrix_filter.copy()
            logger.info(f"📋 Keine Sortierung - {len(self.matrix_sort)} Zeilen übernommen")
        
        # DEBUG: SORT-Matrix (ZIEL nach Sortierung)
        self._debug_matrix("SORT", self.matrix_sort)
        logger.info(f"✅ Interne Sortierung abgeschlossen")
    
    def _apply_unified_search_filter(self, search_string: str) -> bool:
        """
        EINHEITLICHER Search-String Filter (neue Architektur)
        Parst Search-String Format: 'field1:value1 AND field2:value2' oder 'global_value'
        
        Args:
            search_string: 'familienname_show:ma AND vorname_show:au' oder einfach 'ma'
        """
        try:
            logger.info(f"🎯 EINHEITLICHER FILTER: '{search_string}'")
            logger.info(f"🔍 DEBUG SEARCH-STRING: Typ={type(search_string)}, Länge={len(search_string) if search_string else 0}, Inhalt='{search_string}'")
            
            if not search_string or search_string.strip() == "":
                self.matrix_filter = self.matrix_base.copy()
                return True
            
            search_string = search_string.strip()
            
            # KRITISCH: Prüfe zuerst auf Klammern (komplexe Filter mit OR-Gruppen)
            if '(' in search_string and ')' in search_string:
                # Komplexer Filter mit Klammern: '(field:op:val OR field:op:val) AND field:op:val'
                logger.info(f"🔍 Komplexer Filter mit Klammern erkannt: '{search_string}'")
                return self._apply_multi_field_filter(search_string)
            elif ' AND ' in search_string:
                # Mehrfach-Filter: 'field1:value1 AND field2:value2'
                logger.info(f"🔍 Mehrfach-Filter erkannt: '{search_string}'")
                return self._apply_multi_field_filter(search_string)
            elif ':' in search_string:
                # Einzel-Feld-Filter: 'field:value' oder 'field:operator:value'
                logger.info(f"🔍 Feld-Filter erkannt: '{search_string}'")
                return self._apply_single_field_filter(search_string)
            else:
                # Globaler Filter: 'value'
                logger.info(f"🔍 Global-Filter erkannt: '{search_string}'")
                return self._apply_global_search_filter(search_string)
                
        except Exception as e:
            logger.error(f"❌ Fehler bei einheitlichem Filter: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.matrix_filter = self.matrix_base.copy()
            return False
    
    def _apply_multi_field_filter(self, search_string: str) -> bool:
        """
        Mehrfach-Feld-Filter: 'field1:value1 AND field2:value2' oder 'field1:value1 AND NOT field2:value2'
        
        ERWEITERT: Unterstützt komplexe Operatoren und OR-Verknüpfung mit Klammern
        Format: "(field:operator:value OR field:operator:value) AND field:operator:value"
        
        Operatoren:
        - contains: Enthält (Standard wenn nur ':' verwendet wird)
        - startswith: Beginnt mit
        - equals: Gleich
        - gte: Größer gleich
        - lte: Kleiner gleich
        - gt: Größer
        - lt: Kleiner
        """
        try:
            # Behandle Klammern für OR-Gruppen
            if '(' in search_string and ')' in search_string:
                return self._apply_complex_filter_with_groups(search_string)
            
            # Einfache AND-verknüpfte Filter (mit NOT-Unterstützung)
            field_filters = search_string.split(' AND ')
            logger.info(f"🔍 Gefundene Feld-Filter: {len(field_filters)}")
            
            filtered_rows = []
            for row in self.matrix_base:
                match_all = True
                
                # Alle Filter müssen zutreffen (AND-Verknüpfung)
                for field_filter in field_filters:
                    field_filter = field_filter.strip()
                    
                    # Prüfe auf NOT-Operation
                    is_negative = field_filter.startswith('NOT ')
                    if is_negative:
                        field_filter = field_filter[4:].strip()  # Entferne 'NOT '
                    
                    # Prüfe Filter
                    if not self._check_single_condition(row, field_filter, is_negative):
                        match_all = False
                        break
                
                if match_all:
                    filtered_rows.append(row)
            
            self.matrix_filter = filtered_rows
            logger.info(f"📋 Mehrfach-Filter: {len(self.matrix_filter)} von {len(self.matrix_base)} Zeilen gefunden")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Mehrfach-Filter: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _apply_complex_filter_with_groups(self, search_string: str) -> bool:
        """
        Komplexer Filter mit OR-Gruppen in Klammern
        Format: "(field:operator:value OR field:operator:value) AND field:operator:value"
        """
        try:
            logger.info(f"🔧 Komplexer Filter mit Gruppen: '{search_string}'")
            
            # Parse Gruppen und AND-Teile
            import re
            
            # Finde alle Klammergruppen
            pattern = r'\(([^)]+)\)'
            groups = re.findall(pattern, search_string)
            
            # Ersetze Gruppen temporär durch Platzhalter
            temp_string = search_string
            for i, group in enumerate(groups):
                temp_string = temp_string.replace(f'({group})', f'__GROUP{i}__', 1)
            
            # Parse AND-Teile
            and_parts = temp_string.split(' AND ')
            
            filtered_rows = []
            for row in self.matrix_base:
                match_all = True
                
                for part_idx, part in enumerate(and_parts):
                    part = part.strip()
                    
                    # Prüfe ob Platzhalter (Gruppe)
                    if part.startswith('__GROUP') and part.endswith('__'):
                        group_idx = int(part.replace('__GROUP', '').replace('__', ''))
                        group_content = groups[group_idx]
                        
                        # Prüfe Gruppe (kann AND oder OR enthalten)
                        if not self._check_group(row, group_content):
                            match_all = False
                            break
                    else:
                        # Normaler Filter
                        is_negative = part.startswith('NOT ')
                        if is_negative:
                            part = part[4:].strip()
                        
                        if not self._check_single_condition(row, part, is_negative):
                            match_all = False
                            break
                
                if match_all:
                    filtered_rows.append(row)
            
            self.matrix_filter = filtered_rows
            logger.info(f"📋 Komplexer Filter: {len(self.matrix_filter)} von {len(self.matrix_base)} Zeilen gefunden")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei komplexem Filter: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _check_group(self, row: dict, group_content: str) -> bool:
        """
        Prüft Gruppen-Inhalt - unterstützt sowohl AND als auch OR Logik
        
        Logik:
        - Wenn ' AND ' vorhanden: ALLE Bedingungen müssen erfüllt sein
        - Wenn ' OR ' vorhanden: MINDESTENS EINE Bedingung muss erfüllt sein
        - AND hat Vorrang vor OR (wird zuerst geprüft)
        """
        try:
            # Prüfe ob AND oder OR Logik
            if ' AND ' in group_content:
                # AND-Logik: ALLE Bedingungen müssen erfüllt sein
                and_parts = group_content.split(' AND ')
                
                for and_part in and_parts:
                    and_part = and_part.strip()
                    is_negative = and_part.startswith('NOT ')
                    if is_negative:
                        and_part = and_part[4:].strip()
                    
                    if not self._check_single_condition(row, and_part, is_negative):
                        return False  # Eine Bedingung nicht erfüllt → Gruppe schlägt fehl
                
                return True  # Alle Bedingungen erfüllt
            
            elif ' OR ' in group_content:
                # OR-Logik: MINDESTENS EINE Bedingung muss erfüllt sein
                or_parts = group_content.split(' OR ')
                
                for or_part in or_parts:
                    or_part = or_part.strip()
                    is_negative = or_part.startswith('NOT ')
                    if is_negative:
                        or_part = or_part[4:].strip()
                    
                    if self._check_single_condition(row, or_part, is_negative):
                        return True  # Mindestens eine Bedingung erfüllt
                
                return False  # Keine Bedingung erfüllt
            
            else:
                # Keine Logik-Operatoren → Einzelne Bedingung
                is_negative = group_content.startswith('NOT ')
                if is_negative:
                    group_content = group_content[4:].strip()
                
                return self._check_single_condition(row, group_content, is_negative)
        
        except Exception as e:
            logger.error(f"❌ Fehler bei Gruppen-Prüfung: {e}")
            return False
    
    def _check_single_condition(self, row: dict, condition: str, is_negative: bool = False) -> bool:
        """
        Prüft eine einzelne Bedingung mit Operator-Unterstützung
        
        Format: "field:operator:value" oder "field:value" (Standard=contains)
        """
        try:
            parts = condition.split(':')
            
            if len(parts) < 2:
                logger.warning(f"⚠️ Ungültige Bedingung: '{condition}'")
                return False
            
            # Parse Bedingung
            if len(parts) == 2:
                # Einfaches Format: "field:value" → Standard=contains
                field_name, value = parts
                operator = 'contains'
            elif len(parts) == 3:
                # Erweitertes Format: "field:operator:value"
                field_name, operator, value = parts
            else:
                logger.warning(f"⚠️ Zu viele ':' in Bedingung: '{condition}'")
                return False
            
            field_name = field_name.strip()
            operator = operator.strip().lower()
            value = value.strip()
            
            # Hole Zellwert
            cell_value = row.get(field_name, '')
            
            # Führe Vergleich durch
            result = self._compare_values(cell_value, value, operator)
            
            # NOT-Logik anwenden
            if is_negative:
                result = not result
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Bedingungsprüfung: {e}")
            return False
    
    def _compare_values(self, cell_value, search_value, operator: str) -> bool:
        """
        Vergleicht Werte mit verschiedenen Operatoren
        
        Args:
            cell_value: Wert aus der Zelle (kann None, String, int, float sein)
            search_value: Suchwert (immer String aus Filter-Dialog)
            operator: Vergleichsoperator
            
        Returns:
            bool: True wenn Bedingung erfüllt
        """
        try:
            # NUMERISCHE OPERATOREN: Zuerst numerische Konvertierung versuchen
            if operator in ['gte', 'lte', 'gt', 'lt']:
                # Behandle None/leere Werte
                if cell_value is None or cell_value == '':
                    logger.debug(f"🔢 Leerer Zellwert bei numerischem Vergleich - ignoriere Zeile")
                    return False
                
                try:
                    # Versuche direkte numerische Konvertierung (ohne lowercase!)
                    # Unterstützt: int, float, Decimal, oder numerische Strings
                    cell_num = float(str(cell_value).strip())
                    search_num = float(search_value.strip())
                    
                    if operator == 'gte':
                        result = cell_num >= search_num
                    elif operator == 'lte':
                        result = cell_num <= search_num
                    elif operator == 'gt':
                        result = cell_num > search_num
                    elif operator == 'lt':
                        result = cell_num < search_num
                    else:
                        result = False
                    
                    logger.debug(f"🔢 Numerischer Vergleich: {cell_num} {operator} {search_num} = {result}")
                    return result
                    
                except (ValueError, TypeError) as e:
                    # Fallback auf String-Vergleich nur wenn explizit gewünscht
                    logger.warning(f"⚠️ Keine numerische Konvertierung möglich: '{cell_value}' (Typ: {type(cell_value).__name__}) {operator} '{search_value}' - Fehler: {e}")
                    logger.warning(f"⚠️ Zeile wird ignoriert (kein String-Fallback bei numerischen Operatoren)")
                    return False
            
            # STRING-OPERATOREN: lowercase-Konvertierung für case-insensitive Vergleich
            else:
                # Behandle None-Werte
                if cell_value is None:
                    cell_value = ''
                
                # Konvertiere zu lowercase-Strings
                cell_str = str(cell_value).lower()
                search_str = search_value.lower()
                
                if operator == 'contains':
                    return search_str in cell_str
                
                elif operator == 'startswith':
                    return cell_str.startswith(search_str)
                
                elif operator == 'equals':
                    return cell_str == search_str
                
                else:
                    logger.warning(f"⚠️ Unbekannter Operator: '{operator}' - verwende 'contains'")
                    return search_str in cell_str
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Wert-Vergleich: {e}")
            return False
    
    def _apply_single_field_filter(self, search_string: str) -> bool:
        """
        Einzel-Feld-Filter: 'field:value'
        """
        try:
            field_name, search_value = search_string.split(':', 1)
            field_name = field_name.strip()
            search_value = search_value.strip().lower()
            
            logger.info(f"🔍 Feld '{field_name}' enthält '{search_value}'")
            
            filtered_rows = []
            for row in self.matrix_base:
                cell_value = str(row.get(field_name, '')).lower()
                if search_value in cell_value:
                    filtered_rows.append(row)
            
            self.matrix_filter = filtered_rows
            logger.info(f"📋 Feld-Filter: {len(self.matrix_filter)} von {len(self.matrix_base)} Zeilen gefunden")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Feld-Filter: {e}")
            return False
    
    def _apply_global_search_filter(self, search_string: str) -> bool:
        """
        Global-Filter: 'value' (sucht in allen Spalten)
        """
        try:
            search_value = search_string.lower()
            logger.info(f"🔍 Global-Suche: '{search_value}' in allen Spalten")
            
            filtered_rows = []
            for row in self.matrix_base:
                found = False
                for column in self.columns:
                    cell_value = str(row.get(column, '')).lower()
                    if search_value in cell_value:
                        found = True
                        break
                
                if found:
                    filtered_rows.append(row)
            
            self.matrix_filter = filtered_rows
            logger.info(f"📋 Global-Filter: {len(self.matrix_filter)} von {len(self.matrix_base)} Zeilen gefunden")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Global-Filter: {e}")
            return False
    
    def _apply_simple_filter(self, filter_criteria: Dict[str, Any]) -> bool:
        """
        Einfacher Filter anwenden (Globale Suche, spezifische Feldsuche oder parametrische Filter)
        
        Args:
            filter_criteria: {'search_value': str} oder 
                           {'field_name': str, 'search_value': str, 'operator': str} oder
                           {'filter_params': dict}
        """
        try:
            search_value = filter_criteria.get('search_value', '')
            field_name = filter_criteria.get('field_name', '')
            operator = filter_criteria.get('operator', 'enthält')
            filter_params = filter_criteria.get('filter_params', {})
            
            if filter_params:
                # Parametrische Filter aus erweiterten Suchparametern
                logger.info(f"🔍 Einfacher Filter (Parametrisch): {len(filter_params)} Parameter")
                return self._apply_parametric_filter(filter_params)
                
            elif field_name:
                # Spezifische Feldsuche (für einfachen Filter aus erweiterten Filterdaten)
                logger.info(f"🔍 Einfacher Filter (Feld): {field_name} {operator} '{search_value}'")
                
                if field_name not in self.columns:
                    logger.warning(f"⚠️ Spalte '{field_name}' nicht verfügbar")
                    self.matrix_filter = self.matrix_base.copy()
                    return True
                
                filtered_rows = []
                search_value_lower = search_value.lower()
                
                for row in self.matrix_base:
                    cell_value = str(row.get(field_name, '')).lower()
                    
                    if operator == 'enthält':
                        if search_value_lower in cell_value:
                            filtered_rows.append(row)
                    elif operator == 'beginnt_mit':
                        if cell_value.startswith(search_value_lower):
                            filtered_rows.append(row)
                    elif operator == 'gleich':
                        if cell_value == search_value_lower:
                            filtered_rows.append(row)
                    elif operator == 'nicht_gleich':
                        if cell_value != search_value_lower:
                            filtered_rows.append(row)
                
                self.matrix_filter = filtered_rows
                logger.info(f"📋 Einfacher Filter (Feld): {len(self.matrix_filter)} von {len(self.matrix_base)} Zeilen gefunden")
                return True
            else:
                # Globale Suche in allen Spalten
                logger.info(f"🔍 Einfacher Filter (Global): '{search_value}'")
                
                if not search_value:
                    self.matrix_filter = self.matrix_base.copy()
                    return True
                
                filtered_rows = []
                search_value_lower = search_value.lower()
                
                for row in self.matrix_base:
                    # Suche in allen Spalten
                    found = False
                    for column in self.columns:
                        cell_value = str(row.get(column, '')).lower()
                        if search_value_lower in cell_value:
                            found = True
                            break
                    
                    if found:
                        filtered_rows.append(row)
                
                self.matrix_filter = filtered_rows
                logger.info(f"📋 Einfacher Filter (Global): {len(self.matrix_filter)} von {len(self.matrix_base)} Zeilen gefunden")
                return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei einfachem Filter: {e}")
            self.matrix_filter = self.matrix_base.copy()
            return False
    
    def _apply_parametric_filter(self, filter_params: Dict[str, str]) -> bool:
        """
        Parametrische Filter anwenden (mehrere Feld-Wert Paare)
        
        Args:
            filter_params: Dict mit {field_name: search_value} Paaren
        """
        try:
            logger.info(f"🔍 Parametrische Filter: {len(filter_params)} Parameter")
            
            filtered_rows = []
            
            for row in self.matrix_base:
                row_matches = True
                
                # Alle Filter-Parameter müssen erfüllt sein (AND-Verknüpfung)
                for field_name, search_value in filter_params.items():
                    if not search_value.strip():
                        continue  # Leere Filter ignorieren
                    
                    if field_name not in self.columns:
                        logger.warning(f"⚠️ Spalte '{field_name}' nicht verfügbar")
                        continue
                    
                    cell_value = str(row.get(field_name, '')).lower()
                    search_value_lower = search_value.lower()
                    
                    # Standard-Operator: 'enthält'
                    if search_value_lower not in cell_value:
                        row_matches = False
                        break
                
                if row_matches:
                    filtered_rows.append(row)
            
            self.matrix_filter = filtered_rows
            logger.info(f"📋 Parametrische Filter: {len(filtered_rows)} von {len(self.matrix_base)} Zeilen gefunden")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei parametrischen Filtern: {e}")
            self.matrix_filter = self.matrix_base.copy()
            return False
    
    def _apply_extended_filter(self, filter_criteria: Dict[str, Any]) -> bool:
        """
        Erweiterter Filter anwenden (4-Positionen Struktur)
        
        Args:
            filter_criteria: Extended Filter Konfiguration mit conditions und logical_operator
        """
        try:
            logger.info(f"🔍 Erweiterter Filter: {filter_criteria}")
            
            # Fallback: wenn noch alte Struktur mit search_value
            if 'search_value' in filter_criteria:
                return self._apply_simple_filter(filter_criteria)
            
            # Neue Struktur mit conditions und logical_operator
            conditions = filter_criteria.get('conditions', [])
            logical_operator = filter_criteria.get('logical_operator', 'AND')
            
            if not conditions:
                logger.info(f"📋 Keine Bedingungen - alle {len(self.matrix_base)} Zeilen übernommen")
                self.matrix_filter = self.matrix_base.copy()
                return True
            
            logger.info(f"🔧 Erweiterte Filter-Anwendung: {len(conditions)} Bedingungen mit {logical_operator}")
            
            filtered_rows = []
            total_checked = 0
            
            for row in self.matrix_base:
                total_checked += 1
                row_matches = self._evaluate_extended_conditions(row, conditions, logical_operator)
                
                if row_matches:
                    filtered_rows.append(row)
            
            self.matrix_filter = filtered_rows
            logger.info(f"📋 Erweiterter Filter: {len(self.matrix_filter)} von {total_checked} Zeilen gefunden")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei erweitertem Filter: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.matrix_filter = self.matrix_base.copy()
            return False

    def _evaluate_extended_conditions(self, row: Dict, conditions: List[Dict], logical_operator: str) -> bool:
        """
        Evaluiert erweiterte Filter-Bedingungen für eine Zeile
        
        Args:
            row: Datenzeile
            conditions: Liste der Filter-Bedingungen
            logical_operator: 'AND' oder 'OR'
            
        Returns:
            True wenn Zeile den Bedingungen entspricht
        """
        try:
            if not conditions:
                return True
            
            # Sammle Ergebnisse aller Bedingungen
            condition_results = []
            
            for i, condition in enumerate(conditions):
                field_name = condition.get('field_name')
                value = condition.get('value', '')
                operator_type = condition.get('operator_type', 'enthält')
                negation = condition.get('negation', 'IS')
                
                # Debug der Bedingung
                logger.debug(f"🔍 Bedingung {i+1}: field_name='{field_name}', value='{value}', operator='{operator_type}', negation='{negation}'")
                
                # Wenn field_name nicht angegeben, versuche es basierend auf Position zu erraten
                if not field_name:
                    # Erste Bedingung = Familienname, Zweite = Vorname (basierend auf Trace)
                    if i == 0:
                        field_name = 'familienname_show'
                        logger.info(f"🔧 Feldname erraten für Bedingung 1: {field_name}")
                    elif i == 1:
                        field_name = 'vorname_show'
                        logger.info(f"🔧 Feldname erraten für Bedingung 2: {field_name}")
                    else:
                        logger.warning(f"⚠️ Kein Feldname für Bedingung {i+1} gefunden")
                        continue
                
                # Hole Feldwert aus der Zeile
                field_value = str(row.get(field_name, '')).lower()
                
                # Evaluiere Bedingung
                matches = self._matches_condition(field_value, value, operator_type)
                
                # Berücksichtige Negation
                if negation == 'NOT':
                    matches = not matches
                
                condition_results.append(matches)
                
                logger.debug(f"🔍 Bedingung {i+1}: {field_name}='{field_value}' {operator_type} '{value}' → {matches}")
            
            # Kombiniere Ergebnisse basierend auf logical_operator
            if logical_operator == 'AND':
                result = all(condition_results)
            else:  # OR
                result = any(condition_results)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Bedingungsauswertung: {e}")
            return False

    def _matches_condition(self, field_value: str, search_value: str, operator_type: str) -> bool:
        """
        Prüft ob ein Feldwert einer Bedingung entspricht
        
        Args:
            field_value: Wert aus der Datenzeile (bereits lowercase)
            search_value: Suchwert
            operator_type: Operator ('enthält', 'beginnt mit', 'endet mit', 'ist gleich')
            
        Returns:
            True wenn Bedingung erfüllt
        """
        if not search_value:
            return True
        
        search_value = str(search_value).lower()
        
        if operator_type == 'enthält':
            return search_value in field_value
        elif operator_type == 'beginnt mit':
            return field_value.startswith(search_value)
        elif operator_type == 'endet mit':
            return field_value.endswith(search_value)
        elif operator_type == 'ist gleich':
            return field_value == search_value
        else:
            # Default: enthält
            return search_value in field_value
    
    def _apply_gesamtfilter(self, filter_criteria: Dict[str, Any]) -> bool:
        """
        Gesamtfilter anwenden (Datenbank-Level Filter)
        
        Args:
            filter_criteria: Gesamtfilter Konfiguration
        """
        try:
            logger.info(f"🔍 Gesamtfilter: {filter_criteria}")
            
            # TODO: Integration mit Datenbank-Level Filtern
            # Für jetzt: Alle Daten übernehmen
            self.matrix_filter = self.matrix_base.copy()
            logger.info(f"📋 Gesamtfilter: {len(self.matrix_filter)} Zeilen")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Gesamtfilter: {e}")
            self.matrix_filter = self.matrix_base.copy()
            return False
    
    def get_final_data(self) -> List[Dict]:
        """
        Finale Daten für Projektion holen (matrix_sort)
        
        Returns:
            Liste der finalen Datenzeilen
        """
        return self.matrix_sort.copy() if self.matrix_sort else []
    
    def get_available_columns(self) -> set:
        """
        Verfügbare Spalten abrufen
        
        Returns:
            Set aller verfügbaren Spalten
        """
        return self.columns.copy()
    
    def test_filter_functionality(self):
        """
        Test der Filter-Funktionalität mit Debug-Ausgabe
        """
        logger.info("🧪 === FILTER-FUNKTIONALITÄT TESTEN ===")
        
        if not self.matrix_base:
            logger.warning("⚠️ Keine Basis-Daten für Test verfügbar")
            return
        
        # Test 1: Parametrischer Filter
        logger.info("🧪 Test 1: Parametrischer Filter 'familienname' enthält 'Lau'")
        success = self.apply_filter('parametric', {
            'field_name': 'familienname', 
            'search_value': 'Lau',
            'operator': 'enthält'
        })
        logger.info(f"📊 Test 1 Ergebnis: {success}, {len(self.matrix_filter)} Zeilen gefiltert")
        
        # Test 2: Einfacher Filter
        logger.info("🧪 Test 2: Einfacher Filter 'Schmidt'")
        success = self.apply_filter('simple', {
            'search_value': 'Schmidt'
        })
        logger.info(f"📊 Test 2 Ergebnis: {success}, {len(self.matrix_filter)} Zeilen gefiltert")
        
        # Test 3: Kein Filter (Reset)
        logger.info("🧪 Test 3: Filter zurücksetzen")
        success = self.apply_filter(None, None)
        logger.info(f"📊 Test 3 Ergebnis: {success}, {len(self.matrix_filter)} Zeilen (alle)")
        
        logger.info("✅ Filter-Test abgeschlossen")
    
    def _debug_matrix(self, matrix_name: str, matrix_data: List[Dict]):
        """
        Debug-Ausgabe einer Matrix (erste 3 Zeilen)
        
        Args:
            matrix_name: Name der Matrix (BASIS/FILTER/SORT)
            matrix_data: Matrix-Daten
        """
        debug_columns = ['uid_original', 'vorname_original', 'vorname_show', 'geburtsdatum_original', 'geburtsdatum_show']
        
        if not matrix_data:
            logger.info(f"   📝 {matrix_name}_MATRIX ist leer")
            return
        
        # Verfügbare Debug-Spalten finden
        available_columns = [col for col in debug_columns if col in self.columns]
        if not available_columns:
            logger.info(f"   📝 {matrix_name}_MATRIX: Debug-Spalten nicht verfügbar")
            logger.info(f"   📝 Verfügbare Spalten: {list(self.columns)[:5]}...")
            return
        
        logger.info(f"   📋 {matrix_name}_MATRIX ({len(matrix_data)} Zeilen) - Debug-Spalten: {' | '.join(available_columns)}")
        
        # Erste 3 Zeilen
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
    
    def get_status(self) -> Dict[str, Any]:
        """
        Matrix-Status für Debugging
        
        Returns:
            Status-Dictionary
        """
        return {
            'view_guid': self.view_guid,
            'basis_rows': len(self.matrix_base) if self.matrix_base else 0,
            'filter_rows': len(self.matrix_filter) if self.matrix_filter else 0,
            'sort_rows': len(self.matrix_sort) if self.matrix_sort else 0,
            'columns_count': len(self.columns),
            'current_filter': self.current_filter,
            'current_sort_column': self.current_sort_column,
            'current_sort_ascending': self.current_sort_ascending
        }


# Factory Function
_matrix_managers = {}

def get_matrix_manager(view_guid: str) -> PdvmMatrixManager:
    """
    Factory für PdvmMatrixManager - ein Manager pro View
    
    Args:
        view_guid: GUID der View
        
    Returns:
        PdvmMatrixManager Instanz
    """
    if view_guid not in _matrix_managers:
        manager = PdvmMatrixManager(view_guid)
        manager.initialize_with_gcs()
        _matrix_managers[view_guid] = manager
        logger.info(f"🏗️ Neuer PdvmMatrixManager für {view_guid} erstellt")
    else:
        logger.info(f"♻️ PdvmMatrixManager für {view_guid} wiederverwendet")
    
    return _matrix_managers[view_guid]

def reset_all_matrix_managers():
    """
    Alle Matrix-Manager zurücksetzen (bei Stichtag-Wechsel)
    """
    global _matrix_managers
    _matrix_managers.clear()
    logger.info("🔄 Alle Matrix-Manager zurückgesetzt")