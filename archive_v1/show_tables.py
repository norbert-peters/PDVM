import sqlite3

# Verbindung zur Datenbank
conn = sqlite3.connect('PdvmManager.db')
cursor = conn.cursor()

# Alle Tabellen anzeigen
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tabellen in PdvmManager.db:")
for table in tables:
    print(f"  - {table[0]}")

conn.close()
