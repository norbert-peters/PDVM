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
        
        logger.info("Menu-Handler initialisiert")
    
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
    
    def register_handler(self, name: str, handler: callable):
        """
        Registriert Handler manuell (für Erweiterungen)
        
        Args:
            name: Handler-Name
            handler: Handler-Funktion
        """
        self.handler_registry.register(name, handler)
        logger.info(f"✅ Handler registriert: {name}")
    
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
        Lädt ein spezifisches Menü (z.B. App-Menü)
        
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
            
            # ULTRA EINFACH: Setze neue GUID in menu_system_db
            gcs._menu_system_db.set_guid(menu_guid)
            logger.info(f"✅ Menu-System-DB GUID gewechselt: {menu_guid}")
            
            # Rendere Menü (mit neuer GUID in DB)
            PdvmMenuSystemAutonomous.load_startmenu(menu_guid, self)
            
            # Stelle Menü-Sichtbarkeit wieder her
            if hasattr(self.main_window, 'restore_menu_visibility'):
                self.main_window.restore_menu_visibility()
            
            logger.info(f"✅ Menü geladen: {menu_guid}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Menüs {menu_guid}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
