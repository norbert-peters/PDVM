"""
🔍 EINHEITLICHER SEARCH STRING PARSER
======================================
ZWECK: Parst einheitliche search_strings von allen 3 Filter-Managern und
       wandelt sie in ausführbare Filter-Funktionen um.

FORMATE:
--------
1. SCHNELLSUCHE: "GLOBAL:contains:lau"
   → Suche "lau" in ALLEN sichtbaren Spalten

2. EINFACH: "familienname_show:contains:Müller"
   → Suche "Müller" in Spalte familienname_show mit contains

3. EINFACH MULTI: "familienname_show:contains:Müller||vorname_show:contains:Max"
   → ALLE Bedingungen müssen zutreffen (AND-Verknüpfung)

4. KOMPLEX: "familienname_show:AND|IS|contains|Müller"
   → 4-Positionen Struktur mit AND/OR + IS/NOT + Operator + Wert

5. KOMPLEX MULTI: "familienname_show:AND|IS|contains|Müller||familienname_show:OR|NOT|equals|Schmidt"
   → Mehrere Bedingungen mit komplexer Logik

STRUKTUR:
---------
basis_part = "feld:operator:wert" (Einfach)
komplex_part = "feld:pos1|pos2|pos3|pos4" (Komplex)
multi = "part1||part2||part3" (Mehrere Bedingungen)
"""

import logging
from typing import List, Dict, Any, Callable, Optional
import re

logger = logging.getLogger(__name__)


