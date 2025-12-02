"""
CLEANUP: Migriert ALLE config-Varianten zur finalen configs-Struktur

ALTE VARIANTEN (werden alle bereinigt):
1. "dropdown_config": {table, key, value}
2. "dropdown": {table, key, value}  (falsch migriert)
3. "help_config": {table, key, value}
4. "viewtable_config": {guid}

FINALE STRUKTUR:
"configs": {
  "dropdown": {table, key, feld, gruppe},
  "help": {table, key, feld, gruppe},
  "viewtable": {table, key, feld}
}
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
    
    LOGIK:
    1. Sammle alle config-Daten aus allen Varianten
    2. Lösche alle alten Keys
    3. Setze nur noch "configs" mit korrekter Struktur
    """
    # Finale configs sammeln
    final_configs = control.get('configs', {})
    changed = False
    
    # ========== DROPDOWN ==========
    dropdown_data = None
    
    # Variante 1: dropdown_config
    if 'dropdown_config' in control:
        old = control['dropdown_config']
        if old and (old.get('table') or old.get('key') or old.get('value')):
            dropdown_data = {
                'table': old.get('table', ''),
                'key': old.get('key', ''),
                'feld': old.get('value', ''),  # value → feld
                'gruppe': old.get('gruppe', '')
            }
            changed = True
        del control['dropdown_config']
    
    # Variante 2: dropdown (falsch migriert)
    if 'dropdown' in control and isinstance(control['dropdown'], dict):
        old = control['dropdown']
        # Prüfe ob es ein Config-Dict ist (hat table/key/value)
        if 'table' in old or 'key' in old or 'value' in old:
            dropdown_data = {
                'table': old.get('table', ''),
                'key': old.get('key', ''),
                'feld': old.get('value', ''),  # value → feld
                'gruppe': old.get('gruppe', '')
            }
            changed = True
            del control['dropdown']
    
    # Variante 3: configs.dropdown bereits vorhanden (korrekt)
    if 'dropdown' in final_configs:
        # Übernehmen, aber sicherstellen dass "feld" statt "value"
        existing = final_configs['dropdown']
        if 'value' in existing and 'feld' not in existing:
            existing['feld'] = existing.pop('value')
            changed = True
        dropdown_data = existing
    
    # Dropdown in finale Struktur übernehmen
    if dropdown_data:
        final_configs['dropdown'] = dropdown_data
    
    # ========== HELP ==========
    help_data = None
    
    # Variante 1: help_config
    if 'help_config' in control:
        old = control['help_config']
        if old and (old.get('table') or old.get('key') or old.get('value')):
            help_data = {
                'table': old.get('table', ''),
                'key': old.get('key', ''),
                'feld': old.get('value', ''),  # value → feld
                'gruppe': old.get('gruppe', '')
            }
            changed = True
        del control['help_config']
    
    # Variante 2: help (falsch migriert - unwahrscheinlich aber möglich)
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
    
    # Variante 3: configs.help bereits vorhanden
    if 'help' in final_configs:
        existing = final_configs['help']
        if 'value' in existing and 'feld' not in existing:
            existing['feld'] = existing.pop('value')
            changed = True
        help_data = existing
    
    # Help in finale Struktur übernehmen
    if help_data:
        final_configs['help'] = help_data
    
    # ========== VIEWTABLE ==========
    viewtable_data = None
    
    # Variante 1: viewtable_config
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
    
    # Variante 2: configs.viewtable bereits vorhanden
    if 'viewtable' in final_configs:
        viewtable_data = final_configs['viewtable']
    
    # Viewtable in finale Struktur übernehmen
    if viewtable_data:
        final_configs['viewtable'] = viewtable_data
    
    # ========== FINALE STRUKTUR SETZEN ==========
    if final_configs:
        control['configs'] = final_configs
    elif 'configs' in control and not final_configs:
        # Leere configs entfernen
        del control['configs']
        changed = True
    
    return control, changed


def cleanup_all_views():
    """Bereinigt alle Views"""
    logger.info("="*70)
    logger.info("🧹 CLEANUP: Finale configs-Struktur")
    logger.info("="*70)
    logger.info(f"📂 System-DB: {SYSTEM_DB_PATH}\n")
    
    if not os.path.exists(SYSTEM_DB_PATH):
        logger.error(f"❌ System-DB nicht gefunden!")
        return
    
    conn = sqlite3.connect(SYSTEM_DB_PATH)
    cursor = conn.cursor()
    
    # ALLE Views laden
    cursor.execute('SELECT uid, daten, name FROM sys_viewdaten WHERE uid != ?', (TEMPLATE_GUID,))
    views = cursor.fetchall()
    
    logger.info(f"📋 Analysiere {len(views)} Views...\n")
    
    migrated_count = 0
    controls_fixed = 0
    
    for view_uid, view_json, view_name in views:
        view_label = view_name or view_uid[:8]
        
        try:
            data = json.loads(view_json)
            metadaten = data.get('METADATEN', {})
            
            view_changed = False
            
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
                            view_changed = True
                            controls_fixed += 1
                
                # standard_controls bereinigen
                if 'standard_controls' in table_data:
                    for control_guid, control_data in table_data['standard_controls'].items():
                        cleaned_control, changed = cleanup_control_configs(control_data)
                        
                        if changed:
                            table_data['standard_controls'][control_guid] = cleaned_control
                            view_changed = True
                            controls_fixed += 1
            
            if view_changed:
                # Speichern
                updated_json = json.dumps(data, ensure_ascii=False)
                cursor.execute(
                    'UPDATE sys_viewdaten SET daten = ?, modified_at = datetime("now") WHERE uid = ?',
                    (updated_json, view_uid)
                )
                migrated_count += 1
                logger.info(f"  ✅ {view_label}: Bereinigt")
        
        except Exception as e:
            logger.error(f"  ❌ {view_label}: Fehler - {e}")
    
    conn.commit()
    conn.close()
    
    logger.info(f"\n{'='*70}")
    logger.info(f"✅ CLEANUP ABGESCHLOSSEN!")
    logger.info(f"  📊 {migrated_count} Views bereinigt")
    logger.info(f"  🔧 {controls_fixed} Controls korrigiert")
    logger.info(f"{'='*70}")


if __name__ == '__main__':
    cleanup_all_views()
