import sqlite3
import json

# VIEW Template prüfen
print("="*60)
print("VIEW TEMPLATE (sys_viewdaten)")
print("="*60)

conn = sqlite3.connect('Daten/pdvm_system.db')
cursor = conn.cursor()

cursor.execute("SELECT uid, name, daten FROM sys_viewdaten WHERE uid LIKE '5555%'")
row = cursor.fetchone()

if row:
    print(f"UID: {row[0]}")
    print(f"Name: {row[1]}")
    daten = json.loads(row[2])
    print(f"\nGruppen: {list(daten.keys())}\n")
    
    for gruppe in sorted(daten.keys()):
        print(f"📁 {gruppe}:")
        if isinstance(daten[gruppe], dict):
            for key, value in sorted(daten[gruppe].items()):
                val_str = str(value)[:50]
                print(f"  - {key}: {val_str}")
        else:
            print(f"  - Type: {type(daten[gruppe])}")
        print()
else:
    print("NICHT GEFUNDEN!")

conn.close()

# FRAME Template prüfen
print("="*60)
print("FRAME TEMPLATE (sys_framedaten)")
print("="*60)

conn = sqlite3.connect('Daten/pdvm_system.db')
cursor = conn.cursor()

cursor.execute("SELECT uid, name, daten FROM sys_framedaten WHERE uid LIKE '5555%'")
row = cursor.fetchone()

if row:
    print(f"UID: {row[0]}")
    print(f"Name: {row[1]}")
    daten = json.loads(row[2])
    print(f"\nGruppen: {list(daten.keys())}\n")
    
    for gruppe in sorted(daten.keys()):
        print(f"📁 {gruppe}:")
        if isinstance(daten[gruppe], dict):
            for key, value in sorted(daten[gruppe].items()):
                val_str = str(value)[:50]
                print(f"  - {key}: {val_str}")
        else:
            print(f"  - Type: {type(daten[gruppe])}")
        print()
else:
    print("NICHT GEFUNDEN!")

conn.close()
