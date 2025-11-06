#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDVM Datenbank-Struktur Setup für flexible Multi-Tab-Architektur
Erstellt und verwaltet die neuen Strukturen in der Datenbank
"""

import os
import sys
import logging
import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

# Logger Setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class PdvmDatabaseStructureSetup:
    """Setup-Klasse für die Datenbank-Strukturen"""
    
    # Standard-GUIDs für Templates
    INPUTCONTROL_TEMPLATE_GUID = "11111111-1111-1111-1111-111111111111"
    FRAME_TEMPLATE_GUID = "22222222-2222-2222-2222-222222222222"
    
    def __init__(self, db_path: str = "PdvmManager.db"):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Verbindung zur Datenbank herstellen"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Ermöglicht Zugriff per Spaltenname
            logger.info(f"✅ Verbindung zur Datenbank {self.db_path} hergestellt")
            return True
        except Exception as e:
            logger.error(f"❌ Fehler beim Verbinden zur Datenbank: {e}")
            return False
    
    def disconnect(self):
        """Verbindung zur Datenbank schließen"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("🔌 Datenbank-Verbindung geschlossen")
    
    def create_flexible_frame_structure_tables(self):
        """Erstellt die neuen Tabellen für flexible Frame-Strukturen"""
        
        if not self.conn:
            logger.error("❌ Keine Datenbank-Verbindung")
            return False
        
        try:
            cursor = self.conn.cursor()
            
            # 1. Erweiterte framedaten-Tabelle (bestehende erweitern)
            logger.info("🔹 Prüfe framedaten-Tabelle...")
            
            # Prüfen ob neue Spalten bereits existieren
            cursor.execute("PRAGMA table_info(framedaten)")
            columns = [row[1] for row in cursor.fetchall()]
            
            new_columns = [
                ("structure_version", "TEXT DEFAULT '2.0'"),
                ("structure_type", "TEXT DEFAULT 'flexible_multi_tab'"),
                ("tab_definitions", "TEXT"),  # JSON für Tab-Definitionen
                ("group_definitions", "TEXT"),  # JSON für Gruppen-Definitionen
                ("mode_configurations", "TEXT"),  # JSON für Modi-Konfigurationen
                ("layout_settings", "TEXT"),  # JSON für Layout-Einstellungen
                ("created_at", "TEXT"),
                ("modified_at", "TEXT"),
                ("created_by", "TEXT"),
                ("template_source", "TEXT")  # Referenz auf Template-GUID
            ]
            
            for col_name, col_def in new_columns:
                if col_name not in columns:
                    cursor.execute(f"ALTER TABLE framedaten ADD COLUMN {col_name} {col_def}")
                    logger.info(f"✅ Spalte {col_name} zu framedaten hinzugefügt")
            
            # 2. Neue Tabelle für InputControl-Templates
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inputcontrol_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_guid TEXT UNIQUE NOT NULL,
                    template_name TEXT NOT NULL,
                    template_description TEXT,
                    field_definitions TEXT,  -- JSON für Feld-Definitionen
                    control_settings TEXT,   -- JSON für Control-Einstellungen
                    validation_rules TEXT,   -- JSON für Validierungsregeln
                    access_control TEXT,     -- JSON für Zugriffs-Steuerung
                    created_at TEXT,
                    modified_at TEXT,
                    created_by TEXT,
                    version TEXT DEFAULT '1.0',
                    is_active INTEGER DEFAULT 1
                )
            """)
            logger.info("✅ Tabelle inputcontrol_templates erstellt/geprüft")
            
            # 3. Neue Tabelle für Frame-Templates
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS frame_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_guid TEXT UNIQUE NOT NULL,
                    template_name TEXT NOT NULL,
                    template_description TEXT,
                    base_structure TEXT,     -- JSON für Basis-Struktur
                    default_tabs TEXT,       -- JSON für Standard-Tabs
                    default_groups TEXT,     -- JSON für Standard-Gruppen
                    default_modes TEXT,      -- JSON für Standard-Modi
                    usage_context TEXT,      -- Verwendungskontext (datenpflege, frame_pflege, etc.)
                    created_at TEXT,
                    modified_at TEXT,
                    created_by TEXT,
                    version TEXT DEFAULT '1.0',
                    is_active INTEGER DEFAULT 1
                )
            """)
            logger.info("✅ Tabelle frame_templates erstellt/geprüft")
            
            # 4. Neue Tabelle für Tab-Definitionen (normalisiert)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tab_definitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tab_guid TEXT UNIQUE NOT NULL,
                    frame_guid TEXT NOT NULL,
                    tab_id TEXT NOT NULL,
                    tab_name TEXT NOT NULL,
                    tab_type TEXT DEFAULT 'inputframe',
                    tab_order INTEGER DEFAULT 100,
                    tab_icon TEXT,
                    assigned_groups TEXT,    -- JSON Array der Gruppen-IDs
                    primary_group TEXT,
                    visible INTEGER DEFAULT 1,
                    enabled INTEGER DEFAULT 1,
                    start_tab INTEGER DEFAULT 0,
                    view_guid TEXT,
                    tab_grouping_style TEXT DEFAULT 'sections',
                    scrollable INTEGER DEFAULT 1,
                    max_height INTEGER,
                    columns INTEGER DEFAULT 1,
                    visible_modes TEXT,      -- JSON Array der Modi
                    auto_save INTEGER DEFAULT 1,
                    confirm_changes INTEGER DEFAULT 1,
                    read_only INTEGER DEFAULT 0,
                    created_at TEXT,
                    version TEXT DEFAULT '1.0'
                )
            """)
            logger.info("✅ Tabelle tab_definitions erstellt/geprüft")
            
            # 5. Neue Tabelle für Gruppen-Definitionen (normalisiert)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_definitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_guid TEXT UNIQUE NOT NULL,
                    frame_guid TEXT NOT NULL,
                    group_id TEXT NOT NULL,
                    group_name TEXT NOT NULL,
                    group_description TEXT,
                    group_icon TEXT,
                    parent_group_id TEXT,
                    sub_groups TEXT,         -- JSON Array der Untergruppen-IDs
                    grouping_style TEXT DEFAULT 'sections',
                    sort_order INTEGER DEFAULT 100,
                    collapsible INTEGER DEFAULT 0,
                    initially_collapsed INTEGER DEFAULT 0,
                    field_types TEXT,        -- JSON Array der Feldtypen
                    field_count_estimate INTEGER DEFAULT 0,
                    visible INTEGER DEFAULT 1,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT,
                    version TEXT DEFAULT '1.0'
                )
            """)
            logger.info("✅ Tabelle group_definitions erstellt/geprüft")
            
            # Änderungen committen
            self.conn.commit()
            logger.info("✅ Alle Tabellen-Strukturen erfolgreich erstellt/aktualisiert")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der Tabellen-Strukturen: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def create_inputcontrol_template(self) -> bool:
        """Erstellt das InputControl-Template unter GUID 1111..."""
        
        if not self.conn:
            logger.error("❌ Keine Datenbank-Verbindung")
            return False
        
        try:
            cursor = self.conn.cursor()
            
            # InputControl-Template-Daten
            template_data = {
                "template_guid": self.INPUTCONTROL_TEMPLATE_GUID,
                "template_name": "Standard InputControl Template",
                "template_description": "Basis-Template für alle InputControl-Definitionen",
                "field_definitions": json.dumps({
                    "standard_fields": {
                        "text_field": {
                            "type": "text",
                            "validation": {"required": False, "max_length": 255},
                            "display": {"width": 200, "placeholder": "Text eingeben..."}
                        },
                        "dropdown_field": {
                            "type": "dropdown",
                            "validation": {"required": False},
                            "display": {"width": 150, "empty_text": "Bitte wählen..."}
                        },
                        "datetime_field": {
                            "type": "datetime",
                            "validation": {"required": False, "min_date": None, "max_date": None},
                            "display": {"format": "dd.MM.yyyy", "show_time": False}
                        },
                        "number_field": {
                            "type": "number",
                            "validation": {"required": False, "min_value": None, "max_value": None},
                            "display": {"decimals": 2, "thousand_separator": True}
                        },
                        "boolean_field": {
                            "type": "boolean",
                            "validation": {"required": False},
                            "display": {"style": "checkbox", "text": "Aktiviert"}
                        }
                    }
                }),
                "control_settings": json.dumps({
                    "default_width": 200,
                    "default_height": 25,
                    "label_width": 120,
                    "spacing": 5,
                    "group_spacing": 15,
                    "use_icons": True,
                    "show_help": True,
                    "show_history": True,
                    "auto_save": True
                }),
                "validation_rules": json.dumps({
                    "global_rules": {
                        "required_fields_check": True,
                        "data_type_validation": True,
                        "custom_validation": True
                    },
                    "field_level_rules": {
                        "length_validation": True,
                        "format_validation": True,
                        "range_validation": True
                    }
                }),
                "access_control": json.dumps({
                    "field_level_rights": {
                        "visible": True,
                        "readonly": True,
                        "required": True
                    },
                    "group_level_rights": {
                        "visible": True,
                        "enabled": True,
                        "collapsible": True
                    },
                    "frame_level_rights": {
                        "access": True,
                        "edit": True,
                        "delete": True
                    }
                }),
                "created_at": datetime.now().isoformat(),
                "modified_at": datetime.now().isoformat(),
                "created_by": "SYSTEM",
                "version": "1.0",
                "is_active": 1
            }
            
            # Prüfen ob Template bereits existiert
            cursor.execute("SELECT template_guid FROM inputcontrol_templates WHERE template_guid = ?", 
                         (self.INPUTCONTROL_TEMPLATE_GUID,))
            
            if cursor.fetchone():
                # Update
                cursor.execute("""
                    UPDATE inputcontrol_templates 
                    SET template_name = ?, template_description = ?, field_definitions = ?,
                        control_settings = ?, validation_rules = ?, access_control = ?,
                        modified_at = ?, version = ?
                    WHERE template_guid = ?
                """, (
                    template_data["template_name"],
                    template_data["template_description"],
                    template_data["field_definitions"],
                    template_data["control_settings"],
                    template_data["validation_rules"],
                    template_data["access_control"],
                    template_data["modified_at"],
                    template_data["version"],
                    self.INPUTCONTROL_TEMPLATE_GUID
                ))
                logger.info("✅ InputControl-Template aktualisiert")
            else:
                # Insert
                cursor.execute("""
                    INSERT INTO inputcontrol_templates 
                    (template_guid, template_name, template_description, field_definitions,
                     control_settings, validation_rules, access_control, created_at, 
                     modified_at, created_by, version, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    template_data["template_guid"],
                    template_data["template_name"],
                    template_data["template_description"],
                    template_data["field_definitions"],
                    template_data["control_settings"],
                    template_data["validation_rules"],
                    template_data["access_control"],
                    template_data["created_at"],
                    template_data["modified_at"],
                    template_data["created_by"],
                    template_data["version"],
                    template_data["is_active"]
                ))
                logger.info("✅ InputControl-Template erstellt")
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des InputControl-Templates: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def create_frame_template(self) -> bool:
        """Erstellt das Frame-Template unter GUID 2222..."""
        
        if not self.conn:
            logger.error("❌ Keine Datenbank-Verbindung")
            return False
        
        try:
            cursor = self.conn.cursor()
            
            # Frame-Template-Daten
            template_data = {
                "template_guid": self.FRAME_TEMPLATE_GUID,
                "template_name": "Standard Frame Template",
                "template_description": "Basis-Template für neue Frame-Strukturen",
                "base_structure": json.dumps({
                    "frame_version": "2.0",
                    "structure_type": "flexible_multi_tab",
                    "default_dialog_size": {"width": 1200, "height": 800},
                    "default_grouping_style": "sections",
                    "supports_multi_tabs": True,
                    "supports_hierarchical_groups": True
                }),
                "default_tabs": json.dumps([
                    {
                        "tab_id": "view_tab",
                        "tab_name": "Ansicht",
                        "tab_type": "view",
                        "tab_order": 1,
                        "tab_icon": "👁️",
                        "start_tab": True,
                        "visible_modes": [0, 1, 2, 3, 4, 5]
                    },
                    {
                        "tab_id": "edit_tab",
                        "tab_name": "Bearbeiten",
                        "tab_type": "inputframe",
                        "tab_order": 2,
                        "tab_icon": "📝",
                        "assigned_groups": ["main_group"],
                        "visible_modes": [0, 1, 2, 3, 4, 5]
                    }
                ]),
                "default_groups": json.dumps([
                    {
                        "group_id": "main_group",
                        "group_name": "Hauptdaten",
                        "group_description": "Haupt-Datengruppe",
                        "group_icon": "📋",
                        "grouping_style": "sections",
                        "sort_order": 10,
                        "field_types": ["text", "dropdown", "datetime"],
                        "field_count_estimate": 5
                    }
                ]),
                "default_modes": json.dumps([
                    {
                        "mode_id": 0,
                        "mode_name": "Datenpflege",
                        "mode_icon": "📝",
                        "mode_tabs": ["view_tab", "edit_tab"],
                        "default_start_tab": "view_tab"
                    }
                ]),
                "usage_context": "universal",
                "created_at": datetime.now().isoformat(),
                "modified_at": datetime.now().isoformat(),
                "created_by": "SYSTEM",
                "version": "1.0",
                "is_active": 1
            }
            
            # Prüfen ob Template bereits existiert
            cursor.execute("SELECT template_guid FROM frame_templates WHERE template_guid = ?", 
                         (self.FRAME_TEMPLATE_GUID,))
            
            if cursor.fetchone():
                # Update
                cursor.execute("""
                    UPDATE frame_templates 
                    SET template_name = ?, template_description = ?, base_structure = ?,
                        default_tabs = ?, default_groups = ?, default_modes = ?,
                        usage_context = ?, modified_at = ?, version = ?
                    WHERE template_guid = ?
                """, (
                    template_data["template_name"],
                    template_data["template_description"],
                    template_data["base_structure"],
                    template_data["default_tabs"],
                    template_data["default_groups"],
                    template_data["default_modes"],
                    template_data["usage_context"],
                    template_data["modified_at"],
                    template_data["version"],
                    self.FRAME_TEMPLATE_GUID
                ))
                logger.info("✅ Frame-Template aktualisiert")
            else:
                # Insert
                cursor.execute("""
                    INSERT INTO frame_templates 
                    (template_guid, template_name, template_description, base_structure,
                     default_tabs, default_groups, default_modes, usage_context,
                     created_at, modified_at, created_by, version, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    template_data["template_guid"],
                    template_data["template_name"],
                    template_data["template_description"],
                    template_data["base_structure"],
                    template_data["default_tabs"],
                    template_data["default_groups"],
                    template_data["default_modes"],
                    template_data["usage_context"],
                    template_data["created_at"],
                    template_data["modified_at"],
                    template_data["created_by"],
                    template_data["version"],
                    template_data["is_active"]
                ))
                logger.info("✅ Frame-Template erstellt")
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des Frame-Templates: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def migrate_existing_framedaten(self) -> bool:
        """Migriert bestehende framedaten auf neue Struktur"""
        
        if not self.conn:
            logger.error("❌ Keine Datenbank-Verbindung")
            return False
        
        try:
            cursor = self.conn.cursor()
            
            # Alle bestehenden framedaten laden
            cursor.execute("""
                SELECT guid, ROOT, METADATEN 
                FROM framedaten 
                WHERE structure_version IS NULL OR structure_version != '2.0'
            """)
            
            existing_frames = cursor.fetchall()
            logger.info(f"🔹 Gefunden: {len(existing_frames)} Frame(s) zum Migrieren")
            
            for frame in existing_frames:
                frame_guid = frame['guid']
                root_data = json.loads(frame['ROOT']) if frame['ROOT'] else {}
                metadata = json.loads(frame['METADATEN']) if frame['METADATEN'] else {}
                
                logger.info(f"🔄 Migriere Frame {frame_guid}")
                
                # Flexible Struktur aus bestehenden Daten erstellen
                flexible_structure = self.create_flexible_structure_from_existing(
                    frame_guid, root_data, metadata
                )
                
                # Frame-Daten aktualisieren
                cursor.execute("""
                    UPDATE framedaten 
                    SET structure_version = ?, structure_type = ?, 
                        tab_definitions = ?, group_definitions = ?, 
                        mode_configurations = ?, layout_settings = ?,
                        modified_at = ?, template_source = ?
                    WHERE guid = ?
                """, (
                    "2.0",
                    "flexible_multi_tab",
                    json.dumps(flexible_structure["tabs"]),
                    json.dumps(flexible_structure["groups"]),
                    json.dumps(flexible_structure["modes"]),
                    json.dumps(flexible_structure["layout"]),
                    datetime.now().isoformat(),
                    self.FRAME_TEMPLATE_GUID,
                    frame_guid
                ))
                
                logger.info(f"✅ Frame {frame_guid} erfolgreich migriert")
            
            self.conn.commit()
            logger.info(f"✅ {len(existing_frames)} Frame(s) erfolgreich migriert")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei der Migration: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def create_flexible_structure_from_existing(self, frame_guid: str, root_data: Dict, metadata: Dict) -> Dict:
        """Erstellt flexible Struktur aus bestehenden Daten"""
        
        # Standard-Tabs basierend auf bestehenden Daten
        tabs = [
            {
                "tab_id": "view_tab",
                "tab_name": "Ansicht",
                "tab_type": "view",
                "tab_order": 1,
                "tab_icon": "👁️",
                "start_tab": True,
                "visible_modes": [0, 1, 2, 3, 4, 5],
                "assigned_groups": []
            },
            {
                "tab_id": "main_edit_tab",
                "tab_name": "Daten bearbeiten",
                "tab_type": "inputframe",
                "tab_order": 2,
                "tab_icon": "📝",
                "assigned_groups": ["main_data_group"],
                "visible_modes": [0],
                "tab_grouping_style": "sections",
                "columns": 1
            }
        ]
        
        # Gruppen aus Metadaten ableiten
        groups = []
        field_count = len(metadata.keys()) if metadata else 0
        
        if field_count > 0:
            # Hauptgruppe für alle Felder
            groups.append({
                "group_id": "main_data_group",
                "group_name": "Hauptdaten",
                "group_description": f"Alle Datenfelder ({field_count} Felder)",
                "group_icon": "📋",
                "grouping_style": "sections",
                "sort_order": 10,
                "field_types": ["text", "dropdown", "datetime"],
                "field_count_estimate": field_count,
                "visible": True,
                "enabled": True
            })
        
        # Modi-Konfiguration
        modes = [
            {
                "mode_id": 0,
                "mode_name": "Datenpflege",
                "mode_icon": "📝",
                "mode_tabs": ["view_tab", "main_edit_tab"],
                "default_start_tab": "view_tab",
                "tab_organization": "horizontal"
            }
        ]
        
        # Layout-Einstellungen
        layout = {
            "dialog_width": 1000,
            "dialog_height": 700,
            "dialog_resizable": True,
            "default_grouping_style": "sections",
            "auto_save": True,
            "confirm_changes": True
        }
        
        return {
            "tabs": tabs,
            "groups": groups,
            "modes": modes,
            "layout": layout
        }
    
    def setup_complete_database_structure(self) -> bool:
        """Führt das komplette Datenbank-Setup durch"""
        
        logger.info("🚀 Starte komplettes Datenbank-Setup...")
        
        if not self.connect():
            return False
        
        try:
            # 1. Tabellen-Strukturen erstellen
            if not self.create_flexible_frame_structure_tables():
                return False
            
            # 2. InputControl-Template erstellen
            if not self.create_inputcontrol_template():
                return False
            
            # 3. Frame-Template erstellen
            if not self.create_frame_template():
                return False
            
            # 4. Bestehende Daten migrieren
            if not self.migrate_existing_framedaten():
                return False
            
            logger.info("✅ Komplettes Datenbank-Setup erfolgreich abgeschlossen")
            return True
            
        finally:
            self.disconnect()
    
    def get_setup_info(self) -> Dict[str, Any]:
        """Gibt Informationen über das Setup zurück"""
        
        info = {
            "database_path": self.db_path,
            "inputcontrol_template_guid": self.INPUTCONTROL_TEMPLATE_GUID,
            "frame_template_guid": self.FRAME_TEMPLATE_GUID,
            "new_tables": [
                "inputcontrol_templates",
                "frame_templates", 
                "tab_definitions",
                "group_definitions"
            ],
            "extended_tables": [
                "framedaten (neue Spalten für flexible Struktur)"
            ],
            "setup_steps": [
                "1. Tabellen-Strukturen erstellen/erweitern",
                "2. InputControl-Template (1111...) erstellen",
                "3. Frame-Template (2222...) erstellen", 
                "4. Bestehende framedaten migrieren"
            ]
        }
        
        return info


