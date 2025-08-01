# PDVM-Systemstart.py
import sys, io, os, logging

# Erzwinge UTF-8 für alle IO
os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Umstellung auf UTF-8 für die Console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

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

from pdvm_login import LoginApp
from pdvm_menu_editor import PdvmMenuEditor
from pdvm_view_manager import PdvmViewManager
from pdvm_search_list_widget import PdvmSearchListWidget
from pdvm_dialog_widget import PdvmDialogWidget
# from pdvm_unified_dialog_widget import UnifiedPdvmDialogWidget  # V2 auskommentiert
import json
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QApplication, QDialog
)
from PyQt5.QtCore import Qt, QTimer

from pdvm_command_handler import PdvmCommandHandler
from pdvm_menu_handler import PdvmMenuHandler

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
        self.user_name = f"{self.user_daten.get("Benutzer").get("Vorname")} {self.user_daten.get
                                                                             ("Benutzer").get("Name")}"
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

        # Handler initialisieren
        self.command_handler = PdvmCommandHandler(self)
        
        # Startmenü laden (DRY-Prinzip: Eine zentrale Methode für Startmenü)
        self.open_start_menu()

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
        self._show_label(f"{text}", small=False, 
                        clear_content=True)
#        self._show_label(text)

    def show_text_klein(self, text):
        """Kleine Meldung unten anhängen."""
        # Hänge neuen Text an
        current = []
        self.clear_content_layout()
#        for i in range(self.content_layout.count()):
#            w = self.content_layout.itemAt(i).widget()
#            if isinstance(w, QLabel):
#                current.append(w.text())
#        combined = "\n".join(current + [text])
#        self._show_label(combined, small=True)

    def clear_content_layout(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout():
                # Falls ein verschachteltes Layout, rekursiv löschen
                self._clear_layout(item.layout())
            # Spacer/Stretches werden durch takeAt automatisch entfernt

    def open_menu_editor(self, menu_type, call_path=None):
        """Zeigt den Menüeditor im Inhaltsbereich an."""
        logger.debug(f"🔹 Öffne Menüeditor für Typ: {menu_type} - Pfad: {call_path}")
        logger.info(f"🔹 Benutzer {self.user_name} öffnet Menüeditor für {menu_type} - content_layout: {self.content_layout}")
        # Inhalt löschen
        self.clear_content_layout()
#        for i in reversed(range(self.content_layout.count())):
#            w = self.content_layout.itemAt(i).widget()
#            if w:
#                w.setParent(None)
        # Editor instanziieren und anzeigen
        editor = PdvmMenuEditor(self.content_frame, self.menu_handler.menu, menu_type, self, call_path)
        self.content_layout.addWidget(editor)

    def open_app_menu(self, user_app):
        """
        Wechselt in die Menüstruktur einer anderen Anwendung.
        DEPRECATED: Wird durch pdvm_start() ersetzt - hier als Fallback für Kompatibilität
        """
        logger.warning(f"⚠️ open_app_menu() ist deprecated, verwende stattdessen pdvm_start('{user_app}')")
        
        # Fallback zur neuen Methode
        self.pdvm_start(user_app)

    def open_start_menu(self):
        """Lädt erneut das Startmenü."""
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
        self._show_label("🔹 Willkommen im PDVM-System!", small=False, 
                        clear_content=True)
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

    def pdvm_modern_view(self, frame_guid):
        """
        Zeigt die moderne View-Tabelle für die angegebene frame_guid.
        frame_guid MUSS übergeben werden. Kein Default, kein Test-Frame.
        """
        if not frame_guid:
            logger.error("❌ Es wurde keine frame_guid übergeben!")
            self.clear_content_layout()
            self._show_label("❌ Es wurde keine frame_guid übergeben!", small=False, clear_content=False)
            return

        self.clear_content_layout()
#        try:
        from pdvm_central_datenbank import PdvmCentralDatenbank
        framedaten_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="framedaten",
            guid=frame_guid
        )
        frame_data = framedaten_db.lesen()
        if not frame_data or not isinstance(frame_data, dict):
            logger.error(f"❌ Keine framedaten gefunden für GUID: {frame_guid}")
            raise ValueError(f"Keine framedaten gefunden für GUID: {frame_guid}")
        root_config = frame_data.get("ROOT", {})
        view_guid = root_config.get("view_guid")
        if not view_guid:
            logger.error(f"❌ Keine view_guid in ROOT gefunden für Frame: {frame_guid}")
            raise ValueError(f"Keine view_guid in ROOT gefunden für Frame: {frame_guid}")
        from pdvm_modern_view_widget import PdvmModernViewWidget
        self.modern_view_widget = PdvmModernViewWidget(
            view_guid=view_guid,
            user_guid=self.user_guid,
            parent=self
        )
        self.content_layout.addWidget(self.modern_view_widget, 1)
        # Test-Label nach dem Widget, um Layout-Fehler zu erkennen
        test_label = QLabel("[DEBUG] ModernViewWidget wurde dem Layout hinzugefügt")
        test_label.setStyleSheet("color: green; font-size: 12px; padding: 4px;")
        self.content_layout.addWidget(test_label)
        self.content_frame.updateGeometry()
        self.modern_view_widget.updateGeometry()
        QApplication.processEvents()
        self.current_dialog_widget = self.modern_view_widget
        logger.info(f"🔹 Modernes View-Widget geladen für Frame: {frame_guid}")
