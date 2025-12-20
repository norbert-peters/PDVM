#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prüfe Frame und Controls für sys_benutzer
"""
import sqlite3
import json

# 1. Suche Views für sys_benutzer
print("=== 1. VIEWS für sys_benutzer ===\n")
conn = sqlite3.connect('Daten/pdvm_system.db')
cursor = conn.cursor()

cursor.execute('SELECT uid, daten FROM sys_viewdaten')
views = cursor.fetchall()

benutzer_views = []
for view in views:
    view_guid = view[0]
    data = json.loads(view[1])
    table = data.get('ROOT', {}).get('TABLE')
    if table == 'sys_benutzer':
        benutzer_views.append((view_guid, data))
        print(f"View-GUID: {view_guid}")
        print(f"TABLE: {table}")
        print(f"EDIT_TYPE: {data.get('ROOT', {}).get('EDIT_TYPE')}")
        print("---\n")

# 2. Suche Frames die diese Views verwenden
print("\n=== 2. FRAMES für sys_benutzer Views ===\n")

cursor.execute('SELECT uid, daten FROM sys_framedaten')
frames = cursor.fetchall()

for frame in frames:
    frame_guid = frame[0]
    frame_data = json.loads(frame[1])
    view_guid = frame_data.get('ROOT', {}).get('VIEW_GUID')
    
    # Prüfe ob dieser Frame eine sys_benutzer View verwendet
    for bv_guid, bv_data in benutzer_views:
        if view_guid == bv_guid:
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
                        print(f"    Control-GUIDs: {list(controls.keys())[:3]}...")  # Erste 3
            else:
                print("  ⚠️ KEINE GRUPPEN DEFINIERT - KEINE CONTROLS!")
            
            print("=" * 60 + "\n")

conn.close()
