#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDVM-Systemstart mit finaler GCS-Integration

Angepasste Version für die finale Systemsteuerung-Architektur
"""

import sys, io, os, logging

# Erzwinge UTF-8 für alle IO
os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Logger-Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("pdvm_app_final.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)
logger.info("🔹 Finale Hauptanwendung gestartet")

import json
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QApplication,
    QDateTimeEdit, QPushButton
)
from PyQt5.QtCore import Qt, QDateTime, QDate, QTime
from PyQt5.QtGui import QFont

# FINALE SYSTEMSTEUERUNG Import
from pdvm_central_systemsteuerung_final import get_gcs, is_gcs_initialized

class MainAppFinal(QMainWindow):
    """Finale Hauptanwendung mit robuster GCS-Architektur"""
    
    def __init__(self, user_daten=None):
        """
        Initialisierung der finalen Hauptanwendung
        
        Args:
            user_daten: [email, None, user_data, user_guid] - Kompatibilitäts-Format
        """
        super().__init__()
        
        self.user_daten = user_daten
        self.user_guid = user_daten[3] if user_daten and len(user_daten) > 3 else None
        self.user_email = user_daten[0] if user_daten and len(user_daten) > 0 else "unknown@example.com"
        
        logger.info(f"🏗️ Finale MainApp initialisiert für User: {self.user_guid}")
        
        # Prüfe finale GCS-Verfügbarkeit
        if not is_gcs_initialized():
            logger.error("❌ Finale GCS nicht initialisiert!")
            raise RuntimeError("Finale GCS muss vor MainApp initialisiert werden!")
        
        self.gcs = get_gcs()
        logger.info("✅ Finale GCS erfolgreich geladen")
        
        # Setup UI
        self._setup_ui()
        
        # Erstelle Stichtag-Bar
        self._create_stichtag_bar()
        
        logger.info("✅ Finale MainApp vollständig initialisiert")
    
    def _setup_ui(self):
        """Setup der Benutzeroberfläche"""
        self.setWindowTitle("PDVM - Finale Version")
        self.setGeometry(100, 100, 1200, 800)
        
        # Zentrales Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Hauptlayout
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Titel
        title_label = QLabel("PDVM - Finale Systemsteuerung")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        self.main_layout.addWidget(title_label)
        
        # Status-Bereich
        self._create_status_section()
        
        # Content-Bereich für weitere Komponenten
        self.content_layout = QVBoxLayout()
        self.main_layout.addLayout(self.content_layout)
        
        logger.info("✅ UI-Setup abgeschlossen")
    
    def _create_status_section(self):
        """Erstelle Status-Bereich"""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.StyledPanel)
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #e8f4f8;
                border: 1px solid #b0d4e3;
                border-radius: 5px;
                padding: 10px;
                margin-bottom: 10px;
            }
        """)
        
        status_layout = QVBoxLayout(status_frame)
        
        # GCS-Status
        gcs_status = QLabel(f"🌐 GCS Status: ✅ Initialisiert (User: {self.gcs.user_guid})")
        status_layout.addWidget(gcs_status)
        
        # User-Info
        username = self.gcs.field_value('username') or 'Unbekannt'
        user_info = QLabel(f"👤 Benutzer: {username} ({self.user_email})")
        status_layout.addWidget(user_info)
        
        # Systemeinstellungen
        country = self.gcs.field_value('country') or 'Unbekannt'
        mode = self.gcs.field_value('mode') or 'Unbekannt'
        settings_info = QLabel(f"⚙️ Land: {country}, Modus: {mode}")
        status_layout.addWidget(settings_info)
        
        self.main_layout.addWidget(status_frame)
    
    def _create_stichtag_bar(self):
        """Erstelle Stichtag-Bar mit finaler GCS-Integration"""
        logger.info("🔧 Erstelle finale Stichtag-Bar...")
        
        try:
            from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QFrame
            from PyQt5.QtGui import QFont
            
            # Stichtag-Container
            stichtag_frame = QFrame()
            stichtag_frame.setFrameStyle(QFrame.StyledPanel)
            stichtag_frame.setStyleSheet("""
                QFrame {
                    background-color: #f0f0f0;
                    border: 1px solid #c0c0c0;
                    border-radius: 5px;
                    padding: 5px;
                    margin-bottom: 10px;
                }
            """)
            
            layout = QHBoxLayout(stichtag_frame)
            layout.setContentsMargins(10, 5, 10, 5)
            
            # "Stichtag:" Label
            stichtag_label = QLabel("Stichtag:")
            font = QFont()
            font.setBold(True)
            stichtag_label.setFont(font)
            layout.addWidget(stichtag_label)
            
            # Stichtag-Anzeige
            st_inst = self.gcs.st_inst
            if st_inst:
                stichtag_display = QLabel(st_inst.FormTimeStamp)
                stichtag_display.setStyleSheet("font-weight: bold; color: #2c5aa0;")
                layout.addWidget(stichtag_display)
                self.stichtag_display = stichtag_display
                
                logger.info(f"✅ Stichtag-Anzeige: {st_inst.FormTimeStamp}")
            else:
                error_label = QLabel("❌ Stichtag nicht verfügbar")
                error_label.setStyleSheet("color: red;")
                layout.addWidget(error_label)
            
            # Aktualisieren-Button
            refresh_btn = QPushButton("🔄 Aktualisieren")
            refresh_btn.clicked.connect(self._refresh_stichtag)
            layout.addWidget(refresh_btn)
            
            # Demo: Stichtag ändern
            change_btn = QPushButton("📅 Demo: Stichtag ändern")
            change_btn.clicked.connect(self._demo_change_stichtag)
            layout.addWidget(change_btn)
            
            # Stretcher
            layout.addStretch()
            
            # Am Anfang des Content-Bereichs einfügen
            self.content_layout.insertWidget(0, stichtag_frame)
            
            logger.info("✅ Finale Stichtag-Bar erstellt")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Stichtag-Bar Erstellung: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _refresh_stichtag(self):
        """Aktualisiere Stichtag-Anzeige"""
        try:
            st_inst = self.gcs.st_inst
            if st_inst and hasattr(self, 'stichtag_display'):
                self.stichtag_display.setText(st_inst.FormTimeStamp)
                logger.info(f"🔄 Stichtag aktualisiert: {st_inst.FormTimeStamp}")
        except Exception as e:
            logger.error(f"❌ Fehler bei Stichtag-Aktualisierung: {e}")
    
    def _demo_change_stichtag(self):
        """Demo: Ändere Stichtag über finale GCS"""
        try:
            from PyQt5.QtWidgets import QInputDialog
            
            # Eingabe-Dialog für neuen Stichtag
            current_value = self.gcs.stichtag
            new_value, ok = QInputDialog.getDouble(
                self, 
                "Stichtag ändern", 
                f"Neuer Stichtag (PDVM-Format):\\n\\nAktuell: {current_value}",
                current_value,
                0,
                999999999,
                1
            )
            
            if ok:
                # Verwende finale GCS parametrisierte Property
                self.gcs.field_value('stichtag', new_value)
                
                # Aktualisiere Anzeige
                self._refresh_stichtag()
                
                logger.info(f"✅ Stichtag über finale GCS geändert: {new_value}")
                logger.info(f"📄 Neuer FormTimeStamp: {self.gcs.st_inst.FormTimeStamp}")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Stichtag-Änderung: {e}")

# Hauptklasse für Kompatibilität
MainApp = MainAppFinal

def main():
    """Test-Funktion"""
    app = QApplication(sys.argv)
    
    # Test-Daten
    user_daten = ["test@example.com", None, {"email": "test@example.com"}, "test-guid"]
    
    try:
        main_window = MainAppFinal(user_daten)
        main_window.show()
        sys.exit(app.exec_())
    except Exception as e:
        logger.error(f"❌ Fehler beim Start: {e}")
        print(f"FEHLER: {e}")

if __name__ == "__main__":
    main()
