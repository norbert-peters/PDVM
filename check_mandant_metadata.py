"""Prüft Mandanten-Daten in auth.db"""
import sqlite3
import json

conn = sqlite3.connect('Daten/auth.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Hole User-Daten
cursor.execute('SELECT daten FROM sys_benutzer WHERE uid = ?', 
               ('4886ad26-061b-4662-a762-c8c83f36692d',))
user_row = cursor.fetchone()
user_data = json.loads(user_row['daten'])

default_mandant_guid = user_data.get('MANDANTEN', {}).get('DEFAULT')

print('=== USER MANDANTEN-KONFIGURATION ===\n')
print(f'Default Mandant GUID: {default_mandant_guid}')

# Hole Mandanten-Daten
cursor.execute('SELECT uid, daten FROM sys_mandanten WHERE uid = ?', 
               (default_mandant_guid,))
mandant_row = cursor.fetchone()

if mandant_row:
    mandant_data = json.loads(mandant_row['daten'])
    print(f'\n=== MANDANTEN-DATEN ===\n')
    print(json.dumps(mandant_data, indent=2, ensure_ascii=False))
    
    mandant_id = mandant_data.get('METADATEN', {}).get('MANDANT_ID', 'NICHT GESETZT')
    print(f'\n=== MANDANT_ID (für DB-Pfad) ===')
    print(f'MANDANT_ID: {mandant_id}')
    print(f'\nDB-Pfad würde sein: Daten/{mandant_id}/datenbank.db')
else:
    print(f'\n❌ Mandant {default_mandant_guid} NICHT GEFUNDEN!')

conn.close()
