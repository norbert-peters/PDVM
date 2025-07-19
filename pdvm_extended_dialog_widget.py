#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Erweiterte PdvmDialogWidget-Klasse für Frame-Bearbeitung
Unterstützt die neue flexible Multi-Tab-Architektur und Frame-Verwaltung
"""

import os
import sys
import logging
import json
from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QScrollArea,
    QLabel, QPushButton, QGroupBox, QGridLayout, QFrame,
    QLineEdit, QTextEdit, QComboBox, QSpinBox, QCheckBox,
    QMessageBox, QSplitter, QTreeWidget, QTreeWidgetItem,
    QFormLayout, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

# Import bestehender Module
from pdvm_dialog_widget import PdvmDialogWidget
from flexible_frame_structure import FlexibleFrameDataGenerator, FlexibleFrameStructure
from flexible_universal_tab_dialog import FlexibleUniversalTabDialog
from pdvm_database_structure_setup import PdvmDatabaseStructureSetup

logger = logging.getLogger(__name__)


class FrameEditDialog(QDialog):
    """Dialog für die Bearbeitung von Frame-Strukturen"""
    
    frame_saved = pyqtSignal(str, dict)  # frame_guid, frame_data
    
    def __init__(self, frame_data: Dict[str, Any] = None, parent=None):
        super().__init__(parent)
        
        self.frame_data = frame_data or {}
        self.is_new_frame = not bool(frame_data)
        
        self.setWindowTitle("📝 Frame-Struktur bearbeiten")
        self.setModal(True)
        self.resize(800, 600)
        
        self.init_ui()
        self.load_frame_data()
    
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("🏗️ Frame-Struktur Editor")
        header_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_label.setStyleSheet("padding: 10px; background-color: #e3f2fd; border-radius: 5px;")
        layout.addWidget(header_label)
        
        # Tab-Widget für verschiedene Bereiche
        self.tab_widget = QTabWidget()
        
        # Tab 1: Basis-Informationen
        self.create_basic_info_tab()
        
        # Tab 2: Tab-Definitionen
        self.create_tabs_definition_tab()
        
        # Tab 3: Gruppen-Definitionen
        self.create_groups_definition_tab()
        
        # Tab 4: Modi-Konfiguration
        self.create_modes_configuration_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("💾 Speichern")
        self.save_button.clicked.connect(self.save_frame)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("❌ Abbrechen")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        if not self.is_new_frame:
            self.validate_button = QPushButton("✓ Validieren")
            self.validate_button.clicked.connect(self.validate_frame)
            button_layout.addWidget(self.validate_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def create_basic_info_tab(self):
        """Erstellt den Tab für Basis-Informationen"""
        
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Frame-Name
        self.frame_name_edit = QLineEdit()
        layout.addRow("Frame-Name:", self.frame_name_edit)
        
        # Frame-Beschreibung
        self.frame_description_edit = QTextEdit()
        self.frame_description_edit.setMaximumHeight(80)
        layout.addRow("Beschreibung:", self.frame_description_edit)
        
        # Frame-Version
        self.frame_version_edit = QLineEdit("2.0")
        self.frame_version_edit.setReadOnly(True)
        layout.addRow("Version:", self.frame_version_edit)
        
        # View-GUID Verknüpfung
        self.view_guid_edit = QLineEdit()
        layout.addRow("View-GUID:", self.view_guid_edit)
        
        # Dialog-Größe
        size_layout = QHBoxLayout()
        self.dialog_width_spin = QSpinBox()
        self.dialog_width_spin.setRange(400, 2000)
        self.dialog_width_spin.setValue(1200)
        size_layout.addWidget(self.dialog_width_spin)
        
        size_layout.addWidget(QLabel("x"))
        
        self.dialog_height_spin = QSpinBox()
        self.dialog_height_spin.setRange(300, 1500)
        self.dialog_height_spin.setValue(800)
        size_layout.addWidget(self.dialog_height_spin)
        
        size_layout.addStretch()
        layout.addRow("Dialog-Größe:", size_layout)
        
        # Standard-Gruppierungsstil
        self.default_grouping_combo = QComboBox()
        self.default_grouping_combo.addItems(["sections", "accordion", "tabs", "inline"])
        layout.addRow("Standard-Gruppierung:", self.default_grouping_combo)
        
        # Auto-Save
        self.auto_save_check = QCheckBox("Automatisch speichern")
        self.auto_save_check.setChecked(True)
        layout.addRow("", self.auto_save_check)
        
        self.tab_widget.addTab(tab, "📋 Basis-Info")
    
    def create_tabs_definition_tab(self):
        """Erstellt den Tab für Tab-Definitionen"""
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        add_tab_btn = QPushButton("➕ Tab hinzufügen")
        add_tab_btn.clicked.connect(self.add_tab_definition)
        toolbar_layout.addWidget(add_tab_btn)
        
        remove_tab_btn = QPushButton("➖ Tab entfernen")
        remove_tab_btn.clicked.connect(self.remove_tab_definition)
        toolbar_layout.addWidget(remove_tab_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # Tab-Liste
        self.tabs_tree = QTreeWidget()
        self.tabs_tree.setHeaderLabels(["Tab-ID", "Name", "Typ", "Reihenfolge", "Icon", "Sichtbare Modi"])
        layout.addWidget(self.tabs_tree)
        
        self.tab_widget.addTab(tab, "🗂️ Tabs")
    
    def create_groups_definition_tab(self):
        """Erstellt den Tab für Gruppen-Definitionen"""
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        add_group_btn = QPushButton("➕ Gruppe hinzufügen")
        add_group_btn.clicked.connect(self.add_group_definition)
        toolbar_layout.addWidget(add_group_btn)
        
        remove_group_btn = QPushButton("➖ Gruppe entfernen")
        remove_group_btn.clicked.connect(self.remove_group_definition)
        toolbar_layout.addWidget(remove_group_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # Gruppen-Liste
        self.groups_tree = QTreeWidget()
        self.groups_tree.setHeaderLabels(["Gruppen-ID", "Name", "Stil", "Reihenfolge", "Felder-Anzahl"])
        layout.addWidget(self.groups_tree)
        
        self.tab_widget.addTab(tab, "📁 Gruppen")
    
    def create_modes_configuration_tab(self):
        """Erstellt den Tab für Modi-Konfiguration"""
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Modi-Liste
        self.modes_tree = QTreeWidget()
        self.modes_tree.setHeaderLabels(["Modus-ID", "Name", "Icon", "Tabs", "Start-Tab"])
        layout.addWidget(self.modes_tree)
        
        # Standard-Modi hinzufügen
        self.populate_default_modes()
        
        self.tab_widget.addTab(tab, "⚙️ Modi")
    
    def populate_default_modes(self):
        """Fügt Standard-Modi hinzu"""
        
        default_modes = [
            (0, "📝", "Datenpflege", ["view_tab", "edit_tab"], "view_tab"),
            (1, "🏗️", "Frame-Pflege", ["view_tab", "frame_edit_tab"], "frame_edit_tab"),
            (2, "📋", "Menü-Pflege", ["view_tab", "menu_edit_tab"], "view_tab"),
            (3, "⚙️", "App-Pflege", ["view_tab", "app_edit_tab"], "view_tab"),
            (4, "👤", "User-Settings", ["view_tab", "user_edit_tab"], "view_tab"),
            (5, "👥", "User-Verwaltung", ["view_tab", "admin_edit_tab"], "view_tab")
        ]
        
        for mode_id, icon, name, tabs, start_tab in default_modes:
            item = QTreeWidgetItem([
                str(mode_id), name, icon, ", ".join(tabs), start_tab
            ])
            self.modes_tree.addTopLevelItem(item)
    
    def add_tab_definition(self):
        """Fügt eine neue Tab-Definition hinzu"""
        
        # Einfacher Dialog für Tab-Eingabe
        tab_id = f"custom_tab_{self.tabs_tree.topLevelItemCount() + 1}"
        tab_name = f"Custom Tab {self.tabs_tree.topLevelItemCount() + 1}"
        
        item = QTreeWidgetItem([
            tab_id, tab_name, "inputframe", "100", "📝", "0"
        ])
        self.tabs_tree.addTopLevelItem(item)
    
    def remove_tab_definition(self):
        """Entfernt die ausgewählte Tab-Definition"""
        
        current_item = self.tabs_tree.currentItem()
        if current_item:
            index = self.tabs_tree.indexOfTopLevelItem(current_item)
            self.tabs_tree.takeTopLevelItem(index)
    
    def add_group_definition(self):
        """Fügt eine neue Gruppen-Definition hinzu"""
        
        group_id = f"custom_group_{self.groups_tree.topLevelItemCount() + 1}"
        group_name = f"Custom Gruppe {self.groups_tree.topLevelItemCount() + 1}"
        
        item = QTreeWidgetItem([
            group_id, group_name, "sections", "100", "5"
        ])
        self.groups_tree.addTopLevelItem(item)
    
    def remove_group_definition(self):
        """Entfernt die ausgewählte Gruppen-Definition"""
        
        current_item = self.groups_tree.currentItem()
        if current_item:
            index = self.groups_tree.indexOfTopLevelItem(current_item)
            self.groups_tree.takeTopLevelItem(index)
    
    def load_frame_data(self):
        """Lädt bestehende Frame-Daten in die UI"""
        
        if not self.frame_data:
            return
        
        # Basis-Informationen
        self.frame_name_edit.setText(self.frame_data.get("frame_name", ""))
        self.frame_description_edit.setPlainText(self.frame_data.get("description", ""))
        self.view_guid_edit.setText(self.frame_data.get("view_guid", ""))
        
        # Dialog-Größe
        self.dialog_width_spin.setValue(self.frame_data.get("dialog_width", 1200))
        self.dialog_height_spin.setValue(self.frame_data.get("dialog_height", 800))
        
        # Standard-Gruppierung
        grouping_style = self.frame_data.get("default_grouping_style", "sections")
        index = self.default_grouping_combo.findText(grouping_style)
        if index >= 0:
            self.default_grouping_combo.setCurrentIndex(index)
        
        # Auto-Save
        self.auto_save_check.setChecked(self.frame_data.get("auto_save", True))
        
        # Tabs laden
        self.load_tabs_data()
        
        # Gruppen laden
        self.load_groups_data()
    
    def load_tabs_data(self):
        """Lädt Tab-Daten"""
        
        tabs_data = self.frame_data.get("tabs", [])
        self.tabs_tree.clear()
        
        for tab in tabs_data:
            visible_modes = ", ".join(map(str, tab.get("visible_modes", [])))
            item = QTreeWidgetItem([
                tab.get("tab_id", ""),
                tab.get("tab_name", ""),
                tab.get("tab_type", ""),
                str(tab.get("tab_order", 100)),
                tab.get("tab_icon", ""),
                visible_modes
            ])
            self.tabs_tree.addTopLevelItem(item)
    
    def load_groups_data(self):
        """Lädt Gruppen-Daten"""
        
        groups_data = self.frame_data.get("groups", {})
        self.groups_tree.clear()
        
        for group_id, group in groups_data.items():
            item = QTreeWidgetItem([
                group_id,
                group.get("group_name", ""),
                group.get("grouping_style", ""),
                str(group.get("sort_order", 100)),
                str(group.get("field_count_estimate", 0))
            ])
            self.groups_tree.addTopLevelItem(item)
    
    def save_frame(self):
        """Speichert die Frame-Daten"""
        
        try:
            # Frame-Daten sammeln
            frame_data = {
                "frame_name": self.frame_name_edit.text(),
                "frame_description": self.frame_description_edit.toPlainText(),
                "frame_version": self.frame_version_edit.text(),
                "view_guid": self.view_guid_edit.text(),
                "dialog_width": self.dialog_width_spin.value(),
                "dialog_height": self.dialog_height_spin.value(),
                "default_grouping_style": self.default_grouping_combo.currentText(),
                "auto_save": self.auto_save_check.isChecked(),
                "tabs": self.collect_tabs_data(),
                "groups": self.collect_groups_data(),
                "modes": self.collect_modes_data()
            }
            
            # Validierung
            if not frame_data["frame_name"]:
                QMessageBox.warning(self, "Fehler", "Frame-Name ist erforderlich!")
                return
            
            # Signal emittieren
            frame_guid = self.frame_data.get("frame_guid", "")
            self.frame_saved.emit(frame_guid, frame_data)
            
            QMessageBox.information(self, "Erfolg", "Frame-Daten erfolgreich gespeichert!")
            self.accept()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Frame-Daten: {e}")
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern: {e}")
    
    def collect_tabs_data(self) -> List[Dict]:
        """Sammelt Tab-Daten aus der UI"""
        
        tabs = []
        for i in range(self.tabs_tree.topLevelItemCount()):
            item = self.tabs_tree.topLevelItem(i)
            
            visible_modes = []
            modes_text = item.text(5)
            if modes_text:
                try:
                    visible_modes = [int(m.strip()) for m in modes_text.split(",") if m.strip().isdigit()]
                except:
                    visible_modes = [0]  # Fallback
            
            tab = {
                "tab_id": item.text(0),
                "tab_name": item.text(1),
                "tab_type": item.text(2),
                "tab_order": int(item.text(3)) if item.text(3).isdigit() else 100,
                "tab_icon": item.text(4),
                "visible_modes": visible_modes,
                "assigned_groups": [],  # Könnte erweitert werden
                "visible": True,
                "enabled": True
            }
            tabs.append(tab)
        
        return tabs
    
    def collect_groups_data(self) -> Dict[str, Dict]:
        """Sammelt Gruppen-Daten aus der UI"""
        
        groups = {}
        for i in range(self.groups_tree.topLevelItemCount()):
            item = self.groups_tree.topLevelItem(i)
            
            group_id = item.text(0)
            groups[group_id] = {
                "group_id": group_id,
                "group_name": item.text(1),
                "grouping_style": item.text(2),
                "sort_order": int(item.text(3)) if item.text(3).isdigit() else 100,
                "field_count_estimate": int(item.text(4)) if item.text(4).isdigit() else 0,
                "group_description": "",
                "group_icon": "📋",
                "visible": True,
                "enabled": True
            }
        
        return groups
    
    def collect_modes_data(self) -> List[Dict]:
        """Sammelt Modi-Daten aus der UI"""
        
        modes = []
        for i in range(self.modes_tree.topLevelItemCount()):
            item = self.modes_tree.topLevelItem(i)
            
            tabs = []
            tabs_text = item.text(3)
            if tabs_text:
                tabs = [t.strip() for t in tabs_text.split(",") if t.strip()]
            
            mode = {
                "mode_id": int(item.text(0)) if item.text(0).isdigit() else 0,
                "mode_name": item.text(1),
                "mode_icon": item.text(2),
                "mode_tabs": tabs,
                "default_start_tab": item.text(4),
                "tab_organization": "horizontal"
            }
            modes.append(mode)
        
        return modes
    
    def validate_frame(self):
        """Validiert die Frame-Struktur"""
        
        errors = []
        
        # Basis-Validierung
        if not self.frame_name_edit.text():
            errors.append("Frame-Name ist erforderlich")
        
        # Tab-Validierung
        tab_ids = set()
        for i in range(self.tabs_tree.topLevelItemCount()):
            item = self.tabs_tree.topLevelItem(i)
            tab_id = item.text(0)
            if not tab_id:
                errors.append(f"Tab {i+1}: Tab-ID ist erforderlich")
            elif tab_id in tab_ids:
                errors.append(f"Tab-ID '{tab_id}' ist bereits vorhanden")
            else:
                tab_ids.add(tab_id)
        
        # Gruppen-Validierung
        group_ids = set()
        for i in range(self.groups_tree.topLevelItemCount()):
            item = self.groups_tree.topLevelItem(i)
            group_id = item.text(0)
            if not group_id:
                errors.append(f"Gruppe {i+1}: Gruppen-ID ist erforderlich")
            elif group_id in group_ids:
                errors.append(f"Gruppen-ID '{group_id}' ist bereits vorhanden")
            else:
                group_ids.add(group_id)
        
        # Ergebnis anzeigen
        if errors:
            error_text = "\n".join([f"• {error}" for error in errors])
            QMessageBox.warning(self, "Validierungsfehler", f"Folgende Fehler wurden gefunden:\n\n{error_text}")
        else:
            QMessageBox.information(self, "Validierung", "Alle Daten sind korrekt!")


class ExtendedPdvmDialogWidget(PdvmDialogWidget):
    """Erweiterte Version des PdvmDialogWidget für Frame-Bearbeitung"""
    
    def __init__(self, call_daten, parent=None):
        super().__init__(call_daten, parent)
        
        # Prüfen ob Frame-Bearbeitung aktiviert ist
        self.frame_editing_enabled = call_daten.get("enable_frame_editing", False)
        
        if self.frame_editing_enabled:
            self.add_frame_editing_features()
    
    def add_frame_editing_features(self):
        """Fügt Frame-Bearbeitungs-Features hinzu"""
        
        # Frame-Edit Button zur UI hinzufügen
        try:
            main_layout = self.layout()
            if main_layout:
                frame_edit_layout = QHBoxLayout()
                
                self.frame_edit_button = QPushButton("🏗️ Frame bearbeiten")
                self.frame_edit_button.clicked.connect(self.open_frame_editor)
                frame_edit_layout.addWidget(self.frame_edit_button)
                
                self.new_frame_button = QPushButton("➕ Neues Frame")
                self.new_frame_button.clicked.connect(self.create_new_frame)
                frame_edit_layout.addWidget(self.new_frame_button)
                
                frame_edit_layout.addStretch()
                
                # Layout zur Hauptlayout hinzufügen
                if isinstance(main_layout, QVBoxLayout):
                    main_layout.insertLayout(0, frame_edit_layout)
                else:
                    # Falls kein VBoxLayout, einen Wrapper erstellen
                    wrapper_layout = QVBoxLayout()
                    wrapper_layout.addLayout(frame_edit_layout)
                    
                    # Existierende Widgets sammeln
                    items = []
                    while main_layout.count():
                        child = main_layout.takeAt(0)
                        if child:
                            items.append(child)
                    
                    # Widgets zum Wrapper hinzufügen
                    for item in items:
                        if item.widget():
                            wrapper_layout.addWidget(item.widget())
                        elif item.layout():
                            wrapper_layout.addLayout(item.layout())
                    
                    self.setLayout(wrapper_layout)
        except Exception as e:
            logger.error(f"❌ Fehler beim Hinzufügen der Frame-Edit Features: {e}")
            # Fallback: Einfach die Buttons als Widget hinzufügen
            self.frame_edit_widget = QWidget()
            frame_edit_layout = QHBoxLayout(self.frame_edit_widget)
            
            self.frame_edit_button = QPushButton("🏗️ Frame bearbeiten")
            self.frame_edit_button.clicked.connect(self.open_frame_editor)
            frame_edit_layout.addWidget(self.frame_edit_button)
            
            self.new_frame_button = QPushButton("➕ Neues Frame")
            self.new_frame_button.clicked.connect(self.create_new_frame)
            frame_edit_layout.addWidget(self.new_frame_button)
    
    def open_frame_editor(self):
        """Öffnet den Frame-Editor"""
        
        try:
            # Aktuelle Frame-Daten laden
            frame_data = self.get_current_frame_data()
            
            # Editor-Dialog öffnen
            editor = FrameEditDialog(frame_data, self)
            editor.frame_saved.connect(self.on_frame_saved)
            editor.exec_()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Öffnen des Frame-Editors: {e}")
            QMessageBox.critical(self, "Fehler", f"Fehler beim Öffnen des Frame-Editors: {e}")
    
    def create_new_frame(self):
        """Erstellt ein neues Frame"""
        
        try:
            # Leerer Editor für neues Frame
            editor = FrameEditDialog(None, self)
            editor.frame_saved.connect(self.on_new_frame_created)
            editor.exec_()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen eines neuen Frames: {e}")
            QMessageBox.critical(self, "Fehler", f"Fehler beim Erstellen eines neuen Frames: {e}")
    
    def get_current_frame_data(self) -> Dict[str, Any]:
        """Holt die aktuellen Frame-Daten"""
        
        # Aus call_daten extrahieren (vereinfacht)
        frame_guid = self.call_daten.get("frame_guid", "")
        
        # Hier würde normalerweise aus der Datenbank geladen
        # Für Demo verwenden wir die call_daten
        frame_data = {
            "frame_guid": frame_guid,
            "frame_name": f"Frame {frame_guid[:8]}",
            "frame_description": "Bestehende Frame-Struktur",
            "view_guid": self.call_daten.get("view_guid", ""),
            "dialog_width": 1000,
            "dialog_height": 700,
            "default_grouping_style": "sections",
            "auto_save": True,
            "tabs": [],
            "groups": {},
            "modes": []
        }
        
        return frame_data
    
    def on_frame_saved(self, frame_guid: str, frame_data: Dict[str, Any]):
        """Callback wenn Frame gespeichert wurde"""
        
        logger.info(f"✅ Frame {frame_guid} wurde gespeichert")
        
        # Hier würde normalerweise in die Datenbank gespeichert
        # Für Demo nur Logging
        logger.info(f"   Frame-Name: {frame_data.get('frame_name')}")
        logger.info(f"   Anzahl Tabs: {len(frame_data.get('tabs', []))}")
        logger.info(f"   Anzahl Gruppen: {len(frame_data.get('groups', {}))}")
        
        # UI aktualisieren
        QMessageBox.information(self, "Frame gespeichert", 
                              f"Frame '{frame_data.get('frame_name')}' wurde erfolgreich gespeichert!")
    
    def on_new_frame_created(self, frame_guid: str, frame_data: Dict[str, Any]):
        """Callback wenn neues Frame erstellt wurde"""
        
        import uuid
        new_frame_guid = str(uuid.uuid4())
        
        logger.info(f"✅ Neues Frame {new_frame_guid} wurde erstellt")
        logger.info(f"   Frame-Name: {frame_data.get('frame_name')}")
        
        # Hier würde normalerweise in die Datenbank gespeichert
        # Für Demo nur Logging
        QMessageBox.information(self, "Neues Frame erstellt", 
                              f"Neues Frame '{frame_data.get('frame_name')}' wurde erfolgreich erstellt!\n"
                              f"GUID: {new_frame_guid}")


def demo_extended_dialog():
    """Demonstriert das erweiterte Dialog-Widget"""
    
    print("=== Extended PdvmDialogWidget Demo ===")
    
    # Demo Call-Daten mit Frame-Editing aktiviert
    call_daten = {
        "user_guid": "4886ad26-061b-4662-a762-c8c83f36692d",
        "frame_guid": "4078079f-4028-45ed-879c-3c779ecf3d0d",
        "view_guid": "0d10a0d0-b1a5-4544-b284-e8a09ca979b5",
        "mode": 1,  # Frame-Pflege Modus
        "language": "de",
        "enable_frame_editing": True  # Frame-Bearbeitung aktivieren
    }
    
    print("✅ Extended PdvmDialogWidget mit Frame-Editing konfiguriert")
    print(f"   Frame-GUID: {call_daten['frame_guid']}")
    print(f"   Modus: {call_daten['mode']} (Frame-Pflege)")
    print(f"   Frame-Editing: {call_daten['enable_frame_editing']}")
    
    print("\n=== Demo abgeschlossen ===")


if __name__ == "__main__":
    demo_extended_dialog()
