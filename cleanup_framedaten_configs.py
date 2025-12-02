"""
CLEANUP: Migriert sys_framedaten zur finalen configs-Struktur

Gleiche Logik wie bei sys_viewdaten:
- dropdown_config/dropdown → configs.dropdown
- help_config → configs.help
- viewtable_config → configs.viewtable
"""
import sqlite3
import json
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s', encoding='utf-8')
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SYSTEM_DB_PATH = os.path.join(BASE_DIR, 'Daten', 'pdvm_system.db')
TEMPLATE_GUID = '55555555-5555-5555-5555-555555555555'


def cleanup_control_configs(control):
    """
    Bereinigt ein Control und bringt es zur finalen configs-Struktur.
    Identische Logik wie bei sys_viewdaten.
    """
    final_configs = control.get('configs', {})
    changed = False
    
    # ========== DROPDOWN ==========
    dropdown_data = None
    
    if 'dropdown_config' in control:
        old = control['dropdown_config']
        if old and (old.get('table') or old.get('key') or old.get('value')):
            dropdown_data = {
                'table': old.get('table', ''),
                'key': old.get('key', ''),
                'feld': old.get('value', ''),
                'gruppe': old.get('gruppe', '')
            }
            changed = True
        del control['dropdown_config']
    
    if 'dropdown' in control and isinstance(control['dropdown'], dict):
        old = control['dropdown']
        if 'table' in old or 'key' in old or 'value' in old:
            dropdown_data = {
                'table': old.get('table', ''),
                'key': old.get('key', ''),
                'feld': old.get('value', ''),
                'gruppe': old.get('gruppe', '')
            }
            changed = True
            del control['dropdown']
    
    if 'dropdown' in final_configs:
        existing = final_configs['dropdown']
        if 'value' in existing and 'feld' not in existing:
            existing['feld'] = existing.pop('value')
            changed = True
        dropdown_data = existing
    
    if dropdown_data:
        final_configs['dropdown'] = dropdown_data
    
    # ========== HELP ==========
    help_data = None
    
    if 'help_config' in control:
        old = control['help_config']
        if old and (old.get('table') or old.get('key') or old.get('value')):
            help_data = {
                'table': old.get('table', ''),
                'key': old.get('key', ''),
                'feld': old.get('value', ''),
                'gruppe': old.get('gruppe', '')
            }
            changed = True
        del control['help_config']
    
    if 'help' in control and isinstance(control['help'], dict):
        old = control['help']
        if 'table' in old or 'key' in old or 'value' in old:
            help_data = {
                'table': old.get('table', ''),
                'key': old.get('key', ''),
                'feld': old.get('value', ''),
                'gruppe': old.get('gruppe', '')
            }
            changed = True
            del control['help']
    
    if 'help' in final_configs:
        existing = final_configs['help']
        if 'value' in existing and 'feld' not in existing:
            existing['feld'] = existing.pop('value')
            changed = True
        help_data = existing
    
    if help_data:
        final_configs['help'] = help_data
    
    # ========== VIEWTABLE ==========
    viewtable_data = None
    
    if 'viewtable_config' in control:
        old = control['viewtable_config']
        if old and old.get('guid'):
            viewtable_data = {
                'table': 'sys_viewdaten',
                'key': old.get('guid', ''),
                'feld': ''
            }
            changed = True
        del control['viewtable_config']
    
    if 'viewtable' in final_configs:
        viewtable_data = final_configs['viewtable']
    
    if viewtable_data:
        final_configs['viewtable'] = viewtable_data
    
    # ========== FINALE STRUKTUR ==========
    if final_configs:
        control['configs'] = final_configs
    elif 'configs' in control and not final_configs:
        del control['configs']
        changed = True
    
    return control, changed


def cleanup_all_frames():
    """Bereinigt alle Frames"""
    logger.info("="*70)
    logger.info("🧹 CLEANUP: sys_framedaten → finale configs-Struktur")
    logger.info("="*70)
    logger.info(f"📂 System-DB: {SYSTEM_DB_PATH}\n")
    
    if not os.path.exists(SYSTEM_DB_PATH):
        logger.error(f"❌ System-DB nicht gefunden!")
        return
    
    conn = sqlite3.connect(SYSTEM_DB_PATH)
    cursor = conn.cursor()
    
    # Prüfe ob sys_framedaten existiert
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sys_framedaten'")
    if not cursor.fetchone():
        logger.warning("⚠️  Tabelle sys_framedaten nicht vorhanden - übersprungen")
        conn.close()
        return
    
    # ALLE Frames laden
    cursor.execute('SELECT uid, daten, name FROM sys_framedaten WHERE uid != ?', (TEMPLATE_GUID,))
    frames = cursor.fetchall()
    
    logger.info(f"📋 Analysiere {len(frames)} Frames...\n")
    
    migrated_count = 0
    controls_fixed = 0
    
    for frame_uid, frame_json, frame_name in frames:
        frame_label = frame_name or frame_uid[:8]
        
        # Schnellcheck: Hat Frame alte configs?
        has_old_configs = ('dropdown_config' in frame_json or 
                          'help_config' in frame_json or 
                          'viewtable_config' in frame_json or
                          '"dropdown": {' in frame_json)  # Auch falsch migrierte
        
        if not has_old_configs:
            logger.info(f"  ⏭️  {frame_label}: Keine alten configs")
            continue
        
        logger.info(f"  🔍 {frame_label}: Hat alte configs - bereinige...")
        
        try:
            data = json.loads(frame_json)
            metadaten = data.get('METADATEN', {})
            
            frame_changed = False
            
            # Durch alle Tabellen iterieren
            for table_key, table_data in metadaten.items():
                if not isinstance(table_data, dict):
                    continue
                
                # controls bereinigen
                if 'controls' in table_data:
                    for control_guid, control_data in table_data['controls'].items():
                        cleaned_control, changed = cleanup_control_configs(control_data)
                        
                        if changed:
                            table_data['controls'][control_guid] = cleaned_control
                            frame_changed = True
                            controls_fixed += 1
                            
                            label = control_data.get('label', control_guid[:8])
                            logger.info(f"    ✅ {label}")
                
                # standard_controls bereinigen
                if 'standard_controls' in table_data:
                    for control_guid, control_data in table_data['standard_controls'].items():
                        cleaned_control, changed = cleanup_control_configs(control_data)
                        
                        if changed:
                            table_data['standard_controls'][control_guid] = cleaned_control
                            frame_changed = True
                            controls_fixed += 1
                            
                            label = control_data.get('label', control_guid[:8])
                            logger.info(f"    ✅ {label}")
            
            if frame_changed:
                # Speichern
                updated_json = json.dumps(data, ensure_ascii=False)
                cursor.execute(
                    'UPDATE sys_framedaten SET daten = ?, modified_at = datetime("now") WHERE uid = ?',
                    (updated_json, frame_uid)
                )
                migrated_count += 1
        
        except Exception as e:
            logger.error(f"  ❌ {frame_label}: Fehler - {e}")
    
    conn.commit()
    conn.close()
    
    logger.info(f"\n{'='*70}")
    logger.info(f"✅ CLEANUP ABGESCHLOSSEN!")
    logger.info(f"  📊 {migrated_count} Frames bereinigt")
    logger.info(f"  🔧 {controls_fixed} Controls korrigiert")
    logger.info(f"{'='*70}")


if __name__ == '__main__':
    cleanup_all_frames()
