# -*- coding: utf-8 -*-
"""
Template-Datensatz für sys_mandanten erstellen

Erstellt Template-Datensatz 55555555-5555-5555-5555-555555555555
mit Struktur wie sys_viewdaten für input_controls Integration

AUTOR: Norbert Peters
DATUM: 08.12.2025
VERSION: 1.0
"""
import sqlite3
import json
import time

# Template-GUID (wie bei sys_benutzer)
TEMPLATE_GUID = "55555555-5555-5555-5555-555555555555"

# Template-Daten für sys_mandanten (ähnlich sys_viewdaten)
template_data = {
    "ROOT": {
        "TABLE": "sys_mandanten",
        "EDIT_TYPE": "input_controls",
        "HEADER_TEXT": "Mandanten verwalten",
        "DIALOG_GUID": "",
        "SELF_GUID": TEMPLATE_GUID,
        "DISPLAY_ST": "current",
        "DISPLAY_TIME_SHORT": False,
        "EDIT_TABS": 3,
        "EDIT_TAB_LABEL_01": "STAMMDATEN",
        "EDIT_TAB_LABEL_02": "EINSTELLUNGEN",
        "EDIT_TAB_LABEL_03": "DATENBANK"
    },
    "ROOT_CONTROLS": {
        "ctrl-root-selfguid": {
            "name": "SELF_GUID",
            "label": "GUID",
            "type": "text",
            "tab": 0,
            "display_order": 1
        },
        "ctrl-root-table": {
            "name": "TABLE",
            "label": "Basis-Tabelle",
            "type": "text",
            "tab": 0,
            "display_order": 2
        },
        "ctrl-root-edittype": {
            "name": "EDIT_TYPE",
            "label": "Editor-Typ",
            "type": "text",
            "tab": 0,
            "display_order": 3
        },
        "ctrl-root-header": {
            "name": "HEADER_TEXT",
            "label": "Kopfzeile",
            "type": "text",
            "tab": 0,
            "display_order": 4
        },
        "ctrl-root-tabs": {
            "name": "EDIT_TABS",
            "label": "Anzahl Tabs",
            "type": "number",
            "tab": 0,
            "display_order": 5
        }
    },
    "CONTROL_PROPERTIES": {
        "prop-name": {
            "name": "name",
            "label": "Name",
            "type": "text",
            "display_order": 1
        },
        "prop-label": {
            "name": "label",
            "label": "Label",
            "type": "text",
            "display_order": 2
        },
        "prop-type": {
            "name": "type",
            "label": "Typ",
            "type": "dropdown",
            "display_order": 3
        },
        "prop-gruppe": {
            "name": "gruppe",
            "label": "Daten-Gruppe",
            "type": "text",
            "display_order": 4
        },
        "prop-feld": {
            "name": "feld",
            "label": "Daten-Feld",
            "type": "text",
            "display_order": 5
        },
        "prop-tab": {
            "name": "tab",
            "label": "Tab",
            "type": "number",
            "display_order": 6
        },
        "prop-display_order": {
            "name": "display_order",
            "label": "Reihenfolge",
            "type": "number",
            "display_order": 7
        },
        "prop-read_only": {
            "name": "read_only",
            "label": "Nur Lesen",
            "type": "boolean",
            "display_order": 8
        }
    },
    "TEMPLATES": {
        "tmpl-stamm-text": {
            "name": "stamm_text",
            "table": "",
            "gruppe": "STAMMDATEN",
            "feld": "",
            "type": "text",
            "tab": 1,
            "display_order": 0,
            "read_only": False
        },
        "tmpl-stamm-dropdown": {
            "name": "stamm_dropdown",
            "table": "",
            "gruppe": "STAMMDATEN",
            "feld": "",
            "type": "dropdown",
            "tab": 1,
            "display_order": 0,
            "read_only": False
        },
        "tmpl-einstellungen-text": {
            "name": "einstellungen_text",
            "table": "",
            "gruppe": "EINSTELLUNGEN",
            "feld": "",
            "type": "text",
            "tab": 2,
            "display_order": 0,
            "read_only": False
        },
        "tmpl-einstellungen-bool": {
            "name": "einstellungen_bool",
            "table": "",
            "gruppe": "EINSTELLUNGEN",
            "feld": "",
            "type": "boolean",
            "tab": 2,
            "display_order": 0,
            "read_only": False
        },
        "tmpl-datenbank-text": {
            "name": "datenbank_text",
            "table": "",
            "gruppe": "DATENBANK",
            "feld": "",
            "type": "text",
            "tab": 3,
            "display_order": 0,
            "read_only": False
        }
    }
}

# Datenbank öffnen und Template einfügen/aktualisieren
print("🔧 Erstelle sys_mandanten Template in auth.db...")

db_path = "Daten/auth.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Prüfen ob Template bereits existiert
cursor.execute("SELECT COUNT(*) FROM sys_mandanten WHERE uid = ?", (TEMPLATE_GUID,))
exists = cursor.fetchone()[0] > 0

# JSON-Daten
json_daten = json.dumps(template_data, ensure_ascii=False, indent=2)
timestamp = time.time()

if exists:
    # Update
    cursor.execute(
        "UPDATE sys_mandanten SET daten = ?, modified_at = ? WHERE uid = ?",
        (json_daten, timestamp, TEMPLATE_GUID)
    )
    print(f"✅ Template aktualisiert: {TEMPLATE_GUID}")
else:
    # Insert - Standard-Struktur (uid, daten, name + Standard-Spalten)
    cursor.execute(
        """INSERT INTO sys_mandanten 
           (uid, name, daten, created_at, modified_at, historisch, source_hash, sec_id, gilt_bis) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            TEMPLATE_GUID,
            "TEMPLATE Mandant",
            json_daten,
            timestamp,
            timestamp,
            0,
            "",
            0,
            999999999.0
        )
    )
    print(f"✅ Template erstellt: {TEMPLATE_GUID}")

conn.commit()

# Template-Struktur anzeigen
print("\n📋 Template-Struktur:")
print(f"   📂 ROOT: {len(template_data['ROOT'])} Felder")
print(f"   📋 ROOT Controls: {len(template_data['ROOT_CONTROLS'])}")
print(f"   🔧 Control Properties: {len(template_data['CONTROL_PROPERTIES'])}")
print(f"   📝 Templates: {len(template_data['TEMPLATES'])}")

conn.close()

print("\n✅ Fertig!")
