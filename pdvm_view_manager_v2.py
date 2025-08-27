#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optimierter PdvmViewManager V2.0
Linearer Ablauf ohne Komplexität - basierend auf Control-Strukturen
"""

import sys
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PdvmViewManager:
    """
    Optimierter View-Manager mit linearem Ablauf:
    
    1. Initialisierung: Basistabelle + Basis_View_Control_Struktur
    2. Systemsteuerung: Display_View_Control_Struktur laden/erstellen
    3. Tabellen-Aufbau: Basierend auf Display_View_Control_Struktur
    4. Änderungen: Display_Control → Systemsteuerung → DB
    5. Expert-Modus: Expert-Spalten zu normale Spalten umwandeln
    """
    
    def __init__(
        self,
        view_guid: str,
        view_config: dict,
        central_systemsteuerung,
        db_name: str = "PdvmManager.db",
        stichtag: Optional[float] = None
    ):
        """
        Initialisiert den optimierten ViewManager.
        
        Args:
            view_guid: GUID der View
            view_config: View-Konfiguration mit metadata
            central_systemsteuerung: Zentrale Systemsteuerung-Instanz
            db_name: Datenbank-Name
            stichtag: Stichtag für Datenabfrage
        """
        self.view_guid = view_guid
        self.view_config = view_config
        self.central_systemsteuerung = central_systemsteuerung
        self.db_name = db_name
        self.stichtag = stichtag
        
        # Datenstrukturen
        self.basis_view_control = None      # Unveränderliche Basis-Struktur
        self.display_view_control = None    # Aktuelle Display-Struktur (änderbar)
        self.basistabelle = []              # Vollständige Basisdaten
        self.display_tabelle = []           # Gefilterte/sortierte Display-Daten
        
        logger.info(f"🔹 PdvmViewManager initialisiert für View: {view_guid}")
        
        # SCHRITT 1: Basistabelle und Basis-Control-Struktur erstellen
        self._initialize_basis_data()
        
        # SCHRITT 2: Display-Control-Struktur aus Systemsteuerung laden/erstellen
        self._initialize_display_control()
        
        # SCHRITT 3: Display-Tabelle erstellen
        self._build_display_table()
    
    def _initialize_basis_data(self):
        """
        SCHRITT 1: Erstellt Basistabelle und Basis_View_Control_Struktur
        """
        logger.info("🔧 SCHRITT 1: Basistabelle und Basis-Control-Struktur erstellen")
        
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            
            # View-Tabelle ermitteln
            table_name = self.view_config["ROOT"]["view_table"]
            
            # PdvmCentralDatenbank für Viewdaten erstellen
            view_db = PdvmCentralDatenbank(
                db_name=self.db_name,
                table_name=table_name,
                guid=None  # Keine spezifische GUID - wir laden alle Daten
            )
            
            # get_value_view() aufrufen → Basistabelle + Basis_View_Control_Struktur
            result = view_db.get_value_view(self.view_config, self.stichtag)
            
            if isinstance(result, tuple) and len(result) == 2:
                self.basis_view_control, self.basistabelle = result
                logger.info(f"✅ Basistabelle geladen: {len(self.basistabelle)} Datensätze")
                logger.info(f"✅ Basis-Control-Struktur: {len(self.basis_view_control.columns)} Spalten")
            else:
                # Fallback für altes Format
                self.basistabelle = result if isinstance(result, list) else []
                self.basis_view_control = None
                logger.warning("⚠️ Alte get_value_view() ohne Control-Struktur")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Basisdaten: {e}")
            self.basistabelle = []
            self.basis_view_control = None
    
    def _initialize_display_control(self):
        """
        SCHRITT 2: Display_View_Control_Struktur aus Systemsteuerung laden/erstellen
        """
        logger.info("🔧 SCHRITT 2: Display-Control-Struktur aus Systemsteuerung laden")
        
        if not self.basis_view_control:
            logger.error("❌ Keine Basis-Control-Struktur verfügbar")
            return
        
        try:
            # Versuche Display-Control aus Systemsteuerung zu laden
            display_control_data = self.central_systemsteuerung.get_value(
                gruppe=self.view_guid,
                feld="display_view_control",
                ab_zeit=None
            )
            
            if display_control_data and display_control_data.get("wert"):
                # Display-Control aus Systemsteuerung laden
                control_dict = display_control_data.get("wert")
                self.display_view_control = self._dict_to_control_structure(control_dict)
                logger.info("✅ Display-Control-Struktur aus Systemsteuerung geladen")
            else:
                # Basis-Control-Struktur als Display-Control übernehmen
                self.display_view_control = self._copy_control_structure(self.basis_view_control)
                
                # In Systemsteuerung speichern
                self._save_display_control_to_systemsteuerung()
                logger.info("✅ Display-Control-Struktur aus Basis erstellt und gespeichert")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Display-Control: {e}")
            # Fallback: Basis-Control kopieren
            self.display_view_control = self._copy_control_structure(self.basis_view_control)
    
    def _build_display_table(self):
        """
        SCHRITT 3: Display-Tabelle basierend auf Display_View_Control_Struktur erstellen
        """
        logger.info("🔧 SCHRITT 3: Display-Tabelle basierend auf Display-Control erstellen")
        
        if not self.display_view_control or not self.basistabelle:
            logger.error("❌ Keine Display-Control oder Basistabelle verfügbar")
            self.display_tabelle = []
            return
        
        try:
            # Sichtbare Spalten ermitteln
            visible_columns = []
            for col in self.display_view_control.columns:
                if col.get('show', False):
                    visible_columns.append(col['name'])
            
            # Sortierung anwenden (falls vorhanden)
            sorted_columns = sorted(
                visible_columns,
                key=lambda col_name: self._get_column_order(col_name)
            )
            
            # Display-Tabelle mit nur sichtbaren Spalten erstellen
            self.display_tabelle = []
            for row in self.basistabelle:
                display_row = {col: row.get(col, "") for col in sorted_columns}
                self.display_tabelle.append(display_row)
            
            logger.info(f"✅ Display-Tabelle erstellt: {len(self.display_tabelle)} Zeilen, {len(sorted_columns)} Spalten")
            logger.info(f"📋 Sichtbare Spalten: {sorted_columns}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der Display-Tabelle: {e}")
            self.display_tabelle = []
    
    def _get_column_order(self, column_name: str) -> int:
        """Ermittelt die Sortier-Reihenfolge einer Spalte"""
        for col in self.display_view_control.columns:
            if col['name'] == column_name:
                return col.get('order', 9999)
        return 9999
    
    def _copy_control_structure(self, source_control):
        """Erstellt eine Kopie der Control-Struktur"""
        if not source_control:
            return None
        
        # Deep Copy der Control-Struktur
        from copy import deepcopy
        return deepcopy(source_control)
    
    def _control_structure_to_dict(self, control_structure) -> dict:
        """Konvertiert Control-Struktur zu Dict für Systemsteuerung-Speicherung"""
        if not control_structure:
            return {}
        
        return {
            "columns": [dict(col) for col in control_structure.columns],
            "metadata": getattr(control_structure, 'metadata', {})
        }
    
    def _dict_to_control_structure(self, control_dict: dict):
        """Konvertiert Dict zurück zu Control-Struktur"""
        if not control_dict:
            return None
        
        try:
            from pdvm_central_datenbank import ColumnControl
            
            control = ColumnControl()
            
            # Spalten wiederherstellen
            columns_data = control_dict.get("columns", [])
            for col_data in columns_data:
                control.columns.append(col_data)
            
            # Metadaten wiederherstellen
            control.metadata = control_dict.get("metadata", {})
            
            return control
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Konvertieren von Dict zu Control-Struktur: {e}")
            return None
    
    def _save_display_control_to_systemsteuerung(self):
        """Speichert Display-Control-Struktur in Systemsteuerung"""
        try:
            control_dict = self._control_structure_to_dict(self.display_view_control)
            
            self.central_systemsteuerung.set_value(
                gruppe=self.view_guid,
                feld="display_view_control",
                wert=control_dict,
                ab_zeit=1001.0
            )
            
            self.central_systemsteuerung.save_values()
            logger.info("✅ Display-Control-Struktur in Systemsteuerung gespeichert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Display-Control: {e}")
    
    # PUBLIC API METHODS
    
    def get_display_data(self) -> List[Dict[str, Any]]:
        """Gibt die aktuelle Display-Tabelle zurück"""
        return self.display_tabelle
    
    def get_display_columns(self) -> List[str]:
        """Gibt die aktuell sichtbaren Spalten zurück"""
        if not self.display_view_control:
            return []
        
        visible_columns = []
        for col in self.display_view_control.columns:
            if col.get('show', False):
                visible_columns.append(col['name'])
        
        # Nach Order sortieren
        return sorted(visible_columns, key=lambda col: self._get_column_order(col))
    
    def set_column_visibility(self, column_name: str, visible: bool):
        """
        Setzt die Sichtbarkeit einer Spalte
        
        Args:
            column_name: Name der Spalte
            visible: True=sichtbar, False=ausgeblendet
        """
        logger.info(f"🔧 Spalten-Sichtbarkeit ändern: {column_name} → {visible}")
        
        if not self.display_view_control:
            logger.error("❌ Keine Display-Control-Struktur verfügbar")
            return
        
        # Spalte in Display-Control aktualisieren
        column_found = False
        for col in self.display_view_control.columns:
            if col['name'] == column_name:
                col['show'] = visible
                column_found = True
                break
        
        if column_found:
            # Änderungen speichern und Tabelle neu aufbauen
            self._save_display_control_to_systemsteuerung()
            self._build_display_table()
            logger.info(f"✅ Spalte {column_name} Sichtbarkeit geändert: {visible}")
        else:
            logger.error(f"❌ Spalte {column_name} nicht gefunden")
    
    def set_column_order(self, column_name: str, new_order: int):
        """
        Setzt die Reihenfolge einer Spalte
        
        Args:
            column_name: Name der Spalte
            new_order: Neue Reihenfolge-Position
        """
        logger.info(f"🔧 Spalten-Reihenfolge ändern: {column_name} → Position {new_order}")
        
        if not self.display_view_control:
            logger.error("❌ Keine Display-Control-Struktur verfügbar")
            return
        
        # Spalte in Display-Control aktualisieren
        for col in self.display_view_control.columns:
            if col['name'] == column_name:
                col['order'] = new_order
                break
        
        # Änderungen speichern und Tabelle neu aufbauen
        self._save_display_control_to_systemsteuerung()
        self._build_display_table()
        logger.info(f"✅ Spalte {column_name} Reihenfolge geändert: {new_order}")
    
    def toggle_expert_mode_column(self, column_name: str, to_normal: bool = True):
        """
        Wandelt Expert-Spalte zu normaler Spalte um oder umgekehrt
        
        Args:
            column_name: Name der Spalte
            to_normal: True=Expert zu Normal, False=Normal zu Expert
        """
        logger.info(f"🔧 Expert-Modus umschalten: {column_name} → {'Normal' if to_normal else 'Expert'}")
        
        if not self.display_view_control:
            logger.error("❌ Keine Display-Control-Struktur verfügbar")
            return
        
        # Spalte in Display-Control aktualisieren
        for col in self.display_view_control.columns:
            if col['name'] == column_name:
                if to_normal:
                    # Expert → Normal: expert=False, show=True
                    col['expert'] = False
                    col['show'] = True
                else:
                    # Normal → Expert: expert=True, show=False
                    col['expert'] = True
                    col['show'] = False
                break
        
        # Änderungen speichern und Tabelle neu aufbauen
        self._save_display_control_to_systemsteuerung()
        self._build_display_table()
        logger.info(f"✅ Expert-Modus für {column_name} umgeschaltet")
    
    def reset_to_basis(self):
        """
        RESET: Basis-Control-Struktur → Display-Control-Struktur
        """
        logger.info("🔧 RESET: Display-Control auf Basis zurücksetzen")
        
        if not self.basis_view_control:
            logger.error("❌ Keine Basis-Control-Struktur verfügbar")
            return
        
        # Basis-Control als Display-Control übernehmen
        self.display_view_control = self._copy_control_structure(self.basis_view_control)
        
        # In Systemsteuerung speichern und Tabelle neu aufbauen
        self._save_display_control_to_systemsteuerung()
        self._build_display_table()
        
        logger.info("✅ Display-Control auf Basis zurückgesetzt")
    
    def get_all_columns_info(self) -> List[Dict[str, Any]]:
        """
        Gibt Informationen über alle verfügbaren Spalten zurück
        
        Returns:
            Liste mit Spalten-Informationen (name, show, expert, order, type, etc.)
        """
        if not self.display_view_control:
            return []
        
        columns_info = []
        for col in self.display_view_control.columns:
            info = {
                'name': col['name'],
                'show': col.get('show', False),
                'expert': col.get('expert', False),
                'order': col.get('order', 0),
                'type': col.get('type', 'unknown'),
                'anzeige': col.get('anzeige', col['name']),
                'is_auto_generated': col.get('is_auto_generated', False)
            }
            columns_info.append(info)
        
        return columns_info


if __name__ == "__main__":
    # Test-Code für den optimierten ViewManager
    print("🧪 PdvmViewManager V2.0 - Optimierter linearer Ablauf")
    print("Dieser Manager implementiert den durchdachten 6-Schritte-Ablauf:")
    print("1. Basistabelle + Basis_View_Control_Struktur")
    print("2. Display_View_Control_Struktur aus Systemsteuerung")
    print("3. Display-Tabelle basierend auf Control-Struktur")
    print("4. Änderungen → Display_Control → Systemsteuerung → DB")
    print("5. Expert-Modus: Expert-Spalten ↔ Normale Spalten")
    print("6. Reset: Basis → Display → Systemsteuerung")
