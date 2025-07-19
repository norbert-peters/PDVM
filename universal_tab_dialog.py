#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Universeller Tab-Dialog für verschiedene Modi
Implementiert Tab-basierte UI mit View- und InputFrame-Integration
"""

import sys
import logging
from typing import Dict, List, Optional, Any
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QLabel, QPushButton, QMessageBox, QSplitter,
                             QScrollArea, QFrame, QButtonGroup, QDialog,
                             QDialogButtonBox, QTextEdit, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon

# Import der bestehenden Module
from universal_frame_structure import UniversalFrameDataGenerator
from pdvm_grouped_ui_manager import GroupedInputWidget
from pdvm_optimized_data_manager import OptimizedDataManager

logger = logging.getLogger(__name__)


class UniversalTabDialog(QWidget):
    """
    Universeller Tab-Dialog der verschiedene Modi unterstützt:
    - Mode 0: Datenpflege
    - Mode 1: Pflege Framedaten  
    - Mode 2: Pflege Menü
    - Mode 3: Pflege Anwendung
    - Mode 4: Pflege Benutzereinstellungen
    - Mode 5: Pflege Benutzer
    - Mode >5: Hinweis "nicht vorhanden"
    """
    
    # Signals
    data_changed = pyqtSignal(dict)  # Datenänderung
    mode_changed = pyqtSignal(int)   # Modus-Wechsel
    tab_changed = pyqtSignal(str)    # Tab-Wechsel
    save_requested = pyqtSignal(dict)  # Speichern angefordert
    
    def __init__(self, call_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        
        self.call_data = call_data
        self.current_mode = call_data.get("mode", 0)
        self.current_data = {}
        self.tab_widgets = {}  # tab_id -> widget
        self.is_modified = False
        
        # Central DB Integration
        self.central_db = None  # Wird später mit PdvmCentralDatenbank verbunden
        
        self.setup_ui()
        self.load_initial_data()
        
        logger.info(f"UniversalTabDialog initialisiert - Modus: {self.current_mode}")
    
    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header mit Modus-Info
        self.create_header(layout)
        
        # Tab-Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        layout.addWidget(self.tab_widget)
        
        # Footer mit Buttons
        self.create_footer(layout)
        
        # Tabs erstellen
        self.create_tabs()
        
        # Dialog-Größe setzen
        framedaten = self.call_data.get("framedaten", {})
        dialog_config = framedaten.get("dialog_config", {})
        width = dialog_config.get("default_width", 1000)
        height = dialog_config.get("default_height", 700)
        self.resize(width, height)
    
    def create_header(self, layout):
        """Erstellt den Header-Bereich"""
        
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_frame.setStyleSheet("background-color: #f0f0f0; padding: 10px;")
        header_layout = QHBoxLayout(header_frame)
        
        # Modus-Info
        framedaten = self.call_data.get("framedaten", {})
        mode_config = framedaten.get("mode_config", {})
        
        mode_icon = mode_config.get("mode_icon", "❓")
        mode_name = mode_config.get("mode_name", "Unbekannter Modus")
        mode_desc = mode_config.get("mode_description", "")
        
        self.mode_label = QLabel(f"{mode_icon} {mode_name}")
        self.mode_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(self.mode_label)
        
        if mode_desc:
            desc_label = QLabel(f"• {mode_desc}")
            desc_label.setStyleSheet("color: #666; font-style: italic;")
            header_layout.addWidget(desc_label)
        
        header_layout.addStretch()
        
        # Status-Info
        self.status_label = QLabel("Bereit")
        self.status_label.setStyleSheet("color: #666;")
        header_layout.addWidget(self.status_label)
        
        layout.addWidget(header_frame)
    
    def create_footer(self, layout):
        """Erstellt den Footer-Bereich mit Buttons"""
        
        footer_layout = QHBoxLayout()
        
        # Info-Button
        self.btn_info = QPushButton("ℹ️ Info")
        self.btn_info.clicked.connect(self.show_info)
        footer_layout.addWidget(self.btn_info)
        
        # Refresh-Button
        self.btn_refresh = QPushButton("🔄 Aktualisieren")
        self.btn_refresh.clicked.connect(self.refresh_data)
        footer_layout.addWidget(self.btn_refresh)
        
        footer_layout.addStretch()
        
        # Speichern-Button
        self.btn_save = QPushButton("💾 Speichern")
        self.btn_save.clicked.connect(self.save_data)
        self.btn_save.setEnabled(False)  # Erst bei Änderungen aktiviert
        footer_layout.addWidget(self.btn_save)
        
        # Schließen-Button
        self.btn_close = QPushButton("❌ Schließen")
        self.btn_close.clicked.connect(self.close_dialog)
        footer_layout.addWidget(self.btn_close)
        
        layout.addLayout(footer_layout)
    
    def create_tabs(self):
        """Erstellt alle Tabs basierend auf den Framedaten"""
        
        framedaten = self.call_data.get("framedaten", {})
        tabs_config = framedaten.get("tabs", [])
        start_tab_id = self.call_data.get("start_tab", "")
        
        start_tab_index = 0
        
        for i, tab_config in enumerate(tabs_config):
            if not tab_config.get("visible", True):
                continue
            
            tab_id = tab_config["tab_id"]
            tab_name = tab_config["tab_name"]
            tab_icon = tab_config.get("tab_icon", "")
            tab_type = tab_config["tab_type"]
            
            # Tab-Widget erstellen
            tab_widget = self.create_tab_widget(tab_config)
            
            # Tab hinzufügen
            tab_title = f"{tab_icon} {tab_name}" if tab_icon else tab_name
            tab_index = self.tab_widget.addTab(tab_widget, tab_title)
            
            # Tab-Widget speichern
            self.tab_widgets[tab_id] = tab_widget
            
            # Start-Tab merken
            if tab_id == start_tab_id or tab_config.get("start_tab", False):
                start_tab_index = tab_index
        
        # Start-Tab aktivieren
        if self.tab_widget.count() > 0:
            self.tab_widget.setCurrentIndex(start_tab_index)
        else:
            self.show_no_tabs_message()
    
    def create_tab_widget(self, tab_config: Dict[str, Any]) -> QWidget:
        """Erstellt ein Widget für einen Tab"""
        
        tab_type = tab_config["tab_type"]
        tab_id = tab_config["tab_id"]
        
        if tab_type == "view":
            return self.create_view_tab(tab_config)
        elif tab_type == "inputframe":
            return self.create_inputframe_tab(tab_config)
        elif tab_type == "settings":
            return self.create_settings_tab(tab_config)
        else:
            return self.create_placeholder_tab(tab_config)
    
    def create_view_tab(self, tab_config: Dict[str, Any]) -> QWidget:
        """Erstellt einen View-Tab"""
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QLabel("👁️ Daten-Ansicht")
        header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px; background-color: #e3f2fd;")
        layout.addWidget(header)
        
        # View-Bereich (Platzhalter)
        view_area = QScrollArea()
        view_content = QWidget()
        view_layout = QVBoxLayout(view_content)
        
        # Mock-View-Daten
        view_data_group = QGroupBox("📊 View-Daten")
        view_data_layout = QVBoxLayout(view_data_group)
        
        view_guid = tab_config.get("view_guid", "")
        if view_guid:
            info_text = f"""
