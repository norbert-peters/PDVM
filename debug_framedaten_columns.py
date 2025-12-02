"""Debug-Script: sys_framedaten Tabellenstruktur prüfen"""
import sqlite3

db_path = r"C:\Users\norbe\OneDrive\Dokumente\MyApplication\Daten\pdvm_system.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Tabellenstruktur prüfen
cursor.execute("PRAGMA table_info(sys_framedaten)")
columns = cursor.fetchall()

print("=" * 80)
print("sys_framedaten Tabellenstruktur")
print("=" * 80)
for col in columns:
    print(f"  {col[1]:20s} {col[2]:15s} NOT NULL={col[3]} DEFAULT={col[4]} PK={col[5]}")

# Erste 5 Einträge mit uid und name
print("\n" + "=" * 80)
print("Erste 5 Einträge (uid, name)")
print("=" * 80)

cursor.execute("SELECT uid, name FROM sys_framedaten LIMIT 5")
results = cursor.fetchall()

for uid, name in results:
    print(f"UID: {uid[:20]}... → Name: {name}")

conn.close()
print("\n✅ Analyse abgeschlossen")
