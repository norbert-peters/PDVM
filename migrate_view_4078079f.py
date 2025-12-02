"""
Migriert spezifische View 4078079f-4028-45ed-879c-3c779ecf3d0d
von alter zu neuer configs-Struktur
"""
import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SYSTEM_DB = os.path.join(BASE_DIR, 'Daten', 'pdvm_system.db')
TARGET_GUID = '4078079f-4028-45ed-879c-3c779ecf3d0d'


def migrate_control(control):
    """Migriert ein Control von alter zu neuer Struktur"""
    configs = {}
    changed = False
    
    # dropdown_config migrieren
    if 'dropdown_config' in control:
        old_config = control['dropdown_config']
        if old_config and old_config.get('table'):
            configs['dropdown'] = {
                'table': old_config.get('table', ''),
                'key': old_config.get('key', ''),
                'feld': old_config.get('value', ''),
                'gruppe': old_config.get('gruppe', '')
            }
            changed = True
        del control['dropdown_config']
    
    # help_config migrieren
    if 'help_config' in control:
        old_config = control['help_config']
        if old_config and old_config.get('table'):
            configs['help'] = {
                'table': old_config.get('table', ''),
                'key': old_config.get('key', ''),
                'feld': old_config.get('value', ''),
                'gruppe': old_config.get('gruppe', '')
            }
            changed = True
        del control['help_config']
    
    # viewtable_config migrieren
    if 'viewtable_config' in control:
        old_config = control['viewtable_config']
        if old_config and old_config.get('guid'):
            configs['viewtable'] = {
                'table': 'sys_viewdaten',
                'key': old_config.get('guid', ''),
                'feld': ''
            }
            changed = True
        del control['viewtable_config']
    
    # Neue Struktur hinzufügen
    if configs:
        control['configs'] = configs
    
    return control, changed


def migrate_specific_view():
    """Migriert spezifische View"""
    print(f"🔧 Migriere View: {TARGET_GUID}")
    print(f"📂 System-DB: {SYSTEM_DB}\n")
    
    if not os.path.exists(SYSTEM_DB):
        print(f"❌ System-DB nicht gefunden!")
        return
    
    conn = sqlite3.connect(SYSTEM_DB)
    cursor = conn.cursor()
    
    # View laden
    cursor.execute('SELECT daten, name FROM sys_viewdaten WHERE uid = ?', (TARGET_GUID,))
    result = cursor.fetchone()
    
    if not result:
        print(f"❌ View nicht gefunden!")
        conn.close()
        return
    
    view_json, view_name = result
    data = json.loads(view_json)
    
    print(f"✅ View geladen: {view_name or 'Unnamed'}")
    
    metadaten = data.get('METADATEN', {})
    total_migrated = 0
    
    # Durch alle Tabellen iterieren
    for table_key, table_data in metadaten.items():
        if not isinstance(table_data, dict):
            continue
        
        print(f"\n📋 Tabelle: {table_key}")
        
        # controls migrieren
        if 'controls' in table_data:
            controls = table_data['controls']
            print(f"  🔹 {len(controls)} Controls gefunden")
            
            for control_guid, control_data in controls.items():
                migrated_control, changed = migrate_control(control_data)
                
                if changed:
                    table_data['controls'][control_guid] = migrated_control
                    total_migrated += 1
                    
                    label = control_data.get('label', control_guid[:8])
                    has_dropdown = 'dropdown' in migrated_control.get('configs', {})
                    has_help = 'help' in migrated_control.get('configs', {})
                    has_viewtable = 'viewtable' in migrated_control.get('configs', {})
                    
                    configs_str = []
                    if has_dropdown:
                        configs_str.append('dropdown')
                    if has_help:
                        configs_str.append('help')
                    if has_viewtable:
                        configs_str.append('viewtable')
                    
                    print(f"    ✅ {label}: {', '.join(configs_str)}")
        
        # standard_controls migrieren
        if 'standard_controls' in table_data:
            std_controls = table_data['standard_controls']
            if std_controls:
                print(f"  🔹 {len(std_controls)} Standard-Controls gefunden")
                
                for control_guid, control_data in std_controls.items():
                    migrated_control, changed = migrate_control(control_data)
                    
                    if changed:
                        table_data['standard_controls'][control_guid] = migrated_control
                        total_migrated += 1
                        
                        label = control_data.get('label', control_guid[:8])
                        print(f"    ✅ {label}: migriert")
    
    # Speichern
    if total_migrated > 0:
        updated_json = json.dumps(data, ensure_ascii=False)
        cursor.execute(
            'UPDATE sys_viewdaten SET daten = ?, modified_at = datetime("now") WHERE uid = ?',
            (updated_json, TARGET_GUID)
        )
        conn.commit()
        
        print(f"\n{'='*70}")
        print(f"✅ MIGRATION ERFOLGREICH!")
        print(f"📊 {total_migrated} Controls migriert")
        print(f"{'='*70}")
    else:
        print(f"\nℹ️  Keine Änderungen nötig")
    
    conn.close()


if __name__ == '__main__':
    migrate_specific_view()
