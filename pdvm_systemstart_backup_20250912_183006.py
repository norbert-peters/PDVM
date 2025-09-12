# pdvm_systemstart.py - BEREINIGT
import sys, io, os, logging

# Erzwinge UTF-8 für alle IO
os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Logger-Setup noch VOR allen anderen Imports!
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("pdvm_app.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)
logger.info("🔹 Hauptanwendung gestartet")

import json
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QApplication,
    QDateTimeEdit, QPushButton
)
from PyQt5.QtCore import Qt, QDateTime, QDate, QTime
from PyQt5.QtGui import QFont

# 🔒 SICHERE IMPORTS: Nur grundlegende Komponenten - Handler werden lazy geladen
from pdvm_central_datenbank import PdvmCentralDatenbank
# NOTE: Systemsteuerung wird ERST nach Login importiert!

# 🔒 LAZY IMPORTS: Werden erst nach Login geladen
# from pdvm_central_systemsteuerung_global import initialize_after_login  # ← Nach Login
# from pdvm_login import LoginApp                 # ← Lazy Import
# from pdvm_command_handler import PdvmCommandHandler  # ← Lazy Import  
# from pdvm_menu_handler import PdvmMenuHandler        # ← Lazy Import
# from pdvm_menu_editor import PdvmMenuEditor          # ← Lazy Import


            

