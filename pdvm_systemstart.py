#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDVM-Systemstart mi                # Benutzername für Titelleiste aus GCS
                vorname = gcs.get_property('Vorname', 'u') or ''
                name = gcs.get_property('Name', 'u') or ''
                self.user_name = f"{vorname} {name}".strip() or self.user_email
                
                # Kompatibilität: user_daten für bestehende Handler
                self.user_daten = {
                    'email': self.user_email,
                    'guid': gcs._user_guid,
                    'Vorname': vorname,
                    'Name': name,
                    'MeineApps': self.startmenu_id
                }
                
                logger.info(f"✅ Alle Benutzerdaten aus finaler GCS geladen")
                logger.info(f"🔹 E-Mail: {self.user_email}")
                logger.info(f"🔹 GUID: {gcs._user_guid}")
                logger.info(f"🔹 Startmenü-ID: {self.startmenu_id}")
                logger.info(f"🔹 Benutzername: {self.user_name}")
            else:
                logger.error("❌ Finale GCS nicht verfügbar - verwende Fallback-Werte")
                self.user_email = 'test@example.com'
                # Fallback entfernt - GCS ist jetzt erforderlich
                self.user_name = 'Test Benutzer'
                self.startmenu_id = "5ca6674e-b9ce-4581-9756-64e742883f80"
                self.user_daten = {}ursprünglicher Funktionalität + finale GCS-Integration

Kombiniert alle Features aus pdvm_systemstart.py mit der finalen GCS-Architektur
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

# 🔒 SICHERE IMPORTS: Nur grundlegende Komponenten - Handler werden lazy geladen
from global_gcs import gcs
from pdvm_central_datenbank import PdvmCentralDatenbank

