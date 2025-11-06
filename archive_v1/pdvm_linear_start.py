# pdvm_linear_start.py
# LINEARER STARTABLAUF - Kein kompliziertes System mehr!
"""
LINEARER STARTABLAUF:
1. Login-Fenster öffnen
2. Login validieren  
3. 2-Faktor Bestätigung (optional/vorbereitet)
4. Globale Systemsteuerung initialisieren
5. Hauptanwendung mit Menü starten

KEINE FALLBACKS - Klare Fehlermeldungen bei jedem Schritt!
"""

import sys
import os
import logging
import traceback

# UTF-8 Setup
os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("pdvm_linear_start.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

from PyQt5.QtWidgets import QApplication, QMessageBox, QInputDialog
from PyQt5.QtCore import Qt

# Import der sicheren Login-Logik aus separater Datei
from pdvm_login import LoginDialog


class LinearStartManager:
    """Verwaltet den linearen Startablauf"""
    
    def __init__(self):
        self.app = None
        self.current_user_guid = None
        self.current_user_data = None
        self.main_window = None
        
    def start(self):
        """Startet den kompletten linearen Ablauf"""
        try:
            logger.info("🚀 LINEARER STARTABLAUF GESTARTET")
            
            # QApplication erstellen
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("PDVM System")
            
            # Schritt 1: Login-Fenster
            user_data = self.show_login_dialog()
            if not user_data:
                logger.info("❌ Login abgebrochen")
                return False
                
            # Schritt 2: Login validieren
            if not self.validate_login(user_data):
                logger.error("❌ Login-Validierung fehlgeschlagen")
                return False
                
            # Schritt 3: 2-Faktor Bestätigung (optional)
            if not self.two_factor_confirmation():
                logger.error("❌ 2-Faktor Bestätigung fehlgeschlagen")
                return False
                
            # Schritt 4: Globale Systemsteuerung initialisieren
            if not self.initialize_global_system(user_data['user_guid']):
                logger.error("❌ Systemsteuerung-Initialisierung fehlgeschlagen")
                return False
                
            # Schritt 5: Hauptanwendung starten
            if not self.start_main_application():
                logger.error("❌ Hauptanwendung konnte nicht gestartet werden")
                return False
                
            logger.info("✅ LINEARER STARTABLAUF ERFOLGREICH ABGESCHLOSSEN")
            
            # Event-Loop starten
            return self.app.exec_()
            
        except Exception as e:
            logger.error(f"❌ KRITISCHER FEHLER im Startablauf: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            if self.app:
                QMessageBox.critical(None, "Kritischer Fehler", 
                                   f"Startablauf fehlgeschlagen:\n{e}")
            return False
    
    def show_login_dialog(self):
        """Schritt 1: SICHERER Login-Dialog mit getrennter Logik"""
        logger.info("🔐 Schritt 1: Sichere Login-Dialog öffnen")
        
        try:
            # Sichere Login-Klasse aus pdvm_login.py importieren
            from pdvm_login import LoginDialog
            
            # Sicheren Login-Dialog erstellen
            login_dialog = LoginDialog()
            login_dialog.show()
            login_dialog.raise_()
            login_dialog.activateWindow()
            
            # Modal ausführen - blockiert bis Login abgeschlossen
            result = login_dialog.exec_()
            
            if result == LoginDialog.Accepted:
                # SICHERE Login-Daten aus getrennter Logik erhalten
                user_data = login_dialog.get_login_data()
                if user_data:
                    logger.info(f"📝 Sichere Login-Daten erhalten für User: {user_data['username']}")
                    return user_data
                else:
                    logger.error("❌ Keine Login-Daten erhalten trotz Accepted")
                    return None
            else:
                logger.info("❌ Login abgebrochen")
                return None
                
        except Exception as e:
            logger.error(f"❌ Fehler bei sicherem Login-Dialog: {e}")
            QMessageBox.critical(None, "Login-Fehler", f"Sichere Login-Dialog Fehler:\n{e}")
            return None
    
    def validate_login(self, user_data):
        """Schritt 2: Login bereits validiert - Überprüfe nur Daten-Vollständigkeit"""
        logger.info("🔍 Schritt 2: Login-Daten validieren")
        
        try:
            # Login wurde bereits in pdvm_login.py validiert
            # Hier nur prüfen ob alle nötigen Daten vorhanden sind
            
            if not user_data:
                logger.error("❌ Keine Login-Daten erhalten")
                QMessageBox.critical(None, "Login-Daten fehlen", "Keine Login-Daten erhalten!")
                return False
                
            required_fields = ['username', 'user_guid', 'email', 'user_json']
            missing_fields = []
            
            for field in required_fields:
                if field not in user_data or not user_data[field]:
                    missing_fields.append(field)
            
            if missing_fields:
                logger.error(f"❌ Fehlende Login-Daten: {missing_fields}")
                QMessageBox.critical(None, "Login-Daten unvollständig", 
                                   f"Fehlende Daten: {', '.join(missing_fields)}")
                return False
            
            # Vollständige Benutzerdaten speichern
            self.current_user_guid = user_data['user_guid']
            self.current_user_data = user_data
            logger.info(f"✅ Login-Daten vollständig für User: {user_data['username']} (GUID: {self.current_user_guid})")
            return True
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Login-Daten-Validierung: {e}")
            QMessageBox.critical(None, "Validierungs-Fehler", 
                               f"Login-Daten-Validierung fehlgeschlagen:\n{e}")
            return False
    
    def two_factor_confirmation(self):
        """Schritt 3: 2-Faktor Bestätigung (vorbereitet für Zukunft)"""
        logger.info("🔐 Schritt 3: 2-Faktor Bestätigung")
        
        try:
            # Für jetzt: Einfache Bestätigung
            # TODO: Hier kann später echter 2-Faktor Code eingebaut werden
            
            reply = QMessageBox.question(None, "Bestätigung", 
                                       "Login bestätigen?\n\n(Hier kann später 2-Faktor eingebaut werden)",
                                       QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                logger.info("✅ 2-Faktor Bestätigung erfolgreich")
                return True
            else:
                logger.info("❌ 2-Faktor Bestätigung abgebrochen")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler bei 2-Faktor Bestätigung: {e}")
            QMessageBox.critical(None, "2-Faktor Fehler", 
                               f"2-Faktor Bestätigung fehlgeschlagen:\n{e}")
            return False
    
    def initialize_global_system(self, user_guid):
        """Schritt 4: Globale Systemsteuerung initialisieren"""
        logger.info("🔧 Schritt 4: Globale Systemsteuerung initialisieren")
        
        try:
            from pdvm_central_systemsteuerung_global import initialize_gcs
            
            # Globale Systemsteuerung für den User initialisieren
            initialize_gcs(user_guid)
            
            logger.info(f"✅ Globale Systemsteuerung initialisiert für User: {user_guid}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Systemsteuerung-Initialisierung: {e}")
            QMessageBox.critical(None, "Systemsteuerung-Fehler", 
                               f"Systemsteuerung konnte nicht initialisiert werden:\n{e}")
            return False
    
    def start_main_application(self):
        """Schritt 5: Hauptanwendung mit Menü starten"""
        logger.info("🎯 Schritt 5: Hauptanwendung starten")
        
        try:
            # Importiere die globale Systemsteuerung um sicherzustellen dass sie funktioniert
            from pdvm_central_systemsteuerung_global import gcs
            
            # Test: Zugriff auf gcs sollte jetzt funktionieren
            test_stichtag = gcs.stichtag
            logger.info(f"📅 GCS Test erfolgreich - Stichtag: {test_stichtag}")
            
            # Hauptanwendung importieren und starten
            from pdvm_systemstart import MainApp
            
            # Benutzerdaten in erwartetem Array-Format für MainApp erstellen
            # MainApp erwartet: [email, password, user_json, user_guid]
            user_array = [
                self.current_user_data['email'],        # [0] = Email
                self.current_user_data['password'],     # [1] = Passwort
                self.current_user_data['user_json'],    # [2] = User-JSON-Daten
                self.current_user_data['user_guid']     # [3] = User-GUID
            ]
            
            logger.info(f"📋 Erstelle MainApp mit Benutzerdaten für: {self.current_user_data['email']}")
            self.main_window = MainApp(user_array)
            self.main_window.show()
            
            logger.info("✅ Hauptanwendung gestartet")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten der Hauptanwendung: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            QMessageBox.critical(None, "Anwendungs-Fehler", 
                               f"Hauptanwendung konnte nicht gestartet werden:\n{e}")
            return False


def main():
    """Hauptfunktion - Startet den linearen Ablauf"""
    manager = LinearStartManager()
    exit_code = manager.start()
    sys.exit(exit_code if exit_code else 0)


if __name__ == "__main__":
    main()
