"""Debug: Prüfe sys_viewdaten Struktur für viewtable"""
import sqlite3
import json

db_path = r"C:\Users\norbe\OneDrive\Dokumente\MyApplication\Daten\pdvm_system.db"
view_guid = "86aa89c0-43e3-4317-8df6-03dee6f63689"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print(f"sys_viewdaten Analyse: {view_guid}")
print("=" * 80)

# View-Daten laden
cursor.execute("SELECT daten FROM sys_viewdaten WHERE uid = ?", (view_guid,))
result = cursor.fetchone()

if not result:
    print(f"❌ View {view_guid} nicht gefunden!")
    conn.close()
    exit(1)

daten = json.loads(result[0])

print("\n📋 Gruppen in View:")
for gruppe in daten.keys():
    print(f"  - {gruppe}")

print("\n📋 ROOT-Struktur:")
if 'ROOT' in daten:
    root = daten['ROOT']
    for key, value in root.items():
        if isinstance(value, str) and len(value) > 100:
            print(f"  {key}: {value[:100]}... (gekürzt)")
        else:
            print(f"  {key}: {value}")
else:
    print("  ❌ ROOT nicht gefunden!")

# Prüfe ob VIEW_TABLE existiert
print("\n🔍 VIEW_TABLE Prüfung:")
if 'ROOT' in daten:
    if 'VIEW_TABLE' in daten['ROOT']:
        print(f"  ✅ VIEW_TABLE: {daten['ROOT']['VIEW_TABLE']}")
    else:
        print("  ❌ VIEW_TABLE nicht vorhanden!")
        print(f"  Verfügbare Keys: {list(daten['ROOT'].keys())}")

# Prüfe ob TABLE existiert (alternative)
if 'ROOT' in daten:
    if 'TABLE' in daten['ROOT']:
        print(f"  ✅ TABLE: {daten['ROOT']['TABLE']}")

conn.close()
print("\n✅ Analyse abgeschlossen")
