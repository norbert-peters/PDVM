"""
PHASE 7-9: Erstellt Templates und migriert restliche Systemtabellen

- sys_dialogdaten: Template erstellen
- sys_dropdowndaten: Template + Sprachgruppen-Struktur
- sys_beschreibungen: Template + Sprachgruppen-Struktur
"""

import sqlite3
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = r"c:\Users\norbe\OneDrive\Dokumente\MyApplication\Daten\pdvm_system.db"
TEMPLATE_GUID = "55555555-5555-5555-5555-555555555555"


# ============================================================================
# PHASE 7: sys_dialogdaten Template
# ============================================================================

def migrate_sys_dialogdaten(cursor):
    """Erstellt Template und migriert sys_dialogdaten"""
    logger.info("="*80)
    logger.info("📋 PHASE 7: sys_dialogdaten")
    logger.info("="*80)
    
    # Template erstellen
    template_data = {
        "ROOT": {
            "TABLE": "",
            "DIALOG_GUID": "",
            "DIALOG_NAME": "",
            "DIALOG_TYPE": "standard",
            "WIDTH": 800,
            "HEIGHT": 600,
            "RESIZABLE": True
        }
    }
    
    # Prüfen ob Template existiert
    cursor.execute("SELECT uid FROM sys_dialogdaten WHERE uid = ?", (TEMPLATE_GUID,))
    if cursor.fetchone():
        # Update
        cursor.execute(
            "UPDATE sys_dialogdaten SET daten = ? WHERE uid = ?",
            (json.dumps(template_data, ensure_ascii=False, indent=2), TEMPLATE_GUID)
        )
        logger.info("✅ Template aktualisiert")
    else:
        # Insert
        cursor.execute(
            "INSERT INTO sys_dialogdaten (uid, daten) VALUES (?, ?)",
            (TEMPLATE_GUID, json.dumps(template_data, ensure_ascii=False, indent=2))
        )
        logger.info("✅ Template erstellt")
    
    # Datensätze migrieren (TABLE statt ROOT_TABLE)
    cursor.execute("SELECT uid, daten FROM sys_dialogdaten WHERE uid != ?", (TEMPLATE_GUID,))
    rows = cursor.fetchall()
    
    for uid, daten_str in rows:
        data = json.loads(daten_str)
        
        if 'ROOT_TABLE' in data.get('ROOT', {}):
            data['ROOT']['TABLE'] = data['ROOT'].pop('ROOT_TABLE')
        
        cursor.execute(
            "UPDATE sys_dialogdaten SET daten = ? WHERE uid = ?",
            (json.dumps(data, ensure_ascii=False, indent=2), uid)
        )
    
    logger.info(f"💾 {len(rows)} Datensätze aktualisiert")


# ============================================================================
# PHASE 8: sys_dropdowndaten Template + Sprachstruktur
# ============================================================================

def migrate_sys_dropdowndaten(cursor):
    """Erstellt Template und neue Sprachgruppen-Struktur"""
    logger.info("="*80)
    logger.info("📋 PHASE 8: sys_dropdowndaten")
    logger.info("="*80)
    
    # Template mit Sprachgruppen-Struktur
    template_data = {
        "ROOT": {
            "TABLE": "sys_dropdowndaten",
            "DROPDOWN_NAME": "",
            "DEFAULT_LANGUAGE": "DE-DE"
        },
        "DE-DE": {},  # Deutsche Einträge
        "US-EN": {},  # Englische Einträge
        "FR-FR": {}   # Französische Einträge (optional)
    }
    
    cursor.execute("SELECT uid FROM sys_dropdowndaten WHERE uid = ?", (TEMPLATE_GUID,))
    if cursor.fetchone():
        cursor.execute(
            "UPDATE sys_dropdowndaten SET daten = ? WHERE uid = ?",
            (json.dumps(template_data, ensure_ascii=False, indent=2), TEMPLATE_GUID)
        )
        logger.info("✅ Template aktualisiert")
    else:
        cursor.execute(
            "INSERT INTO sys_dropdowndaten (uid, daten) VALUES (?, ?)",
            (TEMPLATE_GUID, json.dumps(template_data, ensure_ascii=False, indent=2))
        )
        logger.info("✅ Template erstellt")
    
    # Bestehende Datensätze analysieren und migrieren
    cursor.execute("SELECT uid, daten FROM sys_dropdowndaten WHERE uid != ?", (TEMPLATE_GUID,))
    rows = cursor.fetchall()
    
    logger.info(f"📊 {len(rows)} Datensätze gefunden")
    
    for uid, daten_str in rows:
        data = json.loads(daten_str)
        logger.info(f"   Datensatz: {uid}")
        logger.info(f"   Keys: {list(data.keys())}")
        
        # Hier müssten wir die bestehende Struktur analysieren
        # und in Sprachgruppen umwandeln
        # Für jetzt: ROOT.TABLE setzen falls ROOT_TABLE vorhanden
        
        if 'ROOT' in data and 'ROOT_TABLE' in data['ROOT']:
            data['ROOT']['TABLE'] = data['ROOT'].pop('ROOT_TABLE')
            
            cursor.execute(
                "UPDATE sys_dropdowndaten SET daten = ? WHERE uid = ?",
                (json.dumps(data, ensure_ascii=False, indent=2), uid)
            )
    
    logger.info("💾 Datensätze vorbereitet")


