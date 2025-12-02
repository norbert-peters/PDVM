"""
MASTER MIGRATION: Alle Systemtabellen auf lineare Gruppe→Feld-Struktur

REGELN:
1. ROOT.TABLE statt ROOT.ROOT_TABLE / ROOT.VIEW_TABLE
2. Jede sys_tabelle hat Template mit GUID 555...
3. Keine METADATEN/controls-Verschachtelung mehr
4. Gruppe = TABLE, darunter Controls als Felder
5. Linear und einfach: GRUPPE → FELD
"""

import sqlite3
import json
import uuid
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = r"c:\Users\norbe\OneDrive\Dokumente\MyApplication\Daten\pdvm_system.db"
TEMPLATE_GUID = "55555555-5555-5555-5555-555555555555"


# ============================================================================
# PHASE 1: sys_viewdaten Template
# ============================================================================

def migrate_sys_viewdaten_template(cursor):
    """Migriert sys_viewdaten Template auf lineare Struktur"""
    logger.info("="*80)
    logger.info("📋 PHASE 1: sys_viewdaten Template")
    logger.info("="*80)
    
    # Template laden
    cursor.execute("SELECT daten FROM sys_viewdaten WHERE uid = ?", (TEMPLATE_GUID,))
    row = cursor.fetchone()
    
    if not row:
        logger.error("❌ Template nicht gefunden!")
        return
    
    data = json.loads(row[0])
    
    # ROOT: VIEW_TABLE → TABLE
    if 'VIEW_TABLE' in data.get('ROOT', {}):
        data['ROOT']['TABLE'] = data['ROOT'].pop('VIEW_TABLE')
        logger.info("✅ VIEW_TABLE → TABLE")
    
    # METADATEN → direkte Gruppen
    if 'METADATEN' in data:
        metadaten = data.pop('METADATEN')
        
        # TEMPLATES, ROOT_CONTROLS, CONTROL_PROPERTIES als direkte Gruppen
        for gruppe in ['TEMPLATES', 'ROOT_CONTROLS', 'CONTROL_PROPERTIES']:
            if gruppe in metadaten:
                data[gruppe] = metadaten[gruppe]
                logger.info(f"✅ METADATEN.{gruppe} → {gruppe}")
        
        # PFADE als direkte Gruppe
        if 'PFADE' in metadaten:
            data['PFADE'] = metadaten['PFADE']
            logger.info("✅ METADATEN.PFADE → PFADE")
    
    # Speichern
    cursor.execute(
        "UPDATE sys_viewdaten SET daten = ? WHERE uid = ?",
        (json.dumps(data, ensure_ascii=False, indent=2), TEMPLATE_GUID)
    )
    
    logger.info("💾 sys_viewdaten Template aktualisiert")


# ============================================================================
# PHASE 2: sys_viewdaten Datensätze
# ============================================================================

def migrate_sys_viewdaten_records(cursor):
    """Migriert alle sys_viewdaten Datensätze"""
    logger.info("="*80)
    logger.info("📋 PHASE 2: sys_viewdaten Datensätze")
    logger.info("="*80)
    
    # Alle Datensätze außer Template
    cursor.execute("SELECT uid, daten FROM sys_viewdaten WHERE uid != ?", (TEMPLATE_GUID,))
    rows = cursor.fetchall()
    
    logger.info(f"📊 {len(rows)} Datensätze zu migrieren")
    
    for uid, daten_str in rows:
        data = json.loads(daten_str)
        
        # ROOT: VIEW_TABLE → TABLE
        if 'VIEW_TABLE' in data.get('ROOT', {}):
            data['ROOT']['TABLE'] = data['ROOT'].pop('VIEW_TABLE')
        
        # METADATEN.TABELLE.controls → TABELLE (direkt)
        if 'METADATEN' in data:
            metadaten = data.pop('METADATEN')
            
            # Jede Tabelle als direkte Gruppe
            for table_name, table_data in metadaten.items():
                if isinstance(table_data, dict):
                    # controls und standard_controls mergen
                    merged = {}
                    
                    if 'controls' in table_data:
                        merged.update(table_data['controls'])
                    
                    if 'standard_controls' in table_data:
                        merged.update(table_data['standard_controls'])
                    
                    if merged:
                        data[table_name] = merged
        
        # Speichern
        cursor.execute(
            "UPDATE sys_viewdaten SET daten = ? WHERE uid = ?",
            (json.dumps(data, ensure_ascii=False, indent=2), uid)
        )
    
    logger.info(f"💾 {len(rows)} Datensätze aktualisiert")


