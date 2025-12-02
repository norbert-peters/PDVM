"""
Korrigiert DEFAULT_SORT_COLUMN control_type in Template-Daten
GUID: 55555555-5555-5555-5555-555555555555

Läuft OHNE GCS - direkter System-DB Zugriff
"""
import sqlite3
import json
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(message)s', encoding='utf-8')
logger = logging.getLogger(__name__)

# System-DB Pfad ermitteln
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SYSTEM_DB_PATH = os.path.join(BASE_DIR, 'Daten', 'pdvm_system.db')
TEMPLATE_GUID = '55555555-5555-5555-5555-555555555555'

def fix_template():
    """Korrigiert DEFAULT_SORT_COLUMN control_type"""
    logger.info("🔧 Starte Template-Korrektur...")
    logger.info(f"📂 System-DB: {SYSTEM_DB_PATH}")
    
    if not os.path.exists(SYSTEM_DB_PATH):
        logger.error(f"❌ System-DB nicht gefunden: {SYSTEM_DB_PATH}")
        return
    
    # Direkt auf System-DB zugreifen
    conn = sqlite3.connect(SYSTEM_DB_PATH)
    cursor = conn.cursor()
    
    # Template-Daten laden
    cursor.execute('SELECT daten FROM sys_viewdaten WHERE uid = ?', (TEMPLATE_GUID,))
    result = cursor.fetchone()
    
    if not result:
        logger.error(f"❌ Template {TEMPLATE_GUID} nicht gefunden!")
        conn.close()
        return
    
    data = json.loads(result[0])
    if not data:
        logger.error(f"❌ Template {TEMPLATE_GUID} nicht gefunden!")
        return
    
    logger.info(f"✅ Template geladen")
    
    # ROOT_CONTROLS holen
    root_controls = data.get('METADATEN', {}).get('ROOT_CONTROLS', {})
    
    if not root_controls:
        logger.error("❌ ROOT_CONTROLS nicht gefunden!")
        return
    
    # Änderungen vornehmen
    changes_made = False
    
    # 1. DEFAULT_SORT_COLUMN korrigieren
    if 'DEFAULT_SORT_COLUMN' in root_controls:
        old_type = root_controls['DEFAULT_SORT_COLUMN'].get('control_type')
        if old_type == 'checkbox':
            root_controls['DEFAULT_SORT_COLUMN']['control_type'] = 'text'
            logger.info(f"✅ DEFAULT_SORT_COLUMN: checkbox → text")
            changes_made = True
        else:
            logger.info(f"ℹ️  DEFAULT_SORT_COLUMN ist bereits '{old_type}'")
    
    # 2. ROOT leeren (Optional)
    if data.get('ROOT'):
        logger.info(f"ℹ️  ROOT enthält Daten: {list(data['ROOT'].keys())}")
        logger.info(f"   (Template-ROOT sollte leer sein, aber nicht kritisch)")
    
    # Speichern wenn Änderungen
    if changes_made:
        # Direkt in DB speichern
        data['METADATEN']['ROOT_CONTROLS'] = root_controls
        updated_json = json.dumps(data, ensure_ascii=False)
        
        cursor.execute(
            'UPDATE sys_viewdaten SET daten = ?, modified_at = datetime("now") WHERE uid = ?',
            (updated_json, TEMPLATE_GUID)
        )
        conn.commit()
        logger.info(f"💾 Template gespeichert")
    else:
        logger.info(f"ℹ️  Keine Änderungen nötig")
    
    conn.close()
    
    logger.info(f"✅ Fertig!")
    
    # Template-Struktur anzeigen
    logger.info("\n📋 ROOT_CONTROLS Struktur:")
    for key, control in sorted(root_controls.items(), key=lambda x: x[1].get('display_order', 999)):
        control_type = control.get('control_type', '?')
        label = control.get('label', key)
        readonly = '🔒' if control.get('readonly', False) else '✏️'
        muss = '⚠️' if control.get('muss', False) else '  '
        logger.info(f"  {readonly} {muss} {key:25} [{control_type:10}] {label}")

if __name__ == '__main__':
    fix_template()
