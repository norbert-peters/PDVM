#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 PDVM GENERELLER DIALOG - Herzstück für alle Datenänderungen

Universeller Dialog für:
- Datensatz-Anzeige (View im Tab 1)
- Datensatz-Bearbeitung (Edit-Bereiche in Tab 2+)
- Inputcontrols, Menü-Editor, Benutzerkonten, Frame Input, View Input

Architektur:
- Tab 1: View (Übersicht aller Datensätze)
- Tab 2+: Edit-Bereiche (stichtagsgenau, basierend auf ausgewähltem Datensatz)

Features:
- ✅ Framedaten-basierte Konfiguration (framedaten.db)
- ✅ View-Integration
- ✅ Datensatz-Auswahl → Edit-Bereiche
- ✅ Stichtagsgenau
- ✅ GCS-Integration
- ✅ Persistierung in dialogdaten.db (NICHT anwendungsdaten!)

Datenbank-Nutzung:
- framedaten.db: Frame-Konfiguration (TABLE, VIEW_GUID, DIALOG_GUID, HEADER_TEXT)
- dialogdaten.db: Dialog-Status (Tab-Einstellungen, selected_guid)
- anwendungsdaten.db: NUR über GCS für User-bezogene Daten (View-Filter, etc.)

Version: 1.0.0 (Grundgerüst)
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QPushButton, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from pdvm_central_systemsteuerung import get_gcs
from pdvm_central_datenbank import PdvmCentralDatenbank  # V2: Datenbank!

logger = logging.getLogger(__name__)


