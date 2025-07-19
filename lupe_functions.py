# Lupe-Funktionen für das UnifiedPdvmDialogWidget

import logging

# Logger konfigurieren
logger = logging.getLogger(__name__)

def set_view_lupe(self):
    """Maximiert den View-Bereich (100% View, 0% Input)"""
    try:
        self.previous_mode = self.display_mode
        self.display_mode = "view_lupe"
        self._set_display_mode("view_lupe")
        logger.info("🔍 View-Lupe aktiviert")
        self.show_status_message("🔍 View maximiert")
    except Exception as e:
        logger.error(f"❌ Fehler bei View-Lupe: {e}")

def set_input_lupe(self):
    """Maximiert den Input-Bereich (0% View, 100% Input)"""
    try:
        self.previous_mode = self.display_mode
        self.display_mode = "input_lupe"
        self._set_display_mode("input_lupe")
        logger.info("📝 Input-Lupe aktiviert")
        self.show_status_message("📝 Input maximiert")
    except Exception as e:
        logger.error(f"❌ Fehler bei Input-Lupe: {e}")

def set_normal_mode(self):
    """Setzt 50/50 Aufteilung zwischen View und Input"""
    try:
        self.previous_mode = self.display_mode
        self.display_mode = "normal"
        self._set_display_mode("normal")
        logger.info("⚖️ Normal-Modus aktiviert")
        self.show_status_message("⚖️ Normal-Modus 50/50")
    except Exception as e:
        logger.error(f"❌ Fehler bei Normal-Modus: {e}")

def toggle_display_mode(self):
    """Wechselt zwischen aktuellem und vorherigem Display-Modus"""
    try:
        if self.display_mode == self.previous_mode:
            # Fallback zum Normal-Modus wenn gleich
            self.set_normal_mode()
        else:
            # Wechsel zum vorherigen Modus
            if self.previous_mode == "view_lupe":
                self.set_view_lupe()
            elif self.previous_mode == "input_lupe":
                self.set_input_lupe()
            else:
                self.set_normal_mode()
        logger.info(f"🔄 Display-Modus gewechselt: {self.display_mode}")
    except Exception as e:
        logger.error(f"❌ Fehler beim Display-Modus-Wechsel: {e}")

def _set_display_mode(self, mode):
    """Interne Funktion zum Setzen der Splitter-Größen"""
    try:
        if not hasattr(self, 'main_splitter'):
            logger.warning("⚠️ Splitter noch nicht initialisiert")
            return
            
        # Splitter-Größen aus den definierten Positionen
        sizes = self.splitter_positions.get(mode, [50, 50])
        
        # Total-Size ermitteln
        total_height = self.main_splitter.height()
        if total_height <= 0:
            total_height = 600  # Fallback
            
        # Prozentuale Größen in echte Pixel umrechnen
        actual_sizes = [int(total_height * size / 100) for size in sizes]
        
        # Splitter-Größen setzen
        self.main_splitter.setSizes(actual_sizes)
        
        # UI-Einstellungen speichern
        self.save_ui_settings()
        
        logger.info(f"✅ Display-Modus '{mode}' gesetzt: {actual_sizes}")
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Setzen des Display-Modus '{mode}': {e}")

def _setup_keyboard_shortcuts(self):
    """Setzt Tastatur-Shortcuts für Lupe-Modi"""
    try:
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        
        # F1 = View-Lupe
        QShortcut(QKeySequence("F1"), self, self.set_view_lupe)
        
        # F2 = Input-Lupe  
        QShortcut(QKeySequence("F2"), self, self.set_input_lupe)
        
        # F3 = Normal-Modus
        QShortcut(QKeySequence("F3"), self, self.set_normal_mode)
        
        # F11 = Toggle
        QShortcut(QKeySequence("F11"), self, self.toggle_display_mode)
        
        logger.info("✅ Keyboard-Shortcuts für Lupe-Modi aktiviert")
        
    except Exception as e:
        logger.warning(f"⚠️ Fehler bei Keyboard-Shortcuts: {e}")
