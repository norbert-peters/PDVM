#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prüfe Frame-GUID 18725509-5460-4a2a-b968-0b0bc1e20846
"""
import sqlite3
import json

FRAME_GUID = "18725509-5460-4a2a-b968-0b0bc1e20846"

conn = sqlite3.connect('Daten/pdvm_system.db')
cursor = conn.cursor()

print("=" * 80)
print(f"FRAME-ANALYSE: {FRAME_GUID}")
print("=" * 80)

# Frame laden
cursor.execute('SELECT daten FROM sys_framedaten WHERE uid = ?', (FRAME_GUID,))
row = cursor.fetchone()

if not row:
    print(f"❌ Frame {FRAME_GUID} NICHT GEFUNDEN!")
    conn.close()
    exit(1)

frame_data = json.loads(row[0])
root = frame_data.get('ROOT', {})

print(f"\n📋 FRAME-KONFIGURATION:")
print(f"   HEADER_TEXT: {root.get('HEADER_TEXT')}")
print(f"   TABLE: {root.get('TABLE')}")
print(f"   VIEW_GUID: {root.get('VIEW_GUID')}")
print(f"   DIALOG_GUID: {root.get('DIALOG_GUID')}")
print(f"   EDIT_TYPE: {root.get('EDIT_TYPE')}")

# Prüfe Controls
gruppen = [k for k in frame_data.keys() if k != 'ROOT']
print(f"\n   Controls-Gruppen: {gruppen}")
if gruppen:
    for gruppe in gruppen:
        controls = frame_data.get(gruppe, {})
        print(f"      {gruppe}: {len(controls)} Controls")

# View laden
view_guid = root.get('VIEW_GUID')
if view_guid:
    print(f"\n📋 VIEW-KONFIGURATION ({view_guid}):")
    cursor.execute('SELECT daten FROM sys_viewdaten WHERE uid = ?', (view_guid,))
    view_row = cursor.fetchone()
    
    if view_row:
        view_data = json.loads(view_row[0])
        view_root = view_data.get('ROOT', {})
        
        print(f"   TABLE: {view_root.get('TABLE')}")
        print(f"   NO_DATA: {view_root.get('NO_DATA')}")
        print(f"   PROJECTION_MODE: {view_root.get('PROJECTION_MODE', '(NICHT GESETZT!)')}")
        print(f"   ALLOW_FILTER: {view_root.get('ALLOW_FILTER')}")
        print(f"   ALLOW_SORT: {view_root.get('ALLOW_SORT')}")
        print(f"   EDIT_TYPE: {view_root.get('EDIT_TYPE')}")
        
        # View-Controls
        view_gruppen = [k for k in view_data.keys() if k not in ['ROOT', 'VIEW_CONFIG']]
        print(f"   View-Controls-Gruppen: {view_gruppen}")
    else:
        print(f"   ❌ View {view_guid} NICHT GEFUNDEN!")
else:
    print(f"\n⚠️ KEINE VIEW_GUID gesetzt!")

# Dialog laden
dialog_guid = root.get('DIALOG_GUID')
if dialog_guid:
    print(f"\n📋 DIALOG-KONFIGURATION ({dialog_guid}):")
    cursor.execute('SELECT daten FROM sys_dialogdaten WHERE uid = ?', (dialog_guid,))
    dialog_row = cursor.fetchone()
    
    if dialog_row:
        dialog_data = json.loads(dialog_row[0])
        dialog_root = dialog_data.get('ROOT', {})
        
        print(f"   NAME: {dialog_root.get('NAME')}")
        print(f"   TITLE: {dialog_root.get('TITLE')}")
        print(f"   DIALOG_TYPE: {dialog_root.get('DIALOG_TYPE')}")
    else:
        print(f"   ❌ Dialog {dialog_guid} NICHT GEFUNDEN!")
else:
    print(f"\n⚠️ KEINE DIALOG_GUID gesetzt!")

# Prüfe ob Daten in auth.db existieren
table_name = root.get('TABLE')
if table_name:
    print(f"\n📊 DATEN-PRÜFUNG ({table_name}):")
    
    if table_name in ['sys_benutzer', 'sys_mandanten']:
        conn_auth = sqlite3.connect('Daten/auth.db')
        cursor_auth = conn_auth.cursor()
        
        try:
            cursor_auth.execute(f'SELECT COUNT(*) FROM {table_name}')
            count = cursor_auth.fetchone()[0]
            print(f"   ✅ Datensätze in auth.db: {count}")
            
            # Beispiel-Datensatz
            cursor_auth.execute(f'SELECT uid, name, daten FROM {table_name} LIMIT 1')
            example = cursor_auth.fetchone()
            if example:
                print(f"\n   📋 Beispiel-Datensatz:")
                print(f"      UID: {example[0]}")
                print(f"      Name: {example[1]}")
                data = json.loads(example[2])
                print(f"      Gruppen: {list(data.keys())}")
        except Exception as e:
            print(f"   ❌ Fehler: {e}")
        
        conn_auth.close()

conn.close()

print("\n" + "=" * 80)
