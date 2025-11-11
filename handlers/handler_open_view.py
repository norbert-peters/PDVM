"""
Handler: View öffnen (V2.0)
============================
Öffnet eine View direkt im workspace_frame (Matrix-basiert)

V3.1: Verwendet skip_clear=False (default) → Arbeitsbereich wird geleert

FUNKTIONSWEISE:
- Lädt View-Konfiguration aus sys_viewdaten
- Erstellt V2PdvmViewController mit Matrix-Pipeline
- Zeigt View-Widget im workspace_frame an

Autor: PDVM V2.0
Datum: 05.11.2025
"""

import logging
from PyQt5.QtWidgets import QVBoxLayout

logger = logging.getLogger(__name__)

# V3.1: Handler-Metadaten für Pipeline
SKIP_CLEAR = False  # Arbeitsbereich leeren (default)


def execute(params: dict, context: dict, gcs) -> bool:
    """
    Öffnet eine View direkt im workspace_frame via Pipeline (Matrix-basiert)
    
    V3.1: Verwendet workspace_pipeline() mit skip_clear=False (default)
    → Arbeitsbereich wird geleert, neue View wird angezeigt
    
    Args:
        params: {
            'view_guid': str,       # GUID der View (required)
            'title': str            # View-Titel (optional, wird aus sys_viewdaten geladen)
        }
        context: {
            'main_app': MainAppComplete,    # Hauptanwendung mit workspace_pipeline
            'menu_handler': V3MenuHandler   # Menü-Handler
        }
        gcs: GlobalCentralSystemsteuerung
    
    Returns:
        True bei Erfolg
    """
    logger.info("🔵 Handler: open_view (V3.1 Pipeline-basiert)")
    
    # 1. Parameter validieren
    view_guid = params.get('view_guid')
    if not view_guid:
        logger.error("❌ Parameter 'view_guid' fehlt")
        return False
    
    title = params.get('title', 'View')
    
    logger.info(f"   View-GUID: {view_guid}")
    logger.info(f"   Titel: {title}")
    
    # 2. Context validieren
    main_app = context.get('main_app')
    if not main_app:
        logger.error("❌ main_app nicht im Context")
        return False
    
    # 3. GCS validieren
    if not gcs:
        logger.error("❌ GCS nicht verfügbar")
        return False
    
    # 4. View-Controller-Funktion für Pipeline vorbereiten
    def _create_and_show_view():
        """Erstellt View-Controller und fügt Widget in workspace_layout ein"""
        try:
            from pdvm_view_controller import V2PdvmViewController
            
            logger.info("🔧 Erstelle View-Controller...")
            
            # call_daten für Controller vorbereiten
            call_daten = {
                'view_guid': view_guid,
                'title': title,
                'first_call': False,
                'test_mode': False
            }
            
            # Controller erstellen (parent ist workspace_container)
            controller = V2PdvmViewController(
                call_daten=call_daten,
                parent=main_app.workspace_container
            )
            
            # Controller initialisieren (lädt Daten, erstellt Matrix, baut UI)
            logger.info("🚀 Initialisiere View-Controller (Matrix-Pipeline)...")
            success = controller.initialize()
            
            if not success:
                logger.error("❌ Controller-Initialisierung fehlgeschlagen")
                return False
            
            # Widget holen
            view_widget = controller.get_widget()
            if not view_widget:
                logger.error("❌ View-Widget konnte nicht erstellt werden")
                return False
            
            logger.info("✅ View-Widget erfolgreich erstellt")
            
            # V3.1: Widget direkt in workspace_container einfügen
            # Workspace-Container hat schon ein Layout (aus pdvm_systemstart.py)
            workspace_layout = main_app.workspace_container.layout()
            
            # Falls kein Layout vorhanden, erstelle eins
            if not workspace_layout:
                from PyQt5.QtWidgets import QVBoxLayout
                workspace_layout = QVBoxLayout(main_app.workspace_container)
                workspace_layout.setContentsMargins(0, 0, 0, 0)
                workspace_layout.setSpacing(0)
            
            # Altes Widget entfernen (falls vorhanden)
            while workspace_layout.count():
                child = workspace_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            # Neues Widget einfügen
            workspace_layout.addWidget(view_widget)
            
            # Referenz für Stichtag-Refresh speichern
            main_app.current_view_controller = controller
            main_app.current_view_widget = view_widget
            
            logger.info(f"✅ View erfolgreich geöffnet: {view_guid}")
            logger.info(f"   📊 Titel: {title}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Öffnen der View: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    # 5. V3.1: Pipeline aufrufen (skip_clear=False → Arbeitsbereich leeren)
    # Pipeline wurde bereits vom menu_handler aufgerufen!
    # Wir müssen hier NUR die View erstellen und einfügen
    return _create_and_show_view()
