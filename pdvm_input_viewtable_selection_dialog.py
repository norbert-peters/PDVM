"""
PDVM Input Viewtable Selection Dialog - ULTRA-EINFACHE VERSION

Modal-Dialog zur Auswahl eines Datensatzes aus einer View-Tabelle.
Nutzt die AUTONOME VIEW - NUR view_guid benötigt!

ULTRA-EINFACH:
- Nur view_guid übergeben
- View holt sich ALLES SELBST aus viewdaten-Tabelle
- Keine call_daten, keine manuelle Konfiguration

AUTOR: Norbert Peters
DATUM: 26.10.2025 - ULTRA-EINFACHE VERSION
"""

import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QWidget)
from PyQt5.QtGui import QFont

from pdvm_autonome_view import create_autonome_view

logger = logging.getLogger(__name__)


class PdvmInputViewtableSelectionDialog(QDialog):
    """
    ULTRA-EINFACHER Dialog zur Auswahl aus View-Tabelle
    
    Nutzt autonome View:
    - Nur view_guid übergeben
    - View holt sich alles selbst
    - Alle Features (Schnellsuche, Filter, Sort) automatisch verfügbar
    
    Auswahl via:
    - Doppelklick auf Zeile
    - Zeile markieren + OK-Button
    """
    
    def __init__(self, viewtable_guid: str, current_guid: str = None, parent=None):
        """
        Args:
            viewtable_guid: GUID der View-Konfiguration (aus viewdaten-Tabelle)
            current_guid: Aktuell ausgewählte GUID (optional, für Vorauswahl)
            parent: Parent-Widget
        """
        super().__init__(parent)
        
        self.viewtable_guid = viewtable_guid
        self.current_guid = current_guid
        
        # Ausgewählte GUID (wird bei OK gesetzt)
        self.selected_guid = None
        
        # Autonome View (wird erstellt)
        self.view = None
        
        # Dialog-Konfiguration
        self.setWindowTitle(f"Auswahl aus View-Tabelle")
        self.setModal(True)
        self.setMinimumWidth(1000)
        self.setMinimumHeight(700)
        
        # UI erstellen
        self._create_ui()
        
        # View initialisieren
        self._initialize_view()
    
    def _create_ui(self):
        """Erstellt UI mit Header + View-Container + Buttons"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # === HEADER ===
        header_label = QLabel(f"📊 Auswahl aus View-Tabelle")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # === VIEW-CONTAINER (für autonome View) ===
        self.view_container = QWidget()
        view_layout = QVBoxLayout(self.view_container)
        view_layout.setContentsMargins(0, 0, 0, 0)
        view_layout.setSpacing(0)
        layout.addWidget(self.view_container)
        
        # === BUTTONS ===
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Abbrechen-Button
        cancel_button = QPushButton("Abbrechen")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        button_layout.addWidget(cancel_button)
        
        # OK-Button
        self.ok_button = QPushButton("✓ Auswählen")
        self.ok_button.clicked.connect(self._on_ok_clicked)
        self.ok_button.setEnabled(True)
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
    
    def _initialize_view(self):
        """
        Initialisiert AUTONOME VIEW - ULTRA-EINFACH!
        
        Nur view_guid übergeben → View holt sich alles selbst!
        """
        try:
            logger.info(f"🚀 === AUTONOME VIEW (ULTRA-EINFACH) ===")
            logger.info(f"📋 View-GUID: {self.viewtable_guid}")
            
            # Autonome View erstellen - ULTRA-EINFACH!
            self.view = create_autonome_view(
                view_guid=self.viewtable_guid,
                parent=self.view_container
            )
            
            # View in Container einfügen
            layout = self.view_container.layout()
            layout.addWidget(self.view)
            
            # Doppelklick-Signal verbinden
            self.view.row_double_clicked.connect(self._on_row_double_clicked)
            
            # Titel aktualisieren
            if self.view.view_table:
                self.setWindowTitle(f"Auswahl: {self.view.view_table}")
            
            logger.info(f"✅ Autonome View initialisiert!")
            logger.info(f"   - Tabelle: {self.view.view_table}")
            logger.info(f"   - Controls: {len(self.view.controls)}")
            logger.info(f"   - Alle Features verfügbar!")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei View-Initialisierung: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _on_row_double_clicked(self, guid: str):
        """Handler für Doppelklick - GUID direkt vom Signal"""
        logger.info(f"👆 Doppelklick: {guid}")  # Vollständige GUID loggen
        self.selected_guid = guid
        self.accept()
    
    def _on_ok_clicked(self):
        """Handler für OK-Button"""
        # GUID von View holen
        self.selected_guid = self.view.get_selected_guid()
        if self.selected_guid:
            logger.info(f"✅ Auswahl: {self.selected_guid}")  # Vollständige GUID loggen
            self.accept()
        else:
            logger.warning("⚠️ Keine Zeile ausgewählt")

