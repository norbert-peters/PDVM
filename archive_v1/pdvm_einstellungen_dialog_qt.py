#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EINSTELLUNGSMENÜ DIALOG - PyQt5 VERSION

Dialog für Systemeinstellungen mit:
1. Einstellungen Spalten
2. ExpertModus ein/aus (nur für Admins)
3. Filter ein/aus
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QCheckBox, QGroupBox, QMessageBox, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import logging
from global_gcs import gcs

logger = logging.getLogger(__name__)

class PdvmEinstellungsDialogQt(QDialog):
    """PyQt5 Dialog für Systemeinstellungen"""
    
    def __init__(self, parent=None):
        """
        Initialisierung des Einstellungs-Dialogs
        
        Args:
            parent: Parent-Fenster (optional)
        """
        super().__init__(parent)
    # gcs ist jetzt global verfügbar
        
        # Tracking-Variablen
        self.expert_mode_checkbox = None
        self.filter_mode_checkbox = None
        
        self._setup_dialog()
        self._create_gui()
        
        logger.info("🔧 PyQt5 Einstellungsmenü Dialog erstellt")
    
    def _setup_dialog(self):
        """Dialog-Eigenschaften konfigurieren"""
        self.setWindowTitle("Systemeinstellungen")
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        # Dialog zentrieren
        self._center_dialog()
    
    def _center_dialog(self):
        """Dialog auf dem Bildschirm zentrieren"""
        if self.parent():
            # Zentriere relativ zum Parent
            parent_geometry = self.parent().geometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            self.move(x, y)
        else:
            # Zentriere auf dem Bildschirm
            screen = self.screen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
    
    def _create_gui(self):
        """GUI-Elemente erstellen"""
        try:
            # Hauptlayout
            main_layout = QVBoxLayout(self)
            main_layout.setSpacing(15)
            main_layout.setContentsMargins(20, 20, 20, 20)
            
            # Titel
            title_label = QLabel("Systemeinstellungen")
            title_font = QFont("Arial", 14, QFont.Bold)
            title_label.setFont(title_font)
            title_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(title_label)
            
            # Anzeige-Einstellungen
            display_group = QGroupBox("Anzeigeeinstellungen")
            display_layout = QVBoxLayout(display_group)
            
            # Button: Einstellungen Spalten
            btn_spalten = QPushButton("Einstellungen Spalten")
            btn_spalten.clicked.connect(self._spalten_einstellungen)
            display_layout.addWidget(btn_spalten)
            
            main_layout.addWidget(display_group)
            
            # Admin-Einstellungen (nur für Admins)
            if gcs.is_admin:
                admin_group = QGroupBox("Administrator-Einstellungen")
                admin_layout = QVBoxLayout(admin_group)
                
                # ExpertModus Toggle
                self.expert_mode_checkbox = QCheckBox("ExpertModus aktiviert")
                self.expert_mode_checkbox.setChecked(gcs.expert_mode)
                self.expert_mode_checkbox.toggled.connect(self._toggle_expert_mode)
                admin_layout.addWidget(self.expert_mode_checkbox)
                
                main_layout.addWidget(admin_group)
            
            # Filter-Einstellungen
            filter_group = QGroupBox("Filter-Einstellungen")
            filter_layout = QVBoxLayout(filter_group)
            
            # Filter Toggle (Platzhalter)
            self.filter_mode_checkbox = QCheckBox("Filter aktiviert")
            self.filter_mode_checkbox.setChecked(False)
            self.filter_mode_checkbox.setEnabled(False)  # Deaktiviert
            self.filter_mode_checkbox.toggled.connect(self._toggle_filter_mode)
            filter_layout.addWidget(self.filter_mode_checkbox)
            
            # Info-Label für Filter
            filter_info = QLabel("(Wird in zukünftiger Version implementiert)")
            filter_info.setStyleSheet("color: gray; font-style: italic;")
            filter_layout.addWidget(filter_info)
            
            main_layout.addWidget(filter_group)
            
            # Spacer
            main_layout.addStretch()
            
            # Button-Layout
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            # Schließen Button
            btn_close = QPushButton("Schließen")
            btn_close.clicked.connect(self.accept)
            button_layout.addWidget(btn_close)
            
            main_layout.addLayout(button_layout)
            
            logger.info("✅ PyQt5 GUI-Elemente erstellt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der GUI: {e}")
            raise
    
    def _spalten_einstellungen(self):
        """Spalten-Einstellungen Dialog öffnen"""
        try:
            # Placeholder für zukünftige Spalten-Einstellungen
            QMessageBox.information(self, "Spalten-Einstellungen", 
                                  "Spalten-Einstellungen werden in zukünftiger Version implementiert.")
            logger.info("ℹ️ Spalten-Einstellungen aufgerufen")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Spalten-Einstellungen: {e}")
            QMessageBox.critical(self, "Fehler", f"Spalten-Einstellungen Fehler:\n{e}")
    
    def _toggle_expert_mode(self, checked):
        """ExpertModus ein/aus schalten"""
        try:
            # In GCS speichern
            gcs.expert_mode = checked
            
            # Feedback an Benutzer
            mode_text = "aktiviert" if checked else "deaktiviert"
            QMessageBox.information(self, "ExpertModus", f"ExpertModus wurde {mode_text}.")
            
            logger.info(f"✅ ExpertModus {mode_text}: {checked}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Umschalten des ExpertModus: {e}")
            QMessageBox.critical(self, "Fehler", f"ExpertModus konnte nicht umgeschaltet werden:\n{e}")
            # Zurücksetzen bei Fehler
            if self.expert_mode_checkbox:
                self.expert_mode_checkbox.setChecked(gcs.expert_mode)
    
    def _toggle_filter_mode(self, checked):
        """Filter-Modus ein/aus schalten (Platzhalter)"""
        try:
            mode_text = "aktiviert" if checked else "deaktiviert"
            
            # Placeholder - noch nicht implementiert
            QMessageBox.information(self, "Filter-Modus", 
                                  f"Filter-Modus {mode_text} (noch nicht implementiert).")
            
            logger.info(f"ℹ️ Filter-Modus {mode_text}: {checked} (Placeholder)")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Umschalten des Filter-Modus: {e}")
            QMessageBox.critical(self, "Fehler", f"Filter-Modus konnte nicht umgeschaltet werden:\n{e}")

