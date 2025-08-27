# pdvm_modern_dialog_loader.py
# -*- coding: utf-8 -*-
"""
Moderne Dialog-Loader für UnifiedPdvmDialogWidget V3
===================================================

Erweitert das UnifiedPdvmDialogWidget V3 um:
- Laden der modernen framedaten-Struktur
- Tab-basierte InputControl-Erzeugung
- View-Daten aus der Datenbank
- Echte Persondaten-Anzeige
"""

import json
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QTextEdit, QPushButton, QScrollArea, QFrame,
    QDateEdit, QTreeWidget, QTreeWidgetItem
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont

from pdvm_central_datenbank import PdvmCentralDatenbank
from pdvm_datetime import Pdvm_DateTime

logger = logging.getLogger(__name__)

class ModernDialogLoader:
    """Lädt moderne framedaten-Struktur und erzeugt entsprechende UI-Elemente"""
    
    def __init__(self, unified_widget):
        self.widget = unified_widget
        self.frame_guid = unified_widget.frame_guid
        self.user_guid = unified_widget.user_guid
        
        # Datenstrukturen
        self.frame_data = None
        self.view_data = None
        self.person_data = None
        self.systemwerte = None
        
        # UI-Elemente Cache
        self.input_controls = {}
        self.tab_widgets = {}
        
    def load_frame_structure(self):
        """Lädt die moderne framedaten-Struktur aus der Datenbank"""
        try:
            # Framedaten laden
            frame_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="framedaten",
                guid=self.frame_guid
            )
            
            self.frame_data = frame_db.lesen().get(self.frame_guid, {})
            
            if not self.frame_data:
                logger.error(f"❌ Keine framedaten für GUID {self.frame_guid} gefunden")
                return False
                
            logger.info(f"✅ Framedaten geladen - Version: {self.frame_data.get('ROOT', {}).get('version', 'unknown')}")
            
            # View-Daten laden falls konfiguriert
            view_config = self.frame_data.get('ViewConfig', {})
            if view_config.get('view_enabled', False):
                view_guid = view_config.get('view_guid')
                if view_guid:
                    self.load_view_data(view_guid)
            
            # Systemwerte laden
            self.load_systemwerte()
            
            # Persondaten laden
            self.load_person_data()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der framedaten-Struktur: {e}")
            return False
    
    def load_view_data(self, view_guid):
        """Lädt die View-Konfiguration"""
        try:
            view_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="viewdaten",
                guid=view_guid
            )
            
            self.view_data = view_db.lesen().get(view_guid, {})
            logger.info(f"✅ View-Daten geladen für GUID: {view_guid}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der View-Daten: {e}")
    
    def load_systemwerte(self):
        """Lädt die Systemwerte für Dropdown-Felder"""
        try:
            sys_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="systemwerte",
                guid="global"
            )
            
            self.systemwerte = sys_db.lesen().get("global", {})
            logger.info(f"✅ Systemwerte geladen: {list(self.systemwerte.keys())}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Systemwerte: {e}")
            self.systemwerte = {}
    
    def load_person_data(self):
        """Lädt die Persondaten"""
        try:
            person_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="persondaten",
                guid="global"
            )
            
            raw_data = person_db.lesen().get("global", {})
            self.person_data = list(raw_data.values()) if raw_data else []
            logger.info(f"✅ Persondaten geladen: {len(self.person_data)} Einträge")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Persondaten: {e}")
            self.person_data = []
    
    def populate_modern_view(self):
        """Füllt die View mit echten Persondaten basierend auf der modernen Struktur"""
        
        if not self.widget.view_content:
            return
            
        # View leeren
        self.widget.view_content.clear()
        
        # View-Konfiguration
        view_config = self.frame_data.get('ViewConfig', {})
        if not view_config.get('view_enabled', False):
            info_item = QTreeWidgetItem(["ℹ️ View deaktiviert", "", ""])
            self.widget.view_content.addTopLevelItem(info_item)
            return
            
        # View-Header
        view_title = view_config.get('view_title', 'Datenansicht')
        header_item = QTreeWidgetItem([f"📊 {view_title}", "", ""])
        self.widget.view_content.addTopLevelItem(header_item)
        
        # Persondaten anzeigen
        if self.person_data:
            for i, person in enumerate(self.person_data):
                person_name = f"{person.get('vorname', '')} {person.get('name', '')}"
                person_item = QTreeWidgetItem([f"👤 {person_name}", "", "Person"])
                self.widget.view_content.addTopLevelItem(person_item)
                
                # Person-Details
                for field, value in person.items():
                    if field != 'guid' and value:
                        field_item = QTreeWidgetItem([field, str(value), "String"])
                        person_item.addChild(field_item)
                        
                # Nur ersten 5 Einträge expandieren (Performance)
                if i < 5:
                    person_item.setExpanded(True)
        else:
            no_data_item = QTreeWidgetItem(["ℹ️ Keine Persondaten verfügbar", "", ""])
            self.widget.view_content.addTopLevelItem(no_data_item)
        
        # Frame-Info hinzufügen
        frame_info = QTreeWidgetItem(["⚙️ Frame-Konfiguration", "", ""])
        self.widget.view_content.addTopLevelItem(frame_info)
        
        root_data = self.frame_data.get('ROOT', {})
        for key, value in root_data.items():
            info_item = QTreeWidgetItem([key, str(value), "Config"])
            frame_info.addChild(info_item)
        
        frame_info.setExpanded(True)
    
    def create_modern_input_tabs(self):
        """Erstellt die Input-Tabs basierend auf der modernen framedaten-Struktur"""
        
        if not self.widget.input_tabs:
            return
            
        # Bestehende Tabs löschen
        self.widget.input_tabs.clear()
        self.input_controls.clear()
        self.tab_widgets.clear()
        
        # Tab-Konfiguration
        tab_config = self.frame_data.get('TabConfig', {})
        if not tab_config.get('tabs_enabled', False):
            self.create_fallback_tab()
            return
            
        # InputControls nach Tabs gruppieren
        input_controls = self.frame_data.get('InputControls', {})
        tabs_data = tab_config.get('tabs', [])
        
        # Tabs nach Order sortieren
        sorted_tabs = sorted(tabs_data, key=lambda x: x.get('tab_order', 999))
        
        for tab_info in sorted_tabs:
            if not tab_info.get('enabled', True):
                continue
                
            tab_id = tab_info['tab_id']
            tab_name = tab_info['tab_name']
            
            # Tab-Widget erstellen
            tab_widget = self.create_tab_widget(tab_id, input_controls)
            
            # Tab hinzufügen
            icon = tab_info.get('icon', '')
            if icon:
                self.widget.input_tabs.addTab(tab_widget, f"{self.get_icon(icon)} {tab_name}")
            else:
                self.widget.input_tabs.addTab(tab_widget, tab_name)
            
            self.tab_widgets[tab_id] = tab_widget
            
        logger.info(f"✅ {len(sorted_tabs)} moderne Input-Tabs erstellt")
    
    def create_tab_widget(self, tab_id, input_controls):
        """Erstellt ein einzelnes Tab-Widget mit den zugehörigen InputControls"""
        
        # Scroll-Container für das Tab
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Content-Widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # InputControls für dieses Tab filtern und sortieren
        tab_controls = {
            ic_id: ic_data for ic_id, ic_data in input_controls.items()
            if ic_data.get('tab_id') == tab_id
        }
        
        sorted_controls = sorted(
            tab_controls.items(),
            key=lambda x: x[1].get('order', 999)
        )
        
        # InputControls erstellen
        for ic_id, ic_data in sorted_controls:
            control_widget = self.create_input_control(ic_id, ic_data)
            if control_widget:
                layout.addWidget(control_widget)
                self.input_controls[ic_id] = control_widget
        
        # Stretch am Ende für bessere Verteilung
        layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        return scroll_area
    
    def create_input_control(self, ic_id, ic_data):
        """Erstellt ein einzelnes InputControl basierend auf dem Typ"""
        
        control_type = ic_data.get('type', 'text')
        label_text = ic_data.get('label', ic_id)
        tooltip = ic_data.get('tooltip', '')
        required = ic_data.get('required', False)
        
        # Container für das Control
        container = QFrame()
        container.setFrameStyle(QFrame.Box)
        layout = QVBoxLayout(container)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 8, 10, 8)
        
        # Label
        label = QLabel(label_text)
        if required:
            label.setText(f"{label_text} *")
            label.setStyleSheet("font-weight: bold; color: #d32f2f;")
        else:
            label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)
        
        # Input-Element je nach Typ
        input_widget = None
        
        if control_type == 'text':
            input_widget = QLineEdit()
            input_widget.setPlaceholderText(f"{label_text} eingeben...")
            
        elif control_type == 'textarea':
            input_widget = QTextEdit()
            input_widget.setMaximumHeight(ic_data.get('height', 100))
            input_widget.setPlaceholderText(f"{label_text} eingeben...")
            
        elif control_type == 'datetime':
            input_widget = QDateEdit()
            input_widget.setCalendarPopup(True)
            input_widget.setDate(QDate.currentDate())
            
        elif control_type == 'dropdown':
            input_widget = QComboBox()
            dropdown_config = ic_data.get('dropdown_config', {})
            self.populate_dropdown(input_widget, dropdown_config)
            
        elif control_type == 'viewtable':
            # Für ViewTable erstmal einen ComboBox als Ersatz
            input_widget = QComboBox()
            input_widget.addItem("(ViewTable - wird implementiert)")
            
        else:
            input_widget = QLineEdit()
            input_widget.setPlaceholderText(f"Unbekannter Typ: {control_type}")
        
        if input_widget:
            if tooltip:
                input_widget.setToolTip(tooltip)
            
            # Breite setzen falls definiert
            width = ic_data.get('width')
            if width:
                input_widget.setFixedWidth(width)
            
            layout.addWidget(input_widget)
        
        return container
    
    def populate_dropdown(self, combobox, dropdown_config):
        """Füllt eine ComboBox mit Systemwerten"""
        
        if dropdown_config.get('allow_empty', True):
            combobox.addItem("", "")
        
        source = dropdown_config.get('source', '')
        kategorie = dropdown_config.get('kategorie', '')
        
        if source == 'systemwerte' and kategorie and self.systemwerte:
            kategorie_data = self.systemwerte.get(kategorie, {})
            
            # Werte nach Order sortieren
            sorted_items = sorted(
                kategorie_data.items(),
                key=lambda x: x[1].get('order', 999)
            )
            
            for value, data in sorted_items:
                text = data.get('text', value)
                combobox.addItem(text, value)
    
    def create_fallback_tab(self):
        """Erstellt ein Fallback-Tab wenn keine Tab-Konfiguration vorhanden"""
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        info_label = QLabel("ℹ️ Keine Tab-Konfiguration verfügbar")
        info_label.setStyleSheet("color: #666; font-size: 12pt; padding: 20px;")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        layout.addStretch()
        scroll_area.setWidget(content_widget)
        
        self.widget.input_tabs.addTab(scroll_area, "📝 Standard")
    
    def get_icon(self, icon_name):
        """Gibt ein Unicode-Icon für den gegebenen Icon-Namen zurück"""
        
        icon_map = {
            'person': '👤',
            'contact': '📞',
            'info': 'ℹ️',
            'settings': '⚙️',
            'data': '📊',
            'edit': '✏️'
        }
        
        return icon_map.get(icon_name, '📄')

def enhance_unified_widget(unified_widget):
    """Erweitert ein UnifiedPdvmDialogWidget um moderne Datenlade-Funktionen"""
    
    # Modernen Loader erstellen
    loader = ModernDialogLoader(unified_widget)
    
    # Framedaten-Struktur laden
    if loader.load_frame_structure():
        # View mit echten Daten füllen
        loader.populate_modern_view()
        
        # Moderne Input-Tabs erstellen
        loader.create_modern_input_tabs()
        
        logger.info("✅ UnifiedPdvmDialogWidget erfolgreich mit moderner Struktur erweitert")
        return True
    else:
        logger.error("❌ Konnte moderne Struktur nicht laden")
        return False
