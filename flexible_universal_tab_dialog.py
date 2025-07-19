#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Flexibler Universal-Tab-Dialog mit Multi-Tab-Support
Unterstützt hierarchische Gruppierungen und mehrere Tabs pro Modus
"""

import logging
from typing import Dict, List, Optional, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QScrollArea,
    QLabel, QPushButton, QGroupBox, QGridLayout, QFrame,
    QSplitter, QMessageBox, QProgressBar, QStatusBar
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QIcon

# Import bestehender Module
from pdvm_grouped_ui_manager import GroupedInputWidget

logger = logging.getLogger(__name__)


class FlexibleTabWidget(QWidget):
    """
    Erweiterte Tab-Widget-Klasse für flexible Multi-Tab-Unterstützung
    """
    
    # Signale
    tab_changed = pyqtSignal(str)  # tab_id
    data_changed = pyqtSignal(str, dict)  # tab_id, data
    
    def __init__(self, tab_definition: Dict[str, Any], groups_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        
        self.tab_definition = tab_definition
        self.groups_data = groups_data
        self.grouped_widgets = {}  # group_id -> GroupedInputWidget
        
        self.init_ui()
        
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche für diesen Tab"""
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Tab-Header mit Icon und Beschreibung
        self.create_tab_header(layout)
        
        # Haupt-Content-Bereich
        self.create_content_area(layout)
        
        # Tab-spezifische Aktions-Buttons
        self.create_action_buttons(layout)
    
    def create_tab_header(self, parent_layout):
        """Erstellt den Header-Bereich des Tabs"""
        
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_frame.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px;")
        
        header_layout = QHBoxLayout(header_frame)
        
        # Icon und Titel
        icon_label = QLabel(self.tab_definition.get("tab_icon", "📋"))
        icon_label.setFont(QFont("Arial", 14))
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(self.tab_definition.get("tab_name", "Unbekannter Tab"))
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Info über Anzahl Gruppen
        group_count = len(self.tab_definition.get("assigned_groups", []))
        info_label = QLabel(f"{group_count} Gruppen")
        info_label.setStyleSheet("color: #6c757d; font-size: 10px;")
        header_layout.addWidget(info_label)
        
        parent_layout.addWidget(header_frame)
    
    def create_content_area(self, parent_layout):
        """Erstellt den Haupt-Content-Bereich"""
        
        # Scrollbarer Bereich
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Content Widget
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)
        
        # Layout basierend auf Tab-Konfiguration
        columns = self.tab_definition.get("columns", 1)
        tab_grouping_style = self.tab_definition.get("tab_grouping_style", "sections")
        
        if tab_grouping_style == "tabs":
            # Gruppierungen als Unter-Tabs
            self.create_subtab_layout(content_widget)
        elif columns > 1:
            # Multi-Column Layout
            self.create_multicolumn_layout(content_widget, columns)
        else:
            # Standard Vertical Layout
            self.create_standard_layout(content_widget)
        
        parent_layout.addWidget(scroll_area)
    
    def create_subtab_layout(self, content_widget):
        """Erstellt Unter-Tabs für Gruppen"""
        
        layout = QVBoxLayout(content_widget)
        
        # Sub-Tab-Widget
        sub_tab_widget = QTabWidget()
        sub_tab_widget.setTabPosition(QTabWidget.North)
        
        # Jede Gruppe als eigener Sub-Tab
        for group_id in self.tab_definition.get("assigned_groups", []):
            if group_id in self.groups_data:
                group_data = self.groups_data[group_id]
                
                # GroupedInputWidget für diese Gruppe
                group_widget = GroupedInputWidget(
                    group_style=group_data.get("grouping_style", "sections"),
                    parent=sub_tab_widget
                )
                
                # Demo-Daten für die Gruppe hinzufügen
                self.setup_demo_group_data(group_widget, group_data)
                
                self.grouped_widgets[group_id] = group_widget
                
                # Als Sub-Tab hinzufügen
                tab_title = f"{group_data.get('group_icon', '')} {group_data.get('group_name', '')}"
                sub_tab_widget.addTab(group_widget, tab_title)
        
        layout.addWidget(sub_tab_widget)
    
    def create_multicolumn_layout(self, content_widget, columns):
        """Erstellt Multi-Column Layout für Gruppen"""
        
        main_layout = QVBoxLayout(content_widget)
        
        # Grid-Layout für Spalten
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)
        
        assigned_groups = self.tab_definition.get("assigned_groups", [])
        
        for i, group_id in enumerate(assigned_groups):
            if group_id in self.groups_data:
                group_data = self.groups_data[group_id]
                
                # GroupedInputWidget für diese Gruppe
                group_widget = GroupedInputWidget(
                    group_style=group_data.get("grouping_style", "sections"),
                    parent=content_widget
                )
                
                self.grouped_widgets[group_id] = group_widget
                
                # Demo-Daten für die Gruppe hinzufügen
                self.setup_demo_group_data(group_widget, group_data)
                
                # Position im Grid berechnen
                row = i // columns
                col = i % columns
                
                grid_layout.addWidget(group_widget, row, col)
        
        main_layout.addLayout(grid_layout)
        main_layout.addStretch()
    
    def create_standard_layout(self, content_widget):
        """Erstellt Standard Vertical Layout für Gruppen"""
        
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        
        # Gruppen in der definierten Reihenfolge hinzufügen
        assigned_groups = self.tab_definition.get("assigned_groups", [])
        
        for group_id in assigned_groups:
            if group_id in self.groups_data:
                group_data = self.groups_data[group_id]
                
                # GroupedInputWidget für diese Gruppe
                group_widget = GroupedInputWidget(
                    group_style=group_data.get("grouping_style", "sections"),
                    parent=content_widget
                )
                
                self.grouped_widgets[group_id] = group_widget
                
                # Demo-Daten für die Gruppe hinzufügen
                self.setup_demo_group_data(group_widget, group_data)
                layout.addWidget(group_widget)
        
        layout.addStretch()
    
    def setup_demo_group_data(self, group_widget, group_data):
        """Erstellt Demo-Daten für ein GroupedInputWidget"""
        
        # Gruppe definieren
        group_definition = {
            "group_id": group_data.get("group_id", "demo_group"),
            "group_name": group_data.get("group_name", "Demo Gruppe"),
            "group_description": group_data.get("group_description", ""),
            "sort_order": group_data.get("sort_order", 100),
            "collapsible": group_data.get("collapsible", False),
            "initially_collapsed": group_data.get("initially_collapsed", False)
        }
        
        # Demo-Felder basierend auf field_types erstellen
        field_types = group_data.get("field_types", ["text"])
        field_count = group_data.get("field_count_estimate", 3)
        
        demo_fields = {}
        for i in range(min(field_count, 5)):  # Maximal 5 Demo-Felder
            field_type = field_types[i % len(field_types)] if field_types else "text"
            field_key = f"{group_data.get('group_id', 'demo')}_{field_type}_{i+1}"
            
            demo_fields[field_key] = {
                "field_key": field_key,
                "field_name": f"{field_type.title()} Feld {i+1}",
                "field_type": field_type,
                "group_id": group_data.get("group_id", "demo_group"),
                "sort_order": (i+1) * 10,
                "required": i == 0,  # Erstes Feld als Pflichtfeld
                "readonly": False,
                "visible": True
            }
        
        # Daten an GroupedInputWidget übergeben
        try:
            if hasattr(group_widget, 'setup_groups_and_fields'):
                group_widget.setup_groups_and_fields(
                    {group_definition["group_id"]: group_definition},
                    demo_fields
                )
            else:
                # Fallback: Direkt setzen
                group_widget.groups_data = {group_definition["group_id"]: group_definition}
                group_widget.fields_data = demo_fields
        except Exception as e:
            logger.error(f"❌ Fehler beim Setup der Demo-Daten für Gruppe {group_data.get('group_name')}: {e}")
    
    def create_action_buttons(self, parent_layout):
        """Erstellt Tab-spezifische Aktions-Buttons"""
        
        if self.tab_definition.get("tab_type") == "view":
            # View-Tabs haben andere Buttons
            return
        
        action_frame = QFrame()
        action_frame.setFrameStyle(QFrame.StyledPanel)
        action_layout = QHBoxLayout(action_frame)
        
        # Speichern-Button (nur wenn nicht read-only)
        if not self.tab_definition.get("read_only", False):
            save_btn = QPushButton("💾 Speichern")
            save_btn.clicked.connect(self.save_tab_data)
            action_layout.addWidget(save_btn)
        
        # Zurücksetzen-Button
        reset_btn = QPushButton("🔄 Zurücksetzen")
        reset_btn.clicked.connect(self.reset_tab_data)
        action_layout.addWidget(reset_btn)
        
        action_layout.addStretch()
        
        # Validierung-Button
        validate_btn = QPushButton("✓ Validieren")
        validate_btn.clicked.connect(self.validate_tab_data)
        action_layout.addWidget(validate_btn)
        
        parent_layout.addWidget(action_frame)
    
    def save_tab_data(self):
        """Speichert die Daten dieses Tabs"""
        logger.info(f"💾 Speichere Daten für Tab: {self.tab_definition.get('tab_name')}")
        
        # Daten von allen GroupedInputWidgets sammeln
        all_data = {}
        for group_id, widget in self.grouped_widgets.items():
            try:
                group_data = widget.get_input_data()
                all_data[group_id] = group_data
            except Exception as e:
                logger.error(f"❌ Fehler beim Sammeln der Daten für Gruppe {group_id}: {e}")
        
        # Signal emittieren
        self.data_changed.emit(self.tab_definition["tab_id"], all_data)
        
        # Erfolgs-Nachricht
        QMessageBox.information(self, "Speichern", f"Daten für Tab '{self.tab_definition.get('tab_name')}' gespeichert.")
    
    def reset_tab_data(self):
        """Setzt die Daten dieses Tabs zurück"""
        logger.info(f"🔄 Setze Daten für Tab zurück: {self.tab_definition.get('tab_name')}")
        
        # Alle GroupedInputWidgets zurücksetzen
        for group_id, widget in self.grouped_widgets.items():
            try:
                widget.reset_input_data()
            except Exception as e:
                logger.error(f"❌ Fehler beim Zurücksetzen der Daten für Gruppe {group_id}: {e}")
    
    def validate_tab_data(self):
        """Validiert die Daten dieses Tabs"""
        logger.info(f"✓ Validiere Daten für Tab: {self.tab_definition.get('tab_name')}")
        
        validation_errors = []
        
        # Alle GroupedInputWidgets validieren
        for group_id, widget in self.grouped_widgets.items():
            try:
                if hasattr(widget, 'validate_input_data'):
                    errors = widget.validate_input_data()
                    if errors:
                        validation_errors.extend([f"Gruppe {group_id}: {err}" for err in errors])
            except Exception as e:
                validation_errors.append(f"Gruppe {group_id}: Validierungsfehler - {e}")
        
        # Ergebnis anzeigen
        if validation_errors:
            error_text = "\n".join(validation_errors)
            QMessageBox.warning(self, "Validierungsfehler", f"Folgende Fehler wurden gefunden:\n\n{error_text}")
        else:
            QMessageBox.information(self, "Validierung", "Alle Daten sind korrekt!")


