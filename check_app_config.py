"""Prüft ANWENDUNGEN-Konfiguration für User"""
import sqlite3
import json

conn = sqlite3.connect('Daten/auth.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT daten FROM sys_benutzer WHERE uid = ?', 
               ('4886ad26-061b-4662-a762-c8c83f36692d',))
row = cursor.fetchone()
conn.close()

daten = json.loads(row['daten'])
anwendungen = daten.get('ANWENDUNGEN', {})

print('=== ANWENDUNGEN KONFIGURATION ===\n')
for name, app_data in anwendungen.items():
    menu_guid = app_data.get('MENU', 'NICHT KONFIGURIERT')
    print(f'{name}:')
    print(f'  MENU: {menu_guid}')
    print(f'  Daten: {app_data}')
    print()
