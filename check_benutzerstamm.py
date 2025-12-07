import sqlite3

# Hauptdatenbank prüfen
conn = sqlite3.connect('Daten/mandant_001/datenbank.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print('Tabellen in Hauptdatenbank:', ', '.join(tables))
if 'benutzerstamm' in tables:
    print('❌ benutzerstamm Tabelle gefunden!')
else:
    print('✅ Keine benutzerstamm Tabelle')
conn.close()

# auth.db prüfen
conn = sqlite3.connect('Daten/auth.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print('\nTabellen in auth.db:', ', '.join(tables))
if 'sys_benutzer' in tables:
    print('✅ sys_benutzer Tabelle gefunden')
else:
    print('❌ sys_benutzer Tabelle FEHLT!')
conn.close()
