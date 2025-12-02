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
            'frame_guid': str,          # GUID des Frames (required)
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
    
    # Parameter: frame_guid (steuert gesamten Dialog + Editoren)
    frame_guid = params.get('frame_guid')
    
    if not frame_guid:
        logger.error("❌ Parameter 'frame_guid' fehlt")
        return False
    
    dialog_mode = params.get('dialog_mode', 0)
    selected_id = params.get('selected_id')
    
    logger.info(f"   Frame-GUID: {frame_guid}")
    logger.info(f"   Dialog-Mode: {dialog_mode}")
    logger.info(f"   Selected-ID: {selected_id}")
    
    # Hole main_app
    main_app = context.get('main_app')
    if not main_app:
        logger.error("❌ main_app nicht im Context")
        return False
    
    try:
        # Dialog direkt öffnen (in workspace_container)
        from pdvm_genereller_dialog import V2PdvmGenerellerDialog
        
        # Dialog erstellen
        dialog_widget = V2PdvmGenerellerDialog(
            frame_guid=frame_guid,
            parent=main_app.workspace_container,
            main_app=main_app
        )
        
        # Workspace clearen: Nur Widgets entfernen, Layout behalten!
        workspace_layout = main_app.workspace_container.layout()
        if workspace_layout is None:
            logger.error("❌ Workspace-Container hat kein Layout!")
            return False
        
        while workspace_layout.count():
            child = workspace_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Event-Loop verarbeiten, damit Widgets SOFORT gelöscht werden
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
        
        # Dialog-Widget einfügen
        workspace_layout.addWidget(dialog_widget)
        
        # Referenz speichern
        main_app.current_dialog_widget = dialog_widget
        
        logger.info(f"✅ Dialog geöffnet: Frame={frame_guid}")
        return True
            
    except Exception as e:
        logger.error(f"❌ Fehler beim Öffnen des Dialogs: {e}")
        import traceback
        traceback.print_exc()
        return False