# ============================================================================
# PHASE 9: sys_beschreibungen Template + Sprachstruktur
# ============================================================================

def migrate_sys_beschreibungen(cursor):
    """Erstellt Template und neue Sprachgruppen-Struktur"""
    logger.info("="*80)
    logger.info("📋 PHASE 9: sys_beschreibungen")
    logger.info("="*80)
    
    # Template mit Sprachgruppen-Struktur
    template_data = {
        "ROOT": {
            "TABLE": "sys_beschreibungen",
            "BESCHREIBUNG_NAME": "",
            "DEFAULT_LANGUAGE": "DE-DE"
        },
        "DE-DE": {},  # Deutsche Texte
        "US-EN": {},  # Englische Texte
        "FR-FR": {}   # Französische Texte (optional)
    }
    
    cursor.execute("SELECT uid FROM sys_beschreibungen WHERE uid = ?", (TEMPLATE_GUID,))
    if cursor.fetchone():
        cursor.execute(
            "UPDATE sys_beschreibungen SET daten = ? WHERE uid = ?",
            (json.dumps(template_data, ensure_ascii=False, indent=2), TEMPLATE_GUID)
        )
        logger.info("✅ Template aktualisiert")
    else:
        cursor.execute(
            "INSERT INTO sys_beschreibungen (uid, daten) VALUES (?, ?)",
            (TEMPLATE_GUID, json.dumps(template_data, ensure_ascii=False, indent=2))
        )
        logger.info("✅ Template erstellt")
    
    # Bestehende Datensätze
    cursor.execute("SELECT uid, daten FROM sys_beschreibungen WHERE uid != ?", (TEMPLATE_GUID,))
    rows = cursor.fetchall()
    
    logger.info(f"📊 {len(rows)} Datensätze gefunden")
    
    for uid, daten_str in rows:
        data = json.loads(daten_str)
        logger.info(f"   Datensatz: {uid}")
        logger.info(f"   Keys: {list(data.keys())}")
        
        if 'ROOT' in data and 'ROOT_TABLE' in data['ROOT']:
            data['ROOT']['TABLE'] = data['ROOT'].pop('ROOT_TABLE')
            
            cursor.execute(
                "UPDATE sys_beschreibungen SET daten = ? WHERE uid = ?",
                (json.dumps(data, ensure_ascii=False, indent=2), uid)
            )
    
    logger.info("💾 Datensätze vorbereitet")


# ============================================================================
# MAIN
# ============================================================================

def run_migration():
    """Führt Phase 7-9 durch"""
    logger.info("\n")
    logger.info("🚀 START: PHASE 7-9 (Restliche Tabellen)")
    logger.info("="*80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        migrate_sys_dialogdaten(cursor)
        migrate_sys_dropdowndaten(cursor)
        migrate_sys_beschreibungen(cursor)
        
        conn.commit()
        
        logger.info("="*80)
        logger.info("✅ PHASE 7-9 ERFOLGREICH ABGESCHLOSSEN")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"❌ Fehler: {e}", exc_info=True)
        conn.rollback()
    finally:
        conn.close()


if __name__ == '__main__':
    run_migration()
