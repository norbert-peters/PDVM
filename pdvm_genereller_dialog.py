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

from global_gcs import gcs
from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)


class PdvmGenerellerDialog(QWidget):
    """
    🎯 Genereller Dialog für alle Datenänderungen
    
    Workflow:
    1. Frame-GUID → Framedaten laden (ROOT_TABLE, VIEW_GUID, DIALOG_GUID, HEADER_TEXT)
    2. DIALOG_GUID → Dialogdaten laden/erstellen (Tab-Konfiguration)
    3. Tab 1: View initialisieren
    4. Tab 2: Edit-Bereich (Phase 1: nur GUID-Anzeige)
    5. Datensatz-Auswahl → Tab 2 öffnen + GUID übergeben
    """
    
    # Signal wenn Datensatz ausgewählt wird
    datensatz_ausgewaehlt = pyqtSignal(str)  # GUID des ausgewählten Datensatzes
    
    def __init__(self, frame_guid, parent=None):
        """
        Initialisiert den Generellen Dialog
        
        Args:
            frame_guid: GUID der Frame-Konfiguration
            parent: Parent-Widget (Arbeitsbereich des Systems)
        """
        super().__init__(parent)
        
        logger.info("🎯 === GENERELLER DIALOG - INITIALISIERUNG ===")
        logger.info(f"📋 Frame-GUID: {frame_guid}")
        
        # GCS-Zugriff prüfen
        if not gcs or not gcs.is_initialized:
            raise RuntimeError("❌ GCS muss initialisiert sein!")
        
        self.frame_guid = frame_guid
        self.gcs = gcs
        
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
        self.current_selected_guid = None
        
        # Signal-Verbindung
        self.datensatz_ausgewaehlt.connect(self._on_datensatz_ausgewaehlt)
        
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
            # Framedaten-DB Instanz erstellen mit frame_guid
            self.framedaten_db = PdvmCentralDatenbank('framedaten', self.frame_guid)
            
            # ROOT-Gruppe lesen
            gruppe = 'ROOT'
            
            # ROOT_TABLE
            self.root_table, _ = self.framedaten_db.get_value(
                gruppe, 'ROOT_TABLE'
            )
            logger.info(f"  📋 ROOT_TABLE: {self.root_table}")
            
            # VIEW_GUID
            self.view_guid, _ = self.framedaten_db.get_value(
                gruppe, 'VIEW_GUID'
            )
            logger.info(f"  📋 VIEW_GUID: {self.view_guid}")
            
            # DIALOG_GUID
            self.dialog_guid, _ = self.framedaten_db.get_value(
                gruppe, 'DIALOG_GUID'
            )
            logger.info(f"  📋 DIALOG_GUID: {self.dialog_guid}")
            
            # HEADER_TEXT
            self.header_text, _ = self.framedaten_db.get_value(
                gruppe, 'HEADER_TEXT'
            )
            logger.info(f"  📋 HEADER_TEXT: {self.header_text}")
            
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
            
            # Dialogdaten-DB Instanz erstellen
            # WICHTIG: Verwende 'dialogdaten' Datenbank mit DIALOG_GUID
            # NICHT 'anwendungsdaten' - das ist nur für User-bezogene Daten über GCS!
            self.dialogdaten_db = PdvmCentralDatenbank('dialogdaten', self.dialog_guid)
            
            # Prüfen ob ROOT-Gruppe existiert (via get_value - wenn None dann nicht vorhanden)
            active_tab_test, _ = self.dialogdaten_db.get_value('ROOT', 'active_tab')
            root_exists = (active_tab_test is not None)
            
            if not root_exists:
                logger.info("  🆕 Erstelle initiale Dialogdaten...")
                
                # Initiale ROOT-Parameter
                self.dialogdaten_db.set_value('ROOT', 'active_tab', 0)
                self.dialogdaten_db.set_value('ROOT', 'tab_count', 2)
                
                # Tab01 Parameter (View)
                self.dialogdaten_db.set_value('Tab01', 'tab_type', 'view')
                self.dialogdaten_db.set_value('Tab01', 'tab_title', 'Übersicht')
                self.dialogdaten_db.set_value('Tab01', 'view_guid', self.view_guid)
                
                # Tab02 Parameter (Edit)
                self.dialogdaten_db.set_value('Tab02', 'tab_type', 'edit')
                self.dialogdaten_db.set_value('Tab02', 'tab_title', 'Bearbeiten')
                self.dialogdaten_db.set_value('Tab02', 'selected_guid', None)
                
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
            # Tab-Anzahl aus Dialogdaten
            tab_count, _ = self.dialogdaten_db.get_value('ROOT', 'tab_count')
            tab_count = int(tab_count) if tab_count else 2
            
            logger.info(f"  📊 Tab-Anzahl: {tab_count}")
            
            # Tab 1: View (IMMER vorhanden)
            self._create_view_tab()
            
            # Tab 2: Edit-Bereich (Phase 1: nur GUID-Anzeige)
            self._create_edit_tab()
            
            # Aktiven Tab wiederherstellen
            active_tab, _ = self.dialogdaten_db.get_value('ROOT', 'active_tab')
            if active_tab is not None:
                active_tab = int(active_tab)
                if 0 <= active_tab < self.tab_widget.count():
                    self.tab_widget.setCurrentIndex(active_tab)
                    logger.info(f"  ✅ Aktiver Tab wiederhergestellt: {active_tab}")
            
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
            # Tab-Titel aus Dialogdaten
            tab_title, _ = self.dialogdaten_db.get_value('Tab01', 'tab_title')
            tab_title = tab_title or 'Übersicht'
            
            # View-Container
            view_container = QWidget()
            view_layout = QVBoxLayout(view_container)
            view_layout.setContentsMargins(0, 0, 0, 0)
            
            # View-Controller initialisieren
            from pdvm_view_controller import PdvmViewController
            
            # call_daten für View (wie in test_pdvm_view)
            call_daten = {
                'frame_guid': self.frame_guid,
                'view_guid': self.view_guid,
                'root_table': self.root_table,
                'title': tab_title
            }
            
            self.view_controller = PdvmViewController(call_daten, parent=view_container)
            
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
            # Tab-Titel aus Dialogdaten
            tab_title, _ = self.dialogdaten_db.get_value('Tab02', 'tab_title')
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
        
        Args:
            selected_guid: GUID des ausgewählten Datensatzes
        """
        logger.info(f"🎯 Datensatz-Auswahl verarbeiten: {selected_guid}")
        
        try:
            # GUID speichern
            self.current_selected_guid = selected_guid
            
            # GUID in Dialogdaten speichern
            self.dialogdaten_db.set_value('Tab02', 'selected_guid', selected_guid)
            self.dialogdaten_db.save_all_values()
            
            # Edit-Manager initialisieren mit PdvmEditManager
            logger.info("  🔧 Initialisiere PdvmEditManager...")
            from pdvm_edit_manager import PdvmEditManager
            
            self.edit_manager = PdvmEditManager(
                frame_guid=self.frame_guid,
                root_table=self.root_table,
                gcs=self.gcs
            )
            
            # Datensatz laden
            logger.info("  📂 Lade Datensatz in EditManager...")
            self.edit_manager.load_datensatz(selected_guid)
            
            # Edit-Widget erstellen
            logger.info("  🎨 Erstelle Edit-Widget...")
            new_edit_widget = self.edit_manager.get_widget()
            
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
            self.edit_widget = new_edit_widget
            self.edit_layout.addWidget(self.edit_widget)
            
            # Tab 2 öffnen
            self.tab_widget.setCurrentIndex(1)
            
            logger.info("✅ Edit-Bereich aktualisiert mit Datensatz")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Datensatz-Auswahl-Verarbeitung: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _on_tab_changed(self, index):
        """Handler für Tab-Wechsel"""
        logger.info(f"🔄 Tab gewechselt: {index}")
        
        try:
            # Aktiven Tab speichern
            self.dialogdaten_db.set_value('ROOT', 'active_tab', index)
            self.dialogdaten_db.save_all_values()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Tab-Wechsel: {e}")
