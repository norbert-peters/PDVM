# sort_manager.py
"""
🎯 SORT-MANAGER: Lineare Sortierung, Gruppierung und Summierung

ARCHITEKTUR:
- Arbeitet auf Filter-Matrix (gefilterte Daten)
- Erzeugt Sort-Matrix mit Sortierung/Gruppierung
- Summiert Gruppen und Gesamtsummen
- Persistiert Sortier-Einstellungen in GCS

MATRIX-PIPELINE:
BASIS → FILTER → SORT → PROJECTION → VIEW
"""

import logging
from typing import List, Dict, Any, Tuple
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)


class SortManager:
    """
    Verwaltet Sortierung, Gruppierung und Summierung für eine View
    
    LINEARE ARCHITEKTUR:
    1. Nimmt Filter-Matrix als Input (bereits gefiltert!)
    2. Wendet Sortierung an (einfach oder erweitert)
    3. Fügt Gruppen-Zeilen und Summen-Zeilen ein
    4. Gibt Sort-Matrix zurück für Projektion
    """
    
    def __init__(self, view_guid: str):
        """
        Initialisiert Sort-Manager für eine View
        
        Args:
            view_guid: Eindeutige GUID der View für Persistierung
        """
        self.view_guid = view_guid
        self.controls_config = {}
        self.sort_config = []  # Liste von Sortier-Definitionen
        
        logger.info(f"🔧 SortManager initialisiert für View: {view_guid}")
    
    def set_controls_config(self, controls_config: Dict[str, Any]):
        """
        Setzt Controls-Konfiguration für Sortierung
        
        Args:
            controls_config: Dictionary mit Control-Definitionen
        """
        self.controls_config = controls_config
        logger.info(f"📋 Controls-Config gesetzt: {len(controls_config)} Controls")
    
    def simple_sort(self, filter_matrix: List[Dict], column_key: str, 
                   toggle_direction: bool = True) -> List[Dict]:
        """
        🎯 EINFACHE SORTIERUNG: Header-Click Sortierung
        
        Args:
            filter_matrix: Gefilterte Matrix-Daten
            column_key: Control-Key der zu sortierenden Spalte
            toggle_direction: Wenn True, wechselt Richtung bei erneutem Click
            
        Returns:
            Sortierte Matrix (Sort-Matrix)
        """
        try:
            if not filter_matrix:
                logger.warning("⚠️ Keine Daten zum Sortieren")
                return []
            
            # Control-Config für Spalte holen
            control = self.controls_config.get(column_key, {})
            
            # Prüfe ob Spalte sortierbar ist
            ui_config = control.get('ui', {})
            if not ui_config.get('sortable', False):
                logger.warning(f"⚠️ Spalte '{column_key}' ist nicht sortierbar")
                return filter_matrix
            
            # Aktuelle Sort-Direction aus Control holen
            current_direction = ui_config.get('sortDirection', 'asc')
            
            # Toggle Direction wenn gewünscht
            if toggle_direction:
                new_direction = 'desc' if current_direction == 'asc' else 'asc'
                logger.info(f"🔄 Sortier-Richtung gewechselt: {current_direction} → {new_direction}")
                
                # Persistiere neue Direction in GCS
                self._save_sort_direction(column_key, new_direction)
                current_direction = new_direction
            
            # Sortier-Spalte bestimmen: Original vs Show
            sort_by_original = ui_config.get('sortByOriginal', False)
            if sort_by_original and control.get('control_type') == 'show':
                # Sortiere nach Original-Spalte
                original_key = column_key.replace('_show', '_original')
                if original_key in self.controls_config:
                    sort_key = original_key
                    logger.info(f"🔀 Sortiere nach Original-Spalte: {sort_key}")
                else:
                    sort_key = column_key
                    logger.warning(f"⚠️ Original-Spalte nicht gefunden, verwende Show-Spalte")
            else:
                sort_key = column_key
            
            # Sortierung durchführen
            reverse_order = (current_direction == 'desc')
            
            sorted_matrix = self._sort_matrix_by_key(
                filter_matrix, 
                sort_key, 
                reverse_order,
                control.get('type', 'string')
            )
            
            logger.info(f"✅ Einfache Sortierung: {len(sorted_matrix)} Zeilen nach '{column_key}' ({current_direction})")
            return sorted_matrix
            
        except Exception as e:
            logger.error(f"❌ Fehler bei einfacher Sortierung: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return filter_matrix
    
    def advanced_sort(self, filter_matrix: List[Dict], 
                     sort_config: List[Dict],
                     sum_columns: List[str] = None) -> List[Dict]:
        """
        🎓 ERWEITERTE SORTIERUNG: Multi-Level mit Gruppierung und Summierung
        
        Args:
            filter_matrix: Gefilterte Matrix-Daten
            sort_config: Liste von Sortier-Definitionen
                [
                    {
                        'column_key': 'familienname_show',
                        'direction': 'asc',
                        'is_group': True  # Gruppierung aktiviert
                    },
                    {
                        'column_key': 'vorname_show',
                        'direction': 'asc',
                        'is_group': False
                    }
                ]
            sum_columns: Liste von Spalten für Summierung
            
        Returns:
            Sortierte Matrix mit Gruppen- und Summen-Zeilen
        """
        try:
            if not filter_matrix:
                logger.warning("⚠️ Keine Daten zum Sortieren")
                return []
            
            if not sort_config:
                logger.warning("⚠️ Keine Sortier-Konfiguration")
                return filter_matrix
            
            # Speichere Sort-Config für spätere Verwendung
            self.sort_config = sort_config
            
            # 1. Multi-Level Sortierung durchführen
            sorted_matrix = self._multi_level_sort(filter_matrix, sort_config)
            
            # 2. Gruppierung und Summierung wenn gewünscht
            if any(cfg.get('is_group', False) for cfg in sort_config):
                result_matrix = self._apply_grouping_and_sums(
                    sorted_matrix, 
                    sort_config,
                    sum_columns or []
                )
            else:
                result_matrix = sorted_matrix
            
            logger.info(f"✅ Erweiterte Sortierung: {len(result_matrix)} Zeilen (mit Gruppen/Summen)")
            return result_matrix
            
        except Exception as e:
            logger.error(f"❌ Fehler bei erweiterter Sortierung: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return filter_matrix
    
    def _sort_matrix_by_key(self, matrix: List[Dict], sort_key: str, 
                           reverse: bool, data_type: str) -> List[Dict]:
        """
        Sortiert Matrix nach einem Schlüssel mit Typ-Beachtung
        
        Args:
            matrix: Zu sortierende Matrix
            sort_key: Schlüssel für Sortierung
            reverse: Absteigende Sortierung wenn True
            data_type: Datentyp ('string', 'number', 'date', etc.)
            
        Returns:
            Sortierte Matrix
        """
        try:
            # Sortier-Funktion je nach Typ
            if data_type in ['number', 'float', 'decimal']:
                # Numerische Sortierung
                def sort_func(row):
                    value = row.get(sort_key)
                    if value is None or value == '':
                        return float('-inf') if not reverse else float('inf')
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return float('-inf') if not reverse else float('inf')
            
            elif data_type == 'date':
                # Datum-Sortierung (über Abdatum wenn verfügbar)
                abdatum_key = f"{sort_key}_abdatum"
                def sort_func(row):
                    # Versuche Abdatum zu verwenden
                    abdatum = row.get(abdatum_key)
                    if abdatum is not None:
                        try:
                            return float(abdatum)
                        except (ValueError, TypeError):
                            pass
                    
                    # Fallback: String-Sortierung
                    value = row.get(sort_key, '')
                    return str(value).lower()
            
            else:
                # String-Sortierung (case-insensitive)
                def sort_func(row):
                    value = row.get(sort_key, '')
                    if value is None:
                        return ''
                    return str(value).lower()
            
            # Sortierung durchführen
            sorted_matrix = sorted(matrix, key=sort_func, reverse=reverse)
            
            return sorted_matrix
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Matrix-Sortierung: {e}")
            return matrix
    
    def _multi_level_sort(self, matrix: List[Dict], 
                         sort_config: List[Dict]) -> List[Dict]:
        """
        Multi-Level Sortierung (mehrere Sortier-Ebenen)
        
        Args:
            matrix: Zu sortierende Matrix
            sort_config: Liste von Sortier-Definitionen
            
        Returns:
            Sortierte Matrix
        """
        try:
            # Sortierung von hinten nach vorne (letzte Ebene zuerst)
            # Python's sort ist stabil, daher funktioniert das
            result = list(matrix)
            
            for sort_def in reversed(sort_config):
                column_key = sort_def.get('column_key')
                direction = sort_def.get('direction', 'asc')
                
                # Control-Config für Typ holen
                control = self.controls_config.get(column_key, {})
                
                # sortByOriginal beachten
                ui_config = control.get('ui', {})
                sort_by_original = ui_config.get('sortByOriginal', False)
                
                if sort_by_original and control.get('control_type') == 'show':
                    original_key = column_key.replace('_show', '_original')
                    if original_key in self.controls_config:
                        sort_key = original_key
                    else:
                        sort_key = column_key
                else:
                    sort_key = column_key
                
                # Sortierung durchführen
                reverse_order = (direction == 'desc')
                data_type = control.get('type', 'string')
                
                result = self._sort_matrix_by_key(
                    result, 
                    sort_key, 
                    reverse_order,
                    data_type
                )
                
                logger.info(f"🔧 Sortier-Ebene angewandt: {column_key} ({direction})")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Multi-Level Sortierung: {e}")
            return matrix
    
    def _apply_grouping_and_sums(self, sorted_matrix: List[Dict],
                                 sort_config: List[Dict],
                                 sum_columns: List[str]) -> List[Dict]:
        """
        Fügt Gruppen-Header und Summen-Zeilen ein
        
        Args:
            sorted_matrix: Bereits sortierte Matrix
            sort_config: Sortier-Konfiguration mit Gruppen
            sum_columns: Spalten für Summierung
            
        Returns:
            Matrix mit Gruppen- und Summen-Zeilen
        """
        try:
            # Finde Gruppen-Spalten
            group_columns = [
                cfg['column_key'] for cfg in sort_config 
                if cfg.get('is_group', False)
            ]
            
            if not group_columns:
                logger.warning("⚠️ Keine Gruppen-Spalten definiert")
                return sorted_matrix
            
            logger.info(f"📊 Gruppierung nach: {group_columns}")
            logger.info(f"📊 Summierung für: {sum_columns}")
            
            result_matrix = []
            current_group_values = {}
            group_data_rows = []
            group_sums = {col: Decimal('0') for col in sum_columns}
            total_sums = {col: Decimal('0') for col in sum_columns}
            
            for row_idx, row in enumerate(sorted_matrix):
                # Prüfe ob Gruppenwechsel
                group_changed = False
                new_group_values = {}
                
                for group_col in group_columns:
                    new_value = row.get(group_col, '')
                    new_group_values[group_col] = new_value
                    
                    if current_group_values.get(group_col) != new_value:
                        group_changed = True
                        break
                
                # Bei Gruppenwechsel: Gruppen-Summe einfügen
                if group_changed and group_data_rows:
                    # Füge Gruppen-Summen-Zeile ein
                    sum_row = self._create_group_sum_row(
                        current_group_values,
                        group_sums,
                        len(group_data_rows),
                        sum_columns
                    )
                    result_matrix.append(sum_row)
                    
                    # Reset für neue Gruppe
                    group_data_rows = []
                    group_sums = {col: Decimal('0') for col in sum_columns}
                
                # Aktualisiere Gruppen-Werte
                if group_changed:
                    current_group_values = new_group_values
                    
                    # Füge Gruppen-Header ein
                    header_row = self._create_group_header_row(
                        current_group_values,
                        group_columns
                    )
                    result_matrix.append(header_row)
                
                # Füge Daten-Zeile hinzu
                result_matrix.append(row)
                group_data_rows.append(row)
                
                # Aktualisiere Summen
                for col in sum_columns:
                    value = row.get(col)
                    try:
                        numeric_value = Decimal(str(value)) if value not in [None, ''] else Decimal('0')
                        group_sums[col] += numeric_value
                        total_sums[col] += numeric_value
                    except (InvalidOperation, ValueError):
                        # Nicht-numerischer Wert - zähle nur
                        pass
            
            # Letzte Gruppen-Summe einfügen
            if group_data_rows:
                sum_row = self._create_group_sum_row(
                    current_group_values,
                    group_sums,
                    len(group_data_rows),
                    sum_columns
                )
                result_matrix.append(sum_row)
            
            # Gesamtsumme einfügen
            if sum_columns and sorted_matrix:
                total_sum_row = self._create_total_sum_row(
                    total_sums,
                    len(sorted_matrix),
                    sum_columns
                )
                result_matrix.append(total_sum_row)
            
            logger.info(f"✅ Gruppierung abgeschlossen: {len(result_matrix)} Zeilen (mit Gruppen/Summen)")
            return result_matrix
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Gruppierung/Summierung: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return sorted_matrix
    
    def _create_group_header_row(self, group_values: Dict[str, Any],
                                 group_columns: List[str]) -> Dict[str, Any]:
        """
        Erstellt Gruppen-Header-Zeile
        
        Args:
            group_values: Werte der Gruppen-Spalten
            group_columns: Liste der Gruppen-Spalten
            
        Returns:
            Gruppen-Header-Zeile
        """
        # Erstelle Header-Text
        header_parts = []
        for col in group_columns:
            value = group_values.get(col, '')
            control = self.controls_config.get(col, {})
            name = control.get('name', col)
            header_parts.append(f"{name}: {value}")
        
        header_text = " | ".join(header_parts)
        
        # Erstelle Zeile mit Markierung
        header_row = {
            '_row_type': 'group_header',
            '_group_text': header_text,
            'display': True  # Immer anzeigen
        }
        
        return header_row
    
    def _create_group_sum_row(self, group_values: Dict[str, Any],
                             sums: Dict[str, Decimal],
                             count: int,
                             sum_columns: List[str]) -> Dict[str, Any]:
        """
        Erstellt Gruppen-Summen-Zeile
        
        Args:
            group_values: Werte der Gruppen-Spalten
            sums: Berechnete Summen
            count: Anzahl Zeilen in Gruppe
            sum_columns: Spalten für Summierung
            
        Returns:
            Gruppen-Summen-Zeile
        """
        sum_row = {
            '_row_type': 'group_sum',
            '_group_count': count,
            'display': True
        }
        
        # Füge Summen für jede Spalte hinzu
        for col in sum_columns:
            sum_value = sums.get(col, Decimal('0'))
            
            # Prüfe ob numerisch
            if sum_value != Decimal('0'):
                sum_row[col] = f"Σ {sum_value}"
            else:
                # Keine numerischen Werte - zeige Anzahl
                sum_row[col] = f"Anzahl: {count}"
        
        return sum_row
    
    def _create_total_sum_row(self, sums: Dict[str, Decimal],
                             count: int,
                             sum_columns: List[str]) -> Dict[str, Any]:
        """
        Erstellt Gesamtsummen-Zeile
        
        Args:
            sums: Berechnete Gesamt-Summen
            count: Gesamt-Anzahl Zeilen
            sum_columns: Spalten für Summierung
            
        Returns:
            Gesamtsummen-Zeile
        """
        total_row = {
            '_row_type': 'total_sum',
            '_total_count': count,
            'display': True
        }
        
        # Füge Gesamtsummen für jede Spalte hinzu
        for col in sum_columns:
            sum_value = sums.get(col, Decimal('0'))
            
            if sum_value != Decimal('0'):
                total_row[col] = f"GESAMT: {sum_value}"
            else:
                total_row[col] = f"GESAMT: {count} Datensätze"
        
        return total_row
    
    def _save_sort_direction(self, column_key: str, direction: str):
        """
        Persistiert Sort-Direction in GCS
        
        Args:
            column_key: Control-Key der Spalte
            direction: Neue Richtung ('asc' oder 'desc')
        """
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs:
                logger.warning("⚠️ GCS nicht verfügbar - Sort-Direction nicht persistiert")
                return
            
            # Hole aktuellen Control
            control = self.controls_config.get(column_key, {})
            
            if not control:
                logger.warning(f"⚠️ Control '{column_key}' nicht gefunden")
                return
            
            # Aktualisiere UI-Config
            if 'ui' not in control:
                control['ui'] = {}
            
            control['ui']['sortDirection'] = direction
            
            # Speichere in GCS
            gcs.set_control_value(self.view_guid, column_key, control)
            
            logger.info(f"💾 Sort-Direction persistiert: {column_key} → {direction}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Persistieren der Sort-Direction: {e}")


# Factory-Funktion für globalen Zugriff
_sort_managers = {}

def get_sort_manager(view_guid: str) -> SortManager:
    """
    Holt oder erstellt SortManager für eine View
    
    Args:
        view_guid: View-GUID
        
    Returns:
        SortManager-Instanz
    """
    if view_guid not in _sort_managers:
        _sort_managers[view_guid] = SortManager(view_guid)
        logger.info(f"🔧 Neuer SortManager erstellt für View: {view_guid}")
    
    return _sort_managers[view_guid]
