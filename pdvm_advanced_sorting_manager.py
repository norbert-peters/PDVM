#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDVM Erweiterter Sorting Manager - Multi-Level mit Gruppierung
============================================================

Erweitert den bestehenden Sorting Manager um:
1. Multi-Level Sortierung 
2. Gruppierung mit konfigurierbaren Optionen
3. Tabellen-Integration für gruppierte Darstellung
4. Persistierung von erweiterten Sortier-Konfigurationen
"""

import logging
from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

logger = logging.getLogger(__name__)


class PdvmAdvancedSortingManager:
    """Erweiterter Sorting Manager für Multi-Level Sortierung und Gruppierung"""
    
    def __init__(self, base_manager=None):
        """
        Initialisiert den erweiterten Sorting Manager
        
        Args:
            base_manager: Bestehender Sorting Manager für Kompatibilität
        """
        self.base_manager = base_manager
        self.current_engine = None
        self.current_group_config = None
        self.original_data = []
        self.current_table = None
        
    def apply_advanced_sorting(self, engine, group_config) -> bool:
        """
        Wendet erweiterte Sortierung mit der gegebenen Engine an
        
        Args:
            engine: PdvmAdvancedSortingEngine Instanz
            group_config: GroupConfig für Gruppierung
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        try:
            self.current_engine = engine
            self.current_group_config = group_config
            
            logger.info("🚀 Starte erweiterte Sortierung...")
            logger.info(f"📊 Konfiguration: {len(engine.sort_levels)} Ebenen, Gruppierung: {group_config.enabled}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei erweiterter Sortierung: {e}")
            return False
    
    def apply_to_table(self, table: QTableWidget, data: List[Dict]) -> bool:
        """
        Wendet erweiterte Sortierung auf eine QTableWidget an
        STRATEGIE: Verwende Table-Items statt rohe Daten für konsistente Sortierung
        
        Args:
            table: Ziel-Tabelle
            data: Ursprungsdaten (wird ignoriert - verwende Table-Items)
            
        Returns:
            bool: True bei Erfolg
        """
        try:
            if not self.current_engine:
                logger.warning("⚠️ Keine Sortierungs-Engine verfügbar")
                return False
            
            self.current_table = table
            self.original_data = data.copy()
            
            # NEUE STRATEGIE: Extrahiere Daten aus der Tabelle (bereits formatiert)
            table_data = self._extract_data_from_table(table)
            
            if not table_data:
                logger.warning("⚠️ Keine Daten aus Tabelle extrahiert")
                return False
            
            # Daten mit Engine verarbeiten (jetzt alle Strings - kein Typ-Konflikt)
            processed_data = self.current_engine.process_data(table_data)
            
            # Tabelle mit verarbeiteten Daten füllen
            self._populate_table_with_grouped_data(table, processed_data)
            
            logger.info(f"✅ Tabelle mit {len(processed_data)} Zeilen (gruppiert) aktualisiert")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anwenden auf Tabelle: {e}")
            return False
    
    def _extract_data_from_table(self, table: QTableWidget) -> List[Dict]:
        """
        Extrahiert Daten aus QTableWidget - ALLE WERTE SIND BEREITS STRINGS
        Das löst das Typ-Problem, da QTableWidgetItems immer als Strings vorliegen
        
        Args:
            table: QTableWidget Instanz
            
        Returns:
            List[Dict]: Extrahierte Daten (alle Werte als Strings)
        """
        try:
            data = []
            
            if table.rowCount() == 0 or table.columnCount() == 0:
                return data
            
            # Spalten-Namen aus Header extrahieren
            column_names = []
            for col in range(table.columnCount()):
                header_item = table.horizontalHeaderItem(col)
                if header_item:
                    # Multi-line Header berücksichtigen
                    column_name = header_item.text().split('\n')[0]
                    column_names.append(column_name)
                else:
                    column_names.append(f"col_{col}")
            
            # Zeilen extrahieren
            for row in range(table.rowCount()):
                row_data = {}
                
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    column_name = column_names[col]
                    
                    if item:
                        # QTableWidgetItem.text() gibt IMMER einen String zurück
                        row_data[column_name] = item.text()
                    else:
                        row_data[column_name] = ""
                
                data.append(row_data)
            
            logger.debug(f"🔍 Extrahiert {len(data)} Zeilen aus Tabelle (alle Strings)")
            return data
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Extrahieren der Tabellen-Daten: {e}")
            return []
    
    def _populate_table_with_grouped_data(self, table: QTableWidget, data: List[Dict]):
        """Füllt Tabelle mit gruppierten Daten und spezieller Formatierung"""
        try:
            if not data:
                table.setRowCount(0)
                return
            
            # Tabellen-Größe setzen
            table.setRowCount(len(data))
            
            # Erste Zeile für Spalten-Namen verwenden (ignoriere Meta-Spalten)
            data_columns = [key for key in data[0].keys() if not key.startswith('_pdvm_')]
            if table.columnCount() == 0:
                table.setColumnCount(len(data_columns))
                table.setHorizontalHeaderLabels(data_columns)
            
            # Zeilen füllen
            for row_idx, row_data in enumerate(data):
                row_type = row_data.get('_pdvm_row_type', 'normal')
                
                for col_idx, column in enumerate(data_columns):
                    value = row_data.get(column, "")
                    item = QTableWidgetItem(str(value))
                    
                    # Spezielle Formatierung je nach Zeilen-Typ
                    if row_type == 'group_header':
                        self._format_group_header_item(item, row_data)
                    elif row_type == 'group_sum':
                        self._format_group_sum_item(item, row_data)
                    else:
                        self._format_normal_item(item, row_data)
                    
                    table.setItem(row_idx, col_idx, item)
            
            # Spalten-Breite anpassen
            table.resizeColumnsToContents()
            
            logger.debug(f"📋 Tabelle gefüllt: {len(data)} Zeilen, {len(data_columns)} Spalten")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Füllen der Tabelle: {e}")
            raise
    
    def _format_group_header_item(self, item: QTableWidgetItem, row_data: Dict):
        """Formatiert Gruppen-Header Items"""
        # Font-Größe aus GCS holen (zentral definiert)
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            if gcs and hasattr(gcs, 'group_font_size'):
                group_size = gcs.group_font_size
            else:
                group_size = 10  # Fallback = 9pt Basis + 1pt
        except:
            group_size = 10  # Fallback bei Import-Fehler
        
        # Fett und größer
        font = QFont()
        font.setBold(True)
        font.setPointSize(group_size)
        item.setFont(font)
        
        # Hintergrundfarbe
        item.setBackground(QColor(230, 240, 250))  # Hellblau
        
        # Nicht editierbar
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        
        # Tooltip mit Gruppen-Info
        count = row_data.get('_pdvm_group_count', 0)
        item.setToolTip(f"Gruppe: {count} Einträge")
    
    def _format_group_sum_item(self, item: QTableWidgetItem, row_data: Dict):
        """Formatiert Gruppen-Summen Items"""
        # Kursiv
        font = QFont()
        font.setItalic(True)
        font.setBold(True)
        item.setFont(font)
        
        # Hintergrundfarbe
        item.setBackground(QColor(250, 250, 230))  # Hellgelb
        
        # Nicht editierbar
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        
        # Tooltip
        item.setToolTip("Gruppen-Summe")
    
    def _format_normal_item(self, item: QTableWidgetItem, row_data: Dict):
        """Formatiert normale Daten-Items"""
        # Standard-Formatierung
        item.setFlags(item.flags() | Qt.ItemIsEditable)
    
    def clear_advanced_sorting(self, table: QTableWidget) -> bool:
        """Entfernt erweiterte Sortierung und stellt ursprüngliche Daten wieder her"""
        try:
            if self.original_data and table:
                # Ursprüngliche Daten ohne Gruppierung wiederherstellen
                self._populate_table_with_original_data(table, self.original_data)
                
                # State zurücksetzen
                self.current_engine = None
                self.current_group_config = None
                
                logger.info("✅ Erweiterte Sortierung entfernt")
                return True
            else:
                logger.warning("⚠️ Keine ursprünglichen Daten zum Wiederherstellen verfügbar")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Entfernen der erweiterten Sortierung: {e}")
            return False
    
    def _populate_table_with_original_data(self, table: QTableWidget, data: List[Dict]):
        """Füllt Tabelle mit ursprünglichen Daten ohne Gruppierung"""
        try:
            if not data:
                table.setRowCount(0)
                return
            
            # Tabellen-Größe setzen
            table.setRowCount(len(data))
            
            # Spalten setzen
            data_columns = list(data[0].keys())
            if table.columnCount() == 0:
                table.setColumnCount(len(data_columns))
                table.setHorizontalHeaderLabels(data_columns)
            
            # Zeilen mit Standard-Formatierung füllen
            for row_idx, row_data in enumerate(data):
                for col_idx, column in enumerate(data_columns):
                    value = row_data.get(column, "")
                    item = QTableWidgetItem(str(value))
                    
                    # Standard-Formatierung
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                    
                    table.setItem(row_idx, col_idx, item)
            
            # Spalten-Breite anpassen
            table.resizeColumnsToContents()
            
            logger.debug(f"📋 Ursprüngliche Daten wiederhergestellt: {len(data)} Zeilen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Wiederherstellen ursprünglicher Daten: {e}")
            raise
    
    def get_group_statistics(self) -> Dict[str, Any]:
        """Gibt aktuelle Gruppen-Statistiken zurück"""
        if self.current_engine:
            return self.current_engine.get_group_statistics()
        return {}
    
    def is_grouped_sorting_active(self) -> bool:
        """Prüft ob gruppierte Sortierung aktiv ist"""
        return (self.current_engine is not None and 
                self.current_group_config is not None and 
                self.current_group_config.enabled)
    
    def get_current_configuration(self) -> Dict[str, Any]:
        """Gibt aktuelle Sortier-Konfiguration zurück"""
        if not self.current_engine or not self.current_group_config:
            return {}
        
        return {
            'sort_levels': [(level.column_key, level.direction, level.display_name) 
                          for level in self.current_engine.sort_levels],
            'grouping': {
                'enabled': self.current_group_config.enabled,
                'show_sums': self.current_group_config.show_sums,
                'collapsible': self.current_group_config.collapsible,
                'sum_columns': self.current_group_config.sum_columns
            }
        }