class MainAppComplete(QMainWindow):
    """
    Vollständige MainApp-Implementation mit ursprünglicher Funktionalität.
    Kombiniert die finale GCS-Architektur mit allen Features aus pdvm_systemstart.py.
    
    Features:
    - ✅ Startmenü-System mit Apps
    - ✅ Menüsteuerung (ein-/ausblendbar)
    - ✅ Stichtag-Balken mit finale GCS-Integration
    - ✅ Command-Handler-System
    - ✅ View-Integration mit Multi-Tab
    - ✅ Menüeditor-Integration
    - ✅ Alle ursprünglichen Funktionalitäten
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDVM System - Vollständige finale Hauptanwendung")
        self.resize(1000, 600)
        
        # Prüfe GCS-Verfügbarkeit (ohne Fallbacks)
        if not gcs or not gcs.is_initialized:
            raise RuntimeError("❌ GCS muss vor MainApp initialisiert sein!")
        
        # Benutzername für Titelleiste direkt aus GCS
        # Debug: Verfügbare Benutzerdaten
        logger.info(f"🔍 Debug: Verfügbare Benutzerdaten-Gruppen: {list(gcs._u_db.data.keys()) if hasattr(gcs, '_u_db') and hasattr(gcs._u_db, 'data') else 'Keine'}")
        
        # Verwende neue hierarchische Abfrage-Methoden
        vorname = gcs.get_property('Vorname', 'u', 'Benutzer') or ''
        name = gcs.get_property('Name', 'u', 'Benutzer') or ''
        anrede = gcs.get_property('Anrede', 'u', 'Benutzer') or ''
        user_name = f"{anrede} {vorname} {name}".strip() or 'Unbekannt'
        self.setWindowTitle(f"PDVM System - Vollständige finale Hauptanwendung - {user_name}")

        logger.info(f"✅ Hauptanwendung gestartet für User: {gcs.user_guid}")
        
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
        try:
            from pdvm_command_handler import PdvmCommandHandler
            self.command_handler = PdvmCommandHandler(self)
        except ImportError as e:
            logger.warning(f"⚠️ Command Handler nicht verfügbar: {e}")
            self.command_handler = None
        
        # FINALE STICHTAG-BALKEN direkt aus GCS
        logger.info("🔧 Erstelle vollständigen Stichtag-Balken...")
        self.stichtag_bar = self._create_complete_stichtag_bar()
        if self.stichtag_bar:
            logger.info("✅ Vollständiger Stichtag-Balken erstellt, füge zu Layout hinzu...")
            self.content_layout.insertWidget(0, self.stichtag_bar)  # Am Anfang einfügen
            logger.info("✅ Vollständiger Stichtag-Balken erfolgreich zu Layout hinzugefügt")
        else:
            logger.error("❌ Vollständiger Stichtag-Balken konnte nicht erstellt werden!")
        
        # Separator-Line für optische Trennung
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.content_layout.insertWidget(1, separator)  # Nach Stichtag-Balken
        
        # STARTMENÜ laden (klar getrennt von App-Menüs)
        self.open_start_menu()

    def _create_complete_stichtag_bar(self):
        """
        Erstellt den vollständigen Stichtag-Balken für historische Datenansicht.
        
        Verwendet die finale GCS-Architektur mit gcs.st_inst.
        Layout: 'Stichtag:' (PdvmDateTimePicker) --> verwendeter Stichtag: (PdvmTimeStamp) [Refresh]
        
        Returns:
            QWidget: Vollständige Stichtag-Balken Widget
        """
        logger.info("🔧 _create_vollständigen_stichtag_bar gestartet...")
        
        from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QFrame
        from PyQt5.QtGui import QFont
        
        # Prüfe finale GCS direkt (vereinfacht)
        if not gcs:
            logger.error("❌ Finale GCS nicht verfügbar - kann Balken nicht erstellen")
            return QLabel("❌ Finale GCS nicht verfügbar")
        logger.info("✅ Finale GCS verfügbar")
        
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
            # Für finale GCS verwenden wir gcs.st_inst direkt
            try:
                from pdvm_date_time_picker import PdvmDateTimePicker
                self.stichtag_picker = PdvmDateTimePicker(
                    parent=self,
                    pdvm_datetime=gcs.st_inst,  # Finale GCS st_inst!
                    display="all",
                    display_time_short=False
                )
                logger.info(f"✅ Vollständige PdvmDateTimePicker Datum: {gcs.st_inst}") 
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
        Aktualisiert die Anzeige des verwendeten Stichtags mit finale GCS.
        """
        try:
            if gcs:
                # Finale GCS verwendet st_inst direkt
                stichtag_value = gcs.st_inst
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
        4. Optionale View-Aktualisierung
        """
        try:
            logger.info("🔄 Vollständige Stichtag-Refresh gestartet...")
            
            # 1. Picker-Änderungen speichern (finale Architektur)
            if hasattr(self, 'stichtag_picker') and self.stichtag_picker:
                if hasattr(self.stichtag_picker, 'save'):
                    self.stichtag_picker.save()
                    logger.info("💾 Vollständige Stichtag-Picker Änderungen gespeichert")
                else:
                    logger.warning("⚠️ Vollständige Stichtag-Picker hat keine save()-Methode")
            
            # 2. Stichtag in finale GCS persistieren
            if gcs and hasattr(gcs, 'update_stichtag'):
                gcs.update_stichtag()
                logger.info("💾 Stichtag erfolgreich in finale GCS persistiert")
            else:
                logger.warning("⚠️ Finale GCS nicht verfügbar oder update_stichtag() fehlt")
            
            # 3. Display aktualisieren (finale GCS)
            self._update_complete_stichtag_display()
            
            # 4. Optionale View-Aktualisierung falls vorhanden
            if hasattr(self, 'current_view_widget') and self.current_view_widget:
                if hasattr(self.current_view_widget, 'reload'):
                    logger.info("🔄 Aktualisiere aktuelle View nach Stichtag-Änderung...")
                    self.current_view_widget.reload()
                    logger.info("✅ View erfolgreich nach Stichtag-Refresh aktualisiert")
                else:
                    logger.warning("⚠️ Aktuelle View hat keine reload()-Methode")
                
                logger.info("✅ Vollständige Stichtag-Balken erfolgreich aktualisiert")
            else:
                logger.warning("⚠️ Vollständige Stichtag-Balken-Komponenten nicht verfügbar für Update")
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren des vollständigen Stichtag-Balkens: {e}")

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
                db.guid = gcs._user_guid
                logger.info(f"✅ DB GUID gesetzt für Demo-Menü: {gcs._user_guid}")
            
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
        self.content_layout.addSpacing(30)
        
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
            self.content_layout.addWidget(scroll_area)
            
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
                self.content_layout.addWidget(lbl)
        
        # Flexibler unterer Abstand (nimmt den restlichen Platz ein)
        self.content_layout.addStretch(1)

    def show_text(self, text, small=False):
        """Normaler Text im Hauptbereich."""
        self._show_label(f"{text}", small=small, clear_content=True)

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
        
        try:
            # Lazy Import - nur bei Bedarf laden
            from pdvm_menu_editor import PdvmMenuEditor
            
            # Inhalt löschen
            self.clear_content_layout()
            
            # Editor instanziieren und anzeigen
            editor = PdvmMenuEditor(self.content_frame, self.menu_handler.menu, menu_type, self, call_path)
            self.content_layout.addWidget(editor)
        except ImportError as e:
            logger.warning(f"⚠️ Menüeditor nicht verfügbar: {e}")
            self.show_text(f"⚠️ Menüeditor nicht verfügbar: {e}")

    def open_start_menu(self):
        """STARTMENÜ mit Berechtigungsprüfung - klar getrennt von App-Menüs"""
        logger.info("🏠 open_start_menu() - STARTMENÜ wird geladen...")
        
        try:
            # Startmenü-GUID direkt aus GCS (ohne Zwischenvariable)
            startmenu_guid = gcs.get_menu_id('Startbereich')
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
        Startet eine Anwendung basierend auf den Benutzer-Berechtigungen aus der GCS.
        
        Args:
            application_name: Name der Anwendung (z.B. "Testbereich", "Personalwesen")
        """
        try:
            logger.info(f"🚀 Starte Anwendung: {application_name}")
            
            # Hole Menü-GUID aus GCS-Benutzerdaten basierend auf App-Berechtigung
            try:
                # Prüfe Menü-Berechtigung für die Anwendung
                menu_guid = gcs.get_menu_id(application_name)
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

    def pdvm_modern_view(self, frame_guid, title=None):
        """
        🔧 FINALE VERSION: Moderne View-Dialog Integration für finale GCS
        
        Vereinfachte Dialog-basierte View-Architektur ohne set_menu_command.
        """
        if not frame_guid:
            logger.error("❌ Es wurde keine frame_guid übergeben!")
            self.show_text("❌ Fehler: Keine Frame-GUID übergeben")
            return

        try:
            logger.info(f"🚀 Starte moderne View für Frame: {frame_guid}")
            
            # Frame-Daten laden
            from pdvm_central_datenbank import PdvmCentralDatenbank
            framedaten_db = PdvmCentralDatenbank(
                table_name="framedaten", 
                guid=frame_guid
            )
            
            # View-GUID aus Frame-Daten ermitteln
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
                        logger.info(f"📝 Standard-Titel verwendet: {view_title}")
                except Exception as title_error:
                    logger.warning(f"⚠️ Fehler beim Titel-Laden: {title_error}")
                    view_title = f"View: {view_guid}"

            # call_daten für neuen Dialog vorbereiten - ALLE ERFORDERLICHEN Daten
            call_daten = {
                "view_guid": view_guid,
                "title": "Persönliche Daten",  # Immer einen Titel setzen!
                "first_call": True,  # Initialer Aufruf
            }
            
            logger.info(f"📋 Call-Daten vorbereitet: view_guid={view_guid}, user_guid={gcs._user_guid}, title='{view_title}'")

            # Vereinfachte Architektur ohne set_menu_command - direkte View-Dialog Erstellung
            try:
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
                
            except ImportError as import_error:
                logger.error(f"❌ PdvmViewDialog nicht verfügbar: {import_error}")
                self.show_text(f"🔧 View-Dialog wird geladen...\n\nView-GUID: {view_guid}\nTitel: {view_title}\n\n(PdvmViewDialog nicht verfügbar)")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten der modernen View: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Benutzerfreundliche Fehlermeldung anzeigen
            self.show_text(f"❌ Fehler beim Laden der View:\n\n{str(e)}")

    def show_text_klein(self, text):
        """Kleine Meldung unten anhängen."""
        # Einfache Implementierung: Zeige als normalen Text
        self._show_label(f"{text}", small=True, clear_content=True)

    def open_menu_editor(self, menu_type, call_path=None):
        """Öffnet den Menü-Editor für den angegebenen Menü-Typ."""
        try:
            logger.info(f"🔧 Öffne Menü-Editor für: {menu_type}")
            
            # 🔒 LAZY IMPORT: Editor erst bei Bedarf laden
            from pdvm_menu_editor import PdvmMenuEditor
            
            # Inhalt löschen
            self.clear_content_layout()
            
            # Editor instanziieren und anzeigen
            editor = PdvmMenuEditor(self.content_frame, self.menu_handler.menu, menu_type, self, call_path)
            self.content_layout.addWidget(editor)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Öffnen des Menü-Editors: {e}")
            self.show_text(f"❌ Fehler beim Öffnen des Menü-Editors:\n\n{str(e)}")

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
            
            # GCS zurücksetzen für Neustart
            try:
                from pdvm_central_systemsteuerung import _gcs_instance
                import pdvm_central_systemsteuerung
                pdvm_central_systemsteuerung._gcs_instance = None
                logger.info("🔄 GCS zurückgesetzt für Neustart")
            except:
                logger.warning("⚠️ GCS-Reset fehlgeschlagen - wird beim Neustart automatisch überschrieben")
            
            # Neuen Hauptprozess starten
            import subprocess
            import sys
            import os
            
            # Starte main.py in neuem Prozess
            python_exe = sys.executable
            main_script = os.path.join(os.getcwd(), "main.py")
            
            logger.info(f"🚀 Starte neuen Prozess: {python_exe} {main_script}")
            subprocess.Popen([python_exe, main_script], cwd=os.getcwd())
            
            # Aktuellen Prozess beenden
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(500, lambda: sys.exit(0))
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Neustart: {e}")
            # Fallback: Einfach das Fenster schließen
            self.close()

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
            startmenu_guid = gcs.get_menu_id('Startbereich')
            
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
            startmenu_guid = gcs.get_menu_id('Startbereich')
            
            # SICHERHEIT: Falls irrtümlich für STARTMENÜ aufgerufen - FEHLER!
            if current_menu_id == startmenu_guid:
                logger.error(f"🚨 FEHLER: _load_and_apply_menu_visibility() für STARTMENÜ aufgerufen! Das darf nicht passieren!")
                return
            
            # APP-MENÜS: Status aus GCS laden, Default = False (versteckt) beim ersten Aufruf
            menu_visible = gcs.get_menu_panel_visible(current_menu_id)  # Default = True falls nicht gesetzt
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
        return gcs.get_menu_id('Startbereich')

    def _save_menu_visibility_status(self):
        """Klare Trennung: NUR APP-MENÜS werden gespeichert, STARTMENÜ nie"""
        try:
            current_menu_id = self._get_current_menu_id()
            startmenu_guid = gcs.get_menu_id('Startbereich')
            menu_visible = getattr(self, '_menu_visible', True)

            # NUR APP-MENÜS speichern (STARTMENÜ wird nie gespeichert)
            if current_menu_id != startmenu_guid:
                gcs.set_menu_panel_visible(current_menu_id, menu_visible)
                logger.info(f"💾 APP-MENÜ Panel-Status gespeichert: {menu_visible} für Menü {current_menu_id}")
            else:
                logger.debug(f"🏠 STARTMENÜ - keine Speicherung (immer sichtbar)")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern des Menü-Status: {e}")

    def test_sortier_projektionen_diagnose(self):
        """
        🔧 CLEAN MATRIX-MANAGER SYSTEM-TEST
        
        Direkt im laufenden System - testet die 3 Debug-Matrizen:
        1. BASIS_MATRIX (beim Start/Stichtag)
        2. FILTERED_MATRIX (beim Filter) 
        3. SORTED_MATRIX (beim Sort)
        
        Aufruf über Menü im System - zeigt Live-Debug der Matrix-Pipeline
        """
        logger.info("🔧 CLEAN MATRIX-MANAGER SYSTEM-TEST gestartet...")
        
        try:
            self.clear_content_layout()
            
            ergebnisse = [
                "🔧 CLEAN MATRIX-MANAGER SYSTEM-TEST",
                "=" * 50,
                "",
                "Teste die 3 Matrix-Debug-Ausgaben direkt im System:",
                "• BASIS_MATRIX → beim Start/Stichtag",
                "• FILTERED_MATRIX → beim Filter", 
                "• SORTED_MATRIX → beim Sort",
                "",
                "SCHRITT 1: Clean Matrix-Manager erstellen",
                "-" * 50
            ]
            
            # SCHRITT 1: Clean Matrix-Manager erstellen
            try:
                from clean_matrix_manager import get_clean_matrix_manager, reset_matrix_managers
                
                # Reset für sauberen Test
                reset_matrix_managers()
                
                test_view_guid = "test_debug_view_12345"
                clean_manager = get_clean_matrix_manager(test_view_guid)
                
                ergebnisse.extend([
                    f"✅ Clean Matrix-Manager erstellt für: {test_view_guid}",
                    f"   Manager-Typ: {type(clean_manager).__name__}",
                    f"   View-GUID: {clean_manager.view_guid}",
                    ""
                ])
                
            except Exception as e:
                ergebnisse.extend([
                    f"❌ FEHLER beim Clean Matrix-Manager erstellen:",
                    f"   Error: {str(e)}",
                    ""
                ])
                self._show_label(ergebnisse, small=True, clear_content=True, max_height=500)
                return
            
            # SCHRITT 2: Test-Daten mit Debug-Spalten erstellen
            ergebnisse.extend([
                "SCHRITT 2: Test-Daten mit Debug-Spalten erstellen",
                "-" * 50
            ])
            
            # Test-Daten mit den kritischen Debug-Spalten
            test_data = [
                {
                    'uid_original': 'test-uid-001',
                    'vorname_original': 'Anna-Maria',
                    'vorname_show': 'Anna-Maria',
                    'geburtsdatum_original': '1985123.0',
                    'geburtsdatum_show': '03.05.1985',
                    'familienname': 'Mueller',
                    'strasse': 'Teststraße 1'
                },
                {
                    'uid_original': 'test-uid-002', 
                    'vorname_original': 'Peter-Klaus',
                    'vorname_show': 'Peter-Klaus',
                    'geburtsdatum_original': '1990067.0',
                    'geburtsdatum_show': '08.03.1990',
                    'familienname': 'Schmidt',
                    'strasse': 'Teststraße 2'
                },
                {
                    'uid_original': 'test-uid-003',
                    'vorname_original': 'Maria-Elisabeth', 
                    'vorname_show': 'Maria-Elisabeth',
                    'geburtsdatum_original': '1975298.0',
                    'geburtsdatum_show': '25.10.1975',
                    'familienname': 'Lauer',
                    'strasse': 'Teststraße 3'
                }
            ]
            
            test_columns = list(test_data[0].keys())
            
            ergebnisse.extend([
                f"✅ Test-Daten erstellt: {len(test_data)} Zeilen",
                f"   Spalten: {len(test_columns)} → {test_columns[:3]}...",
                f"   Debug-Spalten enthalten: uid_original, vorname_original, vorname_show",
                ""
            ])
            
            # SCHRITT 3: BASIS_MATRIX Test
            ergebnisse.extend([
                "SCHRITT 3: BASIS_MATRIX Test (Start/Stichtag)",
                "-" * 50,
                "→ Erwarte: DEBUG BASIS_MATRIX im Log mit 3 Zeilen Test-Daten",
                ""
            ])
            
            try:
                # BASIS_MATRIX setzen → sollte DEBUG-Ausgabe erzeugen
                clean_manager.set_basis_data(test_data, test_columns)
                
                ergebnisse.extend([
                    f"✅ BASIS_MATRIX gesetzt → Debug-Ausgabe im Log",
                    f"   Zeilen: {len(clean_manager.basis_matrix)}",
                    f"   Spalten: {len(clean_manager.columns)}",
                    ""
                ])
                
            except Exception as e:
                ergebnisse.extend([
                    f"❌ FEHLER bei BASIS_MATRIX:",
                    f"   Error: {str(e)}",
                    ""
                ])
            
            # SCHRITT 4: FILTERED_MATRIX Test
            ergebnisse.extend([
                "SCHRITT 4: FILTERED_MATRIX Test (Filter-Änderung)",
                "-" * 50,
                "→ Erwarte: DEBUG FILTERED_MATRIX im Log (linear!)",
                ""
            ])
            
            try:
                # Filter anwenden → sollte nur FILTERED_MATRIX Debug erzeugen
                clean_manager.apply_filter()
                
                ergebnisse.extend([
                    f"✅ FILTERED_MATRIX angewendet → Debug-Ausgabe im Log",
                    f"   Gefilterte Zeilen: {len(clean_manager.filtered_matrix)}",
                    ""
                ])
                
            except Exception as e:
                ergebnisse.extend([
                    f"❌ FEHLER bei FILTERED_MATRIX:",
                    f"   Error: {str(e)}",
                    ""
                ])
            
            # SCHRITT 5: SORTED_MATRIX Test
            ergebnisse.extend([
                "SCHRITT 5: SORTED_MATRIX Test (Sort-Änderung)",
                "-" * 50,
                "→ Erwarte: DEBUG SORTED_MATRIX im Log (linear!)",
                ""
            ])
            
            try:
                # Sortierung anwenden → sollte nur SORTED_MATRIX Debug erzeugen
                clean_manager.apply_sort('vorname_original', True)
                
                ergebnisse.extend([
                    f"✅ SORTED_MATRIX angewendet → Debug-Ausgabe im Log",
                    f"   Sortierte Zeilen: {len(clean_manager.sorted_matrix)}",
                    f"   Sort-Spalte: vorname_original (aufsteigend)",
                    ""
                ])
                
            except Exception as e:
                ergebnisse.extend([
                    f"❌ FEHLER bei SORTED_MATRIX:",
                    f"   Error: {str(e)}",
                    ""
                ])
            
            # SCHRITT 6: Status und finale Daten
            ergebnisse.extend([
                "SCHRITT 6: Matrix-Status und finale Daten",
                "-" * 50
            ])
            
            try:
                status = clean_manager.get_status()
                final_data = clean_manager.get_final_data()
                
                ergebnisse.extend([
                    f"📊 Matrix-Status:",
                    f"   View-GUID: {status['view_guid']}",
                    f"   BASIS: {status['basis']['rows']} Zeilen, {status['basis']['columns']} Spalten",
                    f"   FILTERED: {status['filtered']['rows']} Zeilen", 
                    f"   SORTED: {status['sorted']['rows']} Zeilen",
                    f"   Erste Spalten: {status['columns']}",
                    "",
                    f"🎯 Finale Daten: {len(final_data)} Zeilen für View-Anzeige",
                    ""
                ])
                
                # Zeige erste sortierte Zeile als Beispiel
                if final_data:
                    first_row = final_data[0]
                    ergebnisse.extend([
                        f"📋 Erste sortierte Zeile (Beispiel):",
                        f"   vorname_original: {first_row.get('vorname_original', 'N/A')}",
                        f"   vorname_show: {first_row.get('vorname_show', 'N/A')}",
                        f"   geburtsdatum_original: {first_row.get('geburtsdatum_original', 'N/A')}",
                        f"   geburtsdatum_show: {first_row.get('geburtsdatum_show', 'N/A')}",
                        ""
                    ])
                
            except Exception as e:
                ergebnisse.extend([
                    f"❌ FEHLER bei Status-Abfrage:",
                    f"   Error: {str(e)}",
                    ""
                ])
            
            # ZUSAMMENFASSUNG
            ergebnisse.extend([
                "ERWARTETE LOG-AUSGABEN:",
                "=" * 50,
                "",
                "Im main.log sollten jetzt erscheinen:",
                "",
                "1. DEBUG BASIS_MATRIX (3 Zeilen):",
                "   📋 Debug-Spalten: uid_original | vorname_original | vorname_show | ...",
                "   📄 Zeile 1: test-uid-001 | Anna-Maria | Anna-Maria | ...",
                "   📄 Zeile 2: test-uid-002 | Peter-Klaus | Peter-Klaus | ...",
                "   📄 Zeile 3: test-uid-003 | Maria-Elisabeth | Maria-Elisabeth | ...",
                "",
                "2. DEBUG FILTERED_MATRIX (3 Zeilen):",
                "   📋 Debug-Spalten: uid_original | vorname_original | vorname_show | ...",
                "   📄 Zeile 1: [gefilterte Daten]",
                "   📄 Zeile 2: [gefilterte Daten]", 
                "   📄 Zeile 3: [gefilterte Daten]",
                "",
                "3. DEBUG SORTED_MATRIX (3 Zeilen, sortiert nach vorname_original):",
                "   📋 Debug-Spalten: uid_original | vorname_original | vorname_show | ...",
                "   📄 Zeile 1: [sortierte Daten]",
                "   📄 Zeile 2: [sortierte Daten]",
                "   📄 Zeile 3: [sortierte Daten]",
                "",
                "🎯 LINEAR: Jede Matrix nur bei ihrer Änderung geloggt!",
                "",
                "📋 Prüfen Sie das main.log für die Debug-Ausgaben!",
                "🔧 Falls keine Debug-Ausgaben → Clean Matrix-Manager Problem",
                "✅ Falls alle 3 Debug-Ausgaben da → Matrix-System funktioniert!"
            ])
            
            # Ergebnisse anzeigen
            self._show_label(ergebnisse, small=True, clear_content=True, max_height=600)
            
            logger.info("✅ CLEAN MATRIX-MANAGER SYSTEM-TEST abgeschlossen - prüfen Sie main.log!")
            
        except Exception as e:
            logger.error(f"❌ Kritischer Fehler im Clean Matrix-Manager System-Test: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            self._show_label([
                "❌ KRITISCHER FEHLER im Clean Matrix-Manager Test",
                "",
                f"Error: {str(e)}",
                "",
                "Siehe main.log für Details"
            ], small=True, clear_content=True)


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
        main_window = MainAppComplete(demo_user_data)
        main_window.show()
        logger.info("🚀 Vollständige finale Hauptanwendung gestartet")
        return app.exec_()
    except Exception as e:
        logger.error(f"❌ Fehler beim Starten der vollständigen finalen Hauptanwendung: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
