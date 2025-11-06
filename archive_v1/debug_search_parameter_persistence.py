#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Debug-Tool für SearchParameter Persistierung
Testet, ob Filter korrekt in anwendungsdaten gespeichert werden
"""

import logging
import sys
import os

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('main.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def debug_persistence():
    """Debug SearchParameter Persistierung"""
    try:
        logger.info("🔍 === DEBUGGING SEARCH PARAMETER PERSISTIERUNG ===")
        
        # GCS importieren
        from pdvm_central_systemsteuerung import get_gcs
        gcs = get_gcs()
        
        if not gcs:
            logger.error("❌ GCS nicht verfügbar!")
            return
        
        if not hasattr(gcs, '_app_db') or not gcs._app_db:
            logger.error("❌ APP-DB nicht verfügbar!")
            return
            
        logger.info("✅ GCS und APP-DB verfügbar")
        
        # Test-View-GUID
        view_guid = "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"
        logger.info(f"📂 Test View-GUID: {view_guid}")
        
        # Alle gespeicherten Keys für diese View anzeigen
        logger.info("\n🔍 AKTUELLE DATEN IN ANWENDUNGSDATEN:")
        possible_fields = ['familienname_show', 'vorname_show', 'anrede_show', 'geburtsdatum_show', 'geburtsdatum_alter_show', 'uid_show']
        
        found_data = False
        for field_key in possible_fields:
            field_data, timestamp = gcs._app_db.get_value(view_guid, field_key) or (None, None)
            if field_data:
                found_data = True
                logger.info(f"  📥 {field_key}: {field_data} (Timestamp: {timestamp})")
            else:
                logger.info(f"  ❌ {field_key}: Keine Daten")
        
        if not found_data:
            logger.info("❌ KEINE PERSISTENTEN DATEN GEFUNDEN!")
        
        # Teste manuelles Speichern
        logger.info("\n🧪 TESTE MANUELLES SPEICHERN:")
        test_data = {
            'simple_search': 'TEST_WERT_DEBUG',
            'conditions': []
        }
        
        test_field = 'familienname_show'
        logger.info(f"💾 Speichere Test-Daten für {test_field}: {test_data}")
        
        gcs._app_db.set_value(view_guid, test_field, test_data)
        gcs._app_db.save_all_values()
        
        # Sofort wieder auslesen
        read_data, read_timestamp = gcs._app_db.get_value(view_guid, test_field) or (None, None)
        if read_data:
            logger.info(f"✅ ERFOLGREICH: {test_field} = {read_data}")
        else:
            logger.error(f"❌ FAILED: Konnte {test_field} nicht auslesen!")
            
        logger.info("\n🔍 DATABASE-FILE PRÜFUNG:")
        try:
            import sqlite3
            # Suche die anwendungsdaten.db Datei
            db_files = []
            for root, dirs, files in os.walk('.'):
                for file in files:
                    if 'anwendungsdaten' in file.lower() and file.endswith('.db'):
                        db_files.append(os.path.join(root, file))
            
            logger.info(f"📂 Gefundene DB-Dateien: {db_files}")
            
            for db_file in db_files:
                if os.path.exists(db_file):
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    
                    # Tabellen anzeigen
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    logger.info(f"📊 Tabellen in {db_file}: {tables}")
                    
                    # Suche nach view_guid Daten
                    for table_name, in tables:
                        try:
                            cursor.execute(f"SELECT * FROM {table_name} WHERE view_guid LIKE '%0d10a0d0%' LIMIT 5")
                            rows = cursor.fetchall()
                            if rows:
                                logger.info(f"  🔍 Daten in {table_name}: {len(rows)} Zeilen")
                                for row in rows[:2]:  # Nur erste 2 zeigen
                                    logger.info(f"    📄 {row}")
                        except Exception as e:
                            logger.debug(f"  ⚠️ Konnte {table_name} nicht lesen: {e}")
                    
                    conn.close()
                    
        except Exception as e:
            logger.warning(f"⚠️ Database-Prüfung fehlgeschlagen: {e}")
            
    except Exception as e:
        logger.error(f"❌ Debug fehlgeschlagen: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    debug_persistence()