"""
Detaillierte Analyse der View-Struktur
"""
import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SYSTEM_DB = os.path.join(BASE_DIR, 'Daten', 'pdvm_system.db')

conn = sqlite3.connect(SYSTEM_DB)
cursor = conn.cursor()

# Persondaten View analysieren (mit den Beispiel-Daten die du gezeigt hast)
cursor.execute("SELECT uid, name, daten FROM sys_viewdaten WHERE name LIKE '%person%' AND historisch = 0 LIMIT 1")
result = cursor.fetchone()

if result:
    view_uid, view_name, view_json = result
    print(f"📋 View: {view_name} ({view_uid})")
    print("="*70)
    
    data = json.loads(view_json)
    metadaten = data.get('METADATEN', {})
    
    for table_key, table_data in metadaten.items():
        if not isinstance(table_data, dict):
            continue
            
        print(f"\n🔑 Tabelle: {table_key}")
        
        if 'controls' in table_data:
            controls = table_data['controls']
            print(f"  📦 {len(controls)} Controls gefunden\n")
            
            # Ersten Control detailliert analysieren
            for control_guid, control_data in list(controls.items())[:2]:
                print(f"  Control GUID: {control_guid[:20]}...")
                print(f"    label: {control_data.get('label', 'N/A')}")
                print(f"    type: {control_data.get('type', 'N/A')}")
                
                # Alte Struktur prüfen
                if 'dropdown_config' in control_data:
                    print(f"    ❌ dropdown_config: {control_data['dropdown_config']}")
                if 'help_config' in control_data:
                    print(f"    ❌ help_config: {control_data['help_config']}")
                if 'viewtable_config' in control_data:
                    print(f"    ❌ viewtable_config: {control_data['viewtable_config']}")
                
                # Neue Struktur prüfen
                if 'configs' in control_data:
                    print(f"    ✅ configs: {control_data['configs']}")
                
                print()

conn.close()
