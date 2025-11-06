# pdvm_systemstart_correct.py
# KORREKTE HAUPTANWENDUNG basierend auf Original mit neuer Systemsteuerung
"""
MainApp mit korrekter UI-Struktur wie im Original:
- Links: Vertikales Menü (immer sichtbar im Startmenü)
- Rechts oben: Stichtagsbar
- Rechts unten: Arbeitsbereich
- Alle Original-Methoden für Menü-Kommandos
"""

import logging
import sys
import traceback
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QApplication, QFrame, QMessageBox,
                             QTextEdit, QSizePolicy)
from PyQt5.QtCore import Qt

# Setup Logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MainAppCorrect(QMainWindow):
    """
    Hauptanwendung mit korrekter UI-Struktur wie im Original
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize references
        self._gcs_instance = None
        self.stichtag_bar = None
        self.stichtag_picker = None
        self.refresh_button = None
        self.stichtag_display = None
        
        # Layout containers wie im Original
        self.main_layout = None
        self.menu_frame = None
        self.content_frame = None
        self.content_layout = None
        
        # Menu und Command Handler
        self.command_handler = None
        self.menu_handler = None
        self.startmenu_id = None
        
        # User data
        self.user_daten = {}
        self.user_name = ""
        
        # Current display tracking
        self.current_display_widget = None
        self.current_view_widget = None
        
        logger.info("🏠 MainAppCorrect initialisiert")
        
        # UI Setup wie im Original
        self.setup_ui_correct()
        
        # Teste neue GCS nach UI-Setup
        self.test_new_gcs_integration()
        
        # Startmenü laden
        self.open_start_menu()
    
    def setup_ui_correct(self):
        """Setup der Benutzeroberfläche EXAKT wie im Original"""
        try:
            logger.info("🎨 Setup UI korrekt für MainAppCorrect...")
            
            # Window properties
            self.setWindowTitle("PDVM - Neue Systemsteuerung")
            self.setGeometry(100, 100, 1200, 800)
            
            # Zentrales Widget und Layout (EXAKT wie Original)
            central = QWidget()
            self.setCentralWidget(central)
            self.main_layout = QHBoxLayout(central)
            central.setLayout(self.main_layout)

            # Linke Sidebar für vertikales Menü (EXAKT wie Original)
            self.menu_frame = QFrame()
            self.menu_frame.setFrameShape(QFrame.StyledPanel)
            self.menu_frame.setLayout(QVBoxLayout())
            self.main_layout.addWidget(self.menu_frame, 1)

            # Rechter Bereich als Container für Inhalte (EXAKT wie Original)
            self.content_frame = QWidget()
            self.content_layout = QVBoxLayout(self.content_frame)
            self.content_frame.setLayout(self.content_layout)
            
            self.main_layout.addWidget(self.content_frame, 4)
            
            # NEUER ZENTRALER STICHTAG-BALKEN (kompakt)
            logger.info("🔧 Erstelle Stichtag-Balken...")
            self.stichtag_bar = self._create_stichtag_bar_compact()
            
            if self.stichtag_bar:
                logger.info("✅ Stichtag-Balken erstellt, füge zu Layout hinzu...")
                self.content_layout.insertWidget(0, self.stichtag_bar)  # Am Anfang einfügen
                logger.info("✅ Stichtag-Balken erfolgreich zu Layout hinzugefügt")
            else:
                logger.error("❌ Stichtag-Balken konnte nicht erstellt werden!")
            
            # Separator-Line für optische Trennung (wie Original)
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            self.content_layout.insertWidget(1, separator)  # Nach Stichtag-Balken
            
            logger.info("✅ UI Setup korrekt abgeschlossen")
            
        except Exception as e:
            logger.error(f"❌ UI Setup fehlgeschlagen: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _get_new_gcs_safely(self):
        """Holt die neue globale Systemsteuerung sicher"""
        try:
            from pdvm_central_systemsteuerung_global_new import gcs, is_initialized
            
            if is_initialized():
                return gcs
            else:
                logger.error("❌ Neue globale Systemsteuerung ist nicht initialisiert!")
                return None
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Zugriff auf neue GCS: {e}")
            return None
    
    def _create_stichtag_bar_compact(self):
        """Erstellt kompakte Stichtagbar mit neuer Systemsteuerung"""
        try:
            logger.info("🔧 _create_stichtag_bar_compact gestartet...")
            
            # Hole neue GCS
            gcs_instance = self._get_new_gcs_safely()
            if not gcs_instance:
                logger.error("❌ Keine neue GCS verfügbar für Stichtagbar")
                return QLabel("❌ Keine Systemsteuerung verfügbar")
            
            from pdvm_date_time_picker import PdvmDateTimePicker
            
            # Container für Stichtagbar - KOMPAKT
            stichtag_frame = QFrame()
            stichtag_frame.setFrameStyle(QFrame.Box)
            stichtag_frame.setMaximumHeight(45)  # Noch kompakter
            stichtag_frame.setStyleSheet("""
                QFrame {
                    background-color: #f8f8f8;
                    border: 1px solid #d0d0d0;
                    border-radius: 3px;
                    margin: 1px;
                    padding: 2px;
                    max-height: 45px;
                }
            """)
            
            layout = QHBoxLayout(stichtag_frame)
            layout.setContentsMargins(3, 1, 3, 1)  # Sehr kleine Margins
            layout.setSpacing(3)  # Minimaler Abstand
            
            # Label - sehr kompakt
            label = QLabel("Stichtag:")
            label.setStyleSheet("font-weight: bold; font-size: 10px; padding: 1px;")
            label.setMaximumHeight(25)
            layout.addWidget(label)
            
            # DatetimePicker mit globaler Stichtag-Instanz
            try:
                self.stichtag_picker = PdvmDateTimePicker(
                    parent=self,
                    pdvm_datetime=gcs_instance.global_stichtag_inst,
                    display="all",
                    display_time_short=False
                )
                
                # Picker kompakter machen
                if hasattr(self.stichtag_picker, 'setMaximumHeight'):
                    self.stichtag_picker.setMaximumHeight(25)
                
                layout.addWidget(self.stichtag_picker)
                logger.info(f"✅ PdvmDateTimePicker (Neue GCS) erstellt")
                
            except Exception as e:
                logger.error(f"❌ Fehler beim Erstellen des PdvmDateTimePicker: {e}")
                return QLabel(f"❌ DateTimePicker Fehler: {e}")
            
            # Pfeil "→" - sehr kompakt
            arrow_label = QLabel(" → ")
            arrow_label.setStyleSheet("font-size: 10px; font-weight: bold; padding: 1px;")
            arrow_label.setMaximumHeight(25)
            layout.addWidget(arrow_label)
            
            # Anzeige aktueller Stichtag - sehr kompakt
            self.stichtag_display = QLabel()
            self.stichtag_display.setMaximumHeight(25)
            self.stichtag_display.setStyleSheet("""
                background-color: white;
                border: 1px solid #999;
                padding: 2px 4px;
                border-radius: 2px;
                font-family: monospace;
                font-size: 9px;
                max-height: 25px;
            """)
            layout.addWidget(self.stichtag_display)
            
            # Refresh Button - sehr kompakt
            self.refresh_button = QPushButton("↻")  # Symbol statt Text
            self.refresh_button.setMaximumHeight(25)
            self.refresh_button.setMaximumWidth(30)
            self.refresh_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 2px;
                    border-radius: 2px;
                    font-weight: bold;
                    font-size: 10px;
                    max-height: 25px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            layout.addWidget(self.refresh_button)
            
            # Funktionalität verbinden
            if self.refresh_button:
                self.refresh_button.clicked.connect(self._refresh_stichtag_display)
            
            # Initial display aktualisieren
            self._refresh_stichtag_display()
            
            return stichtag_frame
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der kompakten Stichtagbar: {e}")
            return QLabel(f"❌ Stichtagbar Fehler: {e}")
    
    def _refresh_stichtag_display(self):
        """Aktualisiert die Stichtag-Anzeige"""
        try:
            gcs_instance = self._get_new_gcs_safely()
            if gcs_instance and self.stichtag_display:
                current_time = gcs_instance.global_stichtag_inst.FormTimeStamp
                self.stichtag_display.setText(current_time)
                logger.info(f"🔄 Stichtag-Anzeige aktualisiert: {current_time}")
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der Stichtag-Anzeige: {e}")
    
    def test_new_gcs_integration(self):
        """Testet die Integration mit der neuen GCS"""
        try:
            logger.info("🧪 Teste neue GCS-Integration...")
            
            gcs_instance = self._get_new_gcs_safely()
            if gcs_instance:
                logger.info(f"✅ Neue GCS verfügbar:")
                logger.info(f"  - Country: {gcs_instance.country}")
                logger.info(f"  - Stichtag: {gcs_instance.stichtag}")
                logger.info(f"  - Mode: {gcs_instance.mode}")
                logger.info(f"  - Global Stichtag Inst: {gcs_instance.global_stichtag_inst}")
            else:
                logger.error("❌ Neue GCS nicht verfügbar!")
                
        except Exception as e:
            logger.error(f"❌ Neue GCS-Integration Test fehlgeschlagen: {e}")

    def open_start_menu(self):
        """Lädt das Startmenü mit neuer Systemsteuerung - EXAKT wie Original"""
        try:
            logger.info("🏠 Lade Startmenü...")
            
            # 🔒 LAZY IMPORT: Handler erst nach Login laden (wie Original)
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
            
            # Startmenü-ID aus Benutzerdaten holen (wie Original)
            self.startmenu_id = self.user_daten.get("Anwendungen", {}).get("MeineApps")
            if not self.startmenu_id:
                logger.error("❌ Keine Startmenü-GUID in Benutzerdaten gefunden!")
                raise ValueError("Startmenü-GUID fehlt in Benutzerdaten")
                
            logger.info(f"🔹 Starte mit Startmenu-ID: {self.startmenu_id}")
            
            # Debug: Verfügbare Anwendungen anzeigen (wie Original)
            applications = self.user_daten.get("Anwendungen", {}).get("Application", {})
            available_apps = [app for app, config in applications.items() if config.get("Menu")]
            logger.info(f"🔹 Verfügbare Anwendungen für Benutzer: {available_apps}")
            
            # Handler nur initialisieren wenn noch nicht vorhanden (wie Original)
            if not hasattr(self, 'command_handler'):
                self.command_handler = PdvmCommandHandler(self)
                
            self.menu_handler = PdvmMenuHandler(
                root=self,
                menu_widget=self.menu_frame,
                menu_id=self.startmenu_id,
                command_handler=self.command_handler
            )
            
            # Menüs erstellen (wie Original)
            self.menu_handler.create_menus()
            self.setWindowTitle(f"PDVM System - Hauptanwendung - {self.user_name}")
            
            # Zentraler Startbildschirm (wie Original)
            self._show_label("🔹 Willkommen im PDVM-System!", small=False, clear_content=True)
            self._show_label([
                "🔹 Bitte wählen Sie eine Anwendung aus dem Menü links.",
                "📱 Multi-Tab mit Navigation: F4 für parallele Tab-Anzeige → Navigation erscheint",
                "🔍 Lupe-Funktionen: F1 (View) | F2 (Input) | F3 (Reset)",
                "⌨️ Tab-Navigation: Ctrl+←/→ oder Alt+1-9 für direkten Tab-Zugriff"
            ], small=True, clear_content=False)
            
            # Startmenü: Menü immer anzeigen (wie Original)
            self._ensure_menu_visible()
            logger.info("🏠 Startmenü geladen - Menü automatisch eingeblendet")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Startmenüs: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    # ==========================================================================
    # ORIGINAL METHODEN FÜR MENÜ-KOMMANDOS - übernommen aus PDVM-Systemstart.py
    # ==========================================================================
    
    def _show_label(self, texts, small=False, clear_content=True):
        """
        Zeigt Text-Label(s) im Content-Bereich an.
        ORIGINAL METHODE übernommen
        """
        try:
            if clear_content:
                # Lösche alle bestehenden Widgets im Content-Bereich (außer Stichtagbar und Separator)
                for i in reversed(range(self.content_layout.count())):
                    item = self.content_layout.itemAt(i)
                    widget = item.widget()
                    if widget and widget != self.stichtag_bar and not isinstance(widget, QFrame):
                        widget.setParent(None)
            
            # Einzelner Text oder Liste
            if isinstance(texts, str):
                texts = [texts]
            
            for text in texts:
                label = QLabel(text)
                if small:
                    label.setStyleSheet("font-size: 12px; padding: 5px;")
                else:
                    label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
                self.content_layout.addWidget(label)
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Anzeigen von Labels: {e}")
    
    def show_text(self, text):
        """
        Zeigt Text im Content-Bereich an.
        ORIGINAL METHODE übernommen
        """
        self._show_label(text, small=False, clear_content=True)
    
    def show_text_klein(self, text):
        """
        Zeigt kleinen Text im Content-Bereich an.
        ORIGINAL METHODE übernommen
        """
        self._show_label(text, small=True, clear_content=True)
    
    def pdvm_start(self, application_name):
        """
        Startet eine Anwendung basierend auf den Benutzer-Berechtigungen.
        ORIGINAL METHODE übernommen und angepasst
        """
        try:
            logger.info(f"🚀 Starte Anwendung: {application_name}")
            
            # Prüfe Benutzerberechtigung für diese Anwendung
            applications = self.user_daten.get("Anwendungen", {}).get("Application", {})
            
            if application_name not in applications:
                logger.warning(f"❌ Anwendung '{application_name}' nicht in Benutzerdaten gefunden")
                self.show_text(f"❌ Anwendung '{application_name}' nicht vorhanden")
                return
            
            app_config = applications[application_name]
            
            if not app_config.get("Menu"):
                logger.warning(f"❌ Keine Menü-Berechtigung für '{application_name}'")
                self.show_text(f"❌ Keine Berechtigung für '{application_name}'")
                return
            
            # Lade die spezifische Anwendung
            self.show_text(f"🚀 Lade Anwendung: {application_name}")
            
            # Hier würde die spezifische Anwendung geladen werden
            # (Implementation je nach Anwendung)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten der Anwendung '{application_name}': {e}")
            self.show_text(f"❌ Fehler beim Starten von '{application_name}': {e}")
    
    def toggle_menu_visibility(self):
        """
        Blendet das Menü ein/aus.
        ORIGINAL METHODE übernommen
        """
        try:
            if self.menu_frame.isVisible():
                self.menu_frame.hide()
                logger.info("🔒 Menü ausgeblendet")
            else:
                self.menu_frame.show()
                logger.info("🔓 Menü eingeblendet")
        except Exception as e:
            logger.error(f"❌ Fehler beim Toggle Menü-Sichtbarkeit: {e}")
    
    def _ensure_menu_visible(self):
        """
        Stellt sicher, dass das Menü sichtbar ist.
        ORIGINAL METHODE übernommen
        """
        try:
            if not self.menu_frame.isVisible():
                self.menu_frame.show()
                logger.info("🔓 Menü sichtbar gemacht")
        except Exception as e:
            logger.error(f"❌ Fehler beim Sichtbar-machen des Menüs: {e}")
    
    def _show_simple_welcome(self):
        """Zeigt einfache Willkommensnachricht ohne Menü"""
        try:
            self._show_label([
                "🏠 PDVM System - Neue Systemsteuerung aktiv",
                "✅ Stichtagbar funktioniert mit neuer Systemsteuerung",
                "⚠️ Startmenü konnte nicht geladen werden - prüfe User-Daten"
            ], small=False, clear_content=True)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anzeigen der einfachen Willkommensnachricht: {e}")


def main():
    """Hauptfunktion für Test der korrekten MainApp"""
    logger.info("🚀 === TEST: KORREKTE MAINAPP MIT NEUER SYSTEMSTEUERUNG ===")
    
    try:
        # QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        
        # Teste neue GCS-Verfügbarkeit
        from pdvm_central_systemsteuerung_global_new import is_initialized, gcs
        
        if not is_initialized():
            # Für direkten Test: Initialisiere neue GCS
            from pdvm_central_systemsteuerung_global_new import initialize_gcs
            initialize_gcs('test-user-mainapp-correct')
            logger.info("🔧 Neue GCS für direkten Test initialisiert")
        
        # Erstelle korrekte MainApp
        main_window = MainAppCorrect()
        main_window.show()
        
        logger.info("🎉 Korrekte MainApp gestartet!")
        
        # Start event loop nur wenn direkt ausgeführt
        if __name__ == "__main__":
            sys.exit(app.exec_())
            
    except Exception as e:
        logger.error(f"❌ Kritischer Fehler beim Start der korrekten MainApp: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    main()
