"""Korrigiert User-Mandanten-Liste mit echten GUIDs"""
import sqlite3
import json

conn = sqlite3.connect('Daten/auth.db')
cursor = conn.cursor()

# 1. Mandanten-GUIDs holen
cursor.execute('SELECT uid, daten FROM sys_mandanten')
mandanten = cursor.fetchall()

mandant_mapping = {}
for uid, daten_json in mandanten:
    daten = json.loads(daten_json)
    mandant_id = daten['METADATEN']['MANDANT_ID']
    mandant_mapping[mandant_id] = uid
    print(f"{mandant_id} → {uid}")

# 2. Alle User durchgehen und MANDANTEN.LIST korrigieren
cursor.execute('SELECT benutzer, uid, daten FROM sys_benutzer')
users = cursor.fetchall()

for email, user_uid, daten_json in users:
    daten = json.loads(daten_json)
    
    # Alte Liste (mit mandant_001, mandant_002)
    old_list = daten['MANDANTEN']['LIST']
    old_default = daten['MANDANTEN'].get('DEFAULT')
    
    # Neue Liste (mit echten GUIDs)
    new_list = [mandant_mapping[m] for m in old_list if m in mandant_mapping]
    new_default = mandant_mapping.get(old_default) if old_default else new_list[0] if new_list else None
    
    print(f"\n👤 {email}:")
    print(f"   ALT: {old_list}")
    print(f"   NEU: {new_list}")
    print(f"   DEFAULT: {old_default} → {new_default}")
    
    # Update
    daten['MANDANTEN']['LIST'] = new_list
    daten['MANDANTEN']['DEFAULT'] = new_default
    
    # Speichern
    cursor.execute(
        'UPDATE sys_benutzer SET daten = ? WHERE benutzer = ?',
        (json.dumps(daten, ensure_ascii=False), email)
    )

conn.commit()
conn.close()

print("\n✅ User-Mandanten mit GUIDs aktualisiert!")
