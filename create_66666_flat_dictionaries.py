#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erstellt FLACHE Tabellen-Dictionaries - ALLE unter 66666...!

STRUKTUR (LINEAR, KEINE VERSCHACHTELUNG):
ALLE Tabellen verwenden die GLEICHE GUID: 66666666-6666-6666-6666-666666666666

persondaten (Daten/mandant_001/datenbank.db)
└── 66666666-6666-6666-6666-666666666666 ← Dictionary für persondaten

sys_mandanten (Daten/auth.db)
└── 66666666-6666-6666-6666-666666666666 ← Dictionary für sys_mandanten

sys_framedaten (Daten/pdvm_system.db)
└── 66666666-6666-6666-6666-666666666666 ← Dictionary für sys_framedaten

SORGLOSER ZUGRIFF: Immer 66666... verwenden, egal welche Tabelle!
"""

import sqlite3
import json
import sys
sys.path.insert(0, '.')
import allgemeines as all

# ZENTRALE DICTIONARY-GUID (für ALLE Tabellen!)
DICT_GUID = "66666666-6666-6666-6666-666666666666"

def create_dictionary_for_table(table_name, gruppen_def, db_path="Daten/pdvm_system.db"):
    """
    Erstellt Dictionary IN DER EIGENEN TABELLE unter 66666... (gekapselt!).
    
    Args:
        table_name: z.B. "persondaten", "sys_mandanten"
        gruppen_def: Dict mit Gruppen-Definitionen
        db_path: Datenbank-Pfad (für persondaten anders als sys_*)
    """
    data = {
        "ROOT": {
            "TABLE": table_name,
            "NAME": f"{table_name}-Dictionary",
            "DESCRIPTION": f"Control-Definitionen für {table_name}"
        }
    }
    
    # Gruppen hinzufügen (direkt unter ROOT!)
    for gruppe_name, felder_list in gruppen_def.items():
        data[gruppe_name] = {}
        
        for feld_def in felder_list:
            feld_guid = all.neue_guid()
            data[gruppe_name][feld_guid] = feld_def
    
    # In EIGENE Tabelle speichern unter 66666...!
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Prüfen ob existiert
    cursor.execute(f"SELECT uid FROM {table_name} WHERE uid = ?", (DICT_GUID,))
    exists = cursor.fetchone()
    
    if exists:
        print(f"⚠️  Dictionary 66666... existiert in {table_name} - wird überschrieben")
        cursor.execute(f"DELETE FROM {table_name} WHERE uid = ?", (DICT_GUID,))
    
    json_data = json.dumps(data, ensure_ascii=False, indent=2)
    
    cursor.execute(f"""
        INSERT INTO {table_name} (uid, name, daten, created_at, modified_at, historisch, source_hash, sec_id, gilt_bis)
        VALUES (?, ?, ?, ?, ?, 0, '', NULL, 9999365.99999)
    """, (DICT_GUID, f"{table_name}-Dictionary", json_data, 2025351.0, 2025351.0))
    
    conn.commit()
    conn.close()
    
    return data

# ========================================
# PERSONDATEN Dictionary (66666...)
# IN persondaten Tabelle!
# ========================================
print("🔧 Erstelle persondaten Dictionary IN persondaten...")

persondaten_gruppen = {
    "PERSONDATEN": [
        {"name": "pers_anrede", "label": "Anrede", "type": "dropdown", "display_order": 0},
        {"name": "pers_vorname", "label": "Vorname", "type": "text", "display_order": 1},
        {"name": "pers_familienname", "label": "Familienname", "type": "text", "display_order": 2},
        {"name": "pers_geburtsdatum", "label": "Geburtsdatum", "type": "datetime", "display_order": 3},
    ],
    "FINANZDATEN": [
        {"name": "fin_kontonummer", "label": "Konto Nummer", "type": "text", "display_order": 0},
        {"name": "fin_kontobezeichnung", "label": "Konto Bezeichnung", "type": "text", "display_order": 1},
        {"name": "fin_kontoinhaber", "label": "Konto Inhaber", "type": "text", "display_order": 2},
        {"name": "fin_waehrung", "label": "Konto Währung", "type": "dropdown", "display_order": 3},
    ],
    "ANSCHRIFT": [
        {"name": "pers_wohnort", "label": "Wohnort", "type": "text", "display_order": 8},
    ]
}

persondaten_dict = create_dictionary_for_table(
    "persondaten",
    persondaten_gruppen,
    "Daten/mandant_001/datenbank.db"  # IN persondaten Tabelle!
)

print(f"✅ persondaten Dictionary IN persondaten: {len(persondaten_gruppen)} Gruppen")
for gruppe, felder in persondaten_gruppen.items():
    print(f"   {gruppe}: {len(felder)} Felder")

# ========================================
# sys_mandanten Dictionary (77777...)
# IN sys_mandanten Tabelle (auth.db)!
# ========================================
print("\n🔧 Erstelle sys_mandanten Dictionary IN sys_mandanten...")

mandanten_gruppen = {
    "STAMMDATEN": [
        {"name": "DB_NAME", "label": "Datenbank-Name", "type": "string", "required": True, "display_order": 1},
        {"name": "BEZEICHNUNG", "label": "Bezeichnung", "type": "string", "required": True, "display_order": 2},
    ],
    "METADATEN": [
        {"name": "MANDANT_ID", "label": "Mandanten-ID", "type": "string", "display_order": 1},
        {"name": "SYSTEM_DB", "label": "System-DB", "type": "string", "display_order": 2},
        {"name": "STATUS", "label": "Status", "type": "string", "display_order": 3},
        {"name": "ERSTELLT_AM", "label": "Erstellt am", "type": "datetime", "display_order": 4},
        {"name": "ERSTELLT_VON", "label": "Erstellt von", "type": "string", "display_order": 5},
        {"name": "LOGO_PATH", "label": "Logo-Pfad", "type": "string", "display_order": 6},
        {"name": "COUNTRY", "label": "Land", "type": "string", "display_order": 7},
    ]
}

mandanten_dict = create_dictionary_for_table(
    "sys_mandanten",
    mandanten_gruppen,
    "Daten/auth.db"  # IN sys_mandanten Tabelle (auth.db)!
)

print(f"✅ sys_mandanten Dictionary IN sys_mandanten: {len(mandanten_gruppen)} Gruppen")
for gruppe, felder in mandanten_gruppen.items():
    print(f"   {gruppe}: {len(felder)} Felder")

# ========================================
# sys_framedaten Dictionary (88888...)
# IN sys_framedaten Tabelle!
# ========================================
print("\n🔧 Erstelle sys_framedaten Dictionary IN sys_framedaten...")

framedaten_gruppen = {
    "STAMMDATEN": [
        {"name": "TABLE", "label": "Tabelle", "type": "string", "required": True, "display_order": 1},
        {"name": "VIEW_GUID", "label": "View GUID", "type": "guid", "required": True, "display_order": 2},
        {"name": "DIALOG_GUID", "label": "Dialog GUID", "type": "guid", "required": True, "display_order": 3},
        {"name": "HEADER_TEXT", "label": "Kopfzeile", "type": "string", "display_order": 4},
        {"name": "EDIT_TYPE", "label": "Bearbeitungstyp", "type": "string", "display_order": 5},
    ],
    "BEARBEITUNG": [
        {"name": "ALLOW_NEW", "label": "Neu erlaubt", "type": "boolean", "display_order": 1},
        {"name": "ALLOW_EDIT", "label": "Bearbeiten erlaubt", "type": "boolean", "display_order": 2},
        {"name": "ALLOW_DELETE", "label": "Löschen erlaubt", "type": "boolean", "display_order": 3},
        {"name": "READ_ONLY", "label": "Nur lesen", "type": "boolean", "display_order": 4},
    ]
}

framedaten_dict = create_dictionary_for_table(
    "sys_framedaten",

    framedaten_gruppen,
    "Daten/pdvm_system.db"  # IN sys_framedaten Tabelle!
)

print(f"✅ sys_framedaten Dictionary IN sys_framedaten: {len(framedaten_gruppen)} Gruppen")
for gruppe, felder in framedaten_gruppen.items():
    print(f"   {gruppe}: {len(felder)} Felder")

# ========================================
# sys_viewdaten Dictionary (99999...)
# IN sys_viewdaten Tabelle!
# ========================================
print("\n🔧 Erstelle sys_viewdaten Dictionary IN sys_viewdaten...")

viewdaten_gruppen = {
    "VIEW_CONFIG": [
        {"name": "TABLE", "label": "Tabelle", "type": "string", "required": True, "display_order": 1},
        {"name": "NO_DATA", "label": "Keine Daten laden", "type": "boolean", "display_order": 2},
        {"name": "PROJECTION_MODE", "label": "Projektionsmodus", "type": "string", "display_order": 3},
        {"name": "ALLOW_FILTER", "label": "Filter erlaubt", "type": "boolean", "display_order": 4},
        {"name": "ALLOW_SORT", "label": "Sortierung erlaubt", "type": "boolean", "display_order": 5},
    ]
}

viewdaten_dict = create_dictionary_for_table(
    "sys_viewdaten",

    viewdaten_gruppen,
    "Daten/pdvm_system.db"  # IN sys_viewdaten Tabelle!
)

print(f"✅ sys_viewdaten Dictionary IN sys_viewdaten: {len(viewdaten_gruppen)} Gruppen")
for gruppe, felder in viewdaten_gruppen.items():
    print(f"   {gruppe}: {len(felder)} Felder")

print("\n🎉 Alle Dictionaries mit EINHEITLICHER GUID erstellt!")
print(f"   {DICT_GUID} → persondaten (Daten/mandant_001/datenbank.db)")
print(f"   {DICT_GUID} → sys_mandanten (Daten/auth.db)")
print(f"   {DICT_GUID} → sys_framedaten (Daten/pdvm_system.db)")
print(f"   {DICT_GUID} → sys_viewdaten (Daten/pdvm_system.db)")
print(f"\n✨ SORGLOSER ZUGRIFF: Immer 66666... verwenden!")
