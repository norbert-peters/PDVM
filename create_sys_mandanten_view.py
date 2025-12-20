# -*- coding: utf-8 -*-
"""
sys_mandanten View und Frame erstellen

Erstellt View + Frame für Mandanten-Verwaltung analog zu sys_benutzer

AUTOR: Norbert Peters
DATUM: 08.12.2025
VERSION: 1.0
"""
import sqlite3
import json
import time
import sys
sys.path.insert(0, '.')
import allgemeines as all

# GUIDs
VIEW_GUID = all.neue_guid()
FRAME_GUID = all.neue_guid()
DIALOG_GUID = all.neue_guid()

print(f"🔧 Erstelle sys_mandanten View + Frame...")
print(f"   View-GUID: {VIEW_GUID}")
print(f"   Frame-GUID: {FRAME_GUID}")
print(f"   Dialog-GUID: {DIALOG_GUID}")

# VIEW-DATEN
view_data = {
    "ROOT": {
        "TABLE": "sys_mandanten",
        "VIEW_GUID": VIEW_GUID,
        "NO_DATA": True,  # Keine Gruppen laden, nur automatische Spalten
        "DIALOG_GUID": DIALOG_GUID
    },
    "VIEW_CONFIG": {
        "TITLE": "Mandanten-Übersicht",
        "SHOW_SEARCH": True,
        "SHOW_FILTER": True,
        "SHOW_SORT": True
    }
}

# FRAME-DATEN
frame_data = {
    "ROOT": {
        "TABLE": "sys_mandanten",
        "VIEW_GUID": VIEW_GUID,
        "DIALOG_GUID": DIALOG_GUID,
        "HEADER_TEXT": "Mandant bearbeiten",
        "EDIT_TYPE": "input_controls"
    }
}

# System-DB öffnen
conn = sqlite3.connect("Daten/pdvm_system.db")
cursor = conn.cursor()
timestamp = time.time()

# 1. VIEW erstellen
json_view = json.dumps(view_data, ensure_ascii=False)
cursor.execute(
    "INSERT INTO sys_viewdaten (uid, name, daten, created_at, modified_at, historisch, source_hash, sec_id, gilt_bis) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
    (VIEW_GUID, "Mandanten", json_view, timestamp, timestamp, 0, "", 0, 999999999.0)
)
print(f"✅ View erstellt: {VIEW_GUID}")

# 2. FRAME erstellen
json_frame = json.dumps(frame_data, ensure_ascii=False)
cursor.execute(
    "INSERT INTO sys_framedaten (uid, name, daten, created_at, modified_at, historisch, source_hash, sec_id, gilt_bis) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
    (FRAME_GUID, "Mandant bearbeiten", json_frame, timestamp, timestamp, 0, "", 0, 999999999.0)
)
print(f"✅ Frame erstellt: {FRAME_GUID}")

# 3. DIALOG erstellen
dialog_data = {
    "VIEW_GUID": VIEW_GUID,
    "FRAME_GUID": FRAME_GUID
}
json_dialog = json.dumps(dialog_data, ensure_ascii=False)
cursor.execute(
    "INSERT INTO sys_dialogdaten (uid, name, daten, created_at, modified_at, historisch, source_hash, sec_id, gilt_bis) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
    (DIALOG_GUID, "Mandanten-Dialog", json_dialog, timestamp, timestamp, 0, "", 0, 999999999.0)
)
print(f"✅ Dialog erstellt: {DIALOG_GUID}")

conn.commit()
conn.close()

print("\n✅ Fertig! sys_mandanten View + Frame erstellt")
print(f"\n📋 Verwende diese GUIDs im Menü:")
print(f"   VIEW: {VIEW_GUID}")
print(f"   FRAME: {FRAME_GUID}")
