#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erstellt zentrale Tabellen-Dictionary (66666666-6666-6666-6666-666666666666)

Definiert für ALLE sys_* Tabellen:
- Verfügbare Gruppen (mit GUID als Schlüssel)
- Verfügbare Felder pro Gruppe (mit GUID als Schlüssel)
- Jedes Feld hat 'name' Property

STRUKTUR:
66666666-6666-6666-6666-666666666666
├── ROOT (TABLE, NAME, DESCRIPTION)
├── sys_framedaten
│   └── <gruppe_guid>
│       ├── name: "STAMMDATEN"
│       ├── label: "Stammdaten"
│       └── felder
│           └── <feld_guid>
│               ├── name: "TABLE"
│               ├── label: "Tabelle"
│               └── type: "string"
└── sys_mandanten
    └── <gruppe_guid>
        ├── name: "STAMMDATEN"
        └── felder
            └── <feld_guid>
                ├── name: "DB_NAME"
                ├── label: "Datenbank-Name"
                └── type: "string"
"""

import sqlite3
import json
import sys
sys.path.insert(0, '.')
import allgemeines as all

def create_tabellen_dictionary():
    """Erstellt 66666... Dictionary in pdvm_system.db"""
    
    DICT_GUID = "66666666-6666-6666-6666-666666666666"
    
    print(f"🔧 Erstelle Tabellen-Dictionary: {DICT_GUID}")
    
    # Basis-Struktur
    data = {
        "ROOT": {
            "TABLE": "sys_tabellen_dictionary",
            "NAME": "Tabellen-Dictionary",
            "DESCRIPTION": "Zentrale Definitionen für alle Tabellen - Gruppen und Felder Templates"
        }
    }
    
    # ========================================
    # sys_framedaten
    # ========================================
    data["sys_framedaten"] = {}
    
    # STAMMDATEN Gruppe
    stammdaten_guid = all.neue_guid()
    data["sys_framedaten"][stammdaten_guid] = {
        "name": "STAMMDATEN",
        "label": "Stammdaten",
        "description": "Grundlegende Frame-Informationen",
        "display_order": 1,
        "felder": {}
    }
    
    # STAMMDATEN Felder
    felder_stammdaten = [
        {"name": "TABLE", "label": "Tabelle", "type": "string", "required": True},
        {"name": "VIEW_GUID", "label": "View GUID", "type": "guid", "required": True},
        {"name": "DIALOG_GUID", "label": "Dialog GUID", "type": "guid", "required": True},
        {"name": "HEADER_TEXT", "label": "Kopfzeile", "type": "string"},
        {"name": "EDIT_TYPE", "label": "Bearbeitungstyp", "type": "string"},
    ]
    
    for idx, feld in enumerate(felder_stammdaten):
        feld_guid = all.neue_guid()
        data["sys_framedaten"][stammdaten_guid]["felder"][feld_guid] = {
            "name": feld["name"],
            "label": feld["label"],
            "type": feld["type"],
            "required": feld.get("required", False),
            "display_order": idx + 1
        }
    
    # BEARBEITUNG Gruppe
    bearbeitung_guid = all.neue_guid()
    data["sys_framedaten"][bearbeitung_guid] = {
        "name": "BEARBEITUNG",
        "label": "Bearbeitung",
        "description": "Bearbeitungs-Einstellungen",
        "display_order": 2,
        "felder": {}
    }
    
    felder_bearbeitung = [
        {"name": "ALLOW_NEW", "label": "Neu erlaubt", "type": "boolean"},
        {"name": "ALLOW_EDIT", "label": "Bearbeiten erlaubt", "type": "boolean"},
        {"name": "ALLOW_DELETE", "label": "Löschen erlaubt", "type": "boolean"},
        {"name": "READ_ONLY", "label": "Nur lesen", "type": "boolean"},
    ]
    
    for idx, feld in enumerate(felder_bearbeitung):
        feld_guid = all.neue_guid()
        data["sys_framedaten"][bearbeitung_guid]["felder"][feld_guid] = {
            "name": feld["name"],
            "label": feld["label"],
            "type": feld["type"],
            "display_order": idx + 1
        }
    
    # ========================================
    # sys_viewdaten
    # ========================================
    data["sys_viewdaten"] = {}
    
    # VIEW_CONFIG Gruppe
    view_config_guid = all.neue_guid()
    data["sys_viewdaten"][view_config_guid] = {
        "name": "VIEW_CONFIG",
        "label": "View-Konfiguration",
        "description": "View-Einstellungen",
        "display_order": 1,
        "felder": {}
    }
    
    felder_view_config = [
        {"name": "TABLE", "label": "Tabelle", "type": "string", "required": True},
        {"name": "NO_DATA", "label": "Keine Daten laden", "type": "boolean"},
        {"name": "PROJECTION_MODE", "label": "Projektionsmodus", "type": "string"},
        {"name": "ALLOW_FILTER", "label": "Filter erlaubt", "type": "boolean"},
        {"name": "ALLOW_SORT", "label": "Sortierung erlaubt", "type": "boolean"},
    ]
    
    for idx, feld in enumerate(felder_view_config):
        feld_guid = all.neue_guid()
        data["sys_viewdaten"][view_config_guid]["felder"][feld_guid] = {
            "name": feld["name"],
            "label": feld["label"],
            "type": feld["type"],
            "required": feld.get("required", False),
            "display_order": idx + 1
        }
    
    # ========================================
    # sys_mandanten
    # ========================================
    data["sys_mandanten"] = {}
    
    # STAMMDATEN Gruppe
    mandant_stammdaten_guid = all.neue_guid()
    data["sys_mandanten"][mandant_stammdaten_guid] = {
        "name": "STAMMDATEN",
        "label": "Stammdaten",
        "description": "Grundlegende Mandanten-Informationen",
        "display_order": 1,
        "felder": {}
    }
    
    felder_mandant_stammdaten = [
        {"name": "DB_NAME", "label": "Datenbank-Name", "type": "string", "required": True},
        {"name": "BEZEICHNUNG", "label": "Bezeichnung", "type": "string", "required": True},
    ]
    
    for idx, feld in enumerate(felder_mandant_stammdaten):
        feld_guid = all.neue_guid()
        data["sys_mandanten"][mandant_stammdaten_guid]["felder"][feld_guid] = {
            "name": feld["name"],
            "label": feld["label"],
            "type": feld["type"],
            "required": feld.get("required", False),
            "display_order": idx + 1
        }
    
    # METADATEN Gruppe
    mandant_metadaten_guid = all.neue_guid()
    data["sys_mandanten"][mandant_metadaten_guid] = {
        "name": "METADATEN",
        "label": "Metadaten",
        "description": "Erweiterte Mandanten-Informationen",
        "display_order": 2,
        "felder": {}
    }
    
    felder_mandant_metadaten = [
        {"name": "MANDANT_ID", "label": "Mandanten-ID", "type": "string"},
        {"name": "SYSTEM_DB", "label": "System-DB", "type": "string"},
        {"name": "STATUS", "label": "Status", "type": "string"},
        {"name": "ERSTELLT_AM", "label": "Erstellt am", "type": "datetime"},
        {"name": "ERSTELLT_VON", "label": "Erstellt von", "type": "string"},
        {"name": "LOGO_PATH", "label": "Logo-Pfad", "type": "string"},
        {"name": "COUNTRY", "label": "Land", "type": "string"},
    ]
    
    for idx, feld in enumerate(felder_mandant_metadaten):
        feld_guid = all.neue_guid()
        data["sys_mandanten"][mandant_metadaten_guid]["felder"][feld_guid] = {
            "name": feld["name"],
            "label": feld["label"],
            "type": feld["type"],
            "display_order": idx + 1
        }
    
    # ========================================
    # sys_benutzer
    # ========================================
    data["sys_benutzer"] = {}
    
    # USER Gruppe
    user_guid = all.neue_guid()
    data["sys_benutzer"][user_guid] = {
        "name": "USER",
        "label": "Benutzer",
        "description": "Benutzer-Basisdaten",
        "display_order": 1,
        "felder": {}
    }
    
    felder_user = [
        {"name": "ANREDE", "label": "Anrede", "type": "string"},
        {"name": "VORNAME", "label": "Vorname", "type": "string"},
        {"name": "NAME", "label": "Nachname", "type": "string", "required": True},
    ]
    
    for idx, feld in enumerate(felder_user):
        feld_guid = all.neue_guid()
        data["sys_benutzer"][user_guid]["felder"][feld_guid] = {
            "name": feld["name"],
            "label": feld["label"],
            "type": feld["type"],
            "required": feld.get("required", False),
            "display_order": idx + 1
        }
    
    # SETTINGS Gruppe
    settings_guid = all.neue_guid()
    data["sys_benutzer"][settings_guid] = {
        "name": "SETTINGS",
        "label": "Einstellungen",
        "description": "Benutzer-Einstellungen",
        "display_order": 2,
        "felder": {}
    }
    
    felder_settings = [
        {"name": "THEME", "label": "Theme", "type": "string"},
        {"name": "LANGUAGE", "label": "Sprache", "type": "string"},
        {"name": "COUNTRY", "label": "Land", "type": "string"},
        {"name": "MODE", "label": "Modus", "type": "string"},
        {"name": "FONT_SIZE", "label": "Schriftgröße", "type": "integer"},
        {"name": "EXPERT_MODE", "label": "Expertenmodus", "type": "boolean"},
    ]
    
    for idx, feld in enumerate(felder_settings):
        feld_guid = all.neue_guid()
        data["sys_benutzer"][settings_guid]["felder"][feld_guid] = {
            "name": feld["name"],
            "label": feld["label"],
            "type": feld["type"],
            "display_order": idx + 1
        }
    
    # ========================================
    # In pdvm_system.db speichern (sys_framedaten Tabelle)
    # ========================================
    conn = sqlite3.connect("Daten/pdvm_system.db")
    cursor = conn.cursor()
    
    # Prüfen ob schon existiert
    cursor.execute("SELECT uid FROM sys_framedaten WHERE uid = ?", (DICT_GUID,))
    exists = cursor.fetchone()
    
    if exists:
        print(f"⚠️  Dictionary existiert bereits - wird überschrieben")
        cursor.execute("DELETE FROM sys_framedaten WHERE uid = ?", (DICT_GUID,))
    
    # JSON erstellen
    json_data = json.dumps(data, ensure_ascii=False, indent=2)
    
    # Einfügen
    cursor.execute("""
        INSERT INTO sys_framedaten (uid, name, daten, created_at, modified_at, historisch, source_hash, sec_id, gilt_bis)
        VALUES (?, ?, ?, ?, ?, 0, '', NULL, 9999365.99999)
    """, (
        DICT_GUID,
        "Tabellen-Dictionary",
        json_data,
        2025351.0,  # Heute
        2025351.0
    ))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Tabellen-Dictionary erstellt!")
    print(f"   GUID: {DICT_GUID}")
    print(f"   Tabellen: sys_framedaten, sys_viewdaten, sys_mandanten, sys_benutzer")
    
    # Statistik
    print(f"\n📊 Statistik:")
    for tabelle, gruppen in data.items():
        if tabelle == "ROOT":
            continue
        print(f"   {tabelle}: {len(gruppen)} Gruppen")
        for gruppe_guid, gruppe_data in gruppen.items():
            felder_count = len(gruppe_data.get("felder", {}))
            print(f"      {gruppe_data['name']}: {felder_count} Felder")

if __name__ == "__main__":
    create_tabellen_dictionary()