# Hauptanwendungsklasse
# Diese Klasse wird nach erfolgreichem Login instanziiert
class MainApp(QMainWindow):
    def __init__(self, user_daten):
        super().__init__()
        self.setWindowTitle("PDVM System - Hauptanwendung")
        self.resize(1000, 600)
        self.user_email = user_daten[0]  # Benutzername
        self.user_guid = user_daten[3]  # Benutzer GUID 
        
        # user_daten als dict laden
        if isinstance(user_daten[1], str):
            try:
                self.user_daten = json.loads(user_daten[2])
            except json.JSONDecodeError:
                self.user_daten = {}
        else:
            self.user_daten = user_daten[2]

        # Hilfsfunktion für sicheren Zugriff auf globale Systemsteuerung
        self._gcs_instance = None
    
        # Benutzername in der Titelleiste anzeigen
        self.user_name = f"{self.user_daten.get("Benutzer").get("Vorname")} {self.user_daten.get("Benutzer").get("Name")}"
        self.setWindowTitle(f"PDVM System - Hauptanwendung - {self.user_name}")

        # Startmenü-ID aus Benutzerdaten holen
        self.startmenu_id = self.user_daten.get("Anwendungen", {}).get("MeineApps")
        if not self.startmenu_id:
            logger.error("❌ Keine Startmenü-GUID in Benutzerdaten gefunden!")
            raise ValueError("Startmenü-GUID fehlt in Benutzerdaten")
            
        logging.log(logging.INFO, f"🔹 Starte mit Startmenu-ID: {self.startmenu_id}")
        
        # Debug: Verfügbare Anwendungen anzeigen
        applications = self.user_daten.get("Anwendungen", {}).get("Application", {})
        available_apps = [app for app, config in applications.items() if config.get("Menu")]
        logger.info(f"🔹 Verfügbare Anwendungen für Benutzer: {available_apps}")

        # Zentrales Widget und Layout
        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QHBoxLayout(central)
        central.setLayout(self.main_layout)

        # Linke Sidebar für vertikales Menü
        self.menu_frame = QFrame()
        self.menu_frame.setFrameShape(QFrame.StyledPanel)
        self.menu_frame.setLayout(QVBoxLayout())
        self.main_layout.addWidget(self.menu_frame, 1)

        # Rechter Bereich als Container für Inhalte
        self.content_frame = QWidget()
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_frame.setLayout(self.content_layout)
        
        self.main_layout.addWidget(self.content_frame, 4)

        # 🔒 LAZY IMPORT: Handler erst nach Login laden
        from pdvm_command_handler import PdvmCommandHandler
        self.command_handler = PdvmCommandHandler(self)
        
        # ZENTRALE SYSTEMSTEUERUNG-INSTANZ erstellen (nur einmal für die gesamte Anwendung)
        self._initialize_central_systemsteuerung()
        
        # NEUER ZENTRALER STICHTAG-BALKEN nach Systemsteuerung-Initialisierung
        logger.info("🔧 Erstelle Stichtag-Balken...")
        self.stichtag_bar = self._create_stichtag_bar()
        if self.stichtag_bar:
            logger.info("✅ Stichtag-Balken erstellt, füge zu Layout hinzu...")
            self.content_layout.insertWidget(0, self.stichtag_bar)  # Am Anfang einfügen
            logger.info("✅ Stichtag-Balken erfolgreich zu Layout hinzugefügt")
        else:
            logger.error("❌ Stichtag-Balken konnte nicht erstellt werden!")
        
        # Separator-Line für optische Trennung
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.content_layout.insertWidget(1, separator)  # Nach Stichtag-Balken
        
        # Startmenü laden (DRY-Prinzip: Eine zentrale Methode für Startmenü)
        self.open_start_menu()

    def _get_gcs_safely(self):
        """
        MODERNE LINEARE SYSTEMSTEUERUNG-ZUGRIFF:
        
        Verwendet direkt das globale gcs-Proxy-Objekt für Zugriff.
        Keine lokale Instanz-Verwaltung mehr nötig.
        
        Returns:
            PdvmCentralSystemsteuerung oder None falls nicht initialisiert
        """
        try:
            from pdvm_central_systemsteuerung_global import gcs, is_initialized
            
            if is_initialized():
                # Direkter Zugriff über globales gcs-Proxy
                return gcs
            else:
                logger.warning("⚠️ Globale Systemsteuerung noch nicht initialisiert")
                return None
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Zugriff auf globale Systemsteuerung: {e}")
            return None



    def _create_stichtag_bar(self):
        """
        Erstellt den zentralen Stichtag-Balken für historische Datenansicht.
        
        Verwendet die zentrale PdvmDateTime-Instanz aus dem StichtagManager.
        Layout: 'Stichtag:' (PdvmDateTimePicker) --> verwendeter Stichtag: (PdvmTimeStamp) [Refresh]
        
        Returns:
            QWidget: Stichtag-Balken Widget
        """
        logger.info("🔧 _create_stichtag_bar gestartet...")
        
        from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QFrame
        from PyQt5.QtGui import QFont
        from pdvm_date_time_picker import PdvmDateTimePicker
        
        # Prüfe globale Systemsteuerung (gcs)
        gcs_instance = self._get_gcs_safely()
        if not gcs_instance:
            logger.error("❌ Globale Systemsteuerung nicht verfügbar - kann Balken nicht erstellen")
            return QLabel("❌ Systemsteuerung nicht verfügbar")
        logger.info("✅ Globale Systemsteuerung verfügbar")
        
        # Hauptcontainer für Stichtag-Balken
        stichtag_widget = QFrame()
        stichtag_widget.setFrameStyle(QFrame.StyledPanel)
        stichtag_widget.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 1px solid #c0c0c0;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        logger.info("✅ Stichtag-Widget Container erstellt")
        
        layout = QHBoxLayout(stichtag_widget)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # "Stichtag:" Label
        stichtag_label = QLabel("Stichtag:")
        font = QFont()
        font.setBold(True)
        stichtag_label.setFont(font)
        layout.addWidget(stichtag_label)
        logger.info("✅ Stichtag-Label hinzugefügt")
        
        # Stichtag-Instanz aus globaler Systemsteuerung holen
        try:
            stichtag_inst = gcs_instance.global_stichtag_inst
            # PdvmDateTimePicker arbeitet direkt auf der Instanz
            self.stichtag_picker = PdvmDateTimePicker(
                parent=self,
                pdvm_datetime=gcs_instance.global_stichtag_inst,  # Instanz!
#                pdvm_datetime=stichtag_inst,  # Instanz!
                display="all",
                display_time_short=False
            )
            logger.info(f"✅ PdvmDateTimePicker (Instanz) Datum: {gcs_instance.global_stichtag_inst.PdvmDateTime}") 
            if hasattr(self.stichtag_picker, '_date_edit'):
                calendar = self.stichtag_picker._date_edit.calendarWidget()
                if calendar:
                    calendar.setMinimumSize(350, 220)
            layout.addWidget(self.stichtag_picker)
            logger.info("✅ PdvmDateTimePicker (Instanz) erstellt und hinzugefügt")
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des PdvmDateTimePicker: {e}")
            return QLabel(f"❌ Fehler beim Erstellen des DateTimePicker: {e}")
        
        # Pfeil "→"
        arrow_label = QLabel(" → ")
        arrow_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(arrow_label)
        
        # "verwendeter Stichtag:" Label
        verwendeter_label = QLabel("verwendeter Stichtag:")
        layout.addWidget(verwendeter_label)
        
        # PdvmTimeStamp Anzeige (schreibgeschützt)
        self.stichtag_display = QLabel()
        self.stichtag_display.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #a0a0a0;
                border-radius: 3px;
                padding: 3px 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-weight: bold;
            }
        """)
        self._update_stichtag_display()
        layout.addWidget(self.stichtag_display)
        logger.info("✅ Stichtag-Display erstellt")
        
        # Refresh Button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.refresh_button.clicked.connect(self._on_stichtag_refresh)
        layout.addWidget(self.refresh_button)
        logger.info("✅ Refresh-Button erstellt")
        
        # Stretch am Ende für rechte Ausrichtung
        layout.addStretch(1)
        
        logger.info("✅ Stichtag-Balken vollständig erstellt")
        return stichtag_widget

    def _update_stichtag_display(self):
        """
        Aktualisiert die Anzeige des verwendeten Stichtags.
        Verwendet PdvmTimeStamp aus der globalen Stichtag-Instanz.
        """
        try:
            gcs_instance = self._get_gcs_safely()
            if gcs_instance:
                stichtag_inst = gcs_instance.global_stichtag_inst
                # Anzeige als PdvmTimeStamp (schönes Format)
                self.stichtag_display.setText(str(getattr(stichtag_inst, 'FormTimeStamp', stichtag_inst.PdvmDateTime)))
                logger.debug(f"🔄 Stichtag-Anzeige aktualisiert: {getattr(stichtag_inst, 'FormTimeStamp', stichtag_inst.PdvmDateTime)}")
            else:
                self.stichtag_display.setText("Stichtag lädt...")
                logger.warning("⚠️ Globale Systemsteuerung nicht verfügbar für Display-Update")
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der Stichtag-Anzeige: {e}")
            self.stichtag_display.setText("Fehler beim Laden")

    def _on_stichtag_refresh(self):
        """
        🎯 NEUE LINEARE REFRESH-ARCHITEKTUR:
        
        Behandelt den Refresh-Button Click mit linearer Technik:
        1. save() auf Picker → Änderungen landen direkt in zentraler Instanz  
        2. Manager informieren zur Persistierung
        3. Anzeige aktualisieren
        4. Aktuellen Menüpunkt neu laden (allgemein gültig für alle Menüpunkte)
        
        Ein Refresh ist ein wiederholter Aufruf des Menüpunktes mit first_call=False.
        """
        try:
            logger.info("🎯 Stichtag-Refresh: Lineare Architektur gestartet")
            gcs_instance = self._get_gcs_safely()
            
            if gcs_instance:
                # 1. Picker speichert direkt in die Instanz
                if hasattr(self.stichtag_picker, 'save'):
                    self.stichtag_picker.save()
                    logger.info("✅ Picker.save() ausgeführt → Wert in Instanz geschrieben")
                
                # 2. Persistiere über globale Systemsteuerung  
                gcs_instance.save_stichtag()
                logger.info("✅ Stichtag in DB gespeichert (save_stichtag)")
                
                # 3. Anzeige aktualisieren
                self._update_stichtag_display()
                
                # 4. 🎯 NEUE LINEARE TECHNIK: Menüpunkt refresh über current_command
                refresh_call_daten = gcs_instance.refresh_current_menu()
                
                if refresh_call_daten:
                    logger.info("🎯 Führe linearen Menü-Refresh aus (first_call=False)")
                    self._execute_menu_refresh(refresh_call_daten)
                else:
                    logger.info("ℹ️ Kein aktueller Menüpunkt für Refresh verfügbar")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Stichtag-Refresh: {e}")
            self._update_stichtag_display()
    
    def _execute_menu_refresh(self, refresh_call_daten):
        """
        🎯 NEUE LINEARE REFRESH-ARCHITEKTUR:
        
        Führt den Menü-Refresh durch - allgemein gültig für alle Menüpunkte.
        Ein Refresh ist ein wiederholter Aufruf des Menüpunktes mit first_call=False.
        
        Args:
            refresh_call_daten (dict): Call-Daten mit first_call=False für Refresh
        """
        try:
            logger.info("🎯 Starte linearen Menü-Refresh...")
            
            # Schließe aktuelles Display-Widget falls vorhanden
            if hasattr(self, 'current_display_widget') and self.current_display_widget:
                logger.info("🔄 Entferne aktuelles Display-Widget für Refresh")
                self.content_layout.removeWidget(self.current_display_widget)
                self.current_display_widget.deleteLater()
                self.current_display_widget = None
                
            # Setze Dialog-Referenz zurück
            if hasattr(self, 'current_view_widget'):
                self.current_view_widget = None
            
            # 🎯 LINEARE TECHNIK: Wiederholter Menüaufruf mit first_call=False
            logger.info(f"🎯 Führe Menü-Refresh aus: {refresh_call_daten.get('title', 'Unknown')}")
            
            # Lade den Handler für den Refresh-Aufruf
            from pdvm_view_dialog import PdvmViewDialog
            
            # Erstelle neuen Dialog mit Refresh-call_daten
            view_dialog = PdvmViewDialog(refresh_call_daten, parent=self)
            view_widget = view_dialog.get_display_widget()
            
            # Zeige refreshten Content
            self.content_layout.addWidget(view_widget)
            view_widget.show()
            
            # Speichere Referenzen für weiteren Refresh
            self.current_view_widget = view_dialog  # PdvmViewDialog-Instanz
            self.current_display_widget = view_widget  # Das tatsächliche QWidget
            
            logger.info("✅ Linearer Menü-Refresh erfolgreich abgeschlossen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Menü-Refresh: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")

    def _refresh_stichtag_bar_after_init(self):
        """
        Aktualisiert den Stichtag-Balken nach vollständiger Initialisierung.
        Da wir die globale Instanz verwenden, ist normalerweise kein Update nötig.
        """
        try:
            if hasattr(self, 'stichtag_picker') and self.stichtag_picker:
                logger.info("🔄 Aktualisiere Stichtag-Balken nach Initialisierung")
                
                # Picker sollte bereits die globale Instanz verwenden,
                # aber wir können das Display trotzdem aktualisieren
                if hasattr(self.stichtag_picker, 'update_display'):
                    self.stichtag_picker.update_display()
                self._update_stichtag_display()
                
                logger.info("✅ Stichtag-Balken erfolgreich aktualisiert")
            else:
                logger.warning("⚠️ Stichtag-Balken-Komponenten nicht verfügbar für Update")
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren des Stichtag-Balkens: {e}")

    def _initialize_central_systemsteuerung(self):
        """
        Initialisiert die zentrale Systemsteuerung-Instanz für die gesamte Anwendung.
        
        SICHERHEITS-ARCHITEKTUR:
        - PdvmCentralSystemsteuerung wird ERST nach Login mit user_guid erstellt
        - Lazy Import der Systemsteuerung-Module erst hier
        - Keine Fallbacks auf "default_user" mehr!
        """
        try:
            if not self.user_guid:
                raise ValueError("❌ KRITISCH: user_guid fehlt! Login nicht erfolgreich.")
            
            logger.info(f"🎛️ Initialisiere Systemsteuerung nach Login für User: {self.user_guid}")
            
            # LAZY IMPORT: Erst nach Login importieren
            from pdvm_central_systemsteuerung import PdvmCentralSystemsteuerung
            import pdvm_central_systemsteuerung_global
            
            # ✅ SICHERE INITIALISIERUNG: Globale Systemsteuerung mit user_guid
            pdvm_central_systemsteuerung_global.initialize_after_login(self.user_guid)
            
            # Lokale Referenz für diese Klasse
            self.central_systemsteuerung = pdvm_central_systemsteuerung_global.get_central_systemsteuerung()
            
            # Debug-Ausgabe aller initialisierten Werte
            self.central_systemsteuerung.debug_values()
            
            # Sprache für App-Kontext übernehmen
            self.language = self.central_systemsteuerung.global_language
            
            logger.info(f"✅ Zentrale Systemsteuerung sicher initialisiert")
            logger.info(f"🎯 Alle Werte verfügbar über Properties: global_stichtag, global_expert_mode, global_mode, global_language, global_country")
            
            # Stichtag-Balken nach vollständiger Initialisierung aktualisieren
            self._refresh_stichtag_bar_after_init()
            
        except Exception as e:
            logger.error(f"❌ KRITISCHER FEHLER bei Systemsteuerung-Initialisierung: {e}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"Systemsteuerung konnte nicht initialisiert werden: {e}") from e
            self.central_systemsteuerung = None
            self.language = "de-de"
            self.language = "DE"

    def _refresh_stichtag_bar_after_init(self):
        """
        Aktualisiert den Stichtag-Balken nach vollständiger Initialisierung.
        Da wir die globale Instanz verwenden, ist normalerweise kein Update nötig.
        """
        try:
            if hasattr(self, 'stichtag_picker') and self.stichtag_picker:
                logger.info("🔄 Aktualisiere Stichtag-Balken nach Initialisierung")
                
                # Picker sollte bereits die globale Instanz verwenden,
                # aber wir können das Display trotzdem aktualisieren
                if hasattr(self.stichtag_picker, 'update_display'):
                    self.stichtag_picker.update_display()
                self._update_stichtag_display()
                
                logger.info("✅ Stichtag-Balken erfolgreich aktualisiert")
            else:
                logger.warning("⚠️ Stichtag-Balken-Komponenten nicht verfügbar für Update")
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren des Stichtag-Balkens: {e}")

    def _show_label(self, texts, small=False, clear_content=True):
        """
        Zeigt eine oder mehrere Zeilen Text im Inhaltsbereich an.
        texts: Liste von Strings (oder ein einzelner String)
        """
        if clear_content:
            self.clear_content_layout()
        
        # Größerer oberer Abstand (30px statt vorher zentriert)
        self.content_layout.addSpacing(30)
        
        # Labels
        if isinstance(texts, str):
            texts = [texts]
        for text in texts:
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignCenter)
            if small:
                lbl.setStyleSheet("font-size: 12px; margin: 5px;")
            else:
                lbl.setStyleSheet("font-size: 16px; margin: 10px;")
            self.content_layout.addWidget(lbl)
        
        # Flexibler unterer Abstand (nimmt den restlichen Platz ein)
        self.content_layout.addStretch(1)

    def show_text(self, text):
        """Normaler Text im Hauptbereich."""
        self._show_label(f"{text}", small=False, clear_content=True)

    def show_text_klein(self, text):
        """Kleine Meldung unten anhängen."""
        # Einfache Implementierung: Zeige als normalen Text
        self._show_label(f"{text}", small=True, clear_content=True)

    def clear_content_layout(self):
        """
        Löscht alle Inhalte aus dem content_layout.
        SCHÜTZT den Stichtag-Balken (Index 0) und Separator (Index 1).
        """
        # Rückwärts durch das Layout gehen, um Indizes stabil zu halten
        # Beginne bei Index 2, um Stichtag-Balken (0) und Separator (1) zu schützen
        protected_items = 2  # Stichtag-Balken + Separator
        
        while self.content_layout.count() > protected_items:
            # Immer das letzte Item nehmen (höchster Index)
            last_index = self.content_layout.count() - 1
            item = self.content_layout.takeAt(last_index)
            
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
                logger.debug(f"🗑️ Widget entfernt: {widget.__class__.__name__}")
            elif item.layout():
                # Falls ein verschachteltes Layout, rekursiv löschen
                self._clear_layout(item.layout())
                logger.debug("🗑️ Layout entfernt")
            # Spacer/Stretches werden durch takeAt automatisch entfernt
        
        logger.debug(f"✅ Content-Layout bereinigt - {protected_items} geschützte Items behalten")

    def _clear_layout(self, layout):
        """Hilfsmethode zum rekursiven Löschen von Layouts"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())

    def open_menu_editor(self, menu_type, call_path=None):
        """Zeigt den Menüeditor im Inhaltsbereich an."""
        logger.debug(f"🔹 Öffne Menüeditor für Typ: {menu_type} - Pfad: {call_path}")
        logger.info(f"🔹 Benutzer {self.user_name} öffnet Menüeditor für {menu_type}")
        
        # Lazy Import - nur bei Bedarf laden
        from pdvm_menu_editor import PdvmMenuEditor
        
        # Inhalt löschen
        self.clear_content_layout()
        
        # Editor instanziieren und anzeigen
        editor = PdvmMenuEditor(self.content_frame, self.menu_handler.menu, menu_type, self, call_path)
        self.content_layout.addWidget(editor)

    def open_start_menu(self):
        """Lädt erneut das Startmenü."""
        # 🔒 LAZY IMPORT: Handler erst nach Login laden
        from pdvm_command_handler import PdvmCommandHandler
        from pdvm_menu_handler import PdvmMenuHandler
        
        # Handler nur initialisieren wenn noch nicht vorhanden (für __init__)
        if not hasattr(self, 'command_handler'):
            self.command_handler = PdvmCommandHandler(self)
            
        self.menu_handler = PdvmMenuHandler(
            root=self,
            menu_widget=self.menu_frame,
            menu_id=self.startmenu_id,
            command_handler=self.command_handler
        )
        self.menu_handler.create_menus()
        self.setWindowTitle(f"PDVM System - Hauptanwendung - {self.user_name}")
        
        # Zentraler Startbildschirm - wird sowohl im __init__ als auch beim Zurückkehren verwendet
        self._show_label("🔹 Willkommen im PDVM-System!", small=False, clear_content=True)
        self._show_label([
            "🔹 Bitte wählen Sie eine Anwendung aus dem Menü links.",
            "📱 Multi-Tab mit Navigation: F4 für parallele Tab-Anzeige → Navigation erscheint",
            "🔍 Lupe-Funktionen: F1 (View) | F2 (Input) | F3 (Reset)",
            "⌨️ Tab-Navigation: Ctrl+←/→ oder Alt+1-9 für direkten Tab-Zugriff"
        ], small=True, clear_content=False)
        
        # Startmenü: Menü immer anzeigen (Sicherheit)
        self._ensure_menu_visible()
        logger.info("🏠 Startmenü geladen - Menü automatisch eingeblendet")

    def pdvm_start(self, application_name):
        """
        Startet eine Anwendung basierend auf den Benutzer-Berechtigungen.
        
        Args:
            application_name: Name der Anwendung aus den Benutzerdaten
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
            menu_guid = app_config.get("Menu")
            
            if not menu_guid:
                logger.warning(f"❌ Keine Menü-GUID für Anwendung '{application_name}' gefunden")
                self.show_text(f"❌ Anwendung '{application_name}' nicht verfügbar\n(Keine Menü-Berechtigung)")
                return
            
            # Menü-Status für vorheriges Menü speichern
            self._save_menu_visibility_status()
            
            # 🔒 LAZY IMPORT: MenuHandler erst nach Login laden
            from pdvm_menu_handler import PdvmMenuHandler
            
            # Neues Anwendungsmenü laden
            self.menu_handler = PdvmMenuHandler(
                root=self,
                menu_widget=self.menu_frame,
                menu_id=menu_guid,
                command_handler=self.command_handler
            )
            
            try:
                self.menu_handler.create_menus()
                self.setWindowTitle(f"PDVM {application_name} - {self.user_name}")
                self.show_text(f"🔹 Willkommen in {application_name}!")
                
                # Menü-Status für neues Menü wiederherstellen
                self._restore_menu_visibility_status(menu_guid)
                
                logger.info(f"✅ Anwendung '{application_name}' erfolgreich geladen mit Menü-GUID: {menu_guid}")
                
            except Exception as menu_error:
                logger.error(f"❌ Fehler beim Laden des Menüs für '{application_name}': {menu_error}")
                self.show_text(f"❌ Fehler beim Laden der Anwendung '{application_name}'\n{str(menu_error)}")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten der Anwendung '{application_name}': {e}")
            self.show_text(f"❌ Fehler beim Starten der Anwendung '{application_name}'\n{str(e)}")

    def pdvm_modern_view(self, frame_guid, title=None):
        """
        🔧 TITEL-FIX: Moderne View-Dialog Integration mit korrekter Titel-Übergabe
        
        Vereinfachte Dialog-basierte View-Architektur:
        - Dialog = autonome Anwendung + Datenmanager
        - Display = nur UI-Verantwortung
        - Lineare Ausführung statt komplexe Widget/Manager-Struktur
        """
        if not frame_guid:
            logger.error("❌ Es wurde keine frame_guid übergeben!")
            self.show_text("❌ Fehler: Keine Frame-GUID übergeben")
            return

        try:
            logger.info(f"🚀 Starte moderne View für Frame: {frame_guid}")
            
            # Frame-Daten laden (bestehende Logik)
            framedaten_db = PdvmCentralDatenbank(
                table_name="framedaten", 
                guid=frame_guid
            )
            
            # View-GUID aus Frame-Daten ermitteln (bestehende Logik)
            view_guid = framedaten_db.get_static_value("ROOT", "VIEW_GUID")
            if not view_guid:
                logger.error(f"❌ Keine view_guid in Frame-Daten gefunden für Frame: {frame_guid}")
                self.show_text(f"❌ Fehler: Keine View-GUID für Frame {frame_guid} gefunden")
                return

            logger.info(f"📋 View-GUID ermittelt: {view_guid}")
            
            # 🔧 TITEL-ERSTELLUNG aus Frame-Daten oder Parameter
            view_title = title
            if not view_title:
                # Versuche Titel aus Frame-Daten zu holen
                try:
                    view_header = framedaten_db.get_static_value("ROOT", "VIEW_HEADER")
                    if view_header:
                        view_title = view_header
                    else:
                        view_title = f"Personalstamm Verwaltung"
                        logger.info(f"📝 Titel aus Frame-Header erstellt: {view_title}")
                except Exception as title_error:
                    logger.warning(f"⚠️ Fehler beim Titel-Laden: {title_error}")
                    view_title = f"View: {view_guid}"

            # call_daten für neuen Dialog vorbereiten - ALLE ERFORDERLICHEN Daten
            call_daten = {
                "view_guid": view_guid,
                "user_guid": self.user_guid,
                "title": view_title,  # Immer einen Titel setzen!
                "first_call": True,  # Initialer Aufruf
            }
            
            logger.info(f"📋 Call-Daten vorbereitet: view_guid={view_guid}, user_guid={self.user_guid}, title='{view_title}'")

            # 🎯 NEUE REFRESH-ARCHITEKTUR: Command in Systemsteuerung speichern
            gcs_instance = self._get_gcs_safely()
            if gcs_instance:
                gcs_instance.set_menu_command(call_daten, from_menu=True)
                call_daten = gcs_instance.prepare_call_daten(call_daten)  # first_call automatisch setzen
                logger.info("🎯 Menübefehl in Systemsteuerung gespeichert für Refresh-Mechanismus")

            # Neue Dialog-Architektur starten
            from pdvm_view_dialog import PdvmViewDialog
            
            view_dialog = PdvmViewDialog(call_daten, parent=self)
            
            # Widget für Arbeitsbereich holen und integrieren
            view_widget = view_dialog.get_display_widget()
            
            # Altes Content löschen und neues Widget hinzufügen
            self.clear_content_layout()
            self.content_layout.addWidget(view_widget)
            
            # ViewDialog für Stichtag-Refresh speichern (nicht nur das Display-Widget!)
            self.current_view_widget = view_dialog  # Das Dialog hat die reload() Methode
            self.current_display_widget = view_widget  # Für spätere Verwendung
            
            logger.info(f"✅ Moderne View-Dialog gestartet: {view_guid} mit Titel '{view_title}'")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten der modernen View: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Benutzerfreundliche Fehlermeldung anzeigen
            self.show_text(f"❌ Fehler beim Laden der View:\n\n{str(e)}")

    def toggle_menu_visibility(self):
        """
        Schaltet die Sichtbarkeit des vertikalen Menüs um.
        
        Entfernt oder fügt das vertikale Menü (menu_frame) zum Layout hinzu
        und gibt dem Content-Bereich den gesamten verfügbaren Platz.
        """
        try:
            # Status-Variable für Menü-Sichtbarkeit initialisieren falls nicht vorhanden
            if not hasattr(self, '_menu_visible'):
                self._menu_visible = True
            
            if self._menu_visible:
                # Menü aus Layout entfernen
                self.main_layout.removeWidget(self.menu_frame)
                self.menu_frame.hide()
                logger.info("🎛️ Vertikales Menü ausgeblendet - Content-Bereich vergrößert")
                self._menu_visible = False
            else:
                # Menü wieder zum Layout hinzufügen
                self.main_layout.insertWidget(0, self.menu_frame, 1)  # Position 0 = links
                self.menu_frame.show()
                logger.info("🎛️ Vertikales Menü eingeblendet - Layout wiederhergestellt")
                self._menu_visible = True
            
            # Layout-Update erzwingen
            self.main_layout.update()
            QApplication.processEvents()
            
            # Aktuellen Status speichern
            self._save_menu_visibility_status()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Umschalten der Menü-Sichtbarkeit: {e}")

    def _ensure_menu_visible(self):
        """Stellt sicher, dass das Menü sichtbar ist."""
        if not hasattr(self, '_menu_visible'):
            self._menu_visible = True
            
        if not self._menu_visible:
            self.main_layout.insertWidget(0, self.menu_frame, 1)
            self.menu_frame.show()
            self._menu_visible = True
            self.main_layout.update()
            QApplication.processEvents()

    def _get_current_menu_id(self):
        """Holt die aktuelle Menü-ID."""
        if hasattr(self, 'menu_handler') and self.menu_handler:
            return self.menu_handler.menu_id
        return self.startmenu_id

    def _save_menu_visibility_status(self):
        """Speichert den Menü-Sichtbarkeits-Status für das aktuelle Menü in der systemsteuerung-Tabelle."""
        try:
            gcs_instance = self._get_gcs_safely()
            if not gcs_instance:
                logger.warning("⚠️ Globale Systemsteuerung nicht verfügbar - Menü-Status wird nicht gespeichert")
                return
            
            current_menu_id = self._get_current_menu_id()
            menu_visible = getattr(self, '_menu_visible', True)
            
            # MenuStatus unter user_guid-Gruppe speichern
            gcs_instance.set_value(
                gruppe=self.user_guid,  # user_guid ist die Gruppe
                feld=f"menu_{current_menu_id}",  # Feld: menu_<menu_id>
                wert=menu_visible,
                ab_zeit=1001.0  # Standard-Zeitstempel für nicht-historische Felder
            )
            
            # Änderungen persistieren
            gcs_instance.save_values()
            
            logger.debug(f"💾 Menü-Status in globale Systemsteuerung gespeichert: Gruppe={self.user_guid}, Feld=menu_{current_menu_id}, Wert={menu_visible}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern des Menü-Status: {e}")

    def _restore_menu_visibility_status(self, menu_id):
        """Stellt den gespeicherten Menü-Sichtbarkeits-Status aus der systemsteuerung-Tabelle wieder her."""
        try:
            # Startmenü: Immer sichtbar
            if menu_id == self.startmenu_id:
                self._ensure_menu_visible()
                return
            
            gcs_instance = self._get_gcs_safely()
            if not gcs_instance:
                logger.warning("⚠️ Globale Systemsteuerung nicht verfügbar - Menü wird eingeblendet")
                self._ensure_menu_visible()
                return
            
            # MenuStatus aus user_guid-Gruppe laden
            menu_value = gcs_instance.get_value(
                gruppe=self.user_guid,  # user_guid ist die Gruppe
                feld=f"menu_{menu_id}",  # Feld: menu_<menu_id>
                ab_zeit=None  # Aktueller Zeitstempel
            )
            saved_visibility = menu_value.get("wert", True) if menu_value else True  # Default: sichtbar
            
            # Status anwenden
            if saved_visibility and not getattr(self, '_menu_visible', True):
                # Menü einblenden
                self.main_layout.insertWidget(0, self.menu_frame, 1)
                self.menu_frame.show()
                self._menu_visible = True
                logger.info(f"🔄 Menü für {menu_id} wiederhergestellt: eingeblendet")
            elif not saved_visibility and getattr(self, '_menu_visible', True):
                # Menü ausblenden
                self.main_layout.removeWidget(self.menu_frame)
                self.menu_frame.hide()
                self._menu_visible = False
                logger.info(f"🔄 Menü für {menu_id} wiederhergestellt: ausgeblendet")
            
            self.main_layout.update()
            QApplication.processEvents()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Wiederherstellen des Menü-Status: {e}")
            # Fallback: Menü anzeigen
            self._ensure_menu_visible()

    def debug_systemsteuerung(self):
        """
        DEBUG-Methode: Zeigt den Zustand der zentralen Systemsteuerung an
        """
        logger.info("🔍 DEBUG: Zentrale Systemsteuerung-Zustand")
        
        if not self.central_systemsteuerung:
            logger.error("❌ Keine zentrale Systemsteuerung verfügbar!")
            self.show_text("❌ Keine zentrale Systemsteuerung verfügbar!")
            return
        
        try:
            # Alle Daten aus der Systemsteuerung laden
            all_data = self.central_systemsteuerung.lesen()
            
            info_lines = [
                "🔍 SYSTEMSTEUERUNG DEBUG-INFO",
                "=" * 40,
                f"Tabelle: {self.central_systemsteuerung.table_name}",
                f"GUID: {self.central_systemsteuerung.guid}",
                f"Historisch: {self.central_systemsteuerung.historisch}",
                f"User-GUID: {self.user_guid}",
                "",
                f"Gefundene Gruppen: {len(all_data) if all_data else 0}",
            ]
            
            if all_data:
                info_lines.append("\nGruppen:")
                for gruppe_name, gruppe_data in list(all_data.items())[:10]:  # Erste 10 Gruppen
                    felder_count = len(gruppe_data) if isinstance(gruppe_data, dict) else 1
                    info_lines.append(f"  - {gruppe_name}: {felder_count} Felder")
                
                if len(all_data) > 10:
                    info_lines.append(f"  ... und {len(all_data) - 10} weitere Gruppen")
            else:
                info_lines.append("\n❌ Keine Daten in Systemsteuerung!")
            
            # Als Text anzeigen
            self.show_text("\n".join(info_lines))
            
            # Auch ins Log
            for line in info_lines:
                logger.info(line)
                
        except Exception as e:
            error_msg = f"❌ Fehler beim Debug der Systemsteuerung: {e}"
            logger.error(error_msg)
            self.show_text(error_msg)

    def logout(self):
        """
        🔒 SICHERER LOGOUT: Schließt die Hauptanwendung und kehrt zum Login zurück
        
        SICHERHEITSARCHITEKTUR:
        1. MainApp wird vollständig geschlossen (alle Ressourcen freigegeben)
        2. Globale Systemsteuerung wird zurückgesetzt
        3. Anwendung wird komplett beendet (clean exit)
        """
        logger.info("🔒 Logout eingeleitet - sichere Bereinigung...")
        
        try:
            # Globale Instanzen zurücksetzen (Sicherheit!)
            global _global_central_systemsteuerung
            _global_central_systemsteuerung = None
            logger.info("🧹 Globale Systemsteuerung-Instanz zurückgesetzt")
            
            # Sauberes Beenden der Anwendung
            QApplication.quit()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Logout: {e}")
            # Fallback: App beenden
            QApplication.quit()


def main():
    """
    🔒 SICHERE HAUPTFUNKTION
    
    EINFACHE SICHERE ARCHITEKTUR:
    1. QApplication wird erstellt
    2. Login wird direkt gestartet
    3. MainApp wird nur bei erfolgreichem Login erstellt
    4. Event-Loop läuft bis Anwendung beendet wird
    """
    logger.info("🚀 === PDVM SYSTEM START - SICHERE ARCHITEKTUR ===")
    
    try:
        app = QApplication(sys.argv)
        
        # 🔒 DIREKTER LOGIN-START: Ohne zusätzliche Funktion
        logger.info("🔒 Starte direkten Login-Dialog")
        
        # 🔒 LAZY IMPORT: LoginApp erst bei Bedarf laden
        from pdvm_login import LoginApp
        
        # Login-Dialog erstellen und anzeigen
        login = LoginApp(main_app_class=MainApp)
        login.show()
        
        logger.info("🔑 Login-Dialog bereit - starte Event-Loop")
        
        # Event-Loop starten - läuft bis App beendet wird
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"❌ Kritischer Anwendungsfehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
