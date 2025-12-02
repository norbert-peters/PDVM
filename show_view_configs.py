"""
Zeigt alle Views mit ihrer configs-Struktur
"""
import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SYSTEM_DB = os.path.join(BASE_DIR, 'Daten', 'pdvm_system.db')
TEMPLATE_GUID = '55555555-5555-5555-5555-555555555555'

conn = sqlite3.connect(SYSTEM_DB)
cursor = conn.cursor()

# Alle Views laden
cursor.execute('SELECT uid, name, daten FROM sys_viewdaten WHERE uid != ? AND historisch = 0', (TEMPLATE_GUID,))
views = cursor.fetchall()

print(f"📋 Views in pdvm_system.db:\n")
print("="*70)

for view_uid, view_name, view_json in views:
    data = json.loads(view_json)
    metadaten = data.get('METADATEN', {})
    
    print(f"\n🔑 GUID: {view_uid}")
    print(f"📌 Name: {view_name or 'Unnamed'}")
    
    # Prüfe ob View Controls hat
    has_controls = False
    for table_key, table_data in metadaten.items():
        if isinstance(table_data, dict) and 'controls' in table_data:
            controls = table_data['controls']
            if controls:
                has_controls = True
                print(f"\n   Tabelle: {table_key}")
                print(f"   Controls: {len(controls)}")
                
                # Zeige ersten Control mit Struktur
                first_control_key = list(controls.keys())[0]
                first_control = controls[first_control_key]
                
                print(f"\n   Beispiel-Control (GUID: {first_control_key[:20]}...):")
                print(f"     label: {first_control.get('label', 'N/A')}")
                print(f"     type: {first_control.get('type', 'N/A')}")
                
                # Zeige configs wenn vorhanden
                if 'configs' in first_control:
                    print(f"     ✅ configs: {json.dumps(first_control['configs'], indent=8, ensure_ascii=False)}")
                else:
                    print(f"     ❌ Keine 'configs' vorhanden")
                
                # Zeige alte Struktur wenn vorhanden
                if 'dropdown_config' in first_control:
                    print(f"     ⚠️  dropdown_config: {first_control['dropdown_config']}")
                if 'help_config' in first_control:
                    print(f"     ⚠️  help_config: {first_control['help_config']}")
                if 'viewtable_config' in first_control:
                    print(f"     ⚠️  viewtable_config: {first_control['viewtable_config']}")
                
                break
    
    if not has_controls:
        print(f"   ℹ️  Keine Controls vorhanden")
    
    print("-"*70)

conn.close()