View GUID: {view_guid}
Grouping Style: {tab_config.get('grouping_style', 'sections')}
Scrollable: {'Ja' if tab_config.get('scrollable', True) else 'Nein'}

Hier würden die echten View-Daten aus der Datenbank angezeigt werden,
basierend auf der View-GUID und dem aktuellen Gruppierungsstil.
            """
        else:
            info_text = "Keine View-GUID konfiguriert."
        
        info_label = QLabel(info_text.strip())
        info_label.setWordWrap(True)
        info_label.setStyleSheet("padding: 10px; background-color: #f5f5f5;")
        view_data_layout.addWidget(info_label)
        
        view_layout.addWidget(view_data_group)
        view_layout.addStretch()
        
        view_area.setWidget(view_content)
        view_area.setWidgetResizable(True)
        layout.addWidget(view_area)
        
        return widget
    
    def create_inputframe_tab(self, tab_config: Dict[str, Any]) -> QWidget:
        """Erstellt einen InputFrame-Tab"""
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        tab_name = tab_config.get("tab_name", "InputFrame")
        tab_icon = tab_config.get("tab_icon", "📝")
        header = QLabel(f"{tab_icon} {tab_name}")
        header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px; background-color: #fff3cd;")
        layout.addWidget(header)
        
        # GroupedInputWidget erstellen
        grouping_style = tab_config.get("grouping_style", "sections")
        
        try:
            grouped_widget = GroupedInputWidget(grouping_style)
            
            # Demo-Gruppen hinzufügen basierend auf Tab-Typ
            self.add_demo_groups_for_tab(grouped_widget, tab_config)
            
            # Scroll-Area wenn nötig
            if tab_config.get("scrollable", True):
                scroll_area = QScrollArea()
                scroll_area.setWidget(grouped_widget)
                scroll_area.setWidgetResizable(True)
                layout.addWidget(scroll_area)
            else:
                layout.addWidget(grouped_widget)
            
            # Change-Handler verbinden
            if hasattr(grouped_widget, 'field_changed'):
                grouped_widget.field_changed.connect(self.on_field_changed)
                
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des InputFrame-Tab: {e}")
            error_label = QLabel(f"❌ Fehler beim Laden des InputFrame: {str(e)}")
            error_label.setStyleSheet("color: red; padding: 20px;")
            layout.addWidget(error_label)
        
        return widget
    
    def create_settings_tab(self, tab_config: Dict[str, Any]) -> QWidget:
        """Erstellt einen Settings-Tab"""
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        tab_name = tab_config.get("tab_name", "Einstellungen")
        tab_icon = tab_config.get("tab_icon", "⚙️")
        header = QLabel(f"{tab_icon} {tab_name}")
        header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px; background-color: #e8f5e8;")
        layout.addWidget(header)
        
        # Settings-Bereiche
        settings_area = QScrollArea()
        settings_content = QWidget()
        settings_layout = QVBoxLayout(settings_content)
        
        # Demo-Settings basierend auf Tab-ID
        tab_id = tab_config.get("tab_id", "")
        if tab_id == "user_settings":
            self.create_user_settings_content(settings_layout)
        elif tab_id == "application_maintenance":
            self.create_application_settings_content(settings_layout)
        else:
            self.create_generic_settings_content(settings_layout, tab_config)
        
        settings_layout.addStretch()
        settings_area.setWidget(settings_content)
        settings_area.setWidgetResizable(True)
        layout.addWidget(settings_area)
        
        return widget
    
    def create_placeholder_tab(self, tab_config: Dict[str, Any]) -> QWidget:
        """Erstellt einen Platzhalter-Tab für unbekannte Typen"""
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QLabel("❓ Unbekannter Tab-Typ")
        header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px; background-color: #ffe6e6;")
        layout.addWidget(header)
        
        # Platzhalter-Inhalt
        placeholder = QLabel(f"""
