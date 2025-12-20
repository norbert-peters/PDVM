"""
Prüft Details der sys_error_log Einträge
"""
import sqlite3
import json

conn = sqlite3.connect('Daten/mandant_001/datenbank.db')
cursor = conn.cursor()

cursor.execute('SELECT uid, daten, name FROM sys_error_log')
errors = cursor.fetchall()

print(f"\n✅ {len(errors)} Error(s) in sys_error_log:\n")
print("=" * 80)

for i, (uid, data_json, name) in enumerate(errors, 1):
    data = json.loads(data_json)
    root = data.get('ROOT', {})
    
    print(f"\nFEHLER #{i} - {uid[:8]}...")
    print(f"Name:            {name}")
    print(f"Typ:             {root.get('error_type')}")
    print(f"Tabelle:         {root.get('table_name')}")
    print(f"Datensatz:       {root.get('record_guid')}")
    print(f"Häufigkeit:      {root.get('occurrence_count')}x")
    print(f"Timestamp:       {root.get('timestamp')}")
    print(f"Last Occurrence: {root.get('last_occurrence')}")
    print(f"Severity:        {root.get('severity')}")
    print(f"User-GUID:       {root.get('user_guid')}")
    print(f"Message:         {root.get('error_message')[:80]}...")

conn.close()
print("\n" + "=" * 80)
