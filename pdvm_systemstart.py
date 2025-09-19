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
                    'guid': self.user_guid,
                    'Vorname': vorname,
                    'Name': name,
                    'MeineApps': self.startmenu_id
                }
                
                logger.info(f"✅ Alle Benutzerdaten aus finaler GCS geladen")
                logger.info(f"🔹 E-Mail: {self.user_email}")
                logger.info(f"🔹 GUID: {self.user_guid}")
                logger.info(f"🔹 Startmenü-ID: {self.startmenu_id}")
                logger.info(f"🔹 Benutzername: {self.user_name}")
            else:
                logger.error("❌ Finale GCS nicht verfügbar - verwende Fallback-Werte")
                self.user_email = 'test@example.com'
                self.user_guid = 'unknown'
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
        
        # Hilfsfunktion für sicheren Zugriff auf finale GCS
        self._gcs_instance = None
        
        # ALLE Daten aus der finalen GCS beziehen - KEINE Parameter mehr!
        try:
            # Hole Benutzerdaten aus der finalen GCS
            if gcs and gcs.is_initialized:
                # Benutzer-E-Mail aus GCS
                self.user_email = gcs.get_property('email', 'u') or 'test@example.com'
                self.user_guid = gcs.user_guid
                
                # Startmenü-GUID aus GCS
                self.startmenu_id = gcs.get_menu_id('Startbereich') or "5ca6674e-b9ce-4581-9756-64e742883f80"
                
                # Benutzername für Titelleiste aus GCS
                vorname = gcs.get_property('Vorname', 'u') or ''
                name = gcs.get_property('Name', 'u') or ''
                self.user_name = f"{vorname} {name}".strip() or self.user_email
                
                # Kompatibilität: user_daten für bestehende Handler
                self.user_daten = {
                    'email': self.user_email,
                    'guid': self.user_guid,
                    'Vorname': vorname,
                    'Name': name,
                    'MeineApps': self.startmenu_id
                }
                
                logger.info(f"✅ Alle Benutzerdaten aus finaler GCS geladen")
                logger.info(f"🔹 E-Mail: {self.user_email}")
                logger.info(f"🔹 GUID: {self.user_guid}")
                logger.info(f"🔹 Startmenü-ID: {self.startmenu_id}")
                logger.info(f"🔹 Benutzername: {self.user_name}")
            else:
                logger.error("❌ Finale GCS nicht verfügbar - verwende Fallback-Werte")
                self.user_email = 'test@example.com'
                self.user_guid = 'unknown'
                self.user_name = 'Test Benutzer'
                self.startmenu_id = "5ca6674e-b9ce-4581-9756-64e742883f80"
                self.user_daten = {}
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Benutzerdaten aus GCS: {e}")
            self.user_email = 'test@example.com'
            self.user_guid = 'unknown'
            self.user_name = 'Test Benutzer'
            self.startmenu_id = "5ca6674e-b9ce-4581-9756-64e742883f80"
            self.user_daten = {}

        # Benutzername in der Titelleiste anzeigen
        self.setWindowTitle(f"PDVM System - Vollständige finale Hauptanwendung - {self.user_name}")

        logger.info(f"✅ Startmenü-GUID aus finaler GCS: {self.startmenu_id}")
        
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
        
        # FINALE GCS-INSTANZ ist bereits vom linearen Start initialisiert
        # Verwende die globale GCS direkt
        if gcs and gcs.is_initialized:
            logger.info("✅ Finale GCS bereits verfügbar - verwende bestehende Instanz")
            
            # Lade Benutzerdaten aus der globalen GCS
            self.user_guid = gcs.user_guid
            self.user_email = gcs.get_property('email', 'u') or 'test@example.com'
            vorname = gcs.get_property('Vorname', 'u') or ''
            name = gcs.get_property('Name', 'u') or ''
            self.user_name = f"{vorname} {name}".strip() or self.user_email
            self.startmenu_id = gcs.get_menu_id('Startbereich') or "5ca6674e-b9ce-4581-9756-64e742883f80"
            
            logger.info(f"✅ Alle Benutzerdaten aus finaler GCS geladen")
            logger.info(f"🔹 E-Mail: {self.user_email}")
            logger.info(f"🔹 GUID: {self.user_guid}")
            logger.info(f"🔹 Startmenü-ID: {self.startmenu_id}")
            logger.info(f"🔹 Benutzername: {self.user_name}")
        else:
            logger.warning("⚠️ Finale GCS noch nicht initialisiert")
            self._initialize_finale_gcs()
        
        # FINALE STICHTAG-BALKEN nach GCS-Initialisierung
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
        
        # Startmenü laden (DRY-Prinzip: Eine zentrale Methode für Startmenü)
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

    def _initialize_finale_gcs(self):
        """
        Initialisiert die finale GCS-Instanz für die gesamte Anwendung.
        
        FINALE SICHERHEITS-ARCHITEKTUR:
        - Finale GCS wird ERST nach Login mit user_guid erstellt
        - Verwendet pdvm_central_systemsteuerung_final.py
        - Keine Fallbacks auf "default_user" mehr!
        """
        try:
            if not self.user_guid:
                raise ValueError("❌ KRITISCH: user_guid fehlt! Login nicht erfolgreich.")
            
            logger.info(f"🎛️ Initialisiere finale GCS nach Login für User: {self.user_guid}")
            
            # FINALE GCS IMPORT
            from pdvm_central_systemsteuerung import initialize_gcs
            
            # ✅ FINALE SICHERE INITIALISIERUNG
            # Verwende die Benutzerdaten aus der globalen GCS falls verfügbar
            if gcs and gcs.is_initialized:
                user_data_for_init = gcs.user_data
                logger.info("✅ Verwende Benutzerdaten aus bereits initialisierter GCS")
            else:
                # Fallback: Verwende gespeicherte Benutzerdaten aus dem Login
                user_data_for_init = getattr(self, 'user_daten', None)
                if not user_data_for_init:
                    raise ValueError("❌ Keine Benutzerdaten verfügbar für GCS-Initialisierung!")
            
            success = initialize_gcs(self.user_guid, user_data_for_init)
            
            if success:
                logger.info(f"✅ Finale GCS sicher initialisiert")
                logger.info(f"🎯 Alle Werte verfügbar über finale Properties: st_inst, expert_mode, etc.")
                
                # Stichtag-Balken nach vollständiger Initialisierung aktualisieren
                self._refresh_complete_stichtag_bar_after_init()
            else:
                raise RuntimeError("Finale GCS-Initialisierung fehlgeschlagen")
            
        except Exception as e:
            logger.error(f"❌ KRITISCHER FEHLER bei finale GCS-Initialisierung: {e}")
            import traceback
            traceback.print_exc()
            # Nicht abbrechen - Fallback verwenden
            logger.warning("⚠️ Verwende Fallback-Modus ohne GCS")

    def _refresh_complete_stichtag_bar_after_init(self):
        """
        Aktualisiert den vollständigen Stichtag-Balken nach vollständiger Initialisierung.
        """
        try:
            if hasattr(self, 'stichtag_picker') and self.stichtag_picker:
                logger.info("🔄 Aktualisiere vollständigen Stichtag-Balken nach Initialisierung")
                
                if hasattr(self.stichtag_picker, 'update_display'):
                    self.stichtag_picker.update_display()
                self._update_complete_stichtag_display()
                
                logger.info("✅ Vollständiger Stichtag-Balken erfolgreich aktualisiert")
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
                db.guid = self.user_guid
                logger.info(f"✅ DB GUID gesetzt für Demo-Menü: {self.user_guid}")
            
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
        """Lädt erneut das Startmenü."""
        logger.info("🔹 open_start_menu() gestartet...")
        
        try:
            # 🔒 LAZY IMPORT: Handler erst nach Login laden
            logger.info("🔹 Importiere Handler-Module...")
            from pdvm_command_handler import PdvmCommandHandler
            from pdvm_menu_handler import PdvmMenuHandler
            logger.info("✅ Handler-Module erfolgreich importiert")
            
            # Handler nur initialisieren wenn noch nicht vorhanden (für __init__)
            if not hasattr(self, 'command_handler') or not self.command_handler:
                logger.info("🔹 Erstelle Command Handler...")
                self.command_handler = PdvmCommandHandler(self)
                logger.info("✅ Command Handler erstellt")
                
            logger.info(f"🔹 Erstelle Menu Handler mit Startmenu-ID: {self.startmenu_id}")
            self.menu_handler = PdvmMenuHandler(
                root=self,
                menu_widget=self.menu_frame,
                menu_id=self.startmenu_id,
                command_handler=self.command_handler
            )
            logger.info("✅ Menu Handler erstellt")
            
            logger.info("🔹 Erstelle Menüs...")
            self.menu_handler.create_menus()
            logger.info("✅ Menüs erstellt")
            
            self.setWindowTitle(f"PDVM System - Vollständige finale Hauptanwendung - {self.user_name}")
            
            # Zentraler Startbildschirm
            self._show_label("🔹 Willkommen im vollständigen finalen PDVM-System!", small=False, clear_content=True)
            self._show_label([
                "🔹 Bitte wählen Sie eine Anwendung aus dem Menü links.",
                "📱 Multi-Tab mit Navigation: F4 für parallele Tab-Anzeige → Navigation erscheint",
                "🔍 Lupe-Funktionen: F1 (View) | F2 (Input) | F3 (Reset)",
                "⌨️ Tab-Navigation: Ctrl+←/→ oder Alt+1-9 für direkten Tab-Zugriff"
            ], small=True, clear_content=False)
            
            # Startmenü: Menü immer anzeigen (Sicherheit)
            self._ensure_menu_visible()
            logger.info("🏠 Vollständiges Startmenü geladen - Menü automatisch eingeblendet")
            
        except ImportError as e:
            logger.error(f"❌ Import-Fehler bei Menü-Handler: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            # Fallback: Einfache Demo-Meldung
            self._show_label("🔹 Willkommen im vollständigen finalen PDVM-System!", small=False, clear_content=True)
            self._show_label([
                "⚠️ Menü-System nicht verfügbar (Import-Fehler)",
                f"Fehler: {e}",
                "🔧 System läuft im Basis-Modus"
            ], small=True, clear_content=False)
        except Exception as e:
            logger.error(f"❌ Allgemeiner Fehler beim Laden des Startmenüs: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            # Fallback: Einfache Demo-Meldung
            self._show_label("🔹 Willkommen im vollständigen finalen PDVM-System!", small=False, clear_content=True)
            self._show_label([
                "⚠️ Menü-System nicht verfügbar (Fehler)",
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
            
            logger.info(f"📋 Call-Daten vorbereitet: view_guid={view_guid}, user_guid={self.user_guid}, title='{view_title}'")

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
        """
        try:
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
        """Speichert den Menü-Sichtbarkeits-Status für das aktuelle Menü in der finale GCS."""
        try:
            if not gcs:
                logger.warning("⚠️ Finale GCS nicht verfügbar - Menü-Status wird nicht gespeichert")
                return

            current_menu_id = self._get_current_menu_id()
            menu_visible = getattr(self, '_menu_visible', True)

            # Finale GCS Persistierung
            gcs.field_value(f"menu_visible_{current_menu_id}", menu_visible)
            logger.info(f"💾 Vollständige finale Menü-Sichtbarkeits-Status gespeichert: {menu_visible} für Menü {current_menu_id}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern des vollständigen finalen Menü-Status: {e}")


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
