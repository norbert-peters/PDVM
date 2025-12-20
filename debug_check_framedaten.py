"""Debug: Prüfe sys_framedaten Einträge"""
import sqlite3
import json
import os

db_path = r"c:\Users\norbe\OneDrive\Dokumente\MyApplication\Daten\pdvm_system.db"

if not os.path.exists(db_path):
    print(f"❌ Datenbank nicht gefunden: {db_path}")
    exit(1)

print(f"✅ Datenbank: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Alle UIDs auflisten
print("\n📋 Alle UIDs in sys_framedaten:")
cursor.execute("SELECT uid FROM sys_framedaten")
all_uids = cursor.fetchall()
print(f"   Gesamt: {len(all_uids)} Einträge")

target_uid = "ed21cb69-046b-465f-b231-6e75852b50b3"
print(f"\n🔍 Suche nach: {target_uid}")

# Prüfe ob unsere GUID existiert
cursor.execute("SELECT uid, daten FROM sys_framedaten WHERE uid = ?", (target_uid,))
result = cursor.fetchone()

if result:
    print(f"✅ GUID gefunden!")
    uid, raw_json = result
    print(f"\n📦 Raw JSON (erste 500 Zeichen):")
    print(raw_json[:500])
    
    try:
        data = json.loads(raw_json)
        print(f"\n✅ JSON geparst: {len(data)} Top-Level Keys")
        print(f"   Keys: {list(data.keys())}")
        
        # Zeige erste paar Einträge
        for i, (key, value) in enumerate(list(data.items())[:3]):
            print(f"\n   [{key}]:")
            if isinstance(value, dict):
                print(f"      Typ: dict mit {len(value)} Einträgen")
                for sub_key in list(value.keys())[:3]:
                    print(f"         - {sub_key}")
            else:
                print(f"      Typ: {type(value).__name__}")
                print(f"      Wert: {str(value)[:100]}")
    except Exception as e:
        print(f"❌ Fehler beim Parsen: {e}")
else:
    print(f"❌ GUID NICHT gefunden!")
    print(f"\n📋 Erste 5 UIDs in der Tabelle:")
    for uid_tuple in all_uids[:5]:
        print(f"   - {uid_tuple[0]}")

conn.close()
