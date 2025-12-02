"""
Migration: dropdown_config/help_config/viewtable_config → configs Structure
Universelle Config-Struktur für View- und Frame-Daten

NEUE STRUKTUR:
"configs": {
  "dropdown": {"table": "...", "key": "...", "feld": "...", "gruppe": "..."},
  "help": {"table": "...", "key": "...", "feld": "...", "gruppe": "..."},
  "viewtable": {"table": "...", "key": "...", "feld": "..."}
}
"""
import sqlite3
import json
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(message)s', encoding='utf-8')
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SYSTEM_DB_PATH = os.path.join(BASE_DIR, 'Daten', 'pdvm_system.db')
TEMPLATE_GUID = '55555555-5555-5555-5555-555555555555'


def migrate_control_to_configs(control):
    """
    Migriert ein einzelnes Control von alter zu neuer Struktur.
    
    ALT:
    - dropdown_config: {table, key, value}
    - dropdown: {table, key, value}  (auch diese Variante!)
    - help_config: {table, key, value}
    - viewtable_config: {guid}
    
    NEU:
    - configs: {
        dropdown: {table, key, feld, gruppe},
        help: {table, key, feld, gruppe},
        viewtable: {table, key, feld}
      }
    """
    configs = control.get('configs', {})
    changed = False
    
    # dropdown_config migrieren (Variante 1)
    if 'dropdown_config' in control:
        old_config = control['dropdown_config']
        if old_config and old_config.get('table'):
            configs['dropdown'] = {
                'table': old_config.get('table', ''),
                'key': old_config.get('key', ''),
                'feld': old_config.get('value', ''),  # value → feld
                'gruppe': old_config.get('gruppe', '')
            }
            changed = True
        del control['dropdown_config']
    
    # dropdown migrieren (Variante 2 - OHNE _config)
    if 'dropdown' in control and isinstance(control['dropdown'], dict):
        old_config = control['dropdown']
        # Nur wenn es ein Config-Dict ist (nicht wenn es schon unter configs steht)
        if 'table' in old_config or 'key' in old_config or 'value' in old_config:
            configs['dropdown'] = {
                'table': old_config.get('table', ''),
                'key': old_config.get('key', ''),
                'feld': old_config.get('value', ''),  # value → feld
                'gruppe': old_config.get('gruppe', '')
            }
            changed = True
            del control['dropdown']
    
    # help_config migrieren
    if 'help_config' in control:
        old_config = control['help_config']
        if old_config and old_config.get('table'):
            configs['help'] = {
                'table': old_config.get('table', ''),
                'key': old_config.get('key', ''),
                'feld': old_config.get('value', ''),  # value → feld
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
    
    # Neue Struktur setzen
    if configs:
        control['configs'] = configs
    
    return control, changed


def update_template_structure():
    """Aktualisiert Template-TEMPLATES mit configs-Struktur"""
    logger.info("🔧 Schritt 1: Template-Struktur aktualisieren...")
    logger.info(f"📂 System-DB: {SYSTEM_DB_PATH}")
    
    if not os.path.exists(SYSTEM_DB_PATH):
        logger.error(f"❌ System-DB nicht gefunden: {SYSTEM_DB_PATH}")
        return False
    
    conn = sqlite3.connect(SYSTEM_DB_PATH)
    cursor = conn.cursor()
    
    # Template laden
    cursor.execute('SELECT daten FROM sys_viewdaten WHERE uid = ?', (TEMPLATE_GUID,))
    result = cursor.fetchone()
    
    if not result:
        logger.error(f"❌ Template {TEMPLATE_GUID} nicht gefunden!")
        conn.close()
        return False
    
    data = json.loads(result[0])
    templates = data.get('METADATEN', {}).get('TEMPLATES', {})
    
    if not templates:
        logger.error("❌ TEMPLATES nicht gefunden!")
        conn.close()
        return False
    
    logger.info(f"✅ Template geladen mit {len(templates)} Templates")
    
    # Templates aktualisieren
    for template_name, template_data in templates.items():
        # Alte dropdown_config Struktur entfernen und durch configs ersetzen
        if 'dropdown_config' in template_data or 'dropdown' in template_data:
            # Neue configs Struktur
            template_data['configs'] = {
                'dropdown': {
                    'table': '',
                    'key': '',
                    'feld': '',
                    'gruppe': ''
                },
                'help': {
                    'table': '',
                    'key': '',
                    'feld': '',
                    'gruppe': ''
                },
                'viewtable': {
                    'table': '',
                    'key': '',
                    'feld': ''
                }
            }
            # Alte Keys entfernen
            template_data.pop('dropdown_config', None)
            template_data.pop('dropdown', None)
            
            logger.info(f"  ✅ {template_name}: configs-Struktur hinzugefügt")
    
    # CONTROL_PROPERTIES erweitern mit configs
    control_props = data.get('METADATEN', {}).get('CONTROL_PROPERTIES', {})
    if control_props:
        # configs Property hinzufügen
        if 'configs' not in control_props:
            control_props['configs'] = {
                'label': 'Konfigurationen',
                'control_type': 'json',  # Spezial-Editor für nested structure
                'display_order': 50
            }
            logger.info(f"  ✅ CONTROL_PROPERTIES: configs Property hinzugefügt")
    
    # Speichern
    data['METADATEN']['TEMPLATES'] = templates
    data['METADATEN']['CONTROL_PROPERTIES'] = control_props
    
    updated_json = json.dumps(data, ensure_ascii=False)
    cursor.execute(
        'UPDATE sys_viewdaten SET daten = ?, modified_at = datetime("now") WHERE uid = ?',
        (updated_json, TEMPLATE_GUID)
    )
    conn.commit()
    conn.close()
    
    logger.info("✅ Template-Struktur aktualisiert!")
    return True


def migrate_all_view_data():
    """Migriert alle View-Daten zur neuen configs-Struktur"""
    logger.info("\n🔧 Schritt 2: Migriere View-Daten...")
    logger.info(f"📂 System-DB: {SYSTEM_DB_PATH}")
    
    if not os.path.exists(SYSTEM_DB_PATH):
        logger.error(f"❌ System-DB nicht gefunden: {SYSTEM_DB_PATH}")
        return False
    
    conn = sqlite3.connect(SYSTEM_DB_PATH)
    cursor = conn.cursor()
    
    # ALLE View-Daten laden (auch historische, um nichts zu verpassen)
    cursor.execute(
        'SELECT uid, daten, name FROM sys_viewdaten WHERE uid != ?',
        (TEMPLATE_GUID,)
    )
    views = cursor.fetchall()
    
    logger.info(f"📋 Gefunden: {len(views)} Views zu analysieren\n")
    
    migrated_count = 0
    error_count = 0
    skipped_count = 0
    
    for view_uid, view_json, view_name in views:
        view_label = view_name or view_uid[:8]
        
        # Schnellcheck: Hat View überhaupt alte Configs?
        has_old_configs = ('dropdown_config' in view_json or 
                          'help_config' in view_json or 
                          'viewtable_config' in view_json)
        
        if not has_old_configs:
            skipped_count += 1
            logger.info(f"  ⏭️  {view_label}: Keine alten configs")
            continue
        
        logger.info(f"  🔍 {view_label}: Hat alte configs - migriere...")
        try:
            data = json.loads(view_json)
            metadaten = data.get('METADATEN', {})
            
            if not metadaten:
                continue
            
            view_changed = False
            
            # Durch alle Tabellen iterieren (z.B. PERSONDATEN, FINANZDATEN)
            for table_key, table_data in metadaten.items():
                if not isinstance(table_data, dict):
                    continue
                
                # controls migrieren
                if 'controls' in table_data:
                    for control_guid, control_data in table_data['controls'].items():
                        migrated_control, changed = migrate_control_to_configs(control_data)
                        table_data['controls'][control_guid] = migrated_control
                        if changed:
                            view_changed = True
                
                # standard_controls migrieren
                if 'standard_controls' in table_data:
                    for control_guid, control_data in table_data['standard_controls'].items():
                        migrated_control, changed = migrate_control_to_configs(control_data)
                        table_data['standard_controls'][control_guid] = migrated_control
                        if changed:
                            view_changed = True
            
            if view_changed:
                # Speichern
                updated_json = json.dumps(data, ensure_ascii=False)
                cursor.execute(
                    'UPDATE sys_viewdaten SET daten = ?, modified_at = datetime("now") WHERE uid = ?',
                    (updated_json, view_uid)
                )
                migrated_count += 1
                logger.info(f"  ✅ {view_name or view_uid[:8]}: Migriert")
        
        except Exception as e:
            error_count += 1
            logger.error(f"  ❌ {view_name or view_uid[:8]}: Fehler - {e}")
    
    conn.commit()
    conn.close()
    
    logger.info(f"\n{'='*70}")
    logger.info(f"✅ Migration abgeschlossen:")
    logger.info(f"  📊 Migriert: {migrated_count} Views")
    logger.info(f"  ⏭️  Übersprungen: {skipped_count} Views (bereits neue Struktur)")
    logger.info(f"  ❌ Fehler: {error_count} Views")
    logger.info(f"{'='*70}")
    
    return True


def main():
    """Führt vollständige Migration durch"""
    logger.info("=" * 70)
    logger.info("🚀 MIGRATION: configs-Struktur Universal")
    logger.info("=" * 70)
    
    # Schritt 1: Template aktualisieren
    if not update_template_structure():
        logger.error("❌ Template-Update fehlgeschlagen!")
        return
    
    # Schritt 2: View-Daten migrieren
    if not migrate_all_view_data():
        logger.error("❌ View-Migration fehlgeschlagen!")
        return
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ MIGRATION ERFOLGREICH ABGESCHLOSSEN!")
    logger.info("=" * 70)
    logger.info("\n📋 Nächste Schritte:")
    logger.info("  1. Editor-Logik erweitern für configs-Pflege")
    logger.info("  2. Input-Controls anpassen (lesen aus configs)")
    logger.info("  3. Anwendung neu starten und testen")


if __name__ == '__main__':
    main()
