import sqlite3, json

conn = sqlite3.connect('Daten/auth.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("SELECT daten FROM sys_benutzer WHERE uid = '4886ad26-061b-4662-a762-c8c83f36692d'")
row = cursor.fetchone()
conn.close()

if row:
    daten = json.loads(row['daten'])
    print("Verfügbare Felder in user_data:")
    for k, v in daten.items():
        print(f"  {k}: {v}")
else:
    print("Kein User gefunden")
