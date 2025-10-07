"""
EXTENDED FILTER ENGINE V3 - 4-POSITIONEN STRUKTUR
==================================================

MODERNE Filter-Engine für die perfekte 4-Positionen Struktur:
Position 1: FIRST/AND/OR | Position 2: IS/NOT | Position 3: Operator | Position 4: Wert
"""

import logging
import re
from typing import List, Dict, Any, Union

logger = logging.getLogger(__name__)


# Import neue SearchCondition Klasse
try:
    from field_search_detail_dialog import SearchCondition
except ImportError:
    # Fallback für 4-Positionen Struktur  
    class SearchCondition:
        def __init__(self, value="", operator_type="=", logic_operator="FIRST", negation="IS"):
            self.value = value
            self.operator_type = operator_type  # Position 3: =, enthält, etc.
            self.logic_operator = logic_operator  # Position 1: FIRST, AND, OR
            self.negation = negation  # Position 2: IS, NOT
        
        def to_dict(self):
            return {
                'value': self.value,
                'operator_type': self.operator_type,
                'logic_operator': self.logic_operator,
                'negation': self.negation
            }
        
        @classmethod
        def from_dict(cls, data):
            return cls(
                value=data.get('value', ''),
                operator_type=data.get('operator_type', '='),
                logic_operator=data.get('logic_operator', 'FIRST'),
                negation=data.get('negation', 'IS')
            )


