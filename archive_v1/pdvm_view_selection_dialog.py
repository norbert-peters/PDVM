"""
PDVM View Selection Dialog

Öffnet View zur Auswahl einer GUID aus einer Liste.

VERWENDUNG:
- Modal Dialog
- Zeigt View mit allen Features (Filter, Sort, etc.)
- Doppelklick auf Zeile wählt GUID aus
- Rückgabe: Gewählte GUID oder None bei Abbruch

ARCHITEKTUR:
- Verwendet PdvmViewController für View-Anzeige
- View-Einstellungen werden unter view_guid in GCS persistent gespeichert
- Kein Caching der BasisMatrix (wird jedes Mal neu geladen)

AUTOR: Norbert Peters
DATUM: 27.10.2025
"""

import logging
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt

from global_gcs import gcs

logger = logging.getLogger(__name__)


class PdvmViewSelectionDialog(QDialog):
    """
    Modal Dialog zur Auswahl einer GUID aus einer View.
    
    Features:
    - Vollständige View mit Filter/Sort/etc.
    - Doppelklick wählt Zeile aus
    - View-Einstellungen persistent unter view_guid
    """
    
    def __init__(self, view_guid, parent=None, selected_guid=None):
        """
        Args:
            view_guid (str): GUID der anzuzeigenden View
            parent (QWidget): Parent-Widget
            selected_guid (str): Aktuell ausgewählte GUID (optional, wird markiert)
        """
        super().__init__(parent)
        
        self.view_guid = view_guid
        self.selected_guid = selected_guid
        self.chosen_guid = None  # Gewählte GUID (return value)
        
        self.setWindowTitle("Auswahl")
        self.setModal(True)
        self.resize(1000, 600)
        
        self._init_ui()
        
        logger.info(f"📋 ViewSelectionDialog geöffnet: {view_guid}")
    
    def _init_ui(self):
        """UI aufbauen"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = QLabel("Bitte wählen Sie einen Eintrag aus:")
        header.setStyleSheet("font-size: 11pt; font-weight: bold; padding: 5px;")
        layout.addWidget(header)
        
        # View-Container
        from pdvm_view_controller import PdvmViewController
        
        try:
            # View-Controller erstellen
            self.view_controller = PdvmViewController(
                view_guid=self.view_guid,
                parent=self,
                test_mode=False,
                first_call=True
            )
            
            # View-Widget holen
            view_widget = self.view_controller.ui.get_widget()
            layout.addWidget(view_widget)
            
            # Doppelklick-Signal verbinden
            self.view_controller.ui.row_double_clicked.connect(self._on_row_double_clicked)
            
            logger.info("  ✅ View geladen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der View: {e}")
            error_label = QLabel(f"Fehler beim Laden der View:\n{e}")
            error_label.setStyleSheet("color: red; padding: 20px;")
            layout.addWidget(error_label)
        
        # Button-Leiste
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Abbrechen-Button
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _on_row_double_clicked(self, row_data):
        """
        Handler für Doppelklick auf Zeile.
        
        Args:
            row_data (dict): Zeilen-Daten mit uid_original
        """
        try:
            # GUID aus row_data extrahieren
            guid = row_data.get('uid_original')
            
            if guid:
                logger.info(f"  ✅ GUID gewählt: {guid[:8]}...")
                self.chosen_guid = guid
                self.accept()  # Dialog schließen mit OK
            else:
                logger.warning("  ⚠️ Keine GUID in row_data gefunden")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Verarbeiten der Zeilen-Auswahl: {e}")
    
    def get_selected_guid(self):
        """
        Gibt gewählte GUID zurück.
        
        Returns:
            str|None: Gewählte GUID oder None wenn abgebrochen
        """
        return self.chosen_guid
