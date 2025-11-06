"""
Analyse der Controls-Struktur in METADATEN.FINANZDATEN
"""
import sqlite3
import json

# Zuerst Systemsteuerungs-DB finden (user_guid brauchen wir nicht genau)
import os
from glob import glob

# Suche nach systemsteuerung_*.db Dateien
pattern = r'c:\Users\norbe\OneDrive\Dokumente\MyApplication\Daten\systemsteuerung_*.db'
db_files = glob(pattern)

if not db_files:
    print("❌ Keine systemsteuerung_*.db gefunden!")
    exit(1)

db_path = db_files[0]  # Nehme die erste gefundene
print(f"📂 Verwende Datenbank: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# METADATEN.FINANZDATEN holen
cursor.execute("""
    SELECT gruppe, feld, wert 
    FROM systemsteuerung 
    WHERE gruppe = 'METADATEN' AND feld = 'FINANZDATEN' 
    LIMIT 1
""")

row = cursor.fetchone()
if row:
    print(f"✅ METADATEN.FINANZDATEN gefunden")
    print(f"   GRUPPE: {row[0]}")
    print(f"   FELD: {row[1]}")
    print(f"   WERT TYPE: {type(row[2])}")
    
    if row[2]:
        data = json.loads(row[2])
        print(f"\n📊 JSON-Struktur:")
        print(f"   Keys: {list(data.keys())}")
        
        if 'controls' in data:
            controls = data['controls']
            print(f"\n🎯 CONTROLS:")
            print(f"   TYPE: {type(controls)}")
            
            if isinstance(controls, dict):
                print(f"   ANZAHL: {len(controls)}")
                print(f"   KEYS (erste 5): {list(controls.keys())[:5]}")
                
                # Ersten Control ausgeben
                first_key = list(controls.keys())[0]
                first_control = controls[first_key]
                print(f"\n📝 Beispiel-Control '{first_key}':")
                print(f"   TYPE: {type(first_control)}")
                if isinstance(first_control, dict):
                    print(f"   KEYS: {list(first_control.keys())}")
                    print(f"   CONTENT: {first_control}")
            elif isinstance(controls, list):
                print(f"   ANZAHL: {len(controls)}")
                print(f"   Erstes Element TYPE: {type(controls[0]) if controls else 'N/A'}")
                if controls:
                    print(f"   Erstes Element: {controls[0]}")
else:
    print("❌ METADATEN.FINANZDATEN nicht gefunden")

conn.close()
