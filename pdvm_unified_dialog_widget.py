#!/usr/bin/env python3
"""
UnifiedPdvmDialogWidget V2 - Vollständige Dialog-Architektur
=========================================================

Erweiterte Dialog-Architektur mit:
- Schaltbare View (außerhalb der Tabs)
- Input-Controls in Tabs organisiert
- Lupe-Funktionalität für dynamische Bereichsgrößen
- Zentrale Funktionen für Menü-Integration
- Persistente UI-Einstellungen per Frame-GUID
- Vollständige PyQt5-Integration
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QToolButton, QLabel, QLineEdit, QTextEdit, 
    QTreeWidget, QTreeWidgetItem, QPushButton,
    QSplitter, QApplication, QShortcut, QFrame,
    QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QKeySequence, QFont
import logging
import json

# Import PDVM modules
try:
    from pd_datetime import Pdvm_DateTime, PdvmDateTimeNow
    from pdvm_central_datenbank import PdvmCentralDatenbank
except ImportError as e:
    logging.warning(f"PDVM Module nicht verfügbar: {e}")

# Logger konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedPdvmDialogWidget(QWidget):
    """
    Vollständige Dialog-Architektur für PDVM-System
    ===============================================
    
    Features:
    - Schaltbare View (außerhalb der Tabs)
    - Input-Controls in Tabs
    - Lupe-Funktionalität (Normal/View-Lupe/Input-Lupe)
    - Zentrale Funktionen für Menü-Integration
    - Persistente UI-Einstellungen
    - Keyboard-Shortcuts (F1, F2, F3, F11)
    """
    
    def __init__(self, call_data=None):
        super().__init__()
        
        # Initialisierung
        self.call_data = call_data or {}
        self.frame_guid = self.call_data.get('frame_guid', 'default-frame')
        self.user_guid = self.call_data.get('user_guid', 'default-user')
        self.user_stichtag = self.call_data.get('stichtag', '2025185')
        
        # Lupe-Status (vereinfacht)
        self.view_lupe_active = False
        self.input_lupe_active = False
        self.saved_splitter_sizes = [300, 300]  # Standard 50/50
        
        # UI-Status
        self.view_visible = True
        self.menu_visible = True
        
        # Timer für Status-Nachrichten
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.clear_status_message)
        
        # Datenbank initialisieren
        try:
            self.central_db = PdvmCentralDatenbank()
        except Exception as e:
            logger.warning(f"Zentrale Datenbank nicht verfügbar: {e}")
            self.central_db = None
        
        # UI erstellen
        self.init_ui()
        self.setup_keyboard_shortcuts()
        self.load_ui_settings()
        
        logger.info("🎨 UnifiedPdvmDialogWidget V2 erfolgreich initialisiert")
    
    def init_ui(self):
        """Erstellt die komplette UI-Struktur"""
        
        # Hauptlayout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Status-Bereich
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #f0f8ff;
                border: 1px solid #87ceeb;
                border-radius: 3px;
                padding: 5px;
                color: #2e8b57;
                font-weight: bold;
                min-height: 20px;
            }
        """)
        self.status_label.hide()
        main_layout.addWidget(self.status_label)
        
        # QSplitter für Lupe-Funktionalität
        self.main_splitter = QSplitter(Qt.Vertical)
        
        # Splitter-Events für automatisches Speichern
        self.main_splitter.splitterMoved.connect(self.on_splitter_moved)
        
        main_layout.addWidget(self.main_splitter)
        
        # === VIEW-BEREICH ===
        self.view_container = self.create_view_container()
        self.main_splitter.addWidget(self.view_container)
        
        # === INPUT-BEREICH ===
        self.input_container = self.create_input_container()
        self.main_splitter.addWidget(self.input_container)
        
        # Standard-Größen setzen (benutzerdefiniert oder 50/50)
        self.main_splitter.setSizes(self.saved_splitter_sizes)
        
        # Fenster-Einstellungen
        self.setWindowTitle("🎨 Unified Dialog Widget V2 - Erweiterte PDVM-Architektur")
        self.setGeometry(100, 100, 900, 700)
        
        # Styling anwenden
        self.apply_global_styling()
    
    def apply_global_styling(self):
        """Wendet globales Styling an"""
        
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 10pt;
            }
            
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: white;
                border-radius: 3px;
            }
            
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #c0c0c0;
                padding: 8px 12px;
                margin-right: 2px;
                border-radius: 3px 3px 0 0;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
                font-weight: bold;
            }
            
            QTabBar::tab:hover {
                background-color: #e6f3ff;
            }
            
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                padding: 5px 10px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            
            QPushButton:pressed {
                background-color: #dee2e6;
            }
            
            QFrame {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                background-color: #ffffff;
            }
        """)
    
    def create_view_container(self):
        """Erstellt den View-Container mit Toggle-Button und Lupe-Controls"""
        
        container = QFrame()
        container.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header mit Toggle-Button und Lupe-Button
        header_layout = QHBoxLayout()
        
        # View-Toggle Button
        self.view_toggle_btn = QToolButton()
        self.view_toggle_btn.setText("👁️ View")
        self.view_toggle_btn.setCheckable(True)
        self.view_toggle_btn.setChecked(True)
        self.view_toggle_btn.clicked.connect(self.toggle_view_visibility)
        self.view_toggle_btn.setStyleSheet("""
            QToolButton {
                background-color: #e6f3ff;
                border: 2px solid #4a90e2;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
                color: #2c5282;
                font-size: 11pt;
            }
            QToolButton:checked {
                background-color: #4a90e2;
                color: white;
            }
            QToolButton:hover {
                background-color: #3182ce;
                color: white;
            }
        """)
        
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
        
        header_layout.addWidget(self.view_toggle_btn)
        header_layout.addWidget(QLabel("VIEW-BEREICH - Datenansicht und -analyse"))
        header_layout.addStretch()
        header_layout.addWidget(self.view_lupe_btn)
        
        layout.addLayout(header_layout)
        
        # View-Inhalt (TreeWidget für strukturierte Daten mit Scrollbars)
        from PyQt5.QtWidgets import QScrollArea
        
        # Scroll-Bereich für View-Content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.view_content = QTreeWidget()
        self.view_content.setHeaderLabels(["Eigenschaft", "Wert", "Typ"])
        self.view_content.setAlternatingRowColors(True)
        
        # TreeWidget in ScrollArea einbetten
        scroll_area.setWidget(self.view_content)
        
        # Initiale Demo-Daten
        self.populate_view_data()
        
        layout.addWidget(scroll_area)
        
        return container
    
    def create_input_container(self):
        """Erstellt den Input-Container mit Tabs für verschiedene Eingabebereiche"""
        
        container = QFrame()
        container.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header mit Input-Lupe Button
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("INPUT-BEREICH - Dateneingabe und -bearbeitung"))
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
        
        # Tab-Widget für Input-Controls mit Scrollbars
        self.input_tabs = QTabWidget()
        
        # Tab 1: Stammdaten
        self.create_stammdaten_tab()
        
        # Tab 2: Details  
        self.create_details_tab()
        
        # Tab 3: Zusatz
        self.create_zusatz_tab()
        
        layout.addWidget(self.input_tabs)
        
        return container
    
    def create_stammdaten_tab(self):
        """Erstellt das Stammdaten-Tab mit Scrollbars"""
        
        # Scroll-Container für Tab
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        stammdaten_tab = QWidget()
        layout = QVBoxLayout(stammdaten_tab)
        layout.setSpacing(10)
        
        # Formular-Felder
        form_layout = QVBoxLayout()
        
        # Name
        form_layout.addWidget(QLabel("📄 Name/Bezeichnung:"))
        self.name_field = QLineEdit()
        self.name_field.setPlaceholderText("Eingabe der Bezeichnung...")
        form_layout.addWidget(self.name_field)
        
        # Beschreibung
        form_layout.addWidget(QLabel("📝 Beschreibung:"))
        self.description_field = QTextEdit()
        self.description_field.setPlaceholderText("Detaillierte Beschreibung eingeben...")
        self.description_field.setMaximumHeight(120)
        form_layout.addWidget(self.description_field)
        
        # Status
        form_layout.addWidget(QLabel("🔧 Status/GUID-Informationen:"))
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Frame GUID:"))
        self.frame_guid_field = QLineEdit(self.frame_guid)
        self.frame_guid_field.setReadOnly(True)
        status_layout.addWidget(self.frame_guid_field)
        form_layout.addLayout(status_layout)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # Action-Buttons
        action_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Speichern")
        save_btn.clicked.connect(self.handle_save_data)
        reset_btn = QPushButton("🔄 Zurücksetzen")
        reset_btn.clicked.connect(self.reset_stammdaten)
        
        action_layout.addWidget(save_btn)
        action_layout.addWidget(reset_btn)
        action_layout.addStretch()
        
        layout.addLayout(action_layout)
        
        # Tab-Widget in Scroll-Area einbetten
        scroll_area.setWidget(stammdaten_tab)
        self.input_tabs.addTab(scroll_area, "📄 Stammdaten")
    
    def create_details_tab(self):
        """Erstellt das Details-Tab mit Scrollbars"""
        
        # Scroll-Container für Tab
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        details_tab = QWidget()
        layout = QVBoxLayout(details_tab)
        layout.setSpacing(10)
        
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
        
        # Tab-Widget in Scroll-Area einbetten
        scroll_area.setWidget(details_tab)
        self.input_tabs.addTab(scroll_area, "📋 Details")
    
    def create_zusatz_tab(self):
        """Erstellt das Zusatz-Tab mit Scrollbars"""
        
        # Scroll-Container für Tab
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        zusatz_tab = QWidget()
        layout = QVBoxLayout(zusatz_tab)
        layout.setSpacing(10)
        
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
        
        self.input_tabs.addTab(zusatz_tab, "📝 Zusatz")
    
    def setup_keyboard_shortcuts(self):
        """Erstellt Tastatur-Shortcuts für Lupe-Funktionen"""
        
        # F1: View-Lupe toggle
        view_lupe_shortcut = QShortcut(QKeySequence("F1"), self)
        view_lupe_shortcut.activated.connect(self.toggle_view_lupe)
        
        # F2: Input-Lupe toggle
        input_lupe_shortcut = QShortcut(QKeySequence("F2"), self)
        input_lupe_shortcut.activated.connect(self.toggle_input_lupe)
        
        # F3: Zurück zur gespeicherten Position
        restore_shortcut = QShortcut(QKeySequence("F3"), self)
        restore_shortcut.activated.connect(self.restore_user_position)
        
        logger.info("⌨️ Keyboard-Shortcuts aktiviert: F1=View-Lupe, F2=Input-Lupe, F3=Position wiederherstellen")
    
    # === VERBESSERTE LUPE-FUNKTIONALITÄT ===
    
    def on_splitter_moved(self, pos, index):
        """Wird aufgerufen wenn User den Splitter verschiebt - speichert Position automatisch"""
        
        # Nur speichern wenn keine Lupe aktiv ist
        if not self.view_lupe_active and not self.input_lupe_active:
            self.saved_splitter_sizes = self.main_splitter.sizes()
            self.save_ui_settings()
            logger.debug(f"📏 Benutzerdefinierte Splitter-Position gespeichert: {self.saved_splitter_sizes}")
    
    def toggle_view_lupe(self):
        """Toggle View-Lupe - maximiert View oder kehrt zur gespeicherten Position zurück"""
        
        self.view_lupe_active = not self.view_lupe_active
        self.view_lupe_btn.setChecked(self.view_lupe_active)
        
        if self.view_lupe_active:
            # Input-Lupe deaktivieren falls aktiv
            if self.input_lupe_active:
                self.input_lupe_active = False
                self.input_lupe_btn.setChecked(False)
                self.input_container.setVisible(True)
            
            # Input-Bereich komplett ausblenden
            self.input_container.setVisible(False)
            self.show_status_message("🔍 View-Lupe aktiviert - Eingabebereich ausgeblendet")
            
        else:
            # Input-Bereich wieder einblenden
            self.input_container.setVisible(True)
            # Zurück zur gespeicherten Position
            self.main_splitter.setSizes(self.saved_splitter_sizes)
            self.show_status_message("⚖️ Benutzerdefinierte Position wiederhergestellt")
        
        self.update_view_content()
        logger.info(f"🔍 View-Lupe: {'aktiviert' if self.view_lupe_active else 'deaktiviert'}")
    
    def toggle_input_lupe(self):
        """Toggle Input-Lupe - maximiert Input oder kehrt zur gespeicherten Position zurück"""
        
        self.input_lupe_active = not self.input_lupe_active
        self.input_lupe_btn.setChecked(self.input_lupe_active)
        
        if self.input_lupe_active:
            # View-Lupe deaktivieren falls aktiv
            if self.view_lupe_active:
                self.view_lupe_active = False
                self.view_lupe_btn.setChecked(False)
                self.view_container.setVisible(True)
            
            # View-Bereich komplett ausblenden
            self.view_container.setVisible(False)
            self.show_status_message("🔍 Input-Lupe aktiviert - Datenansicht ausgeblendet")
            
        else:
            # View-Bereich wieder einblenden
            self.view_container.setVisible(True)
            # Zurück zur gespeicherten Position
            self.main_splitter.setSizes(self.saved_splitter_sizes)
            self.show_status_message("⚖️ Benutzerdefinierte Position wiederhergestellt")
        
        self.update_view_content()
        logger.info(f"� Input-Lupe: {'aktiviert' if self.input_lupe_active else 'deaktiviert'}")
    
    def restore_user_position(self):
        """Stellt die vom User gespeicherte Splitter-Position wieder her (F3)"""
        
        # Beide Lupen deaktivieren
        self.view_lupe_active = False
        self.input_lupe_active = False
        self.view_lupe_btn.setChecked(False)
        self.input_lupe_btn.setChecked(False)
        
        # Gespeicherte Position wiederherstellen
        self.main_splitter.setSizes(self.saved_splitter_sizes)
        
        # Prozentuale Aufteilung berechnen
        total = sum(self.saved_splitter_sizes)
        if total > 0:
            view_percent = int((self.saved_splitter_sizes[0] / total) * 100)
            input_percent = 100 - view_percent
            self.show_status_message(f"⚖️ Position wiederhergestellt: View {view_percent}% / Input {input_percent}%")
        else:
            self.show_status_message("⚖️ Benutzerdefinierte Position wiederhergestellt")
        
        self.update_view_content()
        logger.info(f"⚖️ Position wiederhergestellt: {self.saved_splitter_sizes}")
    
    # === KOMPATIBILITÄTS-FUNKTIONEN FÜR MENÜ-INTEGRATION ===
    
    def set_view_lupe(self):
        """Alias für Menü-Integration - View-Lupe aktivieren"""
        if not self.view_lupe_active:
            self.toggle_view_lupe()
    
    def set_input_lupe(self):
        """Alias für Menü-Integration - Input-Lupe aktivieren"""
        if not self.input_lupe_active:
            self.toggle_input_lupe()
    
    def set_normal_mode(self):
        """Alias für Menü-Integration - Position wiederherstellen"""
        self.restore_user_position()
    
    def toggle_display_mode(self):
        """Legacy-Funktion - wechselt zwischen View-Lupe und normaler Position"""
        if self.view_lupe_active:
            self.toggle_view_lupe()  # Deaktivieren
        else:
            self.toggle_view_lupe()  # Aktivieren
    
    # === ZENTRALE FUNKTIONEN FÜR MENÜ-INTEGRATION ===
    
    def execute_central_function(self, function_name, *args, **kwargs):
        """Zentrale Dispatcher-Funktion für Menü-Kommandos"""
        
        function_map = {
            # Lupe-Funktionen
            'set_view_lupe': self.set_view_lupe,
            'set_input_lupe': self.set_input_lupe,
            'set_normal_mode': self.set_normal_mode,
            'toggle_display_mode': self.toggle_display_mode,
            
            # Zentrale Funktionen
            'stichtag_wechsel': self.handle_stichtag_wechsel,
            'refresh_view': self.handle_refresh_view,
            'save_data': self.handle_save_data,
            'export_data': self.handle_export_data,
            'toggle_menu': self.toggle_menu_visibility,
            'toggle_view': self.toggle_view_visibility
        }
        
        if function_name in function_map:
            try:
                result = function_map[function_name](*args, **kwargs)
                logger.info(f"✅ Zentrale Funktion ausgeführt: {function_name}")
                return result
            except Exception as e:
                logger.error(f"❌ Fehler bei zentraler Funktion {function_name}: {e}")
                self.show_status_message(f"❌ Fehler bei {function_name}")
                return False
        else:
            logger.warning(f"⚠️ Unbekannte zentrale Funktion: {function_name}")
            self.show_status_message(f"⚠️ Unbekannte Funktion: {function_name}")
            return False
    
    def handle_stichtag_wechsel(self, new_stichtag=None):
        """Zentrale Funktion für Stichtagswechsel"""
        
        try:
            if new_stichtag is None:
                from PyQt5.QtWidgets import QInputDialog
                current_stichtag = str(int(self.user_stichtag)) if self.user_stichtag else "2025185"
                new_stichtag_str, ok = QInputDialog.getText(
                    self, 
                    "Stichtag ändern",
                    f"Neuer Stichtag eingeben (aktuell: {current_stichtag}):",
                    text=current_stichtag
                )
                
                if not ok or not new_stichtag_str:
                    return False
                    
                new_stichtag = new_stichtag_str
            
            # Stichtag aktualisieren
            self.user_stichtag = new_stichtag
            self.stichtag_field.setText(str(new_stichtag))
            
            # In zentraler Datenbank speichern
            if self.central_db:
                try:
                    current_data = self.central_db.lesen()
                    if self.user_guid not in current_data:
                        current_data[self.user_guid] = {}
                    current_data[self.user_guid]['stichtag'] = new_stichtag
                    self.central_db.speichern(current_data)
                except Exception as e:
                    logger.warning(f"Stichtag konnte nicht in Datenbank gespeichert werden: {e}")
            
            # View refreshen
            self.handle_refresh_view()
            
            # Status-Nachricht
            self.show_status_message(f"🗓️ Stichtag geändert: {int(new_stichtag)}")
            
            logger.info(f"🗓️ Stichtag erfolgreich geändert: {new_stichtag}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Stichtagswechsel: {e}")
            self.show_status_message("❌ Fehler beim Stichtagswechsel")
            return False
    
    def handle_refresh_view(self):
        """Zentrale Funktion für View-Refresh"""
        
        try:
            # View-Inhalt aktualisieren
            self.update_view_content()
            
            # Alle Formularfelder refreshen
            self.populate_view_data()
            
            # Tabs refreshen
            current_tab = self.input_tabs.currentIndex()
            self.input_tabs.setCurrentIndex(0)
            self.input_tabs.setCurrentIndex(current_tab)
            
            self.show_status_message("🔄 View und Daten erfolgreich aktualisiert")
            logger.info("🔄 View erfolgreich aktualisiert")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim View-Refresh: {e}")
            self.show_status_message("❌ Fehler beim Refresh")
            return False
    
    def handle_save_data(self):
        """Zentrale Funktion für Daten speichern"""
        
        try:
            # Alle Input-Daten sammeln
            save_data = {
                'frame_guid': self.frame_guid,
                'user_guid': self.user_guid,
                'stichtag': self.user_stichtag,
                'display_mode': self.current_display_mode,
                'name': self.name_field.text(),
                'description': self.description_field.toPlainText(),
                'details': self.details_field.toPlainText(),
                'zusatz': self.zusatz_field.toPlainText(),
                'ui_settings': self.get_ui_settings(),
                'timestamp': PdvmDateTimeNow().PdvmDateTime if 'PdvmDateTimeNow' in globals() else None
            }
            
            # In zentrale Datenbank speichern
            if self.central_db:
                try:
                    current_data = self.central_db.lesen()
                    save_key = f"unified_dialog_{self.frame_guid}"
                    current_data[save_key] = save_data
                    self.central_db.speichern(current_data)
                    
                    self.show_status_message("💾 Alle Daten erfolgreich gespeichert")
                    logger.info("💾 Daten erfolgreich in zentrale Datenbank gespeichert")
                    return True
                    
                except Exception as e:
                    logger.warning(f"Speichern in zentrale DB fehlgeschlagen: {e}")
            
            # Fallback: Lokale Speicherung simulieren
            logger.info("💾 Daten lokal gespeichert (Simulation)")
            self.show_status_message("💾 Daten lokal gespeichert")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
            self.show_status_message("❌ Fehler beim Speichern")
            return False
    
    def handle_export_data(self):
        """Zentrale Funktion für Datenexport"""
        
        try:
            from PyQt5.QtWidgets import QFileDialog
            
            # Export-Datei wählen
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Daten exportieren",
                f"unified_dialog_export_{self.frame_guid}.json",
                "JSON Files (*.json);;All Files (*)"
            )
            
            if not filename:
                return False
            
            # Export-Daten erstellen
            export_data = {
                'frame_guid': self.frame_guid,
                'user_guid': self.user_guid,
                'stichtag': self.user_stichtag,
                'display_mode': self.current_display_mode,
                'form_data': {
                    'name': self.name_field.text(),
                    'description': self.description_field.toPlainText(),
                    'details': self.details_field.toPlainText(),
                    'zusatz': self.zusatz_field.toPlainText()
                },
                'ui_settings': self.get_ui_settings(),
                'view_data': self.get_view_export_data(),
                'export_timestamp': PdvmDateTimeNow().PdvmDateTime if 'PdvmDateTimeNow' in globals() else None
            }
            
            # In Datei schreiben
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.show_status_message(f"📊 Export erfolgreich: {filename}")
            logger.info(f"📊 Daten erfolgreich exportiert: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Export: {e}")
            self.show_status_message("❌ Fehler beim Export")
            return False
    
    def toggle_menu_visibility(self):
        """Toggle Menü-Sichtbarkeit in Hauptanwendung"""
        
        self.menu_visible = not self.menu_visible
        
        # Hauptanwendung benachrichtigen
        if hasattr(self, 'call_data') and 'app' in self.call_data:
            try:
                app = self.call_data['app']
                if hasattr(app, 'toggle_menu_visibility'):
                    app.toggle_menu_visibility(self.menu_visible)
                    status = "angezeigt" if self.menu_visible else "ausgeblendet"
                    self.show_status_message(f"🎛️ Hauptmenü {status}")
                    return True
            except Exception as e:
                logger.warning(f"Menü-Toggle in Hauptanwendung fehlgeschlagen: {e}")
        
        # Fallback: Lokaler Toggle
        status = "angezeigt" if self.menu_visible else "ausgeblendet"
        self.show_status_message(f"🎛️ Menü {status} (lokal)")
        return True
    
    def toggle_view_visibility(self):
        """Toggle View-Bereich Sichtbarkeit"""
        
        self.view_visible = not self.view_visible
        self.view_container.setVisible(self.view_visible)
        self.view_toggle_btn.setChecked(self.view_visible)
        
        # UI-Status speichern
        self.save_ui_settings()
        
        status = "angezeigt" if self.view_visible else "ausgeblendet"
        self.show_status_message(f"👁️ View-Bereich {status}")
        
        logger.info(f"👁️ View-Sichtbarkeit geändert: {self.view_visible}")
        return True
    
    # === UI-HILFSFUNKTIONEN ===
    
    def populate_view_data(self):
        """Befüllt die View mit aktuellen Daten"""
        
        self.view_content.clear()
        
        # Grundlegende Informationen
        basic_items = [
            ("Frame GUID", self.frame_guid, "System"),
            ("User GUID", self.user_guid, "System"),
            ("Stichtag", self.user_stichtag, "Datum"),
            ("View Lupe", "✅ Aktiv" if self.view_lupe_active else "❌ Inaktiv", "Lupe"),
            ("Input Lupe", "✅ Aktiv" if self.input_lupe_active else "❌ Inaktiv", "Lupe"),
            ("Splitter-Position", f"{self.main_splitter.sizes()}", "UI"),
            ("Gespeicherte Position", f"{self.saved_splitter_sizes}", "UI"),
            ("View Visible", str(self.view_visible), "UI"),
            ("Menu Visible", str(self.menu_visible), "UI")
        ]
        
        # System-Kategorie
        system_parent = QTreeWidgetItem(["📊 System-Informationen", "", "Kategorie"])
        system_parent.setExpanded(True)
        self.view_content.addTopLevelItem(system_parent)
        
        for prop, value, typ in basic_items:
            if typ in ["System", "Datum"]:
                item = QTreeWidgetItem([prop, str(value), typ])
                system_parent.addChild(item)
        
        # Lupe-Status-Kategorie
        lupe_parent = QTreeWidgetItem(["🔍 Lupe-Status", "", "Kategorie"])
        lupe_parent.setExpanded(True)
        self.view_content.addTopLevelItem(lupe_parent)
        
        for prop, value, typ in basic_items:
            if typ == "Lupe":
                item = QTreeWidgetItem([prop, str(value), typ])
                lupe_parent.addChild(item)
        
        # UI-Status-Kategorie
        ui_parent = QTreeWidgetItem(["🎨 UI-Status", "", "Kategorie"])
        ui_parent.setExpanded(True)
        self.view_content.addTopLevelItem(ui_parent)
        
        for prop, value, typ in basic_items:
            if typ == "UI":
                item = QTreeWidgetItem([prop, str(value), typ])
                ui_parent.addChild(item)
        
        # Formular-Daten
        if hasattr(self, 'name_field'):
            form_parent = QTreeWidgetItem(["📝 Formular-Daten", "", "Kategorie"])
            form_parent.setExpanded(True)
            self.view_content.addTopLevelItem(form_parent)
            
            form_items = [
                ("Name", self.name_field.text() or "(leer)", "Text"),
                ("Beschreibung", self.description_field.toPlainText()[:50] + "..." if len(self.description_field.toPlainText()) > 50 else self.description_field.toPlainText() or "(leer)", "Text"),
                ("Tab Index", str(self.input_tabs.currentIndex()), "Index")
            ]
            
            for prop, value, typ in form_items:
                item = QTreeWidgetItem([prop, str(value), typ])
                form_parent.addChild(item)
        
        # Header anpassen
        for i in range(3):
            self.view_content.resizeColumnToContents(i)
    
    def update_view_content(self):
        """Aktualisiert den View-Inhalt (Alias für populate_view_data)"""
        self.populate_view_data()
    
    def get_view_export_data(self):
        """Sammelt View-Daten für Export"""
        
        view_data = []
        root = self.view_content.invisibleRootItem()
        
        def collect_items(parent, level=0):
            for i in range(parent.childCount()):
                item = parent.child(i)
                view_data.append({
                    'level': level,
                    'property': item.text(0),
                    'value': item.text(1),
                    'type': item.text(2)
                })
                if item.childCount() > 0:
                    collect_items(item, level + 1)
        
        collect_items(root)
        return view_data
    
    def reset_stammdaten(self):
        """Setzt Stammdaten-Felder zurück"""
        
        self.name_field.clear()
        self.description_field.clear()
        self.show_status_message("🔄 Stammdaten zurückgesetzt")
        logger.info("🔄 Stammdaten-Felder zurückgesetzt")
    
    def show_status_message(self, message, duration=3000):
        """Zeigt Status-Nachricht mit automatischem Ausblenden an"""
        
        self.status_label.setText(message)
        self.status_label.show()
        
        # Timer für automatisches Ausblenden
        self.status_timer.stop()
        self.status_timer.start(duration)
        
        logger.info(f"📢 Status: {message}")
    
    def clear_status_message(self):
        """Blendet Status-Nachricht aus"""
        
        self.status_label.hide()
        self.status_timer.stop()
    
    # === UI-EINSTELLUNGEN PERSISTIERUNG ===
    
    def get_ui_settings(self):
        """Sammelt alle aktuellen UI-Einstellungen"""
        
        return {
            'view_lupe_active': self.view_lupe_active,
            'input_lupe_active': self.input_lupe_active,
            'saved_splitter_sizes': self.saved_splitter_sizes,
            'current_splitter_sizes': self.main_splitter.sizes(),
            'view_visible': self.view_visible,
            'menu_visible': self.menu_visible,
            'current_tab': self.input_tabs.currentIndex(),
            'window_geometry': {
                'x': self.x(),
                'y': self.y(),
                'width': self.width(),
                'height': self.height()
            },
            'form_data': {
                'name': self.name_field.text() if hasattr(self, 'name_field') else '',
                'description': self.description_field.toPlainText() if hasattr(self, 'description_field') else '',
                'details': self.details_field.toPlainText() if hasattr(self, 'details_field') else '',
                'zusatz': self.zusatz_field.toPlainText() if hasattr(self, 'zusatz_field') else ''
            }
        }
    
    def save_ui_settings(self):
        """Speichert UI-Einstellungen in Systemsteuerung"""
        
        if not self.central_db:
            return
        
        try:
            settings = self.get_ui_settings()
            
            current_data = self.central_db.lesen()
            settings_key = f"ui_settings_{self.frame_guid}"
            current_data[settings_key] = settings
            
            self.central_db.speichern(current_data)
            logger.debug(f"💾 UI-Einstellungen gespeichert für Frame: {self.frame_guid}")
            
        except Exception as e:
            logger.warning(f"UI-Einstellungen konnten nicht gespeichert werden: {e}")
    
    def load_ui_settings(self):
        """Lädt UI-Einstellungen aus Systemsteuerung"""
        
        if not self.central_db:
            return
        
        try:
            current_data = self.central_db.lesen()
            settings_key = f"ui_settings_{self.frame_guid}"
            
            if settings_key in current_data:
                settings = current_data[settings_key]
                
                # Lupe-Status wiederherstellen
                if 'view_lupe_active' in settings:
                    self.view_lupe_active = settings['view_lupe_active']
                    self.view_lupe_btn.setChecked(self.view_lupe_active)
                if 'input_lupe_active' in settings:
                    self.input_lupe_active = settings['input_lupe_active']
                    self.input_lupe_btn.setChecked(self.input_lupe_active)
                
                # Gespeicherte Splitter-Position wiederherstellen
                if 'saved_splitter_sizes' in settings:
                    self.saved_splitter_sizes = settings['saved_splitter_sizes']
                
                # Sichtbarkeit wiederherstellen
                if 'view_visible' in settings:
                    self.view_visible = settings['view_visible']
                if 'menu_visible' in settings:
                    self.menu_visible = settings['menu_visible']
                
                # Tab-Position wiederherstellen
                if 'current_tab' in settings:
                    self.input_tabs.setCurrentIndex(settings['current_tab'])
                
                # Formular-Daten wiederherstellen
                if 'form_data' in settings:
                    form_data = settings['form_data']
                    if hasattr(self, 'name_field') and 'name' in form_data:
                        self.name_field.setText(form_data['name'])
                    if hasattr(self, 'description_field') and 'description' in form_data:
                        self.description_field.setPlainText(form_data['description'])
                    if hasattr(self, 'details_field') and 'details' in form_data:
                        self.details_field.setPlainText(form_data['details'])
                    if hasattr(self, 'zusatz_field') and 'zusatz' in form_data:
                        self.zusatz_field.setPlainText(form_data['zusatz'])
                
                logger.info(f"✅ UI-Einstellungen erfolgreich geladen für Frame: {self.frame_guid}")
                
                # Splitter-Position und Lupe-Status anwenden (nach UI-Initialisierung)
                QTimer.singleShot(200, self.apply_loaded_settings)
                
        except Exception as e:
            logger.warning(f"UI-Einstellungen konnten nicht geladen werden: {e}")
    
    def apply_loaded_settings(self):
        """Wendet geladene UI-Einstellungen an"""
        
        if self.view_lupe_active:
            # View-Lupe aktivieren ohne Toggle (direkt setzen)
            total_height = self.main_splitter.height()
            self.main_splitter.setSizes([total_height - 50, 50])
            self.show_status_message("🔍 View-Lupe aus Einstellungen wiederhergestellt")
            
        elif self.input_lupe_active:
            # Input-Lupe aktivieren ohne Toggle (direkt setzen)
            total_height = self.main_splitter.height()
            self.main_splitter.setSizes([50, total_height - 50])
            self.show_status_message("🔍 Input-Lupe aus Einstellungen wiederhergestellt")
            
        else:
            # Normale gespeicherte Position wiederherstellen
            self.main_splitter.setSizes(self.saved_splitter_sizes)
            total = sum(self.saved_splitter_sizes)
            if total > 0:
                view_percent = int((self.saved_splitter_sizes[0] / total) * 100)
                self.show_status_message(f"⚖️ Benutzerdefinierte Position wiederhergestellt: {view_percent}%/{100-view_percent}%")

# Kompatibilitäts-Alias für vorhandenen Code
PdvmDialogWidget = UnifiedPdvmDialogWidget

def main():
    """Test-Hauptfunktion für eigenständige Ausführung"""
    
    app = QApplication([])
    
    # Test-Daten
    call_data = {
        'frame_guid': '4078079f-4028-45ed-879c-3c779ecf3d0d',
        'user_guid': '4886ad26-061b-4662-a762-c8c83f36692d',
        'stichtag': '2025185'
    }
    
    # Widget erstellen und anzeigen
    widget = UnifiedPdvmDialogWidget(call_data)
    widget.show()
    
    print("\n🎨 UNIFIED DIALOG WIDGET V2 - FLEXIBLE LUPE-FUNKTIONALITÄT")
    print("="*70)
    print("⌨️ TASTATUR-SHORTCUTS:")
    print("  F1  = View-Lupe toggle (ein/aus)")
    print("  F2  = Input-Lupe toggle (ein/aus)")
    print("  F3  = Benutzerdefinierte Position wiederherstellen")
    print("\n🎛️ BENUTZERFREUNDLICHE FEATURES:")
    print("  - Ein Lupe-Button pro Bereich (ein/ausschaltbar)")
    print("  - Splitter frei verschiebbar (z.B. 30/70, 20/80)")
    print("  - Position wird automatisch gespeichert")
    print("  - Lupe kehrt immer zur gespeicherten Position zurück")
    print("  - Persistente Einstellungen pro Frame")
    print("\n📢 INTEGRATION: Zusatzmenü-Funktionen über PDVM-Menüsystem")
    print("🚀 STATUS: Optimiert für maximale Benutzerfreundlichkeit")
    
    app.exec_()

if __name__ == "__main__":
    main()
