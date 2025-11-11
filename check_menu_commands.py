"""Prüft command-Struktur in GRUND-Menü"""
import sqlite3
import json

# Datenbank verbinden
conn = sqlite3.connect(r'c:\Users\norbe\OneDrive\Dokumente\MyApplication\Daten\mandant_001\datenbank.db')
cursor = conn.cursor()

# Startmenü-Daten holen
cursor.execute('SELECT guid, data FROM sys_menudaten WHERE guid = "5ca6674e-b9ce-4581-9756-64e742883f80"')
result = cursor.fetchone()

if result:
    data = json.loads(result[1])
    grund_items = data.get('GRUND', {})
    
    print("=" * 60)
    print("GRUND Menu Items:")
    print("=" * 60)
    
    for k, v in grund_items.items():
        if isinstance(v, dict):
            item_type = v.get('type')
            label = v.get('label')
            command = v.get('command')
            
            print(f"\nGUID: {k}")
            print(f"  Type: {item_type}")
            print(f"  Label: {label}")
            print(f"  Command: {command}")
            
            if command:
                print(f"  Command-Type: {type(command)}")
                if isinstance(command, dict):
                    print(f"  Handler: {command.get('handler')}")
                    print(f"  Params: {command.get('params')}")

conn.close()