#        except Exception as e:
#            logger.error(f"❌ Fehler beim Laden des Modern View-Widgets: {e}")
#            # Inhaltsbereich immer leeren, damit UI sichtbar bleibt
#            self.clear_content_layout()
#            # Fehler-Label immer anzeigen, auch wenn QLabel-Import fehlschlägt
#            try:
#                from PyQt5.QtWidgets import QLabel
#                error_label = QLabel(f"❌ Fehler beim Laden der modernen View:\n{str(e)}")
#                error_label.setStyleSheet("color: red; font-size: 14px; padding: 20px;")
#                self.content_layout.addWidget(error_label)
#            except Exception as import_error:
#                logger.error(f"❌ Fehler beim Anzeigen des Fehler-Dialogs: {import_error}")
#                # Fallback: Zeige Fehlertext als Label über _show_label
#                self._show_label(f"❌ Fehler beim Laden der modernen View:\n{str(e)}\n(Fehler beim Anzeigen des Fehler-Dialogs)", small=False, clear_content=False)





    def pdvm_dialog_with_view(self, frame_guid=None):
        """
        Dialog mit integriertem modernen View-Widget
        Lädt automatisch die view_guid aus den framedaten
        """
        if not frame_guid:
            frame_guid = "4078079f-4028-45ed-879c-3c779ecf3d0d"  # Default Test-Frame
        
        # Inhalt löschen
        self.clear_content_layout()

        try:
            from pdvm_dialog_view_integration import PdvmDialogViewWidget
            
            # Dialog-View-Widget erstellen
            self.dialog_view_widget = PdvmDialogViewWidget(
                frame_guid=frame_guid,
                user_guid=self.user_guid,
                parent=self
            )
            
            # Signal-Verbindungen
            self.dialog_view_widget.rowSelected.connect(self._on_dialog_view_row_selected)
            self.dialog_view_widget.editRequested.connect(self._on_dialog_view_edit_requested)
            self.dialog_view_widget.newRequested.connect(self._on_dialog_view_new_requested)
            
            # Widget einbetten
            self.content_layout.addWidget(self.dialog_view_widget, 1)
            
            # Layout-Updates
            self.content_frame.updateGeometry()
            self.dialog_view_widget.updateGeometry()
            QApplication.processEvents()
            
            # Widget persistent halten
            self.current_dialog_widget = self.dialog_view_widget
            
            logger.info(f"🔗 Dialog mit integriertem View-Widget geladen für Frame: {frame_guid}")
            logger.info("✅ Funktionen: View + Dialog-Integration mit Neu/Bearbeiten")
            logger.info("🎯 View-GUID wird automatisch aus framedaten geladen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Dialog-View-Widgets: {e}")
            # Fehler-Widget anzeigen
            from PyQt5.QtWidgets import QLabel
            error_label = QLabel(f"❌ Fehler beim Laden der Dialog-View:\n{str(e)}")
            error_label.setStyleSheet("color: red; font-size: 14px; padding: 20px;")
            self.content_layout.addWidget(error_label)

    def _on_dialog_view_row_selected(self, record):
        """Callback wenn eine Zeile in der Dialog-View ausgewählt wird"""
        logger.info(f"🔘 Datensatz in Dialog-View ausgewählt: {record.get('_guid', 'Unbekannt')}")
        
        # Debug-Info in Status-Bereich anzeigen (wenn gewünscht)
        if 'FAMILIENNAME' in record and 'VORNAME' in record:
            name = f"{record['FAMILIENNAME']}, {record['VORNAME']}"
            logger.info(f"   Person: {name}")

    def _on_dialog_view_edit_requested(self, record):
        """Callback wenn Bearbeitung eines Datensatzes angefordert wird"""
        logger.info(f"✏️ Bearbeitung angefordert für: {record.get('_guid', 'Unbekannt')}")
        
        # TODO: Hier würde der Input-Dialog geöffnet werden
        # Für jetzt nur eine Meldung
        if 'FAMILIENNAME' in record and 'VORNAME' in record:
            name = f"{record['FAMILIENNAME']}, {record['VORNAME']}"
            self.show_text(f"✏️ Bearbeitung angefordert für:\n{name}\nGUID: {record.get('_guid', 'Unbekannt')}\n\n(Input-Dialog würde hier öffnen)")

    def _on_dialog_view_new_requested(self):
        """Callback wenn ein neuer Datensatz erstellt werden soll"""
        logger.info("➕ Neuer Datensatz angefordert")
        
        # TODO: Hier würde der Input-Dialog für neuen Datensatz geöffnet werden
        self.show_text("➕ Neuer Datensatz angefordert\n\n(Input-Dialog würde hier öffnen)")

    def pdvm_dialog(self, frame_guid, mode):
        """
        Lädt das Dialog-Widget - automatisch Enhanced Multi-Tab wenn in framedaten aktiviert.
        frame_guid: GUID aus framedaten-Tabelle
        mode: Modus für zukünftige Verwendung (wird in moderne Struktur integriert)
        """
        call_daten = {
            "app": self,  # Wichtig: Referenz zur Hauptanwendung
            "user_guid": self.user_guid,
            "frame_guid": frame_guid,
            "language": "de",
            "stichtag": "2025185"
        }

        # Vorherigen Inhalt im Arbeitsbereich (content_layout) KOMPLETT löschen
        self.clear_content_layout()

        logger.info(f"🔧 pdvm_dialog aufgerufen - frame_guid: {frame_guid}, mode: {mode}")

        # Prüfe Frame-Konfiguration für Multi-Tab-Support
        multi_tab_enabled = self._check_multi_tab_enabled(frame_guid)
        
        if multi_tab_enabled:
            logger.info("� Multi-Tab in framedaten aktiviert - lade Enhanced Widget...")
            self._load_enhanced_dialog_widget(call_daten)
        else:
            logger.info("📄 Standard-Dialog - lade UnifiedPdvmDialogWidget V3...")
            self._load_standard_dialog_widget(call_daten)

    def _load_standard_dialog_widget(self, call_daten):
        """Lädt das Standard UnifiedPdvmDialogWidget V3"""
        try:
            # Setup für moderne framedaten-Struktur
            try:
                from create_modern_framedaten_structure import create_modern_framedaten_database
                logger.info("🔧 Erstelle moderne framedaten-Struktur für Standard-Dialog...")
                create_modern_framedaten_database()
            except Exception as e:
                logger.warning(f"⚠️ Moderne Struktur-Skript: {e}")

            # Standard UnifiedPdvmDialogWidget V3 laden
            from pdvm_unified_dialog_widget_v3 import UnifiedPdvmDialogWidget
            from pdvm_modern_dialog_loader import enhance_unified_widget
            
            # Widget erstellen
            self.dialog_widget = UnifiedPdvmDialogWidget(call_daten)
            
            # Moderne Datenstruktur laden und anwenden
            logger.info("🔧 Lade moderne framedaten-Struktur...")
            enhance_unified_widget(self.dialog_widget)
            
            # Widget in den Arbeitsbereich einbetten
            self.content_layout.addWidget(self.dialog_widget, 1)
            
            # Layout-Updates
            self.content_frame.updateGeometry()
            self.dialog_widget.updateGeometry()
            QApplication.processEvents()
            
            # Widget persistent halten
            self.current_dialog_widget = self.dialog_widget
            
            logger.info("🎨 Standard UnifiedPdvmDialogWidget V3 erfolgreich geladen!")
            logger.info("✅ Moderne Tab-basierte Dialog-Architektur mit echten Daten verfügbar")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Standard Dialog-Widgets: {e}")
            # Fehler-Widget anzeigen
            from PyQt5.QtWidgets import QLabel
            error_label = QLabel(f"❌ Fehler beim Laden des Dialog-Widgets: {str(e)}")
            error_label.setStyleSheet("color: red; font-size: 14px; padding: 20px;")
            self.content_layout.addWidget(error_label)

    def get_current_unified_widget(self):
        """
        Holt das aktuell aktive Unified Widget.
        
        Returns:
            UnifiedPdvmDialogWidget oder None
        """
        if hasattr(self, 'current_dialog_widget') and self.current_dialog_widget:
            return self.current_dialog_widget
        return None

    
    def get_current_unified_widget(self):
        """Gibt das aktuelle Unified Widget zurück (für Menü-Integration)"""
        if hasattr(self, 'current_dialog_widget') and self.current_dialog_widget:
            return self.current_dialog_widget
        elif hasattr(self, 'unified_widget') and self.unified_widget:
            return self.unified_widget
        else:
            logger.warning("⚠️ Kein Unified Dialog Widget aktiv")
            return None

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
            from pdvm_central_datenbank import PdvmCentralDatenbank
            
            current_menu_id = self._get_current_menu_id()
            menu_visible = getattr(self, '_menu_visible', True)
            
            # Systemsteuerung-Datenbank für Benutzer öffnen
            sys_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="systemsteuerung",
                guid=self.user_guid
            )
            
            # Aktuelle Daten laden
            raw_data = sys_db.lesen() or {}
            user_data = raw_data.get(self.user_guid, {})
            
            # MenuStatus-Struktur initialisieren falls nicht vorhanden
            if "MenuStatus" not in user_data:
                user_data["MenuStatus"] = {}
            
            # Aktuellen Menüstatus speichern (unter Menü-UID)
            user_data["MenuStatus"][current_menu_id] = menu_visible
            
            # Zurück in Datenbank speichern
            raw_data[self.user_guid] = user_data
            sys_db.speichern(self.user_guid, raw_data)
            
            logger.debug(f"💾 Menü-Status in systemsteuerung gespeichert für Menü {current_menu_id}: {menu_visible}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern des Menü-Status: {e}")

    def _restore_menu_visibility_status(self, menu_id):
        """Stellt den gespeicherten Menü-Sichtbarkeits-Status aus der systemsteuerung-Tabelle wieder her."""
        try:
            # Startmenü: Immer sichtbar
            if menu_id == self.startmenu_id:
                self._ensure_menu_visible()
                return
            
            from pdvm_central_datenbank import PdvmCentralDatenbank
            
            # Systemsteuerung-Datenbank für Benutzer öffnen
            sys_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="systemsteuerung",
                guid=self.user_guid
            )
            
            # Gespeicherten Status laden
            raw_data = sys_db.lesen() or {}
            user_data = raw_data.get(self.user_guid, {})
            menu_status = user_data.get("MenuStatus", {})
            saved_visibility = menu_status.get(menu_id, True)  # Default: sichtbar
            
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

    def logout(self):
        """Logout: schließt App und zeigt Login erneut."""
        login = LoginApp(main_app_class=MainApp)
        login.show()
        self.close()


def main():
    app = QApplication(sys.argv)
    # Wir übergeben MainApp als Klassereferenz in den Login:
    login = LoginApp(main_app_class=MainApp)
    login.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()