def create_enhanced_sorting_manager(base_manager=None):
    """Factory-Funktion für erweiterten Sorting Manager"""
    return PdvmAdvancedSortingManager(base_manager)


def main():
    """Test der erweiterten Sorting Manager Funktionalität"""
    logger.info("🧪 Teste erweiterten Sorting Manager...")
    
    # Test-Daten
    test_data = [
        {'Name': 'Alice', 'Abteilung': 'IT', 'Gehalt': 50000, 'Alter': 30},
        {'Name': 'Bob', 'Abteilung': 'Sales', 'Gehalt': 45000, 'Alter': 25},
        {'Name': 'Charlie', 'Abteilung': 'IT', 'Gehalt': 60000, 'Alter': 35},
        {'Name': 'Diana', 'Abteilung': 'Sales', 'Gehalt': 48000, 'Alter': 28},
    ]
    
    # Manager erstellen
    manager = create_enhanced_sorting_manager()
    
    # Engine konfigurieren
    from pdvm_advanced_sorting_engine import PdvmAdvancedSortingEngine, GroupConfig
    
    engine = PdvmAdvancedSortingEngine()
    group_config = GroupConfig(enabled=True, show_sums=True, sum_columns=['Gehalt'])
    
    sort_levels = [
        ('Abteilung', 'asc', 'Abteilung'),
        ('Gehalt', 'desc', 'Gehalt')
    ]
    
    engine.set_sort_configuration(sort_levels, group_config)
    
    # Anwenden
    success = manager.apply_advanced_sorting(engine, group_config)
    print(f"📊 Erweiterte Sortierung erfolgreich: {success}")
    
    # Statistiken
    stats = manager.get_group_statistics()
    print(f"📈 Statistiken: {stats}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()