class FlexibleUniversalTabDialog(QWidget):
    """
    Flexibler Universal-Tab-Dialog mit Multi-Tab-Support
    """
    
    # Signale
    mode_changed = pyqtSignal(int)
    tab_changed = pyqtSignal(str)
    data_saved = pyqtSignal(str, dict)  # tab_id, data
    
    def __init__(self, call_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        
        self.call_data = call_data
        self.framedaten = call_data.get("framedaten", {})
        self.current_mode = call_data.get("mode", 0)
        self.current_tab_id = call_data.get("start_tab", "view_tab")
        
        self.tab_widgets = {}  # tab_id -> FlexibleTabWidget
        self.tab_widget = None  # QTabWidget
        
        self.init_ui()
        self.load_mode_tabs()
        
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Header mit Modus-Info
        self.create_header(layout)
        
        # Haupt-Tab-Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setMovable(self.framedaten.get("mode_config", {}).get("allow_tab_reordering", False))
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        layout.addWidget(self.tab_widget)
        
        # Status-Bar
        self.create_status_bar(layout)
        
    def create_header(self, parent_layout):
        """Erstellt den Header-Bereich"""
        
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_frame.setStyleSheet("""
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #e3f2fd, stop: 1 #bbdefb);
            border: 1px solid #2196f3;
            border-radius: 5px;
            padding: 5px;
        """)
        
        header_layout = QHBoxLayout(header_frame)
        
        # Modus-Info
        mode_config = self.framedaten.get("mode_config", {})
        mode_icon = mode_config.get("mode_icon", "❓")
        mode_name = mode_config.get("mode_name", "Unbekannter Modus")
        mode_desc = mode_config.get("mode_description", "")
        
        mode_label = QLabel(f"{mode_icon} {mode_name}")
        mode_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(mode_label)
        
        if mode_desc:
            desc_label = QLabel(f"• {mode_desc}")
            desc_label.setStyleSheet("color: #555; font-size: 11px;")
            header_layout.addWidget(desc_label)
        
        header_layout.addStretch()
        
        # Tab-Anzahl Info
        tab_count = len(self.framedaten.get("tabs", []))
        tab_info_label = QLabel(f"{tab_count} Tabs")
        tab_info_label.setStyleSheet("color: #666; font-size: 10px;")
        header_layout.addWidget(tab_info_label)
        
        parent_layout.addWidget(header_frame)
    
    def create_status_bar(self, parent_layout):
        """Erstellt die Status-Bar"""
        
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.StyledPanel)
        status_frame.setMaximumHeight(30)
        
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(5, 2, 5, 2)
        
        # Status-Label
        self.status_label = QLabel("Bereit")
        self.status_label.setStyleSheet("color: #666; font-size: 10px;")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # Progress-Bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setMaximumHeight(15)
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        parent_layout.addWidget(status_frame)
    
    def load_mode_tabs(self):
        """Lädt alle Tabs für den aktuellen Modus"""
        
        logger.info(f"🔹 Lade Tabs für Modus {self.current_mode}")
        
        tabs_data = self.framedaten.get("tabs", [])
        groups_data = self.framedaten.get("groups", {})
        
        if not tabs_data:
            logger.warning("⚠️ Keine Tab-Daten gefunden")
            self.status_label.setText("Keine Tab-Daten verfügbar")
            return
        
        self.status_label.setText(f"Lade {len(tabs_data)} Tabs...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(tabs_data))
        
        start_tab_index = 0
        
        for i, tab_data in enumerate(tabs_data):
            tab_id = tab_data.get("tab_id", f"tab_{i}")
            tab_name = tab_data.get("tab_name", f"Tab {i+1}")
            tab_icon = tab_data.get("tab_icon", "📋")
            
            try:
                # Flexible Tab-Widget erstellen
                tab_widget = FlexibleTabWidget(
                    tab_definition=tab_data,
                    groups_data=groups_data,
                    parent=self.tab_widget
                )
                
                # Signale verbinden
                tab_widget.data_changed.connect(self.on_tab_data_changed)
                
                # Tab hinzufügen
                show_icons = self.framedaten.get("mode_config", {}).get("show_tab_icons", True)
                if show_icons:
                    tab_title = f"{tab_icon} {tab_name}"
                else:
                    tab_title = tab_name
                
                self.tab_widget.addTab(tab_widget, tab_title)
                self.tab_widgets[tab_id] = tab_widget
                
                # Start-Tab merken
                if tab_data.get("start_tab", False) or tab_id == self.current_tab_id:
                    start_tab_index = i
                
                logger.info(f"✅ Tab '{tab_name}' geladen ({len(tab_data.get('assigned_groups', []))} Gruppen)")
                
            except Exception as e:
                logger.error(f"❌ Fehler beim Laden von Tab '{tab_name}': {e}")
                
            self.progress_bar.setValue(i + 1)
        
        # Start-Tab aktivieren
        self.tab_widget.setCurrentIndex(start_tab_index)
        
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"{len(tabs_data)} Tabs geladen")
        
        logger.info(f"✅ Alle Tabs für Modus {self.current_mode} erfolgreich geladen")
    
    def on_tab_changed(self, index):
        """Event-Handler für Tab-Wechsel"""
        
        if index < 0 or index >= self.tab_widget.count():
            return
        
        current_widget = self.tab_widget.widget(index)
        tab_id = None
        
        # Tab-ID finden
        for tid, widget in self.tab_widgets.items():
            if widget == current_widget:
                tab_id = tid
                break
        
        if tab_id:
            self.current_tab_id = tab_id
            tab_name = self.tab_widget.tabText(index)
            logger.info(f"🔄 Tab gewechselt zu: {tab_name} (ID: {tab_id})")
            self.status_label.setText(f"Aktiver Tab: {tab_name}")
            self.tab_changed.emit(tab_id)
    
    def on_tab_data_changed(self, tab_id: str, data: Dict[str, Any]):
        """Event-Handler für Datenänderungen in Tabs"""
        
        logger.info(f"💾 Daten geändert in Tab: {tab_id}")
        self.status_label.setText(f"Daten gespeichert: Tab {tab_id}")
        self.data_saved.emit(tab_id, data)
    
    def get_all_tab_data(self) -> Dict[str, Any]:
        """Sammelt alle Daten von allen Tabs"""
        
        all_data = {}
        
        for tab_id, tab_widget in self.tab_widgets.items():
            try:
                tab_data = {}
                for group_id, group_widget in tab_widget.grouped_widgets.items():
                    if hasattr(group_widget, 'get_input_data'):
                        tab_data[group_id] = group_widget.get_input_data()
                
                all_data[tab_id] = tab_data
                
            except Exception as e:
                logger.error(f"❌ Fehler beim Sammeln der Daten für Tab {tab_id}: {e}")
        
        return all_data
    
    def validate_all_tabs(self) -> Dict[str, List[str]]:
        """Validiert alle Tabs und gibt Fehler zurück"""
        
        all_errors = {}
        
        for tab_id, tab_widget in self.tab_widgets.items():
            tab_errors = []
            
            for group_id, group_widget in tab_widget.grouped_widgets.items():
                try:
                    if hasattr(group_widget, 'validate_input_data'):
                        errors = group_widget.validate_input_data()
                        if errors:
                            tab_errors.extend([f"Gruppe {group_id}: {err}" for err in errors])
                except Exception as e:
                    tab_errors.append(f"Gruppe {group_id}: Validierungsfehler - {e}")
            
            if tab_errors:
                all_errors[tab_id] = tab_errors
        
        return all_errors


