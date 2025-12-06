# -*- coding: utf-8 -*-
"""
Security System - Initialisierung

Erstellt sys_security Tabelle mit Standard-Profilen für:
- Normal (Standard-Sätze)
- Template (Template-Sätze 5555...)
- System (System-Sätze 0000...)
- Deleted (Gelöschte Sätze)

AUTOR: Norbert Peters
DATUM: 06.12.2025
"""
import logging
import sqlite3
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Standard Security-Profile GUIDs (FEST für Referenzierung)
SECURITY_NORMAL_GUID = "11111111-1111-1111-1111-111111111111"
SECURITY_TEMPLATE_GUID = "22222222-2222-2222-2222-222222222222"
SECURITY_SYSTEM_GUID = "33333333-3333-3333-3333-333333333333"
SECURITY_DELETED_GUID = "44444444-4444-4444-4444-444444444444"

def create_security_system():
    """Erstellt sys_security Tabelle mit Standard-Profilen (direkt via SQLite)"""
    
    print("=" * 80)
    print("🔐 SECURITY SYSTEM - INITIALISIERUNG")
    print("=" * 80)
    
    db_path = "Daten/datenbank.db"
    table_name = "sys_security"
    
    try:
        # SCHRITT 1: Tabelle anlegen (direkt via SQLite, kein GCS nötig)
        print("\n📂 SCHRITT 1: Erstelle sys_security Tabelle...")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Tabelle erstellen
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                uid TEXT PRIMARY KEY,
                name TEXT,
                sec_id TEXT,
                daten TEXT,
                created_at REAL,
                modified_at REAL
            )
        ''')
        conn.commit()
        conn.close()
        
        print("   ✅ Tabelle 'sys_security' angelegt")
        
        # Helper-Funktion zum Speichern
        def save_record(guid, name, data):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            json_data = json.dumps(data, ensure_ascii=False)
            timestamp = 2024312.000000  # Fixer Timestamp für System-Daten
            
            cursor.execute(f'''
                INSERT INTO {table_name} (uid, name, daten, created_at, modified_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (guid, name, json_data, timestamp, timestamp))
            
            conn.commit()
            conn.close()
        
        # SCHRITT 2: System-Satz (00000000-0000-0000-0000-000000000000)
        print("\n📂 SCHRITT 2: Erstelle System-Satz...")
        system_guid = "00000000-0000-0000-0000-000000000000"
        system_data = {
            "ROOT": {
                "name": "System",
                "TABLE": "sys_security"
            }
        }
        save_record(system_guid, "System", system_data)
        print(f"   ✅ System-Satz angelegt (GUID: {system_guid})")
        
        # SCHRITT 3: Template-Satz (55555555-5555-5555-5555-555555555555)
        print("\n📂 SCHRITT 3: Erstelle Template-Satz...")
        template_guid = "55555555-5555-5555-5555-555555555555"
        template_data = {
            "ROOT": {
                "name": "Templates",
                "TABLE": "sys_security"
            },
            "VISIBILITY": {
                "category": {
                    "type": "dropdown",
                    "label": "Kategorie",
                    "options": ["normal", "template", "system", "deleted"],
                    "display_order": 1,
                    "required": True,
                    "default": "normal"
                },
                "show_by_default": {
                    "type": "bool",
                    "label": "Standardmäßig anzeigen",
                    "display_order": 2,
                    "required": True,
                    "default": True
                },
                "requires_permission": {
                    "type": "string",
                    "label": "Benötigte Berechtigung",
                    "display_order": 3,
                    "required": False,
                    "default": ""
                }
            },
            "DATE_RANGE": {
                "valid_from": {
                    "type": "datetime",
                    "label": "Gültig von",
                    "display_order": 1,
                    "required": False,
                    "default": 1001.0
                },
                "valid_until": {
                    "type": "datetime",
                    "label": "Gültig bis",
                    "display_order": 2,
                    "required": False,
                    "default": 9999999.999999
                },
                "enforce_range": {
                    "type": "bool",
                    "label": "Datumsbereich erzwingen",
                    "display_order": 3,
                    "required": False,
                    "default": False
                }
            },
            "FILTER": {
                "pre_filter": {
                    "type": "json",
                    "label": "Pre-Filter Regeln",
                    "display_order": 1,
                    "required": False,
                    "default": ""
                },
                "post_filter": {
                    "type": "json",
                    "label": "Post-Filter Regeln",
                    "display_order": 2,
                    "required": False,
                    "default": ""
                }
            }
        }
        save_record(template_guid, "Templates", template_data)
        print(f"   ✅ Template-Satz angelegt (GUID: {template_guid})")
        
        # SCHRITT 4: Standard Security-Profile anlegen
        print("\n📂 SCHRITT 4: Erstelle Standard Security-Profile...")
        
        # 4.1 NORMAL Profile
        print("\n   🔹 NORMAL Profile...")
        normal_data = {
            "ROOT": {
                "name": "Normal",
                "TABLE": "sys_security"
            },
            "VISIBILITY": {
                "category": "normal",
                "show_by_default": True,
                "requires_permission": None
            },
            "DATE_RANGE": {
                "valid_from": 1001.0,
                "valid_until": 9999999.999999,
                "enforce_range": False
            },
            "FILTER": {
                "pre_filter": None,
                "post_filter": None
            }
        }
        save_record(SECURITY_NORMAL_GUID, "Normal", normal_data)
        print(f"      ✅ NORMAL Profile: {SECURITY_NORMAL_GUID}")
        
        # 4.2 TEMPLATE Profile
        print("\n   🔹 TEMPLATE Profile...")
        template_profile_data = {
            "ROOT": {
                "name": "Template",
                "TABLE": "sys_security"
            },
            "VISIBILITY": {
                "category": "template",
                "show_by_default": False,  # Templates standardmäßig ausblenden
                "requires_permission": "view_templates"
            },
            "DATE_RANGE": {
                "valid_from": 1001.0,
                "valid_until": 9999999.999999,
                "enforce_range": False
            },
            "FILTER": {
                "pre_filter": None,
                "post_filter": None
            }
        }
        db.speichern(SECURITY_TEMPLATE_GUID, template_profile_data)
        db.set_name(SECURITY_TEMPLATE_GUID, "Template")
        print(f"      ✅ TEMPLATE Profile: {SECURITY_TEMPLATE_GUID}")
        
        # 4.3 SYSTEM Profile
        print("\n   🔹 SYSTEM Profile...")
        system_profile_data = {
            "ROOT": {
                "name": "System",
                "TABLE": "sys_security"
            },
            "VISIBILITY": {
                "category": "system",
                "show_by_default": False,  # System standardmäßig ausblenden
                "requires_permission": "view_system"
            },
            "DATE_RANGE": {
                "valid_from": 1001.0,
                "valid_until": 9999999.999999,
                "enforce_range": False
            },
            "FILTER": {
                "pre_filter": None,
                "post_filter": None
            }
        }
        db.speichern(SECURITY_SYSTEM_GUID, system_profile_data)
        db.set_name(SECURITY_SYSTEM_GUID, "System")
        print(f"      ✅ SYSTEM Profile: {SECURITY_SYSTEM_GUID}")
        
        # 4.4 DELETED Profile
        print("\n   🔹 DELETED Profile...")
        deleted_profile_data = {
            "ROOT": {
                "name": "Deleted",
                "TABLE": "sys_security"
            },
            "VISIBILITY": {
                "category": "deleted",
                "show_by_default": False,  # Gelöschte nie anzeigen
                "requires_permission": "view_deleted"
            },
            "DATE_RANGE": {
                "valid_from": 1001.0,
                "valid_until": 1001.0,  # Ungültig (von=bis)
                "enforce_range": True
            },
            "FILTER": {
                "pre_filter": None,
                "post_filter": None
            }
        }
        db.speichern(SECURITY_DELETED_GUID, deleted_profile_data)
        db.set_name(SECURITY_DELETED_GUID, "Deleted")
        print(f"      ✅ DELETED Profile: {SECURITY_DELETED_GUID}")
        
        print("\n" + "=" * 80)
        print("✅ SECURITY SYSTEM ERFOLGREICH INITIALISIERT")
        print("=" * 80)
        print("\n📋 STANDARD PROFILE:")
        print(f"   NORMAL:   {SECURITY_NORMAL_GUID}")
        print(f"   TEMPLATE: {SECURITY_TEMPLATE_GUID}")
        print(f"   SYSTEM:   {SECURITY_SYSTEM_GUID}")
        print(f"   DELETED:  {SECURITY_DELETED_GUID}")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = create_security_system()
    sys.exit(0 if success else 1)