# ============================================================================
# PHASE 3: sys_framedaten Template
# ============================================================================

def migrate_sys_framedaten_template(cursor):
    """Migriert sys_framedaten Template auf lineare Struktur"""
    logger.info("="*80)
    logger.info("📋 PHASE 3: sys_framedaten Template")
    logger.info("="*80)
    
    cursor.execute("SELECT daten FROM sys_framedaten WHERE uid = ?", (TEMPLATE_GUID,))
    row = cursor.fetchone()
    
    if not row:
        logger.error("❌ Template nicht gefunden!")
        return
    
    data = json.loads(row[0])
    
    # ROOT: ROOT_TABLE → TABLE
    if 'ROOT_TABLE' in data.get('ROOT', {}):
        data['ROOT']['TABLE'] = data['ROOT'].pop('ROOT_TABLE')
        logger.info("✅ ROOT_TABLE → TABLE")
    
    # METADATEN → direkte Gruppen
    if 'METADATEN' in data:
        metadaten = data.pop('METADATEN')
        
        for gruppe in ['TEMPLATES', 'ROOT_CONTROLS', 'CONTROL_PROPERTIES']:
            if gruppe in metadaten:
                data[gruppe] = metadaten[gruppe]
                logger.info(f"✅ METADATEN.{gruppe} → {gruppe}")
        
        if 'PFADE' in metadaten:
            data['PFADE'] = metadaten['PFADE']
            logger.info("✅ METADATEN.PFADE → PFADE")
    
    cursor.execute(
        "UPDATE sys_framedaten SET daten = ? WHERE uid = ?",
        (json.dumps(data, ensure_ascii=False, indent=2), TEMPLATE_GUID)
    )
    
    logger.info("💾 sys_framedaten Template aktualisiert")


# ============================================================================
# PHASE 4: sys_framedaten Datensätze
# ============================================================================

def migrate_sys_framedaten_records(cursor):
    """Migriert alle sys_framedaten Datensätze"""
    logger.info("="*80)
    logger.info("📋 PHASE 4: sys_framedaten Datensätze")
    logger.info("="*80)
    
    cursor.execute("SELECT uid, daten FROM sys_framedaten WHERE uid != ?", (TEMPLATE_GUID,))
    rows = cursor.fetchall()
    
    logger.info(f"📊 {len(rows)} Datensätze zu migrieren")
    
    for uid, daten_str in rows:
        data = json.loads(daten_str)
        
        # ROOT: ROOT_TABLE → TABLE
        if 'ROOT_TABLE' in data.get('ROOT', {}):
            data['ROOT']['TABLE'] = data['ROOT'].pop('ROOT_TABLE')
        
        # METADATEN.TABELLE → TABELLE (direkt)
        if 'METADATEN' in data:
            metadaten = data.pop('METADATEN')
            
            for table_name, table_data in metadaten.items():
                if isinstance(table_data, dict):
                    merged = {}
                    
                    if 'controls' in table_data:
                        merged.update(table_data['controls'])
                    
                    if 'standard_controls' in table_data:
                        merged.update(table_data['standard_controls'])
                    
                    if merged:
                        data[table_name] = merged
        
        cursor.execute(
            "UPDATE sys_framedaten SET daten = ? WHERE uid = ?",
            (json.dumps(data, ensure_ascii=False, indent=2), uid)
        )
    
    logger.info(f"💾 {len(rows)} Datensätze aktualisiert")


# ============================================================================
# PHASE 5: sys_menudaten Template
# ============================================================================

