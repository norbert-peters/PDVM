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
- framedaten.db: Frame-Konfiguration (ROOT_TABLE, VIEW_GUID, DIALOG_GUID, HEADER_TEXT)
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
    1. Frame-GUID → sys_framedaten laden (ROOT_TABLE, VIEW_GUID, DIALOG_GUID, HEADER_TEXT)
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
            'menu_editor': 'pdvm_menu_editor_module.PdvmMenuEditorModule',  # ✅ Menü-Editor Integration (Phase 1: Platzhalter)
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
        - ROOT_TABLE: Tabellenname für Daten
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
            
            # ROOT_TABLE
            # V2: Framedaten ist NICHT historisch → get_static_value
            self.root_table = self.framedaten_db.get_static_value(
                gruppe, 'ROOT_TABLE'
            )
            logger.info(f"  📋 ROOT_TABLE: {self.root_table}")
            
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
                raise ValueError("ROOT_TABLE ist leer!")
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
            
            # ⚠️ SPEZIAL-CHECK: Menu-Editor noch nicht V3-kompatibel
            if self.edit_type == 'menu_editor':
                logger.warning("⚠️ Menu-Editor noch nicht V3-kompatibel!")
                logger.info("  📋 Zeige Info-Platzhalter statt Fehler...")
                
                # Platzhalter-Widget erstellen
                from PyQt5.QtWidgets import QLabel
                from PyQt5.QtCore import Qt
                
                placeholder = QLabel()
                placeholder.setWordWrap(True)
                placeholder.setAlignment(Qt.AlignCenter)
                placeholder.setStyleSheet("""
                    QLabel {
                        background-color: #fff3cd;
                        border: 2px solid #ffc107;
                        border-radius: 5px;
                        padding: 30px;
                        font-size: 12pt;
                        color: #856404;
                    }
                """)
                placeholder.setText(
                    "🚧 MENÜ-EDITOR IN ENTWICKLUNG\n\n"
                    "Der Menü-Editor wird aktuell für das neue V3-Menü-System überarbeitet.\n\n"
                    "Grund: Die Menüstruktur wurde fundamental geändert (V3-Migration)\n"
                    "und der Editor muss entsprechend angepasst werden.\n\n"
                    "Bitte nutzen Sie vorerst die Datenbank-Tools zur Menüpflege."
                )
                
                # Widget anzeigen
                self._replace_edit_widget(placeholder)
                logger.info("  ✅ Platzhalter angezeigt")
                return  # Frühzeitiger Return, keine weitere Verarbeitung
            
            # Modul initialisieren mit EINFACHER API
            # WICHTIG: Als Instanzvariable speichern, damit es nicht garbage-collected wird!
            self.current_edit_module = ModuleClass(
                framedaten_db=self.framedaten_db,
                selected_guid=selected_guid,
                main_app=self.main_app,  # ✅ MainApp-Referenz durchreichen für menu_editor
                gcs=self.gcs  # ✅ V2: GCS durchreichen statt get_gcs() Aufruf
            )
            
            # Signal verbinden: refresh_requested → Dialog.refresh()
            if hasattr(self.current_edit_module, 'refresh_requested'):
                self.current_edit_module.refresh_requested.connect(self.refresh)
                logger.info("  🔗 refresh_requested Signal verbunden")
            
            # Signal verbinden: save_completed → Edit-Tab neu laden
            if hasattr(self.current_edit_module, 'save_completed'):
                self.current_edit_module.save_completed.connect(
                    lambda: self._on_datensatz_ausgewaehlt(self.current_selected_guid)
                )
                logger.info("  🔗 save_completed Signal verbunden → Neuaufbau Edit-Tab")
            
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
