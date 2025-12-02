"""
Zeigt alle Controls der persondaten View
"""
import sqlite3
import json

conn = sqlite3.connect('Daten/pdvm_system.db')
cursor = conn.cursor()

cursor.execute('SELECT daten FROM sys_viewdaten WHERE uid = ?', ('0d10a0d0-b1a5-4544-b284-e8a09ca979b5',))
data = json.loads(cursor.fetchone()[0])

print("📋 Alle Controls in PERSONDATEN:")
print("="*100)

controls = data['METADATEN']['PERSONDATEN']['controls']

for control_guid, control in controls.items():
    feld = control.get('feld', 'N/A')
    label = control.get('label', 'N/A')
    has_configs = 'configs' in control
    has_old_dropdown = 'dropdown' in control and isinstance(control.get('dropdown'), dict) and control['dropdown']
    has_old_dropdown_config = 'dropdown_config' in control
    
    status = "✅ configs" if has_configs else "❌ keine configs"
    if has_old_dropdown:
        status += " | ⚠️ dropdown (alt)"
    if has_old_dropdown_config:
        status += " | ⚠️ dropdown_config (alt)"
    
    print(f"{feld:20} | {label:30} | {status}")
    
    # Zeige Control mit ANREDE oder ANSCHRIFT im Detail
    if feld.upper() in ['ANREDE', 'ANSCHRIFT']:
        print(f"\n  🔍 Detail für {feld}:")
        print(f"  GUID: {control_guid}")
        print(f"  Struktur:")
        print(json.dumps(control, indent=4, ensure_ascii=False))
        print()

conn.close()
