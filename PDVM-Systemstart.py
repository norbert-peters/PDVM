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
from PyQt5.QtCore import Qt

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

        self.startmenu_id = self.user_daten.get("Anwendungen", {}).get("MeineApps")
        logging.log(logging.INFO, f"🔹 Starte mit Startmenu-ID: {self.startmenu_id}")

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

        # Platzhalterbegrüßung
        self._show_label("🔹 Willkommen im PDVM-System!", small=False, 
                        clear_content=True)
        # Platzhalter für Anwendungsanleitung - ggf. mehrere Zeilen
        self._show_label(["🔹 Bitte wählen Sie eine Anwendung aus dem Menü links."], 
                 small=True, clear_content=False)        

        # Handler initialisieren
        self.command_handler = PdvmCommandHandler(self)
        self.menu_handler = PdvmMenuHandler(
            root=self,
            menu_widget=self.menu_frame,
            menu_id=self.startmenu_id,
            command_handler=self.command_handler
        )
        self.menu_handler.create_menus()

    def _show_label(self, texts, small=False, clear_content=True):
        """
        Zeigt eine oder mehrere Zeilen Text im Inhaltsbereich an.
        texts: Liste von Strings (oder ein einzelner String)
        """
        if clear_content:
            self.clear_content_layout()
        # Abstand oben
        self.content_layout.addStretch(1)
        # Labels
        if isinstance(texts, str):
            texts = [texts]
        for text in texts:
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignCenter)
            if small:
                lbl.setStyleSheet("font-size: 12px;")
            else:
                lbl.setStyleSheet("font-size: 16px;")
            self.content_layout.addWidget(lbl)
        # Abstand unten
        if clear_content:
            self.content_layout.addStretch(1)
        else:
            # Wenn nicht geleert, dann nur unten Abstand
            self.content_layout.addStretch(25)

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
        """Wechselt in die Menüstruktur einer anderen Anwendung."""
        app_menu_id = self.user_daten.get("Anwendungen", {}).get(user_app, {}).get("Menu")
        self.menu_handler = PdvmMenuHandler(
            root=self,
            menu_widget=self.menu_frame,
            menu_id=app_menu_id,
            command_handler=self.command_handler
        )
        self.menu_handler.create_menus()
        self.setWindowTitle(f"PDVM {user_app} - {self.user_name}")
        self.show_text(f"🔹 Willkommen in {user_app}!")

    def open_start_menu(self):
        """Lädt erneut das Startmenü."""
        self.menu_handler = PdvmMenuHandler(
            root=self,
            menu_widget=self.menu_frame,
            menu_id=self.startmenu_id,
            command_handler=self.command_handler
        )
        self.menu_handler.create_menus()
        self.setWindowTitle(f"PDVM System - Hauptanwendung - {self.user_name}")
        self.show_text("🔹 Willkommen in der App Auswahl!")

    def pdvm_search(self, view_guid, frame_guid, mode):
        """
        Lädt zunächst die View, dann das Input-Frame im content_area.
        view_guid: GUID aus viewdaten-Tabelle
        frame_guid: GUID aus framedaten-Tabelle
        mode: Modus (aktuell ungenutzt)
        """
        call_daten = {
            "user_guid": self.user_guid,
            "view_guid": view_guid,
            "frame_guid": frame_guid,
            "mode": mode,
        }

        # Vorherigen Inhalt im Arbeitsbereich (content_layout) löschen
        for i in reversed(range(self.content_layout.count())):
            w = self.content_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        # 1) View laden
        self.view_manager = PdvmViewManager(call_daten=call_daten)
        table_name = self.view_manager.view_table
        # 2) Erzeuge dein SearchListWidget für eine Tabelle, z.B. 'persondaten'
        search_widget = PdvmSearchListWidget(self.view_manager, table_name=table_name)
        self.content_layout.addWidget(search_widget)

    def pdvm_test(self):
        # Beispielhafte Call-Daten
        call_daten = {
            "user_guid":  "4886ad26-061b-4662-a762-c8c83f36692d",
            "frame_guid": "4078079f-4028-45ed-879c-3c779ecf3d0d",
            "mode":        0,
        }

        # Vorherigen Inhalt im Arbeitsbereich (content_layout) löschen
        for i in reversed(range(self.content_layout.count())):
            w = self.content_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        # Widget erzeugen und anzeigen
        widget = PdvmDialogWidget(call_daten, parent=self.content_frame)
        self.content_layout.addWidget(widget)

    def pdvm_dialog(self, frame_guid, mode):
        """
        Lädt das UnifiedPdvmDialogWidget V3 mit den übergebenen Parametern.
        frame_guid: GUID aus framedaten-Tabelle
        mode: Modus für zukünftige Verwendung
        """
        call_daten = {
            "app": self,  # Wichtig: Referenz zur Hauptanwendung
            "user_guid": self.user_guid,
            "frame_guid": frame_guid,
            "language": "de",
            "stichtag": "2025185",
            "mode": mode  # Für zukünftige Verwendung
        }

        # Vorherigen Inhalt im Arbeitsbereich (content_layout) KOMPLETT löschen
        self.clear_content_layout()

        # DEBUG: Layout-Status
        logger.info(f"🔧 DEBUG pdvm_dialog aufgerufen - frame_guid: {frame_guid}, mode: {mode}")
        logger.info(f"🔧 DEBUG Layout-Elemente nach clear_content_layout(): {self.content_layout.count()}")

        # UnifiedPdvmDialogWidget erstellen und in content_layout einbetten
        try:
            from pdvm_unified_dialog_widget_v3 import UnifiedPdvmDialogWidget
            
            # Widget erstellen
            self.unified_widget = UnifiedPdvmDialogWidget(call_daten)
            
            # DEBUG: Content-Layout Info vor Widget-Einbettung
            logger.info(f"🔧 DEBUG Content-Frame Größe: {self.content_frame.size().width()}x{self.content_frame.size().height()}")
            
            # Widget in den Arbeitsbereich einbetten (nicht als separates Fenster!)
            # KRITISCH: Widget mit stretch=1 für volle Raumnutzung einbetten
            self.content_layout.addWidget(self.unified_widget, 1)
            
            # KRITISCH: Force-Update der Layout-Größen
            self.content_frame.updateGeometry()
            self.unified_widget.updateGeometry()
            QApplication.processEvents()
            
            # DEBUG: Final Widget-Größe
            logger.info(f"🔧 DEBUG Widget finale Größe: {self.unified_widget.size().width()}x{self.unified_widget.size().height()}")
            
            # WICHTIG: Dialog-Widget persistent halten für Menü-Integration
            self.current_dialog_widget = self.unified_widget
            
            # Status-Update
            logger.info(f"🎨 UnifiedPdvmDialogWidget V3 geladen - Frame: {frame_guid}, Mode: {mode}")
            logger.info("✅ UnifiedPdvmDialogWidget V3 erfolgreich in Arbeitsbereich integriert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des UnifiedPdvmDialogWidget: {e}")
            # Fehler-Widget anzeigen
            from PyQt5.QtWidgets import QLabel
            error_label = QLabel(f"❌ Fehler beim Laden: {str(e)}")
            error_label.setStyleSheet("color: red; font-size: 14px; padding: 20px;")
            self.content_layout.addWidget(error_label)

    def dialog_zusatz(self, command: str, **kwargs) -> bool:
        """
        Flexible Dialog-Zusatz-Funktionen.
        
        Unterstützt sowohl direkte Kommandos als auch parameterisierte Aufrufe:
        - dialog_zusatz('Input-Lupe')
        - dialog_zusatz('Lupe', mode='input')
        
        Args:
            command: Kommando-String oder Basis-Kommando
            **kwargs: Zusätzliche Parameter
            
        Returns:
            bool: True wenn erfolgreich
        """
        try:
            # Dialog-Zusatz-Handler laden (lazy loading)
            if not hasattr(self, '_dialog_zusatz_handler'):
                from pdvm_dialog_zusatz import PdvmDialogZusatz
                self._dialog_zusatz_handler = PdvmDialogZusatz(self)
            
            # Kommando ausführen
            result = self._dialog_zusatz_handler.dialog_zusatz(command, **kwargs)
            
            # Logging
            if result:
                logger.info(f"Dialog-Zusatz-Kommando erfolgreich: {command}")
            else:
                logger.warning(f"Dialog-Zusatz-Kommando fehlgeschlagen: {command}")
            
            return result
            
        except Exception as e:
            logger.error(f"Fehler bei Dialog-Zusatz-Kommando '{command}': {e}")
            return False

    def get_current_unified_widget(self):
        """
        Holt das aktuell aktive Unified Widget.
        
        Returns:
            UnifiedPdvmDialogWidget oder None
        """
        if hasattr(self, 'current_dialog_widget') and self.current_dialog_widget:
            return self.current_dialog_widget
        return None

    def pdvm_unified_test(self):
        """Test für das neue UnifiedPdvmDialogWidget mit schaltbarer View und Input-Tabs"""
        # Beispielhafte Call-Daten (ohne Mode!)
        call_daten = {
            "app": self,  # Wichtig: Referenz zur Hauptanwendung
            "user_guid":  self.user_guid,
            "frame_guid": "4078079f-4028-45ed-879c-3c779ecf3d0d",
            "language":   "de",
            "stichtag": "2025185"
        }

        # Vorherigen Inhalt im Arbeitsbereich (content_layout) KOMPLETT löschen
        self.clear_content_layout()  # Das entfernt ALLE Layout-Elemente inklusive Stretches!

        # DEBUG: Prüfe was noch im Layout ist
        logger.info(f"🔧 DEBUG Layout-Elemente nach clear_content_layout(): {self.content_layout.count()}")
        for i in range(self.content_layout.count()):
            item = self.content_layout.itemAt(i)
            if item.widget():
                logger.info(f"🔧 DEBUG Layout[{i}]: Widget {type(item.widget()).__name__}")
            elif item.spacerItem():
                logger.info(f"🔧 DEBUG Layout[{i}]: Spacer/Stretch-Element!")
            else:
                logger.info(f"🔧 DEBUG Layout[{i}]: {type(item).__name__}")

        # UnifiedPdvmDialogWidget erstellen und in content_layout einbetten
        try:
            from pdvm_unified_dialog_widget_v3 import UnifiedPdvmDialogWidget
            
            # Widget erstellen
            self.unified_widget = UnifiedPdvmDialogWidget(call_daten)
            
            # DEBUG: Content-Layout Info vor Widget-Einbettung
            logger.info(f"🔧 DEBUG Content-Frame Größe: {self.content_frame.size().width()}x{self.content_frame.size().height()}")
            logger.info(f"🔧 DEBUG Content-Layout Count vor Einbettung: {self.content_layout.count()}")
            
            # Widget in den Arbeitsbereich einbetten (nicht als separates Fenster!)
            # KRITISCH: Widget mit stretch=1 für volle Raumnutzung einbetten
            self.content_layout.addWidget(self.unified_widget, 1)
            
            # DEBUG: Layout Info nach Widget-Einbettung
            logger.info(f"🔧 DEBUG Content-Layout Count nach Einbettung: {self.content_layout.count()}")
            logger.info(f"🔧 DEBUG Widget in Layout Position: {self.content_layout.indexOf(self.unified_widget)}")
            
            # KRITISCH: Force-Update der Layout-Größen
            self.content_frame.updateGeometry()
            self.unified_widget.updateGeometry()
            QApplication.processEvents()
            
            # DEBUG: Final Widget-Größe
            logger.info(f"🔧 DEBUG Widget finale Größe: {self.unified_widget.size().width()}x{self.unified_widget.size().height()}")
            
            # WICHTIG: Dialog-Widget persistent halten für Menü-Integration
            self.current_dialog_widget = self.unified_widget
            
            # Status-Update (ersetzt update_status)
            logger.info("🎨 Unified Dialog Widget V3 - Bereit für Lupe-Tests!")
            
            logger.info("✅ UnifiedPdvmDialogWidget V3 erfolgreich in Arbeitsbereich integriert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des UnifiedPdvmDialogWidget: {e}")
            # Fehler-Widget anzeigen (ersetzt show_error_widget)
            from PyQt5.QtWidgets import QLabel
            error_label = QLabel(f"❌ Fehler beim Laden: {str(e)}")
            error_label.setStyleSheet("color: red; font-size: 14px; padding: 20px;")
            self.content_layout.addWidget(error_label)
    
    def get_current_unified_widget(self):
        """Gibt das aktuelle Unified Widget zurück (für Menü-Integration)"""
        if hasattr(self, 'current_dialog_widget') and self.current_dialog_widget:
            return self.current_dialog_widget
        elif hasattr(self, 'unified_widget') and self.unified_widget:
            return self.unified_widget
        else:
            logger.warning("⚠️ Kein Unified Dialog Widget aktiv")
            return None

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