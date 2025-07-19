# -*- coding: utf-8 -*-
"""
PDVM Unified Frame Editor
Frame-Editor (Modus 1) für die Unified Database Structure
"""

import sys
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QLineEdit, QPushButton,
    QTextEdit, QSpinBox, QComboBox, QCheckBox, QGroupBox, QFormLayout, QListWidget,
    QListWidgetItem, QSplitter, QTreeWidget, QTreeWidgetItem, QDialog, QDialogButtonBox,
    QMessageBox, QScrollArea, QGridLayout, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from pdvm_unified_database_structure import PdvmUnifiedDatabaseManager

logger = logging.getLogger(__name__)

class UnifiedFrameEditor(QWidget):
    """Unified Frame-Editor für JSON-basierte Frame-Strukturen"""
    
    frame_saved = pyqtSignal(str, dict)  # frame_guid, frame_data
    frame_deleted = pyqtSignal(str)      # frame_guid
    
    def __init__(self, frame_guid: str = None, parent=None):
        super().__init__(parent)
        self.frame_guid = frame_guid
        self.frame_data = {}
        self.db_manager = PdvmUnifiedDatabaseManager()
        self.is_new_frame = frame_guid is None
        self.template_guids = {}
        
        self.init_ui()
        self.load_frame_data()
    
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = "🏗️ Neues Frame erstellen" if self.is_new_frame else "🏗️ Frame bearbeiten"
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("", 14, QFont.Bold))
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Template-Auswahl für neue Frames
        if self.is_new_frame:
            self.template_combo = QComboBox()
            self.template_combo.currentTextChanged.connect(self.on_template_selected)
            header_layout.addWidget(QLabel("Template:"))
            header_layout.addWidget(self.template_combo)
        
        layout.addLayout(header_layout)
        
        # Hauptbereich mit Tabs
        self.tab_widget = QTabWidget()
        
        # Tab 1: Grunddaten
        self.create_basic_info_tab()
        
        # Tab 2: Dialog-Konfiguration
        self.create_dialog_config_tab()
        
        # Tab 3: Tab-Struktur
        self.create_tab_structure_tab()
        
        # Tab 4: Input Controls
        self.create_input_controls_tab()
        
        # Tab 5: Erweitert
        self.create_advanced_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Button-Bereich
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("💾 Speichern")
        self.save_button.clicked.connect(self.save_frame)
        self.save_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        button_layout.addWidget(self.save_button)
        
        self.preview_button = QPushButton("👁️ Vorschau")
        self.preview_button.clicked.connect(self.preview_frame)
        button_layout.addWidget(self.preview_button)
        
        if not self.is_new_frame:
            self.delete_button = QPushButton("🗑️ Löschen")
            self.delete_button.clicked.connect(self.delete_frame)
            self.delete_button.setStyleSheet("background-color: #f44336; color: white;")
            button_layout.addWidget(self.delete_button)
        
        self.close_button = QPushButton("❌ Schließen")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
    
    def create_basic_info_tab(self):
        """Erstellt Tab für Grunddaten"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Frame-Grunddaten
        self.frame_name_edit = QLineEdit()
        layout.addRow("Frame-Name:", self.frame_name_edit)
        
        self.frame_description_edit = QTextEdit()
        self.frame_description_edit.setMaximumHeight(100)
        layout.addRow("Beschreibung:", self.frame_description_edit)
        
        self.view_guid_edit = QLineEdit()
        layout.addRow("View-GUID:", self.view_guid_edit)
        
        self.version_edit = QLineEdit()
        self.version_edit.setText("1.0")
        layout.addRow("Version:", self.version_edit)
        
        # Template-Info (nur anzeigen)
        self.template_type_label = QLabel("Standard")
        layout.addRow("Template-Typ:", self.template_type_label)
        
        self.tab_widget.addTab(tab, "📝 Grunddaten")
    
    def create_dialog_config_tab(self):
        """Erstellt Tab für Dialog-Konfiguration"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Dialog-Konfiguration
        self.mode_spin = QSpinBox()
        self.mode_spin.setRange(0, 10)
        layout.addRow("Modus:", self.mode_spin)
        
        self.dialog_type_combo = QComboBox()
        self.dialog_type_combo.addItems(["standard", "multi_tab", "modal", "embedded"])
        layout.addRow("Dialog-Typ:", self.dialog_type_combo)
        
        self.window_title_edit = QLineEdit()
        layout.addRow("Fenster-Titel:", self.window_title_edit)
        
        # Größe-Einstellungen
        size_group = QGroupBox("Fenster-Größe")
        size_layout = QFormLayout(size_group)
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(400, 2000)
        self.width_spin.setValue(800)
        size_layout.addRow("Breite:", self.width_spin)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(300, 1500)
        self.height_spin.setValue(600)
        size_layout.addRow("Höhe:", self.height_spin)
        
        self.resizable_check = QCheckBox("Größe änderbar")
        self.resizable_check.setChecked(True)
        size_layout.addRow("", self.resizable_check)
        
        layout.addRow(size_group)
        
        self.tab_widget.addTab(tab, "🖼️ Dialog")
    
    def create_tab_structure_tab(self):
        """Erstellt Tab für Tab-Struktur"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Tab-Verwaltung
        tab_header = QHBoxLayout()
        tab_header.addWidget(QLabel("Tab-Struktur:"))
        
        self.add_tab_button = QPushButton("➕ Tab hinzufügen")
        self.add_tab_button.clicked.connect(self.add_new_tab)
        tab_header.addWidget(self.add_tab_button)
        
        tab_header.addStretch()
        layout.addLayout(tab_header)
        
        # Tab-Liste
        splitter = QSplitter(Qt.Horizontal)
        
        # Links: Tab-Liste
        self.tab_list = QListWidget()
        self.tab_list.currentRowChanged.connect(self.on_tab_selected)
        splitter.addWidget(self.tab_list)
        
        # Rechts: Tab-Details
        self.tab_details_widget = QWidget()
        self.create_tab_details_ui()
        splitter.addWidget(self.tab_details_widget)
        
        splitter.setSizes([300, 500])
        layout.addWidget(splitter)
        
        self.tab_widget.addTab(tab, "📑 Tabs")
    
    def create_tab_details_ui(self):
        """Erstellt UI für Tab-Details"""
        layout = QVBoxLayout(self.tab_details_widget)
        
        # Tab-Eigenschaften
        form_layout = QFormLayout()
        
        self.tab_id_edit = QLineEdit()
        form_layout.addRow("Tab-ID:", self.tab_id_edit)
        
        self.tab_name_edit = QLineEdit()
        form_layout.addRow("Tab-Name:", self.tab_name_edit)
        
        self.tab_icon_edit = QLineEdit()
        form_layout.addRow("Tab-Icon:", self.tab_icon_edit)
        
        self.tab_active_check = QCheckBox()
        form_layout.addRow("Aktiv:", self.tab_active_check)
        
        layout.addLayout(form_layout)
        
        # Gruppen-Verwaltung
        group_header = QHBoxLayout()
        group_header.addWidget(QLabel("Gruppen:"))
        
        self.add_group_button = QPushButton("➕ Gruppe hinzufügen")
        self.add_group_button.clicked.connect(self.add_new_group)
        group_header.addWidget(self.add_group_button)
        
        group_header.addStretch()
        layout.addLayout(group_header)
        
        # Gruppen-Liste
        self.group_list = QListWidget()
        self.group_list.currentRowChanged.connect(self.on_group_selected)
        layout.addWidget(self.group_list)
    
    def create_input_controls_tab(self):
        """Erstellt Tab für Input Controls"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Placeholder für Input Controls
        info_label = QLabel("""
🔧 Input Controls

Hier können später Input Controls definiert werden:
• Feld-Definitionen
• Validierungs-Regeln
• Feld-Abhängigkeiten
• Layout-Einstellungen

(Wird in nächster Entwicklungsphase implementiert)
        """.strip())
        info_label.setStyleSheet("padding: 20px; background-color: #f0f0f0; border-radius: 5px;")
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "🎛️ Controls")
    
    def create_advanced_tab(self):
        """Erstellt Tab für erweiterte Einstellungen"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Zugriffskontrolle
        access_group = QGroupBox("Zugriffskontrolle")
        access_layout = QFormLayout(access_group)
        
        self.admin_required_check = QCheckBox()
        access_layout.addRow("Admin erforderlich:", self.admin_required_check)
        
        self.permissions_edit = QLineEdit()
        access_layout.addRow("Berechtigungen:", self.permissions_edit)
        
        layout.addRow(access_group)
        
        # UI-Verhalten
        behavior_group = QGroupBox("UI-Verhalten")
        behavior_layout = QFormLayout(behavior_group)
        
        self.auto_save_check = QCheckBox()
        behavior_layout.addRow("Auto-Speichern:", self.auto_save_check)
        
        self.confirm_close_check = QCheckBox()
        self.confirm_close_check.setChecked(True)
        behavior_layout.addRow("Schließen bestätigen:", self.confirm_close_check)
        
        self.validation_on_change_check = QCheckBox()
        self.validation_on_change_check.setChecked(True)
        behavior_layout.addRow("Validation bei Änderung:", self.validation_on_change_check)
        
        self.show_toolbar_check = QCheckBox()
        self.show_toolbar_check.setChecked(True)
        behavior_layout.addRow("Toolbar anzeigen:", self.show_toolbar_check)
        
        layout.addRow(behavior_group)
        
        # Daten-Binding
        binding_group = QGroupBox("Daten-Binding")
        binding_layout = QFormLayout(binding_group)
        
        self.data_source_edit = QLineEdit()
        binding_layout.addRow("Datenquelle:", self.data_source_edit)
        
        self.primary_key_edit = QLineEdit()
        self.primary_key_edit.setText("uid")
        binding_layout.addRow("Primärschlüssel:", self.primary_key_edit)
        
        self.load_method_combo = QComboBox()
        self.load_method_combo.addItems(["automatic", "manual", "on_demand"])
        binding_layout.addRow("Lade-Methode:", self.load_method_combo)
        
        self.save_method_combo = QComboBox()
        self.save_method_combo.addItems(["automatic", "manual", "on_confirm"])
        binding_layout.addRow("Speicher-Methode:", self.save_method_combo)
        
        layout.addRow(binding_group)
        
        self.tab_widget.addTab(tab, "⚙️ Erweitert")
    
    def load_frame_data(self):
        """Lädt Frame-Daten aus der Datenbank"""
        if not self.db_manager.connect():
            QMessageBox.critical(self, "Fehler", "Keine Datenbankverbindung möglich!")
            return
        
        # Template-GUIDs laden
        self.template_guids = self.db_manager.get_template_guids()
        
        if self.is_new_frame:
            # Template-Combo füllen
            template_names = {
                "frame_basic": "🔹 Basis Frame",
                "frame_datenpflege": "📝 Datenpflege Frame", 
                "frame_settings": "⚙️ Settings Frame",
                "frame_admin": "🔐 Admin Frame"
            }
            
            for key, name in template_names.items():
                if key in self.template_guids:
                    self.template_combo.addItem(name, key)
            
            # Standard-Template laden
            if self.template_combo.count() > 0:
                self.on_template_selected(self.template_combo.currentText())
        else:
            # Bestehende Frame-Daten laden
            record = self.db_manager.get_unified_record("framedaten", self.frame_guid)
            if record:
                self.frame_data = record['daten_parsed']
                self.populate_ui_from_data()
            else:
                QMessageBox.warning(self, "Warnung", f"Frame {self.frame_guid} nicht gefunden!")
        
        self.db_manager.disconnect()
    
    def on_template_selected(self, template_name: str):
        """Behandelt Template-Auswahl"""
        if not self.is_new_frame:
            return
        
        template_key = self.template_combo.currentData()
        if not template_key or template_key not in self.template_guids:
            return
        
        # Template aus Datenbank laden
        if self.db_manager.connect():
            template_guid = self.template_guids[template_key]
            record = self.db_manager.get_unified_record("framedaten", template_guid)
            
            if record:
                self.frame_data = record['daten_parsed'].copy()
                # GUID für neues Frame generieren
                self.frame_data['frame_info']['frame_guid'] = str(uuid.uuid4())
                self.frame_data['frame_info']['frame_bezeichnung'] = "Neues Frame"
                self.frame_data['frame_info']['created_date'] = datetime.now().isoformat()
                
                self.populate_ui_from_data()
            
            self.db_manager.disconnect()
    
    def populate_ui_from_data(self):
        """Füllt UI mit Frame-Daten"""
        if not self.frame_data:
            return
        
        frame_info = self.frame_data.get('frame_info', {})
        dialog_config = self.frame_data.get('dialog_config', {})
        tab_structure = self.frame_data.get('tab_structure', {})
        access_control = self.frame_data.get('access_control', {})
        ui_behavior = self.frame_data.get('ui_behavior', {})
        data_binding = self.frame_data.get('data_binding', {})
        
        # Grunddaten
        self.frame_name_edit.setText(frame_info.get('frame_bezeichnung', ''))
        self.frame_description_edit.setPlainText(frame_info.get('frame_beschreibung', ''))
        self.view_guid_edit.setText(frame_info.get('view_guid', ''))
        self.version_edit.setText(frame_info.get('version', '1.0'))
        self.template_type_label.setText(frame_info.get('template_type', 'Standard'))
        
        # Dialog-Konfiguration
        self.mode_spin.setValue(dialog_config.get('mode', 0))
        self.dialog_type_combo.setCurrentText(dialog_config.get('dialog_type', 'standard'))
        self.window_title_edit.setText(dialog_config.get('window_title', ''))
        
        window_size = dialog_config.get('window_size', {})
        self.width_spin.setValue(window_size.get('width', 800))
        self.height_spin.setValue(window_size.get('height', 600))
        self.resizable_check.setChecked(window_size.get('resizable', True))
        
        # Tab-Struktur
        self.populate_tab_structure(tab_structure)
        
        # Erweiterte Einstellungen
        self.admin_required_check.setChecked(access_control.get('admin_required', False))
        self.permissions_edit.setText(', '.join(access_control.get('required_permissions', [])))
        
        self.auto_save_check.setChecked(ui_behavior.get('auto_save', False))
        self.confirm_close_check.setChecked(ui_behavior.get('confirm_close', True))
        self.validation_on_change_check.setChecked(ui_behavior.get('validation_on_change', True))
        self.show_toolbar_check.setChecked(ui_behavior.get('show_toolbar', True))
        
        self.data_source_edit.setText(data_binding.get('data_source', ''))
        self.primary_key_edit.setText(data_binding.get('primary_key', 'uid'))
        self.load_method_combo.setCurrentText(data_binding.get('load_method', 'automatic'))
        self.save_method_combo.setCurrentText(data_binding.get('save_method', 'automatic'))
    
    def populate_tab_structure(self, tab_structure: Dict[str, Any]):
        """Füllt Tab-Struktur in UI"""
        self.tab_list.clear()
        
        tabs = tab_structure.get('tabs', [])
        for tab_data in tabs:
            item = QListWidgetItem(f"{tab_data.get('tab_icon', '📝')} {tab_data.get('tab_name', 'Tab')}")
            item.setData(Qt.UserRole, tab_data)
            self.tab_list.addItem(item)
        
        if self.tab_list.count() > 0:
            self.tab_list.setCurrentRow(0)
    
    def on_tab_selected(self, row: int):
        """Behandelt Tab-Auswahl"""
        if row < 0:
            return
        
        item = self.tab_list.item(row)
        tab_data = item.data(Qt.UserRole)
        
        if tab_data:
            self.tab_id_edit.setText(tab_data.get('tab_id', ''))
            self.tab_name_edit.setText(tab_data.get('tab_name', ''))
            self.tab_icon_edit.setText(tab_data.get('tab_icon', ''))
            self.tab_active_check.setChecked(tab_data.get('active', False))
            
            # Gruppen laden
            self.populate_groups(tab_data.get('groups', []))
    
    def populate_groups(self, groups: List[Dict[str, Any]]):
        """Füllt Gruppen in UI"""
        self.group_list.clear()
        
        for group_data in groups:
            item = QListWidgetItem(f"📁 {group_data.get('group_name', 'Gruppe')}")
            item.setData(Qt.UserRole, group_data)
            self.group_list.addItem(item)
    
    def on_group_selected(self, row: int):
        """Behandelt Gruppen-Auswahl"""
        # Placeholder für Gruppen-Details
        pass
    
    def add_new_tab(self):
        """Fügt neuen Tab hinzu"""
        # Vereinfachte Tab-Erstellung
        new_tab = {
            "tab_id": f"tab_{len(self.tab_list) + 1}",
            "tab_name": f"Neuer Tab {len(self.tab_list) + 1}",
            "tab_icon": "📝",
            "active": False,
            "groups": [
                {
                    "group_id": "group_main",
                    "group_name": "Hauptgruppe",
                    "group_type": "standard",
                    "layout": "form",
                    "columns": 1,
                    "fields": []
                }
            ]
        }
        
        item = QListWidgetItem(f"{new_tab['tab_icon']} {new_tab['tab_name']}")
        item.setData(Qt.UserRole, new_tab)
        self.tab_list.addItem(item)
        self.tab_list.setCurrentItem(item)
    
    def add_new_group(self):
        """Fügt neue Gruppe hinzu"""
        current_row = self.tab_list.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "Info", "Bitte wählen Sie zuerst einen Tab aus!")
            return
        
        # Vereinfachte Gruppen-Erstellung
        new_group = {
            "group_id": f"group_{len(self.group_list) + 1}",
            "group_name": f"Neue Gruppe {len(self.group_list) + 1}",
            "group_type": "standard",
            "layout": "form",
            "columns": 1,
            "fields": []
        }
        
        item = QListWidgetItem(f"📁 {new_group['group_name']}")
        item.setData(Qt.UserRole, new_group)
        self.group_list.addItem(item)
    
    def collect_ui_data(self) -> Dict[str, Any]:
        """Sammelt Daten aus UI"""
        # Basis-Struktur
        frame_data = {
            "frame_info": {
                "frame_guid": self.frame_guid or str(uuid.uuid4()),
                "frame_bezeichnung": self.frame_name_edit.text(),
                "frame_beschreibung": self.frame_description_edit.toPlainText(),
                "view_guid": self.view_guid_edit.text(),
                "created_date": datetime.now().isoformat(),
                "created_by": "user",
                "version": self.version_edit.text(),
                "template_type": self.template_type_label.text()
            },
            
            "dialog_config": {
                "mode": self.mode_spin.value(),
                "dialog_type": self.dialog_type_combo.currentText(),
                "window_title": self.window_title_edit.text(),
                "window_size": {
                    "width": self.width_spin.value(),
                    "height": self.height_spin.value(),
                    "resizable": self.resizable_check.isChecked()
                },
                "layout": "vertical"
            },
            
            "tab_structure": {
                "tab_count": self.tab_list.count(),
                "default_tab": 0,
                "tabs": []
            },
            
            "input_controls": {
                "controls": [],
                "validation_rules": {},
                "field_dependencies": {}
            },
            
            "access_control": {
                "required_permissions": [p.strip() for p in self.permissions_edit.text().split(',') if p.strip()],
                "admin_required": self.admin_required_check.isChecked(),
                "read_only_fields": [],
                "hidden_fields": []
            },
            
            "data_binding": {
                "data_source": self.data_source_edit.text(),
                "primary_key": self.primary_key_edit.text(),
                "load_method": self.load_method_combo.currentText(),
                "save_method": self.save_method_combo.currentText()
            },
            
            "ui_behavior": {
                "auto_save": self.auto_save_check.isChecked(),
                "confirm_close": self.confirm_close_check.isChecked(),
                "validation_on_change": self.validation_on_change_check.isChecked(),
                "show_toolbar": self.show_toolbar_check.isChecked()
            }
        }
        
        # Tab-Daten sammeln
        tabs = []
        for i in range(self.tab_list.count()):
            item = self.tab_list.item(i)
            tab_data = item.data(Qt.UserRole)
            if tab_data:
                tabs.append(tab_data)
        
        frame_data["tab_structure"]["tabs"] = tabs
        
        return frame_data
    
    def save_frame(self):
        """Speichert Frame in Datenbank"""
        try:
            # Daten sammeln
            frame_data = self.collect_ui_data()
            frame_guid = frame_data["frame_info"]["frame_guid"]
            
            if not self.db_manager.connect():
                QMessageBox.critical(self, "Fehler", "Keine Datenbankverbindung möglich!")
                return
            
            # In Datenbank speichern
            success = self.db_manager.insert_unified_record(
                table="framedaten",
                uid=frame_guid,
                daten=json.dumps(frame_data, ensure_ascii=False),
                name=frame_data["frame_info"]["frame_bezeichnung"]
            )
            
            self.db_manager.disconnect()
            
            if success:
                QMessageBox.information(self, "Erfolg", "Frame erfolgreich gespeichert!")
                self.frame_saved.emit(frame_guid, frame_data)
                
                # Update für neue Frames
                if self.is_new_frame:
                    self.frame_guid = frame_guid
                    self.is_new_frame = False
                    self.title_label.setText("🏗️ Frame bearbeiten")
                    
                    # Delete-Button hinzufügen
                    if not hasattr(self, 'delete_button'):
                        button_layout = self.layout().itemAt(self.layout().count() - 1).layout()
                        self.delete_button = QPushButton("🗑️ Löschen")
                        self.delete_button.clicked.connect(self.delete_frame)
                        self.delete_button.setStyleSheet("background-color: #f44336; color: white;")
                        button_layout.insertWidget(button_layout.count() - 1, self.delete_button)
            else:
                QMessageBox.critical(self, "Fehler", "Fehler beim Speichern des Frames!")
                
        except Exception as e:
            logger.exception("❌ Fehler beim Speichern des Frames:")
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern:\n\n{e}")
    
    def preview_frame(self):
        """Zeigt Frame-Vorschau"""
        # Placeholder für Vorschau-Funktionalität
        frame_data = self.collect_ui_data()
        
        preview_text = f"""