Tab-ID: {tab_config.get('tab_id', 'Unbekannt')}
Tab-Typ: {tab_config.get('tab_type', 'Unbekannt')}

Dieser Tab-Typ ist noch nicht implementiert.
        """.strip())
        placeholder.setStyleSheet("padding: 20px; background-color: #f5f5f5;")
        placeholder.setAlignment(Qt.AlignCenter)
        layout.addWidget(placeholder)
        
        layout.addStretch()
        
        return widget
    
    def add_demo_groups_for_tab(self, grouped_widget: GroupedInputWidget, tab_config: Dict[str, Any]):
        """Fügt Demo-Gruppen basierend auf Tab-Konfiguration hinzu"""
        
        tab_id = tab_config.get("tab_id", "")
        
        if tab_id == "data_maintenance":
            # Datenpflege-Gruppen
            self.add_data_maintenance_groups(grouped_widget)
        elif tab_id == "frame_maintenance":
            # Frame-Pflege-Gruppen
            self.add_frame_maintenance_groups(grouped_widget)
        elif tab_id == "menu_maintenance":
            # Menü-Pflege-Gruppen
            self.add_menu_maintenance_groups(grouped_widget)
        elif tab_id == "user_maintenance":
            # Benutzer-Pflege-Gruppen
            self.add_user_maintenance_groups(grouped_widget)
        else:
            # Standard-Gruppe
            self.add_generic_groups(grouped_widget, tab_id)
    
    def add_data_maintenance_groups(self, grouped_widget: GroupedInputWidget):
        """Fügt Gruppen für Datenpflege hinzu"""
        
        # Grunddaten-Gruppe
        basic_fields = [
            {"field_id": "name", "label": "Name", "type": "text", "required": True},
            {"field_id": "description", "label": "Beschreibung", "type": "textarea"},
            {"field_id": "active", "label": "Aktiv", "type": "checkbox", "default": True}
        ]
        grouped_widget.add_group("basic_data", "📝 Grunddaten", basic_fields)
        
        # Erweiterte Daten-Gruppe
        extended_fields = [
            {"field_id": "category", "label": "Kategorie", "type": "dropdown", 
             "dropdown_options": ["Standard", "Erweitert", "System"]},
            {"field_id": "priority", "label": "Priorität", "type": "number", "default": 1},
            {"field_id": "created", "label": "Erstellt", "type": "datetime", "readonly": True}
        ]
        grouped_widget.add_group("extended_data", "📊 Erweiterte Daten", extended_fields)
    
    def add_frame_maintenance_groups(self, grouped_widget: GroupedInputWidget):
        """Fügt Gruppen für Frame-Pflege hinzu"""
        
        # Frame-Definition
        frame_fields = [
            {"field_id": "frame_guid", "label": "Frame GUID", "type": "text", "readonly": True},
            {"field_id": "frame_name", "label": "Frame Name", "type": "text", "required": True},
            {"field_id": "frame_version", "label": "Version", "type": "text", "default": "1.0"}
        ]
        grouped_widget.add_group("frame_definition", "🏗️ Frame-Definition", frame_fields)
        
        # Tab-Konfiguration
        tab_fields = [
            {"field_id": "default_grouping", "label": "Standard-Gruppierung", "type": "dropdown",
             "dropdown_options": ["sections", "accordion", "tabs", "inline"]},
            {"field_id": "dialog_width", "label": "Dialog-Breite", "type": "number", "default": 1000},
            {"field_id": "dialog_height", "label": "Dialog-Höhe", "type": "number", "default": 700}
        ]
        grouped_widget.add_group("tab_config", "🗂️ Tab-Konfiguration", tab_fields)
    
    def add_menu_maintenance_groups(self, grouped_widget: GroupedInputWidget):
        """Fügt Gruppen für Menü-Pflege hinzu"""
        
        # Menü-Grunddaten
        menu_fields = [
            {"field_id": "menu_id", "label": "Menü ID", "type": "text", "required": True},
            {"field_id": "menu_title", "label": "Menü Titel", "type": "text", "required": True},
            {"field_id": "menu_icon", "label": "Icon", "type": "text"},
            {"field_id": "menu_order", "label": "Reihenfolge", "type": "number", "default": 100}
        ]
        grouped_widget.add_group("menu_basic", "📋 Menü-Grunddaten", menu_fields)
        
        # Berechtigung
        permission_fields = [
            {"field_id": "requires_admin", "label": "Erfordert Admin", "type": "checkbox"},
            {"field_id": "visible_roles", "label": "Sichtbare Rollen", "type": "text"},
            {"field_id": "enabled", "label": "Aktiviert", "type": "checkbox", "default": True}
        ]
        grouped_widget.add_group("menu_permissions", "🔒 Berechtigung", permission_fields)
    
    def add_user_maintenance_groups(self, grouped_widget: GroupedInputWidget):
        """Fügt Gruppen für Benutzer-Pflege hinzu"""
        
        # Benutzer-Grunddaten
        user_fields = [
            {"field_id": "username", "label": "Benutzername", "type": "text", "required": True},
            {"field_id": "email", "label": "E-Mail", "type": "text", "required": True},
            {"field_id": "full_name", "label": "Vollständiger Name", "type": "text"},
            {"field_id": "role", "label": "Rolle", "type": "dropdown",
             "dropdown_options": ["User", "Admin", "Developer"]}
        ]
        grouped_widget.add_group("user_basic", "👤 Benutzer-Grunddaten", user_fields)
        
        # Benutzer-Einstellungen
        settings_fields = [
            {"field_id": "language", "label": "Sprache", "type": "dropdown",
             "dropdown_options": ["de", "en", "fr"]},
            {"field_id": "theme", "label": "Theme", "type": "dropdown",
             "dropdown_options": ["Light", "Dark", "Auto"]},
            {"field_id": "active", "label": "Aktiv", "type": "checkbox", "default": True}
        ]
        grouped_widget.add_group("user_settings", "⚙️ Einstellungen", settings_fields)
    
    def add_generic_groups(self, grouped_widget: GroupedInputWidget, tab_id: str):
        """Fügt generische Demo-Gruppen hinzu"""
        
        generic_fields = [
            {"field_id": "field1", "label": f"Feld 1 ({tab_id})", "type": "text"},
            {"field_id": "field2", "label": f"Feld 2 ({tab_id})", "type": "text"},
            {"field_id": "field3", "label": f"Feld 3 ({tab_id})", "type": "checkbox"}
        ]
        grouped_widget.add_group("generic_group", f"📋 {tab_id.replace('_', ' ').title()}", generic_fields)
    
    def create_user_settings_content(self, layout):
        """Erstellt Benutzereinstellungen-Inhalt"""
        
        group = QGroupBox("👤 Persönliche Einstellungen")
        group_layout = QVBoxLayout(group)
        
        info = QLabel("""
