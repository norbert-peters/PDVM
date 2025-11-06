#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDVM Erweiterte Sortierungs-Engine - Multi-Level mit Gruppierung
==============================================================

Implementiert:
1. Multi-Level Sortierung (mehrere Spalten gleichzeitig)
2. Gruppierung mit konfigurierbaren Optionen
3. Interne Sortierung innerhalb von Gruppen
4. Gruppen-Statistiken und Summen
5. Kollabierbare Gruppen-Darstellung
"""

import logging
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class SortLevel:
    """Definiert eine Sortier-Ebene"""
    column_key: str
    direction: str  # 'asc' oder 'desc'
    display_name: str
    is_group_level: bool = False  # Ob diese Ebene für Gruppierung verwendet wird


@dataclass
class GroupConfig:
    """Konfiguration für Gruppierung"""
    enabled: bool = False
    show_sums: bool = False
    collapsible: bool = False
    sum_columns: List[str] = None  # Spalten für Summen-Berechnung
    
    def __post_init__(self):
        if self.sum_columns is None:
            self.sum_columns = []


@dataclass
class GroupData:
    """Daten einer Gruppe"""
    key: Any  # Gruppierung-Schlüssel
    display_value: str  # Anzeige-Wert der Gruppe
    rows: List[Dict] = None  # Zeilen in dieser Gruppe
    sums: Dict[str, float] = None  # Summen pro Spalte
    count: int = 0
    
    def __post_init__(self):
        if self.rows is None:
            self.rows = []
        if self.sums is None:
            self.sums = {}


class PdvmAdvancedSortingEngine:
    """Erweiterte Sortierungs-Engine mit Multi-Level und Gruppierung"""
    
    def __init__(self):
        self.sort_levels: List[SortLevel] = []
        self.group_config: GroupConfig = GroupConfig()
        self.original_data: List[Dict] = []
        self.processed_data: List[Dict] = []
        self.group_data: Dict[Any, GroupData] = {}
        
    def set_sort_configuration(self, sort_levels: List[Tuple[str, str, str]], 
                             group_config: GroupConfig = None):
        """Setzt die Sortier-Konfiguration"""
        try:
            self.sort_levels = []
            
            # Konvertiere Tupel zu SortLevel-Objekten
            for i, (column_key, direction, display_name) in enumerate(sort_levels):
                # Erste Ebene ist Gruppierung, wenn Gruppierung aktiviert
                is_group_level = (i == 0 and group_config and group_config.enabled)
                
                sort_level = SortLevel(
                    column_key=column_key,
                    direction=direction,
                    display_name=display_name,
                    is_group_level=is_group_level
                )
                self.sort_levels.append(sort_level)
            
            # Gruppierung-Konfiguration setzen
            if group_config:
                self.group_config = group_config
            else:
                self.group_config = GroupConfig()
                
            logger.info(f"📊 Sortier-Konfiguration gesetzt: {len(self.sort_levels)} Ebenen")
            if self.group_config.enabled:
                logger.info(f"🏷️ Gruppierung aktiviert nach: {self.sort_levels[0].display_name}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Setzen der Sortier-Konfiguration: {e}")
            raise
    
    def process_data(self, data: List[Dict]) -> List[Dict]:
        """Verarbeitet Daten mit Multi-Level Sortierung und Gruppierung"""
        try:
            self.original_data = data.copy()
            
            if not self.sort_levels:
                logger.info("ℹ️ Keine Sortierung konfiguriert - ursprüngliche Reihenfolge")
                return data
            
            if self.group_config.enabled and self.sort_levels:
                # Gruppierte Sortierung
                return self._process_grouped_data(data)
            else:
                # Standard Multi-Level Sortierung
                return self._process_standard_sorting(data)
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Datenverarbeitung: {e}")
            raise
    
    def _process_standard_sorting(self, data: List[Dict]) -> List[Dict]:
        """Standard Multi-Level Sortierung ohne Gruppierung"""
        try:
            sorted_data = data.copy()
            
            # Sortiere nach allen Ebenen (reverse order für korrekte Priorität)
            for sort_level in reversed(self.sort_levels):
                reverse_order = (sort_level.direction == 'desc')
                
                sorted_data.sort(
                    key=lambda x: self._get_sort_key(x, sort_level.column_key),
                    reverse=reverse_order
                )
                
                logger.debug(f"🔄 Sortiert nach {sort_level.display_name} ({sort_level.direction})")
            
            self.processed_data = sorted_data
            logger.info(f"✅ Multi-Level Sortierung abgeschlossen: {len(sorted_data)} Zeilen")
            
            return sorted_data
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Standard-Sortierung: {e}")
            raise
    
    def _process_grouped_data(self, data: List[Dict]) -> List[Dict]:
        """Gruppierte Sortierung mit interner Sortierung"""
        try:
            if not self.sort_levels:
                return data
            
            # Erste Ebene = Gruppierung-Spalte
            group_level = self.sort_levels[0]
            internal_levels = self.sort_levels[1:] if len(self.sort_levels) > 1 else []
            
            # Schritt 1: Daten nach Gruppierung-Spalte gruppieren
            groups = self._create_groups(data, group_level.column_key)
            
            # Schritt 2: Interne Sortierung in jeder Gruppe
            for group_key, group_data in groups.items():
                if internal_levels:
                    # Sortiere innerhalb der Gruppe nach den restlichen Ebenen
                    for sort_level in reversed(internal_levels):
                        reverse_order = (sort_level.direction == 'desc')
                        group_data.rows.sort(
                            key=lambda x: self._get_sort_key(x, sort_level.column_key),
                            reverse=reverse_order
                        )
                
                # Gruppen-Statistiken berechnen
                if self.group_config.show_sums:
                    group_data.sums = self._calculate_group_sums(group_data.rows)
                
                group_data.count = len(group_data.rows)
            
            # Schritt 3: Gruppen sortieren (die keys sind bereits sortierbar)
            sorted_group_keys = sorted(
                groups.keys(),
                reverse=(group_level.direction == 'desc')
            )
            
            # Schritt 4: Zusammenfügen mit Gruppen-Headers
            result_data = []
            self.group_data = groups
            
            for group_key in sorted_group_keys:
                group_data = groups[group_key]
                
                # Gruppen-Header einfügen
                if self.group_config.enabled:
                    header_row = self._create_group_header(group_key, group_data)
                    result_data.append(header_row)
                
                # Gruppen-Zeilen einfügen
                result_data.extend(group_data.rows)
                
                # Gruppen-Summen einfügen (optional)
                if self.group_config.show_sums and group_data.sums:
                    sum_row = self._create_group_sum_row(group_data)
                    result_data.append(sum_row)
            
            self.processed_data = result_data
            logger.info(f"✅ Gruppierte Sortierung abgeschlossen: {len(sorted_group_keys)} Gruppen, {len(result_data)} Zeilen total")
            
            return result_data
            
        except Exception as e:
            logger.error(f"❌ Fehler bei gruppierter Sortierung: {e}")
            raise
    
    def _create_groups(self, data: List[Dict], group_column: str) -> Dict[Any, GroupData]:
        """Erstellt Gruppen basierend auf einer Spalte"""
        groups = {}
        
        for row in data:
            # Verwende den sortierbaren Key für Gruppierung
            sort_key = self._get_sort_key(row, group_column)
            original_value = row.get(group_column, "")
            
            if sort_key not in groups:
                groups[sort_key] = GroupData(
                    key=sort_key,
                    display_value=str(original_value) if original_value is not None else "(Leer)",
                    rows=[]
                )
            
            groups[sort_key].rows.append(row)
        
        logger.debug(f"📊 {len(groups)} Gruppen erstellt nach Spalte '{group_column}'")
        return groups
    
    def _calculate_group_sums(self, rows: List[Dict]) -> Dict[str, float]:
        """Berechnet Summen für numerische Spalten in einer Gruppe"""
        sums = {}
        
        if not self.group_config.sum_columns:
            return sums
        
        for column in self.group_config.sum_columns:
            total = 0.0
            count = 0
            
            for row in rows:
                value = row.get(column, 0)
                try:
                    numeric_value = float(value) if value is not None else 0.0
                    total += numeric_value
                    count += 1
                except (ValueError, TypeError):
                    continue  # Nicht-numerische Werte ignorieren
            
            sums[column] = total
        
        return sums
    
    def _create_group_header(self, group_key: Any, group_data: GroupData) -> Dict:
        """Erstellt eine Gruppen-Header Zeile"""
        header_row = {
            '_pdvm_row_type': 'group_header',
            '_pdvm_group_key': group_key,
            '_pdvm_group_display': group_data.display_value,
            '_pdvm_group_count': group_data.count,
            '_pdvm_collapsible': self.group_config.collapsible
        }
        
        # Erste Spalte mit Gruppen-Info
        for key in self.original_data[0].keys() if self.original_data else []:
            if key == list(self.original_data[0].keys())[0]:  # Erste Spalte
                header_row[key] = f"🏷️ {group_data.display_value} ({group_data.count} Einträge)"
            else:
                header_row[key] = ""
        
        return header_row
    
    def _create_group_sum_row(self, group_data: GroupData) -> Dict:
        """Erstellt eine Gruppen-Summen Zeile"""
        sum_row = {
            '_pdvm_row_type': 'group_sum',
            '_pdvm_group_key': group_data.key
        }
        
        # Summen in entsprechende Spalten einfügen
        for key in self.original_data[0].keys() if self.original_data else []:
            if key in group_data.sums:
                sum_row[key] = f"Σ {group_data.sums[key]:.2f}"
            elif key == list(self.original_data[0].keys())[0]:  # Erste Spalte
                sum_row[key] = "📊 Summe:"
            else:
                sum_row[key] = ""
        
        return sum_row
    
    def _get_sort_key(self, row: Dict, column_key: str) -> Any:
        """Erstellt Sortier-Schlüssel für eine Zeile - ROBUST für gemischte Datentypen"""
        value = row.get(column_key, None)
        
        # Debug: Typ des eingehenden Wertes loggen
        logger.debug(f"🔍 Sort Key für '{column_key}': Wert='{value}' (Typ: {type(value)})")
        
        # Behandle None/leere Werte konsistent
        if value is None:
            return ""  # Leere Strings sortieren zuerst
        
        # Konvertiere zu String für konsistente Vergleiche
        str_value = str(value).strip()
        
        if not str_value:
            return ""  # Leere Strings sortieren zuerst
        
        # Versuche numerische Sortierung für Zahlen
        try:
            # Prüfe ob es eine reine Zahl ist
            if str_value.replace('.', '').replace('-', '').isdigit():
                return (0, float(str_value))  # Tuple: (type_priority, value) - Zahlen sortieren vor Text
        except (ValueError, TypeError):
            pass
        
        # String-Sortierung für alle anderen Werte
        return (1, str_value.lower())  # Tuple: (type_priority, value) - Text sortiert nach Zahlen
    
    def get_group_statistics(self) -> Dict[str, Any]:
        """Gibt Gruppen-Statistiken zurück"""
        if not self.group_data:
            return {}
        
        stats = {
            'total_groups': len(self.group_data),
            'total_rows': len(self.original_data),
            'groups': {}
        }
        
        for group_key, group_data in self.group_data.items():
            stats['groups'][group_key] = {
                'count': group_data.count,
                'display_value': group_data.display_value,
                'sums': group_data.sums
            }
        
        return stats
    
    def is_grouped(self) -> bool:
        """Gibt zurück, ob die Daten gruppiert sind"""
        return self.group_config.enabled and len(self.sort_levels) > 0 and self.sort_levels[0].is_group_level


def main():
    """Beispiel-Verwendung der erweiterten Sortierungs-Engine"""
    logger.info("🧪 Teste erweiterte Sortierungs-Engine...")
    
    # Test-Daten
    test_data = [
        {'name': 'Alice', 'department': 'IT', 'salary': 50000, 'age': 30},
        {'name': 'Bob', 'department': 'Sales', 'salary': 45000, 'age': 25},
        {'name': 'Charlie', 'department': 'IT', 'salary': 60000, 'age': 35},
        {'name': 'Diana', 'department': 'Sales', 'salary': 48000, 'age': 28},
        {'name': 'Eve', 'department': 'IT', 'salary': 55000, 'age': 32},
    ]
    
    # Engine erstellen
    engine = PdvmAdvancedSortingEngine()
    
    # Gruppierung konfigurieren
    group_config = GroupConfig(
        enabled=True,
        show_sums=True,
        collapsible=True,
        sum_columns=['salary']
    )
    
    # Sortierung: Gruppiert nach Department, intern nach Salary (absteigend)
    sort_levels = [
        ('department', 'asc', 'Abteilung'),
        ('salary', 'desc', 'Gehalt'),
        ('name', 'asc', 'Name')
    ]
    
    engine.set_sort_configuration(sort_levels, group_config)
    
    # Daten verarbeiten
    result = engine.process_data(test_data)
    
    # Ergebnis anzeigen
    print("\n📊 Sortierungs-Ergebnis:")
    for i, row in enumerate(result):
        print(f"{i+1:2d}: {row}")
    
    # Statistiken
    stats = engine.get_group_statistics()
    print(f"\n📈 Statistiken: {stats}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()