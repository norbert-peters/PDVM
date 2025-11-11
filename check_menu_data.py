"""
Prüft Menü-Daten Struktur in sys_menudaten
"""
import sqlite3
import json

conn = sqlite3.connect('Daten/mandant_001/datenbank.db')
cur = conn.cursor()

# Zeige alle Menüs
print("🔍 Vorhandene Menüs:")
cur.execute("SELECT uid, name FROM sys_menudaten")
for row in cur.fetchall():
    print(f"  {row[0]} | {row[1]}")

# Zeige Struktur vom Admin-Startmenü
print("\n📊 Admin-Startmenü Struktur:")
cur.execute("SELECT daten FROM sys_menudaten WHERE uid='5ca6674e-b9ce-4581-9756-64e742883f80'")
row = cur.fetchone()
if row:
    data = json.loads(row[0])
    print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
    
    # Zeige Top-Level Keys
    print(f"\n🔑 Top-Level Keys: {list(data.keys())}")
    
    # Zeige erste Ebene
    for key, value in list(data.items())[:3]:
        print(f"\n  {key}: {type(value).__name__}")
        if isinstance(value, dict):
            print(f"    Sub-Keys: {list(value.keys())[:5]}")

conn.close()
