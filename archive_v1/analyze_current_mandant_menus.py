"""Analysiert aktuellen Mandanten und verfügbare Menüs"""
import sqlite3
import json
from pathlib import Path

# 1. User-Daten holen
conn = sqlite3.connect('Daten/auth.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT daten FROM sys_benutzer WHERE uid = ?', 
               ('4886ad26-061b-4662-a762-c8c83f36692d',))
user_row = cursor.fetchone()
user_data = json.loads(user_row['daten'])

# 2. Default Mandant holen
default_mandant_guid = user_data.get('MANDANTEN', {}).get('DEFAULT')
print(f'=== USER DEFAULT MANDANT ===')
print(f'GUID: {default_mandant_guid}\n')

# 3. Mandanten-Daten holen
cursor.execute('SELECT uid, daten FROM sys_mandanten WHERE uid = ?', 
               (default_mandant_guid,))
mandant_row = cursor.fetchone()

if not mandant_row:
    print(f'❌ Mandant {default_mandant_guid} nicht gefunden!')
    conn.close()
    exit(1)

mandant_data = json.loads(mandant_row['daten'])
mandant_id = mandant_data.get('METADATEN', {}).get('MANDANT_ID', 'UNBEKANNT')
mandant_name = mandant_data.get('METADATEN', {}).get('NAME', 'UNBEKANNT')

print(f'=== MANDANTEN-INFO ===')
print(f'Name: {mandant_name}')
print(f'MANDANT_ID: {mandant_id}')
print(f'DB-Pfad: Daten/{mandant_id}/datenbank.db\n')

conn.close()

# 4. Prüfe ob Mandanten-DB existiert
db_path = Path(__file__).parent / 'Daten' / mandant_id / 'datenbank.db'
if not db_path.exists():
    print(f'❌ Mandanten-DB existiert nicht: {db_path}')
    exit(1)

print(f'✅ Mandanten-DB gefunden: {db_path}\n')

# 5. Lade alle Menüs aus dieser DB
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Prüfe Tabellenstruktur
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%menu%'")
menu_tables = cursor.fetchall()

print(f'=== MENU-TABELLEN IN {mandant_id} ===')
for table in menu_tables:
    print(f'  - {table[0]}')
print()

# Versuche Menüs zu laden (sys_menudaten)
try:
    cursor.execute("SELECT COUNT(*) FROM sys_menudaten")
    count = cursor.fetchone()[0]
    print(f'=== MENÜS IN sys_menudaten ===')
    print(f'Anzahl Einträge: {count}\n')
    
    # Lade erste 5 Menüs
    cursor.execute("SELECT * FROM sys_menudaten LIMIT 5")
    rows = cursor.fetchall()
    
    # Zeige Spalten
    cursor.execute("PRAGMA table_info(sys_menudaten)")
    columns = cursor.fetchall()
    print('Spalten:')
    for col in columns:
        print(f'  - {col[1]} ({col[2]})')
    print()
    
    # Zeige erste Einträge
    print('Erste Einträge:')
    for row in rows:
        print(f'  {dict(zip([c[1] for c in columns], row))}')
        
except Exception as e:
    print(f'❌ Fehler beim Laden der Menüs: {e}')

conn.close()

# 6. User ANWENDUNGEN
print(f'\n=== USER ANWENDUNGEN ===')
anwendungen = user_data.get('ANWENDUNGEN', {})
for app_name, app_data in anwendungen.items():
    menu_guid = app_data.get('MENU')
    status = '✅' if menu_guid else '❌ NULL'
    print(f'{app_name}: {status} {menu_guid or ""}')
