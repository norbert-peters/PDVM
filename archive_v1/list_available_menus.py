"""Listet alle verfügbaren Menüs in der Mandanten-Datenbank"""
import sqlite3

# Mandant-001 Datenbank
db_path = 'Daten/mandant_001/datenbank.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print('=== VERFÜGBARE MENÜS IN MANDANT_001 ===\n')

cursor.execute('''
    SELECT guid, name, beschreibung 
    FROM sys_menues 
    ORDER BY name
''')

menus = cursor.fetchall()
for menu in menus:
    print(f"{menu['name']}")
    print(f"  GUID: {menu['guid']}")
    print(f"  Beschreibung: {menu['beschreibung']}")
    print()

conn.close()

print(f'\n✅ Insgesamt {len(menus)} Menüs gefunden')
