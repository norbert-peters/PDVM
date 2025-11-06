
# === INTEGRATION IN HAUPTANWENDUNG ===

class MainApp:
    def __init__(self):
        self.unified_widget = None  # Wird gesetzt wenn Dialog geöffnet
        
    def open_unified_dialog(self):
        """Öffnet Unified Dialog und setzt Referenz für Menü-Kommandos"""
        call_data = {
            'app': self,
            'frame_guid': '4078079f-4028-45ed-879c-3c779ecf3d0d',
            'user_guid': '4886ad26-061b-4662-a762-c8c83f36692d'
        }
        
        self.unified_widget = UnifiedPdvmDialogWidget(call_data)
        self.unified_widget.show()
        
        # Zusatzmenü für Dialog-Kontext laden
        self.load_dialog_context_menu()
    
    def load_dialog_context_menu(self):
        """Lädt kontextspezifisches Zusatzmenü für Dialog"""
        try:
            dialog_menu = self.menu.get_submenu("PD_zusatz.PD_z_Menu.Dialog")
            self.update_horizontal_menu(dialog_menu)
            logger.info("✅ Dialog-Zusatzmenü geladen")
        except Exception as e:
            logger.warning(f"⚠️ Dialog-Zusatzmenü konnte nicht geladen werden: {e}")

# === KOMMANDO-AUSFÜHRUNG ===

def execute_unified_command(self, command_key):
    """Führt Unified Dialog Kommandos aus"""
    if not self.unified_widget:
        self.show_message("❌ Kein Dialog geöffnet")
        return
        
    # Kommando an Dialog weiterleiten
    if "execute_central_function" in command_key:
        # Extrahiere Funktionsname
        func_name = command_key.split("'")[1]
        result = self.unified_widget.execute_central_function(func_name)
        
        if result:
            self.show_message(f"✅ Funktion '{func_name}' ausgeführt")
        else:
            self.show_message(f"❌ Fehler bei Funktion '{func_name}'")
    