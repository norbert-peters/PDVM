from global_gcs import gcs
# pdvm_command_handler.py
import json
import logging

logger = logging.getLogger(__name__)
logger.info("🔹 PdvmCommandHandler initialisiert")

class PdvmCommandHandler:
    def __init__(self, app):
        """Initialisiert den PdvmCommandHandler mit der App-Instanz und PdvmMenu."""
        self.app = app  # MainApp-Instanz
#        self.user_daten = gcs.user_data
        self.key = ""

    def execute_command(self, key):
        """Führt das Kommando für den gegebenen Menü-Key aus."""
        logger.info(f"🔹 PdvmCommandHandler: geladene Struktur: {json.dumps(
            self.app.menu_handler.commands_structure, indent=2)}")
        key = key.replace(".", "_")  
        logger.info(f"🔹 PdvmCommandHandler: execute_command aufgerufen mit Key: {key}")
        self.key = key
        command_str = self.app.menu_handler.menu.get_command(key)

        # Spezielle Behandlung für Dialog-Funktionen wenn kein direkter Command gefunden wird
        if not command_str and key.startswith("Dialog_"):
            logger.info(f"🔹 PdvmCommandHandler: Dialog-Kommando erkannt, versuche zentrale Funktion: {key}")
            if self._handle_dialog_command(key):
                return
        
        if command_str:
            logger.info(f"🔹 PdvmCommandHandler: Befehl für '{key}' gefunden: {command_str}")
            try:
                if "open_menu_editor" in command_str:
                    # Parameter extrahieren: menu_type und optional call_path
                    args_str = command_str[command_str.find("(")+1:command_str.rfind(")")]
                    parts = [p.strip().strip("'\"") for p in args_str.split(",")]
                    menu_type = parts[0]
                    call_path = parts[1] if len(parts) > 1 else None
                    logger.info(f"🔹 PdvmCommandHandler: open_menu_editor aufgerufen mit type={menu_type}, path={call_path}")
                    self.app.open_menu_editor(menu_type, call_path)
                else:
                    # eval für einfachere Befehle
                    eval(command_str, {"self": self.app})
            except Exception as e:
                logger.error(f"❌ Fehler beim Ausführen von '{command_str}': {e}")
                self.show_text_klein(f"⚠️ Fehler beim Ausführen von '{command_str}': {e}")
        else:
            logger.warning(f"⚠️ Kein Kommando für Menüpunkt '{key}' hinterlegt.")
            self.show_text_klein(f"⚠️ Kein Kommando für Menüpunkt '{key}' hinterlegt.")
    
    def _handle_dialog_command(self, key):
        """Behandelt spezielle Dialog-Kommandos direkt über das aktuelle Widget"""
        widget = self.app.get_current_unified_widget()
        if not widget:
            logger.warning("⚠️ Kein aktives Dialog-Widget für Menü-Kommando gefunden")
            self.show_text_klein("⚠️ Kein aktiver Dialog für diese Funktion")
            return False
            
        # Mapping der Menü-Keys zu Widget-Funktionen
        dialog_commands = {
            "Dialog_🔍 Lupe-Modi_🔍 View-Lupe": "set_view_lupe",
            "Dialog_🔍 Lupe-Modi_📝 Input-Lupe": "set_input_lupe", 
            "Dialog_🔍 Lupe-Modi_⚖️ Position wiederherstellen": "set_normal_mode",
            "Dialog_⚙️ Zentrale Funktionen_🗓️ Stichtag wechseln": "stichtag_wechsel",
            "Dialog_⚙️ Zentrale Funktionen_🔄 View refreshen": "refresh_view",
            "Dialog_⚙️ Zentrale Funktionen_💾 Daten speichern": "save_data",
            "Dialog_⚙️ Zentrale Funktionen_📊 Daten exportieren": "export_data",
            "Dialog_🎛️ Ansicht_🎛️ Menü ausblenden": "toggle_menu"
        }
        
        function_name = dialog_commands.get(key)
        if function_name:
            logger.info(f"🔹 PdvmCommandHandler: Führe Dialog-Funktion aus: {function_name}")
            try:
                widget.execute_central_function(function_name)
                return True
            except Exception as e:
                logger.error(f"❌ Fehler bei Dialog-Funktion {function_name}: {e}")
                self.show_text_klein(f"⚠️ Fehler bei {function_name}: {e}")
        
        return False

    def show_text(self, text):
        """Zeigt eine normale Textmeldung an."""
#        print(f"📢 {text}")
        self.app.show_text(text)
        
    def show_text_klein(self, text):
        """Zeigt eine kleine Textmeldung an."""
#        print(f"📢 {text}")
        self.app.show_text_klein(text)

    def logout(self):
        """Führt den Logout durch."""
        logger.info("🔹 PdvmCommandHandler: Logout wird durchgeführt.")
        self.app.logout()