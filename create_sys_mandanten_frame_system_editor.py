# -*- coding: utf-8 -*-
"""
Frame-Erstellung: sys_mandanten mit system_editor

Erstellt Frame für sys_mandanten-Stammdaten mit system_editor
(für direktes Bearbeiten der sys_mandanten Tabelle)

EDIT_TYPE: system_editor (für Stammdaten der Mandanten selbst)

Das vorher erstellte Frame mit input_controls ist für die Input-Controls-Verwaltung!
"""
import sqlite3
import json
import time
import sys
sys.path.insert(0, '.')
import allgemeines as all

def create_mandanten_system_editor_frame():
    """Erstellt Frame für sys_mandanten mit system_editor"""
    
    # Bestehende View verwenden (bereits erstellt)
    view_guid = "0326ca8f-d16e-4170-b152-d0f0585b36ba"
    
    # Dialog-GUID: Standard System Editor Dialog
    # (Hier müssen wir prüfen welcher Dialog für system_editor verwendet wird)
    # Für sys_viewdaten wird verwendet: siehe sys_framedaten
    
    conn = sqlite3.connect("Daten/pdvm_system.db")
    cursor = conn.cursor()
    
    # Hole Dialog-GUID von sys_viewdaten Frame (als Vorlage)
    cursor.execute("SELECT daten FROM sys_framedaten WHERE name LIKE '%viewdaten%' LIMIT 1")
    row = cursor.fetchone()
    
    dialog_guid = None
    if row:
        frame_data = json.loads(row[0])
        dialog_guid = frame_data.get('ROOT', {}).get('DIALOG_GUID')
        print(f"📋 Dialog-GUID aus sys_viewdaten Frame: {dialog_guid}")
    
    if not dialog_guid:
        print("⚠️ Kein Standard-Dialog gefunden, verwende Fallback")
        # Hole ersten Dialog aus sys_dialogdaten
        cursor.execute("SELECT uid FROM sys_dialogdaten LIMIT 1")
        row = cursor.fetchone()
        if row:
            dialog_guid = row[0]
    
    if not dialog_guid:
        print("❌ Kein Dialog gefunden!")
        conn.close()
        return None
    
    # Frame-GUID generieren
    frame_guid = all.neue_guid()
    
    # Frame-Daten
    frame_data = {
        "ROOT": {
            "TABLE": "sys_mandanten",
            "VIEW_GUID": view_guid,
            "DIALOG_GUID": dialog_guid,
            "HEADER_TEXT": "Mandanten verwalten",
            "EDIT_TYPE": "system_editor"  # ← Wichtig für Stammdaten-Bearbeitung
        }
    }
    
    # Frame erstellen
    timestamp = time.time()
    json_frame = json.dumps(frame_data, ensure_ascii=False)
    
    cursor.execute(
        "INSERT INTO sys_framedaten (uid, name, daten, created_at, modified_at, historisch, source_hash, sec_id, gilt_bis) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (frame_guid, "Mandanten verwalten (Stammdaten)", json_frame, timestamp, timestamp, 0, "", 0, 999999999.0)
    )
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Frame erstellt: {frame_guid}")
    print(f"   View-GUID: {view_guid}")
    print(f"   Dialog-GUID: {dialog_guid}")
    print(f"   EDIT_TYPE: system_editor")
    print(f"\n💡 Dieser Frame ist für die Stammdaten-Bearbeitung!")
    print(f"   (Der vorherige Frame mit input_controls ist für die Controls-Verwaltung)")
    
    return frame_guid


if __name__ == "__main__":
    frame_guid = create_mandanten_system_editor_frame()
    
    if frame_guid:
        print(f"\n📋 ZUSAMMENFASSUNG:")
        print(f"   Frame-GUID für Menü: {frame_guid}")
        print(f"   Verwendung: Mandanten-Stammdaten bearbeiten")
        print(f"   Edit-Type: system_editor")