Hier würden die persönlichen Benutzereinstellungen angezeigt:
• Sprache
• Theme
• Standard-Gruppierungsstil
• Notification-Einstellungen
• etc.
        """.strip())
        info.setWordWrap(True)
        group_layout.addWidget(info)
        
        layout.addWidget(group)
    
    def create_application_settings_content(self, layout):
        """Erstellt Anwendungseinstellungen-Inhalt"""
        
        group = QGroupBox("⚙️ Anwendungs-Konfiguration")
        group_layout = QVBoxLayout(group)
        
        info = QLabel("""
Hier würden die Anwendungseinstellungen angezeigt:
• Datenbank-Verbindung
• Logging-Level
• Performance-Parameter
• Feature-Flags
• etc.
        """.strip())
        info.setWordWrap(True)
        group_layout.addWidget(info)
        
        layout.addWidget(group)
    
    def create_generic_settings_content(self, layout, tab_config):
        """Erstellt generischen Einstellungs-Inhalt"""
        
        tab_name = tab_config.get("tab_name", "Einstellungen")
        group = QGroupBox(f"⚙️ {tab_name}")
        group_layout = QVBoxLayout(group)
        
        info = QLabel(f"""
Tab ID: {tab_config.get('tab_id', '')}
Grouping Style: {tab_config.get('grouping_style', '')}

