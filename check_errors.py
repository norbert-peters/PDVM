import sqlite3

conn = sqlite3.connect('Daten/mandant_001/datenbank.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM sys_error_log')
count = cursor.fetchone()[0]
print(f'sys_error_log Anzahl: {count}')

cursor.execute('SELECT uid, name FROM sys_error_log LIMIT 5')
rows = cursor.fetchall()
for uid, name in rows:
    print(f'  - {uid[:8]}... | {name}')

conn.close()
