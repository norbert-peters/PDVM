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
        4. Controller-basierte View-Aktualisierung (NEUE ARCHITEKTUR)
        """
        try:
            logger.info("🔄 Vollständige Stichtag-Refresh gestartet...")
            
            # 1. Picker-Änderungen speichern (finale Architektur)
            if hasattr(self, 'stichtag_picker') and self.stichtag_picker:
                logger.info(f"📊 VOR save(): gcs.st_inst={gcs.st_inst.PdvmDateTime}, picker.initial={self.stichtag_picker.initial.PdvmDateTime}")
                
                if hasattr(self.stichtag_picker, 'save'):
                    self.stichtag_picker.save()
                    logger.info("💾 Vollständige Stichtag-Picker Änderungen gespeichert")
                    logger.info(f"📊 NACH save(): gcs.st_inst={gcs.st_inst.PdvmDateTime}")
                else:
                    logger.warning("⚠️ Vollständige Stichtag-Picker hat keine save()-Methode")
            
            # 2. Stichtag in finale GCS persistieren
            if gcs and hasattr(gcs, 'update_stichtag'):
                logger.info(f"📊 VOR update_stichtag(): gcs.st_inst={gcs.st_inst.PdvmDateTime}")
                gcs.update_stichtag()
                logger.info("💾 Stichtag erfolgreich in finale GCS persistiert")
            else:
                logger.warning("⚠️ Finale GCS nicht verfügbar oder update_stichtag() fehlt")
            
            # 3. Display aktualisieren (finale GCS)
            self._update_complete_stichtag_display()
            
            # 4. View-Aktualisierung über CONTROLLER (NEUE ARCHITEKTUR)
            # ✅ Stichtag ist bereits in GCS persistent → refresh() reicht!
            if hasattr(self, 'current_view_controller') and self.current_view_controller:
                logger.info("🔄 Aktualisiere aktuelle View nach Stichtag-Änderung...")
                
                if hasattr(self.current_view_controller, 'refresh'):
                    # refresh() holt sich den aktuellen Stichtag automatisch aus GCS
                    self.current_view_controller.refresh()
                    logger.info(f"✅ View erfolgreich aktualisiert (Stichtag aus GCS: {gcs.stichtag})")
                else:
                    logger.warning("⚠️ Controller hat keine refresh()-Methode")
                
                logger.info("✅ Vollständige Stichtag-Balken erfolgreich aktualisiert")
            
            # 5. Dialog-Aktualisierung (EDIT-BEREICH)
            # ✅ Falls ein genereller Dialog geöffnet ist, auch diesen aktualisieren
            if hasattr(self, 'current_dialog') and self.current_dialog:
                logger.info("🔄 Aktualisiere generellen Dialog nach Stichtag-Änderung...")
                
                if hasattr(self.current_dialog, 'refresh'):
                    # refresh() aktualisiert View UND Edit-Bereich
                    self.current_dialog.refresh()
                    logger.info(f"✅ Dialog erfolgreich aktualisiert (Stichtag aus GCS: {gcs.stichtag})")
                else:
                    logger.warning("⚠️ Dialog hat keine refresh()-Methode")
            
            # Fallback: Alte Widget-basierte Aktualisierung (für Kompatibilität)
            elif hasattr(self, 'current_view_widget') and self.current_view_widget:
                if hasattr(self.current_view_widget, 'reload'):
                    logger.info("🔄 Fallback: Aktualisiere View über Widget (alte Architektur)...")
                    self.current_view_widget.reload()
                    logger.info("✅ View erfolgreich nach Stichtag-Refresh aktualisiert (Widget-Fallback)")
                else:
                    logger.warning("⚠️ Aktuelle View hat keine reload()-Methode")
            else:
                logger.warning("⚠️ Keine View geladen für Stichtag-Aktualisierung")
                
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
                table_name="framedaten", 
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
                self.content_layout.addWidget(view_widget)
                
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
            self.content_layout.addWidget(dialog)
            
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
