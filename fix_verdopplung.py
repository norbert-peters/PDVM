"""
Fix: Entferne Duplikat pers_familienname und stelle pers_vorname wieder her

Basierend auf den Original-Daten die du gegeben hast:
- 556ccb20-2a5d-4bc7-a79e-bc54e5c29fd3 sollte pers_vorname sein (display_order=1)
- 179c62fd-4708-4e12-909c-d12ed7ff2e2b sollte pers_familienname sein (display_order=2)
"""
import sqlite3
import json

db_path = r"C:\Users\norbe\OneDrive\Dokumente\MyApplication\Daten\pdvm_system.db"
frame_uid = "4078079f-4028-45ed-879c-3c779ecf3d0d"

print("=" * 80)
print("FIX: Verdopplung in sys_framedaten korrigieren")
print("=" * 80)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Daten laden
cursor.execute("SELECT daten FROM sys_framedaten WHERE uid = ?", (frame_uid,))
result = cursor.fetchone()

if not result:
    print(f"❌ Frame {frame_uid} nicht gefunden!")
    conn.close()
    exit(1)

daten = json.loads(result[0])

print("\n📋 VORHER:")
print("-" * 80)
if 'PERSONDATEN' in daten:
    for guid, feld in daten['PERSONDATEN'].items():
        print(f"  {guid[:8]}... | {feld.get('name'):25s} | {feld.get('label')}")

# 2. Korrektur durchführen
if 'PERSONDATEN' in daten:
    persondaten = daten['PERSONDATEN']
    
    # GUID 556ccb20... → pers_vorname (aus deinen Originaldaten)
    vorname_guid = "556ccb20-2a5d-4bc7-a79e-bc54e5c29fd3"
    if vorname_guid in persondaten:
        print(f"\n✅ Korrigiere {vorname_guid[:8]}... → pers_vorname")
        persondaten[vorname_guid]['name'] = 'pers_vorname'
        persondaten[vorname_guid]['label'] = 'Vorname'
        persondaten[vorname_guid]['tooltip'] = 'Bitte alle Vornamen eingeben'
        persondaten[vorname_guid]['display_order'] = 1
        persondaten[vorname_guid]['tab'] = 1  # Tab 1 (nicht -4!)
    
    # GUID 179c62fd... → pers_familienname (bleibt)
    familienname_guid = "179c62fd-4708-4e12-909c-d12ed7ff2e2b"
    if familienname_guid in persondaten:
        print(f"✅ Behalte {familienname_guid[:8]}... → pers_familienname")
        persondaten[familienname_guid]['name'] = 'pers_familienname'
        persondaten[familienname_guid]['label'] = 'Familienname'
        persondaten[familienname_guid]['tooltip'] = 'Familienname bzw. Nachname'
        persondaten[familienname_guid]['display_order'] = 2

print("\n📋 NACHHER:")
print("-" * 80)
if 'PERSONDATEN' in daten:
    sorted_felder = sorted(
        daten['PERSONDATEN'].items(),
        key=lambda x: x[1].get('display_order', 999)
    )
    for guid, feld in sorted_felder:
        print(f"  {guid[:8]}... | {feld.get('name'):25s} | {feld.get('label'):20s} | Order={feld.get('display_order')}")

# 3. Zurückschreiben
print("\n💾 Speichere korrigierte Daten...")
daten_json = json.dumps(daten, ensure_ascii=False)
cursor.execute("UPDATE sys_framedaten SET daten = ? WHERE uid = ?", (daten_json, frame_uid))
conn.commit()
conn.close()

print("✅ Korrektur abgeschlossen!")
print("\n📝 ÄNDERUNGEN:")
print("  - 556ccb20... ist jetzt pers_vorname (display_order=1, tab=1)")
print("  - 179c62fd... bleibt pers_familienname (display_order=2)")
