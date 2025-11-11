"""
Handler: Startmenü öffnen
==========================
Kehrt zum Startmenü zurück (Pipeline fügt Welcome-Screen automatisch ein)

V3.2: Verwendet skip_clear=False → Workspace wird geleert (STEP 3.1)
      Handler lädt nur Menü, Pipeline fügt Welcome-Screen ein (STEP 3.3)

Autor: PDVM V2.0
Datum: 06.11.2025
"""

import logging

logger = logging.getLogger(__name__)

# V3.2: Handler-Metadaten für Pipeline
SKIP_CLEAR = False  # Arbeitsbereich leeren, Pipeline fügt Welcome ein


def execute(params: dict, context: dict, gcs) -> bool:
    """
    Öffnet Startmenü (Welcome-Screen kommt automatisch)
    
    V3.2: Lineare Pipeline-Logik
    STEP 3.1: Workspace wird geleert (skip_clear=False)
    STEP 3.2: Handler lädt Menü (KEIN Widget einfügen!)
    STEP 3.3: Pipeline prüft Workspace leer → fügt Welcome-Screen ein
    
    Args:
        params: {} (keine Parameter benötigt)
        context: {
            'menu_handler': PdvmMenuHandler,
            'main_app': MainAppComplete
        }
        gcs: GlobalCentralSystemsteuerung
    
    Returns:
        True bei Erfolg
    """
    logger.info("🔵 Handler: open_start_menu (V3.2 Lineare Pipeline)")
    
    try:
        # Hole menu_handler aus context
        menu_handler = context.get('menu_handler')
        
        if not menu_handler:
            logger.error("❌ menu_handler nicht im Context")
            return False
        
        # Lade Startmenü
        if hasattr(menu_handler, 'load_startmenu'):
            success = menu_handler.load_startmenu()
            if success:
                logger.info("✅ Startmenü geladen")
                
                # V3.2: KEIN _show_welcome_message() mehr!
                # Pipeline fügt Welcome-Screen automatisch ein (STEP 3.3)
                # → Neues Widget wird erstellt (altes wurde in STEP 3.1 gelöscht)
                
                return True
            else:
                logger.error("❌ Startmenü konnte nicht geladen werden")
                return False
        else:
            logger.error("❌ load_startmenu() nicht verfügbar")
            return False
            
    except Exception as e:
        logger.error(f"❌ Fehler beim Öffnen des Startmenüs: {e}")
        import traceback
        traceback.print_exc()
        return False