class SearchStringParser:
    """Parst einheitliche search_strings in Filter-Funktionen"""
    
    # Operator-Mappings
    OPERATOR_MAP = {
        'contains': 'enthält',
        'equals': 'ist',
        'startswith': 'beginnt mit',
        'endswith': 'endet mit',
        '>': 'größer',
        '<': 'kleiner',
        '>=': 'größer gleich',
        '<=': 'kleiner gleich',
        '!=': 'ungleich'
    }
    
    def __init__(self):
        """Initialisiert Parser"""
        logger.info("🔍 SearchStringParser initialisiert")
    
    def parse(self, search_string: str, filter_source: str = None) -> Optional[Callable]:
        """
        RAW-OPTIMIERUNG: Parst search_string mit filter_source Hint
        
        Args:
            search_string: RAW User-Eingabe ODER formatierter String
            filter_source: 'schnell' | 'einfach' | 'komplex' | None (Auto-Detection)
            
        Returns:
            Callable das row → bool Funktion ist, oder None bei Fehler
        """
        try:
            if not search_string or not search_string.strip():
                logger.info("ℹ️ Leerer search_string - kein Filter")
                return None
            
            search_string = search_string.strip()
            logger.info(f"🔍 Parse search_string: '{search_string}' mit source={filter_source}")
            
            # PRIORITÄT: filter_source steuert Parsing-Modus
            if filter_source == 'schnell':
                # Schnellsuche: RAW Input = globale Suche in allen Spalten
                logger.info("🌍 SCHNELL-Modus: Globale Suche")
                return self._parse_global_search_raw(search_string)
            
            elif filter_source == 'einfach':
                # Einfach-Filter: Multi-Field mit || und contains
                logger.info("📋 EINFACH-Modus: Multi-Field Filter")
                if "||" in search_string:
                    return self._parse_multi_field(search_string)
                else:
                    return self._parse_einfach_single(search_string)
            
            elif filter_source == 'komplex':
                # Komplex-Filter: 4-Positionen Struktur
                logger.info("🔬 KOMPLEX-Modus: Erweiterte Filter")
                if "||" in search_string:
                    return self._parse_multi_field(search_string)
                else:
                    return self._parse_komplex_single(search_string)
            
            # FALLBACK: Auto-Detection für alte Formate oder ohne source
            logger.info("🔍 AUTO-Detection: Kein filter_source angegeben")
            
            # 1. GLOBAL-Suche?
            if search_string.startswith("GLOBAL:"):
                return self._parse_global_search(search_string)
            
            # 2. Multi-Field (mit ||)?
            if "||" in search_string:
                return self._parse_multi_field(search_string)
            
            # 3. Komplex (mit |)?
            if "|" in search_string:
                return self._parse_komplex_single(search_string)
            
            # 4. Einfach (feld:operator:wert)
            return self._parse_einfach_single(search_string)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Parsen search_string: {e}", exc_info=True)
            return None
    
    def _parse_global_search(self, search_string: str) -> Callable:
        """
        Parst GLOBAL-Suche: "GLOBAL:contains:lau"
        
        Returns:
            Filter-Funktion die in ALLEN Spalten sucht
        """
        # Format: GLOBAL:operator:wert
        parts = search_string.split(":")
        if len(parts) != 3:
            logger.error(f"❌ Ungültiges GLOBAL Format: {search_string}")
            return None
        
        _, operator, search_value = parts
        search_value = search_value.lower()
        
        logger.info(f"🌍 GLOBAL-Suche: operator='{operator}', value='{search_value}'")
        
        def filter_func(row: Dict[str, Any]) -> bool:
            """Sucht in ALLEN Spalten nach Wert"""
            for col_key, col_value in row.items():
                # Skip spezielle Spalten
                if col_key in ['_uid', 'row_type', '__collapsed', '__abdatum', '__formatiert']:
                    continue
                
                # Skip ab-datum und formatiert Suffix
                if col_key.endswith('__abdatum') or col_key.endswith('__formatiert'):
                    continue
                
                # Wert zu String konvertieren
                str_value = str(col_value).lower() if col_value is not None else ""
                
                # Operator anwenden
                if operator == "contains":
                    if search_value in str_value:
                        return True
                elif operator == "equals":
                    if search_value == str_value:
                        return True
                elif operator == "startswith":
                    if str_value.startswith(search_value):
                        return True
                elif operator == "endswith":
                    if str_value.endswith(search_value):
                        return True
            
            return False
        
        return filter_func
    
    def _parse_global_search_raw(self, search_value: str) -> Callable:
        """
        RAW-OPTIMIERUNG: Parst globale Suche OHNE Format-Präfix
        
        Input: "lau" (direkt vom User, kein "GLOBAL:contains:")
        
        Returns:
            Filter-Funktion die in ALLEN Spalten mit 'contains' sucht
        """
        search_value = search_value.lower()
        logger.info(f"🌍 GLOBAL-Suche (RAW): '{search_value}'")
        
        def filter_func(row: Dict[str, Any]) -> bool:
            """Sucht in ALLEN Spalten nach Wert (default: contains)"""
            for col_key, col_value in row.items():
                # Skip spezielle Spalten
                if col_key in ['_uid', 'row_type', '__collapsed', '__abdatum', '__formatiert']:
                    continue
                
                # Skip ab-datum und formatiert Suffix
                if col_key.endswith('__abdatum') or col_key.endswith('__formatiert'):
                    continue
                
                # Wert zu String konvertieren
                str_value = str(col_value).lower() if col_value is not None else ""
                
                # RAW: Immer 'contains'
                if search_value in str_value:
                    return True
            
            return False
        
        return filter_func
    
    def _parse_einfach_single(self, search_string: str) -> Callable:
        """
        Parst einfache Einzelbedingung: "familienname_show:contains:Müller"
        
        Returns:
            Filter-Funktion für ein Feld
        """
        # Format: feld:operator:wert
        parts = search_string.split(":")
        if len(parts) != 3:
            logger.error(f"❌ Ungültiges EINFACH Format: {search_string}")
            return None
        
        field_key, operator, search_value = parts
        search_value = search_value.lower()
        
        logger.info(f"📋 EINFACH-Filter: feld='{field_key}', operator='{operator}', value='{search_value}'")
        
        def filter_func(row: Dict[str, Any]) -> bool:
            """Prüft eine Spalte mit Operator"""
            if field_key not in row:
                return False
            
            field_value = row[field_key]
            str_value = str(field_value).lower() if field_value is not None else ""
            
            # Operator anwenden
            if operator == "contains":
                return search_value in str_value
            elif operator == "equals":
                return search_value == str_value
            elif operator == "startswith":
                return str_value.startswith(search_value)
            elif operator == "endswith":
                return str_value.endswith(search_value)
            elif operator == ">":
                try:
                    return float(str_value) > float(search_value)
                except:
                    return False
            elif operator == "<":
                try:
                    return float(str_value) < float(search_value)
                except:
                    return False
            elif operator == ">=":
                try:
                    return float(str_value) >= float(search_value)
                except:
                    return False
            elif operator == "<=":
                try:
                    return float(str_value) <= float(search_value)
                except:
                    return False
            elif operator == "!=":
                return search_value != str_value
            else:
                logger.warning(f"⚠️ Unbekannter Operator: {operator}")
                return False
        
        return filter_func
    
    def _parse_multi_field(self, search_string: str) -> Callable:
        """
        Parst Multi-Field Filter: "feld1:op1:val1||feld2:op2:val2"
        
        ALLE Bedingungen müssen zutreffen (AND-Verknüpfung)
        
        Returns:
            Filter-Funktion mit AND-Logik
        """
        # Split bei ||
        parts = search_string.split("||")
        logger.info(f"📋 MULTI-Field Filter: {len(parts)} Bedingungen (AND-verknüpft)")
        
        # Parse jede Einzelbedingung
        conditions = []
        for part in parts:
            part = part.strip()
            
            # Komplex oder Einfach?
            if "|" in part:
                cond_func = self._parse_komplex_single(part)
            else:
                cond_func = self._parse_einfach_single(part)
            
            if cond_func:
                conditions.append(cond_func)
        
        if not conditions:
            logger.error(f"❌ Keine gültigen Bedingungen in: {search_string}")
            return None
        
        def filter_func(row: Dict[str, Any]) -> bool:
            """ALLE Bedingungen müssen zutreffen"""
            for cond in conditions:
                if not cond(row):
                    return False
            return True
        
        return filter_func
    
    def _parse_komplex_single(self, search_string: str) -> Callable:
        """
        Parst komplexe Einzelbedingung: "familienname_show:AND|IS|contains|Müller"
        
        4-Positionen Struktur:
          pos1 = AND/OR (wird hier ignoriert, nur für Multi relevant)
          pos2 = IS/NOT (negiert Bedingung)
          pos3 = Operator
          pos4 = Wert
        
        Returns:
            Filter-Funktion für komplexe Bedingung
        """
        # Format: feld:pos1|pos2|pos3|pos4
        if ":" not in search_string:
            logger.error(f"❌ Ungültiges KOMPLEX Format (kein :): {search_string}")
            return None
        
        feld_part, rest = search_string.split(":", 1)
        positions = rest.split("|")
        
        if len(positions) != 4:
            logger.error(f"❌ Ungültiges KOMPLEX Format (nicht 4 Positionen): {search_string}")
            return None
        
        field_key = feld_part
        pos1, pos2, pos3, pos4 = positions
        
        is_negated = (pos2 == "NOT")
        operator = pos3
        search_value = pos4.lower()
        
        logger.info(f"🔬 KOMPLEX-Filter: feld='{field_key}', neg={is_negated}, op='{operator}', val='{search_value}'")
        
        def filter_func(row: Dict[str, Any]) -> bool:
            """Prüft komplexe Bedingung mit Negation"""
            if field_key not in row:
                return False
            
            field_value = row[field_key]
            str_value = str(field_value).lower() if field_value is not None else ""
            
            # Basis-Check mit Operator
            match = False
            
            if operator == "contains" or operator == "enthält":
                match = search_value in str_value
            elif operator == "equals" or operator == "ist":
                match = search_value == str_value
            elif operator == "startswith" or operator == "beginnt mit":
                match = str_value.startswith(search_value)
            elif operator == "endswith" or operator == "endet mit":
                match = str_value.endswith(search_value)
            elif operator == ">" or operator == "größer":
                try:
                    match = float(str_value) > float(search_value)
                except:
                    match = False
            elif operator == "<" or operator == "kleiner":
                try:
                    match = float(str_value) < float(search_value)
                except:
                    match = False
            elif operator == ">=" or operator == "größer gleich":
                try:
                    match = float(str_value) >= float(search_value)
                except:
                    match = False
            elif operator == "<=" or operator == "kleiner gleich":
                try:
                    match = float(str_value) <= float(search_value)
                except:
                    match = False
            elif operator == "!=" or operator == "ungleich":
                match = search_value != str_value
            else:
                logger.warning(f"⚠️ Unbekannter Operator: {operator}")
                return False
            
            # Negation anwenden?
            if is_negated:
                return not match
            else:
                return match
        
        return filter_func


# Singleton Instance
_parser_instance = None

def get_search_string_parser() -> SearchStringParser:
    """Singleton-Accessor für Parser"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = SearchStringParser()
    return _parser_instance
