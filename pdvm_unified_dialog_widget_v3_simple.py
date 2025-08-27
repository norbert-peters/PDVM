# pdvm_unified_dialog_widget_v3_simple.py
# -*- coding: utf-8 -*-

"""
UnifiedPdvmDialogWidget V3 - Mit einfacher Multi-Tab-Funktionalität
===================================================================

Vereinfachte Version mit integrierter Multi-Tab-Funktionalität
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QLabel, QLineEdit, QTextEdit, QPushButton, QCheckBox,
    QTreeWidget, QTreeWidgetItem, QComboBox,
    QSplitter, QApplication, QShortcut, QFrame,
    QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QKeySequence, QFont
import logging
import json

# Import PDVM modules (optional)
try:
    from pdvm_datetime import Pdvm_DateTime
    from pdvm_central_datenbank import PdvmCentralDatenbank
    PDVM_AVAILABLE = True
except ImportError as e:
    logging.warning(f"PDVM Module nicht verfügbar: {e}")
    PDVM_AVAILABLE = False

# Logger konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleMultiTabManager:
    """Einfacher Multi-Tab-Manager ohne externe Abhängigkeiten"""
    
    def __init__(self, parent_widget, tab_widget):
        self.parent = parent_widget
        self.original_tabs = tab_widget
        self.multi_tab_active = False
        self.current_splitter = None
        self.saved_tabs = []
        
    def toggle_multi_tab_mode(self):
        """Schaltet zwischen Normal- und Multi-Tab-Modus um"""
        if self.multi_tab_active:
            self.deactivate_multi_tab()
        else:
            self.activate_multi_tab()
    
    def activate_multi_tab(self):
        """Aktiviert einfachen 2-Tab-Modus"""
        try:
            if self.original_tabs.count() < 2:
                logger.warning("⚠️ Mindestens 2 Tabs erforderlich")
                return
            
            # Ersten beiden Tabs in horizontalem Splitter anzeigen
            self.current_splitter = QSplitter(Qt.Horizontal)
            
            # Tab 0 und Tab 1 aus Original-Widget entfernen
            tab1_widget = self.original_tabs.widget(0)
            tab1_text = self.original_tabs.tabText(0)
            tab2_widget = self.original_tabs.widget(1)
            tab2_text = self.original_tabs.tabText(1)
            
            # Tabs entfernen (rückwärts, damit Indizes stimmen)
            self.original_tabs.removeTab(1)
            self.original_tabs.removeTab(0)
            
            # Container für jeden Tab erstellen
            container1 = self.create_tab_container(tab1_text, tab1_widget)
            container2 = self.create_tab_container(tab2_text, tab2_widget)
            
            self.current_splitter.addWidget(container1)
            self.current_splitter.addWidget(container2)
            self.current_splitter.setSizes([400, 400])  # Gleichmäßige Aufteilung
            
            # Original-Tab-Widget verstecken und Splitter anzeigen
            self.original_tabs.hide()
            
            # Splitter zu Parent-Layout hinzufügen
            parent_layout = self.parent.layout()
            if parent_layout:
                tab_index = parent_layout.indexOf(self.original_tabs)
                if tab_index >= 0:
                    parent_layout.insertWidget(tab_index, self.current_splitter)
                else:
                    parent_layout.addWidget(self.current_splitter)
            
            # Tabs für Wiederherstellung speichern
            self.saved_tabs = [(tab1_widget, tab1_text), (tab2_widget, tab2_text)]
            
            self.multi_tab_active = True
            logger.info("📱 Multi-Tab-Modus aktiviert (2 Tabs horizontal)")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktivieren des Multi-Tab-Modus: {e}")
    
    def deactivate_multi_tab(self):
        """Deaktiviert Multi-Tab-Modus"""
        try:
            if self.current_splitter:
                # Tabs zurück ins Original-Widget setzen
                for i, (tab_widget, tab_text) in enumerate(self.saved_tabs):
                    self.original_tabs.insertTab(i, tab_widget, tab_text)
                
                # Splitter entfernen
                self.current_splitter.setParent(None)
                self.current_splitter = None
                self.saved_tabs = []
            
            # Original-Tab-Widget wieder anzeigen
            self.original_tabs.show()
            
            self.multi_tab_active = False
            logger.info("📱 Multi-Tab-Modus deaktiviert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Deaktivieren des Multi-Tab-Modus: {e}")
    
    def create_tab_container(self, title, content_widget):
        """Erstellt einen Container für einen Tab"""
        container = QFrame()
        container.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Header
        header = QLabel(f"📋 {title}")
        header.setStyleSheet("font-weight: bold; padding: 5px; background-color: #e9ecef; border-radius: 3px;")
        layout.addWidget(header)
        
        # Content
        layout.addWidget(content_widget)
        
        return container


class UnifiedPdvmDialogWidget(QWidget):
    """Vereinfachtes Dialog-Widget mit integrierter Multi-Tab-Funktionalität"""
    
    status_changed = pyqtSignal(str)
    data_changed = pyqtSignal(dict)
    
    def __init__(self, call_daten):
        super().__init__()
        
        # Basis-Konfiguration
        self.app = call_daten.get("app")
        self.user_guid = call_daten.get("user_guid", "")
        self.frame_guid = call_daten.get("frame_guid", "")
        self.language = call_daten.get("language", "de")
        self.user_stichtag = call_daten.get("stichtag", "2025185")
        
        # UI-Zustand
        self.view_lupe_active = False
        self.input_lupe_active = False
        self.saved_splitter_sizes = [300, 300]
        
        # Multi-Tab-Manager
        self.multi_tab_manager = None
        
        # UI aufbauen
        self.init_ui()
        self.setup_keyboard_shortcuts()
        
        # Size Policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(0, 0)
        self.resize(800, 600)
        
        logger.info("🎨 Vereinfachtes Dialog-Widget mit Multi-Tab-Support initialisiert")
    
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Status-Bereich
        self.status_label = QLabel("🎨 Dialog-Widget V3 - Bereit")
        self.status_label.setStyleSheet("color: #666; font-size: 10pt; padding: 2px;")
        self.status_label.setFixedHeight(20)
        main_layout.addWidget(self.status_label)
        
        # Haupt-Splitter
        self.main_splitter = QSplitter(Qt.Vertical)
        self.main_splitter.splitterMoved.connect(self.on_splitter_moved)
        
        # View-Container
        self.view_container = self.create_view_container()
        self.main_splitter.addWidget(self.view_container)
        
        # Input-Container
        self.input_container = self.create_input_container()
        self.main_splitter.addWidget(self.input_container)
        
        # Splitter-Einstellungen
        self.main_splitter.setSizes(self.saved_splitter_sizes)
        main_layout.addWidget(self.main_splitter, 1)
        
        logger.info("🎨 UI erfolgreich initialisiert")
    
    def create_view_container(self):
        """Erstellt den View-Container"""
        
        container = QFrame()
        container.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header mit Lupe-Button
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("📊 VIEW-BEREICH"))
        header_layout.addStretch()
        
        self.view_lupe_btn = QPushButton("🔍")
        self.view_lupe_btn.setToolTip("View-Lupe (F1)")
        self.view_lupe_btn.setCheckable(True)
        self.view_lupe_btn.clicked.connect(self.toggle_view_lupe)
        self.view_lupe_btn.setFixedSize(40, 40)
        header_layout.addWidget(self.view_lupe_btn)
        layout.addLayout(header_layout)
        
        # View-Inhalt
        self.view_content = QTreeWidget()
        self.view_content.setHeaderLabels(["Eigenschaft", "Wert", "Typ"])
        self.populate_view_data()
        layout.addWidget(self.view_content)
        
        return container
    
    def create_input_container(self):
        """Erstellt den Input-Container mit Tabs"""
        
        container = QFrame()
        container.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header mit Lupe-Button und Multi-Tab-Controls
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("📝 INPUT-BEREICH"))
        header_layout.addStretch()
        
        # Multi-Tab-Button
        self.multi_tab_btn = QPushButton("📱")
        self.multi_tab_btn.setToolTip("Multi-Tab-Modus (F4)")
        self.multi_tab_btn.setCheckable(True)
        self.multi_tab_btn.clicked.connect(self.toggle_multi_tab_mode)
        self.multi_tab_btn.setFixedSize(40, 40)
        header_layout.addWidget(self.multi_tab_btn)
        
        # Input-Lupe-Button
        self.input_lupe_btn = QPushButton("🔍")
        self.input_lupe_btn.setToolTip("Input-Lupe (F2)")
        self.input_lupe_btn.setCheckable(True)
        self.input_lupe_btn.clicked.connect(self.toggle_input_lupe)
        self.input_lupe_btn.setFixedSize(40, 40)
        header_layout.addWidget(self.input_lupe_btn)
        
        layout.addLayout(header_layout)
        
        # Tab-Widget
        self.input_tabs = QTabWidget()
        self.create_demo_tabs()
        layout.addWidget(self.input_tabs)
        
        # Multi-Tab-Manager initialisieren
        self.multi_tab_manager = SimpleMultiTabManager(container, self.input_tabs)
        logger.info("📱 Multi-Tab-Manager erfolgreich initialisiert")
        
        return container
    
    def create_demo_tabs(self):
        """Erstellt Demo-Tabs"""
        
        # Tab 1: Stammdaten
        tab1 = QWidget()
        layout1 = QVBoxLayout(tab1)
        layout1.addWidget(QLabel("📄 Name/Bezeichnung:"))
        layout1.addWidget(QLineEdit("Demo-Eintrag"))
        layout1.addWidget(QLabel("📝 Beschreibung:"))
        layout1.addWidget(QTextEdit("Demo-Beschreibung..."))
        layout1.addStretch()
        self.input_tabs.addTab(tab1, "Stammdaten")
        
        # Tab 2: Details
        tab2 = QWidget()
        layout2 = QVBoxLayout(tab2)
        layout2.addWidget(QLabel("🔧 Details und Einstellungen:"))
        layout2.addWidget(QLineEdit("Detail-Feld 1"))
        layout2.addWidget(QLineEdit("Detail-Feld 2"))
        layout2.addWidget(QTextEdit("Weitere Details..."))
        layout2.addStretch()
        self.input_tabs.addTab(tab2, "Details")
        
        # Tab 3: Zusatz
        tab3 = QWidget()
        layout3 = QVBoxLayout(tab3)
        layout3.addWidget(QLabel("📊 Zusatzinformationen:"))
        layout3.addWidget(QLineEdit("Zusatz-Feld 1"))
        layout3.addWidget(QLineEdit("Zusatz-Feld 2"))
        layout3.addWidget(QTextEdit("Zusatznotizen..."))
        layout3.addStretch()
        self.input_tabs.addTab(tab3, "Zusatz")
    
    def populate_view_data(self):
        """Füllt View mit Demo-Daten"""
        
        demo_data = [
            ("Frame GUID", self.frame_guid, "String"),
            ("User GUID", self.user_guid, "String"),
            ("Sprache", self.language, "String"),
            ("Stichtag", self.user_stichtag, "String"),
            ("Multi-Tab", "Verfügbar", "Status")
        ]
        
        for prop, value, typ in demo_data:
            item = QTreeWidgetItem([prop, str(value), typ])
            self.view_content.addTopLevelItem(item)
    
    def setup_keyboard_shortcuts(self):
        """Setzt Keyboard-Shortcuts auf"""
        
        # F1: View-Lupe
        self.shortcut_f1 = QShortcut(QKeySequence(Qt.Key_F1), self)
        self.shortcut_f1.activated.connect(self.toggle_view_lupe)
        
        # F2: Input-Lupe
        self.shortcut_f2 = QShortcut(QKeySequence(Qt.Key_F2), self)
        self.shortcut_f2.activated.connect(self.toggle_input_lupe)
        
        # F3: Position wiederherstellen
        self.shortcut_f3 = QShortcut(QKeySequence(Qt.Key_F3), self)
        self.shortcut_f3.activated.connect(self.restore_position)
        
        # F4: Multi-Tab-Modus
        self.shortcut_f4 = QShortcut(QKeySequence(Qt.Key_F4), self)
        self.shortcut_f4.activated.connect(self.toggle_multi_tab_mode)
        
        logger.info("⌨️ Keyboard-Shortcuts aktiviert: F1-F4")
    
    def toggle_view_lupe(self):
        """Toggle View-Lupe"""
        self.view_lupe_active = not self.view_lupe_active
        self.view_lupe_btn.setChecked(self.view_lupe_active)
        
        if self.view_lupe_active:
            if self.input_lupe_active:
                self.input_lupe_active = False
                self.input_lupe_btn.setChecked(False)
            self.input_container.hide()
            self.show_status_message("🔍 View-Lupe aktiviert")
        else:
            self.input_container.show()
            self.show_status_message("🔍 View-Lupe deaktiviert")
    
    def toggle_input_lupe(self):
        """Toggle Input-Lupe"""
        self.input_lupe_active = not self.input_lupe_active
        self.input_lupe_btn.setChecked(self.input_lupe_active)
        
        if self.input_lupe_active:
            if self.view_lupe_active:
                self.view_lupe_active = False
                self.view_lupe_btn.setChecked(False)
            self.view_container.hide()
            self.show_status_message("🔍 Input-Lupe aktiviert")
        else:
            self.view_container.show()
            self.show_status_message("🔍 Input-Lupe deaktiviert")
    
    def toggle_multi_tab_mode(self):
        """Toggle Multi-Tab-Modus"""
        if self.multi_tab_manager:
            self.multi_tab_manager.toggle_multi_tab_mode()
            self.multi_tab_btn.setChecked(self.multi_tab_manager.multi_tab_active)
            
            if self.multi_tab_manager.multi_tab_active:
                self.show_status_message("📱 Multi-Tab-Modus aktiviert")
            else:
                self.show_status_message("📱 Multi-Tab-Modus deaktiviert")
        else:
            self.show_status_message("⚠️ Multi-Tab-Manager nicht verfügbar")
    
    def restore_position(self):
        """Stellt Standard-Position wieder her"""
        self.view_lupe_active = False
        self.input_lupe_active = False
        self.view_lupe_btn.setChecked(False)
        self.input_lupe_btn.setChecked(False)
        
        self.view_container.show()
        self.input_container.show()
        self.main_splitter.setSizes(self.saved_splitter_sizes)
        
        if self.multi_tab_manager and self.multi_tab_manager.multi_tab_active:
            self.multi_tab_manager.deactivate_multi_tab()
            self.multi_tab_btn.setChecked(False)
        
        self.show_status_message("🔄 Position wiederhergestellt")
    
    def show_status_message(self, message):
        """Zeigt Status-Nachricht an"""
        self.status_label.setText(message)
        logger.info(message)
        
        # Auto-Reset nach 3 Sekunden
        QTimer.singleShot(3000, lambda: self.status_label.setText("🎨 Dialog-Widget V3 - Bereit"))
    
    def on_splitter_moved(self, pos, index):
        """Speichert Splitter-Position"""
        self.saved_splitter_sizes = self.main_splitter.sizes()


# Demo-Anwendung
if __name__ == "__main__":
    import sys
    
    app = QApplication(sys.argv)
    
    call_daten = {
        "app": None,
        "user_guid": "demo-user-12345",
        "frame_guid": "demo-frame-67890",
        "language": "de",
        "stichtag": "2025185"
    }
    
    widget = UnifiedPdvmDialogWidget(call_daten)
    widget.setWindowTitle("PDVM Dialog Widget V3 - Multi-Tab Demo")
    widget.show()
    
    print("🎨 Demo gestartet - Verwende F4 für Multi-Tab-Modus!")
    sys.exit(app.exec_())
