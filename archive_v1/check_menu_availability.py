"""Prüft ob Menü in beiden Mandanten existiert (V2 Schema)"""
import sqlite3
import json

def check_menu_in_db_v2(db_path, menu_guid):
    """Prüft ob Menü in V2 sys_menudaten existiert"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # V2 Schema: JSON im 'data' Feld
    cursor.execute('''
        SELECT data 
        FROM sys_menudaten 
        WHERE data LIKE ?
        LIMIT 1
    ''', (f'%{menu_guid}%',))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        try:
            menu_data = json.loads(result[0])
            return menu_data.get('MENU_GUID') == menu_guid
        except:
            return False
    return False

# Testbereich Menu GUID
testbereich_guid = '113c6a2c-af9a-4022-929b-6544799e8954'

print('=== MENÜ-VERFÜGBARKEIT ===\n')
print(f'Testbereich Menu: {testbereich_guid}\n')

# Prüfe Mandant 001
db1 = 'Daten/mandant_001/datenbank.db'
try:
    exists_m1 = check_menu_in_db_v2(db1, testbereich_guid)
    print(f'Mandant_001: {"✅ VORHANDEN" if exists_m1 else "❌ NICHT VORHANDEN"}')
except Exception as e:
    print(f'Mandant_001: ❌ FEHLER - {e}')

# Prüfe Mandant 002
db2 = 'Daten/mandant_002/datenbank.db'
try:
    exists_m2 = check_menu_in_db_v2(db2, testbereich_guid)
    print(f'Mandant_002: {"✅ VORHANDEN" if exists_m2 else "❌ NICHT VORHANDEN"}')
except Exception as e:
    print(f'Mandant_002: ❌ FEHLER - {e}')

print('\n=== USER-KONFIGURATION ===')
conn = sqlite3.connect('Daten/auth.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT daten FROM sys_benutzer WHERE uid = ?', 
               ('4886ad26-061b-4662-a762-c8c83f36692d',))
row = cursor.fetchone()
conn.close()

daten = json.loads(row['daten'])
mandanten = daten.get('MANDANTEN', {})
default_mandant = mandanten.get('DEFAULT', 'NICHT GESETZT')
mandant_list = mandanten.get('LIST', [])

print(f'\nUser Default-Mandant: {default_mandant}')
print(f'Verfügbare Mandanten: {mandant_list}')
print(f'\n⚠️ Das Problem ist klar!')
