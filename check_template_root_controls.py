"""Prüft ROOT_CONTROLS Struktur im Template"""
import sqlite3
import json

conn = sqlite3.connect('Daten/datenbank.db')
cursor = conn.cursor()

# Template-GUID
template_guid = '55555555-5555-5555-5555-555555555555'

# Beide Tabellen prüfen
for table in ['sys_framedaten', 'sys_viewdaten']:
    print(f"\n{'='*60}")
    print(f"Tabelle: {table}")
    print('='*60)
    
    try:
        cursor.execute(f"SELECT value FROM {table} WHERE guid = ?", (template_guid,))
        row = cursor.fetchone()
        
        if row:
            print("✅ Template gefunden!")
            data = json.loads(row[0])
            
            # ROOT_CONTROLS prüfen
            metadaten = data.get('METADATEN', {})
            root_controls = metadaten.get('ROOT_CONTROLS', 'NOT_FOUND')
            
            print(f"\nROOT_CONTROLS:")
            print(f"  Type: {type(root_controls)}")
            
            if isinstance(root_controls, dict):
                print(f"  Keys: {list(root_controls.keys())[:5]}...")
                print(f"  Count: {len(root_controls)}")
                # Zeige ersten Eintrag
                if root_controls:
                    first_key = list(root_controls.keys())[0]
                    print(f"\n  Beispiel ({first_key}):")
                    print(f"    {root_controls[first_key]}")
            elif isinstance(root_controls, list):
                print(f"  ❌ IST EINE LISTE! (Count: {len(root_controls)})")
                print(f"  Erste 3 Items:")
                for i, item in enumerate(root_controls[:3]):
                    print(f"    [{i}]: {item}")
            else:
                print(f"  Wert: {root_controls}")
        else:
            print("❌ Template nicht gefunden")
            
    except sqlite3.OperationalError as e:
        print(f"❌ Fehler: {e}")

conn.close()
