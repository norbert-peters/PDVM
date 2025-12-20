"""
Prüft pending_error_popup Flag in GCS Systemsteuerung
"""
import sqlite3
import json

conn = sqlite3.connect('Daten/mandant_001/datenbank.db')
cursor = conn.cursor()

user_guid = "4886ad26-061b-4662-a762-c8c83f36692d"

cursor.execute('SELECT daten FROM sys_systemsteuerung WHERE uid=?', (user_guid,))
row = cursor.fetchone()

if row:
    data = json.loads(row[0])
    flag = data.get('ROOT', {}).get('pending_error_popup')
    print(f"\n✅ User-GUID: {user_guid[:8]}...")
    print(f"📢 pending_error_popup Flag: {flag}")
    print(f"   Type: {type(flag)}")
else:
    print(f"\n❌ Kein Eintrag für User-GUID {user_guid}")

conn.close()
