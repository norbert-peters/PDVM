# pdvm_systemstart_new.py
# HAUPTANWENDUNG mit neuer Systemsteuerung
"""
MainApp mit neuer vereinfachter Systemsteuerung.
Stichtagbar funktioniert direkt mit der globalen Instanz.
"""

import logging
import sys
import traceback
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QApplication, QFrame, QMessageBox)
from PyQt5.QtCore import Qt

# Setup Logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MainAppNew(QMainWindow):
    """
    Hauptanwendung mit neuer Systemsteuerung-Integration
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize references
        self._gcs_instance = None
        self.stichtag_bar = None
        self.stichtag_picker = None
        self.refresh_button = None
        self.stichtag_display = None
        
        # Content area
        self.content_layout = None
        self.current_display_widget = None
        self.current_view_widget = None
        
        logger.info("🏠 MainAppNew initialisiert")
        
        # UI Setup
        self.setup_ui()
        
        # Teste neue GCS nach UI-Setup
        self.test_new_gcs_integration()
        
        # Startmenü laden
        self.open_start_menu()
    
    def setup_ui(self):
        """Setup der Benutzeroberfläche"""
        try:
            logger.info("🎨 Setup UI für MainAppNew...")
            
            # Window properties
            self.setWindowTitle("PDVM - Neue Systemsteuerung")
            self.setGeometry(100, 100, 1200, 800)
            
            # Central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Main layout
            main_layout = QVBoxLayout(central_widget)
            
            # Stichtagbar erstellen (oben)
            self.stichtag_bar = self._create_stichtag_bar()
            if self.stichtag_bar:
                main_layout.addWidget(self.stichtag_bar)
            
            # Layout wie originale MainApp: Links Menü, rechts Content
            content_container = QWidget()
            content_main_layout = QHBoxLayout(content_container)
            main_layout.addWidget(content_container)
            
            # Linke Sidebar für vertikales Menü
            self.menu_frame = QFrame()
            self.menu_frame.setFrameShape(QFrame.StyledPanel)
            self.menu_frame.setLayout(QVBoxLayout())
            content_main_layout.addWidget(self.menu_frame, 1)

            # Rechter Bereich als Container für Inhalte
            content_frame = QFrame()
            content_frame.setFrameStyle(QFrame.Box)
            self.content_layout = QVBoxLayout(content_frame)
            content_main_layout.addWidget(content_frame, 4)
            
            # Status label
            status_label = QLabel("✅ Hauptanwendung mit neuer Systemsteuerung gestartet")
            status_label.setStyleSheet("color: green; font-weight: bold; padding: 10px;")
            self.content_layout.addWidget(status_label)
            
            logger.info("✅ UI Setup abgeschlossen")
            
        except Exception as e:
            logger.error(f"❌ UI Setup fehlgeschlagen: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _get_new_gcs_safely(self):
        """
        Holt die neue globale Systemsteuerung sicher.
        Verwendet direkt das neue gcs-Proxy-Objekt für Zugriff.
        """
        try:
            # Import der NEUEN Systemsteuerung
            from pdvm_central_systemsteuerung_global_new import gcs, is_initialized
            
            if is_initialized():
                # Direkter Zugriff über neues globales gcs-Proxy
                return gcs
            else:
                logger.error("❌ Neue globale Systemsteuerung ist nicht initialisiert!")
                return None
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Zugriff auf neue GCS: {e}")
            return None
    
    def _create_stichtag_bar(self):
        """
        Erstellt die Stichtagbar mit neuer Systemsteuerung.
        
        Layout: 'Stichtag:' (PdvmDateTimePicker) --> verwendeter Stichtag: (PdvmTimeStamp) [Refresh]
        """
        try:
            logger.info("🔧 _create_stichtag_bar gestartet...")
            
            # Hole neue GCS
            gcs_instance = self._get_new_gcs_safely()
            if not gcs_instance:
                logger.error("❌ Keine neue GCS verfügbar für Stichtagbar")
                return QLabel("❌ Keine Systemsteuerung verfügbar")
            
            from pdvm_date_time_picker import PdvmDateTimePicker
            
            # Container für Stichtagbar - SCHMAL machen
            stichtag_frame = QFrame()
            stichtag_frame.setFrameStyle(QFrame.Box)
            stichtag_frame.setMaximumHeight(50)  # Maximale Höhe begrenzen
            stichtag_frame.setStyleSheet("""
                QFrame {
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    margin: 2px;
                    padding: 3px;
                    max-height: 50px;
                }
            """)
            
            layout = QHBoxLayout(stichtag_frame)
            layout.setContentsMargins(5, 2, 5, 2)  # Kleinere Margins
            layout.setSpacing(5)  # Weniger Abstand zwischen Elementen
            
            # Label - kompakter
            label = QLabel("Stichtag:")
            label.setStyleSheet("font-weight: bold; font-size: 11px; padding: 2px;")
            label.setMaximumHeight(30)
            layout.addWidget(label)
            
            # DatetimePicker mit globaler Stichtag-Instanz
            try:
                logger.info(f"🔧 Erstelle PdvmDateTimePicker mit neuer GCS...")
                logger.info(f"📅 Globale Stichtag-Instanz: {gcs_instance.global_stichtag_inst}")
                logger.info(f"📅 Aktueller Stichtag: {gcs_instance.stichtag}")
                
                # PdvmDateTimePicker arbeitet direkt auf der neuen globalen Instanz
                self.stichtag_picker = PdvmDateTimePicker(
                    parent=self,
                    pdvm_datetime=gcs_instance.global_stichtag_inst,  # Neue globale Instanz!
                    display="all",
                    display_time_short=False
                )
                
                if hasattr(self.stichtag_picker, '_date_edit'):
                    calendar = self.stichtag_picker._date_edit.calendarWidget()
                    if calendar:
                        calendar.setMinimumSize(350, 220)
                
                layout.addWidget(self.stichtag_picker)
                logger.info(f"✅ PdvmDateTimePicker (Neue GCS) Datum: {gcs_instance.global_stichtag_inst.PdvmDateTime}")
                
            except Exception as e:
                logger.error(f"❌ Fehler beim Erstellen des PdvmDateTimePicker mit neuer GCS: {e}")
                return QLabel(f"❌ Fehler beim Erstellen des DateTimePicker: {e}")
            
            # Pfeil "→" - kompakter
            arrow_label = QLabel(" → ")
            arrow_label.setStyleSheet("font-size: 12px; font-weight: bold; padding: 2px;")
            arrow_label.setMaximumHeight(30)
            layout.addWidget(arrow_label)
            
            # Anzeige aktueller Stichtag - kompakter
            self.stichtag_display = QLabel()
            self.stichtag_display.setMaximumHeight(30)
            self.stichtag_display.setStyleSheet("""
                background-color: white;
                border: 1px solid #999;
                padding: 3px 6px;
                border-radius: 2px;
                font-family: monospace;
                font-size: 11px;
                max-height: 30px;
            """)
            layout.addWidget(self.stichtag_display)
            
            # Refresh Button - kompakter
            self.refresh_button = QPushButton("Refresh")
            self.refresh_button.setMaximumHeight(30)
            self.refresh_button.setMaximumWidth(80)
            self.refresh_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 10px;
                    max-height: 30px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)
            self.refresh_button.clicked.connect(self._on_stichtag_refresh)
            layout.addWidget(self.refresh_button)
            logger.info("✅ Refresh-Button erstellt")
            
            # Initiale Anzeige aktualisieren
            self._update_stichtag_display()
            
            logger.info("✅ Stichtagbar erfolgreich erstellt")
            return stichtag_frame
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der Stichtagbar: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return QLabel(f"❌ Stichtagbar-Fehler: {e}")
    
    def _update_stichtag_display(self):
        """Aktualisiert die Stichtag-Anzeige"""
        try:
            gcs_instance = self._get_new_gcs_safely()
            if gcs_instance and self.stichtag_display:
                stichtag_inst = gcs_instance.global_stichtag_inst
                if stichtag_inst:
                    display_text = f"Verwendet: {stichtag_inst.FormTimeStamp}"
                    self.stichtag_display.setText(display_text)
                    logger.info(f"📅 Stichtag-Anzeige aktualisiert: {display_text}")
                    
        except Exception as e:
            logger.error(f"❌ Fehler bei Stichtag-Anzeige-Update: {e}")
            if self.stichtag_display:
                self.stichtag_display.setText("❌ Anzeige-Fehler")
    
    def _on_stichtag_refresh(self):
        """
        Behandelt den Refresh-Button Click mit neuer Systemsteuerung:
        1. save() auf Picker → Änderungen landen direkt in neuer globaler Instanz  
        2. Neue GCS speichern
        3. Anzeige aktualisieren
        """
        try:
            logger.info("🎯 Stichtag-Refresh: Neue Systemsteuerung gestartet")
            gcs_instance = self._get_new_gcs_safely()
            
            if gcs_instance:
                # 1. Picker speichert direkt in die neue globale Instanz
                if hasattr(self.stichtag_picker, 'save'):
                    self.stichtag_picker.save()
                    logger.info("✅ Picker.save() ausgeführt → Wert in neue globale Instanz geschrieben")
                
                # 2. Persistiere über neue globale Systemsteuerung  
                gcs_instance.save_stichtag()
                logger.info("✅ Stichtag in DB gespeichert (neue GCS save_stichtag)")
                
                # 3. Anzeige aktualisieren
                self._update_stichtag_display()
                
                logger.info("✅ Stichtag-Refresh mit neuer GCS erfolgreich")
            else:
                logger.warning("⚠️ Keine neue GCS für Refresh verfügbar")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Stichtag-Refresh mit neuer GCS: {e}")
            self._update_stichtag_display()
    
    def test_new_gcs_integration(self):
        """Testet die Integration mit der neuen Systemsteuerung"""
        try:
            logger.info("🧪 Teste neue GCS-Integration...")
            
            gcs_instance = self._get_new_gcs_safely()
            if gcs_instance:
                logger.info(f"✅ Neue GCS verfügbar")
                logger.info(f"🌍 Country: {gcs_instance.country}")
                logger.info(f"📅 Stichtag: {gcs_instance.stichtag}")
                logger.info(f"🔧 Expert Mode: {gcs_instance.expert_mode}")
                logger.info(f"⚙️ Mode: {gcs_instance.mode}")
                logger.info(f"🌐 Language: {gcs_instance.language}")
                
                # Teste globale Stichtag-Instanz
                stichtag_inst = gcs_instance.global_stichtag_inst
                if stichtag_inst:
                    logger.info(f"📅 Globale Stichtag-Instanz: {stichtag_inst.FormTimeStamp}")
                
                logger.info("✅ Neue GCS-Integration erfolgreich getestet")
            else:
                logger.error("❌ Neue GCS nicht verfügbar!")
                
        except Exception as e:
            logger.error(f"❌ Neue GCS-Integration Test fehlgeschlagen: {e}")

    def open_start_menu(self):
        """Lädt das Startmenü mit neuer Systemsteuerung."""
        try:
            logger.info("🏠 Lade Startmenü...")
            
            # 🔒 LAZY IMPORT: Handler erst nach Login laden
            from pdvm_command_handler import PdvmCommandHandler
            from pdvm_menu_handler import PdvmMenuHandler
            
            # Hole User-Daten aus neuer GCS
            from pdvm_central_systemsteuerung_global_new import gcs
            
            # User-Daten direkt aus GCS holen
            if hasattr(gcs, 'user_daten') and gcs.user_daten:
                self.user_daten = gcs.user_daten
                self.user_name = gcs.user_name or "Benutzer"
                logger.info(f"🔹 User-Daten aus GCS: {self.user_name}")
            else:
                logger.warning("❌ Keine User-Daten in GCS verfügbar!")
                self._show_simple_welcome()
                return
            
            # Startmenü-ID aus Benutzerdaten holen
            self.startmenu_id = self.user_daten.get("Anwendungen", {}).get("MeineApps")
            if not self.startmenu_id:
                logger.warning("❌ Keine Startmenü-GUID in Benutzerdaten gefunden!")
                self._show_simple_welcome()
                return
                
            logger.info(f"🔹 Starte mit Startmenu-ID: {self.startmenu_id}")
            
            # Handler nur initialisieren wenn noch nicht vorhanden
            if not hasattr(self, 'command_handler'):
                self.command_handler = PdvmCommandHandler(self)
                
            self.menu_handler = PdvmMenuHandler(
                root=self,
                menu_widget=self.menu_frame,
                menu_id=self.startmenu_id,
                command_handler=self.command_handler
            )
            
            # Menüs erstellen
            self.menu_handler.create_menus()
            
            # Window title
            self.setWindowTitle(f"PDVM System - Neue Systemsteuerung - {self.user_name}")
            
            # Zentraler Startbildschirm
            self._show_welcome_message()
            
            logger.info("🏠 Startmenü erfolgreich geladen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Startmenüs: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self._show_simple_welcome()
    
    def _show_welcome_message(self):
        """Zeigt Willkommensnachricht im Content-Bereich"""
        try:
            # Clear content area
            for i in reversed(range(self.content_layout.count())):
                widget = self.content_layout.itemAt(i).widget()
                if widget and widget != self.stichtag_bar:  # Stichtagbar behalten
                    widget.setParent(None)
            
            # Welcome messages
            welcome_label = QLabel("🔹 Willkommen im PDVM-System mit neuer Systemsteuerung!")
            welcome_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c5aa0; padding: 10px;")
            self.content_layout.addWidget(welcome_label)
            
            info_label = QLabel("""
