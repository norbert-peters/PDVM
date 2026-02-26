"""
PDVM Welcome Screen - Autonomes UI-Modul

ARCHITEKTUR:
- Vollständig autonom - holt GCS für Mandanten-/User-Info
- render(container) fügt Widget zu Container hinzu
- Keine Rückgabewerte nötig
- Container wird vom Aufrufer bereitgestellt

VERWENDUNG:
    from pdvm_welcome_screen import PdvmWelcomeScreen
    
    # Container bereitstellen
    workspace_container = QWidget()
    
    # Autonomes Rendering
    PdvmWelcomeScreen.render(workspace_container)
"""

import logging
from PyQt5.QtWidgets import QTextEdit, QVBoxLayout
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)


class PdvmWelcomeScreen:
    """
    Autonomer Willkommensbildschirm mit System-/Mandanten-Info.
    
    Zeigt:
    - Willkommensnachricht
    - Mandanten-Name
    - Benutzer-Name
    - System-Version
    """
    
    @staticmethod
    def render(container, app_name=None):
        """
        Rendert Willkommensbildschirm autonom in Container.
        
        Args:
            container: QWidget Container für Welcome-Screen
            app_name: Optional - Name der geöffneten Anwendung
            
        Returns:
            None (Widget wird direkt zu Container hinzugefügt)
        """
        logger.info("🔧 PdvmWelcomeScreen.render() gestartet...")
        
        # GCS holen (autonom!)
        from pdvm_central_systemsteuerung import get_gcs
        gcs = get_gcs()
        
        if not gcs:
            logger.error("❌ GCS nicht verfügbar - kann Welcome-Screen nicht rendern")
            return
        
        logger.info("✅ GCS verfügbar")
        
        # Layout holen (wurde bei Startup erstellt)
        logger.info(f"🔍 DEBUG: Container-Typ: {type(container)}")
        logger.info(f"🔍 DEBUG: Container-ID: {id(container)}")
        layout = container.layout()
        logger.info(f"🔍 DEBUG: Layout von container.layout(): {layout}")
        logger.info(f"🔍 DEBUG: Layout ist None? {layout is None}")
        logger.info(f"🔍 DEBUG: Layout bool()? {bool(layout)}")
        logger.info(f"🔍 DEBUG: Layout count()? {layout.count() if layout else 'N/A'}")
        
        if layout is None:
            logger.error("❌ Workspace-Container hat kein Layout! Dies sollte nicht passieren.")
            return
        
        # TextEdit Widget erstellen
        welcome_widget = QTextEdit()
        welcome_widget.setReadOnly(True)
        welcome_widget.setStyleSheet("""
            QTextEdit {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                padding: 20px;
                font-size: 12pt;
            }
        """)
        
        # HTML-Content erstellen
        html_content = PdvmWelcomeScreen._create_welcome_html(gcs, app_name)
        welcome_widget.setHtml(html_content)
        
        # Widget zu Container hinzufügen
        layout.addWidget(welcome_widget)
        
        logger.info("✅ PdvmWelcomeScreen gerendert")
    
    @staticmethod
    def _create_welcome_html(gcs, app_name=None):
        """
        Erstellt HTML-Content für Willkommensbildschirm.
        
        Args:
            gcs: Global Control System Instanz
            app_name: Optional - Name der geöffneten Anwendung
            
        Returns:
            str: HTML-Content
        """
        # Mandanten-Info aus GCS
        try:
            mandant_data = gcs._mandant_data
            root_data = mandant_data.get('ROOT', {})
            mandant_name = root_data.get('BEZEICHNUNG', 'Unbekannt')
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Mandanten-Info: {e}")
            mandant_name = 'Unbekannt'
        
        # User-Info aus GCS
        try:
            user_data = gcs._user_data
            user_info = user_data.get('USER', {})
            anrede = user_info.get('ANREDE', '')
            vorname = user_info.get('VORNAME', '')
            name = user_info.get('NAME', '')
            user_name = f"{anrede} {vorname} {name}".strip() or 'Unbekannt'
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der User-Info: {e}")
            user_name = 'Unbekannt'
        
        # Version aus GCS
        version = gcs.version if hasattr(gcs, 'version') else '0.0'
        
        # Titel anpassen basierend auf App-Name
        if app_name:
            title = f"🎉 Willkommen im PDVM {app_name}"
        else:
            title = "🎉 Willkommen im PDVM-System"
        
        # HTML erstellen
        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: white;
                    color: #333;
                    padding: 40px;
                    text-align: center;
                }}
                h1 {{
                    font-size: 36px;
                    margin-bottom: 10px;
                    color: #667eea;
                    text-shadow: none;
                }}
                .subtitle {{
                    font-size: 18px;
                    margin-bottom: 40px;
                    color: #666;
                }}
                .info-box {{
                    background-color: #f5f5f5;
                    border: 1px solid #ddd;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .info-item {{
                    margin: 15px 0;
                    font-size: 14px;
                    color: #333;
                }}
                .info-label {{
                    font-weight: bold;
                    color: #555;
                }}
                .info-value {{
                    font-size: 16px;
                    margin-left: 10px;
                    color: #333;
                }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <div class="subtitle">Personal Daten Verwaltungs Management System</div>
            
            <div class="info-box">
                <div class="info-item">
                    <span class="info-label">📁 Mandant:</span>
                    <span class="info-value">{mandant_name}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">👤 Benutzer:</span>
                    <span class="info-value">{user_name}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">🚀 Version:</span>
                    <span class="info-value">{version}</span>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
