"""Quick Check: Zeigt ob auth.db korrekt erstellt wurde"""
import sqlite3

conn = sqlite3.connect('Daten/auth.db')
cursor = conn.cursor()

# Tabellen auflisten
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print(f"✅ Tabellen in auth.db: {tables}")

# User zählen
cursor.execute("SELECT COUNT(*) FROM sys_benutzer")
user_count = cursor.fetchone()[0]
print(f"✅ Anzahl User: {user_count}")

# Mandanten zählen
cursor.execute("SELECT COUNT(*) FROM sys_mandanten")
mandant_count = cursor.fetchone()[0]
print(f"✅ Anzahl Mandanten: {mandant_count}")

conn.close()
print("\n🎉 auth.db ist korrekt erstellt!")
