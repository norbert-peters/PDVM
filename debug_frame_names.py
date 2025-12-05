# -*- coding: utf-8 -*-
"""Debug: Prüfe wie Namen in sys_framedaten gespeichert sind"""

import sqlite3
import json
import os

# Direkt auf Datenbank zugreifen
db_path = os.path.join(os.path.dirname(__file__), 'Daten', 'datenbank.db')
print(f"📂 Datenbank: {db_path}")

if not os.path.exists(db_path):
    print("❌ Datenbank nicht gefunden!")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Spalten-Struktur prüfen
print("\n📋 Spalten in sys_framedaten:")
cursor.execute("PRAGMA table_info(sys_framedaten)")
columns = cursor.fetchall()
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

# Ersten Datensatz prüfen
print("\n🔍 Erster Datensatz:")
cursor.execute("SELECT uid, name, daten FROM sys_framedaten LIMIT 1")
row = cursor.fetchone()

if row:
    uid, name_spalte, daten_json = row
    print(f"\nUID: {uid}")
    print(f"name (Spalte): {name_spalte}")
    
    try:
        daten = json.loads(daten_json)
        print(f"daten.ROOT.name: {daten.get('ROOT', {}).get('name', 'NICHT VORHANDEN')}")
        print(f"\nROOT Keys: {list(daten.get('ROOT', {}).keys())}")
    except:
        print("JSON-Parsing Fehler")

conn.close()
