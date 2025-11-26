"""
PDVM System Editor V2 - Vereinfachte flache Struktur
======================================================

Komplett neu entwickelt für lineare GRUPPE→FELD Struktur ohne Verschachtelungen.

ARCHITEKTUR:
1. TAB 1: ROOT Properties (direkte Werte ohne GUID)
2. TAB 2: 3-Spalten-Layout
   - Spalte 1: Gruppen-Liste (+ / -)
   - Spalte 2: Felder-Liste (+ / -) mit ↑↓ Sortierung
   - Spalte 3: Properties-Editor + Configs-Sektion

FEATURES:
- Farbliche Markierung: Gelb=geändert, Grün=neu, Rot=gelöscht
- Undo/Redo vor Save
- Validierung vor Save
- Property-Kopie für schnelles Anlegen
- Tabellen-spezifische Templates

DATENFLUSS:
PdvmCentralDatenbank → self.data (dict) → UI → self.changes_stack → Save

Erstellt: 26.11.2025
"""

import sys
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QListWidget, QListWidgetItem, QPushButton, QLabel,
    QLineEdit, QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox,
    QTextEdit, QGroupBox, QScrollArea, QFormLayout, QMessageBox,
    QSplitter, QTableWidget, QTableWidgetItem, QHeaderView,
    QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont

# Import PdvmCentralDatenbank
from pdvm_central_datenbank import PdvmCentralDatenbank
from pdvm_central_systemsteuerung import get_gcs

logger = logging.getLogger(__name__)


class ChangeType:
    """Änderungs-Typen für Change-Tracking"""
    ADDED = "added"      # Neu hinzugefügt (Grün)
    MODIFIED = "modified"  # Geändert (Gelb)
    DELETED = "deleted"   # Gelöscht (Rot)


