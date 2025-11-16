# -*- coding: utf-8 -*-
"""
PDVM Menu Handler - Menü-Aktionen ausführen

Führt Menü-Aktionen aus basierend auf command-Daten.
Verwendet Handler-Registry aus handlers/ Verzeichnis.
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

_MENU_HANDLER_INSTANCE: Optional['PdvmMenuHandler'] = None

def get_menu_handler(main_window) -> 'PdvmMenuHandler':
    global _MENU_HANDLER_INSTANCE
    if _MENU_HANDLER_INSTANCE is None:
        logger.info("Menu-Handler erstellt")
        _MENU_HANDLER_INSTANCE = PdvmMenuHandler(main_window)
    return _MENU_HANDLER_INSTANCE

class PdvmMenuHandler:
    def __init__(self, main_window):
        self.main_window = main_window
        
        # Handler-Registry importieren
        from handlers import get_handler_registry
        self.handler_registry = get_handler_registry()
        
        # Zusatzmenü-Verwaltung
        self._zusatz_mapping = {}  # {item_guid: zusatz_guid} Mapping
        self._current_menu_matrix = []  # Aktuelle Menu-Matrix für Zusatzmenü-Ermittlung
        
        logger.info("Menu-Handler initialisiert")
    
    def set_menu_matrix(self, menu_matrix: list, replace: bool = False):
        """
        Setzt aktuelle Menu-Matrix und baut Zusatzmenü-Mapping auf.
        
        Wird bei jedem Menü-Wechsel aufgerufen (load_startmenu, load_menu).
        
        Args:
            menu_matrix: Komplette Menu-Matrix (VERTIKAL oder GRUND)
            replace: True = Mapping ersetzen, False = Mapping erweitern (default)
        """
        self._current_menu_matrix = menu_matrix
        
        # Zusatzmenü-Mapping aufbauen
        from pdvm_central_systemsteuerung import get_gcs
        gcs = get_gcs()
        if gcs:
            new_mapping = gcs.build_zusatzmenu_mapping(menu_matrix)
            
            if replace:
                # Komplettes Mapping ersetzen
                self._zusatz_mapping = new_mapping
                logger.info(f"✅ Zusatzmenü-Mapping ersetzt: {len(self._zusatz_mapping)} Zuordnungen")
            else:
                # Mapping erweitern (merge)
                self._zusatz_mapping.update(new_mapping)
                logger.info(f"✅ Zusatzmenü-Mapping erweitert: {len(new_mapping)} neue Zuordnungen (gesamt: {len(self._zusatz_mapping)})")
        else:
            logger.warning("⚠️ GCS nicht verfügbar - Zusatzmenü-Mapping konnte nicht erstellt werden")
    
    def execute_command(self, command_data: Dict[str, Any]) -> bool:
        """
        Führt Command aus basierend auf Handler-Name und Params.
        
        Command-Format:
            {"handler": "logout", "params": {}}
            {"handler": "open_app_menu", "params": {"app_name": "PERSONALWESEN"}}
        
        Args:
            command_data: Dict mit 'handler' und 'params'
            
        Returns:
            True bei Erfolg
        """
        if not command_data:
            logger.warning("⚠️ Kein Command-Data übergeben")
            return False
        
        handler_name = command_data.get('handler')
        params = command_data.get('params', {})
        
        if not handler_name:
            logger.warning("⚠️ Kein Handler-Name in Command-Data")
            return False
        
        # Handler aus Registry holen (lädt automatisch bei Bedarf)
        handler_func = self.handler_registry.get(handler_name)
        
        if not handler_func:
            logger.error(f"❌ Unbekannter Handler: {handler_name}")
            return False
        
        try:
            # Handler aufrufen mit Standard-Signatur
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            context = {
                'main_app': self.main_window,
                'menu_handler': self
            }
            
            logger.info(f"🔧 Führe Handler aus: {handler_name}")
            result = handler_func(params, context, gcs)
            
            if result:
                logger.info(f"✅ Handler erfolgreich: {handler_name}")
            else:
                logger.warning(f"⚠️ Handler gab False zurück: {handler_name}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Handler-Fehler '{handler_name}': {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def execute_command_with_zusatz(self, command_data: Dict[str, Any], item_guid: str) -> bool:
        """
        Führt Command aus UND aktualisiert Zusatzmenü.
        
        Workflow:
        1. Command normal ausführen
        2. Zusatzmenü für item_guid ermitteln
        3. Horizontales Menü neu rendern (GRUND + ZUSATZ)
        
        Args:
            command_data: Dict mit 'handler' und 'params'
            item_guid: GUID des geklickten Menu-Items
            
        Returns:
            True bei Erfolg
        """
        # 1. Command normal ausführen
        result = self.execute_command(command_data)
        
        # 2. Zusatzmenü ermitteln und rendern
        self._update_zusatzmenu(item_guid)
        
        return result
    
    def _update_zusatzmenu(self, item_guid: str):
        """
        Aktualisiert Zusatzmenü basierend auf item_guid.
        
        Args:
            item_guid: GUID des aktiven Menu-Items
        """
        try:
            from pdvm_central_systemsteuerung import get_gcs
            from pdvm_menu_system_autonomous import PdvmMenuSystemAutonomous
            
            gcs = get_gcs()
            if not gcs:
                logger.warning("⚠️ GCS nicht verfügbar - Zusatzmenü kann nicht aktualisiert werden")
                return
            
            # Zusatzmenü-GUID für Item ermitteln (aus Mapping)
            zusatz_guid = gcs.get_zusatzmenu_for_item(item_guid, self._zusatz_mapping)
            
            if zusatz_guid:
                logger.info(f"📎 Zusatzmenü aktiv für Item '{item_guid}': {zusatz_guid}")
                
                # Zusatzmenü-Daten laden
                zusatz_matrix = gcs.load_zusatzmenu_data(zusatz_guid)
                
                # GRUND-Matrix holen (aus aktueller Menu-Matrix)
                grund_matrix = self._current_menu_matrix
                
                # Horizontales Menü neu rendern (GRUND + ZUSATZ)
                grund_container = gcs._menu_containers.get('grund')
                if grund_container:
                    PdvmMenuSystemAutonomous.render_horizontal_combined(
                        grund_matrix=grund_matrix,
                        zusatz_matrix=zusatz_matrix,
                        container=grund_container,
                        menu_handler=self,
                        gcs=gcs
                    )
                    logger.info("✅ Horizontales Menü mit Zusatzmenü aktualisiert")
                else:
                    logger.warning("⚠️ GRUND-Container nicht verfügbar")
            else:
                logger.info(f"📋 Kein Zusatzmenü für Item '{item_guid}' - nur GRUND-Menü")
                
                # Nur GRUND-Menü rendern (ohne ZUSATZ)
                grund_matrix = self._current_menu_matrix
                grund_container = gcs._menu_containers.get('grund')
                if grund_container:
                    PdvmMenuSystemAutonomous.render_horizontal_combined(
                        grund_matrix=grund_matrix,
                        zusatz_matrix=[],  # Leeres Zusatzmenü
                        container=grund_container,
                        menu_handler=self,
                        gcs=gcs
                    )
                    logger.info("✅ Horizontales Menü ohne Zusatzmenü aktualisiert")
        
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren des Zusatzmenüs: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def register_handler(self, name: str, handler: callable):
        """
        Registriert Handler manuell (für Erweiterungen)
        
        Args:
            name: Handler-Name
            handler: Handler-Funktion
        """
        self.handler_registry.register(name, handler)
        logger.info(f"✅ Handler registriert: {name}")
    
    def _clear_workspace_and_show_welcome(self) -> None:
        """
        Cleart den Workspace-Container und zeigt Welcome-Screen an.
        
        V0.9-Style: Entfernt nur Widgets, behält Layout bei.
        """
        try:
            workspace = self.main_window.workspace_container
            logger.info(f"🔍 DEBUG: Workspace-Container-Typ: {type(workspace)}")
            logger.info(f"🔍 DEBUG: Workspace-Container-ID: {id(workspace)}")
            layout = workspace.layout()
            logger.info(f"🔍 DEBUG: Layout von workspace.layout(): {layout}")
            logger.info(f"🔍 DEBUG: Layout ist None? {layout is None}")
            logger.info(f"🔍 DEBUG: Layout bool()? {bool(layout)}")
            
            if layout is None:
                logger.error("❌ Workspace hat kein Layout! Dies sollte nicht passieren.")
                return
            
            # Alle Widgets entfernen (Layout bleibt!)
            widget_count = layout.count()
            logger.info(f"🧹 Entferne {widget_count} Widgets aus Workspace...")
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    widget = child.widget()
                    logger.debug(f"  🗑️ Entferne Widget: {widget.__class__.__name__}")
                    widget.deleteLater()
            
            # WICHTIG: Event-Loop verarbeiten, damit Widgets SOFORT gelöscht werden
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()
            
            logger.info("🧹 Workspace geleert")
            
            # Welcome-Screen anzeigen (mit aktuellem App-Namen, falls vorhanden)
            from pdvm_welcome_screen import PdvmWelcomeScreen
            app_name = getattr(self.main_window, '_current_app_name', None)
            PdvmWelcomeScreen.render(workspace, app_name)
            logger.info(f"✅ Welcome-Screen angezeigt (App: {app_name or 'PDVM System'})")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Clearen des Workspace: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def load_startmenu(self) -> bool:
        """
        Lädt Startmenü neu (kehrt zum Hauptmenü zurück)
        
        Lädt die Startmenü-GUID aus der Datenbank und rendert das Menü neu.
        
        Returns:
            True bei Erfolg
        """
        logger.info("🔧 Lade Startmenü neu...")
        
        try:
            from pdvm_central_systemsteuerung import get_gcs
            from pdvm_menu_system_autonomous import PdvmMenuSystemAutonomous
            
            gcs = get_gcs()
            if not gcs:
                logger.error("❌ GCS nicht verfügbar")
                return False
            
            # Beim Startmenü-Wechsel App-Name zurücksetzen (Hauptmenü)
            self.main_window._current_app_name = None
            
            # MENÜWECHSEL: Workspace clearen + Welcome-Screen anzeigen
            self._clear_workspace_and_show_welcome()
            
            # Hole Startmenü-GUID aus menu_system_db
            try:
                menu_db = gcs._menu_system_db
                startmenu_guid_data, _ = menu_db.get_value(gcs.user_guid, 'startmenu')
                startmenu_guid = startmenu_guid_data if startmenu_guid_data else '5ca6674e-b9ce-4581-9756-64e742883f80'
                logger.info(f"📋 Startmenü-GUID: {startmenu_guid}")
            except Exception as e:
                logger.warning(f"⚠️ Konnte Startmenü-GUID nicht laden: {e}")
                startmenu_guid = '5ca6674e-b9ce-4581-9756-64e742883f80'
                logger.info(f"📋 Verwende Standard-Startmenü-GUID: {startmenu_guid}")
            
            # Setze GUID in menu_system_db
            gcs._menu_system_db.set_guid(startmenu_guid)
            logger.info(f"✅ Menu-System-DB GUID auf Startmenü gesetzt: {startmenu_guid}")
            
            # Rendere Startmenü
            PdvmMenuSystemAutonomous.load_startmenu(startmenu_guid, self)
            
            # Stelle Menü-Sichtbarkeit wieder her
            if hasattr(self.main_window, 'restore_menu_visibility'):
                self.main_window.restore_menu_visibility()
            
            logger.info("✅ Startmenü geladen")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Startmenüs: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def load_menu(self, menu_guid: str) -> bool:
        """
        Lädt spezifisches Menü
        
        Args:
            menu_guid: GUID des zu ladenden Menüs
            
        Returns:
            True bei Erfolg
        """
        logger.info(f"🔧 Lade Menü: {menu_guid}")
        
        try:
            from pdvm_central_systemsteuerung import get_gcs
            from pdvm_menu_system_autonomous import PdvmMenuSystemAutonomous
            
            gcs = get_gcs()
            if not gcs:
                logger.error("❌ GCS nicht verfügbar")
                return False
            
            # MENÜWECHSEL: Workspace clearen + Welcome-Screen anzeigen
            self._clear_workspace_and_show_welcome()
            
            # Setze GUID in menu_system_db
            gcs._menu_system_db.set_guid(menu_guid)
            logger.info(f"✅ Menu-System-DB GUID gesetzt: {menu_guid}")
            
            # Rendere Menü
            PdvmMenuSystemAutonomous.load_startmenu(menu_guid, self)
            
            # Stelle Menü-Sichtbarkeit wieder her
            if hasattr(self.main_window, 'restore_menu_visibility'):
                self.main_window.restore_menu_visibility()
            
            logger.info("✅ Menü geladen")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Menüs: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
