"""
Handler: Menü-Editor öffnen
============================

Öffnet den Menu-Editor Dialog zum Bearbeiten von Menüs.

Ablauf:
1. View-Dialog öffnen: Menü-GUID aus sys_menudaten auswählen
2. Editor-Dialog öffnen: Menü bearbeiten (2 Tabs + Vorschau)

Autor: PDVM V2.0
Datum: 07.11.2025
"""

import logging
from PyQt5.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)


def execute(params: dict, context: dict, gcs) -> bool:
    """
    Öffnet Menu-Editor
    
    Args:
        params: Handler-Parameter (leer für Menu-Editor)
        context: {'main_app': V2MainAppComplete}
        gcs: GlobalCentralSystemsteuerung
    
    Returns:
        True bei Erfolg
    """
    try:
        logger.info("🎨 Menu-Editor Handler gestartet")
        
        # Hole main_app
        main_app = context.get('main_app')
        if not main_app:
            logger.error("❌ main_app nicht im Context")
            return False
        
        if not gcs:
            logger.error("❌ GCS nicht verfügbar")
            QMessageBox.critical(
                main_app,
                "Fehler",
                "Systemsteuerung nicht verfügbar!"
            )
            return False
        
        # STEP 1: Allgemeiner Dialog mit Frame-GUID
        # Frame-GUID für Menü-Editor (bereits in sys_framedaten)
        frame_guid = "794cbfc3-ccb6-4681-b432-efa9f44682c8"
        
        logger.info(f"🔍 Öffne allgemeinen Dialog für Menü-Bearbeitung: {frame_guid}")
        
        from pdvm_view_dialog import PdvmViewDialog
        
        view_dialog = PdvmViewDialog(
            view_guid=frame_guid,
            parent=main_app,
            title="Menü zum Bearbeiten auswählen",
            selection_mode='single'
        )
        
        # Dialog ausführen
        if not view_dialog.exec_():
            logger.info("ℹ️ Menü-Auswahl abgebrochen")
            return False
        
        # Ausgewählte Menü-GUID holen
        selected_rows = view_dialog.get_selected_rows()
        if not selected_rows:
            logger.warning("⚠️ Kein Menü ausgewählt")
            return False
        
        menu_guid = selected_rows[0].get('GUID')
        menu_name = selected_rows[0].get('MENU_NAME', 'Unbekannt')
        
        if not menu_guid:
            logger.error("❌ Keine GUID in ausgewähltem Menü")
            QMessageBox.critical(
                main_app,
                "Fehler",
                "Ausgewähltes Menü hat keine GUID!"
            )
            return False
        
        logger.info(f"✅ Menü ausgewählt: {menu_name} ({menu_guid})")
        
        # STEP 2: Menu-Editor-Dialog öffnen (OPTIMIERTE VERSION)
        from pdvm_menu_editor_optimized import create_menu_editor_dialog
        
        logger.info("🎨 Öffne Menu-Editor-Dialog (optimiert)...")
        
        editor_dialog = create_menu_editor_dialog(
            menu_guid=menu_guid,
            parent=main_app
        )
        
        # Dialog ausführen
        result = editor_dialog.exec_()
        
        if result:
            logger.info("✅ Menu-Editor erfolgreich abgeschlossen")
        else:
            logger.info("ℹ️ Menu-Editor abgebrochen")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler im Menu-Editor Handler: {e}", exc_info=True)
        QMessageBox.critical(
            main_app if 'main_app' in locals() else None,
            "Fehler",
            f"Menu-Editor konnte nicht geöffnet werden:\n\n{str(e)}"
        )
        return False