def migrate_sys_menudaten_template(cursor):
    """Migriert sys_menudaten Template (META → ROOT)"""
    logger.info("="*80)
    logger.info("📋 PHASE 5: sys_menudaten Template")
    logger.info("="*80)
    
    cursor.execute("SELECT daten FROM sys_menudaten WHERE uid = ?", (TEMPLATE_GUID,))
    row = cursor.fetchone()
    
    if not row:
        # Template erstellen
        logger.info("📝 Template wird erstellt...")
        
        template_data = {
            "ROOT": {
                "TABLE": "",
                "VIEW_GUID": "",
                "DIALOG_GUID": "",
                "HEADER_TEXT": "",
                "EDIT_TYPE": "menu_editor",
                "EDIT_TABS": 1,
                "EDIT_TAB_LABEL_01": "Menü",
                "DISPLAY_ST": "only_date",
                "DISPLAY_TIME_SHORT": True
            },
            "SYS_MENUDATEN": {}  # Controls werden von bestehenden Daten übernommen
        }
        
        cursor.execute(
            "INSERT INTO sys_menudaten (uid, daten) VALUES (?, ?)",
            (TEMPLATE_GUID, json.dumps(template_data, ensure_ascii=False, indent=2))
        )
        logger.info("✅ Template erstellt")
    else:
        # Bestehendes Template anpassen
        data = json.loads(row[0])
        
        # META → ROOT
        if 'META' in data:
            data['ROOT'] = data.pop('META')
            logger.info("✅ META → ROOT")
        
        # TABLE statt ROOT_TABLE
        if 'ROOT_TABLE' in data.get('ROOT', {}):
            data['ROOT']['TABLE'] = data['ROOT'].pop('ROOT_TABLE')
            logger.info("✅ ROOT_TABLE → TABLE")
        
        cursor.execute(
            "UPDATE sys_menudaten SET daten = ? WHERE uid = ?",
            (json.dumps(data, ensure_ascii=False, indent=2), TEMPLATE_GUID)
        )
        logger.info("✅ Template aktualisiert")


# ============================================================================
# PHASE 6: sys_menudaten Datensätze
# ============================================================================

def migrate_sys_menudaten_records(cursor):
    """Migriert alle sys_menudaten Datensätze"""
    logger.info("="*80)
    logger.info("📋 PHASE 6: sys_menudaten Datensätze")
    logger.info("="*80)
    
    cursor.execute("SELECT uid, daten FROM sys_menudaten WHERE uid != ?", (TEMPLATE_GUID,))
    rows = cursor.fetchall()
    
    logger.info(f"📊 {len(rows)} Datensätze zu migrieren")
    
    for uid, daten_str in rows:
        data = json.loads(daten_str)
        
        # META → ROOT (falls noch vorhanden)
        if 'META' in data:
            data['ROOT'] = data.pop('META')
        
        # TABLE statt ROOT_TABLE
        if 'ROOT_TABLE' in data.get('ROOT', {}):
            data['ROOT']['TABLE'] = data['ROOT'].pop('ROOT_TABLE')
        
        cursor.execute(
            "UPDATE sys_menudaten SET daten = ? WHERE uid = ?",
            (json.dumps(data, ensure_ascii=False, indent=2), uid)
        )
    
    logger.info(f"💾 {len(rows)} Datensätze aktualisiert")


# ============================================================================
# MAIN
# ============================================================================

def run_migration():
    """Führt komplette Migration durch"""
    logger.info("\n")
    logger.info("🚀 START: MASTER MIGRATION LINEARE STRUKTUR")
    logger.info("="*80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # PHASE 1-2: sys_viewdaten
        migrate_sys_viewdaten_template(cursor)
        migrate_sys_viewdaten_records(cursor)
        
        # PHASE 3-4: sys_framedaten
        migrate_sys_framedaten_template(cursor)
        migrate_sys_framedaten_records(cursor)
        
        # PHASE 5-6: sys_menudaten
        migrate_sys_menudaten_template(cursor)
        migrate_sys_menudaten_records(cursor)
        
        conn.commit()
        
        logger.info("="*80)
        logger.info("✅ MIGRATION ERFOLGREICH ABGESCHLOSSEN")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"❌ Fehler: {e}", exc_info=True)
        conn.rollback()
    finally:
        conn.close()


if __name__ == '__main__':
    run_migration()
