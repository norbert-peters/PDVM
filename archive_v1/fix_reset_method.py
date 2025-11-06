"""Script zum Ersetzen der reset_controls_to_default Methode"""
import re

# Datei einlesen
with open('pdvm_view_controller.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Neue Methode
new_method = '''    def reset_controls_to_default(self):
        """
        Controls auf Standard zurücksetzen - View komplett neu laden
        
        WORKFLOW:
        1. Altes UI-Widget schließen
        2. Reset-Flag setzen
        3. Komplett neu initialisieren (wie beim ersten Start)
        """
        logger.info("=== CONTROLS RESET TO DEFAULT ===")
        
        try:
            # SCHRITT 1: Altes UI-Widget schließen
            logger.info("  Schliesse altes UI-Widget...")
            if self.ui and hasattr(self.ui, 'close'):
                self.ui.close()
                self.ui = None
            
            # SCHRITT 2: Reset-Flag setzen
            logger.info("  Setze Reset-Flag...")
            self.reset = True
            
            # SCHRITT 3: View komplett neu initialisieren
            logger.info("  Initialisiere View komplett neu...")
            self.initialize()
            
            logger.info("Controls erfolgreich auf Standard zurückgesetzt - View neu geladen")
            
        except Exception as e:
            logger.error(f"Controls-Reset fehlgeschlagen: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise'''

# Pattern: Von "def reset_controls_to_default" bis zur nächsten "def"
pattern = r'    def reset_controls_to_default\(self\):.*?(?=\n    def [a-z_]+\()'

# Ersetzen
new_content = re.sub(pattern, new_method, content, flags=re.DOTALL)

# Zurückschreiben
with open('pdvm_view_controller.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Methode erfolgreich ersetzt!")
print("📝 reset_controls_to_default() schließt jetzt altes UI und initialisiert komplett neu")
