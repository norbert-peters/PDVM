"""
Prüft bestehende Menü-Struktur in Datenbank
"""
import sqlite3
import json

db_path = r"Daten\mandant_001\datenbank.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔍 Menü-Tabellen in Datenbank:")
print("=" * 60)

# Alle Tabellen mit 'menu' im Namen
cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name LIKE '%menu%' 
    ORDER BY name
""")
tables = cursor.fetchall()
for table in tables:
    print(f"  - {table[0]}")

print("\n📊 sys_menudaten Struktur:")
print("=" * 60)

# Struktur von sys_menudaten
cursor.execute("PRAGMA table_info(sys_menudaten)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]})")

print("\n📋 Verfügbare Menüs:")
print("=" * 60)

# Alle Menüs
cursor.execute("SELECT uid, name FROM sys_menudaten ORDER BY name")
menus = cursor.fetchall()
for menu in menus:
    print(f"  {menu[1]}: {menu[0]}")

print("\n🔍 Frame-Daten Tabelle:")
print("=" * 60)

# Prüfe ob framedaten existiert
cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name = 'framedaten'
""")
if cursor.fetchone():
    # Struktur
    cursor.execute("PRAGMA table_info(framedaten)")
    columns = cursor.fetchall()
    print("\nStruktur:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Einträge
    cursor.execute("SELECT uid, name FROM framedaten WHERE name LIKE '%menu%' ORDER BY name")
    frames = cursor.fetchall()
    if frames:
        print("\nMenü-relevante Einträge:")
        for frame in frames:
            print(f"  {frame[1]}: {frame[0]}")
    else:
        print("\n⚠️  Keine menü-relevanten Einträge gefunden")
else:
    print("❌ Tabelle 'framedaten' existiert nicht")

conn.close()
