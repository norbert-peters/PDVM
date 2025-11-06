"""Entfernt ANWENDUNGEN mit NULL-Menü aus User-Daten"""
import sqlite3
import json

user_guid = '4886ad26-061b-4662-a762-c8c83f36692d'

conn = sqlite3.connect('Daten/auth.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# User-Daten laden
cursor.execute('SELECT daten FROM sys_benutzer WHERE uid = ?', (user_guid,))
row = cursor.fetchone()
user_data = json.loads(row['daten'])

print('=== VORHER ===')
anwendungen = user_data.get('ANWENDUNGEN', {})
for app_name, app_data in anwendungen.items():
    menu_guid = app_data.get('MENU')
    status = '✅' if menu_guid else '❌ NULL'
    print(f'{app_name}: {status}')

# Entferne Apps mit NULL-Menü
apps_to_remove = []
for app_name, app_data in anwendungen.items():
    if app_data.get('MENU') is None:
        apps_to_remove.append(app_name)

if apps_to_remove:
    print(f'\n=== ENTFERNE {len(apps_to_remove)} APPS ===')
    for app_name in apps_to_remove:
        print(f'  - {app_name}')
        del anwendungen[app_name]
    
    # Speichern
    user_data['ANWENDUNGEN'] = anwendungen
    cursor.execute('''
        UPDATE sys_benutzer 
        SET daten = ? 
        WHERE uid = ?
    ''', (json.dumps(user_data, ensure_ascii=False, indent=2), user_guid))
    
    conn.commit()
    print('\n✅ User-Daten aktualisiert')
else:
    print('\n✅ Keine Apps mit NULL-Menü gefunden')

print('\n=== NACHHER ===')
for app_name, app_data in anwendungen.items():
    menu_guid = app_data.get('MENU')
    print(f'{app_name}: ✅ {menu_guid}')

conn.close()