class PdvmSystemEditor(QDialog):
    """
    Vereinfachter System-Editor V2 für flache Strukturen
    
    Unterstützt alle sys_* Tabellen mit einheitlichem Interface:
    - sys_framedaten
    - sys_viewdaten
    - sys_dialogdaten
    - sys_menudaten
    """
    
    def __init__(self, table_name: str, record_uid: str, parent=None):
        """
        Initialisiert System-Editor
        
        Args:
            table_name: Name der Tabelle (z.B. 'sys_framedaten')
            record_uid: UID des Datensatzes
            parent: Parent-Widget
        """
        super().__init__(parent)
        
        # Basis-Konfiguration
        self.table_name = table_name
        self.record_uid = record_uid
        self.gcs = get_gcs()
        
        # Datenbank-Verbindung - WICHTIG: Mit record_uid, nicht user_guid!
        self.db = PdvmCentralDatenbank(table_name, record_uid)
        
        # Daten laden
        self.original_data = {}  # Original aus DB
        self.data = {}           # Aktuelle Working Copy
        self.templates = {}      # Templates für Properties
        
        # Change-Tracking
        self.changes_stack = []  # Liste von (change_type, path, old_value, new_value)
        self.stack_index = -1    # Aktueller Index für Undo/Redo
        
        # Property-Clipboard für Kopier-Funktion
        self.property_clipboard = []  # Liste der ausgewählten Property-Namen
        
        # Dirty-Flag für Feld-Editor
        self.feld_dirty = False
        self.current_feld_backup = None  # Backup für Abbrechen
        
        # UI-Komponenten
        self.root_widgets = {}   # Widgets für ROOT-Tab
        self.gruppe_list = None  # Gruppen-Liste
        self.feld_list = None    # Felder-Liste
        self.property_container = None  # Container für Properties
        self.config_container = None    # Container für Configs
        
        # Init
        self._load_data()
        self._load_templates()
        self._setup_ui()
        self._connect_signals()
        
        logger.info(f"✅ System-Editor V2 initialisiert: {table_name} / {record_uid}")
    
    def _load_data(self):
        """Lädt Daten aus Datenbank"""
        logger.info(f"📂 Lade Daten aus {self.table_name}...")
        
        # Daten via get_value_by_group laden
        all_groups = [k for k in self.db.data.keys()]
        
        for gruppe_name in all_groups:
            gruppe_data = self.db.get_value_by_group(gruppe_name)
            self.data[gruppe_name] = gruppe_data.copy() if gruppe_data else {}
        
        # Original-Kopie für Diff
        self.original_data = json.loads(json.dumps(self.data))
        
        logger.info(f"  ✅ {len(self.data)} Gruppen geladen")
    
    def _load_templates(self):
        """Lädt Templates für Property-Auswahl"""
        logger.info(f"📋 Lade Templates für {self.table_name}...")
        
        # Templates aus TEMPLATES Gruppe laden (falls vorhanden)
        if 'TEMPLATES' in self.data:
            self.templates = self.data['TEMPLATES'].copy()
            logger.info(f"  ✅ {len(self.templates)} Templates geladen")
        else:
            # Default-Template erstellen
            self.templates = self._create_default_templates()
            logger.info(f"  ⚠️ Keine Templates gefunden - verwende Defaults")
    
    def _create_default_templates(self) -> dict:
        """Erstellt Default-Templates für Properties"""
        return {
            'field_properties': {
                'name': {'type': 'string', 'required': True, 'label': 'Name'},
                'label': {'type': 'string', 'required': True, 'label': 'Label'},
                'type': {'type': 'choice', 'values': ['string', 'int', 'float', 'bool', 'date'], 'label': 'Typ'},
                'show': {'type': 'bool', 'default': True, 'label': 'Anzeigen'},
                'expert_mode': {'type': 'bool', 'default': False, 'label': 'Expert-Modus'},
                'display_order': {'type': 'int', 'default': 999, 'label': 'Reihenfolge'},
                'searchable': {'type': 'bool', 'default': True, 'label': 'Durchsuchbar'},
                'sortable': {'type': 'bool', 'default': True, 'label': 'Sortierbar'},
            },
            'config_types': {
                'dropdown': {'table': 'string', 'key': 'string', 'feld': 'string', 'gruppe': 'string'},
                'help': {'table': 'string', 'key': 'string', 'feld': 'string', 'gruppe': 'string'},
                'viewtable': {'table': 'string', 'key': 'string', 'feld': 'string', 'gruppe': 'string'},
            }
        }
    
    def _setup_ui(self):
        """Baut UI auf"""
        self.setWindowTitle(f"System-Editor: {self.table_name}")
        self.setMinimumSize(1200, 800)
        
        # Haupt-Layout
        main_layout = QVBoxLayout(self)
        
        # Tab-Widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Tab 1: ROOT Properties
        self.root_tab = self._create_root_tab()
        self.tabs.addTab(self.root_tab, "ROOT Properties")
        
        # Tab 2: Gruppen & Felder
        self.gruppen_tab = self._create_gruppen_tab()
        self.tabs.addTab(self.gruppen_tab, "Gruppen & Felder")
        
        # Button-Leiste unten
        button_layout = QHBoxLayout()
        
        # Undo/Redo
        self.undo_btn = QPushButton("↶ Undo")
        self.undo_btn.setEnabled(False)
        self.undo_btn.clicked.connect(self._undo)
        button_layout.addWidget(self.undo_btn)
        
        self.redo_btn = QPushButton("↷ Redo")
        self.redo_btn.setEnabled(False)
        self.redo_btn.clicked.connect(self._redo)
        button_layout.addWidget(self.redo_btn)
        
        button_layout.addStretch()
        
        # Änderungen anzeigen
        changes_btn = QPushButton("📊 Änderungen anzeigen")
        changes_btn.clicked.connect(self._show_changes)
        button_layout.addWidget(changes_btn)
        
        # Verwerfen
        discard_btn = QPushButton("❌ Verwerfen")
        discard_btn.clicked.connect(self._discard_changes)
        button_layout.addWidget(discard_btn)
        
        # Speichern
        save_btn = QPushButton("💾 Speichern")
        save_btn.clicked.connect(self._save_changes)
        button_layout.addWidget(save_btn)
        
        main_layout.addLayout(button_layout)
    
    def _create_root_tab(self) -> QWidget:
        """Erstellt ROOT Properties Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Scroll-Area für viele Properties
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        form_layout = QFormLayout(scroll_content)
        
        # ROOT-Properties durchgehen
        root_data = self.data.get('ROOT', {})
        
        for key, value in sorted(root_data.items()):
            # Widget basierend auf Typ erstellen
            editor_widget = self._create_editor_widget(value, f"ROOT.{key}")
            self.root_widgets[key] = editor_widget
            
            label = QLabel(f"{key}:")
            label.setFont(QFont("Arial", 10, QFont.Bold))
            form_layout.addRow(label, editor_widget)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return widget
    
    def _create_gruppen_tab(self) -> QWidget:
        """Erstellt Gruppen & Felder Tab mit 3-Spalten-Layout"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Splitter für 3 Bereiche
        splitter = QSplitter(Qt.Horizontal)
        
        # === SPALTE 1: GRUPPEN ===
        gruppen_widget = QWidget()
        gruppen_layout = QVBoxLayout(gruppen_widget)
        
        gruppen_layout.addWidget(QLabel("<b>GRUPPEN</b>"))
        
        self.gruppe_list = QListWidget()
        self.gruppe_list.currentItemChanged.connect(self._on_gruppe_selected)
        gruppen_layout.addWidget(self.gruppe_list)
        
        # Gruppen-Buttons
        gruppen_btn_layout = QHBoxLayout()
        add_gruppe_btn = QPushButton("+ Gruppe")
        add_gruppe_btn.clicked.connect(self._add_gruppe)
        remove_gruppe_btn = QPushButton("- Gruppe")
        remove_gruppe_btn.clicked.connect(self._remove_gruppe)
        gruppen_btn_layout.addWidget(add_gruppe_btn)
        gruppen_btn_layout.addWidget(remove_gruppe_btn)
        gruppen_layout.addLayout(gruppen_btn_layout)
        
        splitter.addWidget(gruppen_widget)
        
        # === SPALTE 2: FELDER ===
        felder_widget = QWidget()
        felder_layout = QVBoxLayout(felder_widget)
        
        felder_layout.addWidget(QLabel("<b>FELDER</b>"))
        
        self.feld_list = QListWidget()
        self.feld_list.currentItemChanged.connect(self._on_feld_selected)
        felder_layout.addWidget(self.feld_list)
        
        # Feld-Buttons
        feld_btn_layout = QHBoxLayout()
        add_feld_btn = QPushButton("+ Feld")
        add_feld_btn.clicked.connect(self._add_feld)
        remove_feld_btn = QPushButton("- Feld")
        remove_feld_btn.clicked.connect(self._remove_feld)
        feld_btn_layout.addWidget(add_feld_btn)
        feld_btn_layout.addWidget(remove_feld_btn)
        felder_layout.addLayout(feld_btn_layout)
        
        # Sortierungs-Buttons
        sort_btn_layout = QHBoxLayout()
        move_up_btn = QPushButton("↑ Hoch")
        move_up_btn.clicked.connect(self._move_feld_up)
        move_down_btn = QPushButton("↓ Runter")
        move_down_btn.clicked.connect(self._move_feld_down)
        sort_btn_layout.addWidget(move_up_btn)
        sort_btn_layout.addWidget(move_down_btn)
        felder_layout.addLayout(sort_btn_layout)
        
        splitter.addWidget(felder_widget)
        
        # === SPALTE 3: PROPERTIES ===
        properties_widget = QWidget()
        properties_layout = QVBoxLayout(properties_widget)
        
        # Übernehmen/Abbrechen Buttons für Feld-Editor
        feld_button_layout = QHBoxLayout()
        self.feld_uebernehmen_btn = QPushButton("✅ Übernehmen")
        self.feld_uebernehmen_btn.clicked.connect(self._feld_uebernehmen)
        self.feld_uebernehmen_btn.setEnabled(False)
        self.feld_abbrechen_btn = QPushButton("❌ Abbrechen")
        self.feld_abbrechen_btn.clicked.connect(self._feld_abbrechen)
        self.feld_abbrechen_btn.setEnabled(False)
        feld_button_layout.addWidget(self.feld_uebernehmen_btn)
        feld_button_layout.addWidget(self.feld_abbrechen_btn)
        feld_button_layout.addStretch()
        properties_layout.addLayout(feld_button_layout)
        
        properties_layout.addWidget(QLabel("<b>PROPERTIES</b>"))
        
        # Scroll-Area für Properties
        prop_scroll = QScrollArea()
        prop_scroll.setWidgetResizable(True)
        self.property_container = QWidget()
        self.property_layout = QFormLayout(self.property_container)
        prop_scroll.setWidget(self.property_container)
        properties_layout.addWidget(prop_scroll)
        
        # Property-Management Buttons
        prop_btn_layout = QHBoxLayout()
        copy_props_btn = QPushButton("📋 Properties kopieren")
        copy_props_btn.clicked.connect(self._copy_properties)
        add_prop_btn = QPushButton("+ Property")
        add_prop_btn.clicked.connect(self._add_property)
        remove_prop_btn = QPushButton("- Property")
        remove_prop_btn.clicked.connect(self._remove_property)
        prop_btn_layout.addWidget(copy_props_btn)
        prop_btn_layout.addWidget(add_prop_btn)
        prop_btn_layout.addWidget(remove_prop_btn)
        properties_layout.addLayout(prop_btn_layout)
        
        # Separator
        separator = QLabel("═" * 50)
        separator.setAlignment(Qt.AlignCenter)
        properties_layout.addWidget(separator)
        
        # CONFIGS Sektion
        properties_layout.addWidget(QLabel("<b>CONFIGS</b>"))
        
        config_scroll = QScrollArea()
        config_scroll.setWidgetResizable(True)
        self.config_container = QWidget()
        self.config_layout = QFormLayout(self.config_container)
        config_scroll.setWidget(self.config_container)
        properties_layout.addWidget(config_scroll)
        
        # Config-Management Buttons
        config_btn_layout = QHBoxLayout()
        add_config_btn = QPushButton("+ Config")
        add_config_btn.clicked.connect(self._add_config)
        remove_config_btn = QPushButton("- Config")
        remove_config_btn.clicked.connect(self._remove_config)
        config_btn_layout.addWidget(add_config_btn)
        config_btn_layout.addWidget(remove_config_btn)
        properties_layout.addLayout(config_btn_layout)
        
        splitter.addWidget(properties_widget)
        
        # Splitter-Verhältnis: 1:1:2
        splitter.setSizes([250, 250, 500])
        
        layout.addWidget(splitter)
        
        # Gruppen-Liste initial befüllen
        self._refresh_gruppen_list()
        
        return widget
    
    def _create_editor_widget(self, value: Any, path: str) -> QWidget:
        """
        Erstellt passendes Editor-Widget für Wert
        
        Args:
            value: Aktueller Wert
            path: Pfad zum Wert (z.B. 'ROOT.TABLE' oder 'PERSONDATEN.guid.name')
            
        Returns:
            Editor-Widget
        """
        # Prüfe ob ROOT-Editor oder Feld-Editor
        is_feld_editor = not path.startswith('ROOT.')
        
        if isinstance(value, bool):
            widget = QCheckBox()
            widget.setChecked(value)
            if is_feld_editor:
                widget.stateChanged.connect(lambda state, p=path: self._on_feld_editor_changed(p, state == Qt.Checked))
            else:
                widget.stateChanged.connect(lambda: self._track_change(path, value, widget.isChecked()))
            return widget
        
        elif isinstance(value, int):
            widget = QSpinBox()
            widget.setRange(-999999, 999999)
            widget.setValue(value)
            if is_feld_editor:
                widget.valueChanged.connect(lambda val, p=path: self._on_feld_editor_changed(p, val))
            else:
                widget.valueChanged.connect(lambda: self._track_change(path, value, widget.value()))
            return widget
        
        elif isinstance(value, float):
            widget = QDoubleSpinBox()
            widget.setRange(-999999.99, 999999.99)
            widget.setValue(value)
            if is_feld_editor:
                widget.valueChanged.connect(lambda val, p=path: self._on_feld_editor_changed(p, val))
            else:
                widget.valueChanged.connect(lambda: self._track_change(path, value, widget.value()))
            return widget
        
        else:  # String oder andere
            widget = QLineEdit()
            widget.setText(str(value))
            if is_feld_editor:
                widget.textChanged.connect(lambda text, p=path: self._on_feld_editor_changed(p, text))
            else:
                widget.textChanged.connect(lambda: self._track_change(path, value, widget.text()))
            return widget
    
    def _refresh_gruppen_list(self):
        """Aktualisiert Gruppen-Liste"""
        self.gruppe_list.clear()
        
        # Alle Gruppen außer ROOT und TEMPLATES
        gruppen = [k for k in self.data.keys() if k not in ['ROOT', 'TEMPLATES']]
        
        for gruppe_name in sorted(gruppen):
            item = QListWidgetItem(gruppe_name)
            
            # Farbmarkierung bei Änderungen
            if self._is_gruppe_changed(gruppe_name):
                item.setBackground(QColor(255, 255, 200))  # Gelb
            if self._is_gruppe_new(gruppe_name):
                item.setBackground(QColor(200, 255, 200))  # Grün
            
            self.gruppe_list.addItem(item)
    
    def _refresh_felder_list(self, gruppe_name: str):
        """Aktualisiert Felder-Liste für Gruppe"""
        self.feld_list.clear()
        
        if gruppe_name not in self.data:
            return
        
        felder_dict = self.data[gruppe_name]
        
        # Nach display_order sortieren
        felder_sorted = sorted(
            felder_dict.items(),
            key=lambda x: x[1].get('display_order', 999)
        )
        
        for feld_guid, feld_data in felder_sorted:
            # Label anzeigen (name + key im Tooltip)
            display_label = feld_data.get('label', 'Kein Label')
            item = QListWidgetItem(display_label)
            item.setData(Qt.UserRole, feld_guid)  # GUID speichern
            
            # Tooltip mit name und key
            name = feld_data.get('name', 'Kein Name')
            tooltip = f"Name: {name}\nKey: {feld_guid}"
            item.setToolTip(tooltip)
            
            # Farbmarkierung
            if self._is_feld_changed(gruppe_name, feld_guid):
                item.setBackground(QColor(255, 255, 200))  # Gelb
            if self._is_feld_new(gruppe_name, feld_guid):
                item.setBackground(QColor(200, 255, 200))  # Grün
            
            self.feld_list.addItem(item)
    
    def _refresh_properties_editor(self, gruppe_name: str, feld_guid: str):
        """Aktualisiert Properties-Editor für Feld"""
        # Properties-Container leeren
        while self.property_layout.count():
            child = self.property_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Config-Container leeren
        while self.config_layout.count():
            child = self.config_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if gruppe_name not in self.data or feld_guid not in self.data[gruppe_name]:
            return
        
        feld_data = self.data[gruppe_name][feld_guid]
        
        # === PROPERTIES ===
        for prop_name, prop_value in sorted(feld_data.items()):
            if prop_name == 'configs':  # Configs separat behandeln
                continue
            
            path = f"{gruppe_name}.{feld_guid}.{prop_name}"
            editor = self._create_editor_widget(prop_value, path)
            
            label = QLabel(f"{prop_name}:")
            self.property_layout.addRow(label, editor)
        
        # === CONFIGS ===
        if 'configs' in feld_data:
            configs = feld_data['configs']
            
            for config_name, config_value in sorted(configs.items()):
                # Config ist dict mit table, key, feld, gruppe
                config_group = QGroupBox(config_name.upper())
                config_form = QFormLayout()
                
                for config_key, config_val in sorted(config_value.items()):
                    path = f"{gruppe_name}.{feld_guid}.configs.{config_name}.{config_key}"
                    editor = self._create_editor_widget(config_val, path)
                    config_form.addRow(QLabel(f"{config_key}:"), editor)
                
                config_group.setLayout(config_form)
                self.config_layout.addRow(config_group)
    
    def _connect_signals(self):
        """Verbindet Signale"""
        pass  # Bereits in _create_editor_widget verbunden
    
    def _on_feld_editor_changed(self, path: str, value):
        """Editor-Wert hat sich geändert - setze Dirty-Flag"""
        if not self.feld_dirty:
            # Backup beim ersten Dirty machen
            gruppe_item = self.gruppe_list.currentItem()
            feld_item = self.feld_list.currentItem()
            if gruppe_item and feld_item:
                gruppe_name = gruppe_item.text()
                feld_guid = feld_item.data(Qt.UserRole)
                self.current_feld_backup = json.loads(json.dumps(self.data[gruppe_name][feld_guid]))
        
        self.feld_dirty = True
        self.feld_uebernehmen_btn.setEnabled(True)
        self.feld_abbrechen_btn.setEnabled(True)
        
        # Wert temporär in working copy speichern
        self._apply_editor_value(path, value)
    
    def _apply_editor_value(self, path: str, value):
        """Wendet Editor-Wert auf Daten an (ohne Change-Tracking)"""
        parts = path.split('.')
        gruppe_name = parts[0]
        feld_guid = parts[1]
        
        if len(parts) == 3:
            # Property: GRUPPE.GUID.property_name
            property_name = parts[2]
            self.data[gruppe_name][feld_guid][property_name] = value
        elif len(parts) == 5 and parts[2] == 'configs':
            # Config: GRUPPE.GUID.configs.config_name.config_key
            config_name = parts[3]
            config_key = parts[4]
            if 'configs' not in self.data[gruppe_name][feld_guid]:
                self.data[gruppe_name][feld_guid]['configs'] = {}
            if config_name not in self.data[gruppe_name][feld_guid]['configs']:
                self.data[gruppe_name][feld_guid]['configs'][config_name] = {}
            self.data[gruppe_name][feld_guid]['configs'][config_name][config_key] = value
    
    def _feld_uebernehmen(self):
        """Übernimmt Feld-Änderungen"""
        if not self.feld_dirty:
            return
        
        gruppe_item = self.gruppe_list.currentItem()
        feld_item = self.feld_list.currentItem()
        
        if not gruppe_item or not feld_item:
            return
        
        gruppe_name = gruppe_item.text()
        feld_guid = feld_item.data(Qt.UserRole)
        
        # Change-Tracking mit Backup
        if self.current_feld_backup:
            current_data = self.data[gruppe_name][feld_guid].copy()
            self._track_change(
                f"{gruppe_name}.{feld_guid}",
                self.current_feld_backup,
                current_data,
                ChangeType.MODIFIED
            )
        
        # Dirty-Flag zurücksetzen
        self.feld_dirty = False
        self.current_feld_backup = None
        self.feld_uebernehmen_btn.setEnabled(False)
        self.feld_abbrechen_btn.setEnabled(False)
        
        # Felder-Liste aktualisieren (Name könnte geändert sein)
        self._refresh_felder_list(gruppe_name)
        
        # Feld wieder auswählen
        for i in range(self.feld_list.count()):
            if self.feld_list.item(i).data(Qt.UserRole) == feld_guid:
                self.feld_list.setCurrentRow(i)
                break
        
        logger.info(f"✅ Feld-Änderungen übernommen: {feld_guid}")
    
    def _feld_abbrechen(self):
        """Bricht Feld-Änderungen ab"""
        if not self.feld_dirty:
            return
        
        gruppe_item = self.gruppe_list.currentItem()
        feld_item = self.feld_list.currentItem()
        
        if not gruppe_item or not feld_item:
            return
        
        gruppe_name = gruppe_item.text()
        feld_guid = feld_item.data(Qt.UserRole)
        
        # Backup wiederherstellen
        if self.current_feld_backup:
            self.data[gruppe_name][feld_guid] = self.current_feld_backup.copy()
        
        # Dirty-Flag zurücksetzen
        self.feld_dirty = False
        self.current_feld_backup = None
        self.feld_uebernehmen_btn.setEnabled(False)
        self.feld_abbrechen_btn.setEnabled(False)
        
        # Properties-Editor neu laden
        self._refresh_properties_editor()
        
        logger.info(f"❌ Feld-Änderungen abgebrochen: {feld_guid}")
    
    # ========================================
    # GRUPPEN-MANAGEMENT
    # ========================================
    
    def _on_gruppe_selected(self, current, previous):
        """Gruppe wurde ausgewählt"""
        # Prüfe auf ungespeicherte Änderungen im Feld-Editor
        if self.feld_dirty:
            reply = QMessageBox.question(
                self,
                "Ungespeicherte Änderungen",
                "Änderungen übernehmen?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Cancel:
                # Wechsel abbrechen - vorherige Gruppe wieder auswählen
                if previous:
                    self.gruppe_list.blockSignals(True)
                    self.gruppe_list.setCurrentItem(previous)
                    self.gruppe_list.blockSignals(False)
                return
            elif reply == QMessageBox.Yes:
                self._feld_uebernehmen()
            else:
                self._feld_abbrechen()
        
        if not current:
            return
        
        gruppe_name = current.text()
        self._refresh_felder_list(gruppe_name)
    
    def _add_gruppe(self):
        """Fügt neue Gruppe hinzu"""
        from PyQt5.QtWidgets import QInputDialog
        
        # Name abfragen
        name, ok = QInputDialog.getText(
            self,
            "Neue Gruppe",
            "Gruppen-Name (GROSSBUCHSTABEN):"
        )
        
        if not ok or not name:
            return
        
        # In Großbuchstaben konvertieren
        name = name.upper().strip()
        
        # Validierung
        if name in self.data:
            QMessageBox.warning(self, "Fehler", f"Gruppe '{name}' existiert bereits!")
            return
        
        if name in ['ROOT', 'TEMPLATES']:
            QMessageBox.warning(self, "Fehler", "Reservierter Name!")
            return
        
        # Gruppe hinzufügen
        self.data[name] = {}
        self._track_change(f"GRUPPE.{name}", None, {}, ChangeType.ADDED)
        
        # UI aktualisieren
        self._refresh_gruppen_list()
        
        # Neue Gruppe auswählen
        for i in range(self.gruppe_list.count()):
            if self.gruppe_list.item(i).text() == name:
                self.gruppe_list.setCurrentRow(i)
                break
        
        logger.info(f"✅ Gruppe '{name}' hinzugefügt")
    
    def _remove_gruppe(self):
        """Entfernt ausgewählte Gruppe"""
        current = self.gruppe_list.currentItem()
        if not current:
            return
        
        gruppe_name = current.text()
        
        # Bestätigung
        felder_count = len(self.data.get(gruppe_name, {}))
        reply = QMessageBox.question(
            self,
            "Gruppe löschen",
            f"Gruppe '{gruppe_name}' mit {felder_count} Feldern wirklich löschen?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            old_data = self.data[gruppe_name].copy()
            del self.data[gruppe_name]
            self._track_change(f"GRUPPE.{gruppe_name}", old_data, None, ChangeType.DELETED)
            
            self._refresh_gruppen_list()
            self.feld_list.clear()
            
            logger.info(f"❌ Gruppe '{gruppe_name}' gelöscht")
    
    # ========================================
    # FELDER-MANAGEMENT
    # ========================================
    
    def _on_feld_selected(self, current, previous):
        """Feld wurde ausgewählt"""
        # Prüfe auf ungespeicherte Änderungen
        if self.feld_dirty:
            reply = QMessageBox.question(
                self,
                "Ungespeicherte Änderungen",
                "Änderungen übernehmen?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Cancel:
                # Wechsel abbrechen - vorheriges Feld wieder auswählen
                if previous:
                    self.feld_list.blockSignals(True)
                    self.feld_list.setCurrentItem(previous)
                    self.feld_list.blockSignals(False)
                return
            elif reply == QMessageBox.Yes:
                self._feld_uebernehmen()
            else:
                self._feld_abbrechen()
        
        if not current:
            return
        
        gruppe_item = self.gruppe_list.currentItem()
        if not gruppe_item:
            return
        
        gruppe_name = gruppe_item.text()
        feld_guid = current.data(Qt.UserRole)
        
        self._refresh_properties_editor(gruppe_name, feld_guid)
    
    def _add_feld(self):
        """Fügt neues Feld zur ausgewählten Gruppe hinzu"""
        import uuid
        
        gruppe_item = self.gruppe_list.currentItem()
        if not gruppe_item:
            QMessageBox.warning(self, "Fehler", "Bitte erst Gruppe auswählen!")
            return
        
        gruppe_name = gruppe_item.text()
        
        # Neue GUID generieren
        neue_guid = str(uuid.uuid4())
        
        # Template holen (mit kopierten Properties falls vorhanden)
        if self.property_clipboard:
            # Mit kopierten Properties
            neues_feld = {prop: self._get_default_value_for_property(prop) for prop in self.property_clipboard}
            neues_feld['name'] = f'NEUES_FELD_{neue_guid[:8].upper()}'
            neues_feld['label'] = 'Neues Feld'
            logger.info(f"  📋 Verwende kopierte Properties: {self.property_clipboard}")
        else:
            # Default-Template
            neues_feld = {
                'name': f'NEUES_FELD_{neue_guid[:8].upper()}',
                'label': 'Neues Feld',
                'type': 'string',
                'show': True,
                'display_order': 999
            }
        
        # Feld hinzufügen
        self.data[gruppe_name][neue_guid] = neues_feld
        self._track_change(f"{gruppe_name}.{neue_guid}", None, neues_feld, ChangeType.ADDED)
        
        # UI aktualisieren
        self._refresh_felder_list(gruppe_name)
        
        # Neues Feld auswählen
        for i in range(self.feld_list.count()):
            if self.feld_list.item(i).data(Qt.UserRole) == neue_guid:
                self.feld_list.setCurrentRow(i)
                break
        
        logger.info(f"✅ Feld '{neue_guid}' zu Gruppe '{gruppe_name}' hinzugefügt")
    
    def _remove_feld(self):
        """Entfernt ausgewähltes Feld"""
        gruppe_item = self.gruppe_list.currentItem()
        feld_item = self.feld_list.currentItem()
        
        if not gruppe_item or not feld_item:
            return
        
        gruppe_name = gruppe_item.text()
        feld_guid = feld_item.data(Qt.UserRole)
        feld_name = feld_item.text()
        
        # Bestätigung
        reply = QMessageBox.question(
            self,
            "Feld löschen",
            f"Feld '{feld_name}' wirklich löschen?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            old_data = self.data[gruppe_name][feld_guid].copy()
            del self.data[gruppe_name][feld_guid]
            self._track_change(f"{gruppe_name}.{feld_guid}", old_data, None, ChangeType.DELETED)
            
            self._refresh_felder_list(gruppe_name)
            
            logger.info(f"❌ Feld '{feld_guid}' gelöscht")
    
    def _move_feld_up(self):
        """Verschiebt Feld nach oben"""
        self._move_feld(-1)
    
    def _move_feld_down(self):
        """Verschiebt Feld nach unten"""
        self._move_feld(1)
    
    def _move_feld(self, direction: int):
        """
        Verschiebt Feld in Reihenfolge
        
        Args:
            direction: -1 für hoch, +1 für runter
        """
        # WICHTIG: Dirty-Flag NICHT prüfen - Sortierung soll immer funktionieren!
        # Falls dirty, automatisch übernehmen
        if self.feld_dirty:
            self._feld_uebernehmen()
        
        gruppe_item = self.gruppe_list.currentItem()
        feld_item = self.feld_list.currentItem()
        
        if not gruppe_item or not feld_item:
            return
        
        gruppe_name = gruppe_item.text()
        current_row = self.feld_list.currentRow()
        target_row = current_row + direction
        
        # Grenzen prüfen
        if target_row < 0 or target_row >= self.feld_list.count():
            return
        
        # GUIDs der beiden Felder
        current_guid = feld_item.data(Qt.UserRole)
        target_guid = self.feld_list.item(target_row).data(Qt.UserRole)
        
        # display_order tauschen
        current_order = self.data[gruppe_name][current_guid].get('display_order', 999)
        target_order = self.data[gruppe_name][target_guid].get('display_order', 999)
        
        self.data[gruppe_name][current_guid]['display_order'] = target_order
        self.data[gruppe_name][target_guid]['display_order'] = current_order
        
        self._track_change(
            f"{gruppe_name}.{current_guid}.display_order",
            current_order,
            target_order
        )
        
        # UI aktualisieren (blockiert Signals, um Dirty-Flag-Prüfung zu vermeiden)
        self.feld_list.blockSignals(True)
        self._refresh_felder_list(gruppe_name)
        self.feld_list.blockSignals(False)
        
        # Neues Item auswählen (ohne Signal-Trigger)
        self.feld_list.blockSignals(True)
        self.feld_list.setCurrentRow(target_row)
        self.feld_list.blockSignals(False)
        
        # Properties-Editor manuell neu laden (da Signals blockiert waren)
        self._refresh_properties_editor(gruppe_name, current_guid)
    
    # ========================================
    # PROPERTY-MANAGEMENT
    # ========================================
    
    def _copy_properties(self):
        """Kopiert Properties des aktuellen Feldes für neue Felder"""
        gruppe_item = self.gruppe_list.currentItem()
        feld_item = self.feld_list.currentItem()
        
        if not gruppe_item or not feld_item:
            QMessageBox.warning(self, "Fehler", "Bitte Feld auswählen!")
            return
        
        gruppe_name = gruppe_item.text()
        feld_guid = feld_item.data(Qt.UserRole)
        
        # Properties kopieren (außer configs)
        feld_data = self.data[gruppe_name][feld_guid]
        self.property_clipboard = [k for k in feld_data.keys() if k != 'configs']
        
        QMessageBox.information(
            self,
            "Properties kopiert",
            f"{len(self.property_clipboard)} Properties kopiert:\n" + "\n".join(self.property_clipboard)
        )
        
        logger.info(f"📋 {len(self.property_clipboard)} Properties kopiert")
    
    def _add_property(self):
        """Fügt Property zum aktuellen Feld hinzu"""
        gruppe_item = self.gruppe_list.currentItem()
        feld_item = self.feld_list.currentItem()
        
        if not gruppe_item or not feld_item:
            QMessageBox.warning(self, "Fehler", "Bitte Feld auswählen!")
            return
        
        # Property-Auswahl-Dialog
        from PyQt5.QtWidgets import QInputDialog
        
        # Verfügbare Properties aus Template
        available_props = list(self.templates.get('field_properties', {}).keys())
        
        prop_name, ok = QInputDialog.getItem(
            self,
            "Property hinzufügen",
            "Property auswählen:",
            available_props,
            0,
            False
        )
        
        if not ok:
            return
        
        gruppe_name = gruppe_item.text()
        feld_guid = feld_item.data(Qt.UserRole)
        
        # Prüfen ob bereits vorhanden
        if prop_name in self.data[gruppe_name][feld_guid]:
            QMessageBox.warning(self, "Fehler", f"Property '{prop_name}' existiert bereits!")
            return
        
        # Default-Wert setzen
        default_value = self._get_default_value_for_property(prop_name)
        self.data[gruppe_name][feld_guid][prop_name] = default_value
        
        self._track_change(
            f"{gruppe_name}.{feld_guid}.{prop_name}",
            None,
            default_value,
            ChangeType.ADDED
        )
        
        # UI aktualisieren
        self._refresh_properties_editor(gruppe_name, feld_guid)
        
        logger.info(f"✅ Property '{prop_name}' hinzugefügt")
    
    def _remove_property(self):
        """Entfernt Property vom aktuellen Feld"""
        gruppe_item = self.gruppe_list.currentItem()
        feld_item = self.feld_list.currentItem()
        
        if not gruppe_item or not feld_item:
            return
        
        gruppe_name = gruppe_item.text()
        feld_guid = feld_item.data(Qt.UserRole)
        
        # Property-Auswahl
        from PyQt5.QtWidgets import QInputDialog
        
        feld_data = self.data[gruppe_name][feld_guid]
        available_props = [k for k in feld_data.keys() if k != 'configs']
        
        prop_name, ok = QInputDialog.getItem(
            self,
            "Property entfernen",
            "Property auswählen:",
            available_props,
            0,
            False
        )
        
        if not ok:
            return
        
        # Bestätigung
        reply = QMessageBox.question(
            self,
            "Property löschen",
            f"Property '{prop_name}' wirklich löschen?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            old_value = feld_data[prop_name]
            del self.data[gruppe_name][feld_guid][prop_name]
            
            self._track_change(
                f"{gruppe_name}.{feld_guid}.{prop_name}",
                old_value,
                None,
                ChangeType.DELETED
            )
            
            # UI aktualisieren
            self._refresh_properties_editor(gruppe_name, feld_guid)
            
            logger.info(f"❌ Property '{prop_name}' gelöscht")
    
    def _get_default_value_for_property(self, prop_name: str) -> Any:
        """Holt Default-Wert für Property aus Template"""
        template_props = self.templates.get('field_properties', {})
        
        if prop_name in template_props:
            prop_def = template_props[prop_name]
            
            if 'default' in prop_def:
                return prop_def['default']
            
            # Default nach Typ
            prop_type = prop_def.get('type', 'string')
            if prop_type == 'bool':
                return False
            elif prop_type == 'int':
                return 0
            elif prop_type == 'float':
                return 0.0
            elif prop_type == 'choice':
                values = prop_def.get('values', [])
                return values[0] if values else ''
            else:
                return ''
        
        # Fallback
        return ''
    
    # ========================================
    # CONFIG-MANAGEMENT
    # ========================================
    
    def _add_config(self):
        """Fügt Config zum aktuellen Feld hinzu"""
        gruppe_item = self.gruppe_list.currentItem()
        feld_item = self.feld_list.currentItem()
        
        if not gruppe_item or not feld_item:
            QMessageBox.warning(self, "Fehler", "Bitte Feld auswählen!")
            return
        
        # Config-Typ auswählen
        from PyQt5.QtWidgets import QInputDialog
        
        config_types = list(self.templates.get('config_types', {}).keys())
        
        config_type, ok = QInputDialog.getItem(
            self,
            "Config hinzufügen",
            "Config-Typ auswählen:",
            config_types,
            0,
            False
        )
        
        if not ok:
            return
        
        gruppe_name = gruppe_item.text()
        feld_guid = feld_item.data(Qt.UserRole)
        
        # Configs-Dict initialisieren falls nicht vorhanden
        if 'configs' not in self.data[gruppe_name][feld_guid]:
            self.data[gruppe_name][feld_guid]['configs'] = {}
        
        # Prüfen ob bereits vorhanden
        if config_type in self.data[gruppe_name][feld_guid]['configs']:
            QMessageBox.warning(self, "Fehler", f"Config '{config_type}' existiert bereits!")
            return
        
        # Config-Template holen
        config_template = self.templates['config_types'][config_type]
        new_config = {k: '' for k in config_template.keys()}
        
        self.data[gruppe_name][feld_guid]['configs'][config_type] = new_config
        
        self._track_change(
            f"{gruppe_name}.{feld_guid}.configs.{config_type}",
            None,
            new_config,
            ChangeType.ADDED
        )
        
        # UI aktualisieren
        self._refresh_properties_editor(gruppe_name, feld_guid)
        
        logger.info(f"✅ Config '{config_type}' hinzugefügt")
    
    def _remove_config(self):
        """Entfernt Config vom aktuellen Feld"""
        gruppe_item = self.gruppe_list.currentItem()
        feld_item = self.feld_list.currentItem()
        
        if not gruppe_item or not feld_item:
            return
        
        gruppe_name = gruppe_item.text()
        feld_guid = feld_item.data(Qt.UserRole)
        
        # Configs holen
        feld_data = self.data[gruppe_name][feld_guid]
        if 'configs' not in feld_data or not feld_data['configs']:
            QMessageBox.warning(self, "Fehler", "Keine Configs vorhanden!")
            return
        
        # Config auswählen
        from PyQt5.QtWidgets import QInputDialog
        
        available_configs = list(feld_data['configs'].keys())
        
        config_name, ok = QInputDialog.getItem(
            self,
            "Config entfernen",
            "Config auswählen:",
            available_configs,
            0,
            False
        )
        
        if not ok:
            return
        
        # Bestätigung
        reply = QMessageBox.question(
            self,
            "Config löschen",
            f"Config '{config_name}' wirklich löschen?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            old_config = feld_data['configs'][config_name].copy()
            del self.data[gruppe_name][feld_guid]['configs'][config_name]
            
            self._track_change(
                f"{gruppe_name}.{feld_guid}.configs.{config_name}",
                old_config,
                None,
                ChangeType.DELETED
            )
            
            # UI aktualisieren
            self._refresh_properties_editor(gruppe_name, feld_guid)
            
            logger.info(f"❌ Config '{config_name}' gelöscht")
    
    # ========================================
    # CHANGE-TRACKING
    # ========================================
    
    def _track_change(self, path: str, old_value: Any, new_value: Any, change_type: str = ChangeType.MODIFIED):
        """
        Tracked Änderung für Undo/Redo
        
        Args:
            path: Pfad zur Änderung (z.B. 'PERSONDATEN.guid.name')
            old_value: Alter Wert
            new_value: Neuer Wert
            change_type: Art der Änderung
        """
        # Keine Änderung wenn Werte gleich
        if old_value == new_value and change_type == ChangeType.MODIFIED:
            return
        
        # Stack kürzen falls wir mitten drin sind
        if self.stack_index < len(self.changes_stack) - 1:
            self.changes_stack = self.changes_stack[:self.stack_index + 1]
        
        # Änderung hinzufügen
        self.changes_stack.append((change_type, path, old_value, new_value))
        self.stack_index += 1
        
        # Buttons aktualisieren
        self._update_undo_redo_buttons()
        
        logger.debug(f"📝 Change tracked: {change_type} @ {path}")
    
    def _update_undo_redo_buttons(self):
        """Aktualisiert Undo/Redo Button States"""
        self.undo_btn.setEnabled(self.stack_index >= 0)
        self.redo_btn.setEnabled(self.stack_index < len(self.changes_stack) - 1)
    
    def _undo(self):
        """Macht letzte Änderung rückgängig"""
        if self.stack_index < 0:
            return
        
        change_type, path, old_value, new_value = self.changes_stack[self.stack_index]
        
        # Änderung rückgängig machen
        self._apply_change_reverse(change_type, path, old_value, new_value)
        
        self.stack_index -= 1
        self._update_undo_redo_buttons()
        
        # UI aktualisieren
        self._refresh_all_ui()
        
        logger.info(f"↶ Undo: {path}")
    
    def _redo(self):
        """Wiederholt rückgängig gemachte Änderung"""
        if self.stack_index >= len(self.changes_stack) - 1:
            return
        
        self.stack_index += 1
        change_type, path, old_value, new_value = self.changes_stack[self.stack_index]
        
        # Änderung erneut anwenden
        self._apply_change_forward(change_type, path, old_value, new_value)
        
        self._update_undo_redo_buttons()
        
        # UI aktualisieren
        self._refresh_all_ui()
        
        logger.info(f"↷ Redo: {path}")
    
    def _apply_change_reverse(self, change_type: str, path: str, old_value: Any, new_value: Any):
        """Wendet Änderung rückwärts an (für Undo)"""
        # TODO: Implementieren
        pass
    
    def _apply_change_forward(self, change_type: str, path: str, old_value: Any, new_value: Any):
        """Wendet Änderung vorwärts an (für Redo)"""
        # TODO: Implementieren
        pass
    
    def _is_gruppe_changed(self, gruppe_name: str) -> bool:
        """Prüft ob Gruppe geändert wurde"""
        if gruppe_name not in self.original_data:
            return True  # Neue Gruppe
        return self.data.get(gruppe_name) != self.original_data.get(gruppe_name)
    
    def _is_gruppe_new(self, gruppe_name: str) -> bool:
        """Prüft ob Gruppe neu ist"""
        return gruppe_name not in self.original_data
    
    def _is_feld_changed(self, gruppe_name: str, feld_guid: str) -> bool:
        """Prüft ob Feld geändert wurde"""
        if gruppe_name not in self.original_data:
            return True
        if feld_guid not in self.original_data[gruppe_name]:
            return True
        return (self.data[gruppe_name][feld_guid] != 
                self.original_data[gruppe_name][feld_guid])
    
    def _is_feld_new(self, gruppe_name: str, feld_guid: str) -> bool:
        """Prüft ob Feld neu ist"""
        if gruppe_name not in self.original_data:
            return True
        return feld_guid not in self.original_data.get(gruppe_name, {})
    
    def _refresh_all_ui(self):
        """Aktualisiert alle UI-Elemente"""
        self._refresh_gruppen_list()
        
        gruppe_item = self.gruppe_list.currentItem()
        if gruppe_item:
            self._refresh_felder_list(gruppe_item.text())
            
            feld_item = self.feld_list.currentItem()
            if feld_item:
                self._refresh_properties_editor(
                    gruppe_item.text(),
                    feld_item.data(Qt.UserRole)
                )
    
    # ========================================
    # SAVE/DISCARD
    # ========================================
    
    def _show_changes(self):
        """Zeigt Dialog mit allen Änderungen"""
        # TODO: Diff-Dialog implementieren
        changes_count = len([c for c in self.changes_stack[:self.stack_index + 1]])
        QMessageBox.information(
            self,
            "Änderungen",
            f"{changes_count} Änderungen im Stack"
        )
    
    def _discard_changes(self):
        """Verwirft alle Änderungen"""
        reply = QMessageBox.question(
            self,
            "Änderungen verwerfen",
            "Wirklich alle Änderungen verwerfen?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Daten neu laden
            self._load_data()
            
            # Stack leeren
            self.changes_stack.clear()
            self.stack_index = -1
            self._update_undo_redo_buttons()
            
            # UI aktualisieren
            self._refresh_all_ui()
            
            logger.info("❌ Alle Änderungen verworfen")
    
    def _save_changes(self):
        """Speichert alle Änderungen"""
        # Validierung
        if not self._validate_data():
            return
        
        try:
            # Daten in Datenbank schreiben
            for gruppe_name, gruppe_data in self.data.items():
                self.db.data[gruppe_name] = gruppe_data
            
            # Speichern
            self.db.save_all_values()
            
            # Original-Daten aktualisieren (für Farb-Markierungen)
            self.original_data = json.loads(json.dumps(self.data))
            
            # Stack leeren
            self.changes_stack.clear()
            self.stack_index = -1
            self._update_undo_redo_buttons()
            
            # Aktuelle Auswahl merken
            current_gruppe = None
            current_feld = None
            gruppe_item = self.gruppe_list.currentItem()
            if gruppe_item:
                current_gruppe = gruppe_item.text()
                feld_item = self.feld_list.currentItem()
                if feld_item:
                    current_feld = feld_item.data(Qt.UserRole)
            
            # UI komplett neu aufbauen (damit Farben verschwinden)
            self._refresh_gruppen_list()
            
            # Auswahl wiederherstellen
            if current_gruppe:
                for i in range(self.gruppe_list.count()):
                    if self.gruppe_list.item(i).text() == current_gruppe:
                        self.gruppe_list.setCurrentRow(i)
                        self._refresh_felder_list(current_gruppe)
                        
                        if current_feld:
                            for j in range(self.feld_list.count()):
                                if self.feld_list.item(j).data(Qt.UserRole) == current_feld:
                                    self.feld_list.setCurrentRow(j)
                                    self._refresh_properties_editor(current_gruppe, current_feld)
                                    break
                        break
            
            # Erfolgsmeldung NACH UI-Update
            QMessageBox.information(self, "Erfolg", "✅ Änderungen erfolgreich gespeichert!")
            logger.info("💾 Änderungen gespeichert")
            
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Speichern fehlgeschlagen:\n{e}")
            logger.error(f"❌ Speichern fehlgeschlagen: {e}")
    
    def _validate_data(self) -> bool:
        """Validiert Daten vor Save"""
        # ROOT.TABLE muss existieren
        if 'TABLE' not in self.data.get('ROOT', {}):
            QMessageBox.warning(self, "Validierung", "ROOT.TABLE fehlt!")
            return False
        
        # Alle Felder müssen 'name' haben
        for gruppe_name, gruppe_data in self.data.items():
            if gruppe_name in ['ROOT', 'TEMPLATES']:
                continue
            
            for feld_guid, feld_data in gruppe_data.items():
                if 'name' not in feld_data or not feld_data['name']:
                    QMessageBox.warning(
                        self,
                        "Validierung",
                        f"Feld {feld_guid[:8]} in Gruppe '{gruppe_name}' hat kein 'name'!"
                    )
                    return False
        
        return True
    
    # ========================================
    # KOMPATIBILITÄT MIT GENERELLEM DIALOG
    # ========================================
    
    def get_widget(self):
        """
        Gibt Widget für Integration in generellen Dialog zurück
        
        Returns:
            self (QDialog kann als Widget verwendet werden)
        """
        return self
    
    def closeEvent(self, event):
        """Prüft beim Schließen auf ungespeicherte Änderungen"""
        if self.feld_dirty:
            reply = QMessageBox.question(
                self,
                "Ungespeicherte Änderungen",
                "Änderungen im Feld-Editor übernehmen?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Cancel:
                event.ignore()
                return
            elif reply == QMessageBox.Yes:
                self._feld_uebernehmen()
        
        # Prüfe auf ungespeicherte Änderungen im Gesamt-Editor
        if self.changes_stack:
            reply = QMessageBox.question(
                self,
                "Ungespeicherte Änderungen",
                f"{len(self.changes_stack)} Änderungen nicht gespeichert!\nTrotzdem schließen?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        event.accept()


# ========================================
# STANDALONE-TEST
# ========================================

if __name__ == "__main__":
    # Logging konfigurieren
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    app = QApplication(sys.argv)
    
    # Test-Dialog öffnen
    dialog = PdvmSystemEditor(
        table_name='sys_framedaten',
        record_uid='55555555-5555-5555-5555-555555555555'
    )
    dialog.show()
    
    sys.exit(app.exec_())
