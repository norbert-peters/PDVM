# main.py
# PRODUKTIONS-VERSION: LINEARER STARTABLAUF mit optimierter Systemsteuerung
"""
OPTIMIERTER LINEARER STARTABLAUF:
1. Login-Fenster öffnen
2. Login validieren  
3. 2-Faktor Bestätigung (optional/vorbereitet)
4. Finale zentrale Systemsteuerung (GCS) initialisieren
5. Hauptanwendung mit vollständiger Menü-Funktionalität starten

Produktions-Version mit:
- Dualer Datenbank-Architektur
- Template-System (!guid! Referenzen)
- Stichtag-Persistierung
- Vollständiger Menu-Integration
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
        logging.FileHandler("main.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

from PyQt5.QtWidgets import QApplication, QMessageBox, QInputDialog
from PyQt5.QtCore import Qt

# Import der sicheren Login-Logik aus separater Datei
from pdvm_login import LoginDialog


class LinearStartManagerNew:
    """Verwaltet den linearen Startablauf mit neuer Systemsteuerung"""
    
    def __init__(self):
        self.app = None
        self.current_user_guid = None
        self.current_user_data = None
        self.main_window = None
    
    def start_linear_process(self):
        """
        Hauptmethode für den linearen Startablauf
        KEINE FALLBACKS - Jeder Schritt muss erfolgreich sein!
        """
        try:
            logger.info("🎯 === LINEARER STARTABLAUF MIT NEUER SYSTEMSTEUERUNG ===")
            
            # Schritt 1: QApplication initialisieren
            self._init_qt_application()
            
            # Schritt 2: Login durchführen
            login_result = self._perform_login()
            if not login_result:
                logger.error("❌ Login fehlgeschlagen - Startablauf abgebrochen")
                return False
            
            # Schritt 3: 2-Faktor (optional - aktuell übersprungen)
            two_factor_result = self._perform_two_factor()
            if not two_factor_result:
                logger.error("❌ 2-Faktor fehlgeschlagen - Startablauf abgebrochen")
                return False
            
            # Schritt 4: NEUE Globale Systemsteuerung initialisieren
            gcs_result = self._initialize_new_global_system()
            if not gcs_result:
                logger.error("❌ Neue Systemsteuerung-Initialisierung fehlgeschlagen - Startablauf abgebrochen")
                return False
            
            # Schritt 5: Hauptanwendung starten
            main_app_result = self._start_main_application()
            if not main_app_result:
                logger.error("❌ Hauptanwendung-Start fehlgeschlagen - Startablauf abgebrochen")
                return False
            
            logger.info("✅ Linearer Startablauf erfolgreich abgeschlossen")
            return True
            
        except Exception as e:
            logger.error(f"❌ KRITISCHER FEHLER im linearen Startablauf: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self._show_critical_error("Kritischer Fehler beim Systemstart", str(e))
            return False
    
    def _init_qt_application(self):
        """Schritt 1: QApplication initialisieren"""
        logger.info("🔧 Schritt 1: Qt-Anwendung initialisieren...")
        
        try:
            # Prüfe ob bereits eine QApplication existiert
            existing_app = QApplication.instance()
            if existing_app:
                self.app = existing_app
                logger.info("✅ Existierende QApplication gefunden und verwendet")
            else:
                self.app = QApplication(sys.argv)
                logger.info("✅ Neue QApplication erstellt")
            
            # Qt-Eigenschaften setzen
            self.app.setApplicationName("PDVM - Neue Systemsteuerung")
            self.app.setApplicationVersion("v2.0")
            
        except Exception as e:
            raise RuntimeError(f"Qt-Anwendung konnte nicht initialisiert werden: {e}")
    
    def _perform_login(self):
        """Schritt 2: Login durchführen"""
        logger.info("🔐 Schritt 2: Login durchführen...")
        
        try:
            # Öffne sicheren Login-Dialog
            login_dialog = LoginDialog()
            result = login_dialog.exec_()
            
            if result == login_dialog.Accepted:
                # Login erfolgreich - hole Benutzer-Daten
                self.current_user_data = login_dialog.get_login_data()
                
                if not self.current_user_data:
                    raise ValueError("Login erfolgreich, aber keine User-Daten erhalten!")
                
                # Extrahiere User-GUID aus den Login-Daten
                self.current_user_guid = self.current_user_data.get('user_guid')
                
                if not self.current_user_guid:
                    raise ValueError("Login erfolgreich, aber keine User-GUID in den Daten gefunden!")
                
                logger.info(f"✅ Login erfolgreich für User: {self.current_user_guid}")
                return True
            else:
                logger.info("ℹ️ Login vom Benutzer abgebrochen")
                return False
                
        except Exception as e:
            logger.error(f"❌ Login-Fehler: {e}")
            self._show_error("Login-Fehler", f"Anmeldung fehlgeschlagen:\n{e}")
            return False
    
    def _perform_two_factor(self):
        """Schritt 3: 2-Faktor Authentifizierung (optional)"""
        logger.info("🔒 Schritt 3: 2-Faktor Authentifizierung...")
        
        # Aktuell übersprungen - kann später implementiert werden
        logger.info("ℹ️ 2-Faktor aktuell übersprungen (nicht implementiert)")
        return True
    
    def _initialize_new_global_system(self):
        """Schritt 4: FINALE Globale Systemsteuerung initialisieren"""
        logger.info("🎯 Schritt 4: Finale Systemsteuerung initialisieren...")
        
        try:
            # Import der PRODUKTIONS-Systemsteuerung
            from pdvm_central_systemsteuerung import initialize_gcs, is_gcs_initialized, get_gcs
            
            if not self.current_user_guid:
               raise ValueError("Keine User-GUID für Systemsteuerung verfügbar!")
            
            if not self.current_user_data:
                raise ValueError("Keine User-Daten für Systemsteuerung verfügbar!")
            
            # LINEAR: Verwende nur user_guid und user_json aus dem Login
            user_guid = self.current_user_data.get('user_guid')
            user_json = self.current_user_data.get('user_json')
            
            # Initialisiere finale GCS LINEAR - nur GUID und JSON-Daten
            logger.info(f"🔧 Initialisiere finale GCS für User: {user_guid}")
            logger.info(f"📋 User-JSON verfügbar: {len(user_json) if user_json else 0} Zeichen")
            
            if not is_gcs_initialized():
                gcs_instance = initialize_gcs(user_guid, user_json)
                logger.info(f"✅ Finale GCS initialisiert - Stichtag: {gcs_instance.stichtag}")
            else:
                gcs_instance = get_gcs()
                logger.info("♻️ Verwende bereits initialisierte finale GCS")
            
            if not gcs_instance:
                raise RuntimeError("Finale GCS-Initialisierung fehlgeschlagen!")
            
            # Verifikation der Initialisierung
            logger.info(f"✅ Finale GCS erfolgreich initialisiert")
            logger.info(f"📅 Stichtag: {gcs_instance.stichtag}")
            if gcs_instance.st_inst:
                logger.info(f"📄 FormTimeStamp: {gcs_instance.st_inst.FormTimeStamp}")
            logger.info(f"🌍 Country: {gcs_instance.field_value('country')}")
            logger.info(f"⚙️ Mode: {gcs_instance.field_value('mode')}")
            logger.info(f"👤 User GUID: {gcs_instance.user_guid}")
            
            # Speichere GCS-Instanz für MainApp
            self.gcs_instance = gcs_instance
            
            # Aktualisiere globale GCS-Instanz für alle Module
            import global_gcs
            global_gcs.gcs = gcs_instance  # Direkte Zuweisung der globalen Variable
            logger.info("🌐 Globale GCS-Instanz für alle Module gesetzt")
            
            logger.info("✅ Finale Systemsteuerung erfolgreich initialisiert")
            logger.info(f"📋 GCS Status: Initialisiert={gcs_instance.is_initialized}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Finale GCS-Initialisierung fehlgeschlagen: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self._show_error("Systemsteuerung-Fehler", f"Finale Systemsteuerung konnte nicht initialisiert werden:\n{e}")
            return False
    
    def _start_main_application(self):
        """Schritt 5: Hauptanwendung starten"""
        logger.info("🏠 Schritt 5: Hauptanwendung starten...")
        
        try:
            # Teste finale GCS-Verfügbarkeit
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            logger.info(f"🧪 Test finale GCS: Country={gcs.field_value('country')}, Stichtag={gcs.stichtag}")
            logger.info(f"📄 Stichtag FormTimeStamp: {gcs.st_inst.FormTimeStamp}")
            
            # Erstelle und zeige VOLLSTÄNDIGE finale Hauptanwendung - OHNE Benutzerdaten!
            # Die MainApp bezieht ALLE Daten aus der finalen GCS
            from pdvm_systemstart import MainAppComplete
            try:
                self.main_window = MainAppComplete()
                # Kompatibilitäts-Brücke aktiviert - keine Fallback user_guid nötig
            except RuntimeError as e:
                if "LIZENZFEHLER" in str(e):
                    logger.error("❌ LIZENZFEHLER beim Hauptanwendung-Start - kritischer Berechtigungsfehler")
                    logger.error("❌ Anwendung wird aus Sicherheitsgründen beendet")
                    return False
                else:
                    raise  # Andere RuntimeErrors weiterleiten
            
            # Stelle sicher, dass das Fenster sichtbar und im Vordergrund ist
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
            
            logger.info("✅ Finale Hauptanwendung mit finaler GCS erfolgreich gestartet")
            
            # Starte Qt Event Loop
            exit_code = self.app.exec_()
            logger.info(f"ℹ️ Finale Anwendung beendet mit Exit-Code: {exit_code}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Finale Hauptanwendung-Start fehlgeschlagen: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self._show_error("Anwendungsstart-Fehler", f"Finale Hauptanwendung konnte nicht gestartet werden:\n{e}")
            return False
    
    def _show_error(self, title, message):
        """Zeigt eine Fehlermeldung an"""
        if self.app:
            QMessageBox.critical(None, title, message)
        else:
            print(f"ERROR {title}: {message}")
    
    def _show_critical_error(self, title, message):
        """Zeigt eine kritische Fehlermeldung an"""
        full_message = f"{message}\n\nDie Anwendung wird beendet."
        if self.app:
            QMessageBox.critical(None, title, full_message)
        else:
            print(f"CRITICAL ERROR {title}: {full_message}")


def main():
    """Hauptfunktion - Startet den linearen Ablauf mit neuer Systemsteuerung"""
    logger.info("🚀 === PDVM LINEARER START MIT NEUER SYSTEMSTEUERUNG ===")
    
    try:
        # Erstelle LinearStartManager
        start_manager = LinearStartManagerNew()
        
        # Starte linearen Prozess
        success = start_manager.start_linear_process()
        
        if success:
            logger.info("🎉 Anwendung erfolgreich gestartet und beendet")
            sys.exit(0)
        else:
            logger.error("❌ Anwendungsstart fehlgeschlagen")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ KRITISCHER FEHLER in main(): {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
