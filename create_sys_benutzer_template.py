"""
Erstellt Template-Datensatz für sys_benutzer (55555555-5555-5555-5555-555555555555)
"""
import sqlite3
import json
import allgemeines as all

# Template-Struktur für sys_benutzer
template_data = {
    "ROOT": {
        "TABLE": "sys_benutzer",
        "EDIT_TYPE": "change_user",
        "HEADER_TEXT": "Benutzer bearbeiten",
        "DIALOG_GUID": "",
        "SELF_GUID": "55555555-5555-5555-5555-555555555555",
        "DISPLAY_ST": "current",
        "DISPLAY_TIME_SHORT": False,
        "EDIT_TABS": 3,
        "EDIT_TAB_LABEL_01": "USER + SECURITY",
        "EDIT_TAB_LABEL_02": "SETTINGS + MANDANTEN",
        "EDIT_TAB_LABEL_03": "APPS + PERMISSIONS"
    },
    
    "ROOT_CONTROLS": {
        # Metadaten-Controls für ROOT-Gruppe
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
        # Standard Control-Properties (wie bei Views/Frames)
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
        # Control-Templates für häufige Felder
        "tmpl-user-text": {
            "name": "user_text",
            "table": "",
            "gruppe": "USER",
            "feld": "",
            "type": "text",
            "tab": 1,
            "display_order": 0,
            "read_only": False
        },
        "tmpl-user-dropdown": {
            "name": "user_dropdown",
            "table": "",
            "gruppe": "USER",
            "feld": "",
            "type": "dropdown",
            "tab": 1,
            "display_order": 0,
            "read_only": False
        },
        "tmpl-security-bool": {
            "name": "security_bool",
            "table": "",
            "gruppe": "SECURITY",
            "feld": "",
            "type": "boolean",
            "tab": 1,
            "display_order": 0,
            "read_only": False
        },
        "tmpl-settings-text": {
            "name": "settings_text",
            "table": "",
            "gruppe": "SETTINGS",
            "feld": "",
            "type": "text",
            "tab": 2,
            "display_order": 0,
            "read_only": False
        }
    }
}

# In Datenbank schreiben
conn = sqlite3.connect('Daten/auth.db')
cursor = conn.cursor()

template_uid = "55555555-5555-5555-5555-555555555555"
template_name = "Templates"
template_json = json.dumps(template_data, indent=2, ensure_ascii=False)

# Prüfen ob Template existiert
cursor.execute("SELECT COUNT(*) FROM sys_benutzer WHERE uid = ?", (template_uid,))
exists = cursor.fetchone()[0] > 0

if exists:
    # Update
    cursor.execute(
        "UPDATE sys_benutzer SET name = ?, daten = ? WHERE uid = ?",
        (template_name, template_json, template_uid)
    )
    print(f"✅ Template aktualisiert: {template_uid}")
else:
    # Insert (vollständige Spalten)
    import time
    current_time = time.time()
    
    cursor.execute("""
        INSERT INTO sys_benutzer 
        (uid, name, daten, benutzer, passwort, historisch, source_hash, sec_id, gilt_bis, created_at, modified_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        template_uid,
        template_name,
        template_json,
        "template@system.internal",  # benutzer (dummy)
        "TEMPLATE_NO_PASSWORD",       # passwort (dummy)
        0,                             # historisch
        "",                            # source_hash
        "",                            # sec_id
        "9999365.00000",              # gilt_bis
        current_time,                  # created_at
        current_time                   # modified_at
    ))
    print(f"✅ Template erstellt: {template_uid}")

conn.commit()
conn.close()

print("\n" + "="*60)
print("TEMPLATE-STRUKTUR:")
print("="*60)
print(f"\n📁 Gruppen: {list(template_data.keys())}")
print(f"\n📋 ROOT Controls: {len(template_data['ROOT_CONTROLS'])}")
print(f"🔧 Control Properties: {len(template_data['CONTROL_PROPERTIES'])}")
print(f"📝 Templates: {len(template_data['TEMPLATES'])}")

print("\n✅ Template für sys_benutzer erfolgreich erstellt!")
