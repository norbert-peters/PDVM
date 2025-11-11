"""
Handler: App-Menü öffnen
=========================
Lädt ein spezifisches App-Menü (Pipeline fügt Welcome-Screen mit App-Name ein)

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
    Öffnet App-Menü (Welcome-Screen mit App-Name kommt automatisch)
    
    V3.2: Lineare Pipeline-Logik
    STEP 3.1: Workspace wird geleert (skip_clear=False)
    STEP 3.2: Handler lädt Menü + setzt _current_app_name
    STEP 3.3: Pipeline prüft Workspace leer → fügt Welcome-Screen mit App-Name ein
    
    Args:
        params: {
            'app_name': str  # Name der Anwendung (z.B. 'TESTBEREICH')
        }
        context: {
            'menu_handler': PdvmMenuHandler,
            'main_app': MainAppComplete
        }
        gcs: GlobalCentralSystemsteuerung
    
    Returns:
        True bei Erfolg
    """
    logger.info("🔵 Handler: open_app_menu (V3.2 Lineare Pipeline)")
    
    app_name = params.get('app_name')
    if not app_name:
        logger.error("❌ Parameter 'app_name' fehlt")
        return False
    
    logger.info(f"   App-Name: {app_name}")
    
    try:
        # Hole menu_handler und main_app aus context
        menu_handler = context.get('menu_handler')
        main_app = context.get('main_app')
        
        if not menu_handler:
            logger.error("❌ menu_handler nicht im Context")
            return False
        
        if not main_app:
            logger.error("❌ main_app nicht im Context")
            return False
        
        # Hole Menu-GUID aus User-Daten
        user_data = gcs._user_data
        anwendungen = user_data.get('ANWENDUNGEN', {})
        
        # Suche nach App (case-insensitive)
        app_key = None
        for key in anwendungen.keys():
            if key.upper() == app_name.upper():
                app_key = key
                break
        
        if not app_key:
            # App nicht gefunden = keine Berechtigung
            logger.warning(f"⚠️ Keine Berechtigung für App '{app_name}'")
            
            from PyQt5.QtWidgets import QMessageBox
            
            msg = QMessageBox(main_app)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Keine Berechtigung")
            msg.setText(f"<b>Zugriff auf '{app_name}' nicht möglich</b>")
            msg.setInformativeText(
                "Sie haben keine Berechtigung für diese Anwendung.\n\n"
                "Bitte setzen Sie sich mit Ihrem Administrator in Verbindung."
            )
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            
            return False
        
        # Hole Menu-GUID
        app_data = anwendungen[app_key]
        menu_guid = app_data.get('MENU')
        
        if not menu_guid:
            logger.error(f"❌ Keine Menu-GUID für Anwendung '{app_name}'")
            
            # Zeige Konfigurations-Fehler
            from PyQt5.QtWidgets import QMessageBox
            
            msg = QMessageBox(main_app)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Konfigurationsfehler")
            msg.setText(f"<b>Menü für '{app_name}' nicht konfiguriert</b>")
            msg.setInformativeText(
                "Die Anwendung hat keine Menü-Konfiguration.\n\n"
                "Bitte setzen Sie sich mit Ihrem Administrator in Verbindung."
            )
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            
            return False
        
        logger.info(f"   Menu-GUID: {menu_guid}")
        
        # V3.2: Menü laden (Pipeline fügt Welcome-Screen automatisch ein!)
        try:
            if hasattr(menu_handler, 'load_menu'):
                success = menu_handler.load_menu(menu_guid)
                
                if success:
                    logger.info(f"✅ App-Menü geladen: {app_name}")
                    
                    # V3.2: KEIN _show_welcome_message() mehr!
                    # Pipeline erstellt NEUES Widget in STEP 3.3 (altes wurde in STEP 3.1 gelöscht)
                    
                    # V3.2: Speichere App-Name für Welcome-Screen Anpassung
                    main_app._current_app_name = app_name
                    logger.info(f"✅ App-Name gespeichert für Welcome-Screen: {app_name}")
                    
                    return True
                else:
                    logger.error(f"❌ Menü '{menu_guid}' konnte nicht geladen werden")
                    
                    # Zeige Fehlermeldung
                    from PyQt5.QtWidgets import QMessageBox
                    
                    msg = QMessageBox(main_app)
                    msg.setIcon(QMessageBox.Critical)
                    msg.setWindowTitle("Menü nicht verfügbar")
                    msg.setText(f"<b>Menü für '{app_name}' nicht gefunden</b>")
                    msg.setInformativeText(
                        f"Das konfigurierte Menü (GUID: {menu_guid[:8]}...) "
                        f"konnte nicht geladen werden.\n\n"
                        f"Bitte setzen Sie sich mit Ihrem Administrator in Verbindung."
                    )
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                    
                    return False
            else:
                logger.error("❌ load_menu() nicht verfügbar")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Menüs: {e}")
            
            # Zeige Fehlermeldung
            from PyQt5.QtWidgets import QMessageBox
            
            msg = QMessageBox(main_app)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Fehler")
            msg.setText(f"<b>Fehler beim Laden von '{app_name}'</b>")
            msg.setInformativeText(
                f"Ein Fehler ist aufgetreten:\n{str(e)}\n\n"
                f"Bitte setzen Sie sich mit Ihrem Administrator in Verbindung."
            )
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            
            return False
            
    except Exception as e:
        logger.error(f"❌ Fehler beim Öffnen des App-Menüs: {e}")
        import traceback
        traceback.print_exc()
        return False
