#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEBUG: Warum wird gespeicherte Systemsteuerung-Config nicht geladen?
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_systemsteuerung_persistenz():
    """Debug warum Speichern/Laden nicht zusammenarbeitet"""
    
    call_daten = {
        "view_guid": "test-view-12345",
        "user_guid": "test-user-67890", 
        "stichtag": 1001.0,
        "mode": "admin"
    }
    
    logger.info("=" * 80)
    logger.info("🔍 DEBUG SYSTEMSTEUERUNG PERSISTENZ")
    
    # Schritt 1: DatenManager erstellen und Spalten holen
    from pdvm_view_daten_manager import PdvmViewDatenManager
    manager = PdvmViewDatenManager(call_daten, widget=None)
    
    columns_vor = manager.get_columns_for_mode("normal")
    logger.info(f"📋 VORHER: {len(columns_vor)} Spalten")
    for col in columns_vor:
        if col['name'] == 'UID_SHOW':
            logger.info(f"   UID_SHOW: display_show={col.get('display_show')}")
    
    # Schritt 2: UID_SHOW auf False setzen und DIREKT speichern
    logger.info("\n🔧 ÄNDERE UID_SHOW auf False und speichere...")
    
    # Spalten modifizieren
    test_columns = []
    for col in columns_vor:
        col_copy = col.copy()
        if col['name'] == 'UID_SHOW':
            col_copy['display_show'] = False
            logger.info(f"   UID_SHOW auf False gesetzt")
        test_columns.append(col_copy)
    
    # DIREKT speichern
    success = manager.set_columns_for_mode("normal", test_columns)
    logger.info(f"💾 Speichern erfolgreich: {success}")
    
    # Schritt 3: NEUEN DatenManager erstellen und laden
    logger.info("\n🔍 NEUER DatenManager - laden von gespeicherter Config...")
    
    manager2 = PdvmViewDatenManager(call_daten, widget=None)
    columns_nach = manager2.get_columns_for_mode("normal")
    
    logger.info(f"📋 NACHHER: {len(columns_nach)} Spalten")
    for col in columns_nach:
        if col['name'] == 'UID_SHOW':
            logger.info(f"   UID_SHOW: display_show={col.get('display_show')}")
            if col.get('display_show') == False:
                logger.info("✅ ERFOLG: UID_SHOW wurde als False geladen!")
            else:
                logger.info("❌ FEHLER: UID_SHOW ist immer noch True")
    
    # Schritt 4: Direkt in Systemsteuerung-DB schauen
    logger.info("\n🔍 DIREKT in Systemsteuerung-DB schauen...")
    
    from pdvm_central_datenbank import PdvmCentralDatenbank
    sys_db = PdvmCentralDatenbank(
        db_name="PdvmManager.db",
        table_name="systemsteuerung",
        guid="test-user-67890"
    )
    
    # Alle Daten für diese GUID
    all_data = sys_db.lesen()
    logger.info(f"📊 Systemsteuerung alle Daten: {all_data}")
    
    # Spezielle Gruppe
    view_data = sys_db.lesen_gruppe("test-view-12345")
    logger.info(f"📊 View-spezifische Daten: {view_data}")
    
    if view_data and "columns_normal" in view_data:
        config = view_data["columns_normal"]
        logger.info(f"📋 Gespeicherte columns_normal: {config}")
        
        if config and 'columns' in config:
            uid_show_config = next(
                (c for c in config['columns'] if c['name'] == 'UID_SHOW'),
                None
            )
            if uid_show_config:
                logger.info(f"🎯 UID_SHOW in DB: show={uid_show_config.get('show')}")
    else:
        logger.info("❌ Keine columns_normal in Systemsteuerung gefunden")
    
    logger.info("=" * 80)

if __name__ == "__main__":
    debug_systemsteuerung_persistenz()
