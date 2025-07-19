import sqlite3
import json

# Verbindung zur Datenbank
conn = sqlite3.connect('PdvmManager.db')
cursor = conn.cursor()

# Struktur der menudaten-Tabelle
cursor.execute("PRAGMA table_info(menudaten)")
columns = cursor.fetchall()
print("Struktur der menudaten-Tabelle:")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

print("\n" + "="*50)

# Beispiel-Daten aus menudaten
cursor.execute("SELECT * FROM menudaten LIMIT 3")
rows = cursor.fetchall()
print(f"\nBeispiel-Daten aus menudaten (erste 3 Zeilen):")
for i, row in enumerate(rows):
    print(f"\nZeile {i+1}:")
    for j, col in enumerate(columns):
        value = row[j]
        if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
            try:
                parsed = json.loads(value)
                print(f"  {col[1]}: {json.dumps(parsed, indent=2)[:200]}...")
            except:
                print(f"  {col[1]}: {value[:100]}...")
        else:
            print(f"  {col[1]}: {value}")

conn.close()