🔹 Bitte wählen Sie eine Anwendung aus dem Menü links.
📱 Multi-Tab mit Navigation: F4 für parallele Tab-Anzeige
🔍 Lupe-Funktionen: F1 (View) | F2 (Input) | F3 (Reset)
⌨️ Tab-Navigation: Ctrl+←/→ oder Alt+1-9 für direkten Tab-Zugriff
            """)
            info_label.setStyleSheet("padding: 10px; line-height: 1.4;")
            self.content_layout.addWidget(info_label)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anzeigen der Willkommensnachricht: {e}")
    
    def _show_simple_welcome(self):
        """Zeigt einfache Willkommensnachricht ohne Menü"""
        try:
            # Clear content area except stichtagbar
            for i in reversed(range(self.content_layout.count())):
                widget = self.content_layout.itemAt(i).widget()
                if widget and widget != self.stichtag_bar:
                    widget.setParent(None)
            
            simple_label = QLabel("🏠 PDVM System - Neue Systemsteuerung aktiv")
            simple_label.setStyleSheet("font-size: 16px; font-weight: bold; color: green; padding: 20px;")
            self.content_layout.addWidget(simple_label)
            
            status_label = QLabel("✅ Stichtagbar funktioniert mit neuer Systemsteuerung")
            status_label.setStyleSheet("padding: 10px; color: #666;")
            self.content_layout.addWidget(status_label)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anzeigen der einfachen Willkommensnachricht: {e}")


def main():
    """Hauptfunktion für Test der neuen MainApp"""
    logger.info("🚀 === TEST: NEUE MAINAPP MIT NEUER SYSTEMSTEUERUNG ===")
    
    try:
        # QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        
        # Teste neue GCS-Verfügbarkeit
        from pdvm_central_systemsteuerung_global_new import is_initialized, gcs
        
        if not is_initialized():
            # Für direkten Test: Initialisiere neue GCS
            from pdvm_central_systemsteuerung_global_new import initialize_gcs
            initialize_gcs('test-user-mainapp-new')
            logger.info("🔧 Neue GCS für direkten Test initialisiert")
        
        # Erstelle neue MainApp
        main_window = MainAppNew()
        main_window.show()
        
        logger.info("🎉 Neue MainApp gestartet - teste Stichtagbar!")
        
        # Start event loop nur wenn direkt ausgeführt
        if __name__ == "__main__":
            sys.exit(app.exec_())
            
    except Exception as e:
        logger.error(f"❌ Fehler beim Start der neuen MainApp: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    main()
