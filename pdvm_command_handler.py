# pdvm_command_handler.py
import json
import logging

logger = logging.getLogger(__name__)
logger.info("🔹 PdvmCommandHandler initialisiert")

class PdvmCommandHandler:
    def __init__(self, app):
        """Initialisiert den PdvmCommandHandler mit der App-Instanz und PdvmMenu."""
        self.app = app  # MainApp-Instanz
        self.user_daten = app.user_daten
        self.key = ""

    def execute_command(self, key):
        """Führt das Kommando für den gegebenen Menü-Key aus."""
        logger.info(f"🔹 PdvmCommandHandler: geladene Struktur: {json.dumps(
            self.app.menu_handler.commands_structure, indent=2)}")
        key = key.replace(".", "_")  
        logger.info(f"🔹 PdvmCommandHandler: execute_command aufgerufen mit Key: {key}")
        self.key = key
        command_str = self.app.menu_handler.menu.get_command(key)

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
                self.show_text_klein(f"⚠️ Fehler beim Ausführen von '{command_str}': {e}")
        else:
            self.show_text_klein(f"⚠️ Kein Kommando für Menüpunkt '{key}' hinterlegt.")

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