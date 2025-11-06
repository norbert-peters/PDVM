#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PdvmSpaltenManager - Vereinfachte Tabellen-Darstellung
======================================================

KONZEPT:
- ColumnControl-Objekte enthalten Spalten + Daten
- Display-Mapping projiziert Controls → Tabelle
- Gekapselte, schrittweise Lösung
- Linear: Control → Mapping → Tabelle

ARCHITEKTUR:
1. SCHRITT: Basis-Mapping erstellen  
2. SCHRITT: Spalten-Header generieren
3. SCHRITT: Daten-Zeilen generieren  
4. SCHRITT: Komplette Tabelle zurückgeben
"""

import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class PdvmSpaltenManager:
    """
    Vereinfachter Manager für Tabellen-Darstellung
    
    Wandelt ColumnControl-Daten in einfache Tabellen-Struktur um:
    - Spalten-Header (mit Anzeige-Namen)
    - Daten-Zeilen (formatiert für Widget)
    - Einheitliche, lineare Logik
    """
    
    def __init__(self, column_control):
        """
        Initialisiert den SpaltenManager mit einem ColumnControl
        
        Args:
            column_control: Das ColumnControl-Objekt mit Spalten + Daten
        """
        self.column_control = column_control
        self.display_mapping = []
        
        logger.info(f"🔧 PdvmSpaltenManager initialisiert mit {len(column_control.columns)} Spalten")
    
    # ================================================================
    # SCHRITT 1: BASIS-MAPPING ERSTELLEN
    # ================================================================
    
    def create_display_mapping(self, show_only: bool = True, mode: str = "normal") -> List[Dict]:
        """
        SCHRITT 1: Erstellt Display-Mapping aus ColumnControl
        
        Definiert welche Spalten wie dargestellt werden:
        - show_only: Nur Spalten mit show=True
        - mode: normal/expert (später für Erweiterung)
        
        Returns:
            List[Dict]: Display-Mapping mit Spalten-Konfiguration
        """
        self.display_mapping = []
        
        logger.info(f"🔧 SCHRITT 1: Erstelle Display-Mapping (show_only={show_only}, mode={mode})")
        
        for col in self.column_control.columns:
            col_name = col['name']
            col_show = col.get('show', False)
            col_anzeige = col.get('anzeige', col_name)
            col_type = col.get('type', 'unknown')
            
            # Filter-Logik: show_only oder alle
            if show_only and not col_show:
                continue
            
            # Mapping-Eintrag erstellen
            mapping_entry = {
                'col_name': col_name,
                'header': col_anzeige,
                'type': col_type,
                'show': col_show,
                'order': col.get('order', 999)
            }
            
            self.display_mapping.append(mapping_entry)
        
        # Nach Order sortieren
        self.display_mapping.sort(key=lambda x: x['order'])
        
        logger.info(f"   ✅ {len(self.display_mapping)} Spalten im Display-Mapping")
        
        return self.display_mapping
    
    # ================================================================
    # SCHRITT 2: SPALTEN-HEADER GENERIEREN
    # ================================================================
    
    def get_table_headers(self) -> List[str]:
        """
        SCHRITT 2: Generiert Spalten-Header für Tabelle
        
        Returns:
            List[str]: Header-Namen für die Tabelle
        """
        if not self.display_mapping:
            self.create_display_mapping()
        
        headers = [mapping['header'] for mapping in self.display_mapping]
        
        logger.info(f"🔧 SCHRITT 2: {len(headers)} Spalten-Header generiert")
        logger.debug(f"   Headers: {headers}")
        
        return headers
    
    # ================================================================
    # SCHRITT 3: DATEN-ZEILEN GENERIEREN
    # ================================================================
    
    def get_table_rows(self) -> List[List[Any]]:
        """
        SCHRITT 3: Generiert Daten-Zeilen für Tabelle
        
        Returns:
            List[List[Any]]: Zeilen-Daten (jede Zeile ist Liste von Werten)
        """
        if not self.display_mapping:
            self.create_display_mapping()
        
        logger.info(f"🔧 SCHRITT 3: Generiere Daten-Zeilen")
        
        rows = []
        col_names = [mapping['col_name'] for mapping in self.display_mapping]
        
        # Für jeden Datensatz (GUID) eine Zeile erstellen
        for guid in self.column_control.row_guids:
            row_data = self.column_control.get_row_data(guid)
            
            # Zeile basierend auf Display-Mapping erstellen
            row = []
            for col_name in col_names:
                value = row_data.get(col_name, '')
                # Wert formatieren (falls nötig)
                formatted_value = self._format_cell_value(value)
                row.append(formatted_value)
            
            rows.append(row)
        
        logger.info(f"   ✅ {len(rows)} Daten-Zeilen generiert")
        
        return rows
    
    def _format_cell_value(self, value: Any) -> str:
        """
        Hilfsmethode: Formatiert einen Zell-Wert für die Anzeige
        
        Args:
            value: Roh-Wert aus den Daten
            
        Returns:
            str: Formatierter Wert für Tabellen-Anzeige
        """
        if value is None:
            return ""
        
        if isinstance(value, str):
            return value
        
        # Zahlen und andere Typen als String
        return str(value)
    
    # ================================================================
    # SCHRITT 4: KOMPLETTE TABELLE ZURÜCKGEBEN  
    # ================================================================
    
    def get_complete_table(self, show_only: bool = True, mode: str = "normal") -> Dict[str, Any]:
        """
        SCHRITT 4: Liefert komplette Tabelle in einheitlichem Format
        
        Args:
            show_only: Nur Spalten mit show=True anzeigen
            mode: Display-Mode (normal/expert) - WIRD ERSTMAL IGNORIERT für Vereinfachung
            
        Returns:
            Dict: Komplette Tabellen-Struktur
            {
                'headers': List[str],           # Spalten-Header
                'rows': List[List[Any]],        # Daten-Zeilen  
                'column_count': int,            # Anzahl Spalten
                'row_count': int,               # Anzahl Zeilen
                'mapping': List[Dict]           # Display-Mapping (für Debugging)
            }
        """
        logger.info(f"🎯 SCHRITT 4: Generiere komplette Tabelle (show_only={show_only}) - MODE IGNORIERT")
        
        # Schritt 1: Mapping erstellen
        self.create_display_mapping(show_only=show_only, mode=mode)
        
        # Schritt 2: Header generieren  
        headers = self.get_table_headers()
        
        # Schritt 3: Zeilen generieren
        rows = self.get_table_rows()
        
        # Schritt 4: Komplette Struktur zusammenbauen
        table = {
            'headers': headers,
            'rows': rows,
            'column_count': len(headers),
            'row_count': len(rows),
            'mapping': self.display_mapping,
            'meta': {
                'show_only': show_only,
                'mode': mode,
                'mode_ignored': True,  # Für Vereinfachung
                'source': 'PdvmSpaltenManager'
            }
        }
        
        logger.info(f"   ✅ TABELLE KOMPLETT: {table['column_count']} Spalten × {table['row_count']} Zeilen")
        
        return table
    
    # ================================================================
    # WIDGET-INTEGRATION
    # ================================================================
    
    def get_widget_ready_table(self) -> Tuple[List[List[Any]], List[str]]:
        """
        Widget-freundliche Methode - liefert Daten im gewohnten Format
        
        Returns:
            Tuple[List[List[Any]], List[str]]: (rows, headers) wie gewohnt
        """
        table = self.get_complete_table(show_only=True)
        
        # Format: (rows, headers) - wie das Widget es erwartet
        rows_as_dicts = []
        headers = table['headers']
        
        # Konvertiere Listen-Zeilen in Dict-Format (falls Widget das braucht)
        for row in table['rows']:
            row_dict = {}
            for i, header in enumerate(headers):
                row_dict[header] = row[i] if i < len(row) else ''
            rows_as_dicts.append(row_dict)
        
        logger.info(f"🎯 Widget-Tabelle bereit: {len(rows_as_dicts)} Zeilen × {len(headers)} Spalten")
        
        return rows_as_dicts, headers
    
    def get_simple_table_data(self) -> Tuple[List[Dict], List[str]]:
        """
        EINFACHE Integration - ersetzt get_table_data_for_display()
        
        Returns:
            Tuple[List[Dict], List[str]]: Gleiche Struktur wie bisherige Methode
        """
        logger.info(f"🔄 Einfache Tabellen-Integration (SpaltenManager)")
        
        return self.get_widget_ready_table()
    
    # ================================================================
    # HELPER & DEBUG METHODEN
    # ================================================================
    
    def get_table_summary(self) -> str:
        """
        Gibt eine lesbare Zusammenfassung der Tabelle zurück
        
        Returns:
            str: Tabellen-Zusammenfassung
        """
        if not self.display_mapping:
            self.create_display_mapping()
        
        headers = self.get_table_headers()
        rows = self.get_table_rows()
        
        summary = []
        summary.append(f"📊 TABELLEN-ZUSAMMENFASSUNG:")
        summary.append(f"   Spalten: {len(headers)} ({', '.join(headers)})")
        summary.append(f"   Zeilen:  {len(rows)}")
        
        if rows:
            summary.append(f"   Beispiel-Zeile: {rows[0]}")
        
        return "\n".join(summary)
    
    def debug_display_mapping(self) -> str:
        """
        Debug-Ausgabe des Display-Mappings
        
        Returns:
            str: Formatierte Debug-Info
        """
        if not self.display_mapping:
            self.create_display_mapping()
        
        debug = []
        debug.append(f"🔍 DISPLAY-MAPPING DEBUG:")
        
        for i, mapping in enumerate(self.display_mapping):
            debug.append(f"   [{i+1}] {mapping['col_name']:<20} → '{mapping['header']}' (show={mapping['show']})")
        
        return "\n".join(debug)
