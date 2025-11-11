"""Prüft JSON-Struktur in sys_menudaten"""
import sqlite3
import json

db_path = "Daten/mandant_001/datenbank.db"
menu_guid = "113c6a2c-af9a-4022-929b-6544799e8954"  # AdminTestmenü

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT daten FROM sys_menudaten WHERE uid = ?", (menu_guid,))
row = cursor.fetchone()

if row:
    data = json.loads(row[0])
    print("JSON Keys:")
    for key in sorted(data.keys()):
        print(f"  - {key}")
    
    print("\nJSON (erste 500 Zeichen):")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
else:
    print("Menü nicht gefunden")

conn.close()
