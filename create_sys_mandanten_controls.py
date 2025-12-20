#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erstellt Controls für sys_mandanten Frames

Generiert automatisch Controls basierend auf der Datenstruktur
"""
import uuid
import sqlite3
import json

# Frame-GUIDs für sys_mandanten (nehmen wir die beiden wichtigsten + den vom User)
FRAME_GUIDS = [
    "011fc4bc-e3a6-4877-bb76-ae14dcdbf43e",  # Mandant bearbeiten
    "7dea382c-7833-4ef2-a49d-7171c304e78c",  # Mandanten verwalten
    "18725509-5460-4a2a-b968-0b0bc1e20846",  # Mandanten Test2 verwalten (USER)
]

# Definition der Controls basierend auf sys_mandanten Struktur
CONTROLS_CONFIG = {
    'STAMMDATEN': [  # ✅ ROOT-Felder in STAMMDATEN-Gruppe (ROOT ist für Frame-Metadaten reserviert!)
        {'feld': 'DB_NAME', 'label': 'Datenbank-Name', 'control_type': 'text', 'display_order': 10, 'gruppe_quelle': 'ROOT'},
        {'feld': 'BEZEICHNUNG', 'label': 'Bezeichnung', 'control_type': 'text', 'display_order': 20, 'gruppe_quelle': 'ROOT'},
    ],
    'METADATEN': [
        {'feld': 'MANDANT_ID', 'label': 'Mandanten-ID', 'control_type': 'text', 'display_order': 10, 'gruppe_quelle': 'METADATEN'},
        {'feld': 'SYSTEM_DB', 'label': 'System-Datenbank', 'control_type': 'text', 'display_order': 20, 'gruppe_quelle': 'METADATEN'},
        {'feld': 'STATUS', 'label': 'Status', 'control_type': 'dropdown', 'display_order': 30, 'gruppe_quelle': 'METADATEN'},
        {'feld': 'ERSTELLT_AM', 'label': 'Erstellt am', 'control_type': 'datetime', 'display_order': 40, 'gruppe_quelle': 'METADATEN'},
        {'feld': 'ERSTELLT_VON', 'label': 'Erstellt von', 'control_type': 'text', 'display_order': 50, 'gruppe_quelle': 'METADATEN'},
        {'feld': 'LOGO_PATH', 'label': 'Logo-Pfad', 'control_type': 'text', 'display_order': 60, 'gruppe_quelle': 'METADATEN'},
        {'feld': 'COUNTRY', 'label': 'Land', 'control_type': 'dropdown', 'display_order': 70, 'gruppe_quelle': 'METADATEN'},
    ],
}

def create_controls_for_frame(frame_guid):
    """Erstellt Controls für einen spezifischen Frame"""
    
    print(f"\n🔧 Erstelle Controls für Frame: {frame_guid}\n")
    
    # SQLite Verbindung
    conn = sqlite3.connect('Daten/pdvm_system.db')
    cursor = conn.cursor()
    
    # Aktuellen Frame laden
    cursor.execute('SELECT daten FROM sys_framedaten WHERE uid = ?', (frame_guid,))
    row = cursor.fetchone()
    if not row:
        print(f"❌ Frame {frame_guid} nicht gefunden!")
        return
    
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
                'table': 'sys_mandanten',
                'gruppe': control_config.get('gruppe_quelle', gruppe_name),  # ✅ Quelle aus Daten (ROOT → STAMMDATEN Mapping)
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
    cursor.execute('UPDATE sys_framedaten SET daten = ? WHERE uid = ?', (frame_json, frame_guid))
    conn.commit()
    conn.close()
    print("✅ Controls erfolgreich erstellt!")

def main():
    """Erstellt Controls für alle sys_mandanten Frames"""
    
    print("=" * 70)
    print("🔧 Erstelle Controls für sys_mandanten Frames")
    print("=" * 70)
    
    for frame_guid in FRAME_GUIDS:
        create_controls_for_frame(frame_guid)
    
    # Zusammenfassung
    total_controls = sum(len(c) for c in CONTROLS_CONFIG.values())
    print("\n" + "=" * 70)
    print(f"📊 Zusammenfassung:")
    print(f"   Frames: {len(FRAME_GUIDS)}")
    print(f"   Gruppen: {len(CONTROLS_CONFIG)}")
    print(f"   Controls pro Frame: {total_controls}")
    print("=" * 70)

if __name__ == '__main__':
    main()
