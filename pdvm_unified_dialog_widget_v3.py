#!/usr/bin/env python3
"""
UnifiedPdvmDialogWidget V3 - Saubere Lupe-Implementierung mit Multi-Tab-Support
==============================================================================

Erweiterte Dialog-Architektur mit:
- Schaltbare View (außerhalb der Tabs)  
- Input-Controls in Tabs organisiert
- Einfache Lupe-Funktionalität (komplettes Ein-/Ausblenden)
- Multi-Tab-Layout (2-3 Tabs parallel anzeigen)
- Zentrale Funktionen für Menü-Integration
- Persistente UI-Einstellungen per Frame-GUID
- Vollständige PyQt5-Integration mit Scrollbars
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QLabel, QLineEdit, QTextEdit, 
    QTreeWidget, QTreeWidgetItem, QPushButton,
    QSplitter, QApplication, QShortcut, QFrame,
    QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QKeySequence, QFont
import logging
import json

# Import PDVM modules
try:
    from pdvm_datetime import Pdvm_DateTime
    from pdvm_central_datenbank import PdvmCentralDatenbank
except ImportError as e:
    logging.warning(f"PDVM Basis-Module nicht verfügbar: {e}")
    
# Multi-Tab-Support Import (optional)
try:
    from pdvm_multi_tab_layout import add_multi_tab_support
    MULTI_TAB_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Multi-Tab-Modul nicht verfügbar: {e}")
    MULTI_TAB_AVAILABLE = False
    # Fallback-Funktion
    def add_multi_tab_support(container, tab_widget):
        logging.warning("Multi-Tab-Support nicht verfügbar - Fallback verwendet")
        return None

# Logger konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedPdvmDialogWidget(QWidget):
    """
    Vollständige Dialog-Architektur für PDVM-System V3
    ================================================
    
    Features:
    - View-Bereich mit kompletter Ein-/Ausblendung
    - Input-Controls in Tabs mit Scrollbars
    - Lupe-Funktionalität (View-Lupe/Input-Lupe)
    - Multi-Tab-Layout (2-3 Tabs parallel)
    - Zentrale Funktionen für Menü-Integration
    - Persistente UI-Einstellungen
    - Keyboard-Shortcuts (F1, F2, F3, F4)
    """
    
    # Signale für Kommunikation mit Hauptanwendung
    status_changed = pyqtSignal(str)
    data_changed = pyqtSignal(dict)
    
    def __init__(self, call_daten):
        super().__init__()
        
        # Basis-Konfiguration aus call_daten
        self.app = call_daten.get("app")
        self.user_guid = call_daten.get("user_guid", "")
        self.frame_guid = call_daten.get("frame_guid", "")
        self.language = call_daten.get("language", "de")
        self.user_stichtag = call_daten.get("stichtag", "2025185")
        
        # UI-Zustandsvariablen
        self.view_lupe_active = False
        self.input_lupe_active = False
        self.saved_splitter_sizes = [300, 300]  # Standard 50/50
        
        # Multi-Tab-Manager (wird später initialisiert)
        self.multi_tab_manager = None
        
        # Widget initialisieren
        self.init_ui()
        self.setup_keyboard_shortcuts()
        self.load_ui_settings()
        
        # KRITISCH: Size Policy für das gesamte Widget setzen
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # KRITISCH: Minimum Size auf 0 setzen, damit Widget klein werden kann
        self.setMinimumSize(0, 0)
        
        # KRITISCH: Widget soll volle verfügbare Größe nutzen
        self.resize(800, 600)  # Fallback falls Parent-Size nicht verfügbar
        
        logger.info("⌨️ Keyboard-Shortcuts aktiviert: F1=View-Lupe, F2=Input-Lupe, F3=Position wiederherstellen, F4=Multi-Tab")
        logger.info("🎨 UnifiedPdvmDialogWidget V3 mit Multi-Tab-Support erfolgreich initialisiert")
    
    def init_ui(self):
        """Initialisiert die gesamte Benutzeroberfläche"""
        
        # Haupt-Layout (wie im originalen Widget)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Status-Bereich (minimiert)
        self.status_label = QLabel("🎨 Unified Dialog Widget V3 - Bereit")
        self.status_label.setStyleSheet("color: #666; font-size: 10pt; padding: 2px;")
        self.status_label.setFixedHeight(20)  # Feste Höhe
        main_layout.addWidget(self.status_label)
        
        # Haupt-Splitter (vertikal: View oben, Input unten)
        self.main_splitter = QSplitter(Qt.Vertical)
        self.main_splitter.splitterMoved.connect(self.on_splitter_moved)
        
        # View-Container erstellen
        self.view_container = self.create_view_container()
        # KRITISCH: Size Policy für volle Raumnutzung setzen
        self.view_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_splitter.addWidget(self.view_container)
        
        # Input-Container erstellen
        self.input_container = self.create_input_container()
        # KRITISCH: Size Policy für volle Raumnutzung setzen
        self.input_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_splitter.addWidget(self.input_container)
        
        # Splitter-Einstellungen
        self.main_splitter.setSizes(self.saved_splitter_sizes)
        
        # DEBUG: Initial-Größen ausgeben
        initial_sizes = self.main_splitter.sizes()
        total_height = sum(initial_sizes)
        view_height = initial_sizes[0] if len(initial_sizes) > 0 else 0
        input_height = initial_sizes[1] if len(initial_sizes) > 1 else 0
        
        logger.info(f"🔧 DEBUG Initial-Setup:")
        logger.info(f"🔧 DEBUG Widget-Größe: {self.size().width()}x{self.size().height()}")
        logger.info(f"🔧 DEBUG Splitter-Gesamthöhe: {total_height}px")
        logger.info(f"🔧 DEBUG View-Bereich: {view_height}px ({view_height/total_height*100:.1f}%)")
        logger.info(f"🔧 DEBUG Input-Bereich: {input_height}px ({input_height/total_height*100:.1f}%)")
        
        # Splitter zum Hauptlayout hinzufügen - MIT STRETCH für volle Raumnutzung
        main_layout.addWidget(self.main_splitter, 1)
    
    def create_view_container(self):
        """Erstellt den View-Container mit Lupe-Button und Scrollbars"""
        
        container = QFrame()
        container.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header mit Lupe-Button
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("📊 VIEW-BEREICH - Datenansicht und -analyse"))
        header_layout.addStretch()
        
        # View-Lupe Button (ein/ausschaltbar)
        self.view_lupe_btn = QPushButton("🔍")
        self.view_lupe_btn.setToolTip("View-Lupe (F1) - Maximiert diesen Bereich")
        self.view_lupe_btn.setCheckable(True)
        self.view_lupe_btn.clicked.connect(self.toggle_view_lupe)
        self.view_lupe_btn.setFixedSize(40, 40)
        self.view_lupe_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 5px;
                font-size: 16pt;
            }
            QPushButton:checked {
                background-color: #ffc107;
                border-color: #ff8f00;
                color: #000;
            }
            QPushButton:hover {
                background-color: #fff3cd;
                border-color: #ffc107;
            }
        """)
        
        header_layout.addWidget(self.view_lupe_btn)
        layout.addLayout(header_layout)
        
        # View-Inhalt mit Scrollbars
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.view_content = QTreeWidget()
        self.view_content.setHeaderLabels(["Eigenschaft", "Wert", "Typ"])
        self.view_content.setAlternatingRowColors(True)
        self.view_content.setRootIsDecorated(False)  # Für flache Darstellung
        
        # Demo-Daten hinzufügen
        self.populate_view_data()
        
        scroll_area.setWidget(self.view_content)
        layout.addWidget(scroll_area)
        
        return container
    
    def create_input_container(self):
        """Erstellt den Input-Container mit Tabs und Lupe-Button"""
        
        container = QFrame()
        container.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header mit Lupe-Button
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("📝 INPUT-BEREICH - Dateneingabe und -bearbeitung"))
        header_layout.addStretch()
        
        # Input-Lupe Button (ein/ausschaltbar)
        self.input_lupe_btn = QPushButton("🔍")
        self.input_lupe_btn.setToolTip("Input-Lupe (F2) - Maximiert diesen Bereich")
        self.input_lupe_btn.setCheckable(True)
        self.input_lupe_btn.clicked.connect(self.toggle_input_lupe)
        self.input_lupe_btn.setFixedSize(40, 40)
        self.input_lupe_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 5px;
                font-size: 16pt;
            }
            QPushButton:checked {
                background-color: #ffc107;
                border-color: #ff8f00;
                color: #000;
            }
            QPushButton:hover {
                background-color: #fff3cd;
                border-color: #ffc107;
            }
        """)
        
        header_layout.addWidget(self.input_lupe_btn)
        layout.addLayout(header_layout)
        
        # Tab-Widget für Input-Controls
        self.input_tabs = QTabWidget()
        
        # Tabs mit Scrollbars erstellen
        self.create_stammdaten_tab()
        self.create_details_tab()
        self.create_zusatz_tab()
        
        # Multi-Tab-Unterstützung hinzufügen
        try:
            if MULTI_TAB_AVAILABLE:
                self.multi_tab_manager = add_multi_tab_support(container, self.input_tabs)
                if self.multi_tab_manager:
                    logger.info("🎨 Multi-Tab-Unterstützung erfolgreich hinzugefügt")
                else:
                    logger.warning("⚠️ Multi-Tab-Manager konnte nicht erstellt werden")
            else:
                logger.info("ℹ️ Multi-Tab-Support nicht verfügbar - läuft ohne Multi-Tab-Features")
                self.multi_tab_manager = None
        except Exception as e:
            logger.warning(f"⚠️ Multi-Tab-Unterstützung konnte nicht hinzugefügt werden: {e}")
            self.multi_tab_manager = None
        
        layout.addWidget(self.input_tabs)
        
        return container
    
    def create_stammdaten_tab(self):
        """Erstellt das Stammdaten-Tab mit Scrollbars"""
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setContentsMargins(0, 0, 0, 0)
        
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setContentsMargins(5, 5, 5, 5)  # Minimale Margins
        layout.setSpacing(10)  # Reduzierter Abstand
        
        # Name
        layout.addWidget(QLabel("📄 Name/Bezeichnung:"))
        self.name_field = QLineEdit()
        self.name_field.setPlaceholderText("Eingabe der Bezeichnung...")
        layout.addWidget(self.name_field)
        
        # Beschreibung
        layout.addWidget(QLabel("📝 Beschreibung:"))
        self.description_field = QTextEdit()
        self.description_field.setPlaceholderText("Detaillierte Beschreibung eingeben...")
        self.description_field.setMaximumHeight(120)
        layout.addWidget(self.description_field)
        
        # Status
        layout.addWidget(QLabel("🔧 Status/GUID-Informationen:"))
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.addWidget(QLabel("Frame GUID:"))
        self.frame_guid_field = QLineEdit(self.frame_guid)
        self.frame_guid_field.setReadOnly(True)
        status_layout.addWidget(self.frame_guid_field)
        layout.addLayout(status_layout)
        
        layout.addStretch(1)  # Füll-Bereich für Lupe-Modus
        
        # Action-Buttons
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(0, 0, 0, 0)
        save_btn = QPushButton("💾 Speichern")
        save_btn.clicked.connect(self.handle_save_data)
        reset_btn = QPushButton("🔄 Zurücksetzen")
        reset_btn.clicked.connect(self.reset_stammdaten)
        
        action_layout.addWidget(save_btn)
        action_layout.addWidget(reset_btn)
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        scroll_area.setWidget(tab_widget)
        self.input_tabs.addTab(scroll_area, "📄 Stammdaten")
    
    def create_details_tab(self):
        """Erstellt das Details-Tab mit Scrollbars"""
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setSpacing(15)
        
        # Details-Bereich
        layout.addWidget(QLabel("📋 Zusätzliche Details und Konfigurationen:"))
        
        self.details_field = QTextEdit()
        self.details_field.setPlaceholderText("Erweiterte Informationen, Konfigurationen oder technische Details...")
        layout.addWidget(self.details_field)
        
        # Stichtag-Bereich
        stichtag_layout = QHBoxLayout()
        stichtag_layout.addWidget(QLabel("🗓️ Stichtag:"))
        self.stichtag_field = QLineEdit(str(self.user_stichtag))
        stichtag_btn = QPushButton("Ändern")
        stichtag_btn.clicked.connect(self.handle_stichtag_wechsel)
        
        stichtag_layout.addWidget(self.stichtag_field)
        stichtag_layout.addWidget(stichtag_btn)
        stichtag_layout.addStretch()
        layout.addLayout(stichtag_layout)
        
        layout.addStretch()
        
        scroll_area.setWidget(tab_widget)
        self.input_tabs.addTab(scroll_area, "📋 Details")
    
    def create_zusatz_tab(self):
        """Erstellt das Zusatz-Tab mit Scrollbars"""
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setSpacing(15)
        
        # Zusatz-Informationen
        layout.addWidget(QLabel("📝 Zusatzinformationen und erweiterte Funktionen:"))
        
        self.zusatz_field = QTextEdit()
        self.zusatz_field.setPlaceholderText("Notizen, Kommentare, erweiterte Konfigurationen...")
        layout.addWidget(self.zusatz_field)
        
        # Export-Bereich
        export_layout = QHBoxLayout()
        export_btn = QPushButton("📊 Daten exportieren")
        export_btn.clicked.connect(self.handle_export_data)
        refresh_btn = QPushButton("🔄 View refreshen")
        refresh_btn.clicked.connect(self.handle_refresh_view)
        
        export_layout.addWidget(export_btn)
        export_layout.addWidget(refresh_btn)
        export_layout.addStretch()
        layout.addLayout(export_layout)
        
        layout.addStretch()
        
        scroll_area.setWidget(tab_widget)
        self.input_tabs.addTab(scroll_area, "📝 Zusatz")
    
    def populate_view_data(self):
        """Füllt die View mit Demo-Daten"""
        
        # Basis-Informationen
        basis_item = QTreeWidgetItem(["📋 Basis-Informationen", "", ""])
        self.view_content.addTopLevelItem(basis_item)
        
        basis_item.addChild(QTreeWidgetItem(["Frame GUID", self.frame_guid, "String"]))
        basis_item.addChild(QTreeWidgetItem(["User GUID", self.user_guid, "String"]))
        basis_item.addChild(QTreeWidgetItem(["Sprache", self.language, "String"]))
        basis_item.addChild(QTreeWidgetItem(["Stichtag", str(self.user_stichtag), "Date"]))
        
        # Lupe-Status
        lupe_item = QTreeWidgetItem(["🔍 Lupe-Status", "", ""])
        self.view_content.addTopLevelItem(lupe_item)
        
        lupe_item.addChild(QTreeWidgetItem(["View-Lupe", "Inaktiv", "Boolean"]))
        lupe_item.addChild(QTreeWidgetItem(["Input-Lupe", "Inaktiv", "Boolean"]))
        lupe_item.addChild(QTreeWidgetItem(["Splitter-Position", "50/50", "Ratio"]))
        
        # Zusätzliche Demo-Daten für mehr Inhalt
        for i in range(10):
            demo_item = QTreeWidgetItem([f"📊 Demo-Datensatz {i+1}", f"Wert {i+1}", "Demo"])
            self.view_content.addTopLevelItem(demo_item)
            
            for j in range(5):
                demo_item.addChild(QTreeWidgetItem([f"Eigenschaft {j+1}", f"Demo-Wert {i+1}.{j+1}", "String"]))
        
        # Alle Items expandieren
        self.view_content.expandAll()
    
    def setup_keyboard_shortcuts(self):
        """Setzt die Keyboard-Shortcuts auf"""
        
        # F1: View-Lupe
        self.shortcut_f1 = QShortcut(QKeySequence(Qt.Key_F1), self)
        self.shortcut_f1.activated.connect(self.toggle_view_lupe)
        
        # F2: Input-Lupe
        self.shortcut_f2 = QShortcut(QKeySequence(Qt.Key_F2), self)
        self.shortcut_f2.activated.connect(self.toggle_input_lupe)
        
        # F3: Position wiederherstellen
        self.shortcut_f3 = QShortcut(QKeySequence(Qt.Key_F3), self)
        self.shortcut_f3.activated.connect(self.restore_user_position)
        
        # F4: Multi-Tab-Modus umschalten
        self.shortcut_f4 = QShortcut(QKeySequence(Qt.Key_F4), self)
        self.shortcut_f4.activated.connect(self.toggle_multi_tab_mode)
    
    def toggle_view_lupe(self):
        """Toggle View-Lupe - blendet Input komplett aus oder wieder ein"""
        
        self.view_lupe_active = not self.view_lupe_active
        self.view_lupe_btn.setChecked(self.view_lupe_active)
        
        if self.view_lupe_active:
            # Input-Lupe deaktivieren falls aktiv
            if self.input_lupe_active:
                self.input_lupe_active = False
                self.input_lupe_btn.setChecked(False)
            
            # Input-Bereich komplett ausblenden - nur View sichtbar
            self.input_container.hide()
            # Splitter-Größen auf Maximum für View setzen
            total_height = self.main_splitter.height()
            self.main_splitter.setSizes([total_height, 0])
            self.show_status_message("🔍 View-Lupe aktiviert - Eingabebereich ausgeblendet")
            
        else:
            # Input-Bereich wieder einblenden und Splitter-Position wiederherstellen
            self.input_container.show()
            if hasattr(self, 'saved_splitter_sizes') and self.saved_splitter_sizes:
                self.main_splitter.setSizes(self.saved_splitter_sizes)
            self.show_status_message("⚖️ Normale Ansicht wiederhergestellt")
        
        # Force Layout-Update
        self.main_splitter.update()
        self.update()
        QApplication.processEvents()
        
        # DEBUG: Höhen nach View-Lupe ausgeben
        sizes = self.main_splitter.sizes()
        total_height = sum(sizes)
        view_height = sizes[0] if len(sizes) > 0 else 0
        input_height = sizes[1] if len(sizes) > 1 else 0
        
        logger.info(f"🔧 DEBUG Nach View-Lupe:")
        logger.info(f"🔧 DEBUG Gesamthöhe: {total_height}px")
        logger.info(f"🔧 DEBUG View-Bereich: {view_height}px ({view_height/total_height*100:.1f}%)")
        logger.info(f"🔧 DEBUG Input-Bereich: {input_height}px ({input_height/total_height*100:.1f}%)")
        
        self.update_view_content()
        logger.info(f"🔍 View-Lupe: {'aktiviert' if self.view_lupe_active else 'deaktiviert'}")
    
    def toggle_input_lupe(self):
        """Toggle Input-Lupe - blendet View komplett aus oder wieder ein"""
        
        self.input_lupe_active = not self.input_lupe_active
        self.input_lupe_btn.setChecked(self.input_lupe_active)
        
        if self.input_lupe_active:
            # View-Lupe deaktivieren falls aktiv
            if self.view_lupe_active:
                self.view_lupe_active = False
                self.view_lupe_btn.setChecked(False)
            
            # View-Bereich komplett ausblenden - nur Input sichtbar
            self.view_container.hide()
            # Splitter-Größen auf Maximum für Input setzen
            total_height = self.main_splitter.height()
            self.main_splitter.setSizes([0, total_height])
            self.show_status_message("🔍 Input-Lupe aktiviert - Datenansicht ausgeblendet")
            
        else:
            # View-Bereich wieder einblenden und Splitter-Position wiederherstellen
            self.view_container.show()
            if hasattr(self, 'saved_splitter_sizes') and self.saved_splitter_sizes:
                self.main_splitter.setSizes(self.saved_splitter_sizes)
            self.show_status_message("⚖️ Normale Ansicht wiederhergestellt")
        
        # Force Layout-Update
        self.main_splitter.update()
        self.update()
        QApplication.processEvents()
        
        # DEBUG: Höhen nach Input-Lupe ausgeben
        sizes = self.main_splitter.sizes()
        total_height = sum(sizes)
        view_height = sizes[0] if len(sizes) > 0 else 0
        input_height = sizes[1] if len(sizes) > 1 else 0
        
        logger.info(f"🔧 DEBUG Nach Input-Lupe:")
        logger.info(f"🔧 DEBUG Gesamthöhe: {total_height}px")
        logger.info(f"🔧 DEBUG View-Bereich: {view_height}px ({view_height/total_height*100:.1f}%)")
        logger.info(f"🔧 DEBUG Input-Bereich: {input_height}px ({input_height/total_height*100:.1f}%)")
        
        self.update_view_content()
        logger.info(f"📝 Input-Lupe: {'aktiviert' if self.input_lupe_active else 'deaktiviert'}")
    
    def restore_user_position(self):
        """Stellt die vom User gespeicherte Splitter-Position wieder her (F3)"""
        
        # Beide Lupen deaktivieren
        self.view_lupe_active = False
        self.input_lupe_active = False
        self.view_lupe_btn.setChecked(False)
        self.input_lupe_btn.setChecked(False)
        
        # Beide Bereiche wieder einblenden
        self.view_container.show()
        self.input_container.show()
        
        # Gespeicherte Position wiederherstellen
        self.main_splitter.setSizes(self.saved_splitter_sizes)
        
        # Prozentuale Aufteilung berechnen
        total = sum(self.saved_splitter_sizes)
        if total > 0:
            view_percent = int((self.saved_splitter_sizes[0] / total) * 100)
            input_percent = 100 - view_percent
            self.show_status_message(f"⚖️ Benutzerdefinierte Position: {view_percent}/{input_percent}")
        else:
            self.show_status_message("⚖️ Standard-Position wiederhergestellt")
        
        self.update_view_content()
        logger.info(f"⚖️ Benutzerdefinierte Position wiederhergestellt: {self.saved_splitter_sizes}")
    
    def on_splitter_moved(self, pos, index):
        """Wird aufgerufen wenn der Splitter bewegt wird"""
        
        sizes = self.main_splitter.sizes()
        
        # DEBUG: Aktuelle Höhen ausgeben
        total_height = sum(sizes)
        view_height = sizes[0] if len(sizes) > 0 else 0
        input_height = sizes[1] if len(sizes) > 1 else 0
        
        logger.info(f"🔧 DEBUG Splitter bewegt - Position: {pos}, Index: {index}")
        logger.info(f"🔧 DEBUG Gesamthöhe: {total_height}px")
        logger.info(f"🔧 DEBUG View-Bereich: {view_height}px ({view_height/total_height*100:.1f}%)")
        logger.info(f"🔧 DEBUG Input-Bereich: {input_height}px ({input_height/total_height*100:.1f}%)")
        
        # Nur speichern wenn keine Lupe aktiv ist
        if not self.view_lupe_active and not self.input_lupe_active:
            self.saved_splitter_sizes = sizes
            self.save_ui_settings()
            logger.info(f"� DEBUG Normale Position gespeichert: {sizes}")
        else:
            logger.info(f"🔧 DEBUG Lupe-Modus aktiv - Position NICHT gespeichert")
    
    def update_view_content(self):
        """Aktualisiert die View-Daten mit aktuellen Lupe-Status"""
        
        # Lupe-Status aktualisieren
        for i in range(self.view_content.topLevelItemCount()):
            item = self.view_content.topLevelItem(i)
            if item.text(0) == "🔍 Lupe-Status":
                # View-Lupe Status
                view_lupe_child = item.child(0)
                if view_lupe_child:
                    view_lupe_child.setText(1, "Aktiv" if self.view_lupe_active else "Inaktiv")
                
                # Input-Lupe Status
                input_lupe_child = item.child(1)
                if input_lupe_child:
                    input_lupe_child.setText(1, "Aktiv" if self.input_lupe_active else "Inaktiv")
                
                # Splitter-Position
                splitter_child = item.child(2)
                if splitter_child:
                    if self.view_lupe_active:
                        splitter_child.setText(1, "100/0 (View-Lupe)")
                    elif self.input_lupe_active:
                        splitter_child.setText(1, "0/100 (Input-Lupe)")
                    else:
                        total = sum(self.saved_splitter_sizes)
                        if total > 0:
                            view_percent = int((self.saved_splitter_sizes[0] / total) * 100)
                            input_percent = 100 - view_percent
                            splitter_child.setText(1, f"{view_percent}/{input_percent}")
                break
    
    def show_status_message(self, message):
        """Zeigt eine Status-Nachricht an"""
        self.status_label.setText(message)
        
        # Nach 3 Sekunden zurück zum Standard-Text
        QTimer.singleShot(3000, lambda: self.status_label.setText("🎨 Unified Dialog Widget V3 - Bereit"))
    
    def load_ui_settings(self):
        """Lädt gespeicherte UI-Einstellungen"""
        # Hier würden normalerweise die Einstellungen aus der Datenbank geladen
        # Für Demo verwenden wir Standard-Werte
        pass
    
    def save_ui_settings(self):
        """Speichert UI-Einstellungen"""
        # Hier würden normalerweise die Einstellungen in der Datenbank gespeichert
        pass
    
    # ========================================
    # ZENTRALE FUNKTIONEN FÜR MENÜ-INTEGRATION
    # ========================================
    
    def execute_central_function(self, function_name):
        """Führt zentrale Funktionen aus (für Menü-Integration)"""
        
        functions = {
            'set_view_lupe': self.external_set_view_lupe,
            'set_input_lupe': self.external_set_input_lupe,
            'set_normal_mode': self.restore_user_position,
            'stichtag_wechsel': self.handle_stichtag_wechsel,
            'refresh_view': self.handle_refresh_view,
            'save_data': self.handle_save_data,
            'export_data': self.handle_export_data,
            'toggle_menu': self.handle_toggle_menu
        }
        
        if function_name in functions:
            try:
                functions[function_name]()
                logger.info(f"✅ Zentrale Funktion '{function_name}' ausgeführt")
                return True
            except Exception as e:
                logger.error(f"❌ Fehler bei zentraler Funktion '{function_name}': {e}")
                return False
        else:
            logger.warning(f"⚠️ Unbekannte zentrale Funktion: {function_name}")
            return False
    
    def external_set_view_lupe(self):
        """Externe View-Lupe: Berücksichtigt aktuellen Status"""
        logger.info(f"🔧 DEBUG External View-Lupe: View aktiv={self.view_lupe_active}, Input aktiv={self.input_lupe_active}")
        
        if self.input_lupe_active:
            # Input-Lupe ist aktiv -> zuerst deaktivieren, dann View-Lupe aktivieren
            logger.info("🔄 Input-Lupe ist aktiv, deaktiviere zuerst...")
            self.input_lupe_active = False
            self.input_lupe_btn.setChecked(False)
            self.view_container.show()
            
        # Jetzt View-Lupe aktivieren (oder umschalten falls bereits aktiv)
        self.toggle_view_lupe()
    
    def external_set_input_lupe(self):
        """Externe Input-Lupe: Berücksichtigt aktuellen Status"""
        logger.info(f"🔧 DEBUG External Input-Lupe: View aktiv={self.view_lupe_active}, Input aktiv={self.input_lupe_active}")
        
        if self.view_lupe_active:
            # View-Lupe ist aktiv -> zuerst deaktivieren, dann Input-Lupe aktivieren
            logger.info("🔄 View-Lupe ist aktiv, deaktiviere zuerst...")
            self.view_lupe_active = False
            self.view_lupe_btn.setChecked(False)
            self.input_container.show()
            
        # Jetzt Input-Lupe aktivieren (oder umschalten falls bereits aktiv)
        self.toggle_input_lupe()
    
    # ========================================
    # EVENT-HANDLER FÜR AKTIONEN
    # ========================================
    
    def handle_save_data(self):
        """Speichert die eingegebenen Daten"""
        self.show_status_message("💾 Daten gespeichert")
        logger.info("💾 Daten gespeichert")
    
    def handle_stichtag_wechsel(self):
        """Wechselt den Stichtag"""
        new_stichtag = self.stichtag_field.text()
        self.user_stichtag = new_stichtag
        self.show_status_message(f"🗓️ Stichtag geändert: {new_stichtag}")
        logger.info(f"🗓️ Stichtag geändert: {new_stichtag}")
    
    def handle_refresh_view(self):
        """Aktualisiert die View"""
        self.populate_view_data()
        self.show_status_message("🔄 View aktualisiert")
        logger.info("🔄 View aktualisiert")
    
    def handle_export_data(self):
        """Exportiert die Daten"""
        self.show_status_message("📊 Daten exportiert")
        logger.info("📊 Daten exportiert")
    
    def handle_toggle_menu(self):
        """Blendet das Menü ein/aus"""
        
        # Zugriff auf die Hauptanwendung über app-Referenz
        if hasattr(self, 'app') and self.app:
            main_app = self.app
            
            # Prüfe ob menu_frame existiert
            if hasattr(main_app, 'menu_frame'):
                menu_frame = main_app.menu_frame
                
                # Toggle-Logik: Sichtbarkeit umschalten
                if menu_frame.isVisible():
                    # Menü ausblenden
                    menu_frame.hide()
                    self.show_status_message("🎛️ Menü ausgeblendet - Vollbild-Modus")
                    logger.info("🎛️ Menü ausgeblendet - mehr Platz für Dialog")
                else:
                    # Menü wieder einblenden
                    menu_frame.show()
                    self.show_status_message("🎛️ Menü wieder eingeblendet")
                    logger.info("🎛️ Menü wieder eingeblendet")
                    
                # Force Layout-Update
                main_app.update()
                
            else:
                logger.warning("⚠️ menu_frame nicht gefunden in Hauptanwendung")
                self.show_status_message("⚠️ Menü-Toggle nicht verfügbar")
        else:
            logger.warning("⚠️ app-Referenz nicht verfügbar für Menü-Toggle")
            self.show_status_message("⚠️ Menü-Toggle nicht verfügbar")
    
    def reset_stammdaten(self):
        """Setzt die Stammdaten zurück"""
        self.name_field.clear()
        self.description_field.clear()
        self.show_status_message("🔄 Stammdaten zurückgesetzt")
        logger.info("🔄 Stammdaten zurückgesetzt")
    
    def toggle_multi_tab_mode(self):
        """Schaltet den Multi-Tab-Modus um (F4)"""
        
        if self.multi_tab_manager:
            try:
                self.multi_tab_manager.toggle_multi_tab_mode()
                
                if self.multi_tab_manager.multi_tab_active:
                    self.show_status_message("📱 Multi-Tab-Modus aktiviert - Parallele Tab-Anzeige")
                    logger.info("📱 Multi-Tab-Modus über F4 aktiviert")
                else:
                    self.show_status_message("📱 Multi-Tab-Modus deaktiviert - Standard-Tab-Anzeige")
                    logger.info("📱 Multi-Tab-Modus über F4 deaktiviert")
                    
            except Exception as e:
                logger.error(f"❌ Fehler beim Umschalten des Multi-Tab-Modus: {e}")
                self.show_status_message(f"❌ Multi-Tab-Fehler: {str(e)}")
        else:
            logger.warning("⚠️ Multi-Tab-Manager nicht verfügbar")
            self.show_status_message("⚠️ Multi-Tab-Modus nicht verfügbar")
    
    def get_multi_tab_status(self):
        """Gibt den aktuellen Status des Multi-Tab-Modus zurück"""
        
        if self.multi_tab_manager:
            return {
                'active': self.multi_tab_manager.multi_tab_active,
                'layout_type': self.multi_tab_manager.layout_combo.currentText() if hasattr(self.multi_tab_manager, 'layout_combo') else None,
                'available_tabs': len(self.multi_tab_manager.available_tabs) if hasattr(self.multi_tab_manager, 'available_tabs') else 0
            }
        return {'active': False, 'layout_type': None, 'available_tabs': 0}

# ========================================
# DEMO/TEST BEREICH
# ========================================

if __name__ == "__main__":
    import sys
    
    app = QApplication(sys.argv)
    
    # Test-Daten
    call_daten = {
        "app": None,
        "user_guid": "test-user-guid",
        "frame_guid": "test-frame-guid",
        "language": "de",
        "stichtag": "2025185"
    }
    
    # Widget erstellen und anzeigen
    widget = UnifiedPdvmDialogWidget(call_daten)
    widget.setWindowTitle("UnifiedPdvmDialogWidget V3 - Demo")
    widget.resize(800, 600)
    widget.show()
    
    print("🎨 UnifiedPdvmDialogWidget V3 Demo gestartet")
    print("⌨️ Shortcuts: F1=View-Lupe, F2=Input-Lupe, F3=Position wiederherstellen")
    
    sys.exit(app.exec_())
