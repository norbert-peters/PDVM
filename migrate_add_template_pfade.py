"""
Migration: PFADE in Template (55555...) hinzufügen

Fügt METADATEN.PFADE in sys_viewdaten und sys_framedaten Templates ein.
OHNE GCS - direkter SQLite-Zugriff!
"""

import logging
import sqlite3
import json

logging.basicConfig(level=logging.INFO, format='%(message)s', encoding='utf-8')
logger = logging.getLogger(__name__)

DB_PATH = r'c:\Users\norbe\OneDrive\Dokumente\MyApplication\Daten\pdvm_system.db'

def migrate_template_pfade():
    """Fügt PFADE in Templates hinzu"""
    
    template_guid = '55555555-5555-5555-5555-555555555555'
    
    # Verbindung öffnen
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # sys_viewdaten Template
    logger.info("=" * 80)
    logger.info("🔧 Migration: PFADE in sys_viewdaten Template")
    logger.info("=" * 80)
    
    # Daten lesen
    cursor.execute(
        "SELECT daten FROM sys_viewdaten WHERE uid = ?",
        (template_guid,)
    )
    row = cursor.fetchone()
    
    if not row:
        logger.error(f"❌ Template nicht gefunden: {template_guid}")
        conn.close()
        return
    
    data = json.loads(row[0])
    
    if 'METADATEN' not in data:
        data['METADATEN'] = {}
    
    # PFADE hinzufügen
    data['METADATEN']['PFADE'] = {
        'normal': '{ROOT_TABLE}.controls',
        'standard': '{ROOT_TABLE}.standard_controls',
        'template': 'TEMPLATES'
    }
    
    logger.info("✅ PFADE hinzugefügt:")
    for mode, pfad in data['METADATEN']['PFADE'].items():
        logger.info(f"   {mode}: {pfad}")
    
    # Speichern
    cursor.execute(
        "UPDATE sys_viewdaten SET daten = ? WHERE uid = ?",
        (json.dumps(data, ensure_ascii=False), template_guid)
    )
    conn.commit()
    logger.info("💾 sys_viewdaten Template gespeichert")
    
    # sys_framedaten Template
    logger.info("")
    logger.info("=" * 80)
    logger.info("🔧 Migration: PFADE in sys_framedaten Template")
    logger.info("=" * 80)
    
    # Daten lesen
    cursor.execute(
        "SELECT daten FROM sys_framedaten WHERE uid = ?",
        (template_guid,)
    )
    row = cursor.fetchone()
    
    if not row:
        logger.error(f"❌ Template nicht gefunden: {template_guid}")
        conn.close()
        return
    
    data = json.loads(row[0])
    
    if 'METADATEN' not in data:
        data['METADATEN'] = {}
    
    # PFADE hinzufügen (für Frames gleiche Struktur)
    data['METADATEN']['PFADE'] = {
        'normal': '{ROOT_TABLE}.controls',
        'standard': '{ROOT_TABLE}.standard_controls',
        'template': 'TEMPLATES'
    }
    
    logger.info("✅ PFADE hinzugefügt:")
    for mode, pfad in data['METADATEN']['PFADE'].items():
        logger.info(f"   {mode}: {pfad}")
    
    # Speichern
    cursor.execute(
        "UPDATE sys_framedaten SET daten = ? WHERE uid = ?",
        (json.dumps(data, ensure_ascii=False), template_guid)
    )
    conn.commit()
    logger.info("💾 sys_framedaten Template gespeichert")
    
    # Verbindung schließen
    conn.close()
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("✅ Migration abgeschlossen!")
    logger.info("=" * 80)

if __name__ == '__main__':
    migrate_template_pfade()
