"""
V2 Command Handler
==================
Führt Menü-Commands mit Security-Prüfung aus

Command-System:
- Commands in COMMANDS-Container gespeichert
- Security Profile Prüfung gegen gcs._u_db
- Standard-GUID 888... → Alle dürfen
- Alternative Security GUIDs → Nur mit Berechtigung

Autor: PDVM V2.0
Datum: 01.11.2025
"""

import logging
from typing import Optional, Dict, Any, List
from PyQt5.QtWidgets import QMessageBox

from v2_menu_schema import MenuCommand
from v2_menu_storage import get_menu_storage
from v2_central_systemsteuerung import get_gcs
from handlers import get_handler_registry

logger = logging.getLogger(__name__)


class V2CommandHandler:
    """
    Command Handler mit Security-Prüfung
    
    Workflow:
    1. Lade Command aus menu_storage
    2. Prüfe Security Profile gegen user_data
    3. Führe Handler-Funktion aus
    """
    
    def __init__(self):
        """Initialisiert Command Handler"""
        self.gcs = get_gcs()
        if not self.gcs:
            raise RuntimeError("GCS nicht initialisiert")
        
        self.storage = get_menu_storage()
        if not self.storage:
            raise RuntimeError("Menu Storage nicht initialisiert")
        
        # Handler-Registry (dynamisches Laden)
        self.handler_registry = get_handler_registry()
        
        logger.info("✅ V2CommandHandler initialisiert")
    
    def register_handler(self, handler_name: str, handler_func: callable):
        """
        Registriert benutzerdefinierten Handler
        
        Args:
            handler_name: Name des Handlers (z.B. "open_view")
            handler_func: Funktion mit Signatur (params: Dict, context: Dict, gcs) -> bool
        """
        self.handler_registry.register(handler_name, handler_func)
        logger.info(f"✅ Handler manuell registriert: {handler_name}")
    
    def execute(
        self, 
        menu_guid: str, 
        command_guid: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Führt Command aus mit Security-Prüfung
        
        Args:
            menu_guid: GUID des Menüs
            command_guid: GUID des Commands
            context: Zusätzlicher Kontext (z.B. selected_item, current_view)
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # 1. Lade Command
            command = self.storage.get_command(menu_guid, command_guid)
            if not command:
                logger.error(f"❌ Command nicht gefunden: {command_guid}")
                self._show_error("Command nicht gefunden", 
                                f"Command {command_guid} existiert nicht im Menü")
                return False
            
            logger.info(f"🎯 Führe Command aus: {command.NAME}")
            
            # 2. Security-Prüfung
            if not self._check_security(command):
                logger.warning(f"⚠️ Keine Berechtigung für Command: {command.NAME}")
                self._show_error("Keine Berechtigung", 
                                f"Sie haben keine Berechtigung für diese Aktion")
                return False
            
            # 3. Handler finden (dynamisch laden falls nötig)
            handler = self.handler_registry.get(command.HANDLER)
            if not handler:
                logger.error(f"❌ Handler nicht gefunden: {command.HANDLER}")
                self._show_error("Handler nicht gefunden", 
                                f"Handler '{command.HANDLER}' ist nicht registriert")
                return False
            
            # 4. Command ausführen (neue Signatur mit gcs)
            context = context or {}
            success = handler(command.PARAMS, context, self.gcs)
            
            if success:
                logger.info(f"✅ Command erfolgreich: {command.NAME}")
            else:
                logger.warning(f"⚠️ Command fehlgeschlagen: {command.NAME}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Command-Ausführung: {e}")
            self._show_error("Fehler", f"Fehler bei Command-Ausführung: {str(e)}")
            return False
    
    def _check_security(self, command: MenuCommand) -> bool:
        """
        Prüft Security Profile
        
        Logik:
        - Standard-GUID 888... → Immer erlaubt
        - Sonst: User muss eines der SEC_PROFILES haben
        
        Args:
            command: MenuCommand mit Security-Einstellungen
            
        Returns:
            True wenn erlaubt
        """
        # Standard-GUID → Alle dürfen
        if command.SEC_PROFILE_DEFAULT.startswith("88888888"):
            logger.info(f"   ✓ Standard-Security (888...) - Zugriff erlaubt")
            return True
        
        # Hole User Security Profiles aus gcs._u_db
        try:
            user_data = self.gcs._user_data
            permissions = user_data.get('PERMISSIONS', {})
            user_sec_profiles = permissions.get('SEC_PROFILES', [])
            
            logger.info(f"   🔍 User Security Profiles: {user_sec_profiles}")
            logger.info(f"   🔍 Benötigte Profiles: {command.SEC_PROFILES}")
            
            # Prüfe ob User eines der benötigten Profile hat
            allowed = command.is_allowed_for_user(user_sec_profiles)
            
            if allowed:
                logger.info(f"   ✓ Security-Prüfung bestanden")
            else:
                logger.warning(f"   ✗ Security-Prüfung fehlgeschlagen")
            
            return allowed
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Security-Prüfung: {e}")
            return False
    
    def _show_error(self, title: str, message: str):
        """Zeigt Fehler-Dialog"""
        try:
            QMessageBox.warning(None, title, message)
        except:
            # Fallback wenn GUI nicht verfügbar
            logger.error(f"GUI-Error: {title} - {message}")


# ===== GLOBAL INSTANCE =====
_handler_instance: Optional[V2CommandHandler] = None


def get_command_handler() -> Optional[V2CommandHandler]:
    """
    Gibt globale Command Handler Instanz zurück
    
    Singleton-Pattern für V2CommandHandler
    """
    global _handler_instance
    
    if _handler_instance is None:
        try:
            _handler_instance = V2CommandHandler()
        except Exception as e:
            logger.error(f"❌ Fehler beim Initialisieren von Command Handler: {e}")
            return None
    
    return _handler_instance


if __name__ == "__main__":
    # ===== TEST =====
    print("🧪 V2 Command Handler Test")
    print("=" * 60)
    print("⚠️ HINWEIS: Test benötigt initialisiertes GCS")
    print("   Führe v2_main.py aus für vollständigen Test")
    print("=" * 60)
    
    # Teste nur Import
    from v2_menu_schema import create_command, MenuCommand
    
    print("\n✅ Import erfolgreich")
    print("   MenuCommand: ✓")
    print("   V2CommandHandler: ✓")
    
    # Teste Command-Erstellung
    cmd = create_command(
        "cmd-test",
        "test_command",
        "open_view",
        params={'view_guid': 'test-view-123'},
        sec_profiles=['sec-admin']
    )
    
    print(f"\n✅ Test-Command erstellt:")
    print(f"   Name: {cmd.NAME}")
    print(f"   Handler: {cmd.HANDLER}")
    print(f"   Security: {cmd.SEC_PROFILES}")
    
    # Teste Security-Prüfung (ohne User)
    user_profiles = ['sec-admin', 'sec-user']
    allowed = cmd.is_allowed_for_user(user_profiles)
    print(f"\n✅ Security Test:")
    print(f"   User Profiles: {user_profiles}")
    print(f"   Erlaubt: {allowed}")
    
    print("\n🎯 Command Handler Module Ready!")
