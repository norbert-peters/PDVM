"""
Handler: Info-Dialog anzeigen
==============================
Zeigt einen einfachen Info-Dialog mit Text und Titel

Autor: PDVM V2.0
Datum: 02.11.2025
"""

import logging
from PyQt5.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)


def execute(params: dict, context: dict, gcs) -> bool:
    """
    Zeigt Info-Dialog
    
    Args:
        params: {
            'message': str,  # Nachricht
            'title': str     # Titel (optional)
        }
        context: {
            'main_app': V2MainAppComplete
        }
        gcs: GlobalCentralSystemsteuerung
    
    Returns:
        True bei Erfolg
    """
    logger.info("🔵 Handler: show_info")
    
    message = params.get('message', 'Information')
    title = params.get('title', 'Info')
    
    logger.info(f"   Titel: {title}")
    logger.info(f"   Nachricht: {message[:50]}...")
    
    try:
        main_app = context.get('main_app')
        
        msg = QMessageBox(main_app if main_app else None)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(title)
        msg.setText(f"<b>{title}</b>")
        msg.setInformativeText(message)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        
        logger.info(f"✅ Info-Dialog angezeigt")
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Anzeigen des Info-Dialogs: {e}")
        import traceback
        traceback.print_exc()
        return False
