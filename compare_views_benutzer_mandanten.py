#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vergleiche View-Konfigurationen für sys_benutzer vs sys_mandanten
"""
import sqlite3
import json

conn = sqlite3.connect('Daten/pdvm_system.db')
cursor = conn.cursor()

# Alle Views laden
cursor.execute('SELECT uid, daten FROM sys_viewdaten')
views = cursor.fetchall()

print("=" * 80)
print("VIEW-VERGLEICH: sys_benutzer vs sys_mandanten")
print("=" * 80)

benutzer_views = []
mandanten_views = []

for view in views:
    view_guid = view[0]
    data = json.loads(view[1])
    table = data.get('ROOT', {}).get('TABLE')
    
    if table == 'sys_benutzer':
        benutzer_views.append((view_guid, data))
    elif table == 'sys_mandanten':
        mandanten_views.append((view_guid, data))

print("\n📋 sys_benutzer Views:")
print("-" * 80)
for guid, data in benutzer_views:
    root = data.get('ROOT', {})
    print(f"\nView-GUID: {guid}")
    print(f"  TABLE: {root.get('TABLE')}")
    print(f"  NO_DATA: {root.get('NO_DATA')}")
    print(f"  EDIT_TYPE: {root.get('EDIT_TYPE', '(nicht gesetzt)')}")
    print(f"  DIALOG_GUID: {root.get('DIALOG_GUID', '(nicht gesetzt)')}")
    print(f"  PROJECTION_MODE: {root.get('PROJECTION_MODE', '(nicht gesetzt)')}")
    
    # Prüfe ob Controls definiert sind
    controls_gruppen = [k for k in data.keys() if k not in ['ROOT', 'VIEW_CONFIG']]
    print(f"  Controls-Gruppen: {controls_gruppen if controls_gruppen else 'KEINE'}")

print("\n" + "=" * 80)
print("\n📋 sys_mandanten Views:")
print("-" * 80)
for guid, data in mandanten_views:
    root = data.get('ROOT', {})
    print(f"\nView-GUID: {guid}")
    print(f"  TABLE: {root.get('TABLE')}")
    print(f"  NO_DATA: {root.get('NO_DATA')}")
    print(f"  EDIT_TYPE: {root.get('EDIT_TYPE', '(nicht gesetzt)')}")
    print(f"  DIALOG_GUID: {root.get('DIALOG_GUID', '(nicht gesetzt)')}")
    print(f"  PROJECTION_MODE: {root.get('PROJECTION_MODE', '(nicht gesetzt)')}")
    
    # Prüfe ob Controls definiert sind
    controls_gruppen = [k for k in data.keys() if k not in ['ROOT', 'VIEW_CONFIG']]
    print(f"  Controls-Gruppen: {controls_gruppen if controls_gruppen else 'KEINE'}")

# Jetzt prüfe die DATEN aus auth.db
print("\n" + "=" * 80)
print("DATEN-PRÜFUNG aus auth.db")
print("=" * 80)

conn_auth = sqlite3.connect('Daten/auth.db')
cursor_auth = conn_auth.cursor()

print("\n✅ sys_benutzer:")
cursor_auth.execute('SELECT COUNT(*) FROM sys_benutzer')
count = cursor_auth.fetchone()[0]
print(f"   Anzahl Datensätze: {count}")

print("\n✅ sys_mandanten:")
cursor_auth.execute('SELECT COUNT(*) FROM sys_mandanten')
count = cursor_auth.fetchone()[0]
print(f"   Anzahl Datensätze: {count}")

# Prüfe ob Tabellen in pdvm_system.db als Controls definiert sind
print("\n" + "=" * 80)
print("CONTROLS-DEFINITIONEN in pdvm_system.db")
print("=" * 80)

cursor.execute('SELECT uid, daten FROM sys_controls')
controls = cursor.fetchall()

benutzer_controls = []
mandanten_controls = []

for control in controls:
    control_guid = control[0]
    data = json.loads(control[1])
    table = data.get('ROOT', {}).get('TABLE')
    
    if table == 'sys_benutzer':
        benutzer_controls.append(control_guid)
    elif table == 'sys_mandanten':
        mandanten_controls.append(control_guid)

print(f"\n📝 sys_benutzer Controls: {len(benutzer_controls)}")
if benutzer_controls:
    print(f"   GUIDs: {benutzer_controls[:3]}...")

print(f"\n📝 sys_mandanten Controls: {len(mandanten_controls)}")
if mandanten_controls:
    print(f"   GUIDs: {mandanten_controls[:3]}...")

conn.close()
conn_auth.close()

print("\n" + "=" * 80)