Hier würden die spezifischen Einstellungen für diesen Tab angezeigt.
        """.strip())
        info.setWordWrap(True)
        group_layout.addWidget(info)
        
        layout.addWidget(group)
    
    def show_no_tabs_message(self):
        """Zeigt eine Meldung wenn keine Tabs verfügbar sind"""
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        message = QLabel(f"""
❌ Keine Tabs verfügbar für Modus {self.current_mode}

Dieser Modus ist entweder nicht konfiguriert oder 
Sie haben keine Berechtigung für die verfügbaren Tabs.
        """.strip())
        message.setAlignment(Qt.AlignCenter)
        message.setStyleSheet("font-size: 14px; color: #666; padding: 50px;")
        layout.addWidget(message)
        
        self.tab_widget.addTab(widget, "❌ Nicht verfügbar")
    
    def load_initial_data(self):
        """Lädt die initialen Daten"""
        
        # Hier würde die Verbindung zur PdvmCentralDatenbank aufgebaut
        # und die entsprechenden Daten geladen
        
        self.status_label.setText("Daten geladen")
        logger.info("Initiale Daten geladen")
    
    def on_tab_changed(self, index):
        """Callback für Tab-Wechsel"""
        
        if index >= 0 and index < self.tab_widget.count():
            tab_text = self.tab_widget.tabText(index)
            self.tab_changed.emit(tab_text)
            logger.debug(f"Tab gewechselt: {tab_text}")
    
    def on_field_changed(self, field_key, value):
        """Callback für Feldänderungen"""
        
        self.current_data[field_key] = value
        self.is_modified = True
        self.btn_save.setEnabled(True)
        self.status_label.setText("Geändert")
        
        self.data_changed.emit(self.current_data)
        logger.debug(f"Feld geändert: {field_key} = {value}")
    
    def save_data(self):
        """Speichert die aktuellen Daten"""
        
        try:
            # Hier würde das Speichern über PdvmCentralDatenbank erfolgen
            
            self.save_requested.emit(self.current_data)
            self.is_modified = False
            self.btn_save.setEnabled(False)
            self.status_label.setText("Gespeichert")
            
            QMessageBox.information(self, "Erfolg", "Daten wurden erfolgreich gespeichert!")
            logger.info("Daten gespeichert")
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern: {e}")
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern: {str(e)}")
    
    def refresh_data(self):
        """Aktualisiert die Daten"""
        
        if self.is_modified:
            reply = QMessageBox.question(
                self, "Nicht gespeicherte Änderungen",
                "Sie haben nicht gespeicherte Änderungen. Möchten Sie trotzdem aktualisieren?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # Daten neu laden
        self.load_initial_data()
        self.is_modified = False
        self.btn_save.setEnabled(False)
        
        QMessageBox.information(self, "Aktualisiert", "Daten wurden aktualisiert!")
    
    def show_info(self):
        """Zeigt Informationen über den Dialog"""
        
        framedaten = self.call_data.get("framedaten", {})
        frame_info = framedaten.get("frame_info", {})
        mode_config = framedaten.get("mode_config", {})
        
        info_text = f"""
