"""
Prüft JSON-Struktur in sys_menudaten
"""

import sqlite3
import json

db_path = "Daten/mandant_001/datenbank.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Hole erstes Menü
cursor.execute("SELECT uid, daten FROM sys_menudaten LIMIT 1")
row = cursor.fetchone()

if row:
    menu_guid, json_data = row
    print(f"Menü-GUID (uid Spalte): {menu_guid}")
    print(f"\nJSON-Struktur:")
    
    data = json.loads(json_data)
    print(f"  Keys: {list(data.keys())}")
    print(f"\nJSON-Inhalt (ersten 500 Zeichen):")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
else:
    print("Keine Menüs gefunden")

conn.close()
