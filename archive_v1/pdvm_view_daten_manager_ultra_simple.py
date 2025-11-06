#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDVM View Daten Manager - ULTRA EINFACHE LÖSUNG
===============================================

KOMPLETT OHNE:
- Provider-Chains
- Controls Manager
- Komplexe Systemsteuerung

NUR:
- Basis-Spalten direkt aus DB
- display_* beim Tabellenaufbau
- Direkte Speicherung
"""

import logging
from typing import List, Dict, Tuple, Any

logger = logging.getLogger(__name__)

class PdvmViewDatenManager:
    """
    ULTRA EINFACHER Daten Manager
    Direkte Spalten-Logik ohne Umwege
    """
    
    def __init__(self, call_daten, widget=None):
        self.call_daten = call_daten
        self.widget = widget
        
        self.view_guid = call_daten.get("view_guid")
        self.user_guid = call_daten.get("user_guid")
        self.stichtag = call_daten.get("stichtag", 1001.0)
        self.mode = call_daten.get("mode", "user")
        
        # Aktueller View-Mode (normal/expert)
        self.current_view_mode = "normal"
        
        # ULTRA EINFACHE Datenstrukturen
        self.basis_data = []
        self.basis_columns = []  # Spalten mit display_* Feldern
        
        logger.info(f"🔧 ULTRA EINFACHER DatenManager gestartet - View: {self.view_guid}")
        
        # Daten laden
        self._load_data()
    
    def _load_data(self):
        """
        ULTRA EINFACH: Demo-Daten mit display_* Feldern sofort aufbauen
        """
        try:
            logger.info("📥 Lade Demo-Basisdaten - ULTRA EINFACHE LÖSUNG")
            
            # DEMO: Standard-Spalten definieren
            demo_columns = [
                {"name": "FAMILIENNAME", "label": "Familienname", "show": True, "order": 1, "expert": False},
                {"name": "VORNAME", "label": "Vorname", "show": True, "order": 2, "expert": False},
                {"name": "UID_SHOW", "label": "UID Show", "show": True, "order": 3, "expert": False},
                {"name": "GEBURTSDATUM", "label": "Geburtsdatum", "show": False, "order": 4, "expert": False},
                {"name": "DEBUG_INFO", "label": "Debug Info", "show": False, "order": 5, "expert": True},
            ]
            
            # DEMO: Basis-Daten
            self.basis_data = [
                {"FAMILIENNAME": "Müller", "VORNAME": "Anna", "UID_SHOW": "uid123", "GEBURTSDATUM": "1985-03-15", "DEBUG_INFO": "debug1"},
                {"FAMILIENNAME": "Schmidt", "VORNAME": "Peter", "UID_SHOW": "uid456", "GEBURTSDATUM": "1990-07-22", "DEBUG_INFO": "debug2"},
                {"FAMILIENNAME": "Weber", "VORNAME": "Lisa", "UID_SHOW": "uid789", "GEBURTSDATUM": "1988-11-03", "DEBUG_INFO": "debug3"},
            ]
            
            # WICHTIG: display_* Felder SOFORT beim Tabellenaufbau erstellen
            self.basis_columns = self._build_columns_with_display_fields(demo_columns)
            
            logger.info(f"✅ Demo-Daten geladen: {len(self.basis_data)} Zeilen, {len(self.basis_columns)} Spalten")
            logger.info(f"🔧 display_* Felder automatisch aufgebaut")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Demo-Daten: {e}")
            self.basis_data = []
            self.basis_columns = []
    
    def _build_columns_with_display_fields(self, raw_columns):
        """
        KERNPUNKT: display_* Felder beim Tabellenaufbau erstellen
        Das ist der Moment wo Sie sagten es soll passieren!
        """
        try:
            columns = []
            
            for i, col in enumerate(raw_columns):
                # Basis-Spalte kopieren
                column = col.copy()
                
                # display_* Felder HIER beim Tabellenaufbau erstellen
                column['display_show'] = col.get('show', True)
                column['display_order'] = col.get('order', i + 1)
                column['display_expert'] = col.get('expert', False)
                
                # Mode-Filter: Im Normal-Mode keine Expert-Spalten
                if self.current_view_mode == "normal" and column['display_expert']:
                    continue
                    
                columns.append(column)
            
            # Nach display_order sortieren
            columns.sort(key=lambda x: x.get('display_order', 999))
            
            logger.info(f"🔧 {len(columns)} Spalten mit display_* Feldern aufgebaut (Mode: {self.current_view_mode})")
            return columns
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aufbau der display_* Felder: {e}")
            return []
    
    # ========================================
    # ULTRA EINFACHE API für Dialog
    # ========================================
    
    def get_columns_for_mode(self, mode):
        """
        ULTRA EINFACH: Bereits aufgebaute Spalten mit display_* Feldern zurückgeben
        """
        try:
            # Mode wechseln falls nötig
            if mode != self.current_view_mode:
                self.current_view_mode = mode
                self._load_data()  # Neu laden für anderen Mode
            
            logger.info(f"📋 {len(self.basis_columns)} Spalten für Mode '{mode}' (display_* bereits vorhanden)")
            return self.basis_columns.copy()
            
        except Exception as e:
            logger.error(f"❌ Fehler bei get_columns_for_mode: {e}")
            return []
    
    def save_columns_from_dialog(self, columns, mode):
        """
        ULTRA EINFACH: Simuliere Speichern und lade Tabelle neu
        """
        try:
            logger.info(f"💾 Speichere {len(columns)} Spalten - ULTRA EINFACHE LÖSUNG")
            
            # SIMULATION: Speichern erfolgreich (später echte DB)
            logger.info("💾 Spalten erfolgreich gespeichert (simuliert)")
            
            # Daten neu laden (damit display_* neu aufgebaut wird)
            self._load_data()
            
            # Widget-Tabelle neu aufbauen
            if self.widget and hasattr(self.widget, 'load_data'):
                logger.info("🔄 Aktualisiere Widget-Tabelle...")
                self.widget.load_data()
            
            logger.info("✅ Spalten gespeichert und Tabelle neu aufgebaut")
            return True
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
            return False
    
    # ========================================
    # ULTRA EINFACHE Tabellen-API
    # ========================================
    
    def get_table_data(self):
        """ULTRA EINFACH: Tabellendaten zurückgeben"""
        return self.basis_data, self.basis_columns
    
    def switch_view_mode(self, new_mode):
        """ULTRA EINFACH: Mode wechseln"""
        if new_mode != self.current_view_mode:
            self.current_view_mode = new_mode
            self._load_data()
            return True
        return False
    
    def is_expert_mode(self):
        """Kompatibilität"""
        return self.current_view_mode == "expert"
