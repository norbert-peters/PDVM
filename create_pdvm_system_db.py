#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erstellt pdvm_system.db mit Schema für zentrale System-Tabellen

SYSTEM-TABELLEN (werden aus Mandanten-DB kopiert):
- sys_beschreibungen
- sys_dialogdaten
- sys_dropdowndaten
- sys_framedaten
- sys_menudaten
- sys_viewdaten

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


def create_pdvm_system_db():
    """
    Erstellt pdvm_system.db mit Schema für System-Tabellen
    
    WICHTIG: Kopiert nur Schema, KEINE Daten!
    Daten werden manuell aus Mandanten-DB kopiert.
    """
    db_path = os.path.join('Daten', 'pdvm_system.db')
    
    # Prüfe ob DB bereits existiert
    if os.path.exists(db_path):
        logger.warning(f"⚠️ {db_path} existiert bereits!")
        response = input("Überschreiben? (j/n): ")
        if response.lower() != 'j':
            logger.info("❌ Abgebrochen")
            return False
        
        # Backup erstellen
        backup_path = db_path + '.backup'
        os.rename(db_path, backup_path)
        logger.info(f"💾 Backup erstellt: {backup_path}")
    
    try:
        logger.info(f"🔧 Erstelle {db_path}...")
        
        # Verbindung öffnen (erstellt DB automatisch)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Standard PDVM Tabellen-Struktur
        table_schema = """
            uid          TEXT    PRIMARY KEY,
            daten        TEXT    NOT NULL,
            name         TEXT,
            historisch   INTEGER DEFAULT 0,
            source_hash  TEXT,
            sec_id       TEXT,
            gilt_bis     TEXT    DEFAULT '9999365.00000',
            created_at   TEXT,
            modified_at  TEXT,
            daten_backup TEXT
        """
        
        # ===== TABELLE: sys_beschreibungen =====
        logger.info("📋 Erstelle Tabelle: sys_beschreibungen")
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS sys_beschreibungen (
                {table_schema}
            )
        """)
        
        # ===== TABELLE: sys_dialogdaten =====
        logger.info("📋 Erstelle Tabelle: sys_dialogdaten")
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS sys_dialogdaten (
                {table_schema}
            )
        """)
        
        # ===== TABELLE: sys_dropdowndaten =====
        logger.info("📋 Erstelle Tabelle: sys_dropdowndaten")
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS sys_dropdowndaten (
                {table_schema}
            )
        """)
        
        # ===== TABELLE: sys_framedaten =====
        logger.info("📋 Erstelle Tabelle: sys_framedaten")
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS sys_framedaten (
                {table_schema}
            )
        """)
        
        # ===== TABELLE: sys_menudaten =====
        logger.info("📋 Erstelle Tabelle: sys_menudaten")
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS sys_menudaten (
                {table_schema}
            )
        """)
        
        # ===== TABELLE: sys_viewdaten =====
        logger.info("📋 Erstelle Tabelle: sys_viewdaten")
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS sys_viewdaten (
                {table_schema}
            )
        """)
        
        # Commit und schließen
        conn.commit()
        conn.close()
        
        logger.info(f"✅ pdvm_system.db erfolgreich erstellt!")
        logger.info(f"📂 Pfad: {os.path.abspath(db_path)}")
        logger.info("")
        logger.info("📋 Nächste Schritte:")
        logger.info("   1. Tabellen-Daten aus Mandanten-DB nach pdvm_system.db kopieren")
        logger.info("   2. In Mandanten-Daten METADATEN.SYSTEM_DB = 'pdvm_system' setzen")
        logger.info("   3. System testen")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen der DB: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🏗️ PDVM System-DB Erstellung")
    logger.info("=" * 60)
    
    success = create_pdvm_system_db()
    
    if success:
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ ERFOLGREICH!")
        logger.info("=" * 60)
    else:
        logger.info("")
        logger.info("=" * 60)
        logger.info("❌ FEHLGESCHLAGEN!")
        logger.info("=" * 60)
