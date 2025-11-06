"""Listet alle Menüs in sys_menudaten"""
import sqlite3
import json

conn = sqlite3.connect('Daten/mandant_001/datenbank.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Hole alle eindeutigen Menü-GUIDs
cursor.execute('''
    SELECT DISTINCT uid, gruppe, feld, wert 
    FROM sys_menudaten 
    WHERE gruppe = '111-MENU' AND feld = 'NAME'
    ORDER BY wert
''')

menus = cursor.fetchall()

print('=== VERFÜGBARE MENÜS ===\n')
for menu in menus:
    menu_guid = menu['uid']
    menu_name = menu['wert']
    
    # Hole Beschreibung
    cursor.execute('''
        SELECT wert FROM sys_menudaten 
        WHERE uid = ? AND gruppe = '111-MENU' AND feld = 'BESCHREIBUNG'
    ''', (menu_guid,))
    desc_row = cursor.fetchone()
    beschreibung = desc_row['wert'] if desc_row else 'Keine Beschreibung'
    
    print(f"{menu_name}")
    print(f"  GUID: {menu_guid}")
    print(f"  Beschreibung: {beschreibung}")
    print()

conn.close()

print(f'✅ Insgesamt {len(menus)} Menüs gefunden')