🔍 Frame-Vorschau

📝 Name: {frame_data['frame_info']['frame_bezeichnung']}
🔧 Modus: {frame_data['dialog_config']['mode']}
📑 Tabs: {frame_data['tab_structure']['tab_count']}
📊 Größe: {frame_data['dialog_config']['window_size']['width']}x{frame_data['dialog_config']['window_size']['height']}

(Detaillierte Vorschau wird in nächster Phase implementiert)
        """.strip()
        
        QMessageBox.information(self, "Frame-Vorschau", preview_text)
    
    def delete_frame(self):
        """Löscht Frame aus Datenbank"""
        if self.is_new_frame:
            return
        
        reply = QMessageBox.question(
            self, "Löschen bestätigen",
            f"Soll das Frame '{self.frame_name_edit.text()}' wirklich gelöscht werden?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if self.db_manager.connect():
                    cursor = self.db_manager.connection.cursor()
                    cursor.execute("DELETE FROM framedaten WHERE uid = ?", (self.frame_guid,))
                    self.db_manager.connection.commit()
                    self.db_manager.disconnect()
                    
                    QMessageBox.information(self, "Erfolg", "Frame erfolgreich gelöscht!")
                    self.frame_deleted.emit(self.frame_guid)
                    self.close()
                else:
                    QMessageBox.critical(self, "Fehler", "Keine Datenbankverbindung möglich!")
                    
            except Exception as e:
                logger.exception("❌ Fehler beim Löschen des Frames:")
                QMessageBox.critical(self, "Fehler", f"Fehler beim Löschen:\n\n{e}")


class UnifiedFrameEditorDialog(QDialog):
    """Dialog-Wrapper für den Unified Frame Editor"""
    
    def __init__(self, frame_guid: str = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🏗️ Unified Frame Editor")
        self.setModal(True)
        self.resize(1000, 700)
        
        layout = QVBoxLayout(self)
        
        # Frame Editor einbetten
        self.frame_editor = UnifiedFrameEditor(frame_guid, self)
        layout.addWidget(self.frame_editor)
        
        # Signale weiterleiten
        self.frame_editor.frame_saved.connect(self.accept)
        self.frame_editor.frame_deleted.connect(self.accept)


if __name__ == "__main__":
    # Test des Unified Frame Editors
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Neuen Frame erstellen
    editor = UnifiedFrameEditorDialog()
    editor.show()
    
    sys.exit(app.exec_())