class ExtendedFilterEngine:
    """
    Engine für erweiterte Filter-Funktionalität
    
    Verarbeitet komplexe Suchbedingungen aus FieldSearchDetailDialog
    und integriert sie in die bestehende Filter-Pipeline
    """
    
    def __init__(self):
        """Initialisiere Extended Filter Engine"""
        self.extended_conditions = {}  # field_key -> List[SearchCondition]
        self.view_guid = None  # Wird beim ersten Laden gesetzt
        
    def reload_extended_conditions(self, view_guid=None):
        """
        Lädt alle erweiterten Bedingungen neu aus der Persistenz - DIREKT über GCS
        VEREINFACHT: Arbeitet immer direkt über GCS, keine view_guid-Abhängigkeit
        """
        try:
            # Importiere GCS lokal um Circular Imports zu vermeiden
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs or not hasattr(gcs, '_app_db') or not gcs._app_db:
                logger.warning("⚠️ GCS._app_db nicht verfügbar für Neuladen der erweiterten Bedingungen")
                return []
                
            # VEREINFACHT: Verwende übergebene view_guid oder hole aus SearchParameterDialog Context
            target_view_guid = view_guid or self.view_guid
            if not target_view_guid:
                # Fallback: Hole view_guid aus dem aktuellen Dialog-Context (falls verfügbar)
                # Das ist sicherer als eine fest codierte GUID
                logger.info("ℹ️ Keine view_guid verfügbar - überspringen Extended Conditions Reload")
                return []
                
            # WICHTIG: Speichere view_guid für künftige Verwendung
            if view_guid:
                self.view_guid = view_guid
                
            # RESET: Alte Bedingungen löschen 
            self.extended_conditions.clear()
                
            # KORREKT: Durchsuche anwendungsdaten über GCS._app_db
            possible_columns = ['familienname_show', 'vorname_show', 'anrede_show', 'geburtsdatum_show', 'geburtsdatum_alter_show', 'uid_show']
            
            loaded_count = 0
            for column_key in possible_columns:
                try:
                    column_data, _ = gcs._app_db.get_value(target_view_guid, column_key) or (None, None)
                    
                    if column_data and isinstance(column_data, dict) and 'conditions' in column_data:
                        conditions_data = column_data['conditions']
                        if conditions_data:
                            # Konvertiere zu SearchCondition Objekten
                            conditions = [SearchCondition.from_dict(c) for c in conditions_data]
                            self.extended_conditions[column_key] = conditions
                            loaded_count += 1
                            logger.info(f"🔄 APP-DB erweiterte Bedingungen für '{column_key}' neu geladen: {len(conditions)} Bedingungen")
                            
                except Exception as e:
                    logger.warning(f"⚠️ Fehler beim Neuladen der Bedingungen für '{column_key}': {e}")
                    continue
                    
            logger.info(f"✅ {loaded_count} erweiterte Filter-Felder neu geladen")
            return self.extended_conditions
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Neuladen der erweiterten Bedingungen: {e}")
            return []
            
            logger.info(f"✅ {loaded_count} erweiterte Filter-Felder aus ANWENDUNGSDATEN neu geladen")
            
        except Exception as e:
            logger.error(f"❌ Kritischer Fehler beim Neuladen der erweiterten Bedingungen: {e}")
        
    def set_field_conditions(self, field_key: str, conditions: List[Dict]):
        """
        Setze erweiterte Bedingungen für ein Feld - NEUE SAUBERE STRUKTUR
        
        Args:
            field_key: Schlüssel des Feldes (ohne field_ Prefix!)
            conditions: Liste von SearchCondition-Dictionaries
        """
        try:
            # Convert dicts to SearchCondition objects if needed
            if conditions and isinstance(conditions[0], dict):
                self.extended_conditions[field_key] = [
                    SearchCondition.from_dict(c) for c in conditions
                ]
            else:
                self.extended_conditions[field_key] = conditions
                
            # SOFORT speichern in neuer sauberer Struktur
            self.save_field_conditions(field_key, conditions)
            
            logger.info(f"✅ Erweiterte Bedingungen für '{field_key}' gesetzt und gespeichert: {len(conditions)} Bedingungen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Setzen der Bedingungen für '{field_key}': {e}")

    def save_field_conditions(self, field_key: str, conditions: List):
        """
        Speichere erweiterte Bedingungen für ein Feld persistent - KORRIGIERT: in anwendungsdaten
        
        Args:
            field_key: Spaltenname ohne field_ prefix
            conditions: Liste der Bedingungen
        """
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs or not hasattr(gcs, '_app_db') or not gcs._app_db or not self.view_guid:
                logger.warning("⚠️ GCS._app_db oder view_guid nicht verfügbar für Speicherung")
                return
            
            # KORREKT: Aktuelle Spalten-Daten aus anwendungsdaten laden
            current_data, _ = gcs._app_db.get_value(self.view_guid, field_key) or ({}, None)
            if not isinstance(current_data, dict):
                current_data = {}
            
            # Conditions setzen
            if conditions:
                # SearchCondition Objekte zu Dicts serialisieren
                if hasattr(conditions[0], 'to_dict'):
                    current_data['conditions'] = [c.to_dict() for c in conditions]
                else:
                    current_data['conditions'] = conditions
            else:
                current_data['conditions'] = []
            
            # Simple_search beibehalten falls vorhanden
            if 'simple_search' not in current_data:
                current_data['simple_search'] = ''
            
            # KORREKT: Zurück in anwendungsdaten speichern
            gcs._app_db.set_value(self.view_guid, field_key, current_data)
            gcs._app_db.save_all_values()
            
            logger.info(f"💾 APP-DB erweiterte Bedingungen gespeichert: {field_key} = {{'simple_search': '{current_data['simple_search']}', 'conditions': {len(current_data['conditions'])} items}}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern erweiterter Bedingungen für '{field_key}': {e}")
            
    def clear_field_conditions(self, field_key: str):
        """Lösche erweiterte Bedingungen für ein Feld"""
        if field_key in self.extended_conditions:
            del self.extended_conditions[field_key]
            logger.info(f"🗑️ Erweiterte Bedingungen für '{field_key}' gelöscht")
            
    def has_conditions(self, field_key: str = None) -> bool:
        """
        Prüfe ob erweiterte Bedingungen existieren
        
        Args:
            field_key: Spezifisches Feld (optional)
            
        Returns:
            bool: True wenn Bedingungen existieren
        """
        if field_key:
            return field_key in self.extended_conditions and bool(self.extended_conditions[field_key])
        else:
            return any(self.extended_conditions.values())
            
    def apply_extended_filters_to_table(self, view_dialog, basic_filters: Dict):
        """
        NEUE METHODE: Wendet erweiterte Filter direkt auf die Tabelle an
        Arbeitet wie der normale Spaltenfilter durch Verstecken/Anzeigen von Zeilen
        
        Args:
            view_dialog: Der View-Dialog mit der Tabelle
            basic_filters: Basis-Filter-Konfiguration
        """
        try:
            logger.info("🔍 🆕 ERWEITERTE FILTER: Direkte Tabellen-Filterung gestartet")
            
            # Tabelle aus view_dialog extrahieren
            table = None
            if hasattr(view_dialog, 'display') and hasattr(view_dialog.display, 'table'):
                table = view_dialog.display.table
            elif hasattr(view_dialog, 'table'):
                table = view_dialog.table
            else:
                logger.error("❌ Keine Tabelle gefunden in view_dialog")
                return
            
            visible_count = 0
            total_count = table.rowCount()
            
            logger.info(f"📊 Tabelle hat {total_count} Zeilen")
            
            # Durch alle Tabellenzeilen iterieren
            for row_index in range(total_count):
                # Zeilen-Daten aus der Tabelle extrahieren (wie sie der Kunde sieht!)
                row_data = self._extract_row_data_from_table(table, row_index)
                
                logger.info(f"📋 Zeile {row_index}: {row_data}")
                
                # Erweiterte Bedingungen prüfen
                matches = self._row_matches_extended_conditions(row_data, basic_filters)
                
                # Zeile anzeigen/verstecken
                logger.info(f"🎯 VOR setRowHidden für Zeile {row_index}: matches={matches}, setRowHidden wird aufgerufen mit: not matches = {not matches}")
                table.setRowHidden(row_index, not matches)
                
                # Direkt nach dem Aufruf prüfen
                actually_hidden = table.isRowHidden(row_index)
                logger.info(f"🎯 NACH setRowHidden für Zeile {row_index}: tatsächlich versteckt = {actually_hidden}, erwartet versteckt = {not matches}")
                
                if matches:
                    visible_count += 1
                    
                logger.info(f"{'✅' if matches else '❌'} Zeile {row_index}: {'sichtbar' if matches else 'versteckt'}")
            
            # Status-Update
            if hasattr(view_dialog, 'search_status'):
                if visible_count == 0:
                    view_dialog.search_status.setText(f"⚠️ Keine Treffer für erweiterte Filter")
                    view_dialog.search_status.setStyleSheet("QLabel { color: #d32f2f; }")
                else:
                    view_dialog.search_status.setText(f"🔍 {visible_count} von {total_count} Zeilen (erweitert gefiltert)")
                    view_dialog.search_status.setStyleSheet("QLabel { color: #388e3c; }")
                    
            logger.info(f"✅ Erweiterte Filter angewendet: {visible_count} von {total_count} Zeilen sichtbar")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei erweiterten Tabellen-Filtern: {e}")
            raise
            
    def _extract_row_data_from_table(self, table, row_index: int) -> Dict[str, Any]:
        """
        Extrahiert Zeilen-Daten direkt aus der QTable (die echten Kundendaten!)
        
        Args:
            table: QTableWidget
            row_index: Zeilen-Index
            
        Returns:
            Dict mit Feld-Namen und Werten
        """
        row_data = {}
        
        try:
            # Header-Labels holen für Spalten-Mapping
            for col in range(table.columnCount()):
                header_item = table.horizontalHeaderItem(col)
                if header_item:
                    header_text = header_item.text()
                    
                    # Zellwert holen
                    cell_item = table.item(row_index, col)
                    cell_value = cell_item.text() if cell_item else ""
                    
                    # Feld-Name normalisieren (wie in Search-Dialog)
                    field_key = self._normalize_field_name(header_text)
                    row_data[field_key] = cell_value
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Extrahieren der Zeilen-Daten: {e}")
            
        return row_data
        
    def _normalize_field_name(self, header_text: str) -> str:
        """Normalisiert Feld-Namen für Mapping zwischen Tabelle und Filter-Bedingungen"""
        # Entferne Sonderzeichen und konvertiere zu lowercase
        normalized = header_text.lower().replace(' ', '_').replace('-', '_')
        
        # Mapping für spezielle Felder
        field_mappings = {
            'vorname': 'vorname_show',
            'familienname': 'familienname_show', 
            'geburtsdatum': 'geburtsdatum_show',
            'anrede': 'anrede_show',
            'uid': 'uid_show',
            'alter': 'geburtsdatum_alter_show'
        }
        
        for original, mapped in field_mappings.items():
            if original in normalized:
                return mapped
                
        return normalized

    def apply_extended_filters(self, original_matrix: List[Dict], basic_filters: Dict) -> List[Dict]:
        """
        Wendet erweiterte Filter auf die Datenmatrix an
        
        Args:
            original_matrix: Ursprüngliche Datenmatrix
            basic_filters: Basis-Filter-Konfiguration (für Kompatibilität)
            
        Returns:
            List[Dict]: Gefilterte Datenmatrix
        """
        try:
            if not self.has_conditions():
                # Keine erweiterten Bedingungen -> keine Filterung
                logger.info("ℹ️ Keine erweiterten Bedingungen aktiv")
                return original_matrix
                
            logger.info(f"🔍 DEBUG: Starte erweiterte Filterung mit {len(original_matrix)} Zeilen")
            logger.info(f"🔍 DEBUG: Aktive Bedingungen: {list(self.extended_conditions.keys())}")
            
            filtered_matrix = []
            
            for i, row in enumerate(original_matrix):
                matches = self._row_matches_extended_conditions(row, basic_filters)
                logger.info(f"🔍 DEBUG: Zeile {i} - Match: {matches}")
                if matches:
                    filtered_matrix.append(row)
            
            logger.info(f"🔍 Erweiterte Filter angewendet: {len(filtered_matrix)} von {len(original_matrix)} Zeilen")
            return filtered_matrix
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anwenden erweiterter Filter: {e}")
            return original_matrix  # Fallback: Original-Matrix zurückgeben
    
    def _row_matches_extended_conditions(self, row: Dict, basic_filters: Dict) -> bool:
        """
        Prüft ob eine Zeile den erweiterten Bedingungen entspricht
        
        Args:
            row: Datenzeile als Dictionary
            basic_filters: Basis-Filter für case_sensitive, etc.
            
        Returns:
            bool: True wenn Zeile den Bedingungen entspricht
        """
        try:
            # Debug: Zeile kurz anzeigen für Kontext
            row_preview = {k: str(v)[:30] + "..." if len(str(v)) > 30 else str(v) for k, v in row.items() if "show" in k}
            logger.info(f"🔍 DEBUG: Prüfe Zeile mit Preview: {row_preview}")
            
            # Alle Felder mit erweiterten Bedingungen müssen erfüllt sein (AND-Verknüpfung zwischen Feldern)
            for field_key, conditions in self.extended_conditions.items():
                if not conditions:  # Leere Bedingungen ignorieren
                    logger.info(f"🔍 DEBUG: Feld '{field_key}' hat leere Bedingungen - wird ignoriert")
                    continue
                    
                field_matches = self._evaluate_field_conditions(row, field_key, conditions, basic_filters)
                logger.info(f"🔍 DEBUG: Feld '{field_key}' Match-Ergebnis: {field_matches}")
                if not field_matches:
                    logger.info(f"🔍 DEBUG: Zeile wird ausgeschlossen da Feld '{field_key}' nicht matcht")
                    return False  # Ein Feld erfüllt Bedingungen nicht -> Zeile ausschließen
                    
            logger.info(f"🔍 DEBUG: Zeile erfüllt ALLE erweiterten Bedingungen - wird akzeptiert")
            return True  # Alle Felder mit Bedingungen erfüllt
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler bei Zeilenevaluierung: {e}")
            return False  # Bei Fehlern: Zeile ausschließen für Sicherheit
    
    def _evaluate_field_conditions(self, row: Dict, field_key: str, conditions: List[SearchCondition], basic_filters: Dict) -> bool:
        """
        Evaluiert alle Bedingungen für ein einzelnes Feld - 4-POSITIONEN STRUKTUR
        
        Beispiel-Bedingungen:
        - "FIRST IS = 'Maier'"  
        - "AND NOT enthält 'test'"
        - "OR IS beginnt mit 'A'"
        
        Args:
            row: Datenzeile
            field_key: Feldschlüssel
            conditions: Liste der SearchCondition-Objekte (4-Positionen)
            basic_filters: Basis-Filter-Konfiguration
            
        Returns:
            bool: True wenn Feldwert den Bedingungen entspricht
        """
        if not conditions:
            logger.info(f"🔍 DEBUG: Keine Bedingungen für Feld '{field_key}'")
            return True  # Keine Bedingungen = erfüllt
            
        # Feldwert extrahieren
        if field_key not in row:
            logger.warning(f"⚠️ Feld '{field_key}' nicht in Zeile gefunden")
            return False
            
        field_value = str(row[field_key]) if row[field_key] is not None else ""
        
        logger.info(f"🔍 DEBUG: Evaluiere Feld '{field_key}' mit Wert '{field_value}' gegen {len(conditions)} Bedingungen")
        
        # ERSTE BEDINGUNG (FIRST): Basis-Ergebnis ermitteln
        first_condition = conditions[0]
        result = self._evaluate_single_condition_4pos(field_value, first_condition, basic_filters)
        
        display_text = f"{first_condition.logic_operator} {first_condition.negation} {first_condition.operator_type} '{first_condition.value}'"
        logger.info(f"🔍 DEBUG: Erste Bedingung '{display_text}' gegen '{field_value}': {result}")
        
        # WEITERE BEDINGUNGEN: AND/OR-Verknüpfung
        for i, condition in enumerate(conditions[1:], 1):
            condition_result = self._evaluate_single_condition_4pos(field_value, condition, basic_filters)
            
            display_text = f"{condition.logic_operator} {condition.negation} {condition.operator_type} '{condition.value}'"
            logger.info(f"🔍 DEBUG: Bedingung {i+1} '{display_text}' gegen '{field_value}': {condition_result}")
            
            # Position 1: Logic-Operator anwenden
            if condition.logic_operator == "AND":
                result = result and condition_result
            elif condition.logic_operator == "OR":
                result = result or condition_result
            else:
                logger.warning(f"⚠️ Unbekannter Logic-Operator: {condition.logic_operator}")
                result = result and condition_result  # Fallback: AND
            
            logger.info(f"🔍 DEBUG: Zwischenergebnis nach {condition.logic_operator}: {result}")
                
        logger.info(f"🔍 DEBUG: Finales Ergebnis für Feld '{field_key}': {result}")
        return result
    
    def _evaluate_single_condition_4pos(self, field_value: str, condition: SearchCondition, basic_filters: Dict) -> bool:
        """
        Evaluiert eine einzelne Suchbedingung - 4-POSITIONEN STRUKTUR
        
        Position 1: FIRST/AND/OR (wird von Caller verarbeitet)
        Position 2: IS/NOT (wird hier angewendet)  
        Position 3: Operator (=, enthält, etc.)
        Position 4: Wert (der Suchbegriff)
        
        Args:
            field_value: Wert des Feldes  
            condition: SearchCondition mit 4-Positionen Struktur
            basic_filters: Basis-Filter für case_sensitive, etc.
            
        Returns:
            bool: True wenn Bedingung erfüllt ist
        """
        try:
            search_value = condition.value  # Position 4: Wert
            if not search_value:  # Leere Suchbegriffe erfüllen nie eine Bedingung
                logger.info(f"🔍 DEBUG: Leerer Suchbegriff in Bedingung")
                return False
                
            # Case sensitivity aus basic_filters oder Default
            case_sensitive = basic_filters.get('case_sensitive', False)
            
            # Textvergleich vorbereiten
            if not case_sensitive:
                field_value_compare = field_value.lower()
                search_value_compare = search_value.lower()
            else:
                field_value_compare = field_value
                search_value_compare = search_value
            
            operator_type = condition.operator_type  # Position 3: Operator
            logger.info(f"🔍 DEBUG: Vergleiche '{field_value_compare}' mit '{search_value_compare}' (Operator: {operator_type}, Case: {case_sensitive})")
            
            # Position 3: Operator-Typ anwenden  
            if operator_type == "=":
                matches = field_value_compare == search_value_compare
            elif operator_type == "!=":
                matches = field_value_compare != search_value_compare
            elif operator_type == "enthält":
                matches = search_value_compare in field_value_compare
            elif operator_type == "beginnt mit":
                matches = field_value_compare.startswith(search_value_compare)
            elif operator_type == "endet mit":
                matches = field_value_compare.endswith(search_value_compare)
            elif operator_type == ">":
                try:
                    matches = float(field_value) > float(search_value)
                except ValueError:
                    matches = field_value_compare > search_value_compare  # Fallback: String-Vergleich
            elif operator_type == "<":
                try:
                    matches = float(field_value) < float(search_value)
                except ValueError:
                    matches = field_value_compare < search_value_compare  # Fallback: String-Vergleich
            elif operator_type == ">=":
                try:
                    matches = float(field_value) >= float(search_value)
                except ValueError:
                    matches = field_value_compare >= search_value_compare  # Fallback: String-Vergleich
            elif operator_type == "<=":
                try:
                    matches = float(field_value) <= float(search_value)
                except ValueError:
                    matches = field_value_compare <= search_value_compare  # Fallback: String-Vergleich
            else:
                logger.warning(f"⚠️ Unbekannter Operator-Typ: {operator_type}")
                matches = search_value_compare in field_value_compare  # Fallback: enthält
            
            logger.info(f"🔍 DEBUG: Suchergebnis vor Negation (Position 2): {matches}")
            
            # Position 2: Negation anwenden
            if condition.negation == "NOT":
                matches = not matches
                logger.info(f"🔍 DEBUG: Suchergebnis nach NOT-Anwendung: {matches}")
            elif condition.negation == "IS":
                # IS = normale positive Suche, matches bleibt unverändert
                logger.info(f"🔍 DEBUG: IS-Bedingung, Ergebnis bleibt: {matches}")
            else:
                logger.warning(f"⚠️ Unbekannte Negation: {condition.negation}, verwende IS")
                
            return matches
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler bei 4-Positionen Bedingungsevaluierung: {e}")
            return False
    
    def _wildcard_match(self, field_value: str, pattern: str) -> bool:
        """
        Wildcard-Matching mit * und ?
        
        Args:
            field_value: Feldwert
            pattern: Wildcard-Pattern
            
        Returns:
            bool: True wenn Pattern matcht
        """
        try:
            # Wildcard zu Regex konvertieren
            regex_pattern = re.escape(pattern)
            regex_pattern = regex_pattern.replace(r'\*', '.*')  # * -> beliebig viele Zeichen
            regex_pattern = regex_pattern.replace(r'\?', '.')   # ? -> ein Zeichen
            regex_pattern = f'^{regex_pattern}$'  # Vollständiger Match
            
            return bool(re.match(regex_pattern, field_value))
            
        except re.error as e:
            logger.warning(f"⚠️ Wildcard-Regex-Fehler: {e}")
            return False
    
    def _regex_match(self, field_value: str, pattern: str, case_sensitive: bool) -> bool:
        """
        Regulärer Ausdruck-Matching
        
        Args:
            field_value: Feldwert
            pattern: Regex-Pattern
            case_sensitive: Case-sensitive matching
            
        Returns:
            bool: True wenn Pattern matcht
        """
        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            return bool(re.search(pattern, field_value, flags))
            
        except re.error as e:
            logger.warning(f"⚠️ Regex-Fehler: {e}")
            return False
    
    def get_active_conditions_summary(self) -> Dict[str, str]:
        """
        Erstelle Zusammenfassung der aktiven Bedingungen für neue Struktur
        
        Returns:
            Dict: field_key -> readable summary
        """
        summary = {}
        
        for field_key, conditions in self.extended_conditions.items():
            if not conditions:
                continue
                
            condition_texts = []
            for i, condition in enumerate(conditions):
                try:
                    if hasattr(condition, 'get_display_text'):
                        # Neue SearchCondition Klasse
                        text = condition.get_display_text()
                    else:
                        # Alte Struktur als Fallback
                        text = self._create_display_text_fallback(condition)
                    
                    if i == 0:
                        # Erste Bedingung: Entferne Logic-Operator aber behalte NOT
                        # Format: "(AND) NOT enthält 'test'" -> "NOT enthält 'test'"
                        text = re.sub(r'^\((?:AND|OR)\)\s*', '', text)
                    
                    condition_texts.append(text)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Fehler bei Bedingung {i}: {e}")
                    continue
                    
            if condition_texts:
                summary[field_key] = " ".join(condition_texts)
            
        return summary
    
    def get_active_conditions(self) -> Dict[str, List]:
        """
        Gibt die aktuell aktiven erweiterten Bedingungen zurück
        
        Returns:
            Dict: field_key -> Liste der Bedingungen
        """
        # Kopie der aktuellen Bedingungen zurückgeben
        return dict(self.extended_conditions)
    
    def _create_display_text_fallback(self, condition) -> str:
        """
        Fallback für alte Bedingungsstrukturen
        """
        try:
            # Dict-Zugriff versuchen
            if hasattr(condition, 'value'):
                value = condition.value
                operator_type = getattr(condition, 'operator_type', 'enthält')
                logic_operator = getattr(condition, 'logic_operator', 'AND')
                negate = getattr(condition, 'negate', False)
            else:
                # Dict-Struktur
                value = condition.get('value', '')
                operator_type = condition.get('operator_type', 'enthält')
                logic_operator = condition.get('logic_operator', 'AND')
                negate = condition.get('negate', False)
            
            parts = []
            
            if logic_operator:
                parts.append(f"({logic_operator})")
            
            if negate:
                parts.append("NOT")
            
            parts.append(operator_type)
            parts.append(f"'{value}'")
            
            return " ".join(parts)
            
        except Exception as e:
            logger.warning(f"⚠️ Fallback-Display-Text Fehler: {e}")
            return "Bedingung"
    
    def clear_all_conditions(self):
        """Lösche alle erweiterten Bedingungen - MIT zentralem Filter-Reset"""
        try:
            from central_filter_reset import reset_all_filters_for_view
            
            if self.view_guid:
                logger.info("🔄 Starte kompletter Filter-Reset über Extended Filter Engine")
                
                # Nutze zentrales Filter-Reset-System
                success = reset_all_filters_for_view(self.view_guid, preserve_gesamtfilter=True)
                
                if success:
                    # Zusätzlich: Lokale Conditions löschen
                    self.extended_conditions.clear()
                    if hasattr(self, 'extended_conditions_cache') and self.view_guid in self.extended_conditions_cache:
                        del self.extended_conditions_cache[self.view_guid]
                    
                    logger.info("✅ Kompletter Filter-Reset über Extended Filter Engine erfolgreich")
                else:
                    # Fallback: Nur lokale Conditions löschen
                    self.extended_conditions.clear()
                    logger.warning("⚠️ Zentraler Reset hatte Probleme - nur lokale Conditions gelöscht")
            else:
                # Kein view_guid - nur lokale Conditions löschen
                self.extended_conditions.clear()
                logger.info("🗑️ Nur lokale Extended Conditions gelöscht (keine view_guid)")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Löschen aller Extended Conditions: {e}")
            # Fallback: Wenigstens lokale Conditions löschen
            self.extended_conditions.clear()


# Globale Instanz der Extended Filter Engine
extended_filter_engine = ExtendedFilterEngine()