📋 Dialog-Informationen:

🎯 Modus: {mode_config.get('mode_name', 'Unbekannt')} (ID: {self.current_mode})
📝 Beschreibung: {mode_config.get('mode_description', '')}
🏗️ Frame: {frame_info.get('frame_name', 'Unbekannt')}
🔧 Frame GUID: {frame_info.get('frame_guid', '')}
👁️ View GUID: {frame_info.get('view_guid', '')}
🗂️ Anzahl Tabs: {self.tab_widget.count()}
🚀 Version: {frame_info.get('frame_version', '1.0')}

Admin erforderlich: {'Ja' if mode_config.get('requires_admin', False) else 'Nein'}
Nur Lesen: {'Ja' if mode_config.get('read_only', False) else 'Nein'}
        """.strip()
        
        QMessageBox.information(self, "Dialog-Informationen", info_text)
    
    def close_dialog(self):
        """Schließt den Dialog"""
        
        if self.is_modified:
            reply = QMessageBox.question(
                self, "Nicht gespeicherte Änderungen",
                "Sie haben nicht gespeicherte Änderungen. Möchten Sie trotzdem schließen?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        self.close()
    
    def closeEvent(self, event):
        """Event-Handler für das Schließen des Dialogs"""
        
        if self.is_modified:
            reply = QMessageBox.question(
                self, "Nicht gespeicherte Änderungen",
                "Sie haben nicht gespeicherte Änderungen. Möchten Sie trotzdem schließen?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        event.accept()


class UniversalTabDialogTest(QDialog):
    """Test-Dialog für den universellen Tab-Dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🚀 Universeller Tab-Dialog Test")
        self.setModal(True)
        self.resize(1200, 800)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Erstellt die Test-UI"""
        
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("🧪 Universeller Tab-Dialog Test")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; background-color: #e3f2fd;")
        layout.addWidget(header)
        
        # Modi-Buttons
        buttons_layout = QHBoxLayout()
        
        for mode in range(7):  # 0-5 + 6 (undefined)
            btn = QPushButton(f"Modus {mode}")
            btn.clicked.connect(lambda checked, m=mode: self.test_mode(m))
            buttons_layout.addWidget(btn)
        
        layout.addLayout(buttons_layout)
        
        # Container für universellen Dialog
        self.dialog_container = QWidget()
        self.dialog_container.setMinimumHeight(600)
        layout.addWidget(self.dialog_container)
        
        # Info-Bereich
        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(150)
        self.info_text.setReadOnly(True)
        layout.addWidget(self.info_text)
    
    def test_mode(self, mode: int):
        """Testet einen bestimmten Modus"""
        
        try:
            # Test-View-GUID
            test_view_guid = "12345678-1234-1234-1234-123456789abc"
            
            # Call-Data generieren
            call_data = UniversalFrameDataGenerator.create_call_data(
                view_guid=test_view_guid,
                mode=mode,
                user_guid="test-user-guid"
            )
            
            # Alten Dialog entfernen
            if hasattr(self, 'current_dialog'):
                self.current_dialog.setParent(None)
                self.current_dialog.deleteLater()
            
            # Neuen Dialog erstellen
            self.current_dialog = UniversalTabDialog(call_data)
            
            # Dialog in Container einbetten
            container_layout = QVBoxLayout(self.dialog_container)
            container_layout.addWidget(self.current_dialog)
            
            # Info aktualisieren
            framedaten = call_data["framedaten"]
            mode_config = framedaten["mode_config"]
            tabs_count = len(framedaten["tabs"])
            
            info = f"""
Modus {mode} getestet: {mode_config['mode_name']} {mode_config['mode_icon']}
Beschreibung: {mode_config['mode_description']}
Anzahl Tabs: {tabs_count}
Start-Tab: {call_data['start_tab']}
Admin erforderlich: {'Ja' if mode_config['requires_admin'] else 'Nein'}
            """.strip()
            
            self.info_text.setPlainText(info)
            
        except Exception as e:
            logger.error(f"Fehler beim Testen von Modus {mode}: {e}")
            self.info_text.setPlainText(f"❌ Fehler beim Testen von Modus {mode}: {str(e)}")


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    logging.basicConfig(level=logging.DEBUG)
    
    app = QApplication(sys.argv)
    
    # Test-Dialog anzeigen
    test_dialog = UniversalTabDialogTest()
    test_dialog.show()
    
    sys.exit(app.exec_())
