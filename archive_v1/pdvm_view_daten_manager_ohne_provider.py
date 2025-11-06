#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDVM View Daten Manager - FINAL EINFACHE LÖSUNG
===============================================

OHNE PROVIDER - Direkte Datenbank-Kommunikation
- Keine Provider-Chains
- Keine Controls Manager
- Direkte DB → display_* → Dialog → DB
"""

import logging
from typing import List, Dict, Tuple, Any

logger = logging.getLogger(__name__)

class PdvmViewDatenManager:
    """
    FINAL EINFACHER Daten Manager
    Direkte DB-Kommunikation ohne Provider-Umwege
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
        
        # EINFACHE Datenstrukturen
        self.basis_data = []
        self.basis_columns = []  # Spalten mit display_* Feldern
        
        logger.info(f"🔧 FINAL EINFACHER DatenManager gestartet - View: {self.view_guid}")
        
        # Daten laden
        self._load_data()
    
    def _load_data(self):
        """
        DIREKTE DB-Kommunikation: Spalten und Daten laden, display_* sofort aufbauen
        """
        try:
            logger.info("📥 Lade Daten direkt aus Datenbank - OHNE PROVIDER")
            
            # SCHRITT 1: Spalten-Definition aus Datenbank laden
            columns = self._load_columns_from_db()
            
            # SCHRITT 2: Tabellen-Daten aus Datenbank laden  
            self.basis_data = self._load_data_from_db()
            
            # SCHRITT 3: WICHTIG - display_* Felder SOFORT beim Tabellenaufbau erstellen
            self.basis_columns = self._build_columns_with_display_fields(columns)
            
            logger.info(f"✅ Direkt geladen: {len(self.basis_data)} Zeilen, {len(self.basis_columns)} Spalten")
            logger.info(f"🔧 display_* Felder automatisch aufgebaut - OHNE PROVIDER")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim direkten DB-Laden: {e}")
            # Fallback auf Demo-Daten
            self._load_demo_data()
    
    def _load_columns_from_db(self):
        """
        DIREKT: Spalten-Definition aus viewdaten-Tabelle laden
        """
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            
            # View-Datenbank öffnen
            view_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="viewdaten",
                guid=self.view_guid
            )
            
            # View-Config laden
            view_config = view_db.lesen()
            
            if view_config and 'columns' in view_config:
                # Echte Spalten-Definition aus DB
                logger.info(f"📋 Spalten aus viewdaten geladen: {len(view_config['columns'])}")
                return view_config['columns']
            else:
                # Fallback: Standard-Spalten
                logger.info("📋 Fallback auf Standard-Spalten")
                return self._get_fallback_columns()
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Spalten-DB-Zugriff: {e}")
            return self._get_fallback_columns()
    
    def _load_data_from_db(self):
        """
        DIREKT: Tabellen-Daten aus der entsprechenden Datentabelle laden
        """
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            
            # Für Demo: persondaten als Beispiel
            data_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="persondaten",  # Anpassbar je nach view_guid
                guid=None  # Alle Datensätze
            )
            
            # Alle Datensätze laden
            all_data = data_db.alle_lesen()
            
            if all_data:
                logger.info(f"📊 Tabellen-Daten aus persondaten geladen: {len(all_data)} Datensätze")
                return list(all_data.values())  # Dict-Values zu Liste
            else:
                logger.info("📊 Keine DB-Daten gefunden - verwende Demo-Daten")
                return self._get_demo_data()
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Daten-DB-Zugriff: {e}")
            return self._get_demo_data()
    
    def _get_fallback_columns(self):
        """Standard-Spalten als Fallback"""
        return [
            {"name": "FAMILIENNAME", "label": "Familienname", "show": True, "order": 1, "expert": False},
            {"name": "VORNAME", "label": "Vorname", "show": True, "order": 2, "expert": False},
            {"name": "UID_SHOW", "label": "UID Show", "show": True, "order": 3, "expert": False},
            {"name": "GEBURTSDATUM", "label": "Geburtsdatum", "show": False, "order": 4, "expert": False},
        ]
    
    def _get_demo_data(self):
        """Demo-Daten als Fallback"""
        return [
            {"FAMILIENNAME": "Müller", "VORNAME": "Anna", "UID_SHOW": "uid123", "GEBURTSDATUM": "1985-03-15"},
            {"FAMILIENNAME": "Schmidt", "VORNAME": "Peter", "UID_SHOW": "uid456", "GEBURTSDATUM": "1990-07-22"},
            {"FAMILIENNAME": "Weber", "VORNAME": "Lisa", "UID_SHOW": "uid789", "GEBURTSDATUM": "1988-11-03"},
        ]
    
    def _load_demo_data(self):
        """Fallback: Demo-Daten laden"""
        logger.info("📥 Fallback auf Demo-Daten")
        columns = self._get_fallback_columns()
        self.basis_data = self._get_demo_data()
        self.basis_columns = self._build_columns_with_display_fields(columns)
    
    def _build_columns_with_display_fields(self, raw_columns):
        """
        KERNPUNKT: display_* Felder beim Tabellenaufbau erstellen
        Genau hier wie Sie es wollten!
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
            
            logger.info(f"🔧 {len(columns)} Spalten mit display_* aufgebaut (Mode: {self.current_view_mode})")
            return columns
            
        except Exception as e:
            logger.error(f"❌ Fehler beim display_* Aufbau: {e}")
            return []
    
    # ========================================
    # EINFACHE API für Dialog (bleibt gleich)
    # ========================================
    
    def get_columns_for_mode(self, mode):
        """
        DIREKT: display_* Felder sind schon beim Tabellenaufbau erstellt
        """
        try:
            # Mode wechseln falls nötig
            if mode != self.current_view_mode:
                self.current_view_mode = mode
                self._load_data()  # Neu laden für anderen Mode
            
            logger.info(f"📋 {len(self.basis_columns)} Spalten für Mode '{mode}' (display_* schon da)")
            return self.basis_columns.copy()
            
        except Exception as e:
            logger.error(f"❌ Fehler bei get_columns_for_mode: {e}")
            return []
    
    def save_columns_from_dialog(self, columns, mode):
        """
        DIREKT: Spalten direkt in Systemsteuerung speichern - OHNE PROVIDER
        """
        try:
            logger.info(f"💾 Speichere {len(columns)} Spalten DIREKT - OHNE PROVIDER")
            
            # DIREKT in systemsteuerung speichern
            success = self._save_to_systemsteuerung_direct(columns, mode)
            
            if success:
                # Daten neu laden (damit display_* neu aufgebaut wird)
                self._load_data()
                
                # Widget-Tabelle neu aufbauen
                if self.widget and hasattr(self.widget, 'load_data'):
                    logger.info("🔄 Aktualisiere Widget-Tabelle...")
                    self.widget.load_data()
                
                logger.info("✅ DIREKT gespeichert und Tabelle neu aufgebaut")
                return True
            else:
                logger.error("❌ Direktes Speichern fehlgeschlagen")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler beim direkten Speichern: {e}")
            return False
    
    def _save_to_systemsteuerung_direct(self, columns, mode):
        """DIREKT in Systemsteuerung speichern - OHNE PROVIDER-UMWEGE"""
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            
            # Systemsteuerung für User
            sys_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="systemsteuerung",
                guid=self.user_guid
            )
            
            # Spalten-Konfiguration vorbereiten
            config = {
                "mode": mode,
                "columns": []
            }
            
            for col in columns:
                config["columns"].append({
                    "name": col.get("name"),
                    "show": col.get("display_show", True),
                    "order": col.get("display_order", 999),
                    "expert": col.get("display_expert", False)
                })
            
            # DIREKT speichern unter view_guid Gruppe
            success = sys_db.set_value(
                gruppe=self.view_guid,
                feld=f"columns_{mode}",
                wert=config
            )
            
            if success:
                logger.info(f"💾 DIREKT in Systemsteuerung gespeichert")
                return True
            else:
                logger.error("❌ Direktes Systemsteuerung-Speichern fehlgeschlagen")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler beim direkten Systemsteuerung-Speichern: {e}")
            return False
    
    # ========================================
    # EINFACHE Tabellen-API (bleibt gleich)
    # ========================================
    
    def get_table_data(self):
        """DIREKT: Tabellendaten zurückgeben"""
        return self.basis_data, self.basis_columns
    
    def switch_view_mode(self, new_mode):
        """DIREKT: Mode wechseln"""
        if new_mode != self.current_view_mode:
            self.current_view_mode = new_mode
            self._load_data()
            return True
        return False
    
    def is_expert_mode(self):
        """Kompatibilität"""
        return self.current_view_mode == "expert"
