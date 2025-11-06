"""
Handler: Hilfe anzeigen
========================
Zeigt Hilfe-Dialog oder Dokumentation an

Autor: PDVM V2.0
Datum: 01.11.2025
"""

import logging
from PyQt5.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)


def execute(params: dict, context: dict, gcs) -> bool:
    """
    Zeigt Hilfe an
    
    Args:
        params: {
            'help_topic': str,          # Hilfe-Thema (optional)
            'help_text': str,           # Direkter Hilfe-Text (optional)
            'help_type': str            # 'dialog' | 'view' | 'browser' (optional)
        }
        context: {
            'main_app': V2MainAppComplete
        }
        gcs: GlobalCentralSystemsteuerung
    
    Returns:
        True bei Erfolg
    """
    logger.info("🔵 Handler: show_help")
    
    help_topic = params.get('help_topic', 'Allgemein')
    help_text = params.get('help_text')
    help_type = params.get('help_type', 'dialog')
    
    logger.info(f"   Hilfe-Thema: {help_topic}")
    logger.info(f"   Hilfe-Typ: {help_type}")
    
    try:
        if help_type == 'dialog':
            # Einfacher Hilfe-Dialog
            title = f"Hilfe - {help_topic}"
            
            if not help_text:
                help_text = f"""
<h3>{help_topic}</h3>
<p>Hilfe für dieses Thema ist in Vorbereitung.</p>
<p>Weitere Informationen finden Sie in der Dokumentation.</p>
                """
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle(title)
            msg.setText(help_text)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            
            logger.info("✅ Hilfe-Dialog angezeigt")
            return True
        
        elif help_type == 'view':
            # Hilfe in eigener View
            main_app = context.get('main_app')
            if main_app and hasattr(main_app, 'show_text_klein'):
                main_app.show_text_klein(help_text or f"Hilfe: {help_topic}")
                logger.info("✅ Hilfe in View angezeigt")
                return True
        
        else:
            logger.warning(f"⚠️ Unbekannter help_type: {help_type}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Anzeigen der Hilfe: {e}")
        import traceback
        traceback.print_exc()
        return False
