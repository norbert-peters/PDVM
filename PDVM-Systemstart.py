# PDVM-Systemstart.py - BEREINIGT
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
from pdvm_central_stichtag_manager import PdvmCentralStichtagManager
from central_systemsteuerung import CentralSystemsteuerung

# 🔒 LAZY IMPORTS: Werden erst nach Login geladen
# from pdvm_login import LoginApp                 # ← Lazy Import
# from pdvm_command_handler import PdvmCommandHandler  # ← Lazy Import  
# from pdvm_menu_handler import PdvmMenuHandler        # ← Lazy Import
# from pdvm_menu_editor import PdvmMenuEditor          # ← Lazy Import

# GLOBALE STICHTAG-MANAGER INSTANZ für zentrale Architektur
_global_stichtag_manager = None
_global_central_systemsteuerung = None

def get_global_stichtag_manager():
    """
    🎯 GLOBALER ZUGRIFF: Zentrale StichtagManager-Instanz abrufen
    
    Wird nach erfolgreichem Login in MainApp initialisiert.
    Ermöglicht allen Komponenten (Widget, ViewManager) zentralen Stichtag-Zugriff.
    
    Returns:
        PdvmCentralStichtagManager: Die globale StichtagManager-Instanz
        
    Raises:
        RuntimeError: Falls noch nicht initialisiert
    """
    global _global_stichtag_manager
    if _global_stichtag_manager is None:
        raise RuntimeError("❌ Globaler StichtagManager noch nicht initialisiert! Login erforderlich.")
    return _global_stichtag_manager

def set_global_stichtag_manager(stichtag_manager):
    """
    🎯 GLOBALE INITIALISIERUNG: StichtagManager-Instanz setzen
    
    Wird von MainApp nach erfolgreicher Initialisierung aufgerufen.
    
    Args:
        stichtag_manager (PdvmCentralStichtagManager): Die zu setzende Instanz
    """
    global _global_stichtag_manager
    _global_stichtag_manager = stichtag_manager
    logger.info("🎯 Globaler StichtagManager gesetzt - zentrale Architektur aktiv")

def get_global_central_systemsteuerung():
    """
    🎯 GLOBALER ZUGRIFF: Zentrale Systemsteuerung-Instanz abrufen
    
    Wird nach erfolgreichem Login in MainApp initialisiert.
    Ermöglicht allen Komponenten zentralen Systemsteuerung-Zugriff.
    
    Returns:
        CentralSystemsteuerung: Die globale central_systemsteuerung-Instanz
        
    Raises:
        RuntimeError: Falls noch nicht initialisiert
    """
    global _global_central_systemsteuerung
    if _global_central_systemsteuerung is None:
        raise RuntimeError("❌ Globale Central-Systemsteuerung noch nicht initialisiert! Login erforderlich.")
    return _global_central_systemsteuerung

