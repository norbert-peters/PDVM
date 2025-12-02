"""Debug-Script: sys_framedaten Struktur prüfen"""
import sqlite3
import json

db_path = r"C:\Users\norbe\OneDrive\Dokumente\MyApplication\Daten\pdvm_system.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Erste 3 Einträge laden
cursor.execute("SELECT uid, daten FROM sys_framedaten LIMIT 3")
frames = cursor.fetchall()

print("=" * 80)
print("sys_framedaten Struktur-Analyse")
print("=" * 80)

for uid, daten_str in frames:
    print(f"\n📋 UID: {uid}")
    print("-" * 80)
    
    # JSON parsen
    try:
        daten = json.loads(daten_str)
        print(f"JSON Keys: {list(daten.keys())}")
        
        if 'ROOT' in daten:
            root = daten['ROOT']
            print(f"ROOT Keys: {list(root.keys())}")
            print(f"ROOT.name: {root.get('name', 'NICHT VORHANDEN')}")
        else:
            print("❌ ROOT nicht gefunden!")
            
        # Vollständiges JSON ausgeben (erste 500 Zeichen)
        print(f"\nJSON (Auszug):\n{json.dumps(daten, indent=2, ensure_ascii=False)[:500]}")
        
    except Exception as e:
        print(f"❌ Fehler beim Parsen: {e}")

# Test: json_extract in SQLite
print("\n" + "=" * 80)
print("Test: json_extract in SQLite")
print("=" * 80)

cursor.execute("""
    SELECT 
        uid,
        json_extract(daten, '$.ROOT.name') as name
    FROM sys_framedaten 
    LIMIT 5
""")

results = cursor.fetchall()
for uid, name in results:
    print(f"UID: {uid[:20]}... → Name: {name}")

conn.close()
print("\n✅ Analyse abgeschlossen")
