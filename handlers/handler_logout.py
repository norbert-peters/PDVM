"""
Handler: Abmelden (Logout)
===========================
Meldet den Benutzer ab und kehrt zum Login zurück

Autor: PDVM V2.0
Datum: 01.11.2025
"""

import logging

logger = logging.getLogger(__name__)


def execute(params: dict, context: dict, gcs) -> bool:
    """
    Meldet Benutzer ab
    
    Args:
        params: {} (keine Parameter benötigt)
        context: {
            'main_app': V2MainAppComplete
        }
        gcs: GlobalCentralSystemsteuerung
    
    Returns:
        True bei Erfolg
    """
    logger.info("🔵 Handler: logout")
    
    # Hole main_app
    main_app = context.get('main_app')
    if not main_app:
        logger.error("❌ main_app nicht im Context")
        return False
    
    try:
        # Versuche verschiedene Logout-Methoden
        if hasattr(main_app, 'logout'):
            main_app.logout()
            logger.info("✅ Logout via logout() durchgeführt")
            return True
        
        elif hasattr(main_app, 'close'):
            # Fenster schließen als Fallback
            main_app.close()
            logger.info("✅ Anwendung geschlossen")
            return True
        
        else:
            logger.error("❌ Keine Logout-Methode verfügbar")
            return False
            
    except Exception as e:
        logger.error(f"❌ Fehler beim Logout: {e}")
        import traceback
        traceback.print_exc()
        return False
