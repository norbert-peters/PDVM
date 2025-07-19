# -*- coding: utf-8 -*-
"""
PDVM Unified Database Structure
Einheitliche Datenhaltung mit JSON-Strukturen in standardisierten Tabellen
"""

import sqlite3
import json
import logging
import uuid
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class PdvmUnifiedDatabaseManager:
    """Einheitlicher Datenbank-Manager für alle PDVM-Tabellen"""
    
    def __init__(self, db_path: str = "PdvmManager.db"):
        self.db_path = db_path
        self.connection = None
        
        # Template-GUID-Struktur
        self.template_guids = {
            # System-Templates (0000...)
            "system_base": "00000000-0000-0000-0000-000000000000",
            
            # Frame-Templates (0000-1111...)
            "frame_basic": "00001111-1111-1111-1111-111111111111",
            "frame_datenpflege": "00001111-1111-1111-1111-111111111112", 
            "frame_settings": "00001111-1111-1111-1111-111111111113",
            "frame_admin": "00001111-1111-1111-1111-111111111114",
            
            # InputControl-Templates (0000-2222...)
            "ic_basic": "00002222-2222-2222-2222-222222222221",
            "ic_text": "00002222-2222-2222-2222-222222222222",
            "ic_number": "00002222-2222-2222-2222-222222222223",
            "ic_date": "00002222-2222-2222-2222-222222222224",
            "ic_dropdown": "00002222-2222-2222-2222-222222222225",
            
            # Dialog-Templates (0000-3333...)
            "dialog_standard": "00003333-3333-3333-3333-333333333331",
            "dialog_multi_tab": "00003333-3333-3333-3333-333333333332",
            
            # Menu-Templates (0000-4444...)
            "menu_main": "00004444-4444-4444-4444-444444444441",
            "menu_context": "00004444-4444-4444-4444-444444444442",
        }
    
    def connect(self) -> bool:
        """Verbindung zur Datenbank herstellen"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            logger.info("✅ Datenbank-Verbindung hergestellt")
            return True
        except Exception as e:
            logger.error(f"❌ Fehler bei Datenbank-Verbindung: {e}")
            return False
    
    def disconnect(self):
        """Datenbank-Verbindung schließen"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("🔌 Datenbank-Verbindung geschlossen")
    
    def create_unified_table_structure(self) -> bool:
        """Erstellt die einheitliche Tabellen-Struktur"""
        try:
            cursor = self.connection.cursor()
            
            # Standard-Tabellen-Schema
            table_schema = """
            CREATE TABLE IF NOT EXISTS {table_name} (
                uid           TEXT    PRIMARY KEY,
                daten         TEXT    NOT NULL,
                name          TEXT,
                historisch    INTEGER NOT NULL DEFAULT 0,
                last_modified TEXT    NOT NULL DEFAULT '',
                source_hash   TEXT    DEFAULT '',
                stichtag      TEXT    NOT NULL DEFAULT '999365.0'
            );
            """
            
            # Haupt-Tabellen erstellen
            tables = [
                "framedaten",
                "inputcontrols", 
                "menudaten",
                "viewdaten",
                "dialogdaten",
                "templatedaten",
                "systemsteuerung"
            ]
            
            for table in tables:
                cursor.execute(table_schema.format(table_name=table))
                logger.info(f"✅ Tabelle '{table}' erstellt/überprüft")
            
            self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der Tabellen-Struktur: {e}")
            return False
    
    def migrate_existing_framedaten(self) -> bool:
        """Migriert bestehende framedaten zur neuen JSON-Struktur"""
        try:
            cursor = self.connection.cursor()
            
            # Prüfen ob framedaten Tabelle überhaupt existiert
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='framedaten'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                logger.info("ℹ️ Keine framedaten Tabelle vorhanden - erstelle neue Struktur")
                # Neue Tabelle erstellen
                cursor.execute("""
                CREATE TABLE framedaten (
                    uid           TEXT    PRIMARY KEY,
                    daten         TEXT    NOT NULL,
                    name          TEXT,
                    historisch    INTEGER NOT NULL DEFAULT 0,
                    last_modified TEXT    NOT NULL DEFAULT '',
                    source_hash   TEXT    DEFAULT '',
                    stichtag      TEXT    NOT NULL DEFAULT '999365.0'
                );
                """)
                self.connection.commit()
                return True
            
            # Prüfen ob bereits neue Struktur vorhanden
            cursor.execute("PRAGMA table_info(framedaten)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'daten' in columns and len(columns) == 7:
                logger.info("✅ Neue Unified Struktur bereits vorhanden")
                return True
            
            # Alte Daten lesen (falls vorhanden)
            try:
                cursor.execute("SELECT * FROM framedaten")
                old_data = cursor.fetchall()
                logger.info(f"ℹ️ Gefunden: {len(old_data)} Frame-Datensätze zur Migration")
            except Exception as e:
                logger.warning(f"⚠️ Fehler beim Lesen alter Daten: {e} - erstelle leere neue Struktur")
                old_data = []
            
            # Backup-Tabelle erstellen (falls Daten vorhanden)
            if old_data:
                backup_name = f"framedaten_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                cursor.execute(f"ALTER TABLE framedaten RENAME TO {backup_name}")
                logger.info(f"✅ Backup erstellt: {backup_name}")
            else:
                # Leere Tabelle einfach löschen
                cursor.execute("DROP TABLE IF EXISTS framedaten")
            
            # Neue Tabelle erstellen
            cursor.execute("""
            CREATE TABLE framedaten (
                uid           TEXT    PRIMARY KEY,
                daten         TEXT    NOT NULL,
                name          TEXT,
                historisch    INTEGER NOT NULL DEFAULT 0,
                last_modified TEXT    NOT NULL DEFAULT '',
                source_hash   TEXT    DEFAULT '',
                stichtag      TEXT    NOT NULL DEFAULT '999365.0'
            );
            """)
            
            # Daten konvertieren
            for row in old_data:
                try:
                    # sqlite3.Row zu Dict konvertieren für .get() Zugriff
                    row_dict = dict(row)
                    
                    # JSON-Struktur für Frame-Daten erstellen
                    frame_json = self.convert_old_frame_to_json(row_dict)
                    
                    # Frame-GUID ermitteln
                    frame_guid = row_dict.get('frame_guid') or row_dict.get('uid') or str(uuid.uuid4())
                    frame_name = row_dict.get('frame_bezeichnung') or row_dict.get('name') or 'Migrated Frame'
                    
                    # In neue Tabelle einfügen
                    self.insert_unified_record(
                        table="framedaten",
                        uid=frame_guid,
                        daten=json.dumps(frame_json, ensure_ascii=False),
                        name=frame_name
                    )
                    
                    logger.info(f"✅ Frame migriert: {frame_name} ({frame_guid[:8]}...)")
                    
                except Exception as e:
                    # Sichere GUID-Ermittlung für Fehlerlog
                    try:
                        row_dict = dict(row)
                        error_guid = row_dict.get('frame_guid') or row_dict.get('uid') or 'unknown'
                    except:
                        error_guid = 'unknown'
                    
                    logger.warning(f"⚠️ Fehler bei Migration von Frame {error_guid}: {e}")
            
            # Commit der neuen Struktur
            self.connection.commit()
            
            migration_count = len(old_data)
            logger.info(f"✅ Frame-Migration abgeschlossen: {migration_count} Datensätze verarbeitet")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Frame-Migration: {e}")
            # Rollback versuchen
            try:
                self.connection.rollback()
            except:
                pass
            return False
    
    def convert_old_frame_to_json(self, old_frame: Dict) -> Dict[str, Any]:
        """Konvertiert alte Frame-Struktur zu neuer JSON-Struktur"""
        
        # Basis-Frame-Struktur
        frame_structure = {
            "frame_info": {
                "frame_beschreibung": old_frame.get('frame_beschreibung', ''),
                "view_guid": old_frame.get('view_guid', ''),
                "created_date": old_frame.get('erstellt_datum', datetime.now().isoformat()),
                "created_by": old_frame.get('erstellt_von', 'system'),
                "version": "1.0"
            },
            
            "dialog_config": {
                "mode": old_frame.get('mode', 0),
                "dialog_type": "standard",
                "window_title": old_frame.get('frame_bezeichnung', 'Dialog'),
                "window_size": {
                    "width": 800,
                    "height": 600,
                    "resizable": True
                },
                "layout": "vertical"
            },
            
            "tab_structure": {
                "tab_count": 1,
                "default_tab": 0,
                "tabs": [
                    {
                        "tab_id": "tab_main",
                        "tab_name": "Grunddaten",
                        "tab_icon": "📝",
                        "active": True,
                        "groups": [
                            {
                                "group_id": "group_main",
                                "group_name": "Hauptbereich",
                                "group_type": "standard",
                                "layout": "form",
                                "fields": []
                            }
                        ]
                    }
                ]
            },
            
            "input_controls": {
                "controls": [],
                "validation_rules": {},
                "field_dependencies": {}
            },
            
            "access_control": {
                "required_permissions": [],
                "admin_required": False,
                "read_only_fields": [],
                "hidden_fields": []
            },
            
            "data_binding": {
                "data_source": old_frame.get('view_guid', ''),
                "primary_key": "uid",
                "load_method": "automatic",
                "save_method": "automatic"
            },
            
            "ui_behavior": {
                "auto_save": False,
                "confirm_close": True,
                "validation_on_change": True,
                "show_toolbar": True
            }
        }
        
        return frame_structure
    
    def create_frame_templates(self) -> bool:
        """Erstellt Standard-Frame-Templates"""
        try:
            templates = {
                self.template_guids["frame_basic"]: {
                    "template": self.create_basic_frame_template(),
                    "name": "Basis Frame Template"
                },
                self.template_guids["frame_datenpflege"]: {
                    "template": self.create_datenpflege_frame_template(),
                    "name": "Datenpflege Frame Template"
                },
                self.template_guids["frame_settings"]: {
                    "template": self.create_settings_frame_template(),
                    "name": "Settings Frame Template"
                },
                self.template_guids["frame_admin"]: {
                    "template": self.create_admin_frame_template(),
                    "name": "Admin Frame Template"
                }
            }
            
            for guid, template_data in templates.items():
                success = self.insert_unified_record(
                    table="framedaten",
                    uid=guid,
                    daten=json.dumps(template_data["template"], ensure_ascii=False),
                    name=template_data["name"]
                )
                
                if success:
                    logger.info(f"✅ Frame-Template '{template_data['name']}' erstellt")
                else:
                    logger.error(f"❌ Fehler beim Erstellen des Templates {guid}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der Frame-Templates: {e}")
            return False
    
    def create_basic_frame_template(self) -> Dict[str, Any]:
        """Erstellt Basis-Frame-Template"""
        return {
            "frame_info": {
                "frame_beschreibung": "Standard-Template für neue Frames",
                "view_guid": "",
                "created_date": datetime.now().isoformat(),
                "created_by": "system",
                "version": "1.0",
                "template_type": "basic"
            },
            
            "dialog_config": {
                "mode": 0,
                "dialog_type": "standard",
                "window_title": "Neues Frame",
                "window_size": {"width": 800, "height": 600, "resizable": True},
                "layout": "vertical"
            },
            
            "tab_structure": {
                "tab_count": 1,
                "default_tab": 0,
                "tabs": [
                    {
                        "tab_id": "tab_main",
                        "tab_name": "Hauptdaten",
                        "tab_icon": "📝",
                        "active": True,
                        "groups": [
                            {
                                "group_id": "group_basic",
                                "group_name": "Grunddaten",
                                "group_type": "standard",
                                "layout": "form",
                                "columns": 1,
                                "fields": []
                            }
                        ]
                    }
                ]
            },
            
            "input_controls": {"controls": [], "validation_rules": {}, "field_dependencies": {}},
            "access_control": {"required_permissions": [], "admin_required": False, "read_only_fields": [], "hidden_fields": []},
            "data_binding": {"data_source": "", "primary_key": "uid", "load_method": "automatic", "save_method": "automatic"},
            "ui_behavior": {"auto_save": False, "confirm_close": True, "validation_on_change": True, "show_toolbar": True}
        }
    
    def create_datenpflege_frame_template(self) -> Dict[str, Any]:
        """Erstellt Datenpflege-Frame-Template"""
        return {
            "frame_info": {
                "frame_beschreibung": "Template für Datenpflege-Dialoge",
                "view_guid": "",
                "created_date": datetime.now().isoformat(),
                "created_by": "system",
                "version": "1.0",
                "template_type": "datenpflege"
            },
            
            "dialog_config": {
                "mode": 0,
                "dialog_type": "multi_tab",
                "window_title": "Datenpflege",
                "window_size": {"width": 1000, "height": 700, "resizable": True},
                "layout": "vertical"
            },
            
            "tab_structure": {
                "tab_count": 3,
                "default_tab": 0,
                "tabs": [
                    {
                        "tab_id": "tab_grunddaten",
                        "tab_name": "Grunddaten",
                        "tab_icon": "📝",
                        "active": True,
                        "groups": [
                            {
                                "group_id": "group_personal",
                                "group_name": "Persönliche Daten",
                                "group_type": "standard",
                                "layout": "form",
                                "columns": 2,
                                "fields": []
                            }
                        ]
                    },
                    {
                        "tab_id": "tab_geschaeftsdaten",
                        "tab_name": "Geschäftsdaten",
                        "tab_icon": "💼",
                        "active": False,
                        "groups": [
                            {
                                "group_id": "group_business",
                                "group_name": "Geschäftliche Informationen",
                                "group_type": "standard",
                                "layout": "form",
                                "columns": 2,
                                "fields": []
                            }
                        ]
                    },
                    {
                        "tab_id": "tab_zusaetzlich",
                        "tab_name": "Zusätzliches",
                        "tab_icon": "➕",
                        "active": False,
                        "groups": [
                            {
                                "group_id": "group_additional",
                                "group_name": "Zusätzliche Informationen",
                                "group_type": "standard",
                                "layout": "form",
                                "columns": 1,
                                "fields": []
                            }
                        ]
                    }
                ]
            },
            
            "input_controls": {"controls": [], "validation_rules": {}, "field_dependencies": {}},
            "access_control": {"required_permissions": ["data_edit"], "admin_required": False, "read_only_fields": [], "hidden_fields": []},
            "data_binding": {"data_source": "", "primary_key": "uid", "load_method": "automatic", "save_method": "automatic"},
            "ui_behavior": {"auto_save": True, "confirm_close": True, "validation_on_change": True, "show_toolbar": True}
        }
    
    def create_settings_frame_template(self) -> Dict[str, Any]:
        """Erstellt Settings-Frame-Template"""
        return {
            "frame_info": {
                "frame_beschreibung": "Template für Einstellungs-Dialoge",
                "view_guid": "",
                "created_date": datetime.now().isoformat(),
                "created_by": "system",
                "version": "1.0",
                "template_type": "settings"
            },
            
            "dialog_config": {
                "mode": 4,
                "dialog_type": "standard",
                "window_title": "Einstellungen",
                "window_size": {"width": 600, "height": 500, "resizable": True},
                "layout": "vertical"
            },
            
            "tab_structure": {
                "tab_count": 1,
                "default_tab": 0,
                "tabs": [
                    {
                        "tab_id": "tab_settings",
                        "tab_name": "Einstellungen",
                        "tab_icon": "⚙️",
                        "active": True,
                        "groups": [
                            {
                                "group_id": "group_ui",
                                "group_name": "Benutzeroberfläche",
                                "group_type": "standard",
                                "layout": "form",
                                "columns": 1,
                                "fields": []
                            },
                            {
                                "group_id": "group_behavior",
                                "group_name": "Verhalten",
                                "group_type": "standard", 
                                "layout": "form",
                                "columns": 1,
                                "fields": []
                            }
                        ]
                    }
                ]
            },
            
            "input_controls": {"controls": [], "validation_rules": {}, "field_dependencies": {}},
            "access_control": {"required_permissions": [], "admin_required": False, "read_only_fields": [], "hidden_fields": []},
            "data_binding": {"data_source": "", "primary_key": "uid", "load_method": "automatic", "save_method": "automatic"},
            "ui_behavior": {"auto_save": True, "confirm_close": False, "validation_on_change": True, "show_toolbar": False}
        }
    
    def create_admin_frame_template(self) -> Dict[str, Any]:
        """Erstellt Admin-Frame-Template"""
        return {
            "frame_info": {
                "frame_beschreibung": "Template für Administrator-Dialoge",
                "view_guid": "",
                "created_date": datetime.now().isoformat(),
                "created_by": "system",
                "version": "1.0",
                "template_type": "admin"
            },
            
            "dialog_config": {
                "mode": 1,
                "dialog_type": "multi_tab",
                "window_title": "Administration",
                "window_size": {"width": 1200, "height": 800, "resizable": True},
                "layout": "vertical"
            },
            
            "tab_structure": {
                "tab_count": 2,
                "default_tab": 0,
                "tabs": [
                    {
                        "tab_id": "tab_structure",
                        "tab_name": "Struktur",
                        "tab_icon": "🏗️",
                        "active": True,
                        "groups": [
                            {
                                "group_id": "group_frame_config",
                                "group_name": "Frame-Konfiguration",
                                "group_type": "standard",
                                "layout": "form",
                                "columns": 2,
                                "fields": []
                            }
                        ]
                    },
                    {
                        "tab_id": "tab_permissions",
                        "tab_name": "Berechtigungen",
                        "tab_icon": "🔐",
                        "active": False,
                        "groups": [
                            {
                                "group_id": "group_access",
                                "group_name": "Zugriffskontrolle",
                                "group_type": "standard",
                                "layout": "form",
                                "columns": 1,
                                "fields": []
                            }
                        ]
                    }
                ]
            },
            
            "input_controls": {"controls": [], "validation_rules": {}, "field_dependencies": {}},
            "access_control": {"required_permissions": ["admin"], "admin_required": True, "read_only_fields": [], "hidden_fields": []},
            "data_binding": {"data_source": "", "primary_key": "uid", "load_method": "manual", "save_method": "manual"},
            "ui_behavior": {"auto_save": False, "confirm_close": True, "validation_on_change": False, "show_toolbar": True}
        }
    
    def insert_unified_record(self, table: str, uid: str, daten: str, name: str = "", 
                             historisch: int = 0, stichtag: str = "999365.0") -> bool:
        """Fügt einen Datensatz in eine Unified-Tabelle ein"""
        try:
            cursor = self.connection.cursor()
            
            # Source-Hash berechnen
            import hashlib
            source_hash = hashlib.md5(daten.encode('utf-8')).hexdigest()
            
            cursor.execute("""
                INSERT OR REPLACE INTO {table} 
                (uid, daten, name, historisch, last_modified, source_hash, stichtag)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """.format(table=table), 
            (uid, daten, name, historisch, datetime.now().isoformat(), source_hash, stichtag))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Einfügen in {table}: {e}")
            return False
    
    def get_unified_record(self, table: str, uid: str) -> Optional[Dict[str, Any]]:
        """Holt einen Datensatz aus einer Unified-Tabelle"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT * FROM {table} WHERE uid = ?", (uid,))
            row = cursor.fetchone()
            
            if row:
                record = dict(row)
                # JSON-Daten parsen
                record['daten_parsed'] = json.loads(record['daten'])
                return record
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Lesen aus {table}: {e}")
            return None
    
    def setup_complete_unified_structure(self) -> bool:
        """Führt das komplette Setup der Unified-Struktur durch"""
        try:
            logger.info("🚀 Starte Unified Database Setup")
            
            # 1. Tabellen erstellen
            if not self.create_unified_table_structure():
                return False
            
            # 2. Bestehende Daten migrieren
            if not self.migrate_existing_framedaten():
                return False
            
            # 3. Templates erstellen
            if not self.create_frame_templates():
                return False
            
            logger.info("✅ Unified Database Setup erfolgreich abgeschlossen")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Unified Setup: {e}")
            return False
    
    def get_template_guids(self) -> Dict[str, str]:
        """Gibt die Template-GUIDs zurück"""
        return self.template_guids.copy()
    
    def get_setup_info(self) -> Dict[str, Any]:
        """Gibt Setup-Informationen zurück"""
        return {
            "database_path": self.db_path,
            "template_guids": self.template_guids,
            "tables_created": ["framedaten", "inputcontrols", "menudaten", "viewdaten", "dialogdaten", "templatedaten"],
            "migration_completed": True,
            "templates_created": len(self.template_guids)
        }
    
    def get_user_settings(self, user_guid: str) -> Dict[str, Any]:
        """Holt Benutzer-Einstellungen aus der Systemsteuerung"""
        try:
            record = self.get_unified_record("systemsteuerung", user_guid)
            if record:
                return record.get('daten_parsed', {})
            else:
                # Standard-Einstellungen erstellen
                default_settings = {
                    "stichtag": 2025185.0,
                    "language": "de"
                }
                self.save_user_settings(user_guid, default_settings)
                return default_settings
        except Exception as e:
            logger.error(f"❌ Fehler beim Lesen der Benutzer-Einstellungen: {e}")
            return {"stichtag": 2025185.0, "language": "de"}
    
    def save_user_settings(self, user_guid: str, settings: Dict[str, Any]) -> bool:
        """Speichert Benutzer-Einstellungen in der Systemsteuerung"""
        try:
            import json
            success = self.insert_unified_record(
                table="systemsteuerung",
                uid=user_guid,
                daten=json.dumps(settings, ensure_ascii=False),
                name=f"Benutzer-Einstellungen {user_guid[:8]}..."
            )
            return success
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Benutzer-Einstellungen: {e}")
            return False
    
    def get_frame_last_guid(self, frame_guid: str) -> Optional[str]:
        """Holt die zuletzt gewählte GUID für ein Frame"""
        try:
            record = self.get_unified_record("systemsteuerung", frame_guid)
            if record:
                frame_data = record.get('daten_parsed', {})
                return frame_data.get('last_root_guid')
            return None
        except Exception as e:
            logger.error(f"❌ Fehler beim Lesen der Frame-GUID: {e}")
            return None
    
    def save_frame_last_guid(self, frame_guid: str, last_root_guid: str) -> bool:
        """Speichert die zuletzt gewählte GUID für ein Frame"""
        try:
            import json
            frame_data = {"last_root_guid": last_root_guid}
            success = self.insert_unified_record(
                table="systemsteuerung",
                uid=frame_guid,
                daten=json.dumps(frame_data, ensure_ascii=False),
                name=f"Frame-Daten {frame_guid[:8]}..."
            )
            return success
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Frame-GUID: {e}")
            return False
    
    def get_system_table_info(self, system_guid: str = "00000000-0000-0000-0000-000000000000") -> Dict[str, Any]:
        """Holt System-Tabellen-Informationen"""
        try:
            record = self.get_unified_record("systemsteuerung", system_guid)
            if record:
                return record.get('daten_parsed', {})
            else:
                # Standard-System-Info erstellen
                default_info = {
                    "benutzerviews": {"last_change": 2025152.8194444445, "row_count": 1, "size_bytes": 3073},
                    "systemsteuerung": {"last_change": 2025152.819513889, "row_count": 3, "size_bytes": 1818},
                    "finanzdaten": {"last_change": 2025143.8393981482, "row_count": 2, "size_bytes": 282},
                    "persondaten": {"last_change": 2025147.6214699075, "row_count": 15, "size_bytes": 14510},
                    "menudaten": {"last_change": 2025150.8075578704, "row_count": 8, "size_bytes": 8255},
                    "beschreibungen": {"last_change": 2025126.652974537, "row_count": 1, "size_bytes": 856}
                }
                self.save_system_table_info(system_guid, default_info)
                return default_info
        except Exception as e:
            logger.error(f"❌ Fehler beim Lesen der System-Tabellen-Info: {e}")
            return {}
    
    def save_system_table_info(self, system_guid: str, table_info: Dict[str, Any]) -> bool:
        """Speichert System-Tabellen-Informationen"""
        try:
            import json
            success = self.insert_unified_record(
                table="systemsteuerung",
                uid=system_guid,
                daten=json.dumps(table_info, ensure_ascii=False),
                name="System-Tabellen-Info"
            )
            return success
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der System-Tabellen-Info: {e}")
            return False

if __name__ == "__main__":
    # Test der Unified Database Structure
    db_manager = PdvmUnifiedDatabaseManager()
    
    if db_manager.connect():
        success = db_manager.setup_complete_unified_structure()
        if success:
            print("✅ Unified Database Setup erfolgreich!")
            print("Template GUIDs:", db_manager.get_template_guids())
        else:
            print("❌ Setup fehlgeschlagen")
        
        db_manager.disconnect()
    else:
        print("❌ Keine Datenbank-Verbindung möglich")