class V2PdvmGenerellerDialog(QWidget):
    """
    🎯 V2 Genereller Dialog für alle Datenänderungen
    
    Workflow:
    1. Frame-GUID → sys_framedaten laden (TABLE, VIEW_GUID, DIALOG_GUID, HEADER_TEXT)
    2. DIALOG_GUID → sys_dialogdaten laden/erstellen (Tab-Konfiguration)
    3. Tab 1: View initialisieren
    4. Tab 2: Edit-Bereich (Phase 1: nur GUID-Anzeige)
    5. Datensatz-Auswahl → Tab 2 öffnen + GUID übergeben
    """
    
    # Signal wenn Datensatz ausgewählt wird
    datensatz_ausgewaehlt = pyqtSignal(str)  # GUID des ausgewählten Datensatzes
    
    def __init__(self, frame_guid, parent=None, main_app=None):
        """
        Initialisiert den Generellen Dialog
        
        Args:
            frame_guid: GUID der Frame-Konfiguration
            parent: Parent-Widget (Arbeitsbereich des Systems)
            main_app: Referenz zur MainAppComplete (für Menü-Editor Module)
        """
        super().__init__(parent)
        
        logger.info("🎯 === GENERELLER DIALOG - INITIALISIERUNG ===")
        logger.info(f"📋 Frame-GUID: {frame_guid}")
        
        # V2: GCS holen und prüfen
        self.gcs = get_gcs()
        if not self.gcs or not self.gcs.is_initialized:
            raise RuntimeError("❌ GCS muss initialisiert sein!")
        
        self.frame_guid = frame_guid
        self.main_app = main_app  # ✅ MainApp-Referenz speichern
        
        # Framedaten-Instanz
        self.framedaten_db = None
        
        # Dialogdaten-Instanz
        self.dialogdaten_db = None
        
        # Konfiguration aus Framedaten
        self.root_table = None
        self.view_guid = None
        self.dialog_guid = None
        self.header_text = None
        
        # UI-Komponenten
        self.tab_widget = None
        self.view_controller = None
        # Current selected GUID (wird bei Datensatz-Auswahl gesetzt)
        self.current_selected_guid = None
        
        # MODUL-REGISTRY: edit_type → Modul-Klasse
        # Einfache Erweiterbarkeit: Neues Modul einfach hier eintragen!
        # GCS wird NICHT übergeben → globaler Import in jedem Modul!
        self.edit_modules = {
            'input_controls': 'pdvm_input_controls_manager.PdvmInputControlsManager',  # ✅ PDVM 0.9 VERSION
            'menu_editor': 'pdvm_menu_editor_module.PdvmMenuEditorModule',  # ✅ Menü-Editor Integration
            'system_editor': 'pdvm_system_editor.PdvmSystemEditor',  # ✅ UNIVERSELL: Alle System-Tabellen (sys_viewdaten, sys_framedaten, etc.)
            # Weitere Module können hier hinzugefügt werden:
            # 'advanced_edit': 'pdvm_advanced_edit_module.PdvmAdvancedEditModule',
            # 'custom_form': 'pdvm_custom_form_module.PdvmCustomFormModule',
        }
        
        logger.info(f"  📋 {len(self.edit_modules)} Edit-Module registriert")
        
        # Signal-Verbindung
        self.datensatz_ausgewaehlt.connect(self._on_datensatz_ausgewaehlt)
        
        # ✅ KRITISCH: Stichtag-Signal verbinden für Input Controls Refresh
        # Der View-Controller verbindet sich automatisch selbst,
        # aber die Input Controls im Edit-Tab brauchen eine Verbindung
        if hasattr(self.gcs, 'stichtag_changed'):
            self.gcs.stichtag_changed.connect(self._on_stichtag_changed)
            logger.info("  🔗 stichtag_changed Signal verbunden → Dialog Refresh")
        
        # Initialisierung
        try:
            self._init_ui()
            self._load_framedaten()
            self._load_or_create_dialogdaten()
            self._init_tabs()
            
            logger.info("✅ Genereller Dialog erfolgreich initialisiert")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Initialisierung: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def _init_ui(self):
        """Initialisiert das Grund-Layout"""
        logger.info("🔧 Initialisiere UI...")
        
        # Haupt-Layout (vertikal)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header-Frame (wird nach Framedaten-Ladung befüllt)
        self.header_frame = QFrame()
        self.header_frame.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-bottom: 2px solid #34495e;
            }
        """)
        self.header_layout = QHBoxLayout(self.header_frame)
        self.header_layout.setContentsMargins(15, 10, 15, 10)
        
        # Header-Label (Platzhalter)
        self.header_label = QLabel("Lade Dialog...")
        self.header_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        self.header_layout.addWidget(self.header_label)
        self.header_layout.addStretch()
        
        layout.addWidget(self.header_frame)
        
        # Tab-Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-top: 2px solid #3498db;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 10px 20px;
                margin-right: 2px;
                border: 1px solid #bdc3c7;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid white;
            }
            QTabBar::tab:hover {
                background-color: #d5dbdb;
            }
        """)
        
        layout.addWidget(self.tab_widget)
        
        logger.info("✅ UI-Grundstruktur erstellt")
    
    def _load_framedaten(self):
        """
        Lädt die Framedaten aus der Datenbank
        
        Liest aus Gruppe ROOT:
        - TABLE: Tabellenname für Daten
        - VIEW_GUID: GUID der View-Konfiguration
        - DIALOG_GUID: GUID für Dialog-Persistierung
        - HEADER_TEXT: Überschrift des Dialogs
        """
        logger.info("📂 Lade Framedaten...")
        
        try:
            # V2: sys_framedaten-DB Instanz erstellen mit frame_guid
            self.framedaten_db = PdvmCentralDatenbank('sys_framedaten', self.frame_guid)
            
            # ROOT-Gruppe lesen
            gruppe = 'ROOT'
            
            # TABLE (neue lineare Struktur)
            # V2: Framedaten ist NICHT historisch → get_static_value
            self.root_table = self.framedaten_db.get_static_value(
                gruppe, 'TABLE'
            )
            logger.info(f"  📋 TABLE: {self.root_table}")
            
            # VIEW_GUID
            self.view_guid = self.framedaten_db.get_static_value(
                gruppe, 'VIEW_GUID'
            )
            logger.info(f"  📋 VIEW_GUID: {self.view_guid}")
            
            # DIALOG_GUID
            self.dialog_guid = self.framedaten_db.get_static_value(
                gruppe, 'DIALOG_GUID'
            )
            logger.info(f"  📋 DIALOG_GUID: {self.dialog_guid}")
            
            # HEADER_TEXT
            self.header_text = self.framedaten_db.get_static_value(
                gruppe, 'HEADER_TEXT'
            )
            logger.info(f"  📋 HEADER_TEXT: {self.header_text}")
            
            # EDIT_TYPE
            self.edit_type = self.framedaten_db.get_static_value(
                gruppe, 'EDIT_TYPE'
            )
            if not self.edit_type:
                self.edit_type = 'input_controls'  # Default
            logger.info(f"  📋 EDIT_TYPE: {self.edit_type}")
            
            # Validierung
            if not self.root_table:
                raise ValueError("TABLE ist leer!")
            if not self.view_guid:
                raise ValueError("VIEW_GUID ist leer!")
            # DIALOG_GUID kann leer sein (wird dann erstellt)
            
            # Header-Label aktualisieren
            if self.header_text:
                self.header_label.setText(self.header_text)
            else:
                self.header_label.setText(f"Dialog: {self.frame_guid[:8]}...")
            
            logger.info("✅ Framedaten erfolgreich geladen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Framedaten: {e}")
            raise
    
    def _load_or_create_dialogdaten(self):
        """
        Lädt oder erstellt die Dialogdaten
        
        Dialogdaten persistieren:
        - Gruppe ROOT: Dialog-weite Parameter (z.B. letzter aktiver Tab)
        - Gruppe Tab(nn): Parameter pro Tab (z.B. Sichtbarkeit, Position)
        """
        logger.info("📂 Lade/Erstelle Dialogdaten...")
        
        try:
            if not self.dialog_guid:
                # DIALOG_GUID ist leer → neue GUID generieren
                import uuid
                self.dialog_guid = str(uuid.uuid4())
                logger.info(f"  🆕 Neue DIALOG_GUID erstellt: {self.dialog_guid}")
                
                # DIALOG_GUID in Framedaten speichern
                self.framedaten_db.set_value(
                    'ROOT', 'DIALOG_GUID', self.dialog_guid
                )
                self.framedaten_db.save_all_values()
                logger.info("  💾 DIALOG_GUID in Framedaten gespeichert")
            
            # V2: Dialogdaten-DB Instanz erstellen
            # WICHTIG: Verwende 'sys_dialogdaten' Datenbank mit DIALOG_GUID
            # NICHT 'anwendungsdaten' - das ist nur für User-bezogene Daten über GCS!
            self.dialogdaten_db = PdvmCentralDatenbank('sys_dialogdaten', self.dialog_guid)
            
            # Prüfen ob ROOT-Gruppe existiert (via get_static_value - dialogdaten ist NICHT historisch)
            # V2: Feldnamen in GROSSBUCHSTABEN!
            active_tab_test = self.dialogdaten_db.get_static_value('ROOT', 'ACTIVE_TAB')
            root_exists = (active_tab_test is not None)
            
            if not root_exists:
                logger.info("  🆕 Erstelle initiale Dialogdaten...")
                
                # Initiale ROOT-Parameter (V2: GROSSBUCHSTABEN!)
                self.dialogdaten_db.set_value('ROOT', 'ACTIVE_TAB', 0)
                self.dialogdaten_db.set_value('ROOT', 'TAB_COUNT', 2)
                
                # Tab01 Parameter (View) - V2: Gruppe GROSS, Felder klein!
                self.dialogdaten_db.set_value('TAB01', 'tab_type', 'view')
                self.dialogdaten_db.set_value('TAB01', 'tab_title', 'Übersicht')
                self.dialogdaten_db.set_value('TAB01', 'view_guid', self.view_guid)
                
                # Tab02 Parameter (Edit) - V2: Gruppe GROSS, Felder klein!
                self.dialogdaten_db.set_value('TAB02', 'tab_type', 'edit')
                self.dialogdaten_db.set_value('TAB02', 'tab_title', 'Bearbeiten')
                self.dialogdaten_db.set_value('TAB02', 'selected_guid', None)
                
                self.dialogdaten_db.save_all_values()
                logger.info("  ✅ Initiale Dialogdaten erstellt")
            else:
                logger.info("  ✅ Dialogdaten existieren bereits")
            
            logger.info("✅ Dialogdaten erfolgreich geladen/erstellt")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Dialogdaten: {e}")
            raise
    
    def _init_tabs(self):
        """Initialisiert die Tabs basierend auf Dialogdaten"""
        logger.info("🔧 Initialisiere Tabs...")
        
        try:
            # Tab-Anzahl aus Dialogdaten (V2: GROSSBUCHSTABEN + get_static_value!)
            tab_count = self.dialogdaten_db.get_static_value('ROOT', 'TAB_COUNT')
            tab_count = int(tab_count) if tab_count else 2
            
            logger.info(f"  📊 Tab-Anzahl: {tab_count}")
            
            # Tab 1: View (IMMER vorhanden)
            self._create_view_tab()
            
            # Tab 2: Edit-Bereich (Phase 1: nur GUID-Anzeige)
            self._create_edit_tab()
            
            # === FEATURE: Letzte GUID aus Systemsteuerung laden ===
            # Wenn eine GUID für diesen Frame gespeichert ist → direkt Edit öffnen
            # V2: Verwende get_value für Konsistenz mit set_value
            last_guid, _ = self.gcs._db.get_value(self.frame_guid, 'LAST_SELECTION')
            
            if last_guid:
                logger.info(f"🔍 Letzte ausgewählte GUID gefunden: {last_guid}")
                logger.info(f"  → Öffne direkt Edit-Tab für diese GUID")
                
                # GUID setzen und Edit-Bereich laden
                self._on_datensatz_ausgewaehlt(last_guid)
                
                # Direkt zu Tab 2 (Edit) wechseln
                self.tab_widget.setCurrentIndex(1)
                logger.info("  ✅ Edit-Tab direkt geöffnet mit letzter GUID")
            else:
                # Kein Last-GUID → IMMER Tab 0 (View) öffnen
                self.tab_widget.setCurrentIndex(0)
                logger.info("  ✅ Keine gespeicherte GUID → Tab 0 (View) geöffnet")
            
            # Signal bei Tab-Wechsel
            self.tab_widget.currentChanged.connect(self._on_tab_changed)
            
            logger.info("✅ Tabs erfolgreich initialisiert")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Tab-Initialisierung: {e}")
            raise
    
    def _create_view_tab(self):
        """Erstellt Tab 1 mit der View"""
        logger.info("🔧 Erstelle View-Tab...")
        
        try:
            # Tab-Titel aus Dialogdaten (V2: Gruppe GROSS, Feld klein!)
            tab_title = self.dialogdaten_db.get_static_value('TAB01', 'tab_title')
            tab_title = tab_title or 'Übersicht'
            
            # View-Container
            view_container = QWidget()
            view_layout = QVBoxLayout(view_container)
            view_layout.setContentsMargins(0, 0, 0, 0)
            
            # === NEU-BUTTON (über View) ===
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            btn_neu = QPushButton("➕ Neuer Datensatz")
            btn_neu.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    font-weight: bold;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #2ecc71;
                }
            """)
            btn_neu.clicked.connect(self._create_new_datensatz)
            button_layout.addWidget(btn_neu)
            
            view_layout.addLayout(button_layout)
            
            # V2: View-Controller initialisieren
            from pdvm_view_controller import V2PdvmViewController
            
            # call_daten für View (wie in test_pdvm_view)
            call_daten = {
                'frame_guid': self.frame_guid,
                'view_guid': self.view_guid,
                'root_table': self.root_table,
                'title': tab_title
            }
            
            self.view_controller = V2PdvmViewController(call_daten, parent=view_container)
            
            # View initialisieren
            init_success = self.view_controller.initialize()
            
            if not init_success:
                raise RuntimeError("View-Controller-Initialisierung fehlgeschlagen")
            
            # View-Widget holen
            view_widget = self.view_controller.get_widget()
            
            if not view_widget:
                raise RuntimeError("Kein Widget vom View-Controller erhalten")
            
            # View-Widget in Container einfügen
            view_layout.addWidget(view_widget)
            
            # Signal-Verbindung: Datensatz ausgewählt
            # WICHTIG: View muss Signal bereitstellen (z.B. row_double_clicked)
            if hasattr(self.view_controller, 'row_double_clicked'):
                self.view_controller.row_double_clicked.connect(self._on_view_row_selected)
                logger.info("  ✅ Signal 'row_double_clicked' verbunden")
            else:
                logger.warning("  ⚠️ View-Controller hat kein 'row_double_clicked' Signal")
            
            # Tab hinzufügen
            self.tab_widget.addTab(view_container, tab_title)
            
            logger.info(f"✅ View-Tab erstellt: '{tab_title}'")
            logger.info(f"  📊 View-GUID: {self.view_guid}")
            logger.info(f"  📋 Root-Table: {self.root_table}")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei View-Tab-Erstellung: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Fallback: Zeige Fehler im Tab
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel(f"❌ Fehler beim Laden der View:\n\n{str(e)}")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("color: red; font-size: 14px;")
            error_layout.addWidget(error_label)
            
            self.tab_widget.addTab(error_widget, "⚠️ Fehler")
    
    def _create_edit_tab(self):
        """Erstellt Tab 2 mit Edit-Bereich (Phase 2.2: PdvmEditManager Integration)"""
        logger.info("🔧 Erstelle Edit-Tab...")
        
        try:
            # Tab-Titel aus Dialogdaten (V2: Gruppe GROSS, Feld klein!)
            tab_title = self.dialogdaten_db.get_static_value('TAB02', 'tab_title')
            tab_title = tab_title or 'Bearbeiten'
            
            # Edit-Container (wird später befüllt)
            self.edit_container = QWidget()
            self.edit_layout = QVBoxLayout(self.edit_container)
            self.edit_layout.setContentsMargins(20, 20, 20, 20)
            
            # Platzhalter-Widget (angezeigt bis Datensatz ausgewählt)
            self.edit_placeholder = QWidget()
            placeholder_layout = QVBoxLayout(self.edit_placeholder)
            
            info_label = QLabel(
                "ℹ️ Edit-Bereich\n\n"
                "Wählen Sie einen Datensatz in der Übersicht aus,\n"
                "um ihn hier zu bearbeiten."
            )
            info_label.setAlignment(Qt.AlignCenter)
            info_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #7f8c8d;
                    padding: 40px;
                }
            """)
            placeholder_layout.addWidget(info_label)
            placeholder_layout.addStretch()
            
            # Platzhalter initial anzeigen
            self.edit_layout.addWidget(self.edit_placeholder)
            
            # Edit-Manager (wird bei Datensatz-Auswahl erstellt)
            self.edit_manager = None
            self.edit_widget = None
            
            # Tab hinzufügen
            self.tab_widget.addTab(self.edit_container, tab_title)
            
            logger.info(f"✅ Edit-Tab erstellt: '{tab_title}' (Phase 2.2: EditManager-Integration)")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Edit-Tab-Erstellung: {e}")
            raise
    
    def _create_new_datensatz(self):
        """
        Erstellt einen neuen Datensatz mit Template-Support (LINEAR - 8 Schritte)
        
        LINEARER WORKFLOW:
        1. Button "Neuer Datensatz" → diese Methode
        2. Name + Tabelle abfragen (beide Pflichtfelder)
        3. Neue GUID generieren + set_guid
        4. ROOT aus Template (55555555...) kopieren + TABLE setzen
        5. METADATEN: controls (leer) + standard_controls (mit dummy) erstellen
        6. save_all_values() → in DB speichern
        7. Datensatz-Auswahl triggern
        8. Tab 2 (Edit) öffnen zum Bearbeiten
        """
        logger.info("➕ Neuen Datensatz erstellen (LINEAR mit Template)...")
        
        try:
            from PyQt5.QtWidgets import QInputDialog, QMessageBox, QDialog, QFormLayout, QLineEdit, QDialogButtonBox
            import uuid
            
            # SCHRITT 1+2: Name + Tabelle abfragen (Custom Dialog mit beiden Feldern)
            dialog = QDialog(self)
            dialog.setWindowTitle("Neuer Datensatz")
            dialog.setModal(True)
            
            layout = QFormLayout(dialog)
            
            # Name-Feld
            name_edit = QLineEdit()
            name_edit.setPlaceholderText("z.B. 'Personen-Übersicht'")
            layout.addRow("Name *:", name_edit)
            
            # Tabelle-Feld (nur für sys_viewdaten, für sys_framedaten optional)
            table_edit = QLineEdit()
            table_edit.setPlaceholderText("z.B. 'personen'")
            
            # Prüfen ob VIEW oder FRAME
            is_view = self.root_table == 'sys_viewdaten'
            is_frame = self.root_table == 'sys_framedaten'
            
            if is_view:
                layout.addRow("Tabelle *:", table_edit)
            elif is_frame:
                layout.addRow("Root-Tabelle *:", table_edit)
            
            # Info-Label
            info_label = QLabel("* = Pflichtfelder")
            info_label.setStyleSheet("color: gray; font-style: italic; font-size: 10px;")
            layout.addWidget(info_label)
            
            # Buttons
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            # Dialog anzeigen
            if dialog.exec_() != QDialog.Accepted:
                logger.info("  ℹ️ Abgebrochen")
                return
            
            # Werte holen und validieren
            name = name_edit.text().strip()
            table_name = table_edit.text().strip()
            
            if not name:
                QMessageBox.warning(self, "Fehler", "Name ist ein Pflichtfeld!")
                return
            
            if (is_view or is_frame) and not table_name:
                QMessageBox.warning(self, "Fehler", "Tabelle ist ein Pflichtfeld!")
                return
            
            logger.info(f"  📝 Name: {name}")
            logger.info(f"  📋 Tabelle: {table_name}")
            
            # SCHRITT 3: Neue GUID generieren
            neue_guid = str(uuid.uuid4())
            logger.info(f"  🆔 Neue GUID: {neue_guid}")
            
            # Tabellenname immer in GROSSBUCHSTABEN für METADATEN
            table_name_upper = table_name.upper()
            logger.info(f"  📋 Tabelle (GROSS): {table_name_upper}")
            
            # Datenbank-Instanz für neuen Datensatz (ohne GUID → leer)
            db = PdvmCentralDatenbank(self.root_table)
            
            # WICHTIG: Container mit GUID + Name initialisieren
            # Dies setzt _pending_name, der bei save_all_values() in DB-Spalte 'name' geschrieben wird
            db.set_new_data_container(neue_guid, name)
            
            # SCHRITT 4: ROOT aus Template kopieren
            template_db = PdvmCentralDatenbank(self.root_table, '55555555-5555-5555-5555-555555555555')
            template_root = template_db.data.get('ROOT', {}).copy()
            
            logger.info(f"  📋 Template ROOT geladen: {len(template_root)} Felder")
            
            # Name und Tabelle in ROOT setzen
            if is_view:
                template_root['VIEW_NAME'] = name
                template_root['TABLE'] = table_name
                template_root['VIEW_GUID'] = neue_guid
            elif is_frame:
                template_root['TABLE'] = table_name
                template_root['DIALOG_GUID'] = neue_guid
                template_root['HEADER_TEXT'] = name
            
            # ROOT in neue Instanz schreiben
            db.data['ROOT'] = template_root
            
            logger.info(f"  ✅ ROOT initialisiert mit Template-Defaults")
            
            # SCHRITT 5: METADATEN-Struktur erstellen
            if is_view and table_name:
                # View: controls (leer) + standard_controls (mit uid + dummy)
                import uuid as uuid_lib
                uid_guid = str(uuid_lib.uuid4())
                dummy_guid = str(uuid_lib.uuid4())
                
                db.data['METADATEN'] = {
                    table_name_upper: {
                        'controls': {},
                        'standard_controls': {
                            uid_guid: {
                                'table': table_name,
                                'gruppe': '',
                                'feld': 'uid',
                                'label': 'UID',
                                'control_type': 'text',
                                'width': 250,
                                'visible': True,
                                'display_order': 0
                            },
                            dummy_guid: {
                                'table': table_name,
                                'gruppe': 'DUMMY',
                                'feld': 'DUMMY',
                                'label': 'Dummy-Spalte (bitte löschen)',
                                'control_type': 'text',
                                'width': 150,
                                'visible': True,
                                'display_order': 1
                            }
                        }
                    }
                }
                logger.info(f"  ✅ METADATEN erstellt: {table_name_upper} → controls (leer) + standard_controls (uid + dummy)")
            
            elif is_frame and table_name:
                # Frame: controls (leer) + standard_controls (mit uid + dummy)
                import uuid as uuid_lib
                uid_guid = str(uuid_lib.uuid4())
                dummy_guid = str(uuid_lib.uuid4())
                
                db.data['METADATEN'] = {
                    table_name_upper: {
                        'controls': {},
                        'standard_controls': {
                            uid_guid: {
                                'table': table_name,
                                'gruppe': '',
                                'feld': 'uid',
                                'label': 'UID',
                                'type': 'text',
                                'tab': 1,
                                'display_order': 0,
                                'read_only': True
                            },
                            dummy_guid: {
                                'table': table_name,
                                'gruppe': 'DUMMY',
                                'feld': 'DUMMY',
                                'label': 'Dummy-Control (bitte löschen)',
                                'type': 'text',
                                'tab': 1,
                                'display_order': 1
                            }
                        }
                    }
                }
                logger.info(f"  ✅ METADATEN erstellt: {table_name_upper} → controls (leer) + standard_controls (uid + dummy)")
            
            # SCHRITT 6: In DB speichern
            db.save_all_values()
            logger.info(f"  💾 Datensatz gespeichert: {self.root_table}/{neue_guid}")
            
            # SCHRITT 7: GUID in Systemsteuerung speichern
            self.gcs._db.set_value(self.frame_guid, 'LAST_SELECTION', neue_guid)
            self.gcs._db.save_all_values()
            
            # SCHRITT 8: Datensatz-Auswahl triggern + Tab 2 öffnen
            self.datensatz_ausgewaehlt.emit(neue_guid)
            self.tab_widget.setCurrentIndex(1)
            
            # View aktualisieren
            if self.view_controller and hasattr(self.view_controller, 'refresh'):
                self.view_controller.refresh()
                logger.info("  🔄 View aktualisiert")
            
            logger.info(f"✅ Neuer Datensatz '{name}' erfolgreich erstellt (LINEAR)")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des Datensatzes: {e}")
            import traceback
            logger.error(traceback.format_exc())
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Fehler",
                f"Datensatz konnte nicht erstellt werden:\n\n{str(e)}"
            )
    
    def _on_view_row_selected(self, row_data):
        """
        Handler wenn Datensatz in View ausgewählt wird
        
        Args:
            row_data: Dictionary mit Zeilen-Daten (3-Ebenen ARRAY-Struktur!)
        """
        logger.info("🎯 Datensatz ausgewählt in View")
        
        try:
            # ✅ ARRAY: GUID aus 3-Ebenen Struktur extrahieren
            # uid_original ist ein Array: [wert, abdatum, formatiert]
            from pdvm_matrix_constants import get_wert
            
            selected_guid = None
            
            if isinstance(row_data, dict):
                # Versuche GUID-Felder (uid_original zuerst - ist ARRAY!)
                for key in ['uid_original', 'guid', 'GUID', 'uid', 'UID', 'id', 'ID']:
                    if key in row_data:
                        value = row_data[key]
                        # ARRAY-Struktur? → get_wert() verwenden
                        selected_guid = get_wert(value) if isinstance(value, list) else value
                        if selected_guid:
                            break
            
            if not selected_guid:
                logger.warning(f"⚠️ Keine GUID in row_data gefunden!")
                logger.warning(f"  📂 Verfügbare Felder: {list(row_data.keys())[:10] if isinstance(row_data, dict) else 'Kein Dict'}")
                # Debug: Zeige uid_original Struktur
                if isinstance(row_data, dict):
                    uid_cell = row_data.get('uid_original')
                    if uid_cell:
                        logger.warning(f"  📂 uid_original Struktur: {uid_cell}")
                return
            
            logger.info(f"  📋 Ausgewählte GUID: {selected_guid}")
            
            # Signal emittieren
            self.datensatz_ausgewaehlt.emit(selected_guid)
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Datensatz-Auswahl: {e}")
    
    def _on_datensatz_ausgewaehlt(self, selected_guid):
        """
        Handler für datensatz_ausgewaehlt Signal
        
        MODULARER ANSATZ:
        1. edit_type aus Framedaten lesen
        2. Modul aus Registry holen
        3. Modul initialisieren
        4. Widget holen und anzeigen
        
        Args:
            selected_guid: GUID des ausgewählten Datensatzes
        """
        logger.info(f"🎯 Datensatz-Auswahl verarbeiten: {selected_guid}")
        
        try:
            # GUID speichern
            self.current_selected_guid = selected_guid
            
            # === FEATURE: GUID in Systemsteuerung speichern ===
            # Speichere die zuletzt ausgewählte GUID für diesen Frame
            # → Beim nächsten Öffnen des Dialogs wird diese GUID direkt geladen
            self.gcs._db.set_value(self.frame_guid, 'LAST_SELECTION', selected_guid)
            self.gcs._db.save_all_values()
            logger.info(f"  💾 GUID in Systemsteuerung gespeichert: {self.frame_guid}.LAST_SELECTION = {selected_guid}")
            
            # === SCHRITT 1: edit_type verwenden (bereits in __init__ geladen) ===
            logger.info(f"  📋 Edit-Type: {self.edit_type}")
            
            # === SCHRITT 2: Modul aus Registry holen ===
            if self.edit_type not in self.edit_modules:
                error_msg = (
                    f"❌ Edit-Modul '{self.edit_type}' nicht gefunden!\n\n"
                    f"Verfügbare Module:\n" +
                    "\n".join(f"  - {key}" for key in self.edit_modules.keys())
                )
                logger.error(error_msg)
                
                # Fehler-Widget anzeigen
                error_widget = QWidget()
                error_layout = QVBoxLayout(error_widget)
                error_label = QLabel(error_msg)
                error_label.setStyleSheet("color: red; padding: 20px; font-family: monospace;")
                error_layout.addWidget(error_label)
                
                self._replace_edit_widget(error_widget)
                self.tab_widget.setCurrentIndex(1)
                return
            
            module_path = self.edit_modules[self.edit_type]
            logger.info(f"  📦 Modul gefunden: {module_path}")
            
            # === SCHRITT 3: Modul importieren und initialisieren ===
            logger.info("  🔧 Importiere und initialisiere Modul...")
            
            # Dynamischer Import
            module_name, class_name = module_path.rsplit('.', 1)
            import importlib
            module = importlib.import_module(module_name)
            ModuleClass = getattr(module, class_name)
            
            # ✅ V3: System-Editor - EINFACH & LINEAR!
            if self.edit_type == 'system_editor':
                # ✅ EINFACH: TABLE aus framedaten übergeben
                # Editor arbeitet in dieser Tabelle mit einem Datensatz
                logger.info(f"  📦 System-Editor: Tabelle = {self.root_table}")
                
                # ✅ NUR 2 Parameter: record_uid + table_name
                self.current_edit_module = ModuleClass(
                    record_uid=selected_guid,  # ✅ SELECTED GUID, nicht frame_guid!
                    table_name=self.root_table,  # ✅ TABLE aus framedaten!
                    parent=self
                )
                logger.info(f"  ✅ System-Editor initialisiert: {self.root_table}")
                
            else:
                # Andere Editoren: Verwenden framedaten_db (sys_framedaten)
                editor_db = self.framedaten_db
                logger.info(f"  ✅ Editor-DB: sys_framedaten (Standard)")
                
                # Modul initialisieren mit alter API
                self.current_edit_module = ModuleClass(
                    framedaten_db=editor_db,
                    selected_guid=selected_guid,
                    main_app=self.main_app,
                    gcs=self.gcs
                )
            
            # Signal verbinden: refresh_requested → Dialog.refresh()
            if hasattr(self.current_edit_module, 'refresh_requested'):
                self.current_edit_module.refresh_requested.connect(self.refresh)
                logger.info("  🔗 refresh_requested Signal verbunden")
            
            # Signal verbinden: save_completed → Edit-Tab neu laden + View aktualisieren
            if hasattr(self.current_edit_module, 'save_completed'):
                def on_save_completed():
                    # Edit-Tab neu laden
                    self._on_datensatz_ausgewaehlt(self.current_selected_guid)
                    # View aktualisieren (damit Änderungen sofort sichtbar sind)
                    if self.view_controller and hasattr(self.view_controller, 'refresh'):
                        self.view_controller.refresh()
                        logger.info("  🔄 View nach Speichern aktualisiert")
                
                self.current_edit_module.save_completed.connect(on_save_completed)
                logger.info("  🔗 save_completed Signal verbunden → Neuaufbau Edit-Tab + View Refresh")
            
            # ✅ KRITISCH: Signal verbinden: stichtag_changed → Input Controls aktualisieren
            # Wenn der Benutzer den Stichtag ändert, müssen die Input Controls
            # ihre Werte neu laden (mit neuem Stichtag aus der historischen Datenbank)
            if hasattr(self.current_edit_module, 'stichtag_changed'):
                if self.gcs and hasattr(self.gcs, 'stichtag_changed'):
                    self.gcs.stichtag_changed.connect(self.current_edit_module.stichtag_changed)
                    logger.info("  🔗 stichtag_changed Signal verbunden → Input Controls Refresh")
                else:
                    logger.warning("  ⚠️ GCS hat kein stichtag_changed Signal")
            else:
                logger.info("  ℹ️ Edit-Modul hat keine stichtag_changed Methode (optional)")
            
            logger.info("  ✅ Modul erfolgreich initialisiert")
            
            # === SCHRITT 4: Widget holen und anzeigen ===
            logger.info("  🎨 Erstelle Edit-Widget...")
            new_edit_widget = self.current_edit_module.get_widget()
            
            # Widget ersetzen
            self._replace_edit_widget(new_edit_widget)
            
            # Tab 2 öffnen
            self.tab_widget.setCurrentIndex(1)
            
            logger.info("✅ Edit-Bereich aktualisiert mit Datensatz")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Datensatz-Auswahl-Verarbeitung: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _replace_edit_widget(self, new_widget):
        """
        Ersetzt das aktuelle Edit-Widget durch ein neues
        
        Args:
            new_widget: Neues QWidget zum Anzeigen
        """
        # Altes Widget entfernen (Platzhalter oder vorheriges Edit-Widget)
        if self.edit_placeholder:
            self.edit_layout.removeWidget(self.edit_placeholder)
            self.edit_placeholder.setParent(None)
            self.edit_placeholder.deleteLater()
            self.edit_placeholder = None
        
        if self.edit_widget:
            self.edit_layout.removeWidget(self.edit_widget)
            self.edit_widget.setParent(None)
            self.edit_widget.deleteLater()
        
        # Neues Widget hinzufügen
        self.edit_widget = new_widget
        self.edit_layout.addWidget(self.edit_widget)
    
    def refresh(self):
        """
        🔄 Aktualisiert den kompletten Dialog nach Stichtag-Änderung
        
        Workflow:
        1. View aktualisieren (über view_controller.reload_with_stichtag())
        2. Edit-Bereich Input Controls aktualisieren (über current_edit_module.stichtag_changed())
        
        WICHTIG: Wird automatisch vom stichtag_changed Signal aufgerufen
        """
        logger.info("🔄 Dialog-Refresh nach Stichtag-Änderung gestartet...")
        
        try:
            # Aktuellen Stichtag holen
            current_stichtag = self.gcs.stichtag if self.gcs else None
            logger.info(f"  📅 Neuer Stichtag: {current_stichtag}")
            
            # 1. View aktualisieren (VOLLSTÄNDIG mit Daten-Neuladung!)
            if hasattr(self, 'view_controller') and self.view_controller:
                logger.info("  🔄 Aktualisiere View-Tab mit reload_with_stichtag()...")
                if hasattr(self.view_controller, 'reload_with_stichtag'):
                    self.view_controller.reload_with_stichtag(current_stichtag)
                    logger.info("  ✅ View-Tab komplett neu geladen")
                else:
                    logger.warning("  ⚠️ view_controller hat keine reload_with_stichtag()-Methode")
            
            # 2. Input Controls im Edit-Tab aktualisieren
            if hasattr(self, 'current_edit_module') and self.current_edit_module:
                logger.info("  🔄 Aktualisiere Input Controls...")
                if hasattr(self.current_edit_module, 'stichtag_changed'):
                    self.current_edit_module.stichtag_changed()
                    logger.info("  ✅ Input Controls aktualisiert")
                else:
                    logger.info("  ℹ️ Edit-Modul hat keine stichtag_changed()-Methode")
            else:
                logger.info("  ℹ️ Kein Edit-Modul geladen, Input Controls übersprungen")
            
            logger.info("✅ Dialog-Refresh abgeschlossen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Dialog-Refresh: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _on_stichtag_changed(self, new_stichtag):
        """
        🔔 Handler für stichtag_changed Signal von GCS
        
        Args:
            new_stichtag: Neuer Stichtag als Float
        """
        logger.info(f"🔔 === STICHTAG-SIGNAL EMPFANGEN IM DIALOG ===")
        logger.info(f"  📅 Neuer Stichtag: {new_stichtag}")
        
        # Refresh aufrufen
        self.refresh()
    
    def _on_tab_changed(self, index):
        """Handler für Tab-Wechsel"""
        logger.info(f"🔄 Tab gewechselt: {index}")
        
        try:
            # Aktiven Tab speichern (V2: GROSSBUCHSTABEN!)
            self.dialogdaten_db.set_value('ROOT', 'ACTIVE_TAB', index)
            self.dialogdaten_db.save_all_values()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Tab-Wechsel: {e}")