def set_global_central_systemsteuerung(central_systemsteuerung):
    """
    🎯 GLOBALE INITIALISIERUNG: Central-Systemsteuerung-Instanz setzen
    
    Wird von MainApp nach erfolgreicher Initialisierung aufgerufen.
    
    Args:
        central_systemsteuerung (CentralSystemsteuerung): Die zu setzende Instanz
    """
    global _global_central_systemsteuerung
    _global_central_systemsteuerung = central_systemsteuerung
    logger.info("🎯 Globale Central-Systemsteuerung gesetzt - zentrale DB-Architektur aktiv")
            

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
        
        # Prüfe StichtagManager zuerst
        if not hasattr(self, 'stichtag_manager') or not self.stichtag_manager:
            logger.error("❌ Stichtag-Manager nicht verfügbar - kann Balken nicht erstellen")
            return QLabel("❌ Stichtag-Manager nicht verfügbar")
            
        logger.info("✅ Stichtag-Manager verfügbar")
        
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
        
        # PdvmDateTimePicker mit der ZENTRALEN Instanz aus dem StichtagManager
        try:
            central_pdvm_datetime = self.stichtag_manager.get_pdvm_datetime()
            logger.info(f"✅ Zentrale PdvmDateTime-Instanz erhalten: {central_pdvm_datetime.PdvmDateTime}")
            
            # PdvmDateTimePicker - der bewährte Picker mit der zentralen Instanz!
            self.stichtag_picker = PdvmDateTimePicker(
                parent=self,
                pdvm_datetime=central_pdvm_datetime,  # ← ZENTRALE INSTANZ!
                display="all",  # Datum + Zeit
                display_time_short=False  # Mit Sekunden
            )
            
            # Kalender-Popup-Optimierung für bessere Darstellung
            if hasattr(self.stichtag_picker, '_date_edit'):
                calendar = self.stichtag_picker._date_edit.calendarWidget()
                if calendar:
                    calendar.setMinimumSize(350, 220)  # Mindestgröße für bessere Spalten-Darstellung
            
            layout.addWidget(self.stichtag_picker)
            logger.info("✅ PdvmDateTimePicker erstellt und hinzugefügt")
            
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
        Verwendet PdvmTimeStamp aus der zentralen Stichtag-Instanz.
        """
        try:
            if hasattr(self, 'stichtag_manager') and self.stichtag_manager:
                # Hole die zentrale PdvmDateTime-Instanz
                central_datetime = self.stichtag_manager.get_pdvm_datetime()
                # Verwende PdvmTimeStamp Property für die Anzeige
                timestamp_display = central_datetime.FormTimeStamp
                self.stichtag_display.setText(timestamp_display)
                logger.debug(f"🔄 Stichtag-Anzeige aktualisiert: {timestamp_display}")
            else:
                self.stichtag_display.setText("Stichtag-Manager lädt...")
                logger.warning("⚠️ Stichtag-Manager nicht verfügbar für Display-Update")
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der Stichtag-Anzeige: {e}")
            self.stichtag_display.setText("Fehler beim Laden")

    def _on_stichtag_refresh(self):
        """
        Behandelt den Refresh-Button Click.
        
        Supersimpler Ablauf mit zentraler Instanz:
        1. save() auf Picker → Änderungen landen direkt in zentraler Instanz
        2. Manager informieren zur Persistierung
        3. Anzeige aktualisieren
        4. Aktuellen Menüpunkt neu laden (zukünftig)
        """
        try:
            logger.info("🔄 Stichtag-Refresh ausgelöst")
            
            # 1. Picker-Werte in zentrale Instanz übertragen
            old_stichtag = self.stichtag_manager.get_stichtag_float()
            self.stichtag_picker.save()  # ← Ändert direkt die zentrale Instanz!
            new_stichtag = self.stichtag_manager.get_stichtag_float()
            
            # 2. Manager über Änderung informieren (für Persistierung)
            if old_stichtag != new_stichtag:
                self.stichtag_manager.set_stichtag(new_stichtag)  # Speichert in DB
                logger.info(f"✅ Stichtag erfolgreich geändert: {old_stichtag} → {new_stichtag}")
            else:
                logger.debug("ℹ️ Stichtag nicht geändert")
                
            # 3. Anzeige aktualisieren  
            self._update_stichtag_display()
            
            # 4. Aktuellen Menüpunkt neu laden (TODO: Zukünftige Erweiterung)
            self._reload_current_menu_content()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Stichtag-Refresh: {e}")
            # Bei Fehler Anzeige auf ursprünglichen Wert zurücksetzen
            self._update_stichtag_display()

    def _reload_current_menu_content(self):
        """
        Lädt den aktuellen Menüpunkt mit dem neuen Stichtag neu.
        
        🎯 ZENTRALE STICHTAG-ARCHITEKTUR: Nutzt die neue reload() Methode
        des aktuellen ViewWidgets ohne Parameter-Passing (zentrale Stichtag-Abfrage).
        """
        try:
            # Stichtag wird jetzt zentral abgerufen - kein Parameter-Passing mehr!
            logger.info(f"🎯 Reloade aktuellen Content mit zentraler Stichtag-Architektur")
            
            # Prüfe ob aktuelles ViewWidget existiert
            if hasattr(self, 'current_view_widget') and self.current_view_widget:
                logger.info("🎯 Führe zentralen Stichtag-Reload auf aktuellem ViewWidget aus...")
                
                # 🎯 NEUE ZENTRALE ARCHITEKTUR: reload() ohne Parameter!
                if hasattr(self.current_view_widget, 'reload'):
                    self.current_view_widget.reload()
                    logger.info("✅ ViewWidget erfolgreich mit zentralem Stichtag refresht")
                elif hasattr(self.current_view_widget, 'reload_with_stichtag'):
                    # Kompatibilität: Alte Methode (deprecated)
                    logger.warning("⚠️ ViewWidget verwendet noch deprecated reload_with_stichtag()")
                    new_stichtag = self.stichtag_manager.get_stichtag_float()
                    self.current_view_widget.reload_with_stichtag(new_stichtag)
                    logger.info("✅ ViewWidget mit deprecated Methode refresht")
                else:
                    # Fallback für ältere Widget-Versionen
                    logger.info("🔄 Fallback: Vollständige Widget-Neuladung...")
                    if hasattr(self.current_view_widget, 'reload_data'):
                        self.current_view_widget.reload_data()
                    elif hasattr(self.current_view_widget, 'load_data'):
                        self.current_view_widget.load_data()
                    else:
                        logger.warning("⚠️ Widget hat keine Reload-Methode")
                        
            else:
                logger.info("ℹ️ Kein aktuelles ViewWidget für Reload verfügbar")
                # Hier könnte zukünftig andere Content-Reload-Logik stehen
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Reload des aktuellen Menüpunkts: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")

    def _widget_reload_callback(self, reload_call_daten):
        """
        PARENT-CALLBACK für echten Widget-Reload:
        
        Das aktuelle Widget kann sich nicht selbst komplett neu aufbauen.
        Diese Callback-Methode wird vom Widget aufgerufen und:
        1. Entfernt das alte Widget aus dem Layout
        2. Erstellt ein komplett neues Widget mit reload_call_daten
        3. Fügt das neue Widget in das Layout ein
        
        Args:
            reload_call_daten (dict): Call-Daten für Widget-Initialisierung (mit first_call=False)
        """
        logger.info("🔄 === PARENT-CALLBACK: Widget-Neuinitialisierung ===")
        
        try:
            # SCHRITT 1: Altes Widget entfernen
            if hasattr(self, 'current_view_widget') and self.current_view_widget:
                logger.info("🗑️ Entferne altes Widget aus Layout...")
                self.content_layout.removeWidget(self.current_view_widget)
                self.current_view_widget.deleteLater()  # Qt-korrekte Entfernung
                self.current_view_widget = None
                logger.info("✅ Altes Widget entfernt")
            
            # SCHRITT 2: Neues Widget erstellen
            logger.info("🔧 Erstelle neues Widget mit reload_call_daten...")
            from pdvm_view_widget import PdvmViewWidget
            
            new_widget = PdvmViewWidget(
                call_daten=reload_call_daten,
                parent=self,
                reload_callback=self._widget_reload_callback  # Callback für nächste Reloads
            )
            
            # SCHRITT 3: Neues Widget in Layout einbinden
            logger.info("📦 Binde neues Widget in Layout ein...")
            self.content_layout.addWidget(new_widget, 1)
            self.current_view_widget = new_widget
            
            # SCHRITT 4: UI-Updates
            self.content_frame.updateGeometry()
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()
            
            logger.info("✅ Parent-Callback: Widget-Neuinitialisierung erfolgreich abgeschlossen")
            
        except Exception as e:
            logger.error(f"❌ Parent-Callback: Widget-Reload fehlgeschlagen: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")

    def _refresh_stichtag_bar_after_init(self):
        """
        Aktualisiert den Stichtag-Balken nach vollständiger Initialisierung des Stichtag-Managers.
        Da wir die zentrale Instanz verwenden, ist normalerweise kein Update nötig.
        """
        try:
            if (hasattr(self, 'stichtag_manager') and hasattr(self, 'stichtag_picker')):
                logger.info("🔄 Aktualisiere Stichtag-Balken nach Initialisierung")
                
                # Picker sollte bereits die zentrale Instanz verwenden,
                # aber wir können das Display trotzdem aktualisieren
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
        
        NEUE ARCHITEKTUR (Post-Login):
        - CentralSystemsteuerung wird bereits im Login initialisiert
        - MainApp verwendet die bereits vorhandene globale Instanz
        - Nur StichtagManager wird hier neu erstellt (benötigt MainApp-Kontext)
        """
        try:
            # 🎯 GLOBALE SYSTEMSTEUERUNG BEREITS VERFÜGBAR: Vom Login initialisiert
            try:
                self.central_systemsteuerung = get_global_central_systemsteuerung()
                logger.info("✅ CentralSystemsteuerung bereits verfügbar - verwende globale Instanz")
            except RuntimeError:
                logger.warning("⚠️ Fallback: Erstelle CentralSystemsteuerung in MainApp (sollte nicht passieren)")
                # Fallback für den unwahrscheinlichen Fall, dass Login-Initialisierung fehlschlug
                self.central_systemsteuerung = CentralSystemsteuerung(
                    user_guid=self.user_guid,
                    db_name="PdvmManager.db"
                )
                set_global_central_systemsteuerung(self.central_systemsteuerung)
            
            # ZENTRALER STICHTAG-MANAGER initialisieren (benötigt MainApp-Kontext)
            self.stichtag_manager = PdvmCentralStichtagManager(
                central_systemsteuerung=self.central_systemsteuerung._db,  # DB-Layer für Manager
                user_guid=self.user_guid,
                initial_stichtag="2025216"
            )
            
            # 🎯 GLOBALE VERFÜGBARKEIT: StichtagManager setzen
            set_global_stichtag_manager(self.stichtag_manager)
            logger.info("🎯 Globaler StichtagManager initialisiert - zentrale Architektur vollständig")
            
            # Kompatibilität: self.stichtag für Legacy-Code bereitstellen
            self.stichtag = self.stichtag_manager.get_stichtag_string()
            
            # Signal-Verbindung für Stichtag-Updates
            self.stichtag_manager.stichtag_changed.connect(self._on_stichtag_changed)
            
            # Sprache laden - jetzt über elegante Property
            self.language = self.central_systemsteuerung.language
            
            logger.info(f"🎛️ Zentrale Architektur bereit: Stichtag={self.stichtag_manager.get_formatted_stichtag()}, Sprache={self.language}")
            logger.info(f"🗓️ Zentraler Stichtag-Manager aktiv - einheitliche Stichtag-Verwaltung")
            logger.info(f"🎯 ExpertMode verfügbar über: central_systemsteuerung.global_expert_mode")
            
            # Stichtag-Balken nach vollständiger Initialisierung aktualisieren
            self._refresh_stichtag_bar_after_init()
            
        except Exception as e:
            logger.error(f"❌ Fehler bei der Initialisierung der zentralen Systemsteuerung: {e}")
            # Fallback-Werte
            self.central_systemsteuerung = None
            self.stichtag_manager = None
            self.stichtag = "2025216"
            self.language = "DE"

    def _on_stichtag_changed(self, new_stichtag_float):
        """Callback für Stichtag-Änderungen - aktualisiert Legacy-Kompatibilität"""
        self.stichtag = str(int(new_stichtag_float))
        logger.info(f"🔄 Legacy-Stichtag aktualisiert: {self.stichtag}")

    def get_stichtag_manager(self):
        """
        Gibt den zentralen Stichtag-Manager zurück
        
        Returns:
            PdvmCentralStichtagManager: Der zentrale Stichtag-Manager
        """
        if hasattr(self, 'stichtag_manager') and self.stichtag_manager:
            return self.stichtag_manager
        else:
            logger.warning("⚠️ Stichtag-Manager nicht verfügbar")
            return None

    def _refresh_stichtag_bar_after_init(self):
        """Aktualisiert die Stichtag-Balken nach der vollständigen Initialisierung"""
        if hasattr(self, 'stichtag_bar') and self.stichtag_bar:
            self._update_stichtag_display()

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

    def open_app_menu(self, application_name):
        """
        DEPRECATED: Kompatibilitätsmethode für alte Menü-Referenzen
        Leitet zu pdvm_start weiter
        """
        logger.warning(f"⚠️ open_app_menu() ist deprecated, verwende pdvm_start('{application_name}')")
        self.pdvm_start(application_name)

    def pdvm_modern_view(self, frame_guid):
        """
        Zentrale PDVM View - der einzige View mit dem weiter gearbeitet wird
        
        Einfacher Aufruf mit frame_guid
        Erstellt call_daten und startet Widget
        """
        if not frame_guid:
            logger.error("❌ Es wurde keine frame_guid übergeben!")
            self.clear_content_layout()
            self._show_label("❌ Es wurde keine frame_guid übergeben!", small=False, clear_content=False)
            return

        self.clear_content_layout()
        
        try:
            logger.info(f"🎯 PDVM Modern View gestartet für Frame: {frame_guid}")
            
            # PRÜFUNG: StichtagManager muss verfügbar sein
            if not hasattr(self, 'stichtag_manager') or not self.stichtag_manager:
                logger.error("❌ StichtagManager nicht verfügbar - Login erforderlich")
                self._show_label("❌ Bitte zuerst einloggen!", small=False, clear_content=False)
                return
            
            # Frame-Daten laden
            framedaten_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="framedaten", 
                guid=frame_guid
            )
            # View-GUID aus Frame-Daten
            view_guid = framedaten_db.get_static_value("ROOT", "VIEW_GUID")
            if not view_guid:
                logger.error(f"❌ Keine view_guid in Frame-Daten gefunden")
                return
            
            # BEREINIGT: call_daten ohne 'stichtag' - Widget holt zentral
            call_daten = {
                "view_guid": view_guid,
                "user_guid": self.user_guid,
                # BEREINIGT: 'stichtag' entfernt - schädlich für zentrale Architektur
                "view_header": "Übersicht Personaldaten",
                "first_call": True,
                "mode": "admin"  # Admin-Modus für Expert-Mode Zugang
            }
            
            logger.info(f"📋 call_daten: {call_daten}")
            
            # PDVM View Widget erstellen
            from pdvm_view_widget import PdvmViewWidget
            
            view_widget = PdvmViewWidget(
                call_daten=call_daten,
                parent=self,
                reload_callback=self._widget_reload_callback  # Parent-Callback für echten Reload
            )
            
            # Widget in Layout einbinden
            self.content_layout.addWidget(view_widget, 1)
            
            # Widget persistent halten
            self.current_view_widget = view_widget
            
            # Layout-Updates
            self.content_frame.updateGeometry()
            QApplication.processEvents()
            
            logger.info(f"✅ PDVM Modern View erfolgreich geladen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des PDVM Modern View: {e}")
            import traceback
            logger.error(traceback.format_exc())

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
            if not self.central_systemsteuerung:
                logger.warning("⚠️ Zentrale Systemsteuerung nicht verfügbar - Menü-Status wird nicht gespeichert")
                return
            
            current_menu_id = self._get_current_menu_id()
            menu_visible = getattr(self, '_menu_visible', True)
            
            # MenuStatus unter user_guid-Gruppe speichern
            self.central_systemsteuerung.set_value(
                gruppe=self.user_guid,  # user_guid ist die Gruppe
                feld=f"menu_{current_menu_id}",  # Feld: menu_<menu_id>
                wert=menu_visible,
                ab_zeit=1001.0  # Standard-Zeitstempel für nicht-historische Felder
            )
            
            # Änderungen persistieren
            self.central_systemsteuerung.save_values()
            
            logger.debug(f"💾 Menü-Status in zentrale Systemsteuerung gespeichert: Gruppe={self.user_guid}, Feld=menu_{current_menu_id}, Wert={menu_visible}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern des Menü-Status: {e}")

    def _restore_menu_visibility_status(self, menu_id):
        """Stellt den gespeicherten Menü-Sichtbarkeits-Status aus der systemsteuerung-Tabelle wieder her."""
        try:
            # Startmenü: Immer sichtbar
            if menu_id == self.startmenu_id:
                self._ensure_menu_visible()
                return
            
            if not self.central_systemsteuerung:
                logger.warning("⚠️ Zentrale Systemsteuerung nicht verfügbar - Menü wird eingeblendet")
                self._ensure_menu_visible()
                return
            
            # MenuStatus aus user_guid-Gruppe laden
            menu_value = self.central_systemsteuerung.get_value(
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
            global _global_stichtag_manager, _global_central_systemsteuerung
            _global_stichtag_manager = None
            _global_central_systemsteuerung = None
            logger.info("🧹 Globale Systemsteuerung-Instanzen zurückgesetzt")
            
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
