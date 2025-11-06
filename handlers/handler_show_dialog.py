"""
Handler: Dialog anzeigen
========================
Öffnet einen spezifischen Dialog

V3.1: Verwendet skip_clear=False (default) → Arbeitsbereich wird geleert

Autor: PDVM V2.0
Datum: 01.11.2025
"""

import logging

logger = logging.getLogger(__name__)

# V3.1: Handler-Metadaten für Pipeline
SKIP_CLEAR = False  # Arbeitsbereich leeren


def execute(params: dict, context: dict, gcs) -> bool:
    """
    Zeigt einen Dialog an
    
    Args:
        params: {
            'dialog_guid': str,         # GUID des Dialogs (required)
            'dialog_mode': int,         # Modus (0=neu, 1=bearbeiten, etc.)
            'selected_id': str          # ID des zu bearbeitenden Datensatzes
        }
        context: {
            'main_app': V2MainAppComplete
        }
        gcs: GlobalCentralSystemsteuerung
    
    Returns:
        True bei Erfolg
    """
    logger.info("🔵 Handler: show_dialog")
    
    # Parameter
    dialog_guid = params.get('dialog_guid')
    if not dialog_guid:
        logger.error("❌ Parameter 'dialog_guid' fehlt")
        return False
    
    dialog_mode = params.get('dialog_mode', 0)
    selected_id = params.get('selected_id')
    
    logger.info(f"   Dialog-GUID: {dialog_guid}")
    logger.info(f"   Dialog-Mode: {dialog_mode}")
    logger.info(f"   Selected-ID: {selected_id}")
    
    # Hole main_app
    main_app = context.get('main_app')
    if not main_app:
        logger.error("❌ main_app nicht im Context")
        return False
    
    try:
        # V2.0: Verwende pdvm_dialog Methode
        if hasattr(main_app, 'pdvm_dialog'):
            result = main_app.pdvm_dialog(
                dialog_guid=dialog_guid,
                mode=dialog_mode,
                selected_id=selected_id
            )
            logger.info(f"✅ V2.0: Dialog via pdvm_dialog {'erfolgreich' if result else 'abgebrochen'}: {dialog_guid}")
            return True
        
        # Fallback: Alte Methoden
        elif hasattr(main_app, 'start_dialog'):
            main_app.start_dialog(dialog_guid)
            logger.info(f"✅ Dialog via start_dialog geöffnet: {dialog_guid}")
            return True
        
        else:
            logger.error("❌ Keine Dialog-Methode verfügbar")
            return False
            
    except Exception as e:
        logger.error(f"❌ Fehler beim Öffnen des Dialogs: {e}")
        import traceback
        traceback.print_exc()
        return False