# Demo-Funktionen
def demo_flexible_dialog():
    """Demonstriert den flexiblen Universal-Tab-Dialog"""
    
    from flexible_frame_structure import FlexibleFrameDataGenerator
    
    print("=== Flexible Universal-Tab-Dialog Demo ===")
    
    # Test-View-GUID
    test_view_guid = "12345678-1234-1234-1234-123456789abc"
    
    # Call-Data für verschiedene Modi generieren
    for mode in [0, 1]:
        print(f"\n--- Modus {mode} ---")
        
        try:
            call_data = FlexibleFrameDataGenerator.create_call_data_flexible(
                view_guid=test_view_guid,
                mode=mode,
                user_guid="test-user-guid"
            )
            
            print(f"✅ Call-Data für Modus {mode} generiert")
            print(f"   - {len(call_data['framedaten']['tabs'])} Tabs")
            print(f"   - {len(call_data['framedaten']['groups'])} Gruppen")
            print(f"   - Start-Tab: {call_data['start_tab']}")
            
            # Tab-Details
            for tab in call_data['framedaten']['tabs']:
                group_count = len(tab['assigned_groups'])
                columns = tab.get('columns', 1)
                style = tab.get('tab_grouping_style', 'sections')
                print(f"   📋 {tab['tab_icon']} {tab['tab_name']}: {group_count} Gruppen, {columns} Spalten, {style}")
            
        except Exception as e:
            print(f"❌ Fehler bei Modus {mode}: {e}")
    
    print("\n=== Demo abgeschlossen ===")


if __name__ == "__main__":
    demo_flexible_dialog()
