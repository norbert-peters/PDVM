#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prüfe Frame und Controls für sys_mandanten
"""
import sqlite3
import json

# 1. Suche Views für sys_mandanten
print("=== 1. VIEWS für sys_mandanten ===\n")
conn = sqlite3.connect('Daten/pdvm_system.db')
cursor = conn.cursor()

cursor.execute('SELECT uid, daten FROM sys_viewdaten')
views = cursor.fetchall()

mandanten_views = []
for view in views:
    view_guid = view[0]
    data = json.loads(view[1])
    table = data.get('ROOT', {}).get('TABLE')
    if table == 'sys_mandanten':
        mandanten_views.append((view_guid, data))
        print(f"View-GUID: {view_guid}")
        print(f"TABLE: {table}")
        print(f"ROOT-Daten: {data.get('ROOT', {})}")
        print("---\n")

# 2. Suche Frames die diese Views verwenden
print("\n=== 2. FRAMES für sys_mandanten Views ===\n")

cursor.execute('SELECT uid, daten FROM sys_framedaten')
frames = cursor.fetchall()

for frame in frames:
    frame_guid = frame[0]
    frame_data = json.loads(frame[1])
    view_guid = frame_data.get('ROOT', {}).get('VIEW_GUID')
    
    # Prüfe ob dieser Frame eine sys_mandanten View verwendet
    for mv_guid, mv_data in mandanten_views:
        if view_guid == mv_guid:
            print(f"Frame-GUID: {frame_guid}")
            print(f"View-GUID: {view_guid}")
            print(f"HEADER_TEXT: {frame_data.get('ROOT', {}).get('HEADER_TEXT')}")
            print(f"TABLE: {frame_data.get('ROOT', {}).get('TABLE')}")
            
            # Prüfe Controls
            print("\nGRUPPEN in Frame (außer ROOT):")
            gruppen = [k for k in frame_data.keys() if k != 'ROOT']
            print(f"  {gruppen}")
            
            if gruppen:
                print("\nControls pro Gruppe:")
                for gruppe in gruppen:
                    controls = frame_data.get(gruppe, {})
                    print(f"  {gruppe}: {len(controls)} Controls")
                    if len(controls) > 0:
                        # Zeige erste Control-Details
                        first_control_guid = list(controls.keys())[0]
                        first_control = controls[first_control_guid]
                        print(f"    Beispiel: {first_control.get('label')} ({first_control.get('feld')})")
            else:
                print("  ⚠️ KEINE GRUPPEN DEFINIERT - KEINE CONTROLS!")
            
            print("=" * 60 + "\n")

# 3. Datenstruktur eines Mandanten prüfen
print("\n=== 3. DATENSTRUKTUR sys_mandanten ===\n")

conn_auth = sqlite3.connect('Daten/auth.db')
cursor_auth = conn_auth.cursor()

cursor_auth.execute('SELECT uid, name, daten FROM sys_mandanten LIMIT 1')
row = cursor_auth.fetchone()

if row:
    print(f"UID: {row[0]}")
    print(f"Name: {row[1]}")
    data = json.loads(row[2])
    print(f"\nGRUPPEN in Daten:")
    for gruppe in data.keys():
        felder = data[gruppe]
        if isinstance(felder, dict):
            print(f"  {gruppe}: {list(felder.keys())}")
        else:
            print(f"  {gruppe}: {felder}")

conn_auth.close()
conn.close()
