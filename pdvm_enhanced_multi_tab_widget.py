# pdvm_enhanced_multi_tab_widget.py
# -*- coding: utf-8 -*-

"""
Enhanced Multi-Tab Widget für PDVM-System
==========================================

Erweiterte Multi-Tab-Funktionalität mit:
- Smart Tab-Anzeige (aktiver Tab + nächste 1-2 rechts davon)
- Frame-basierte Konfiguration aus framedaten
- Benutzer-Einstellungen in systemsteuerung
- Echte Datenausgabe in allen Split-Views
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QLabel, QLineEdit, QTextEdit, QPushButton, QCheckBox,
    QTreeWidget, QTreeWidgetItem, QComboBox,
    QSplitter, QApplication, QShortcut, QFrame,
    QScrollArea, QSizePolicy, QButtonGroup, QRadioButton,
    QSpinBox, QGroupBox, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QKeySequence, QFont
import logging
import json
from typing import Dict, List, Optional, Any

# Import PDVM modules (optional)
try:
    from pdvm_central_datenbank import PdvmCentralDatenbank
    PDVM_AVAILABLE = True
except ImportError as e:
    logging.warning(f"PDVM Module nicht verfügbar: {e}")
    PDVM_AVAILABLE = False

# Logger konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedMultiTabManager:
    """Erweiteter Multi-Tab-Manager mit Smart Tab-Anzeige und Konfiguration"""
    
    def __init__(self, parent_widget, tab_widget, frame_guid=None, user_guid=None):
        self.parent = parent_widget
        self.original_tabs = tab_widget
        self.frame_guid = frame_guid
        self.user_guid = user_guid
        
        # Multi-Tab-Status
        self.multi_tab_active = False
        self.current_splitter = None
        self.saved_tabs = []
        
        # Konfiguration
        self.config = self.load_multi_tab_config()
        self.settings = self.load_user_settings()
        
        # Tab-Verfolgung
        self.active_tab_index = 0
        self.all_tab_widgets = []
        self.all_tab_texts = []
        self.displayed_tab_indices = []  # Aktuell angezeigte Tab-Indizes
        
        # Tab-Navigation im Multi-Tab-Modus
        self.tab_navigation_widget = None
        self.tab_nav_buttons = []
        self.tab_nav_dropdown = None
        
        # Initiale Tab-Daten sammeln
        self.collect_initial_tab_data()
        
    def collect_initial_tab_data(self):
        """Sammelt alle Tab-Daten für Smart-Anzeige"""
        self.all_tab_widgets.clear()
        self.all_tab_texts.clear()
        
        for i in range(self.original_tabs.count()):
            widget = self.original_tabs.widget(i)
            text = self.original_tabs.tabText(i)
            self.all_tab_widgets.append(widget)
            self.all_tab_texts.append(text)
        
        # Aktiven Tab merken
        self.active_tab_index = self.original_tabs.currentIndex()
        
        logger.info(f"📋 {len(self.all_tab_widgets)} Tabs gesammelt, aktiver Index: {self.active_tab_index}")
    
    def load_multi_tab_config(self):
        """Lädt Multi-Tab-Konfiguration aus Framedaten"""
        default_config = {
            "multi_tab_enabled": True,
            "max_tabs_display": 2,
            "layout_orientation": "horizontal",  # horizontal, vertical
            "tab_selection_mode": "smart",  # smart, manual, all
            "allow_user_override": True,
            "default_active": False
        }
        
        if not PDVM_AVAILABLE or not self.frame_guid:
            return default_config
        
        try:
            # Framedaten aus Datenbank laden
            db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="framedaten",
                guid=self.frame_guid
            )
            
            frame_data = db.lesen()
            if frame_data and isinstance(frame_data, dict):
                # Multi-Tab-Konfiguration aus framedaten extrahieren
                multi_tab_config = frame_data.get("multi_tab_config", {})
                if multi_tab_config:
                    # Default-Werte überschreiben
                    for key, value in multi_tab_config.items():
                        if key in default_config:
                            default_config[key] = value
                    logger.info(f"📊 Multi-Tab-Konfiguration aus framedaten geladen: {multi_tab_config}")
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Laden der Multi-Tab-Konfiguration: {e}")
        
        return default_config
    
    def load_user_settings(self):
        """Lädt Benutzer-Einstellungen aus systemsteuerung"""
        default_settings = {
            "preferred_layout": "horizontal",
            "max_tabs_display": 2,
            "auto_activate": False,
            "remember_state": True
        }
        
        if not PDVM_AVAILABLE or not self.user_guid or not self.frame_guid:
            return default_settings
        
        try:
            # Systemsteuerung für Benutzer laden
            sys_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="systemsteuerung",
                guid=self.user_guid
            )
            
            raw_data = sys_db.lesen() or {}
            user_data = raw_data.get(self.user_guid, {})
            
            # Multi-Tab-Einstellungen unter Frame-GUID
            multi_tab_settings = user_data.get("MultiTabSettings", {})
            frame_settings = multi_tab_settings.get(self.frame_guid, {})
            
            if frame_settings:
                # Benutzer-Einstellungen übernehmen
                for key, value in frame_settings.items():
                    if key in default_settings:
                        default_settings[key] = value
                logger.info(f"👤 Benutzer-Einstellungen für Frame {self.frame_guid} geladen: {frame_settings}")
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Laden der Benutzer-Einstellungen: {e}")
        
        return default_settings
    
    def save_user_settings(self):
        """Speichert Benutzer-Einstellungen in systemsteuerung"""
        if not PDVM_AVAILABLE or not self.user_guid or not self.frame_guid:
            return
        
        try:
            sys_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="systemsteuerung",
                guid=self.user_guid
            )
            
            # Aktuelle Daten laden
            raw_data = sys_db.lesen() or {}
            user_data = raw_data.get(self.user_guid, {})
            
            # MultiTabSettings-Struktur initialisieren
            if "MultiTabSettings" not in user_data:
                user_data["MultiTabSettings"] = {}
            
            # Frame-spezifische Einstellungen speichern
            user_data["MultiTabSettings"][self.frame_guid] = self.settings.copy()
            
            # Zurück in Datenbank speichern
            raw_data[self.user_guid] = user_data
            sys_db.speichern(self.user_guid, raw_data)
            
            logger.info(f"💾 Multi-Tab-Einstellungen für Frame {self.frame_guid} gespeichert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Einstellungen: {e}")
    
    def get_smart_tab_selection(self):
        """Ermittelt Smart Tab-Auswahl basierend auf aktivem Tab"""
        if not self.all_tab_widgets:
            return []
        
        total_tabs = len(self.all_tab_widgets)
        max_display = min(self.settings["max_tabs_display"], total_tabs)
        
        if max_display >= total_tabs:
            # Alle Tabs anzeigen
            return list(range(total_tabs))
        
        # Smart-Auswahl: Aktiver Tab + nächste rechts (mit Wraparound)
        selected_indices = []
        for i in range(max_display):
            index = (self.active_tab_index + i) % total_tabs
            selected_indices.append(index)
        
        logger.info(f"🎯 Smart Tab-Auswahl: Indices {selected_indices} von {total_tabs} Tabs")
        self.displayed_tab_indices = selected_indices  # Merken für Navigation
        return selected_indices
    
    def create_tab_navigation_widget(self):
        """Erstellt Tab-Navigation für Multi-Tab-Modus"""
        if self.tab_navigation_widget:
            return self.tab_navigation_widget
        
        nav_widget = QWidget()
        nav_layout = QHBoxLayout(nav_widget)
        nav_layout.setContentsMargins(5, 5, 5, 5)
        
        # Info-Label
        info_label = QLabel("📱 Multi-Tab Navigation:")
        info_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        nav_layout.addWidget(info_label)
        
        # Tab-Buttons für alle verfügbaren Tabs
        self.tab_nav_buttons = []
        for i, tab_text in enumerate(self.all_tab_texts):
            btn = QPushButton(f"{i+1}. {tab_text}")
            btn.setMaximumWidth(120)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, idx=i: self.navigate_to_tab(idx))
            
            # Aktive Tabs hervorheben
            if i in self.displayed_tab_indices:
                btn.setChecked(True)
                btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
            else:
                btn.setStyleSheet("background-color: #E0E0E0; color: #333;")
            
            self.tab_nav_buttons.append(btn)
            nav_layout.addWidget(btn)
        
        nav_layout.addStretch()
        
        # Dropdown für Tab-Wechsel
        nav_layout.addWidget(QLabel("🔄 Tab wechseln:"))
        self.tab_nav_dropdown = QComboBox()
        for i, tab_text in enumerate(self.all_tab_texts):
            self.tab_nav_dropdown.addItem(f"{i+1}. {tab_text}", i)
        
        self.tab_nav_dropdown.setCurrentIndex(self.active_tab_index)
        self.tab_nav_dropdown.currentIndexChanged.connect(self.on_dropdown_tab_change)
        nav_layout.addWidget(self.tab_nav_dropdown)
        
        # Navigation-Buttons
        prev_btn = QPushButton("◀ Vorheriger")
        prev_btn.clicked.connect(self.navigate_previous_tab)
        nav_layout.addWidget(prev_btn)
        
        next_btn = QPushButton("Nächster ▶")
        next_btn.clicked.connect(self.navigate_next_tab)
        nav_layout.addWidget(next_btn)
        
        self.tab_navigation_widget = nav_widget
        return nav_widget
    
    def navigate_to_tab(self, target_index):
        """Navigiert zu einem spezifischen Tab"""
        if target_index < 0 or target_index >= len(self.all_tab_widgets):
            return
        
        old_active = self.active_tab_index
        self.active_tab_index = target_index
        
        logger.info(f"🔄 Tab-Navigation: {old_active} → {target_index} ({self.all_tab_texts[target_index]})")
        
        # Multi-Tab-Anzeige aktualisieren
        if self.multi_tab_active:
            self.refresh_multi_tab_display()
        
        # Dropdown aktualisieren
        if self.tab_nav_dropdown:
            self.tab_nav_dropdown.setCurrentIndex(target_index)
    
    def navigate_previous_tab(self):
        """Navigiert zum vorherigen Tab (mit Wraparound)"""
        total_tabs = len(self.all_tab_widgets)
        if total_tabs <= 1:
            return
        
        prev_index = (self.active_tab_index - 1) % total_tabs
        self.navigate_to_tab(prev_index)
    
    def navigate_next_tab(self):
        """Navigiert zum nächsten Tab (mit Wraparound)"""
        total_tabs = len(self.all_tab_widgets)
        if total_tabs <= 1:
            return
        
        next_index = (self.active_tab_index + 1) % total_tabs
        self.navigate_to_tab(next_index)
    
    def on_dropdown_tab_change(self, index):
        """Handler für Dropdown-Tab-Wechsel"""
        if index >= 0 and index < len(self.all_tab_widgets):
            self.navigate_to_tab(index)
    
    def refresh_multi_tab_display(self):
        """Aktualisiert die Multi-Tab-Anzeige nach Tab-Navigation"""
        if not self.multi_tab_active:
            return
        
        try:
            # Neue Smart-Auswahl basierend auf aktivem Tab
            new_selection = self.get_smart_tab_selection()
            
            # Nur aktualisieren wenn sich die Auswahl geändert hat
            if new_selection != self.displayed_tab_indices:
                logger.info(f"🔄 Multi-Tab-Display wird aktualisiert: {self.displayed_tab_indices} → {new_selection}")
                
                # Multi-Tab deaktivieren und neu aktivieren
                self.deactivate_multi_tab()
                self.activate_multi_tab()
                
                # Navigation-Widget aktualisieren
                self.update_navigation_widget()
        
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der Multi-Tab-Anzeige: {e}")
    
    def update_navigation_widget(self):
        """Aktualisiert das Navigation-Widget"""
        if not self.tab_nav_buttons:
            return
        
        # Button-Status aktualisieren
        for i, btn in enumerate(self.tab_nav_buttons):
            if i in self.displayed_tab_indices:
                btn.setChecked(True)
                btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
            else:
                btn.setChecked(False)
                btn.setStyleSheet("background-color: #E0E0E0; color: #333;")
        
        # Dropdown aktualisieren
        if self.tab_nav_dropdown:
            self.tab_nav_dropdown.setCurrentIndex(self.active_tab_index)
    
    def get_status(self):
        """Gibt aktuellen Multi-Tab-Status zurück"""
        return {
            "active": self.multi_tab_active,
            "max_tabs": self.settings.get("max_tabs_display", 2),
            "layout": self.settings.get("preferred_layout", "horizontal"),
            "total_tabs": len(self.all_tab_widgets),
            "displayed_tabs": len(self.displayed_tab_indices),
            "active_tab_index": self.active_tab_index,
            "active_tab_name": self.all_tab_texts[self.active_tab_index] if self.active_tab_index < len(self.all_tab_texts) else "N/A"
        }
    
    def toggle_multi_tab_mode(self):
        """Schaltet zwischen Normal- und Multi-Tab-Modus um"""
        if not self.config["multi_tab_enabled"]:
            logger.warning("⚠️ Multi-Tab-Modus in Framedaten deaktiviert")
            return
        
        if self.multi_tab_active:
            self.deactivate_multi_tab()
        else:
            self.activate_multi_tab()
    
    def activate_multi_tab(self):
        """Aktiviert erweiterten Multi-Tab-Modus"""
        try:
            # Aktuelle Tab-Daten sammeln
            self.collect_initial_tab_data()
            
            if len(self.all_tab_widgets) < 2:
                logger.warning("⚠️ Mindestens 2 Tabs erforderlich für Multi-Tab-Modus")
                return
            
            # Smart Tab-Auswahl
            selected_indices = self.get_smart_tab_selection()
            
            # Haupt-Container erstellen
            main_container = QWidget()
            main_layout = QVBoxLayout(main_container)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(5)
            
            # Tab-Navigation hinzufügen
            nav_widget = self.create_tab_navigation_widget()
            main_layout.addWidget(nav_widget)
            
            # Splitter erstellen
            orientation = Qt.Horizontal if self.settings["preferred_layout"] == "horizontal" else Qt.Vertical
            self.current_splitter = QSplitter(orientation)
            
            # Ausgewählte Tabs aus Original-Widget entfernen und in Splitter einsetzen
            self.saved_tabs = []
            tab_containers = []
            
            # Rückwärts durch die Indizes, um die Tab-Reihenfolge beizubehalten
            for idx in reversed(sorted(selected_indices)):
                if idx < len(self.all_tab_widgets):
                    widget = self.all_tab_widgets[idx]
                    text = self.all_tab_texts[idx]
                    
                    # Tab aus Original-Widget entfernen
                    tab_idx = self.original_tabs.indexOf(widget)
                    if tab_idx >= 0:
                        self.original_tabs.removeTab(tab_idx)
                    
                    # Container erstellen
                    container = self.create_enhanced_tab_container(text, widget, idx)
                    tab_containers.insert(0, container)  # Vorne einfügen für korrekte Reihenfolge
                    
                    # Für Wiederherstellung speichern
                    self.saved_tabs.insert(0, (widget, text, idx))
            
            # Container zum Splitter hinzufügen
            for container in tab_containers:
                self.current_splitter.addWidget(container)
            
            # Splitter zum Haupt-Container hinzufügen
            main_layout.addWidget(self.current_splitter, 1)  # stretch=1 für Hauptbereich
            
            # Gleichmäßige Aufteilung
            equal_sizes = [400] * len(tab_containers)
            self.current_splitter.setSizes(equal_sizes)
            
            # Original-Tab-Widget verstecken und Multi-Tab-Container anzeigen
            self.original_tabs.hide()
            
            # Container zu Parent-Layout hinzufügen
            parent_layout = self.parent.layout()
            if parent_layout:
                tab_index = parent_layout.indexOf(self.original_tabs)
                if tab_index >= 0:
                    parent_layout.insertWidget(tab_index, main_container)
                else:
                    parent_layout.addWidget(main_container)
            
            # Referenz auf Container für späteres Cleanup merken
            self.multi_tab_container = main_container
            
            self.multi_tab_active = True
            
            # Einstellungen speichern
            self.save_user_settings()
            
            layout_name = self.settings["preferred_layout"]
            tab_count = len(selected_indices)
            logger.info(f"📱 Multi-Tab-Modus aktiviert: {tab_count} Tabs {layout_name} mit Navigation")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktivieren des Multi-Tab-Modus: {e}")
    
    def deactivate_multi_tab(self):
        """Deaktiviert Multi-Tab-Modus"""
        try:
            # Multi-Tab-Container aufräumen
            if hasattr(self, 'multi_tab_container') and self.multi_tab_container:
                parent_layout = self.parent.layout()
                if parent_layout:
                    parent_layout.removeWidget(self.multi_tab_container)
                self.multi_tab_container.deleteLater()
                self.multi_tab_container = None
            
            if self.current_splitter:
                # Tabs zurück ins Original-Widget setzen (in korrekter Reihenfolge)
                for widget, text, original_index in sorted(self.saved_tabs, key=lambda x: x[2]):
                    # Tab an korrekter Position einfügen
                    insert_position = min(original_index, self.original_tabs.count())
                    self.original_tabs.insertTab(insert_position, widget, text)
                
                # Aktiven Tab wiederherstellen
                if self.active_tab_index < self.original_tabs.count():
                    self.original_tabs.setCurrentIndex(self.active_tab_index)
                
                # Splitter entfernen
                self.current_splitter.setParent(None)
                self.current_splitter = None
                self.saved_tabs = []
            
            # Navigation-Widgets zurücksetzen
            self.tab_navigation_widget = None
            self.tab_nav_buttons = []
            self.tab_nav_dropdown = None
            self.displayed_tab_indices = []
            
            # KRITISCH: Original-Tab-Widget wieder anzeigen und sichtbar machen
            if self.original_tabs:
                self.original_tabs.show()
                self.original_tabs.setVisible(True)
            
            self.multi_tab_active = False
            logger.info("📱 Multi-Tab-Modus deaktiviert - Navigation zurückgesetzt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Deaktivieren des Multi-Tab-Modus: {e}")
    
    def create_enhanced_tab_container(self, title, content_widget, tab_index):
        """Erstellt einen erweiterten Container für einen Tab"""
        container = QFrame()
        container.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # Header mit Tab-Info
        header = QLabel(f"📋 {title}")
        header.setStyleSheet("""
            font-weight: bold; 
            padding: 8px; 
            background-color: #4CAF50; 
            border-radius: 4px;
            color: white;
            font-size: 12px;
        """)
        layout.addWidget(header)
        
        # WICHTIG: Content-Widget direkt hinzufügen (NICHT in ScrollArea einbetten)
        # Das ScrollArea kann die Widget-Hierarchie stören
        if content_widget:
            content_widget.setParent(container)
            layout.addWidget(content_widget, 1)  # stretch=1 für volle Höhe
        
        return container
    
    def update_max_tabs_display(self, count):
        """Aktualisiert die maximale Anzahl angezeigter Tabs"""
        self.settings["max_tabs_display"] = count
        if self.multi_tab_active:
            # Multi-Tab-Modus neustarten für Aktualisierung
            self.deactivate_multi_tab()
            self.activate_multi_tab()
    
    def update_layout_orientation(self, orientation):
        """Aktualisiert die Layout-Orientierung"""
        self.settings["preferred_layout"] = orientation
        if self.multi_tab_active:
            # Multi-Tab-Modus neustarten für Aktualisierung
            self.deactivate_multi_tab()
            self.activate_multi_tab()
    
    def get_status(self):
        """Gibt aktuellen Status zurück"""
        return {
            "active": self.multi_tab_active,
            "config_enabled": self.config["multi_tab_enabled"],
            "max_tabs": self.settings["max_tabs_display"],
            "layout": self.settings["preferred_layout"],
            "total_tabs": len(self.all_tab_widgets),
            "active_tab_index": self.active_tab_index
        }


class MultiTabConfigWidget(QWidget):
    """Konfigurations-Widget für Multi-Tab-Einstellungen"""
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, multi_tab_manager):
        super().__init__()
        self.manager = multi_tab_manager
        self.init_ui()
        self.load_current_settings()
    
    def init_ui(self):
        """Initialisiert die Konfigurations-UI"""
        layout = QVBoxLayout(self)
        
        # Überschrift
        title = QLabel("📱 Multi-Tab-Konfiguration")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Tab-Anzahl-Gruppe
        count_group = QGroupBox("Anzahl parallel angezeigter Tabs")
        count_layout = QHBoxLayout(count_group)
        
        count_layout.addWidget(QLabel("Maximale Anzahl:"))
        self.tab_count_spin = QSpinBox()
        self.tab_count_spin.setRange(2, 4)
        self.tab_count_spin.valueChanged.connect(self.on_settings_changed)
        count_layout.addWidget(self.tab_count_spin)
        count_layout.addStretch()
        
        layout.addWidget(count_group)
        
        # Layout-Orientierung-Gruppe
        layout_group = QGroupBox("Layout-Orientierung")
        layout_layout = QHBoxLayout(layout_group)
        
        self.layout_button_group = QButtonGroup()
        
        self.horizontal_radio = QRadioButton("📐 Horizontal")
        self.horizontal_radio.toggled.connect(self.on_settings_changed)
        self.layout_button_group.addButton(self.horizontal_radio)
        layout_layout.addWidget(self.horizontal_radio)
        
        self.vertical_radio = QRadioButton("📏 Vertikal")
        self.vertical_radio.toggled.connect(self.on_settings_changed)
        self.layout_button_group.addButton(self.vertical_radio)
        layout_layout.addWidget(self.vertical_radio)
        
        layout_layout.addStretch()
        layout.addWidget(layout_group)
        
        # Auto-Aktivierung
        self.auto_activate_check = QCheckBox("🔄 Automatisch aktivieren beim Laden")
        self.auto_activate_check.toggled.connect(self.on_settings_changed)
        layout.addWidget(self.auto_activate_check)
        
        # Status-Anzeige
        self.status_label = QLabel("Status: Bereit")
        self.status_label.setStyleSheet("color: #666; font-size: 9pt; margin-top: 10px;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def load_current_settings(self):
        """Lädt aktuelle Einstellungen in UI"""
        if not self.manager:
            return
        
        settings = self.manager.settings
        
        # Tab-Anzahl
        self.tab_count_spin.setValue(settings.get("max_tabs_display", 2))
        
        # Layout-Orientierung
        if settings.get("preferred_layout", "horizontal") == "horizontal":
            self.horizontal_radio.setChecked(True)
        else:
            self.vertical_radio.setChecked(True)
        
        # Auto-Aktivierung
        self.auto_activate_check.setChecked(settings.get("auto_activate", False))
        
        # Status aktualisieren
        self.update_status()
    
    def on_settings_changed(self):
        """Behandelt Einstellungsänderungen"""
        if not self.manager:
            return
        
        # Neue Einstellungen sammeln
        new_settings = {
            "max_tabs_display": self.tab_count_spin.value(),
            "preferred_layout": "horizontal" if self.horizontal_radio.isChecked() else "vertical",
            "auto_activate": self.auto_activate_check.isChecked(),
            "remember_state": True
        }
        
        # Manager-Einstellungen aktualisieren
        self.manager.settings.update(new_settings)
        
        # Tab-Anzahl und Layout direkt aktualisieren
        self.manager.update_max_tabs_display(new_settings["max_tabs_display"])
        self.manager.update_layout_orientation(new_settings["preferred_layout"])
        
        # Signal aussenden
        self.settings_changed.emit(new_settings)
        
        # Status aktualisieren
        self.update_status()
        
        logger.info(f"⚙️ Multi-Tab-Einstellungen geändert: {new_settings}")
    
    def update_status(self):
        """Aktualisiert Status-Anzeige"""
        if not self.manager:
            return
        
        status = self.manager.get_status()
        if status["active"]:
            self.status_label.setText(f"✅ Aktiv: {status['max_tabs']} Tabs {status['layout']}")
            self.status_label.setStyleSheet("color: #27ae60; font-size: 9pt; margin-top: 10px;")
        else:
            self.status_label.setText("⏸️ Inaktiv")
            self.status_label.setStyleSheet("color: #e74c3c; font-size: 9pt; margin-top: 10px;")


class EnhancedUnifiedPdvmDialogWidget(QWidget):
    """Erweiterte Version des Dialog-Widgets mit verbesserter Multi-Tab-Funktionalität"""
    
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
        
        # Enhanced Multi-Tab-Manager
        self.multi_tab_manager = None
        self.config_widget = None
        
        # UI aufbauen
        self.init_ui()
        self.setup_keyboard_shortcuts()
        
        # Size Policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(0, 0)
        self.resize(1000, 700)
        
        logger.info("🎨 Enhanced Dialog-Widget mit Multi-Tab-Support initialisiert")
    
    def init_ui(self):
        """Initialisiert die erweiterte Benutzeroberfläche"""
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Status-Bereich
        self.status_label = QLabel("🎨 Enhanced Dialog-Widget - Bereit")
        self.status_label.setStyleSheet("color: #666; font-size: 10pt; padding: 2px;")
        self.status_label.setFixedHeight(20)
        main_layout.addWidget(self.status_label)
        
        # Haupt-Splitter
        self.main_splitter = QSplitter(Qt.Vertical)
        self.main_splitter.splitterMoved.connect(self.on_splitter_moved)
        
        # Input-Container mit Enhanced Multi-Tab zuerst erstellen
        self.input_container = self.create_enhanced_input_container()
        
        # View-Container danach (benötigt input_tabs für Daten)
        self.view_container = self.create_view_container()
        self.main_splitter.addWidget(self.view_container)
        self.main_splitter.addWidget(self.input_container)
        
        # Konfiguration-Container (anfangs versteckt)
        self.config_container = self.create_config_container()
        self.main_splitter.addWidget(self.config_container)
        self.config_container.hide()
        
        # Splitter-Einstellungen
        self.main_splitter.setSizes([200, 400, 0])  # Config anfangs ausgeblendet
        main_layout.addWidget(self.main_splitter, 1)
        
        # WICHTIG: Tab-Widget initial sichtbar machen
        if hasattr(self, 'input_tabs'):
            self.input_tabs.show()
        
        logger.info("🎨 Enhanced UI erfolgreich initialisiert")
    
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
        
        # View-Inhalt mit erweiterten Daten
        self.view_content = QTreeWidget()
        self.view_content.setHeaderLabels(["Eigenschaft", "Wert", "Typ", "Status"])
        self.populate_enhanced_view_data()
        layout.addWidget(self.view_content)
        
        return container
    
    def create_enhanced_input_container(self):
        """Erstellt den erweiterten Input-Container mit Enhanced Multi-Tab"""
        
        container = QFrame()
        container.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header mit erweiterten Controls
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("📝 INPUT-BEREICH"))
        header_layout.addStretch()
        
        # Config-Button
        self.config_btn = QPushButton("⚙️")
        self.config_btn.setToolTip("Multi-Tab-Konfiguration")
        self.config_btn.setCheckable(True)
        self.config_btn.clicked.connect(self.toggle_config_panel)
        self.config_btn.setFixedSize(40, 40)
        header_layout.addWidget(self.config_btn)
        
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
        
        # Tab-Widget mit echten Daten ZUERST erstellen
        self.input_tabs = QTabWidget()
        self.input_tabs.setMinimumHeight(300)  # Mindesthöhe setzen
        self.create_enhanced_demo_tabs()
        
        # Tab-Widget ZUERST zum Layout hinzufügen
        layout.addWidget(self.input_tabs, 1)
        
        # Enhanced Multi-Tab-Manager NACH Tab-Widget-Setup initialisieren
        self.multi_tab_manager = EnhancedMultiTabManager(
            container, 
            self.input_tabs, 
            self.frame_guid, 
            self.user_guid
        )
        
        # KRITISCH: Tab-Widget sichtbar machen und Size-Policy setzen
        self.input_tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.input_tabs.show()
        self.input_tabs.setVisible(True)
        
        # Timer für delayed visibility check
        QTimer.singleShot(100, self._ensure_tab_visibility)
        
        logger.info("📱 Enhanced Multi-Tab-Manager mit Navigation erfolgreich initialisiert")
        
        return container
    
    def _ensure_tab_visibility(self):
        """Stellt sicher, dass das Tab-Widget nach der Initialisierung sichtbar ist"""
        if hasattr(self, 'input_tabs') and hasattr(self, 'multi_tab_manager'):
            if not self.multi_tab_manager.multi_tab_active:
                self.input_tabs.show()
                self.input_tabs.setVisible(True)
                self.input_tabs.raise_()
                # Layout-Update erzwingen
                if self.input_tabs.parent():
                    self.input_tabs.parent().layout().update()
                logger.info("🔄 Tab-Widget-Sichtbarkeit sichergestellt")
    
    def create_config_container(self):
        """Erstellt den Konfigurations-Container"""
        
        container = QFrame()
        container.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("⚙️ MULTI-TAB-KONFIGURATION"))
        header_layout.addStretch()
        
        close_btn = QPushButton("✖")
        close_btn.setToolTip("Konfiguration schließen")
        close_btn.clicked.connect(self.hide_config_panel)
        close_btn.setFixedSize(30, 30)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # Konfigurations-Widget wird später hinzugefügt
        self.config_content_layout = QVBoxLayout()
        layout.addLayout(self.config_content_layout)
        
        return container
    
    def create_enhanced_demo_tabs(self):
        """Erstellt erweiterte Demo-Tabs mit echten Datenstrukturen"""
        
        # Tab 1: Stammdaten
        tab1 = QWidget()
        layout1 = QVBoxLayout(tab1)
        
        # Personen-Daten
        person_group = QGroupBox("👤 Personen-Daten")
        person_layout = QGridLayout(person_group)
        person_layout.addWidget(QLabel("Vorname:"), 0, 0)
        person_layout.addWidget(QLineEdit("Max"), 0, 1)
        person_layout.addWidget(QLabel("Nachname:"), 1, 0)
        person_layout.addWidget(QLineEdit("Mustermann"), 1, 1)
        person_layout.addWidget(QLabel("E-Mail:"), 2, 0)
        person_layout.addWidget(QLineEdit("max.mustermann@example.com"), 2, 1)
        layout1.addWidget(person_group)
        
        # Adress-Daten
        address_group = QGroupBox("🏠 Adress-Daten")
        address_layout = QGridLayout(address_group)
        address_layout.addWidget(QLabel("Straße:"), 0, 0)
        address_layout.addWidget(QLineEdit("Musterstraße 123"), 0, 1)
        address_layout.addWidget(QLabel("PLZ/Ort:"), 1, 0)
        address_layout.addWidget(QLineEdit("12345 Musterstadt"), 1, 1)
        layout1.addWidget(address_group)
        
        layout1.addStretch()
        self.input_tabs.addTab(tab1, "👤 Stammdaten")
        
        # Tab 2: Geschäftsdaten
        tab2 = QWidget()
        layout2 = QVBoxLayout(tab2)
        
        # Finanz-Daten
        finance_group = QGroupBox("💼 Geschäftsdaten")
        finance_layout = QGridLayout(finance_group)
        finance_layout.addWidget(QLabel("Firma:"), 0, 0)
        finance_layout.addWidget(QLineEdit("Musterfirma GmbH"), 0, 1)
        finance_layout.addWidget(QLabel("Abteilung:"), 1, 0)
        finance_layout.addWidget(QLineEdit("IT-Entwicklung"), 1, 1)
        finance_layout.addWidget(QLabel("Position:"), 2, 0)
        finance_layout.addWidget(QLineEdit("Senior Developer"), 2, 1)
        layout2.addWidget(finance_group)
        
        # Kontakt-Daten
        contact_group = QGroupBox("📞 Kontakt-Daten")
        contact_layout = QGridLayout(contact_group)
        contact_layout.addWidget(QLabel("Telefon:"), 0, 0)
        contact_layout.addWidget(QLineEdit("+49 123 456789"), 0, 1)
        contact_layout.addWidget(QLabel("Mobil:"), 1, 0)
        contact_layout.addWidget(QLineEdit("+49 987 654321"), 1, 1)
        layout2.addWidget(contact_group)
        
        layout2.addStretch()
        self.input_tabs.addTab(tab2, "💼 Geschäft")
        
        # Tab 3: Zusatzdaten
        tab3 = QWidget()
        layout3 = QVBoxLayout(tab3)
        
        # Notizen
        notes_group = QGroupBox("📝 Notizen & Kommentare")
        notes_layout = QVBoxLayout(notes_group)
        notes_layout.addWidget(QLabel("Interne Notizen:"))
        notes_text = QTextEdit()
        notes_text.setPlainText("Wichtiger Kunde seit 2020.\nSpezielle Anforderungen in der Buchhaltung.")
        notes_layout.addWidget(notes_text)
        layout3.addWidget(notes_group)
        
        # System-Daten
        system_group = QGroupBox("⚙️ System-Daten")
        system_layout = QGridLayout(system_group)
        system_layout.addWidget(QLabel("Erstellt:"), 0, 0)
        system_layout.addWidget(QLineEdit("2025-01-21 10:30:00"), 0, 1)
        system_layout.addWidget(QLabel("Geändert:"), 1, 0)
        system_layout.addWidget(QLineEdit("2025-01-21 15:45:00"), 1, 1)
        system_layout.addWidget(QLabel("Status:"), 2, 0)
        system_layout.addWidget(QLineEdit("Aktiv"), 2, 1)
        layout3.addWidget(system_group)
        
        layout3.addStretch()
        self.input_tabs.addTab(tab3, "📋 Zusatz")
        
        # Tab 4: Dokumente
        tab4 = QWidget()
        layout4 = QVBoxLayout(tab4)
        
        # Dokumente
        docs_group = QGroupBox("📎 Dokumente & Dateien")
        docs_layout = QVBoxLayout(docs_group)
        docs_layout.addWidget(QLabel("Anhänge:"))
        docs_list = QTextEdit()
        docs_list.setPlainText("• Vertrag_2025.pdf\n• Ausweis_Kopie.jpg\n• Zusatzvereinbarung.docx")
        docs_layout.addWidget(docs_list)
        layout4.addWidget(docs_group)
        
        layout4.addStretch()
        self.input_tabs.addTab(tab4, "📎 Dokumente")
    
    def populate_enhanced_view_data(self):
        """Füllt View mit erweiterten Demo-Daten"""
        
        # Multi-Tab-Status einbeziehen
        multi_tab_status = "Verfügbar"
        if self.multi_tab_manager:
            status = self.multi_tab_manager.get_status()
            if status["active"]:
                multi_tab_status = f"Aktiv ({status['max_tabs']} Tabs {status['layout']})"
        
        enhanced_data = [
            ("Frame GUID", self.frame_guid[:23] + "...", "String", "✅ Geladen"),
            ("User GUID", self.user_guid[:23] + "...", "String", "✅ Geladen"),
            ("Sprache", self.language, "String", "🌐 DE"),
            ("Stichtag", self.user_stichtag, "String", "📅 Aktuell"),
            ("Multi-Tab", multi_tab_status, "Feature", "🎛️ Enhanced"),
            ("Tab-Anzahl", str(self.input_tabs.count()), "Integer", "📊 Verfügbar"),
            ("Konfiguration", "Frame-basiert", "System", "⚙️ Geladen"),
            ("Benutzer-Settings", "Systemsteuerung", "System", "👤 Geladen")
        ]
        
        for prop, value, typ, status in enhanced_data:
            item = QTreeWidgetItem([prop, str(value), typ, status])
            self.view_content.addTopLevelItem(item)
        
        # Spaltenbreite anpassen
        for i in range(4):
            self.view_content.resizeColumnToContents(i)
    
    def setup_keyboard_shortcuts(self):
        """Setzt erweiterte Keyboard-Shortcuts auf"""
        
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
        
        # F5: Konfiguration
        self.shortcut_f5 = QShortcut(QKeySequence(Qt.Key_F5), self)
        self.shortcut_f5.activated.connect(self.toggle_config_panel)
        
        # Tab-Navigation im Multi-Tab-Modus
        # Ctrl+Pfeiltasten für Tab-Navigation
        self.shortcut_ctrl_left = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Left), self)
        self.shortcut_ctrl_left.activated.connect(self.navigate_previous_tab)
        
        self.shortcut_ctrl_right = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Right), self)
        self.shortcut_ctrl_right.activated.connect(self.navigate_next_tab)
        
        # Alt+Zahlen für direkten Tab-Zugriff (Alt+1, Alt+2, etc.)
        self.tab_shortcuts = []
        for i in range(1, 10):  # Alt+1 bis Alt+9
            shortcut = QShortcut(QKeySequence(Qt.ALT + (Qt.Key_0 + i)), self)
            shortcut.activated.connect(lambda checked, idx=i-1: self.navigate_to_tab_by_number(idx))
            self.tab_shortcuts.append(shortcut)
        
        logger.info("⌨️ Erweiterte Keyboard-Shortcuts aktiviert:")
        logger.info("   F1-F5: Lupen, Multi-Tab, Konfiguration")
        logger.info("   Ctrl+←/→: Tab-Navigation")
        logger.info("   Alt+1-9: Direkter Tab-Zugriff")
    
    def navigate_previous_tab(self):
        """Navigiert zum vorherigen Tab"""
        if self.multi_tab_manager:
            self.multi_tab_manager.navigate_previous_tab()
            self.show_status_message("◀ Vorheriger Tab aktiviert")
    
    def navigate_next_tab(self):
        """Navigiert zum nächsten Tab"""
        if self.multi_tab_manager:
            self.multi_tab_manager.navigate_next_tab()
            self.show_status_message("▶ Nächster Tab aktiviert")
    
    def navigate_to_tab_by_number(self, tab_number):
        """Navigiert direkt zu einem Tab per Nummer (0-basiert)"""
        if self.multi_tab_manager and tab_number < len(self.multi_tab_manager.all_tab_widgets):
            self.multi_tab_manager.navigate_to_tab(tab_number)
            tab_name = self.multi_tab_manager.all_tab_texts[tab_number]
            self.show_status_message(f"🎯 Tab {tab_number + 1}: {tab_name} aktiviert")
    
    def get_multi_tab_manager(self):
        """Gibt den Multi-Tab-Manager zurück"""
        return self.multi_tab_manager
    
    def toggle_view_lupe(self):
        """Toggle View-Lupe"""
        self.view_lupe_active = not self.view_lupe_active
        self.view_lupe_btn.setChecked(self.view_lupe_active)
        
        if self.view_lupe_active:
            if self.input_lupe_active:
                self.input_lupe_active = False
                self.input_lupe_btn.setChecked(False)
            self.input_container.hide()
            self.config_container.hide()
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
            self.config_container.hide()
            self.show_status_message("🔍 Input-Lupe aktiviert")
        else:
            self.view_container.show()
            self.show_status_message("🔍 Input-Lupe deaktiviert")
    
    def toggle_multi_tab_mode(self):
        """Toggle Enhanced Multi-Tab-Modus"""
        if self.multi_tab_manager:
            self.multi_tab_manager.toggle_multi_tab_mode()
            self.multi_tab_btn.setChecked(self.multi_tab_manager.multi_tab_active)
            
            # View-Daten aktualisieren
            self.view_content.clear()
            self.populate_enhanced_view_data()
            
            if self.multi_tab_manager.multi_tab_active:
                status = self.multi_tab_manager.get_status()
                self.show_status_message(f"📱 Multi-Tab aktiv: {status['max_tabs']} Tabs {status['layout']}")
            else:
                self.show_status_message("📱 Multi-Tab-Modus deaktiviert")
        else:
            self.show_status_message("⚠️ Multi-Tab-Manager nicht verfügbar")
    
    def toggle_config_panel(self):
        """Toggle Konfigurations-Panel"""
        is_visible = self.config_container.isVisible()
        
        if is_visible:
            self.hide_config_panel()
        else:
            self.show_config_panel()
    
    def show_config_panel(self):
        """Zeigt das Konfigurations-Panel"""
        # Config-Widget erstellen falls noch nicht vorhanden
        if not self.config_widget and self.multi_tab_manager:
            self.config_widget = MultiTabConfigWidget(self.multi_tab_manager)
            self.config_widget.settings_changed.connect(self.on_config_changed)
            self.config_content_layout.addWidget(self.config_widget)
        
        self.config_container.show()
        self.config_btn.setChecked(True)
        
        # Splitter-Größen anpassen
        current_sizes = self.main_splitter.sizes()
        if len(current_sizes) >= 3:
            total_height = sum(current_sizes)
            config_height = total_height // 4  # 1/4 für Config
            remaining = total_height - config_height
            view_height = remaining // 3  # 1/3 des verbleibenden für View
            input_height = remaining - view_height  # Rest für Input
            
            self.main_splitter.setSizes([view_height, input_height, config_height])
        
        self.show_status_message("⚙️ Konfigurations-Panel geöffnet")
    
    def hide_config_panel(self):
        """Versteckt das Konfigurations-Panel"""
        self.config_container.hide()
        self.config_btn.setChecked(False)
        
        # Splitter-Größen zurücksetzen
        current_sizes = self.main_splitter.sizes()
        if len(current_sizes) >= 3:
            total_height = sum(current_sizes[:2])  # Config ausschließen
            view_height = total_height // 3
            input_height = total_height - view_height
            self.main_splitter.setSizes([view_height, input_height, 0])
        
        self.show_status_message("⚙️ Konfigurations-Panel geschlossen")
    
    def on_config_changed(self, settings):
        """Behandelt Konfigurations-Änderungen"""
        # View-Daten aktualisieren
        self.view_content.clear()
        self.populate_enhanced_view_data()
        
        logger.info(f"⚙️ Konfiguration geändert: {settings}")
    
    def restore_position(self):
        """Stellt Standard-Position wieder her"""
        self.view_lupe_active = False
        self.input_lupe_active = False
        self.view_lupe_btn.setChecked(False)
        self.input_lupe_btn.setChecked(False)
        
        self.view_container.show()
        self.input_container.show()
        self.hide_config_panel()
        
        self.main_splitter.setSizes([200, 400, 0])
        
        if self.multi_tab_manager and self.multi_tab_manager.multi_tab_active:
            self.multi_tab_manager.deactivate_multi_tab()
            self.multi_tab_btn.setChecked(False)
        
        self.show_status_message("🔄 Position und Einstellungen wiederhergestellt")
    
    def show_status_message(self, message):
        """Zeigt Status-Nachricht an"""
        self.status_label.setText(message)
        logger.info(message)
        
        # Auto-Reset nach 3 Sekunden
        QTimer.singleShot(3000, lambda: self.status_label.setText("🎨 Enhanced Dialog-Widget - Bereit"))
    
    def on_splitter_moved(self, pos, index):
        """Speichert Splitter-Position"""
        self.saved_splitter_sizes = self.main_splitter.sizes()
    
    def get_multi_tab_status(self):
        """Gibt Multi-Tab-Status zurück"""
        if self.multi_tab_manager:
            return self.multi_tab_manager.get_status()
        return {"active": False, "error": "Manager nicht verfügbar"}


# Demo-Anwendung
if __name__ == "__main__":
    import sys
    
    app = QApplication(sys.argv)
    
    call_daten = {
        "app": None,
        "user_guid": "demo-user-12345-enhanced",
        "frame_guid": "demo-frame-67890-enhanced",
        "language": "de",
        "stichtag": "2025185"
    }
    
    widget = EnhancedUnifiedPdvmDialogWidget(call_daten)
    widget.setWindowTitle("PDVM Enhanced Dialog Widget - Multi-Tab Demo")
    widget.show()
    
    print("🎨 Enhanced Demo gestartet!")
    print("📱 F4: Multi-Tab-Modus umschalten")
    print("⚙️ F5: Konfigurations-Panel öffnen")
    print("🔍 F1/F2: Lupe-Modi")
    print("🔄 F3: Position zurücksetzen")
    
    sys.exit(app.exec_())
