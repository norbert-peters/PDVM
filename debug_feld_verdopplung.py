"""Debug: Analysiere Feldverdopplung in sys_framedaten"""
import sqlite3
import json

db_path = r"C:\Users\norbe\OneDrive\Dokumente\MyApplication\Daten\pdvm_system.db"
frame_uid = "4078079f-4028-45ed-879c-3c779ecf3d0d"  # Test Frame für Original Dialog

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Frame-Daten laden
cursor.execute("SELECT daten FROM sys_framedaten WHERE uid = ?", (frame_uid,))
result = cursor.fetchone()

if not result:
    print(f"❌ Frame {frame_uid} nicht gefunden!")
    exit(1)

daten = json.loads(result[0])

print("=" * 80)
print(f"Frame-Analyse: {frame_uid}")
print("=" * 80)

# PERSONDATEN Gruppe analysieren
if 'PERSONDATEN' in daten:
    persondaten = daten['PERSONDATEN']
    print(f"\n📋 PERSONDATEN - {len(persondaten)} Felder:")
    print("-" * 80)
    
    # Nach display_order sortieren
    sorted_felder = sorted(
        persondaten.items(),
        key=lambda x: x[1].get('display_order', 999)
    )
    
    for guid, feld in sorted_felder:
        name = feld.get('name', '(KEIN NAME)')
        label = feld.get('label', '(KEIN LABEL)')
        order = feld.get('display_order', 999)
        tab = feld.get('tab', -1)
        typ = feld.get('type', '(KEIN TYP)')
        
        print(f"  [{order:3d}] {name:20s} | {label:20s} | Tab={tab:2d} | Type={typ:10s} | UID={guid[:8]}...")

# Prüfe auf doppelte Namen
names = [f.get('name') for f in persondaten.values()]
duplicates = [n for n in names if names.count(n) > 1]

if duplicates:
    print("\n" + "=" * 80)
    print("⚠️ DOPPELTE NAMEN GEFUNDEN:")
    print("=" * 80)
    for dup in set(duplicates):
        matching = [(g, f) for g, f in persondaten.items() if f.get('name') == dup]
        print(f"\n  Name: {dup}")
        for guid, feld in matching:
            print(f"    - UID: {guid}")
            print(f"      Label: {feld.get('label')}")
            print(f"      Order: {feld.get('display_order')}")
            print(f"      Tab: {feld.get('tab')}")
else:
    print("\n✅ Keine doppelten Namen gefunden")

conn.close()
