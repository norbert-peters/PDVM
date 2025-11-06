#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDVM-SYSTEM Version 0.9 - Hauptanwendung

Personal Daten Verwaltungs Management System
Produktionsstand: Beta

AUTOR: Norbert Peters
DATUM: 06.11.2025
VERSION: 0.9
"""

import sys, io, os, logging, json, traceback

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
        logging.FileHandler("pdvm_app_final.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)
logger.info("🔹 Vollständige finale Hauptanwendung gestartet")

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QApplication,
    QDateTimeEdit, QPushButton
)
from PyQt5.QtCore import Qt, QDateTime, QDate, QTime
from PyQt5.QtGui import QFont
from PyQt5 import sip  # Für isdeleted() Check

# V2.0: Angepasste Imports
from pdvm_central_systemsteuerung import get_gcs
from pdvm_central_datenbank import PdvmCentralDatenbank

class V2MainAppComplete(QMainWindow):
    """
    V2.0 Hauptanwendung (Basis: MainAppComplete aus pdvm_systemstart.py)
    
    Features (übernommen):
    - ✅ Stichtag-Balken mit GCS-Integration
    - ✅ Content-Frame für Views
    - ✅ Fensterlayout
    
    TODO (später):
    - ⏳ Menü-System (neu implementieren)
    - ⏳ MenuHandler (neu implementieren)
    - ⏳ Command-Handler-System
    - ⏳ View-Integration mit Multi-Tab
    """
    
    def __init__(self):
        super().__init__()
        
        # V2.0: GCS-Zugriff
        self.gcs = get_gcs()
        if not self.gcs:
            raise RuntimeError("❌ GCS muss vor MainApp initialisiert sein!")
        
        # Version aus GCS holen
        version = self.gcs.version
        self.setWindowTitle(f"PDVM-SYSTEM Version {version} - Hauptanwendung")
        self.resize(1000, 600)
        
        # V2.0: Mandanten-Bezeichnung aus Mandanten-Daten (ROOT.BEZEICHNUNG)
        try:
            # Hole BEZEICHNUNG aus ROOT-Gruppe der Mandanten-Daten
            mandant_data = self.gcs._mandant_data
            root_data = mandant_data.get('ROOT', {})
            mandant_bezeichnung = root_data.get('BEZEICHNUNG')
            
            if not mandant_bezeichnung:
                logger.error("❌ KRITISCH: Mandanten-Bezeichnung (ROOT.BEZEICHNUNG) fehlt!")
                logger.error(f"   Mandanten-Daten Struktur: {list(mandant_data.keys())}")
                logger.error(f"   ROOT-Gruppe: {root_data}")
                raise ValueError("Mandanten-Bezeichnung nicht gefunden - System kann nicht starten!")
        except Exception as e:
            logger.error(f"❌ FEHLER beim Laden der Mandanten-Bezeichnung: {e}")
            raise RuntimeError(f"Mandanten-Konfiguration fehlerhaft: {e}")
        
        # V2.0: Benutzername aus user_data (auth.db) - Hierarchische Struktur!
        user_data = self.gcs._user_data
        user_info = user_data.get('USER', {})
        anrede = user_info.get('ANREDE', '')
        vorname = user_info.get('VORNAME', '')
        name = user_info.get('NAME', '')
        user_name = f"{anrede} {vorname} {name}".strip() or 'Unbekannt'
        
        # Fensterkopfzeile: Mandant - Benutzername (Version aus GCS)
        version = self.gcs.version
        self.setWindowTitle(f"PDVM-SYSTEM Version {version} - {mandant_bezeichnung} - {user_name}")

        logger.info(f"✅ V2.0 Hauptanwendung gestartet für User: {self.gcs.user_guid}")
        
        # V2.0: Neues Layout mit Menü-System
        central = QWidget()
        self.setCentralWidget(central)
        
        # Haupt-Layout: Vertikal
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. MENÜLEISTE OBEN (GRUND + ZUSATZ in einer Zeile)
        menu_bar_container = QWidget()
        menu_bar_container.setFixedHeight(50)
        menu_bar_layout = QHBoxLayout(menu_bar_container)
        menu_bar_layout.setContentsMargins(0, 0, 0, 0)
        menu_bar_layout.setSpacing(0)
        
        # GRUND-Menü (links)
        self.grund_menu_container = QWidget()
        menu_bar_layout.addWidget(self.grund_menu_container)
        
        # ZUSATZ-Menü (direkt rechts anschließend)
        self.zusatz_menu_container = QWidget()
        menu_bar_layout.addWidget(self.zusatz_menu_container)
        
        # Stretch am Ende für Ausrichtung
        menu_bar_layout.addStretch()
        
        main_layout.addWidget(menu_bar_container)
        
        # 2. ARBEITSBEREICH (VERTIKAL links, Rest rechts)
        work_area = QWidget()
        self.work_area_layout = QHBoxLayout(work_area)  # ✅ Als Instanz-Variable speichern für toggle_menu
        self.work_area_layout.setContentsMargins(0, 0, 0, 0)
        self.work_area_layout.setSpacing(0)
        
        # VERTIKAL-Menü (links)
        self.vertical_menu_container = QWidget()
        self.vertical_menu_container.setFixedWidth(200)
        self.work_area_layout.addWidget(self.vertical_menu_container)
        
        # V2.0: Menü-Sichtbarkeits-Status initialisieren
        self._menu_visible = True  # Standardmäßig sichtbar
        
        # Rechte Seite: Vertikal (Stichtag-Bar + Content)
        right_side = QWidget()
        right_side_layout = QVBoxLayout(right_side)
        right_side_layout.setContentsMargins(0, 0, 0, 0)
        right_side_layout.setSpacing(0)
        self.work_area_layout.addWidget(right_side)
        
        # ========== V3.1: 3-EBENEN-ARCHITEKTUR ==========
        # EBENE 1: Stichtagsbar (FEST - nie vom Pipeline berührt)
        # EBENE 2: Separator (FEST - nie vom Pipeline berührt)
        # EBENE 3: Workspace-Frame (DYNAMISCH - Pipeline verwaltet NUR DIESEN!)
        
        main_layout.addWidget(work_area)

        # V3.0: Menu Handler initialisieren (LINEAR & EINFACH!)
        try:
            from v3_menu_handler import V3MenuHandler
            self.menu_handler = V3MenuHandler(
                self.vertical_menu_container,
                self.grund_menu_container,
                self.zusatz_menu_container
            )
            # WICHTIG: main_app Referenz setzen für Handler-Context
            self.menu_handler.main_app = self
            logger.info("✅ V3 Menu Handler initialisiert")
        except Exception as e:
            logger.error(f"❌ V3 Menu Handler Fehler: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.menu_handler = None
        
        # ========== EBENE 1: STICHTAGSBAR (PERMANENT) ==========
        logger.info("🔧 Erstelle Stichtag-Balken...")
        self.stichtag_bar = self._create_complete_stichtag_bar()
        if self.stichtag_bar:
            logger.info("✅ Stichtag-Balken erstellt")
            right_side_layout.addWidget(self.stichtag_bar)  # Direkt in right_side_layout!
        else:
            logger.error("❌ Stichtag-Balken konnte nicht erstellt werden!")
        
        # ========== EBENE 2: SEPARATOR (PERMANENT) ==========
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        right_side_layout.addWidget(separator)  # Direkt in right_side_layout!
        
        # ========== EBENE 3: WORKSPACE-FRAME (DYNAMISCH) ==========
        # Nur DIESER Frame wird vom Pipeline gelöscht/befüllt!
        self.workspace_frame = QWidget()
        self.workspace_layout = QVBoxLayout(self.workspace_frame)
        self.workspace_layout.setContentsMargins(0, 0, 0, 0)
        self.workspace_layout.setSpacing(0)
        right_side_layout.addWidget(self.workspace_frame)
        
        # Kompatibilitäts-Alias für alte Code-Stellen
        self.content_frame = self.workspace_frame  # DEPRECATED: Verwende workspace_frame!
        
        # V2.0: Willkommensbereich (initial im workspace_frame)
        self.welcome_widget = self._create_welcome_widget()
        self.workspace_layout.addWidget(self.welcome_widget)
        
        # V2.0: Startmenü laden
        if self.menu_handler:
            logger.info("🚀 Lade Startmenü...")
            success = self.menu_handler.load_startmenu()
            if success:
                logger.info("✅ Startmenü erfolgreich geladen")
                # Zeige Willkommenstext für Startmenü
                self._show_welcome_message()
            else:
                logger.warning("⚠️ Startmenü konnte nicht geladen werden")
        else:
            logger.warning("⚠️ Menu Handler nicht verfügbar - kein Menü")

    def _create_welcome_widget(self):
        """Erstellt Widget für Willkommenstext/Menü-Info"""
        from PyQt5.QtWidgets import QTextEdit
        
        widget = QTextEdit()
        widget.setReadOnly(True)
        widget.setStyleSheet("""
            QTextEdit {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                padding: 20px;
                font-size: 12pt;
            }
        """)
        return widget
    
    # ========================================
    # ARBEITSBEREICHS-PIPELINE
    # ========================================
    
    def workspace_pipeline(self, command_func=None, error_message=None, skip_clear=False, alternativ_skip_clear=False, alternativ_func=None):
        """
        V3.2: LINEARE PIPELINE nach User-Vorgabe
        
        3-EBENEN-ARCHITEKTUR:
        - Stichtagsbar (FEST, über workspace_frame)
        - Separator (FEST, über workspace_frame)
        - workspace_frame (DYNAMISCH - Pipeline verwaltet NUR DIESEN!)
        
        ABLAUF (STRIKT LINEAR):
        
        1. Handler wird aufgerufen
        2. Handler bereitet Parameter für Pipeline auf
        3. Pipeline arbeitet:
        
           skip_clear=False (Arbeitsbereich wird neu belegt):
           3.1 Arbeitsbereich löschen
           3.2 Aufruf ausführen (command_func)
           3.3 Falls leer → alternativ_func ausführen (z.B. Welcome-Screen)
           
           skip_clear=True (Arbeitsbereich bleibt):
           4.1 Arbeitsbereich wird NICHT gelöscht
           4.2 Aufruf wird ausgeführt (command_func)
           4.3 alternativ_skip_clear entscheidet:
               False → Pipeline Ende (Arbeitsbereich bleibt)
               True  → Arbeitsbereich löschen + alternativ_func ausführen
        
        Args:
            command_func: Haupt-Funktion (Handler-Logik)
            error_message: Fehlermeldung (optional)
            skip_clear: False = Workspace leeren vor Aufruf, True = behalten
            alternativ_skip_clear: True = Nach skip_clear Workspace löschen
            alternativ_func: Funktion für leeren Workspace (z.B. Welcome-Screen)
        
        Returns:
            bool: True wenn erfolgreich, False bei Fehler
        """
        try:
            # ========== SCHRITT 3.1 / 4.1: WORKSPACE LEEREN (BEDINGT) ==========
            if not skip_clear:
                logger.info("🧹 STEP 3.1: Workspace-Frame leeren...")
                self._clear_workspace_layout()
                logger.info("✅ STEP 3.1 abgeschlossen: Workspace-Frame geleert")
            else:
                logger.info("⏭️ STEP 4.1: Workspace bleibt unverändert (skip_clear=True)")
            
            # ========== SCHRITT 3.2 / 4.2: HAUPTAUFRUF AUSFÜHREN ==========
            if error_message:
                logger.warning(f"⚠️ Zeige Fehlermeldung: {error_message}")
                self._show_error_in_workspace(error_message)
                return False
            
            if command_func:
                logger.info(f"⚡ STEP {3.2 if not skip_clear else 4.2}: Führe Command-Funktion aus...")
                result = command_func()
                logger.info(f"✅ Command ausgeführt (Result: {result})")
            else:
                result = True
            
            # ========== SCHRITT 4.3: ALTERNATIV-LOGIK (nur bei skip_clear=True) ==========
            if skip_clear:
                if alternativ_skip_clear:
                    logger.info("🧹 STEP 4.4: alternativ_skip_clear=True → Workspace leeren")
                    self._clear_workspace_layout()
                    
                    # STEP 4.5: Alternativen Aufruf ausführen
                    if alternativ_func:
                        logger.info("🎨 STEP 4.5: Führe alternativ_func aus...")
                        alternativ_func()
                    elif self.workspace_layout.count() == 0:
                        logger.info("🏠 STEP 4.5: Füge Welcome-Screen ein...")
                        self._insert_welcome_screen()
                else:
                    logger.info("✅ STEP 4.3: alternativ_skip_clear=False → Pipeline Ende")
                
                return result if result is not None else True
            
            # ========== SCHRITT 3.3: WORKSPACE-FÜLLUNG GARANTIEREN ==========
            if self.workspace_layout.count() == 0:
                logger.info("⚠️ STEP 3.3: Workspace leer → Füge Inhalt ein")
                
                if alternativ_func:
                    logger.info("🎨 Führe alternativ_func aus...")
                    alternativ_func()
                else:
                    logger.info("🏠 Füge Welcome-Screen ein...")
                    self._insert_welcome_screen()
            
            return result if result is not None else True
            
        except Exception as e:
            logger.error(f"❌ PIPELINE-FEHLER: {e}", exc_info=True)
            self._show_error_in_workspace(f"Pipeline-Fehler: {str(e)}")
            return False
    
    def _clear_workspace_layout(self):
        """Löscht ALLE Widgets aus workspace_layout"""
        while self.workspace_layout.count() > 0:
            item = self.workspace_layout.takeAt(0)
            if item.widget():
                widget = item.widget()
                widget.hide()
                widget.deleteLater()
                logger.debug(f"  ✅ Widget entfernt: {type(widget).__name__}")
        
        # Alte Referenzen löschen
        if hasattr(self, 'current_dialog_widget'):
            self.current_dialog_widget = None
        if hasattr(self, 'current_view_widget'):
            self.current_view_widget = None
    
    def _insert_welcome_screen(self):
        """
        Fügt Welcome-Screen in workspace_layout ein
        
        WICHTIG: Erstellt NEUES Widget (altes wurde gelöscht!)
        """
        # Erstelle NEUES Widget
        self.welcome_widget = self._create_welcome_widget()
        self._show_welcome_message()
        
        # Füge in Workspace ein
        self.workspace_layout.addWidget(self.welcome_widget)
        self.welcome_widget.show()
        logger.info("✅ Welcome-Screen eingefügt")
        
        # App-Name einfügen (falls gesetzt)
        if hasattr(self, '_current_app_name') and self._current_app_name:
            try:
                app_name = self._current_app_name
                current_html = self.welcome_widget.toHtml()
                
                app_info_html = f"""
                <div style="text-align: center; padding: 20px; margin-top: 20px; 
                            background-color: #e3f2fd; border-radius: 10px; 
                            border-left: 4px solid #0078d4;">
                    <h2 style="color: #0078d4; margin: 0;">📂 {app_name}</h2>
                    <p style="color: #666; margin: 10px 0 0 0;">
                        Wählen Sie eine Aktion aus dem Menü
                    </p>
                </div>
                """
                
                if "<h1" in current_html and "</h1>" in current_html:
                    parts = current_html.split("</h1>", 1)
                    new_html = parts[0] + "</h1>" + app_info_html + parts[1]
                    self.welcome_widget.setHtml(new_html)
                    logger.info(f"✅ App-Name in Welcome-Screen: {app_name}")
                
                # Reset
                self._current_app_name = None
            except Exception as e:
                logger.debug(f"ℹ️ App-Name konnte nicht eingefügt werden: {e}")
    
    # ========================================
    # PIPELINE-HANDLER (V3.2)
    # ========================================
    
    def handler_return_to_startmenu(self):
        """
        🏠 Handler: Zurück zum Startmenü
        
        V3.2: Lädt Startmenü, Pipeline fügt Welcome-Screen automatisch ein
        skip_clear=False → Workspace wird geleert, STEP 3.3 fügt Welcome ein
        """
        try:
            logger.info("🏠 Handler: Zurück zum Startmenü")
            
            def _load_startmenu():
                # Lade Startmenü
                if self.menu_handler:
                    success = self.menu_handler.load_startmenu()
                    if success:
                        logger.info("✅ Startmenü geladen")
                        # V3.2: KEIN _show_welcome_message() mehr!
                        # Pipeline fügt Welcome-Screen automatisch ein (STEP 3.3)
                    else:
                        logger.error("❌ Startmenü konnte nicht geladen werden")
                    return success
                return False
            
            # Pipeline mit skip_clear=False → Workspace leeren (3.1) + Welcome (3.3)
            return self.workspace_pipeline(command_func=_load_startmenu)
            
        except Exception as e:
            logger.error(f"❌ Handler-Fehler (Return to Startmenu): {e}", exc_info=True)
            self.workspace_pipeline(error_message=f"Fehler beim Laden des Startmenüs: {str(e)}")
            return False
    
    def handler_toggle_menu(self):
        """
        🔄 Handler: Menü ein/ausschalten
        
        Toggle Menü-Sichtbarkeit OHNE Arbeitsbereich zu leeren
        Arbeitsbereich bleibt unverändert (skip_clear=True)
        """
        try:
            logger.info("🔄 Handler: Menü ein/aus")
            
            def _toggle_menu():
                # Toggle Menü-Sichtbarkeit
                if hasattr(self, 'vertical_menu_container') and self.vertical_menu_container:
                    current_visible = self.vertical_menu_container.isVisible()
                    new_visible = not current_visible
                    
                    self.vertical_menu_container.setVisible(new_visible)
                    self._menu_visible = new_visible
                    
                    status = "ein" if new_visible else "aus"
                    logger.info(f"✅ Menü {status}geschaltet")
                    return True
                return False
            
            # Pipeline mit skip_clear=True → Arbeitsbereich NICHT leeren!
            return self.workspace_pipeline(command_func=_toggle_menu, skip_clear=True)
            
        except Exception as e:
            logger.error(f"❌ Handler-Fehler (Toggle Menu): {e}", exc_info=True)
            return False
    
    def handler_toggle_stichtagsbar(self):
        """
        🔄 Handler: Stichtagsbar ein/ausschalten
        
        Toggle Stichtagsbar-Sichtbarkeit OHNE Arbeitsbereich zu leeren
        Arbeitsbereich bleibt unverändert (skip_clear=True)
        """
        try:
            logger.info("🔄 Handler: Stichtagsbar ein/aus")
            
            def _toggle_stichtagsbar():
                # Toggle Stichtagsbar-Sichtbarkeit
                if hasattr(self, 'stichtag_bar') and self.stichtag_bar:
                    current_visible = self.stichtag_bar.isVisible()
                    new_visible = not current_visible
                    
                    self.stichtag_bar.setVisible(new_visible)
                    
                    status = "ein" if new_visible else "aus"
                    logger.info(f"✅ Stichtagsbar {status}geschaltet")
                    return True
                return False
            
            # Pipeline mit skip_clear=True → Arbeitsbereich NICHT leeren!
            return self.workspace_pipeline(command_func=_toggle_stichtagsbar, skip_clear=True)
            
        except Exception as e:
            logger.error(f"❌ Handler-Fehler (Toggle Stichtagsbar): {e}", exc_info=True)
            return False
    
    def _show_error_in_workspace(self, error_message: str):
        """
        Zeigt Fehlermeldung im Arbeitsbereich an
        
        Args:
            error_message: Fehlermeldung
        """
        from PyQt5.QtWidgets import QLabel
        
        error_widget = QLabel()
        error_widget.setWordWrap(True)
        error_widget.setStyleSheet("""
            QLabel {
                background-color: #fee;
                border: 2px solid #c00;
                border-radius: 5px;
                padding: 30px;
                font-size: 14pt;
                color: #c00;
            }
        """)
        error_widget.setText(f"❌ FEHLER\n\n{error_message}")
        error_widget.setAlignment(Qt.AlignCenter)
        
        self.workspace_layout.addWidget(error_widget)  # V3.1: workspace_layout statt content_layout!
        logger.debug("  ✅ Fehler-Widget erstellt und angezeigt")
    
    def _show_welcome_message(self):
        """Zeigt Willkommenstext für Startmenü"""
        # Hole User-Info aus GCS
        user_info = self.gcs._user_data.get('USER', {})
        vorname = user_info.get('VORNAME', '')
        name = user_info.get('NAME', '')
        
        # Version aus GCS holen
        version = self.gcs.version
        
        welcome_html = f"""
        <div style="text-align: center; padding: 40px;">
            <h1 style="color: #0078d4;">🎉 Willkommen im PDVM-SYSTEM Version {version}!</h1>
            <h2 style="color: #555;">Hallo {vorname} {name}</h2>
            
            <div style="text-align: left; margin-top: 40px; padding: 20px; background-color: white; border-radius: 5px;">
                <h3 style="color: #0078d4;">📋 Kurzanleitung:</h3>
                <ul style="font-size: 11pt; line-height: 1.8;">
                    <li><b>Vertikalmenü (links):</b> Hauptnavigation - Klicken Sie auf einen Bereich</li>
                    <li><b>Grundmenü (oben):</b> Allgemeine Aktionen wie Datei, Bearbeiten, Ansicht</li>
                    <li><b>Zusatzmenü (oben rechts):</b> Kontextspezifische Aktionen erscheinen automatisch</li>
                    <li><b>Stichtag:</b> Wählen Sie einen Zeitpunkt für historische Datenansicht</li>
                </ul>
                
                <h3 style="color: #0078d4; margin-top: 30px;">🚀 Erste Schritte:</h3>
                <ol style="font-size: 11pt; line-height: 1.8;">
                    <li>Wählen Sie einen Bereich aus dem <b>Vertikalmenü</b> (z.B. "Stammdaten")</li>
                    <li>Im <b>Zusatzmenü</b> erscheinen dann passende Aktionen (z.B. "Neu", "Bearbeiten")</li>
                    <li>Nutzen Sie das <b>Grundmenü</b> für allgemeine Funktionen</li>
                    <li>Der <b>Stichtag</b> ermöglicht Ihnen Zeitreisen in der Datenhistorie</li>
                </ol>
                
                <p style="margin-top: 30px; padding: 15px; background-color: #fff3cd; border-left: 4px solid #ffc107;">
                    <b>💡 Tipp:</b> Klicken Sie auf "Stammdaten" im Vertikalmenü, um die Personenverwaltung zu öffnen!
                </p>
            </div>
        </div>
        """
        
        self.welcome_widget.setHtml(welcome_html)
    
    def _show_menu_info(self, menu_name: str):
        """Zeigt Info über aktuelles Menü"""
        info_html = f"""
        <div style="text-align: center; padding: 40px;">
            <h2 style="color: #0078d4;">📂 Aktuelles Menü</h2>
            <h1 style="color: #333;">{menu_name}</h1>
            
            <p style="font-size: 12pt; color: #666; margin-top: 20px;">
                Wählen Sie eine Aktion aus dem Menü
            </p>
        </div>
        """
        
        self.welcome_widget.setHtml(info_html)

    def _create_complete_stichtag_bar(self):
        """
        Erstellt den vollständigen Stichtag-Balken für historische Datenansicht.
        
        Verwendet die finale GCS-Architektur mit self.gcs.st_inst.
        Layout: 'Stichtag:' (PdvmDateTimePicker) --> verwendeter Stichtag: (PdvmTimeStamp) [Refresh]
        
        Returns:
            QWidget: Vollständige Stichtag-Balken Widget
        """
        logger.info("🔧 _create_vollständigen_stichtag_bar gestartet...")
        
        from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QFrame
        from PyQt5.QtGui import QFont
        
        # V2.0: GCS-Prüfung
        if not self.gcs:
            logger.error("❌ GCS nicht verfügbar - kann Balken nicht erstellen")
            return QLabel("❌ GCS nicht verfügbar")
        logger.info("✅ GCS verfügbar")
        
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
        logger.info("✅ Vollständiger Stichtag-Widget Container erstellt")
        
        layout = QHBoxLayout(stichtag_widget)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # "Stichtag:" Label
        stichtag_label = QLabel("Stichtag:")
        font = QFont()
        font.setBold(True)
        stichtag_label.setFont(font)
        layout.addWidget(stichtag_label)
        logger.info("✅ Stichtag-Label hinzugefügt")
        
        # Stichtag-Instanz aus finale GCS holen - mit Fallback
        try:
            # Für finale GCS verwenden wir self.gcs.st_inst direkt
            try:
                from pdvm_date_time_picker import PdvmDateTimePicker
                self.stichtag_picker = PdvmDateTimePicker(
                    parent=self,
                    pdvm_datetime=self.gcs.st_inst,  # Finale GCS st_inst!
                    display="all",
                    display_time_short=False
                )
                logger.info(f"✅ Vollständige PdvmDateTimePicker Datum: {self.gcs.st_inst}") 
                if hasattr(self.stichtag_picker, '_date_edit'):
                    calendar = self.stichtag_picker._date_edit.calendarWidget()
                    if calendar:
                        calendar.setMinimumSize(350, 220)
                layout.addWidget(self.stichtag_picker)
                logger.info("✅ Vollständige PdvmDateTimePicker erstellt und hinzugefügt")
            except ImportError:
                # Fallback: Einfacher DateTimePicker
                logger.warning("⚠️ PdvmDateTimePicker nicht verfügbar - verwende QDateTimeEdit")
                self.stichtag_picker = QDateTimeEdit()
                self.stichtag_picker.setDisplayFormat("dd.MM.yyyy - hh:mm:ss")
                self.stichtag_picker.setCalendarPopup(True)
                layout.addWidget(self.stichtag_picker)
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des vollständigen DateTimePicker: {e}")
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
        self._update_complete_stichtag_display()
        layout.addWidget(self.stichtag_display)
        logger.info("✅ Vollständige Stichtag-Display erstellt")
        
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
        self.refresh_button.clicked.connect(self._on_complete_stichtag_refresh)
        layout.addWidget(self.refresh_button)
        logger.info("✅ Vollständige Refresh-Button erstellt")
        
        # Stretch am Ende für rechte Ausrichtung
        layout.addStretch(1)
        
        logger.info("✅ Vollständiger Stichtag-Balken vollständig erstellt")
        return stichtag_widget

    def _update_complete_stichtag_display(self):
        """
        Aktualisiert die Anzeige des verwendeten Stichtags mit finale self.gcs.
        """
        try:
            if self.gcs:
                # Finale GCS verwendet st_inst direkt
                stichtag_value = self.gcs.st_inst
                # Anzeige als PdvmTimeStamp (schönes Format)
                if hasattr(stichtag_value, 'FormTimeStamp'):
                    display_text = str(stichtag_value.FormTimeStamp)
                else:
                    display_text = str(stichtag_value)
                    
                self.stichtag_display.setText(display_text)
                logger.debug(f"🔄 Vollständige Stichtag-Anzeige aktualisiert: {display_text}")
            else:
                self.stichtag_display.setText("Stichtag lädt...")
                logger.warning("⚠️ Finale GCS nicht verfügbar für Display-Update")
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der vollständigen Stichtag-Anzeige: {e}")
            self.stichtag_display.setText("Fehler beim Laden")

    def _on_complete_stichtag_refresh(self):
        """
        🎯 VOLLSTÄNDIGE REFRESH-ARCHITEKTUR:
        
        Behandelt den Refresh-Button Click mit finale GCS-Technik:
        1. save() auf Picker → Änderungen landen direkt in finale GCS-Instanz  
        2. Persistierung über finale GCS
        3. Display-Update
        4. Controller-basierte View-Aktualisierung (NEUE ARCHITEKTUR)
        """
        try:
            logger.info("🔄 Vollständige Stichtag-Refresh gestartet...")
            
            # 1. Picker-Änderungen speichern (finale Architektur)
            if hasattr(self, 'stichtag_picker') and self.stichtag_picker:
                logger.info(f"📊 VOR save(): self.gcs.st_inst={self.gcs.st_inst.PdvmDateTime}, picker.initial={self.stichtag_picker.initial.PdvmDateTime}")
                
                if hasattr(self.stichtag_picker, 'save'):
                    self.stichtag_picker.save()
                    logger.info("💾 Vollständige Stichtag-Picker Änderungen gespeichert")
                    logger.info(f"📊 NACH save(): self.gcs.st_inst={self.gcs.st_inst.PdvmDateTime}")
                else:
                    logger.warning("⚠️ Vollständige Stichtag-Picker hat keine save()-Methode")
            
            # 2. Stichtag in finale GCS persistieren
            if self.gcs and hasattr(self.gcs, 'update_stichtag'):
                logger.info(f"📊 VOR update_stichtag(): self.gcs.st_inst={self.gcs.st_inst.PdvmDateTime}")
                self.gcs.update_stichtag()
                logger.info("💾 Stichtag erfolgreich in finale GCS persistiert")
            else:
                logger.warning("⚠️ Finale GCS nicht verfügbar oder update_stichtag() fehlt")
            
            # 3. Display aktualisieren (finale GCS)
            self._update_complete_stichtag_display()
            
            # 4. View-Aktualisierung über SIGNAL (AUTOMATISCH!)
            # ✅ Das stichtag_changed Signal wurde bereits emittiert (durch update_stichtag())
            # ✅ Alle verbundenen Views werden automatisch über reload_with_stichtag() aktualisiert
            # ❌ KEIN direkter refresh() Aufruf nötig - das würde die Daten-Neuladung überschreiben!
            logger.info("✅ Stichtag-Signal emittiert → Views werden automatisch aktualisiert")
            logger.info(f"   📅 Neuer Stichtag: {self.gcs.stichtag}")
            logger.info("   🔔 Alle Views mit reload_with_stichtag() verbunden werden neu geladen")
            
            # 5. Dialog-Aktualisierung (EBENFALLS ÜBER SIGNAL!)
            # ✅ Genereller Dialog sollte auch mit stichtag_changed verbunden sein
            # ❌ Falls nicht, hier Warnung ausgeben
            if hasattr(self, 'current_dialog') and self.current_dialog:
                logger.info("ℹ️ Genereller Dialog offen - sollte ebenfalls Signal empfangen haben")
            
            logger.info("✅ Vollständige Stichtag-Refresh abgeschlossen")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren des vollständigen Stichtag-Balkens: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def _check_and_create_demo_menu(self, menu_id):
        """
        Überprüft ob ein Demo-Startmenü existiert und erstellt es falls nötig.
        NUR FÜR ENTWICKLUNG/TEST - in Produktion sollte dies deaktiviert sein.
        """
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            
            # Prüfe ob schon eine Datenbank-Instanz vorhanden ist
            if hasattr(PdvmCentralDatenbank, '_instance') and PdvmCentralDatenbank._instance:
                db = PdvmCentralDatenbank._instance
            else:
                logger.warning("⚠️ Keine zentrale DB-Instanz - erstelle neue für Demo-Menü-Check")
                db = PdvmCentralDatenbank()
                
            # GUID setzen wenn nicht vorhanden
            if not db.guid:
                db.guid = self.gcs._user_guid
                logger.info(f"✅ DB GUID gesetzt für Demo-Menü: {self.gcs._user_guid}")
            
            # Prüfe ob Demo-Menü bereits existiert (verwende get_value statt load_menu_data)
            existing_menu = db.get_value(
                gruppe=menu_id,
                feld="PD_grund"
            )
            if existing_menu and existing_menu.get("wert"):
                logger.info(f"✅ Demo-Startmenü bereits vorhanden: {menu_id}")
                return True
            
            # Erstelle Demo-Menüstruktur mit set_value
            demo_grund_struktur = {
                "Systemsteuerung": {
                    "PD_name": "Systemsteuerung",
                    "PD_command": "system_settings"
                },
                "Ansichten": {
                    "PD_name": "Ansichten", 
                    "Standardansicht": {
                        "PD_name": "Standardansicht",
                        "PD_command": "show_standard_view"
                    }
                }
            }
            
            # Menü in Datenbank speichern (verwende set_value statt save_menu_data)
            db.set_value(
                gruppe=menu_id,
                feld="PD_grund",
                wert=demo_grund_struktur
            )
            
            # Zusätzliche Menü-Felder setzen
            db.set_value(
                gruppe=menu_id,
                feld="PD_commands",
                wert={}
            )
            
            logger.warning(f"⚠️ Demo-Startmenü erstellt: {menu_id}")
            logger.warning("⚠️ DIES IST NUR FÜR ENTWICKLUNG/TEST!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Demo-Menü-Check: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return False

    def _show_label(self, texts, small=False, clear_content=True, max_height=None):
        """
        Zeigt eine oder mehrere Zeilen Text im Inhaltsbereich an.
        texts: Liste von Strings (oder ein einzelner String)
        max_height: Maximale Höhe in Pixeln - bei Überschreitung wird ScrollArea erstellt
        """
        if clear_content:
            self.clear_content_layout()
        
        # Größerer oberer Abstand (30px statt vorher zentriert)
        self.workspace_layout.addSpacing(30)
        
        # Text aufbereiten
        if isinstance(texts, str):
            texts = [texts]
        
        # Prüfe ob ScrollArea benötigt wird (mehr als 20 Zeilen oder explizite max_height)
        needs_scroll = len(texts) > 20 or max_height is not None
        
        if needs_scroll:
            # 🎯 ScrollArea für lange Inhalte erstellen
            from PyQt5.QtWidgets import QScrollArea, QWidget, QVBoxLayout
            
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            
            # Maximale Höhe setzen (Standard: 400px für Diagnose-Ergebnisse)
            if max_height is None:
                max_height = 400
            scroll_area.setMaximumHeight(max_height)
            scroll_area.setMinimumHeight(min(max_height, 200))  # Mindesthöhe
            
            # Widget für Scroll-Inhalt
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)
            scroll_layout.setSpacing(2)  # Weniger Abstand für kompakte Darstellung
            
            # Labels zu Scroll-Layout hinzufügen
            for text in texts:
                lbl = QLabel(text)
                lbl.setAlignment(Qt.AlignLeft)  # Links ausrichten für bessere Lesbarkeit
                lbl.setWordWrap(True)  # Zeilenumbruch aktivieren
                if small:
                    lbl.setStyleSheet("""
                        font-size: 11px; 
                        margin: 1px; 
                        padding: 2px;
                        font-family: 'Courier New', monospace;
                    """)
                else:
                    lbl.setStyleSheet("""
                        font-size: 13px; 
                        margin: 2px; 
                        padding: 3px;
                        font-family: 'Courier New', monospace;
                    """)
                scroll_layout.addWidget(lbl)
            
            # Stretch am Ende für kompakte Darstellung
            scroll_layout.addStretch(1)
            
            # Widget in ScrollArea setzen
            scroll_area.setWidget(scroll_widget)
            
            # ScrollArea zum Hauptlayout hinzufügen
            self.workspace_layout.addWidget(scroll_area)
            
            logger.info(f"📜 ScrollArea erstellt für {len(texts)} Zeilen (max_height: {max_height}px)")
            
        else:
            # Normale Darstellung ohne ScrollArea
            for text in texts:
                lbl = QLabel(text)
                lbl.setAlignment(Qt.AlignCenter)
                if small:
                    lbl.setStyleSheet("font-size: 12px; margin: 5px;")
                else:
                    lbl.setStyleSheet("font-size: 16px; margin: 10px;")
                self.workspace_layout.addWidget(lbl)
        
        # Flexibler unterer Abstand (nimmt den restlichen Platz ein)
        self.workspace_layout.addStretch(1)

    def show_text(self, text, small=False):
        """Normaler Text im Hauptbereich."""
        self._show_label(f"{text}", small=small, clear_content=True)

    def show_text_klein(self, text):
        """Kleine Meldung unten anhängen."""
        # Einfache Implementierung: Zeige als normalen Text
        self._show_label(f"{text}", small=True, clear_content=True)

    def clear_content_layout(self):
        """
        V3.1: DEPRECATED - Verwende workspace_pipeline() stattdessen!
        
        Diese Methode bleibt aus Kompatibilitätsgründen, leitet aber
        nur noch an workspace_pipeline() weiter.
        
        3-EBENEN-ARCHITEKTUR:
        - Stichtagsbar ist ÜBER workspace_frame (nie berührt)
        - Separator ist ÜBER workspace_frame (nie berührt)
        - workspace_frame wird KOMPLETT geleert
        """
        logger.warning("⚠️ clear_content_layout() ist DEPRECATED - verwende workspace_pipeline()")
        
        # Leite an workspace_pipeline weiter (leert workspace_frame)
        while self.workspace_layout.count() > 0:
            item = self.workspace_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
                logger.debug(f"🗑️ Widget entfernt: {widget.__class__.__name__}")
            elif item.layout():
                self._clear_layout(item.layout())
                logger.debug("🗑️ Layout entfernt")
        
        logger.debug(f"✅ Workspace-Frame bereinigt (V3.1 Architektur)")

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
        
        try:
            # ⚠️ DEAKTIVIERT - Menü-Editor noch nicht fertig (Post-0.9 Feature)
            # Lazy Import - nur bei Bedarf laden
            # from pdvm_menu_editor import PdvmMenuEditor
            
            # Inhalt löschen
            self.clear_content_layout()
            
            # Platzhalter-Meldung
            logger.warning("⚠️ Menü-Editor noch nicht implementiert (Post-0.9 Feature)")
            # Editor instanziieren und anzeigen
            # editor = PdvmMenuEditor(self.content_frame, self.menu_handler.menu, menu_type, self, call_path)
            # self.workspace_layout.addWidget(editor)
        except ImportError as e:
            logger.warning(f"⚠️ Menüeditor nicht verfügbar: {e}")
            self.show_text(f"⚠️ Menüeditor nicht verfügbar: {e}")

    def open_start_menu(self):
        """STARTMENÜ mit Berechtigungsprüfung - klar getrennt von App-Menüs"""
        logger.info("🏠 open_start_menu() - STARTMENÜ wird geladen...")
        
        try:
            # Startmenü-GUID direkt aus GCS (ohne Zwischenvariable)
            startmenu_guid = self.gcs.get_menu_id('Startbereich')
            if not startmenu_guid:
                raise ValueError("Startmenü-GUID nicht in GCS gefunden!")
                
            logger.info(f"🔹 Startmenü-GUID aus GCS: {startmenu_guid}")
            
            # 🔒 LAZY IMPORT: Handler erst nach Login laden
            from pdvm_command_handler import PdvmCommandHandler
            from pdvm_menu_handler import PdvmMenuHandler
            
            # Handler nur initialisieren wenn noch nicht vorhanden
            if not hasattr(self, 'command_handler') or not self.command_handler:
                self.command_handler = PdvmCommandHandler(self)
                
            # STARTMENÜ-Handler erstellen
            self.menu_handler = PdvmMenuHandler(
                root=self,
                menu_widget=self.menu_frame,
                menu_id=startmenu_guid,
                command_handler=self.command_handler
            )
            
            self.menu_handler.create_menus()
            
            # Zentraler Startbildschirm
            self._show_label("🔹 Willkommen im vollständigen finalen PDVM-System!", small=False, clear_content=True)
            self._show_label([
                "🔹 Bitte wählen Sie eine Anwendung aus dem Menü links.",
                "📱 Multi-Tab mit Navigation: F4 für parallele Tab-Anzeige → Navigation erscheint",
                "🔍 Lupe-Funktionen: F1 (View) | F2 (Input) | F3 (Reset)",
                "⌨️ Tab-Navigation: Ctrl+←/→ oder Alt+1-9 für direkten Tab-Zugriff"
            ], small=True, clear_content=False)
            
            # STARTMENÜ: Panel DIREKT anzeigen - KEINE GCS-Abfrage!
            self._menu_visible = True
            # Direkte Panel-Anzeige ohne Umwege
            if self.menu_frame.isHidden():
                self.main_layout.insertWidget(0, self.menu_frame, 1)
                self.menu_frame.show()
            self.main_layout.update()
            QApplication.processEvents()
            logger.info("🏠 STARTMENÜ geladen - Panel DIREKT angezeigt (keine GCS-Abfrage)")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des STARTMENÜS: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Fallback: Einfache Demo-Meldung
            self._show_label("🔹 Willkommen im vollständigen finalen PDVM-System!", small=False, clear_content=True)
            self._show_label([
                "⚠️ Startmenü-System nicht verfügbar",
                f"Fehler: {e}",
                "🔧 System läuft im Basis-Modus"
            ], small=True, clear_content=False)

    def pdvm_start(self, application_name):
        """
        Startet eine Anwendung basierend auf den Benutzer-Berechtigungen aus der self.gcs.
        
        Args:
            application_name: Name der Anwendung (z.B. "Testbereich", "Personalwesen")
        """
        try:
            logger.info(f"🚀 Starte Anwendung: {application_name}")
            
            # Hole Menü-GUID aus GCS-Benutzerdaten basierend auf App-Berechtigung
            try:
                # Prüfe Menü-Berechtigung für die Anwendung
                menu_guid = self.gcs.get_menu_id(application_name)
                logger.debug(f"🔹 Gefundene Menü-GUID für '{application_name}': {menu_guid}")
                if not menu_guid:
                    logger.warning(f"⚠️ Keine Menü-Berechtigung für '{application_name}' - Zugriff verweigert")
                    self.show_text([
                        f"❌ Keine Berechtigung für Anwendung: {application_name}",
                        "",
                        "Sie haben keine Berechtigung für diese Anwendung.",
                        "Das entsprechende Menü steht Ihnen nicht zur Verfügung."
                    ], small=True)
                    return
                
                logger.info(f"✅ Menü-Berechtigung für '{application_name}' gefunden: {menu_guid}")
                
                # Starte die Anwendung mit der gefundenen Menü-GUID
                self._start_application_with_guid(application_name, menu_guid)
                
            except Exception as e:
                logger.error(f"❌ Fehler beim Prüfen der Menü-Berechtigung für '{application_name}': {e}")
                self.show_text([
                    f"❌ Fehler beim Starten von: {application_name}",
                    "",
                    "Berechtigungsprüfung fehlgeschlagen.",
                    "Bitte wenden Sie sich an den Administrator."
                ], small=True)
                
        except Exception as e:
            logger.error(f"❌ Kritischer Fehler beim Starten von '{application_name}': {e}")
    
    def _start_application_with_guid(self, application_name, app_guid):
        """
        Startet die Anwendung mit der gefundenen GUID.
        """
        try:
            logger.info(f"🔹 Lade Menü für '{application_name}' mit GUID: {app_guid}")
            
            # Hier wird das eigentliche Anwendungsmenü geladen und angezeigt
            # Das ist der gleiche Mechanismus wie beim Startmenü
            from pdvm_menu_handler import PdvmMenuHandler
            
            # Erstelle neuen Menü-Handler für die App mit korrekter Signatur
            app_menu_handler = PdvmMenuHandler(
                root=self,
                menu_widget=self.menu_frame,  # Verwende das bestehende Menü-Widget
                menu_id=app_guid,
                command_handler=self.command_handler
            )
            
            # Ersetze das aktuelle Menü mit dem neuen App-Menü
            self.current_app_menu = app_menu_handler
            self.current_app_name = application_name
            
            # Lösche das alte Startmenü und zeige das neue App-Menü
            self._replace_menu_with_app_menu(app_menu_handler)
            
            logger.info(f"✅ Anwendung '{application_name}' erfolgreich gestartet und Menü angezeigt")
            self.show_text([
                f"✅ Anwendung gestartet: {application_name}",
                "",
                f"Menü-ID: {app_guid}"
            ], small=True)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten der Anwendung '{application_name}': {e}")
            self.show_text([
                f"❌ Fehler beim Laden des Menüs für: {application_name}",
                "",
                "Das Menü konnte nicht geladen werden."
            ], small=True)

    def _replace_menu_with_app_menu(self, app_menu_handler):
        """
        Ersetzt das aktuelle Startmenü mit dem neuen App-Menü
        
        ORIGINALIMPLEMENTIERUNG aus pdvm_systemstart.py:
        Komplett Layout leeren und neu aufbauen
        
        Args:
            app_menu_handler: Der neue Menü-Handler für die App
        """
        try:
            logger.info(f"🔄 Ersetze Startmenü mit App-Menü...")
            
            # EXAKTE ORIGINALIMPLEMENTIERUNG: Layout komplett leeren
            layout = self.menu_frame.layout()
            
            # 1) Komplett leeren – Widgets UND Spacer
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w:
                    w.setParent(None)
            
            logger.info(f"🗑️ Menu-Layout vollständig geleert: {layout.count()} Items")
            
            # 2) App-Menü-Handler als neuer self.menu_handler setzen
            self.menu_handler = app_menu_handler
            
            # 3) Neue Menüs erstellen (exakt wie in Original)
            if hasattr(app_menu_handler, 'create_menus'):
                app_menu_handler.create_menus()
                logger.info(f"✅ App-Menüs erstellt und angezeigt")
                
                # 4) Menü-Sichtbarkeits-Status für das neue Menü laden
                self._load_and_apply_menu_visibility()
                
            else:
                logger.warning(f"⚠️ App-Menü-Handler hat keine create_menus Methode")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Ersetzen des Menüs: {e}")

    def test_pdvm_view(self, frame_guid, title=None):
        """
        🧪 TEST-METHODE für SAUBERE ARCHITEKTUR-MIGRATION
        
        Bereitet die Migration vor zu:
        - PdvmViewController (Controller/Logic) 
        - PdvmViewUI (Display/Darstellung)
        - PdvmViewManager (Daten/Matrix)
        
        Aktuell: Ruft die alte PdvmViewDialog auf (wie pdvm_modern_view)
        TODO Migration: Schrittweise auf neue Architektur umstellen
        
        Args:
            frame_guid: GUID der Frame-Daten
            title: Optional - Titel für die View
            
        Aufruf aus Menü:
            main_app.test_pdvm_view("frame-guid-hier", "Test View")
        """
        logger.info("🧪 === TEST PDVM VIEW - ARCHITEKTUR-MIGRATION ===")
        logger.info(f"📋 Frame-GUID: {frame_guid}")
        logger.info(f"📋 Titel: {title or 'Auto'}")
        
        if not frame_guid:
            logger.error("❌ Keine frame_guid übergeben!")
            self.show_text([
                "❌ TEST FEHLER: Keine Frame-GUID",
                "",
                "Bitte frame_guid als Parameter übergeben:",
                "test_pdvm_view('frame-guid-hier', 'Titel')"
            ], small=True)
            return

        try:
            # === SCHRITT 1: Frame-Daten laden ===
            logger.info("📂 SCHRITT 1: Frame-Daten laden...")
            from pdvm_central_datenbank import PdvmCentralDatenbank
            
            framedaten_db = PdvmCentralDatenbank(
                table_name="sys_framedaten", 
                guid=frame_guid
            )
            
            # View-GUID aus Frame-Daten ermitteln
            view_guid = framedaten_db.get_static_value("ROOT", "VIEW_GUID")
            if not view_guid:
                logger.error(f"❌ Keine view_guid in Frame-Daten gefunden")
                self.show_text([
                    "❌ TEST FEHLER: Keine View-GUID",
                    "",
                    f"Frame-GUID: {frame_guid}",
                    "Keine VIEW_GUID in Frame-Daten gefunden"
                ], small=True)
                return

            logger.info(f"✅ View-GUID ermittelt: {view_guid}")
            
            # === SCHRITT 2: Titel bestimmen ===
            logger.info("📝 SCHRITT 2: Titel bestimmen...")
            view_title = title
            if not view_title:
                try:
                    view_header = framedaten_db.get_static_value("ROOT", "VIEW_HEADER")
                    view_title = view_header or f"Test View: {view_guid[:8]}"
                except Exception as e:
                    logger.warning(f"⚠️ Fehler beim Titel-Laden: {e}")
                    view_title = f"Test View: {view_guid[:8]}"
            
            logger.info(f"✅ Titel gesetzt: {view_title}")

            # === SCHRITT 3: call_daten vorbereiten ===
            logger.info("📦 SCHRITT 3: call_daten vorbereiten...")
            call_daten = {
                "view_guid": view_guid,
                "title": view_title,
                "first_call": True,
                "test_mode": True,  # Marker für Test-Aufruf
            }
            
            logger.info(f"✅ call_daten: {call_daten}")

            # === SCHRITT 4: NEUE SAUBERE ARCHITEKTUR verwenden ===
            logger.info("🔧 SCHRITT 4: View laden (NEUE saubere Architektur)...")
            logger.info("✅ PdvmViewController (Controller/Logic)")
            logger.info("✅ PdvmViewUI (Display/Darstellung)")
            logger.info("⏳ PdvmViewManager (Daten) - Optional für später")
            
            try:
                from pdvm_view_controller import PdvmViewController
                
                # NEUE Architektur: Controller erstellen
                view_controller = PdvmViewController(call_daten, parent=self)
                
                # Controller initialisieren (lädt Daten, erstellt UI)
                init_success = view_controller.initialize()
                
                if not init_success:
                    raise RuntimeError("Controller-Initialisierung fehlgeschlagen")
                
                # Widget für Arbeitsbereich holen
                view_widget = view_controller.get_widget()
                
                if not view_widget:
                    raise RuntimeError("Kein Widget vom Controller erhalten")
                
                # Content löschen und neues Widget hinzufügen
                self.clear_content_layout()
                self.workspace_layout.addWidget(view_widget)
                
                # Controller speichern für Stichtag-Refresh und spätere Operationen
                self.current_view_controller = view_controller
                self.current_view_widget = view_widget
                
                logger.info(f"✅ TEST VIEW gestartet: {view_guid}")
                logger.info(f"📊 Titel: {view_title}")
                logger.info(f"🏗️ Architektur: NEU (Controller + UI)")
                logger.info(f"🎯 Controller-Instanz: {type(view_controller).__name__}")
                logger.info(f"🎨 UI-Widget: {type(view_widget).__name__}")
                
            except ImportError as import_error:
                logger.error(f"❌ Neue Architektur nicht verfügbar: {import_error}")
                import traceback
                logger.error(traceback.format_exc())
                self.show_text([
                    "❌ TEST FEHLER: Neue Architektur nicht verfügbar",
                    "",
                    f"Import-Fehler: {import_error}",
                    "",
                    f"View-GUID: {view_guid}",
                    f"Titel: {view_title}",
                    "",
                    "Module prüfen:",
                    "- pdvm_view_controller.py",
                    "- pdvm_view_ui.py"
                ], small=True)
            
        except Exception as e:
            logger.error(f"❌ TEST FEHLER: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            self.show_text([
                "❌ TEST FEHLER beim View-Laden",
                "",
                f"Frame-GUID: {frame_guid}",
                f"Fehler: {str(e)}",
                "",
                "Siehe main.log für Details"
            ], small=True)

    def start_dialog(self, frame_guid):
        """
        🎯 GENERELLER DIALOG - Herzstück für alle Datenänderungen
        
        Startet den universellen Dialog mit:
        - Tab 1: View (Datensatz-Übersicht)
        - Tab 2+: Edit-Bereiche (Inputcontrols, Menü-Editor, etc.)
        
        Der Dialog lädt die Konfiguration aus den Framedaten und zeigt
        die View an. Bei Auswahl eines Datensatzes werden die Edit-Bereiche
        mit den Daten befüllt.
        
        Args:
            frame_guid: GUID der Frame-Konfiguration
            
        Aufruf aus Menü:
            main_app.start_dialog("frame-guid-hier")
            
        Features:
        - ✅ Framedaten-basierte Konfiguration
        - ✅ View-Integration (Tab 1)
        - ✅ Datensatz-Auswahl → Edit-Bereiche
        - ✅ Stichtagsgenau
        - ✅ GCS-Integration
        """
        logger.info("🎯 === GENERELLER DIALOG - START ===")
        logger.info(f"📋 Frame-GUID: {frame_guid}")
        
        if not frame_guid:
            logger.error("❌ Keine frame_guid übergeben!")
            self.show_text([
                "❌ DIALOG FEHLER: Keine Frame-GUID",
                "",
                "Bitte frame_guid als Parameter übergeben:",
                "start_dialog('frame-guid-hier')"
            ], small=True)
            return

        try:
            logger.info("🔧 Initialisiere Generellen Dialog...")
            
            # 🔒 LAZY IMPORT: Dialog erst bei Bedarf laden
            from pdvm_genereller_dialog import PdvmGenerellerDialog
            
            # Inhalt löschen
            self.clear_content_layout()
            
            # Dialog erstellen mit frame_guid und Parent (Arbeitsbereich)
            dialog = PdvmGenerellerDialog(
                frame_guid=frame_guid,
                parent=self.content_frame,
                main_app=self  # ✅ MainApp-Referenz für Menü-Editor Module
            )
            
            # Dialog in Arbeitsbereich anzeigen
            self.workspace_layout.addWidget(dialog)
            
            # Dialog-Instanz speichern für spätere Operationen
            self.current_dialog = dialog
            
            logger.info(f"✅ GENERELLER DIALOG gestartet")
            logger.info(f"📊 Frame-GUID: {frame_guid}")
            logger.info(f"🏗️ Dialog-Instanz: {type(dialog).__name__}")
            
        except Exception as e:
            logger.error(f"❌ DIALOG FEHLER: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            self.show_text([
                "❌ FEHLER beim Dialog-Laden",
                "",
                f"Frame-GUID: {frame_guid}",
                f"Fehler: {str(e)}",
                "",
                "Siehe main.log für Details"
            ], small=True)

    def show_text_klein(self, text): 
        """Kleine Meldung unten anhängen."""
        # Einfache Implementierung: Zeige als normalen Text
        self._show_label(f"{text}", small=True, clear_content=True)

    def open_menu_editor(self, menu_type, call_path=None):
        """Öffnet den Menü-Editor für den angegebenen Menü-Typ."""
        try:
            logger.info(f"🔧 Öffne Menü-Editor für: {menu_type}")
            
            # ⚠️ DEAKTIVIERT - Menü-Editor noch nicht fertig (Post-0.9 Feature)
            # 🔒 LAZY IMPORT: Editor erst bei Bedarf laden
            # from pdvm_menu_editor import PdvmMenuEditor
            
            # Inhalt löschen
            self.clear_content_layout()
            
            # Platzhalter-Meldung
            logger.warning("⚠️ Menü-Editor noch nicht implementiert (Post-0.9 Feature)")
            # Editor instanziieren und anzeigen
            # editor = PdvmMenuEditor(self.content_frame, self.menu_handler.menu, menu_type, self, call_path)
            # self.workspace_layout.addWidget(editor)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Öffnen des Menü-Editors: {e}")
            self.show_text(f"❌ Fehler beim Öffnen des Menü-Editors:\n\n{str(e)}")

    # V3.1: DEPRECATED - Diese Methode ist bereits oben definiert

    def _clear_layout(self, layout):
        """Hilfsmethode zum rekursiven Löschen von Layouts"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def pdvm_dialog(self, dialog_guid, mode=0):
        """Öffnet einen PDVM-Dialog."""
        try:
            logger.info(f"🚀 Starte PDVM-Dialog: {dialog_guid}, Mode: {mode}")
            self.show_text(f"🔧 PDVM-Dialog wird gestartet...\n\nDialog-GUID: {dialog_guid}\nModus: {mode}")
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten des PDVM-Dialogs: {e}")
            self.show_text(f"❌ Fehler beim Starten des Dialogs:\n\n{str(e)}")

    def pdvm_enhanced_test(self):
        """Enhanced Multi-Tab Test."""
        try:
            logger.info("🚀 Starte Enhanced Multi-Tab Test")
            self.show_text("🔧 Enhanced Multi-Tab Test wird ausgeführt...")
        except Exception as e:
            logger.error(f"❌ Fehler beim Enhanced Multi-Tab Test: {e}")
            self.show_text(f"❌ Fehler beim Test:\n\n{str(e)}")

    def pdvm_enhanced_frame(self):
        """Enhanced Multi-Tab SOFORT."""
        try:
            logger.info("🚀 Starte Enhanced Multi-Tab SOFORT")
            self.show_text("🔧 Enhanced Multi-Tab SOFORT wird ausgeführt...")
        except Exception as e:
            logger.error(f"❌ Fehler beim Enhanced Multi-Tab SOFORT: {e}")
            self.show_text(f"❌ Fehler beim Enhanced Frame:\n\n{str(e)}")

    def reload_current_frame_enhanced(self):
        """Current Frame Enhanced Reload."""
        try:
            logger.info("🚀 Starte Current Frame Enhanced Reload")
            self.show_text("🔧 Current Frame Enhanced wird neu geladen...")
        except Exception as e:
            logger.error(f"❌ Fehler beim Current Frame Enhanced Reload: {e}")
            self.show_text(f"❌ Fehler beim Reload:\n\n{str(e)}")

    def open_app_menu(self, app_name):
        """Öffnet ein Anwendungsmenü."""
        try:
            logger.info(f"🚀 Öffne App-Menü: {app_name}")
            if app_name == "MeineApps":
                # Zurück zum Startmenü
                self.open_start_menu()
            else:
                self.show_text(f"🔧 App-Menü '{app_name}' wird geöffnet...")
        except Exception as e:
            logger.error(f"❌ Fehler beim Öffnen des App-Menüs: {e}")
            self.show_text(f"❌ Fehler beim Öffnen des App-Menüs:\n\n{str(e)}")

    def logout(self):
        """
        Meldet den Benutzer ab und startet das System neu.
        """
        try:
            logger.info("🔐 Benutzer-Abmeldung gestartet")
            
            # Kurze Abmelde-Nachricht anzeigen
            self.show_text([
                "🔐 Abmeldung...",
                "",
                "Sie werden abgemeldet.",
                "Das System wird neu gestartet."
            ], small=True)
            
            # Nach kurzer Verzögerung das Hauptfenster schließen
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(1500, self._perform_logout)  # 1.5s Verzögerung
            
        except Exception as e:
            logger.error(f"❌ Fehler bei der Abmeldung: {e}")
            self.show_text(f"❌ Fehler bei der Abmeldung:\n\n{str(e)}")
    
    def _perform_logout(self):
        """
        Führt die tatsächliche Abmeldung durch.
        """
        try:
            logger.info("🔄 Führe Abmeldung durch - starte System neu")
            
            # Hauptfenster schließen
            self.close()
            
            # V2.0: GCS zurücksetzen für Neustart
            try:
                from pdvm_central_systemsteuerung import reset_gcs
                reset_gcs()
                logger.info("🔄 V2 GCS zurückgesetzt für Neustart")
            except Exception as e:
                logger.warning(f"⚠️ GCS-Reset fehlgeschlagen: {e} - wird beim Neustart automatisch überschrieben")
            
            # V2.0: Neuen Hauptprozess starten
            import subprocess
            import sys
            import os
            
            # Starte pdvm_main.py in neuem Prozess (PDVM 0.9)
            python_exe = sys.executable
            main_script = os.path.join(os.getcwd(), "pdvm_main.py")
            
            logger.info(f"🚀 Starte V2.0 Login neu: {python_exe} {main_script}")
            subprocess.Popen([python_exe, main_script], cwd=os.getcwd())
            
            # Aktuellen Prozess beenden
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(500, lambda: sys.exit(0))
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Neustart: {e}")
            # Fallback: Einfach das Fenster schließen
            self.close()

    def pdvm_dialog(self, dialog_guid, mode=0, selected_id=None):
        """
        V2.0: Öffnet einen PDVM-Dialog im Arbeitsbereich (ersetzt aktuellen Inhalt)
        
        Args:
            dialog_guid: Frame-GUID aus sys_framedaten (enthält ROOT_TABLE, VIEW_GUID, DIALOG_GUID)
            mode: Dialog-Modus (0=neu, 1=bearbeiten, etc.)
            selected_id: ID des zu bearbeitenden Datensatzes
        """
        try:
            logger.info(f"🚀 V2.0: Öffne PDVM-Dialog im Arbeitsbereich")
            logger.info(f"  📋 Frame-GUID: {dialog_guid}")
            logger.info(f"  📋 Mode: {mode}, ID: {selected_id}")
            
            # V2-Genereller-Dialog importieren (vollständige Implementierung)
            from pdvm_genereller_dialog import V2PdvmGenerellerDialog
            
            # Verstecke aktuellen Content (welcome_widget) - mit Fehlerbehandlung
            if hasattr(self, 'welcome_widget') and self.welcome_widget:
                try:
                    # Prüfe ob Widget noch existiert (nicht deleted)
                    if not sip.isdeleted(self.welcome_widget):
                        self.welcome_widget.hide()
                        logger.debug("✅ Welcome-Widget versteckt")
                    else:
                        logger.debug("ℹ️ Welcome-Widget bereits gelöscht")
                except RuntimeError as e:
                    # Widget wurde bereits von Qt gelöscht
                    logger.debug(f"ℹ️ Welcome-Widget nicht mehr verfügbar: {e}")
            
            # Entferne altes Dialog-Widget falls vorhanden - mit Fehlerbehandlung
            if hasattr(self, 'current_dialog_widget') and self.current_dialog_widget:
                try:
                    if not sip.isdeleted(self.current_dialog_widget):
                        self.workspace_layout.removeWidget(self.current_dialog_widget)
                        self.current_dialog_widget.deleteLater()
                        logger.debug("✅ Altes Dialog-Widget entfernt")
                    else:
                        logger.debug("ℹ️ Altes Dialog-Widget bereits gelöscht")
                except RuntimeError as e:
                    logger.debug(f"ℹ️ Altes Dialog-Widget nicht mehr verfügbar: {e}")
            
            # V2-Dialog erstellen mit frame_guid (nicht dialog_guid!)
            # Frame enthält ROOT_TABLE, VIEW_GUID, DIALOG_GUID, HEADER_TEXT, EDIT_TYPE
            dialog_widget = V2PdvmGenerellerDialog(
                frame_guid=dialog_guid,  # ✅ frame_guid als Parameter
                parent=self.content_frame,
                main_app=self
            )
            
            # Dialog im Arbeitsbereich anzeigen - nimmt vollen Platz ein
            self.workspace_layout.addWidget(dialog_widget)
            self.current_dialog_widget = dialog_widget
            
            logger.info(f"✅ V2.0: Dialog im Arbeitsbereich angezeigt (voller Platz)")
            return True
            
        except Exception as e:
            logger.error(f"❌ V2.0: Fehler beim Öffnen des PDVM-Dialogs: {e}")
            import traceback
            traceback.print_exc()
            
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Dialog-Fehler",
                f"Fehler beim Öffnen des Dialogs:\n\n{str(e)}"
            )
            return False
    
    def remove_dialog_widget(self):
        """Entfernt aktuelles Dialog-Widget und zeigt wieder welcome_widget"""
        try:
            if hasattr(self, 'current_dialog_widget') and self.current_dialog_widget:
                logger.info("🔒 Entferne Dialog-Widget aus Arbeitsbereich")
                self.workspace_layout.removeWidget(self.current_dialog_widget)
                self.current_dialog_widget.deleteLater()
                self.current_dialog_widget = None
                
                # Zeige welcome_widget wieder an
                if hasattr(self, 'welcome_widget') and self.welcome_widget:
                    self.welcome_widget.show()
                    logger.info("✅ Welcome-Widget wieder angezeigt")
        except Exception as e:
            logger.error(f"❌ Fehler beim Entfernen des Dialog-Widgets: {e}")

    def toggle_menu_visibility(self):
        """
        Schaltet die Sichtbarkeit des vertikalen Menüs um.
        
        Entfernt oder fügt das vertikale Menü (menu_frame) zum Layout hinzu
        und gibt dem Content-Bereich den gesamten verfügbaren Platz.
        
        SICHERHEIT: STARTMENÜ darf nie umgeschaltet werden!
        """
        try:
            # SICHERHEIT: STARTMENÜ-Panel darf NIE umgeschaltet werden!
            current_menu_id = self._get_current_menu_id()
            startmenu_guid = self.gcs.get_menu_id('Startbereich')
            
            if current_menu_id == startmenu_guid:
                logger.warning(f"🚨 SICHERHEIT: STARTMENÜ-Panel darf nicht umgeschaltet werden!")
                return
            
            # Status-Variable für Menü-Sichtbarkeit initialisieren falls nicht vorhanden
            if not hasattr(self, '_menu_visible'):
                self._menu_visible = True
            
            if self._menu_visible:
                # Menü aus Layout entfernen
                self.main_layout.removeWidget(self.menu_frame)
                self.menu_frame.hide()
                logger.info("🎛️ Vollständige finale Vertikales Menü ausgeblendet - Content-Bereich vergrößert")
                self._menu_visible = False
            else:
                # Menü wieder zum Layout hinzufügen
                self.main_layout.insertWidget(0, self.menu_frame, 1)  # Position 0 = links
                self.menu_frame.show()
                logger.info("🎛️ Vollständige finale Vertikales Menü eingeblendet - Layout wiederhergestellt")
                self._menu_visible = True
            
            # Layout-Update erzwingen
            self.main_layout.update()
            QApplication.processEvents()
            
            # Aktuellen Status speichern
            self._save_menu_visibility_status()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Umschalten der vollständigen finalen Menü-Sichtbarkeit: {e}")

    def _load_and_apply_menu_visibility(self):
        """NUR FÜR APP-MENÜS - STARTMENÜ wird NIEMALS hier behandelt!"""
        try:
            if not hasattr(self, '_menu_visible'):
                self._menu_visible = True

            current_menu_id = self._get_current_menu_id()
            startmenu_guid = self.gcs.get_menu_id('Startbereich')
            
            # SICHERHEIT: Falls irrtümlich für STARTMENÜ aufgerufen - FEHLER!
            if current_menu_id == startmenu_guid:
                logger.error(f"🚨 FEHLER: _load_and_apply_menu_visibility() für STARTMENÜ aufgerufen! Das darf nicht passieren!")
                return
            
            # APP-MENÜS: Status aus GCS laden, Default = False (versteckt) beim ersten Aufruf
            menu_visible = self.gcs.get_menu_panel_visible(current_menu_id)  # Default = True falls nicht gesetzt
            self._menu_visible = menu_visible
            
            if self._menu_visible:
                self.main_layout.insertWidget(0, self.menu_frame, 1)
                self.menu_frame.show()
            else:
                self.main_layout.removeWidget(self.menu_frame)
                self.menu_frame.hide()
                
            self.main_layout.update()
            QApplication.processEvents()
            
            logger.info(f"📋 APP-MENÜ Panel-Status angewendet: {self._menu_visible} für Menü {current_menu_id}")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Menü-Status: {e}")
            # Fallback: Menü versteckt für APP-MENÜS
            self._menu_visible = False
            self.main_layout.removeWidget(self.menu_frame)
            self.menu_frame.hide()

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
        """Holt die aktuelle Menü-ID direkt aus dem Handler oder GCS"""
        if hasattr(self, 'menu_handler') and self.menu_handler:
            return self.menu_handler.menu_id
        
        # Fallback: Startmenü-GUID direkt aus GCS
        return self.gcs.get_menu_id('Startbereich')

    def toggle_menu_visibility(self):
        """
        V2.0: Schaltet die Sichtbarkeit des vertikalen Menüs um.
        
        Entfernt oder fügt das vertikale Menü zum Layout hinzu
        und gibt dem Content-Bereich den gesamten verfügbaren Platz.
        
        WICHTIG: Status wird persistent in GCS gespeichert pro Menü!
        """
        try:
            # Hole aktuelle Menü-GUID
            current_menu_guid = self.menu_handler.current_menu_guid if self.menu_handler else None
            
            if not current_menu_guid:
                logger.warning("⚠️ Keine Menü-GUID verfügbar für Toggle")
                return
            
            # Status umschalten
            if self._menu_visible:
                # Menü aus Layout entfernen
                self.work_area_layout.removeWidget(self.vertical_menu_container)
                self.vertical_menu_container.hide()
                logger.info("🎛️ V2.0: Vertikales Menü ausgeblendet - Content-Bereich vergrößert")
                self._menu_visible = False
            else:
                # Menü wieder zum Layout hinzufügen (Position 0 = links)
                self.work_area_layout.insertWidget(0, self.vertical_menu_container)
                self.vertical_menu_container.show()
                logger.info("🎛️ V2.0: Vertikales Menü eingeblendet - Layout wiederhergestellt")
                self._menu_visible = True
            
            # Layout-Update erzwingen
            from PyQt5.QtWidgets import QApplication
            self.work_area_layout.update()
            QApplication.processEvents()
            
            # Status persistent speichern (pro Menü!)
            self._save_menu_visibility_status()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Umschalten der V2.0 Menü-Sichtbarkeit: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_and_apply_menu_visibility(self, menu_guid):
        """
        V2.0: Lädt und wendet gespeicherten Menü-Sichtbarkeits-Status an.
        
        Args:
            menu_guid: GUID des aktuell geladenen Menüs
        """
        try:
            if not hasattr(self, '_menu_visible'):
                self._menu_visible = True
            
            # Status aus GCS laden (Default = True = sichtbar)
            menu_visible = self.gcs.get_menu_panel_visible(menu_guid)
            self._menu_visible = menu_visible
            
            if self._menu_visible:
                # Menü sichtbar machen
                if self.vertical_menu_container not in [self.work_area_layout.itemAt(i).widget() 
                                                          for i in range(self.work_area_layout.count())]:
                    self.work_area_layout.insertWidget(0, self.vertical_menu_container)
                self.vertical_menu_container.show()
            else:
                # Menü verstecken
                self.work_area_layout.removeWidget(self.vertical_menu_container)
                self.vertical_menu_container.hide()
            
            from PyQt5.QtWidgets import QApplication
            self.work_area_layout.update()
            QApplication.processEvents()
            
            logger.info(f"📋 V2.0: Menü-Status angewendet: {self._menu_visible} für Menü {menu_guid}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des V2.0 Menü-Status: {e}")
            import traceback
            traceback.print_exc()

    def _save_menu_visibility_status(self):
        """V2.0: Speichert Menü-Sichtbarkeits-Status in GCS"""
        try:
            current_menu_guid = self.menu_handler.current_menu_guid if self.menu_handler else None
            
            if not current_menu_guid:
                logger.debug("ℹ️ Keine Menü-GUID - kein Status zu speichern")
                return
            
            menu_visible = getattr(self, '_menu_visible', True)
            
            # Status in GCS speichern (persistiert automatisch in sys_systemsteuerung)
            self.gcs.set_menu_panel_visible(current_menu_guid, menu_visible)
            logger.info(f"💾 V2.0: Menü-Status gespeichert: {menu_visible} für Menü {current_menu_guid}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern des V2.0 Menü-Status: {e}")

def main():
    """Hauptfunktion für Demo-Zwecke"""
    app = QApplication(sys.argv)
    
    # Mock user data für Demo - entspricht dem ursprünglichen Format
    demo_user_data = [
        "demo@example.com",  # user_email 
        "",                  # unused
        {                    # user_daten dict
            "Benutzer": {
                "Vorname": "Demo",
                "Name": "Benutzer"
            },
            "Anwendungen": {
                "MeineApps": "demo-startmenu-guid",
                "Application": {
                    "DemoApp": {
                        "Name": "Demo Anwendung",
                        "Menu": "demo-view-guid"
                    }
                }
            }
        }, 
        "demo-user-guid"     # user_guid
    ]
    
    try:
        main_window = V2MainAppComplete()  # V2.0: Kein Parameter, nutzt GCS
        main_window.show()
        logger.info("🚀 V2.0 Hauptanwendung gestartet")
        return app.exec_()
    except Exception as e:
        logger.error(f"❌ Fehler beim Starten der V2.0 Hauptanwendung: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
