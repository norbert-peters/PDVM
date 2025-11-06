"""
Handler: Menü-Editor öffnen
============================
Öffnet den Menü-Editor für ein bestimmtes Menü

Autor: PDVM V2.0
Datum: 01.11.2025
"""

import logging

logger = logging.getLogger(__name__)


def execute(params: dict, context: dict, gcs) -> bool:
    """
    Öffnet Menü-Editor
    
    Args:
        params: {
            'menu_name': str,           # Name des Menüs (optional)
            'menu_guid': str            # GUID des Menüs (optional)
        }
        context: {
            'main_app': V2MainAppComplete
        }
        gcs: GlobalCentralSystemsteuerung
    
    Returns:
        True bei Erfolg
    """
    logger.info("🔵 Handler: open_menu_editor")
    
    menu_name = params.get('menu_name')
    menu_guid = params.get('menu_guid')
    
    logger.info(f"   Menu-Name: {menu_name}")
    logger.info(f"   Menu-GUID: {menu_guid}")
    
    # Hole main_app
    main_app = context.get('main_app')
    if not main_app:
        logger.error("❌ main_app nicht im Context")
        return False
    
    try:
        # Versuche verschiedene Menü-Editor Methoden
        if hasattr(main_app, 'open_menu_editor'):
            if menu_guid:
                main_app.open_menu_editor(menu_guid)
            elif menu_name:
                main_app.open_menu_editor(menu_name)
            else:
                main_app.open_menu_editor()
            logger.info("✅ Menü-Editor geöffnet")
            return True
        
        elif hasattr(main_app, 'pdvm_dialog'):
            # Fallback: Menü-Editor als Dialog
            # TODO: Menü-Editor View-GUID konfigurierbar machen
            logger.warning("⚠️ Menü-Editor noch nicht implementiert")
            return False
        
        else:
            logger.error("❌ Keine Menü-Editor Methode verfügbar")
            return False
            
    except Exception as e:
        logger.error(f"❌ Fehler beim Öffnen des Menü-Editors: {e}")
        import traceback
        traceback.print_exc()
        return False
