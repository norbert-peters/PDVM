"""
Prüft welche Datenbank die echten View-Daten hat
"""
import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SYSTEM_DB = os.path.join(BASE_DIR, 'Daten', 'pdvm_system.db')
MANDANT_DB = os.path.join(BASE_DIR, 'Daten', 'datenbank.db')

def check_db(db_path, db_name):
    print(f"\n{'='*70}")
    print(f"📂 {db_name}: {db_path}")
    print(f"{'='*70}")
    
    if not os.path.exists(db_path):
        print(f"❌ Nicht gefunden!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Prüfe ob sys_viewdaten existiert
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sys_viewdaten'")
    if not cursor.fetchone():
        print(f"❌ Tabelle sys_viewdaten nicht vorhanden")
        conn.close()
        return
    
    # Hole alle Views
    cursor.execute("SELECT uid, name FROM sys_viewdaten WHERE uid != '55555555-5555-5555-5555-555555555555' AND historisch = 0")
    views = cursor.fetchall()
    
    print(f"📋 Gefunden: {len(views)} Views\n")
    
    for view_uid, view_name in views:
        cursor.execute("SELECT daten FROM sys_viewdaten WHERE uid = ?", (view_uid,))
        result = cursor.fetchone()
        
        if result:
            data = json.loads(result[0])
            metadaten = data.get('METADATEN', {})
            
            # Prüfe ersten Control auf alte Struktur
            for table_key, table_data in metadaten.items():
                if isinstance(table_data, dict) and 'controls' in table_data:
                    controls = table_data['controls']
                    if controls:
                        first_control_key = list(controls.keys())[0]
                        first_control = controls[first_control_key]
                        
                        has_old_dropdown = 'dropdown_config' in first_control
                        has_old_help = 'help_config' in first_control
                        has_old_viewtable = 'viewtable_config' in first_control
                        has_new_configs = 'configs' in first_control
                        
                        status = "❌ ALTE STRUKTUR" if (has_old_dropdown or has_old_help or has_old_viewtable) else "✅ NEUE STRUKTUR"
                        
                        print(f"  {status}: {view_name or view_uid[:8]}")
                        if has_old_dropdown:
                            print(f"    → hat 'dropdown_config'")
                        if has_old_help:
                            print(f"    → hat 'help_config'")
                        if has_old_viewtable:
                            print(f"    → hat 'viewtable_config'")
                        if has_new_configs:
                            print(f"    → hat 'configs' ✅")
                        
                        break
                break
    
    conn.close()

check_db(SYSTEM_DB, "System-DB (pdvm_system.db)")
check_db(MANDANT_DB, "Mandanten-DB (datenbank.db)")
