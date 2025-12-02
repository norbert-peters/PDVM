"""
Cleanup: Entfernt PFADE und setzt ROOT.TABLE in Templates
"""

import sqlite3
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

DB_PATH = r"c:\Users\norbe\OneDrive\Dokumente\MyApplication\Daten\pdvm_system.db"
TEMPLATE_GUID = "55555555-5555-5555-5555-555555555555"

def cleanup_templates():
    """Bereinigt Templates: Entfernt PFADE, setzt ROOT.TABLE"""
    
    logger.info("="*80)
    logger.info("🔧 CLEANUP: Templates bereinigen")
    logger.info("="*80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tables = ['sys_viewdaten', 'sys_framedaten', 'sys_menudaten', 
              'sys_dialogdaten', 'sys_dropdowndaten', 'sys_beschreibungen']
    
    for table_name in tables:
        logger.info(f"\n📋 {table_name}")
        
        # Template laden
        cursor.execute(f"SELECT daten FROM {table_name} WHERE uid = ?", (TEMPLATE_GUID,))
        row = cursor.fetchone()
        
        if not row:
            logger.info("   ⚠️  Kein Template vorhanden")
            continue
        
        data = json.loads(row[0])
        changed = False
        
        # 1. PFADE entfernen (nicht mehr benötigt)
        if 'PFADE' in data:
            del data['PFADE']
            logger.info("   ✅ PFADE entfernt")
            changed = True
        
        # 2. ROOT.TABLE setzen falls nicht vorhanden
        if 'ROOT' not in data:
            data['ROOT'] = {}
        
        if 'TABLE' not in data['ROOT'] or not data['ROOT']['TABLE']:
            # Standard-Tabellenname ableiten
            default_table = {
                'sys_viewdaten': 'sys_viewdaten',
                'sys_framedaten': 'sys_framedaten',
                'sys_menudaten': 'sys_menudaten',
                'sys_dialogdaten': 'sys_dialogdaten',
                'sys_dropdowndaten': 'sys_dropdowndaten',
                'sys_beschreibungen': 'sys_beschreibungen'
            }.get(table_name, table_name)
            
            data['ROOT']['TABLE'] = default_table
            logger.info(f"   ✅ ROOT.TABLE = '{default_table}'")
            changed = True
        
        # Speichern
        if changed:
            cursor.execute(
                f"UPDATE {table_name} SET daten = ? WHERE uid = ?",
                (json.dumps(data, ensure_ascii=False, indent=2), TEMPLATE_GUID)
            )
            logger.info("   💾 Gespeichert")
        else:
            logger.info("   ✓  Keine Änderungen nötig")
    
    conn.commit()
    conn.close()
    
    logger.info("\n" + "="*80)
    logger.info("✅ CLEANUP ABGESCHLOSSEN")
    logger.info("="*80)


if __name__ == '__main__':
    cleanup_templates()