def demo_database_setup():
    """Demonstriert das Datenbank-Setup"""
    
    print("=== PDVM Datenbank-Struktur Setup Demo ===")
    
    setup = PdvmDatabaseStructureSetup()
    
    # Setup-Informationen anzeigen
    info = setup.get_setup_info()
    print(f"\n📋 Setup-Informationen:")
    print(f"   Datenbank: {info['database_path']}")
    print(f"   InputControl-Template GUID: {info['inputcontrol_template_guid']}")
    print(f"   Frame-Template GUID: {info['frame_template_guid']}")
    
    print(f"\n📊 Neue Tabellen:")
    for table in info['new_tables']:
        print(f"   • {table}")
    
    print(f"\n🔧 Erweiterte Tabellen:")
    for table in info['extended_tables']:
        print(f"   • {table}")
    
    print(f"\n🚀 Setup-Schritte:")
    for step in info['setup_steps']:
        print(f"   {step}")
    
    # Setup durchführen
    print(f"\n🔄 Führe Setup durch...")
    if setup.setup_complete_database_structure():
        print("✅ Setup erfolgreich abgeschlossen!")
    else:
        print("❌ Setup fehlgeschlagen!")
    
    print("\n=== Demo abgeschlossen ===")


if __name__ == "__main__":
    demo_database_setup()
