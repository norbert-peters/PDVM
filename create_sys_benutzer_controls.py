#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erstellt Controls für sys_benutzer Frame

Generiert automatisch Controls basierend auf der Datenstruktur
"""
import uuid
import sqlite3
import json

# Frame-GUID für sys_benutzer (aus check_benutzer_frame_controls.py)
FRAME_GUID = "6d9f5c34-5780-470e-9902-3e231d00703a"

# Definition der Controls basierend auf sys_benutzer Struktur
CONTROLS_CONFIG = {
    'USER': [
        {'feld': 'ANREDE', 'label': 'Anrede', 'control_type': 'dropdown', 'display_order': 10},
        {'feld': 'VORNAME', 'label': 'Vorname', 'control_type': 'text', 'display_order': 20},
        {'feld': 'NAME', 'label': 'Nachname', 'control_type': 'text', 'display_order': 30},
    ],
    'SETTINGS': [
        {'feld': 'THEME', 'label': 'Theme', 'control_type': 'dropdown', 'display_order': 10},
        {'feld': 'LANGUAGE', 'label': 'Sprache', 'control_type': 'dropdown', 'display_order': 20},
        {'feld': 'COUNTRY', 'label': 'Land', 'control_type': 'dropdown', 'display_order': 30},
        {'feld': 'MODE', 'label': 'Modus', 'control_type': 'dropdown', 'display_order': 40},
        {'feld': 'FONT_SIZE', 'label': 'Schriftgröße', 'control_type': 'number', 'display_order': 50},
        {'feld': 'EXPERT_MODE', 'label': 'Experten-Modus', 'control_type': 'checkbox', 'display_order': 60},
    ],
    'MANDANTEN': [
        {'feld': 'DEFAULT', 'label': 'Standard-Mandant', 'control_type': 'dropdown', 'display_order': 10},
        {'feld': 'LIST', 'label': 'Mandanten-Liste', 'control_type': 'multiselect', 'display_order': 20},
    ],
    'PERMISSIONS': [
        {'feld': 'ROLES', 'label': 'Rollen', 'control_type': 'multiselect', 'display_order': 10},
        {'feld': 'SEC_PROFILES', 'label': 'Sicherheitsprofile', 'control_type': 'multiselect', 'display_order': 20},
    ],
}

def create_controls():
    """Erstellt Controls für sys_benutzer Frame"""
    
    print("🔧 Erstelle Controls für sys_benutzer Frame\n")
    print(f"Frame-GUID: {FRAME_GUID}\n")
    
    # Frame-Instanz laden (direkt mit SQLite, ohne GCS)
    import sqlite3
    import json
    
    conn = sqlite3.connect('Daten/pdvm_system.db')
    cursor = conn.cursor()
    
    # Aktuellen Frame laden
    cursor.execute('SELECT daten FROM sys_framedaten WHERE uid = ?', (FRAME_GUID,))
    row = cursor.fetchone()
    if not row:
        print(f"❌ Frame {FRAME_GUID} nicht gefunden!")
        return
    
    frame_data = json.loads(row[0])
    frame_data = json.loads(row[0])
    
    tab_counter = 1  # Alle Controls auf Tab 1
    
    # Iteriere über alle Gruppen
    for gruppe_name, controls in CONTROLS_CONFIG.items():
        print(f"📂 Gruppe: {gruppe_name} ({len(controls)} Controls)")
        
        # Gruppe erstellen falls nicht vorhanden
        if gruppe_name not in frame_data:
            frame_data[gruppe_name] = {}
        
        for control_config in controls:
            # Neue Control-GUID generieren
            control_guid = str(uuid.uuid4())
            
            # Control-Properties als Dict
            control_data = {
                'table': 'sys_benutzer',
                'gruppe': gruppe_name,
                'feld': control_config['feld'],
                'label': control_config['label'],
                'control_type': control_config['control_type'],
                'display_order': control_config['display_order'],
                'tab': tab_counter,
                'source_path': 'root',
                'visible': True,
                'enabled': True,
                'required': False
            }
            
            # Control zur Gruppe hinzufügen
            frame_data[gruppe_name][control_guid] = control_data
            
            print(f"  ✅ {control_config['label']} ({control_config['feld']})")
    
    # Speichern
    print("\n💾 Speichere Controls...")
    frame_json = json.dumps(frame_data, ensure_ascii=False)
    cursor.execute('UPDATE sys_framedaten SET daten = ? WHERE uid = ?', (frame_json, FRAME_GUID))
    conn.commit()
    conn.close()
    print("✅ Controls erfolgreich erstellt!\n")
    
    # Zusammenfassung
    total_controls = sum(len(c) for c in CONTROLS_CONFIG.values())
    print(f"📊 Zusammenfassung:")
    print(f"   Gruppen: {len(CONTROLS_CONFIG)}")
    print(f"   Controls: {total_controls}")
    print(f"   Frame: {FRAME_GUID}")

if __name__ == '__main__':
    create_controls()
