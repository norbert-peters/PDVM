"""Zeigt Beispiel-Daten aus alter DB"""
import sqlite3
import json

conn = sqlite3.connect('PdvmManager.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

tables = ['systemsteuerung', 'menudaten', 'anwendungsdaten']

for table in tables:
    print(f"\n{'='*70}")
    print(f"BEISPIEL: {table}")
    print('='*70)
    
    cursor.execute(f"SELECT * FROM {table} LIMIT 3")
    rows = cursor.fetchall()
    
    for i, row in enumerate(rows, 1):
        print(f"\nDatensatz {i}:")
        print(f"  uid: {row['uid']}")
        print(f"  name: {row['name']}")
        
        try:
            daten = json.loads(row['daten'])
            print(f"  daten (JSON):")
            print(json.dumps(daten, indent=4, ensure_ascii=False))
        except:
            print(f"  daten (RAW): {row['daten'][:200]}")

conn.close()
