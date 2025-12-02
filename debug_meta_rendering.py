"""
Debug-Skript: META-Daten und Rendering-Mode prüfen
"""

import sqlite3
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_meta_data():
    """Prüft META-Daten in der Datenbank"""
    
    # User-GUID (Demo-User)
    user_guid = "4886ad26-061b-4662-a762-c8c83f36692d"
    
    conn = sqlite3.connect('Daten/datenbank.db')
    cursor = conn.cursor()
    
    # Tabelle mit User-GUID (mit Backticks escapen!)
    table_name = f"`sys_menudaten_{user_guid}`"
    
    logger.info(f"🔍 Prüfe Tabelle: {table_name}")
    
    # Alle META-Einträge holen
    cursor.execute(f"""
        SELECT gruppe, feldname, wert 
        FROM {table_name}
        WHERE gruppe = 'META'
        ORDER BY feldname
    """)
    
    results = cursor.fetchall()
    
    if not results:
        logger.warning("⚠️ KEINE META-Einträge gefunden!")
    else:
        logger.info(f"✅ {len(results)} META-Einträge gefunden:")
        for gruppe, feldname, wert in results:
            logger.info(f"  📋 META[{feldname}] = {wert}")
            
            # JSON parsen
            try:
                if wert and wert.strip():
                    data = json.loads(wert)
                    logger.info(f"      → rendering: {data.get('rendering', 'NICHT GESETZT')}")
                else:
                    logger.warning(f"      → LEER oder WHITESPACE!")
            except json.JSONDecodeError as e:
                logger.error(f"      → JSON-Fehler: {e}")
    
    # GRUND-Gruppe prüfen
    cursor.execute(f"""
        SELECT gruppe, feldname, wert 
        FROM {table_name}
        WHERE gruppe = 'GRUND'
        ORDER BY feldname
    """)
    
    grund_results = cursor.fetchall()
    logger.info(f"\n✅ {len(grund_results)} GRUND-Einträge gefunden:")
    for gruppe, feldname, wert in grund_results[:3]:  # Nur erste 3
        logger.info(f"  📋 GRUND[{feldname}]")
        try:
            if wert and wert.strip():
                data = json.loads(wert)
                logger.info(f"      → label: {data.get('label')}")
                logger.info(f"      → sort_order: {data.get('sort_order')}")
        except:
            pass
    
    conn.close()

if __name__ == "__main__":
    check_meta_data()
