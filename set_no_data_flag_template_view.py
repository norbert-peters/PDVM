#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setzt NO_DATA Flag für Template-View (sys_menudaten)

Template-View hat keine METADATEN, zeigt nur uid und name an.
NO_DATA Flag aktiviert automatischen Modus ohne METADATEN-Anforderung.
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Setzt NO_DATA Flag für Template-View"""
    
    # PyQt5 App für GCS
    app = QApplication(sys.argv)
    
    # Login und GCS initialisieren
    logger.info("🔐 Starte Login...")
    from pdvm_login import PdvmLogin
    from pdvm_central_systemsteuerung import initialize_gcs
    
    login = PdvmLogin()
    if not login.exec_():
        logger.error("❌ Login abgebrochen")
        return 1
    
    user_guid = login.user_guid
    logger.info(f"✅ Login erfolgreich: {user_guid}")
    
    # GCS initialisieren
    initialize_gcs(user_guid)
    from pdvm_central_systemsteuerung import get_gcs
    gcs = get_gcs()
    
    if not gcs:
        logger.error("❌ GCS nicht verfügbar")
        return 1
    
    logger.info("✅ GCS initialisiert")
    
    # Template-View GUID
    TEMPLATE_VIEW_GUID = "8746d0cc-6acb-4f14-a7cb-3d48f97b0751"
    
    logger.info(f"📋 Setze NO_DATA Flag für View: {TEMPLATE_VIEW_GUID}")
    
    # View-Daten laden
    from pdvm_central_datenbank import PdvmCentralDatenbank
    
    view_db = PdvmCentralDatenbank('sys_viewdaten', TEMPLATE_VIEW_GUID)
    
    # Aktuelle Werte prüfen
    view_table = view_db.get_static_value('ROOT', 'VIEW_TABLE')
    no_data_old = view_db.get_static_value('ROOT', 'NO_DATA')
    
    logger.info(f"  VIEW_TABLE: {view_table}")
    logger.info(f"  NO_DATA (alt): {no_data_old}")
    
    if no_data_old:
        logger.info("✅ NO_DATA Flag bereits gesetzt!")
        return 0
    
    # NO_DATA Flag setzen
    logger.info("🔧 Setze NO_DATA Flag...")
    
    stichtag = gcs.st_inst.PdvmDateTime
    view_db.set_value('ROOT', 'NO_DATA', True, stichtag)
    view_db.save_all_values()
    
    logger.info("✅ NO_DATA Flag gesetzt und gespeichert!")
    
    # Verifizieren
    no_data_new = view_db.get_static_value('ROOT', 'NO_DATA')
    logger.info(f"  NO_DATA (neu): {no_data_new}")
    
    logger.info("🎉 Fertig!")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
