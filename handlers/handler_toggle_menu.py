"""
Handler: Menü umschalten
=========================
Schaltet Menü-Sichtbarkeit ein/aus

V3.1: Verwendet skip_clear=True → Arbeitsbereich bleibt unverändert

Autor: PDVM V2.0
Datum: 01.11.2025
"""

import logging

logger = logging.getLogger(__name__)

# V3.1: Handler-Metadaten für Pipeline
SKIP_CLEAR = True  # Arbeitsbereich NICHT leeren!


def execute(params: dict, context: dict, gcs) -> bool:
    """
    Schaltet Menü-Sichtbarkeit um
    
    V3.1: Arbeitsbereich bleibt unverändert (SKIP_CLEAR=True)
    
    Args:
        params: {
            'menu_part': str  # 'all' | 'vertical' | 'grund' (optional, default='all')
        }
        context: {
            'main_app': MainAppComplete,
            'menu_handler': V3MenuHandler
        }
        gcs: GlobalCentralSystemsteuerung
    
    Returns:
        True bei Erfolg
    """
    logger.info("🔵 Handler: toggle_menu (skip_clear=True)")
    
    menu_part = params.get('menu_part', 'all')
    logger.info(f"   Menü-Teil: {menu_part}")
    
    # Hole main_app
    main_app = context.get('main_app')
    if not main_app:
        logger.error("❌ main_app nicht im Context")
        return False
    
    try:
        if hasattr(main_app, 'toggle_menu_visibility'):
            main_app.toggle_menu_visibility()
            logger.info("✅ Menü-Sichtbarkeit umgeschaltet")
            return True
        
        # Fallback: Direkt auf Container zugreifen
        if menu_part == 'all' or menu_part == 'vertical':
            if hasattr(main_app, 'vertical_menu_container'):
                container = main_app.vertical_menu_container
                container.setVisible(not container.isVisible())
                logger.info(f"✅ Vertikal-Menü: {'sichtbar' if container.isVisible() else 'versteckt'}")
        
        if menu_part == 'all' or menu_part == 'grund':
            if hasattr(main_app, 'grund_menu_container'):
                container = main_app.grund_menu_container
                container.setVisible(not container.isVisible())
                logger.info(f"✅ Grund-Menü: {'sichtbar' if container.isVisible() else 'versteckt'}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Umschalten des Menüs: {e}")
        import traceback
        traceback.print_exc()
        return False
