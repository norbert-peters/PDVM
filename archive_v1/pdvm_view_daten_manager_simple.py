#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDVM View Daten Manager - EINFACHE LÖSUNG
==========================================

KONSEQUENT VEREINFACHT:
- Keine komplexen Controls Manager
- Keine Provider-Chains  
- Direkte Spalten-Logik
- display_* Felder werden beim Tabellenaufbau erstellt
- Speichern direkt in Systemsteuerung
"""

import logging
from typing import List, Dict, Tuple, Any

logger = logging.getLogger(__name__)

class PdvmViewDatenManager:
    """
    EINFACHER Daten Manager - nur die Essentials
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
        
        logger.info(f"🔧 EINFACHER DatenManager gestartet - View: {self.view_guid}")
        
        # Daten laden
        self._load_data()
    
    def _load_data(self):
        """
        EINFACH: Daten laden und display_* Felder sofort aufbauen
        """
        try:
            logger.info("📥 Lade Basisdaten - EINFACHE LÖSUNG")
            
            # Provider für Rohdaten verwenden
            from pdvm_value_view_provider import PdvmValueViewProvider
            
            provider = PdvmValueViewProvider(db_name="PdvmManager.db")
            
            # View-Config laden (vereinfacht)
            view_config = self._get_simple_view_config()
            
            # Daten für aktuellen Mode laden
            controls, data = provider.get_value_view(
                view_config=view_config,
                stichtag=self.stichtag,
                mode=self.current_view_mode,
                user_guid=self.user_guid
            )
            
            # Basis-Daten setzen
            self.basis_data = data or []
            
            # WICHTIG: display_* Felder SOFORT beim Tabellenaufbau erstellen
            self.basis_columns = self._build_columns_with_display_fields(controls)
            
            logger.info(f"✅ Daten geladen: {len(self.basis_data)} Zeilen, {len(self.basis_columns)} Spalten")
            logger.info(f"🔧 display_* Felder automatisch aufgebaut")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Daten: {e}")
            self.basis_data = []
            self.basis_columns = []
    
    def _get_simple_view_config(self):
        """EINFACH: View-Config laden"""
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            
            view_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="viewdaten", 
                guid=self.view_guid
            )
            
            config = view_db.lesen()
            return config or {"view_guid": self.view_guid}
            
        except Exception as e:
            logger.warning(f"⚠️ View-Config Fallback: {e}")
            return {"view_guid": self.view_guid}
    
    def _build_columns_with_display_fields(self, controls):
        """
        KERNPUNKT: display_* Felder beim Tabellenaufbau erstellen
        Genau wie Sie sagten - hier werden sie aufgebaut!
        """
        try:
            if not controls or not hasattr(controls, 'columns'):
                logger.warning("⚠️ Keine Controls zum Aufbauen der display_* Felder")
                return []
            
            columns = []
            
            for i, col in enumerate(controls.columns):
                # Basis-Spalte kopieren
                column = col.copy()
                
                # display_* Felder HIER beim Tabellenaufbau erstellen
                column['display_show'] = col.get('show', True)
                column['display_order'] = col.get('order', i + 1)
                column['display_expert'] = col.get('expert', False)
                
                columns.append(column)
            
            # Nach display_order sortieren
            columns.sort(key=lambda x: x.get('display_order', 999))
            
            logger.info(f"🔧 {len(columns)} Spalten mit display_* Feldern aufgebaut")
            return columns
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aufbau der display_* Felder: {e}")
            return []
    
    # ========================================
    # EINFACHE API für Dialog
    # ========================================
    
    def get_columns_for_mode(self, mode):
        """
        EINFACH: Bereits aufgebaute Spalten mit display_* Feldern zurückgeben
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
        EINFACH: Spalten direkt in Systemsteuerung speichern und Tabelle neu aufbauen
        """
        try:
            logger.info(f"💾 Speichere {len(columns)} Spalten - EINFACHE LÖSUNG")
            
            # SCHRITT 1: In Systemsteuerung speichern
            success = self._save_to_systemsteuerung(columns, mode)
            
            if success:
                # SCHRITT 2: Daten neu laden (damit display_* neu aufgebaut wird)
                self._load_data()
                
                # SCHRITT 3: Widget-Tabelle neu aufbauen
                if self.widget and hasattr(self.widget, 'load_data'):
                    self.widget.load_data()
                
                logger.info("✅ Spalten gespeichert und Tabelle neu aufgebaut")
                return True
            else:
                logger.error("❌ Speichern fehlgeschlagen")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
            return False
    
    def _save_to_systemsteuerung(self, columns, mode):
        """EINFACH: Direkt in Systemsteuerung speichern"""
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
            
            # Speichern unter view_guid Gruppe
            success = sys_db.set_value(
                gruppe=self.view_guid,
                feld=f"columns_{mode}",
                wert=config
            )
            
            if success:
                logger.info(f"💾 Spalten-Config in Systemsteuerung gespeichert")
                return True
            else:
                logger.error("❌ Systemsteuerung-Speichern fehlgeschlagen")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Systemsteuerung-Speichern: {e}")
            return False
    
    # ========================================
    # EINFACHE Tabellen-API
    # ========================================
    
    def get_table_data(self):
        """EINFACH: Tabellendaten zurückgeben"""
        return self.basis_data, self.basis_columns
    
    def switch_view_mode(self, new_mode):
        """EINFACH: Mode wechseln"""
        if new_mode != self.current_view_mode:
            self.current_view_mode = new_mode
            self._load_data()
            return True
        return False
    
    def is_expert_mode(self):
        """Kompatibilität"""
        return self.current_view_mode == "expert"
