#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kopiert System-Tabellen von Mandanten-DB nach pdvm_system.db

SYSTEM-TABELLEN:
- sys_beschreibungen
- sys_dialogdaten
- sys_dropdowndaten
- sys_framedaten
- sys_menudaten
- sys_viewdaten

WICHTIG: Nur zum manuellen Kopieren gedacht!
         Wird von Admin ausgeführt, NICHT automatisch!

Autor: PDVM System
Datum: 11.11.2025
"""

import sqlite3
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# System-Tabellen (müssen kopiert werden)
SYSTEM_TABLES = [
    'sys_beschreibungen',
    'sys_dialogdaten',
    'sys_dropdowndaten',
    'sys_framedaten',
    'sys_menudaten',
    'sys_viewdaten'
]


def copy_system_tables(source_db_path, target_db_path='Daten/pdvm_system.db'):
    """
    Kopiert System-Tabellen von Quell-DB nach Ziel-DB
    
    Args:
        source_db_path: Pfad zur Mandanten-DB (Quelle)
        target_db_path: Pfad zur System-DB (Ziel, default: Daten/pdvm_system.db)
    """
    logger.info("=" * 80)
    logger.info("📋 Kopiere System-Tabellen")
    logger.info("=" * 80)
    logger.info(f"   Quelle: {source_db_path}")
    logger.info(f"   Ziel:   {target_db_path}")
    logger.info("")
    
    # Prüfe ob Quell-DB existiert
    if not os.path.exists(source_db_path):
        logger.error(f"❌ Quell-Datenbank nicht gefunden: {source_db_path}")
        return False
    
    # Prüfe ob Ziel-DB existiert
    if not os.path.exists(target_db_path):
        logger.error(f"❌ Ziel-Datenbank nicht gefunden: {target_db_path}")
        logger.error("   Bitte zuerst create_pdvm_system_db.py ausführen!")
        return False
    
    try:
        # Verbindungen öffnen
        source_conn = sqlite3.connect(source_db_path)
        target_conn = sqlite3.connect(target_db_path)
        
        source_cursor = source_conn.cursor()
        target_cursor = target_conn.cursor()
        
        total_rows = 0
        
        # Für jede System-Tabelle
        for table_name in SYSTEM_TABLES:
            logger.info(f"📋 Kopiere Tabelle: {table_name}")
            
            try:
                # Prüfe ob Tabelle in Quelle existiert
                source_cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,)
                )
                if not source_cursor.fetchone():
                    logger.warning(f"   ⚠️ Tabelle {table_name} nicht in Quelle gefunden - überspringe")
                    continue
                
                # Alte Daten in Ziel löschen (falls vorhanden)
                target_cursor.execute(f"DELETE FROM {table_name}")
                logger.debug(f"   🗑️ Alte Daten gelöscht")
                
                # Daten kopieren
                source_cursor.execute(f"SELECT * FROM {table_name}")
                rows = source_cursor.fetchall()
                
                if rows:
                    # Spalten ermitteln
                    source_cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [col[1] for col in source_cursor.fetchall()]
                    placeholders = ','.join(['?' for _ in columns])
                    
                    # Einfügen
                    target_cursor.executemany(
                        f"INSERT INTO {table_name} VALUES ({placeholders})",
                        rows
                    )
                    
                    logger.info(f"   ✅ {len(rows)} Zeilen kopiert")
                    total_rows += len(rows)
                else:
                    logger.info(f"   ℹ️ Tabelle leer - keine Daten zu kopieren")
                
            except Exception as e:
                logger.error(f"   ❌ Fehler beim Kopieren von {table_name}: {e}")
                continue
        
        # Commit und schließen
        target_conn.commit()
        source_conn.close()
        target_conn.close()
        
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"✅ Kopieren abgeschlossen!")
        logger.info(f"   Gesamt: {total_rows} Zeilen in {len(SYSTEM_TABLES)} Tabellen")
        logger.info("=" * 80)
        logger.info("")
        logger.info("📋 Nächste Schritte:")
        logger.info("   1. In Mandanten-Daten METADATEN.SYSTEM_DB = 'pdvm_system' setzen")
        logger.info("   2. System neu starten und testen")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Kopieren: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == '__main__':
    import sys
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("🔧 System-Tabellen Kopier-Tool")
    logger.info("=" * 80)
    logger.info("")
    
    # Mandanten-DB Pfad vom User abfragen
    if len(sys.argv) > 1:
        source_db = sys.argv[1]
    else:
        print("Pfad zur Mandanten-Datenbank (Quelle):")
        print("  Beispiel: Daten/datenbank.db")
        source_db = input(">>> ").strip()
    
    if not source_db:
        logger.error("❌ Kein Pfad angegeben - Abbruch")
        sys.exit(1)
    
    # Kopieren
    success = copy_system_tables(source_db)
    
    if success:
        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ ERFOLGREICH!")
        logger.info("=" * 80)
        sys.exit(0)
    else:
        logger.info("")
        logger.info("=" * 80)
        logger.info("❌ FEHLGESCHLAGEN!")
        logger.info("=" * 80)
        sys.exit(1)
