import sqlite3

conn = sqlite3.connect('Daten/auth.db')
cursor = conn.cursor()

# Schema holen
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='sys_benutzer'")
schema = cursor.fetchone()

print("="*60)
print("sys_benutzer CREATE TABLE Statement:")
print("="*60)
if schema:
    print(schema[0])
else:
    print("Tabelle nicht gefunden!")

print("\n" + "="*60)
print("Spalten-Info:")
print("="*60)
cursor.execute("PRAGMA table_info(sys_benutzer)")
cols = cursor.fetchall()
for col in cols:
    print(f"  {col[0]}: {col[1]} (Type: {col[2]}, NotNull: {col[3]}, Default: {col[4]}, PK: {col[5]})")

conn.close()
