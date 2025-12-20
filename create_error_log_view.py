#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Erstellt sys_viewdaten Eintrag für sys_error_log
=================================================

Einmalig ausführen um die interne View für Error-Log zu erstellen
"""

import logging
import sqlite3
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')
logger = logging.getLogger(__name__)

# View-GUID für sys_error_log (fest codiert für interne Verwendung)
ERROR_LOG_VIEW_GUID = 'INTERNAL_ERROR_LOG_VIEW'

def create_error_log_view():
    """Erstellt View-Definition für sys_error_log in sys_viewdaten"""
    
    logger.info("=" * 70)
    logger.info("🔧 Erstelle interne View für sys_error_log")
    logger.info("=" * 70)
    
    # Direkt in SQLite schreiben (pdvm_system.db im Daten-Ordner!)
    db_path = Path(__file__).parent / "Daten" / "pdvm_system.db"
    
    if not db_path.exists():
        logger.error(f"❌ pdvm_system.db nicht gefunden: {db_path}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Prüfe ob sys_viewdaten existiert
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sys_viewdaten'")
    if not cursor.fetchone():
        logger.error("❌ Tabelle sys_viewdaten existiert nicht!")
        conn.close()
        return
    
    # Controls (Spalten) - ALLE relevanten Felder
    controls = [
        'signature',           # Für Deduplication
        'error_type',
        'table_name',
        'record_guid',
        'user_guid',
        'timestamp',
        'last_occurrence',
        'occurrence_count',
        'error_message',
        'severity',
        'context_guid',
        'context_type',
    ]
    
    # Erstelle daten-JSON
    import json
    from datetime import datetime
    
    now_timestamp = float(datetime.now().strftime('%Y%j')) + (datetime.now().hour * 3600 + datetime.now().minute * 60 + datetime.now().second) / 86400
    
    daten = {
        "ROOT": {
            str(now_timestamp): {
                "view_name": "Error Log Internal View",
                "table_name": "sys_error_log",
                "view_type": "internal",
                "description": "Interne View für Error-Log-Manager Pipeline"
            }
        },
        "CONTROLS": {}
    }
    
    logger.info(f"📋 Definiere {len(controls)} Controls:")
    for idx, control in enumerate(controls):
        daten["CONTROLS"][str(now_timestamp)] = daten["CONTROLS"].get(str(now_timestamp), {})
        daten["CONTROLS"][str(now_timestamp)][f"{idx:03d}"] = control
        logger.info(f"  [{idx:03d}] {control}")
    
    # Prüfe ob Eintrag bereits existiert
    cursor.execute("SELECT uid FROM sys_viewdaten WHERE uid = ?", (ERROR_LOG_VIEW_GUID,))
    existing = cursor.fetchone()
    
    if existing:
        # Update
        cursor.execute(
            "UPDATE sys_viewdaten SET daten = ?, modified_at = ? WHERE uid = ?",
            (json.dumps(daten), now_timestamp, ERROR_LOG_VIEW_GUID)
        )
        logger.info("🔄 View-Definition aktualisiert")
    else:
        # Insert
        cursor.execute(
            "INSERT INTO sys_viewdaten (uid, name, daten, modified_at, sec_id) VALUES (?, ?, ?, ?, ?)",
            (ERROR_LOG_VIEW_GUID, 'Error Log Internal View', json.dumps(daten), now_timestamp, None)
        )
        logger.info("✅ View-Definition erstellt")
    
    conn.commit()
    conn.close()
    
    logger.info("")
    logger.info("✅ View-Definition erstellt!")
    logger.info(f"   View-GUID: {ERROR_LOG_VIEW_GUID}")
    logger.info(f"   Tabelle: sys_error_log")
    logger.info(f"   Controls: {len(controls)}")
    logger.info("")
    logger.info("=" * 70)
    logger.info("✅ FERTIG - View kann jetzt von Error-Manager verwendet werden")
    logger.info("=" * 70)


if __name__ == "__main__":
    try:
        create_error_log_view()
    except Exception as e:
        logger.error(f"❌ Fehler: {e}")
        import traceback
        logger.error(traceback.format_exc())
