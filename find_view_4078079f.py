"""
Sucht nach View 4078079f in allen Mandanten-DBs
"""
import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATEN_DIR = os.path.join(BASE_DIR, 'Daten')
TARGET_GUID = '4078079f-4028-45ed-879c-3c779ecf3d0d'

def search_in_db(db_path, db_name):
    """Sucht View in einer DB"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Prüfe ob sys_viewdaten existiert
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sys_viewdaten'")
        if not cursor.fetchone():
            conn.close()
            return None
        
        # Suche View
        cursor.execute('SELECT daten, name FROM sys_viewdaten WHERE uid = ?', (TARGET_GUID,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return (db_path, db_name, result[0], result[1])
        
        return None
    except Exception as e:
        return None

print(f"🔍 Suche View: {TARGET_GUID}\n")

# Haupt-Datenbanken prüfen
dbs_to_check = [
    (os.path.join(DATEN_DIR, 'pdvm_system.db'), 'pdvm_system.db'),
    (os.path.join(DATEN_DIR, 'datenbank.db'), 'datenbank.db')
]

# Mandanten-DBs prüfen
for item in os.listdir(DATEN_DIR):
    item_path = os.path.join(DATEN_DIR, item)
    if os.path.isdir(item_path):
        # Suche nach .db Dateien im Mandanten-Ordner
        for db_file in os.listdir(item_path):
            if db_file.endswith('.db'):
                db_path = os.path.join(item_path, db_file)
                dbs_to_check.append((db_path, f"{item}/{db_file}"))

found = False
for db_path, db_name in dbs_to_check:
    if not os.path.exists(db_path):
        continue
    
    print(f"  📂 Prüfe: {db_name}")
    result = search_in_db(db_path, db_name)
    
    if result:
        db_path, db_name, view_json, view_name = result
        print(f"\n✅ GEFUNDEN in: {db_name}")
        print(f"   Name: {view_name or 'Unnamed'}")
        
        # Prüfe ob alte Struktur vorhanden
        data = json.loads(view_json)
        has_old_configs = 'dropdown_config' in view_json or 'help_config' in view_json or 'viewtable_config' in view_json
        
        if has_old_configs:
            print(f"   ❌ Hat alte config-Struktur - Migration nötig!")
            print(f"\n📍 Pfad: {db_path}")
        else:
            print(f"   ✅ Bereits neue Struktur")
        
        found = True
        break

if not found:
    print(f"\n❌ View nicht gefunden in keiner Datenbank!")
