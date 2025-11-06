"""Prüft ob Menü in beiden Mandanten existiert"""
import sqlite3
import json

def check_menu_in_db(db_path, menu_guid):
    """Prüft ob Menü in DB existiert"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT uid, wert 
        FROM sys_menudaten 
        WHERE uid = ? 
        LIMIT 1
    ''', (menu_guid,))
    
    result = cursor.fetchone()
    conn.close()
    
    return result is not None

# Testbereich Menu GUID
testbereich_guid = '113c6a2c-af9a-4022-929b-6544799e8954'

print('=== MENÜ-VERFÜGBARKEIT ===\n')
print(f'Testbereich Menu: {testbereich_guid}\n')

# Prüfe Mandant 001
db1 = 'Daten/mandant_001/datenbank.db'
exists_m1 = check_menu_in_db(db1, testbereich_guid)
print(f'Mandant_001: {"✅ VORHANDEN" if exists_m1 else "❌ NICHT VORHANDEN"}')

# Prüfe Mandant 002
db2 = 'Daten/mandant_002/datenbank.db'
exists_m2 = check_menu_in_db(db2, testbereich_guid)
print(f'Mandant_002: {"✅ VORHANDEN" if exists_m2 else "❌ NICHT VORHANDEN"}')

print('\n=== USER-KONFIGURATION ===')
conn = sqlite3.connect('Daten/auth.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT daten FROM sys_benutzer WHERE uid = ?', 
               ('4886ad26-061b-4662-a762-c8c83f36692d',))
row = cursor.fetchone()
conn.close()

daten = json.loads(row['daten'])
default_mandant = daten.get('MANDANTEN', {}).get('DEFAULT', 'NICHT GESETZT')

print(f'\nUser Default-Mandant: {default_mandant}')
print(f'\n⚠️ PROBLEM: User nutzt {default_mandant}, aber Menü ist in mandant_002!')