def show_einstellungen_dialog_qt(parent=None):
    """
    Hilfsfunktion zum Anzeigen des PyQt5 Einstellungsmenü Dialogs
    
    Args:
        parent: Parent-Fenster (optional)
        
    Returns:
        Dialog-Instanz oder None bei Fehler
    """
    try:
        dialog = PdvmEinstellungsDialogQt(parent)
        result = dialog.exec_()
        
        logger.info(f"✅ Einstellungsmenü Dialog geschlossen mit Result: {result}")
        return dialog
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen des PyQt5 Einstellungsmenü Dialogs: {e}")
        if parent:
            QMessageBox.critical(parent, "Fehler", f"Einstellungsmenü konnte nicht geöffnet werden:\n{e}")
        return None

# Alias für einheitliche API
show_einstellungen_dialog = show_einstellungen_dialog_qt

# Test-Funktion
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    # Logging konfigurieren
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Test nur wenn GCS initialisiert ist
    try:
        from pdvm_central_systemsteuerung import is_gcs_initialized
        if not is_gcs_initialized():
            print("❌ GCS nicht initialisiert - kann Einstellungsmenü nicht testen")
            sys.exit(1)
        
        # QApplication erstellen
        app = QApplication(sys.argv)
        
        # Dialog anzeigen
        dialog = show_einstellungen_dialog_qt()
        if dialog:
            sys.exit(app.exec_())
        
    except Exception as e:
        print(f"❌ Test-Fehler: {e}")
        sys.exit(1)