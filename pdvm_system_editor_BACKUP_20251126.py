"""
PDVM System-Editor - UNIVERSELLER Editor für beliebige Tabellen

ARCHITEKTUR V3 (EINFACH & LINEAR):
- Tab 1: ROOT-Felder (TABLE, NO_DATA, etc.)
- Tab 2: Gruppen & Felder (Split-View mit Gruppenliste + Feld-Editor)

DATENFLUSS (LINEAR):
    1. Dialog startet mit frame_guid
    2. Dialog liest framedaten.ROOT.TABLE (z.B. "sys_viewdaten")
    3. Dialog startet Editor mit table_name=TABLE
    4. Editor lädt Datensatz aus dieser Tabelle
    5. Struktur ist flach: ROOT + Gruppen direkt (keine METADATEN-Verschachtelung)

NEUE STRUKTUR:
    {
        "ROOT": {"TABLE": "sys_viewdaten", ...},
        "PERSONDATEN": {"guid-1": {...}, "guid-2": {...}},  # Gruppe → Felder
        "TEMPLATES": {"text": {...}, "dropdown": {...}}
    }
    
    editor = PdvmSystemEditor(
        frame_guid='44d2e239-d429-41ab-b080-e7fcd4b6e8a8',
        table_name='persondaten'  # ROOT_TABLE aus framedaten
    )
    
    # Editor arbeitet in EINER Tabelle mit EINEM Datensatz:
    # - edit_db = PdvmCentralDatenbank('sys_viewdaten', '794cbfc3...')
    # - template_db = PdvmCentralDatenbank('sys_viewdaten', '55555...')
    # - Lineare Struktur: ROOT + direkte Gruppen (PERSONDATEN, TEMPLATES, etc.)
"""

import logging
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QLineEdit, QCheckBox, QPushButton, QListWidget, QListWidgetItem,
    QSplitter, QScrollArea, QFormLayout, QComboBox, QSpinBox,
    QGroupBox, QMessageBox, QInputDialog, QTreeWidget, QTreeWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from pdvm_central_systemsteuerung import get_gcs
from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)


class FieldTreeWidget(QTreeWidget):
    """Custom TreeWidget mit Drag & Drop nur innerhalb gleicher Ebene"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.reorder_callback = None
        # Wichtig: Nur auf Items droppen, nicht zwischen sie
        self.setDropIndicatorShown(True)
    
    def dropEvent(self, event):
        """Override: Prüft ob Drop innerhalb gleicher Ebene"""
        # Aktuelles Item (das gezogen wird)
        dragged_item = self.currentItem()
        if not dragged_item:
            event.ignore()
            return
        
        # Ziel-Item (wohin gezogen wird)
        drop_item = self.itemAt(event.pos())
        if not drop_item:
            event.ignore()
            return
        
        # Eltern-Item des gezogenen Items
        dragged_parent = dragged_item.parent()
        
        # REGEL 1: Nur Control-Items dürfen bewegt werden (keine Ordner)
        if dragged_parent is None:
            event.ignore()
            return
        
        # REGEL 2: Ziel-Item muss auch ein Control sein (gleiche Ebene)
        drop_parent = drop_item.parent()
        
        # Ziel darf NICHT der Ordner selbst sein
        if drop_parent is None:
            event.ignore()
            return
        
        # Ziel muss im GLEICHEN Ordner sein
        if drop_parent != dragged_parent:
            event.ignore()
            return
        
        # REGEL 3: Drop-Indicator Position prüfen
        drop_indicator = self.dropIndicatorPosition()
        
        # Nur erlaubt: OnItem, AboveItem, BelowItem innerhalb gleicher Ebene
        # Nicht erlaubt: OnViewport oder auf andere Ebenen
        if drop_indicator == QTreeWidget.OnViewport:
            event.ignore()
            return
        
        # Drop erlaubt - Standard-Verhalten ausführen
        super().dropEvent(event)
        
        # Callback aufrufen falls gesetzt
        if self.reorder_callback:
            self.reorder_callback()


class PdvmSystemEditor(QWidget):
    """
    Universeller System-Editor für alle System-Tabellen
    
    Signals:
        save_completed: Emittiert nach erfolgreichem Speichern
        refresh_requested: Emittiert wenn Ansicht neu geladen werden soll
    """
    
    save_completed = pyqtSignal()
    refresh_requested = pyqtSignal()
    
    def __init__(self, frame_guid, table_name, parent=None):
        """
        Initialisierung System-Editor - EINFACH & LINEAR
        
        Args:
            frame_guid: Frame-GUID aus Dialog-Aufruf (für LAST_SELECTION)
            table_name: ROOT_TABLE aus framedaten (z.B. 'persondaten', 'sys_viewdaten')
            parent: Parent-Widget (optional)
            
        EINFACH:
            1. Dialog gibt ROOT_TABLE an Editor (z.B. "persondaten")
            2. Editor lädt Datensatz aus dieser Tabelle
            3. Datensatz hat eigene ROOT.ROOT_TABLE für METADATEN-Struktur
        """
        super().__init__(parent)
        
        # ✅ Basis-Parameter
        self.frame_guid = frame_guid
        self.table_name = table_name  # ✅ ROOT_TABLE aus Dialog (z.B. "persondaten")
        
        # GCS holen
        self.gcs = get_gcs()
        if not self.gcs:
            raise RuntimeError("❌ GCS nicht initialisiert!")
        
        # ✅ SCHRITT 1: LAST_SELECTION holen
        last_guid, _ = self.gcs._db.get_value(frame_guid, 'LAST_SELECTION')
        
        # ✅ SCHRITT 2: Datensatz laden
        if last_guid:
            self.edit_db = PdvmCentralDatenbank(table_name, last_guid)
            self.edit_mode = 'template' if last_guid == '55555555-5555-5555-5555-555555555555' else 'data'
            logger.info(f"📄 Lade Datensatz: {last_guid}")
        else:
            self.edit_db = PdvmCentralDatenbank(table_name, None)
            self.edit_mode = 'data'
            logger.info(f"📄 Kein Datensatz - Editor leer")
        
        # ✅ SCHRITT 3: Template laden (aus gleicher Tabelle)
        self.template_db = PdvmCentralDatenbank(table_name, '55555555-5555-5555-5555-555555555555')
        
        logger.info(f"🔧 Editor initialisiert")
        logger.info(f"  📂 Tabelle: {table_name}")
        logger.info(f"  🖼️ Frame: {frame_guid}")
        logger.info(f"  🎯 Modus: {self.edit_mode.upper()}")
        logger.info(f"  📋 GUID: {self.edit_db.guid or 'KEINE'}")
        
        # Daten laden
        self._load_data()
        self._load_templates()
        
        # UI aufbauen
        self._setup_ui()
        
    def _load_data(self):
        """
        Lädt Daten aus edit_db + initialisiert METADATEN-Struktur via Pfade
        
        KRITISCH: Arbeitet NUR mit edit_db - keine Daten aus anderen Quellen!
        """
        # ✅ ALLES aus edit_db - eine Tabelle, ein Datensatz!
        self.data = self.edit_db.data
        
        # Struktur validieren
        if 'ROOT' not in self.data:
            self.data['ROOT'] = {}
        
        # ✅ LINEARE STRUKTUR: Keine METADATEN-Verschachtelung mehr
        # Gruppen sind direkt im data-Dict: ROOT, PERSONDATEN, TEMPLATES, etc.
        logger.info(f"  ✅ Daten geladen: {len(self.data)} Gruppen")
        logger.info(f"  📂 Verfügbare Gruppen: {list(self.data.keys())}")
    
    def _get_table_name(self):
        """Gibt TABLE aus ROOT zurück (einheitlich für alle Systemtabellen)"""
        return self.data.get('ROOT', {}).get('TABLE', '')
    
    def _get_all_gruppen(self):
        """Gibt alle Gruppen außer ROOT zurück"""
        return [key for key in self.data.keys() if key != 'ROOT']
    
    def _get_gruppe_felder(self, gruppe_name):
        """Gibt alle Felder einer Gruppe zurück"""
        return self.data.get(gruppe_name, {})
    
    def _set_gruppe_felder(self, gruppe_name, felder):
        """Setzt alle Felder einer Gruppe"""
        self.data[gruppe_name] = felder
    
    def _ensure_gruppe_exists(self, gruppe_name):
        """Stellt sicher dass Gruppe existiert"""
        if gruppe_name not in self.data:
            self.data[gruppe_name] = {}
            logger.info(f"  ✅ Gruppe erstellt: {gruppe_name}")
    
    def _add_feld_to_gruppe(self, gruppe_name, feld_guid, feld_data):
        """Fügt ein Feld zu einer Gruppe hinzu"""
        self._ensure_gruppe_exists(gruppe_name)
        self.data[gruppe_name][feld_guid] = feld_data
        logger.info(f"  ✅ Feld hinzugefügt: {gruppe_name}.{feld_guid}")
    
    def _remove_feld_from_gruppe(self, gruppe_name, feld_guid):
        """Entfernt ein Feld aus einer Gruppe"""
        if gruppe_name in self.data and feld_guid in self.data[gruppe_name]:
            del self.data[gruppe_name][feld_guid]
            logger.info(f"  ✅ Feld entfernt: {gruppe_name}.{feld_guid}")
    
    def _LEGACY_navigate_path(self, pfad):
        """
        LEGACY-Funktion für alte METADATEN-Struktur
        Wird durch direkte Gruppen-Zugriffe ersetzt
        """
        if not pfad:
            return {}
        
        # Pfad in Teile zerlegen
        parts = pfad.split('.')
        
        # Navigation durch METADATEN
        current = self.data.get('METADATEN', {})
        
        for part in parts:
            if not isinstance(current, dict):
                logger.warning(f"  ⚠️ Pfad ungültig bei '{part}': Erwartet Dict")
                return {}
            
            if part not in current:
                logger.warning(f"  ⚠️ Pfad-Teil '{part}' nicht gefunden")
                return {}
            
            current = current[part]
        
        # Ergebnis sollte Dict sein (mit Controls)
        if not isinstance(current, dict):
            logger.warning(f"  ⚠️ Pfad-Ziel ist kein Dict: {type(current)}")
            return {}
        
        return current
    
    def _set_feld_property(self, gruppe_name, feld_guid, property_key, value):
        """
        Setzt Feld-Property in Gruppe (lineare Struktur)
        
        Args:
            gruppe_name: Name der Gruppe (z.B. "PERSONDATEN", "TEMPLATES")
            feld_guid: GUID des Feldes
            property_key: Property-Name (z.B. 'label', 'tooltip')
            value: Neuer Wert
        """
        if gruppe_name in self.data and feld_guid in self.data[gruppe_name]:
            self.data[gruppe_name][feld_guid][property_key] = value
            logger.info(f"  ✅ Gespeichert: {gruppe_name}.{feld_guid}.{property_key} = {value}")
    
    def set_guid(self, new_guid):
        """
        Setzt neue GUID und lädt Daten neu (bei Doppelklick in View)
        
        Args:
            new_guid: Neue GUID des zu bearbeitenden Datensatzes
        """
        logger.info(f"🔄 Lade neuen Datensatz: {new_guid}")
        
        # GUID in edit_db setzen
        self.edit_db.set_guid(new_guid)
        
        # Modus aktualisieren
        self.edit_mode = 'template' if new_guid == '55555555-5555-5555-5555-555555555555' else 'data'
        
        # Daten neu laden
        self._load_data()
        
        # UI aktualisieren
        self._refresh_field_list()
        self._update_mode_info_label()
        
        # LAST_SELECTION speichern
        self.gcs._db.set_value(self.frame_guid, 'LAST_SELECTION', new_guid)
        self.gcs._db.save_all_values()
        
        logger.info(f"  ✅ Datensatz gewechselt: {new_guid}")
        
    def _load_templates(self):
        """Lädt Control-Templates UND Control-Properties aus Template-DB (lineare Struktur)"""
        logger.info(f"📂 Hole Templates (lineare Struktur)")
        
        # ✅ NEUE LINEARE STRUKTUR: Direkte Gruppen statt METADATEN
        # Daten sind bereits geladen (Constructor mit template_guid)
        
        # ROOT_CONTROLS aus Template laden (direkte Gruppe)
        self.root_controls = self.template_db.data.get('ROOT_CONTROLS', {})
        
        # Templates für neue Controls (direkte Gruppe)
        self.templates = self.template_db.data.get('TEMPLATES', {})
        
        # Control-Properties für Editor (direkte Gruppe)
        self.control_properties = self.template_db.data.get('CONTROL_PROPERTIES', {})
        
        logger.info(f"  ✅ {len(self.root_controls)} ROOT-Controls aus Template geladen")
        logger.info(f"  ✅ {len(self.templates)} Templates geladen: {list(self.templates.keys())}")
        logger.info(f"  ✅ {len(self.control_properties)} Control-Properties geladen")
    
    def _get_template_for_gruppe(self, gruppe_name: str) -> dict:
        """
        Holt Template für eine Gruppe (aus TEMPLATES oder Default)
        
        Args:
            gruppe_name: Name der Gruppe (z.B. 'PERSONDATEN', 'FINANZDATEN')
            
        Returns:
            Template-Dictionary mit Feldern für neues Feld
        """
        # Versuche Template aus TEMPLATES Gruppe zu holen
        if 'TEMPLATES' in self.data:
            templates_gruppe = self.data['TEMPLATES']
            
            # Tabellen-spezifisches Template (z.B. 'persondaten', 'sys_menudaten')
            table_key = self.table_name.lower()
            if table_key in templates_gruppe:
                logger.info(f"  📋 Verwende Template '{table_key}' aus TEMPLATES")
                return templates_gruppe[table_key].copy()
            
            # Fallback: Erstes Template aus TEMPLATES
            if templates_gruppe:
                first_template_key = list(templates_gruppe.keys())[0]
                logger.info(f"  📋 Verwende Fallback-Template '{first_template_key}' aus TEMPLATES")
                return templates_gruppe[first_template_key].copy()
        
        # Default-Template wenn kein Template gefunden
        logger.warning(f"  ⚠️ Kein Template gefunden - verwende Default-Template")
        return {
            'label': 'Neues Feld',
            'feld': 'NEUES_FELD',
            'type': 'string',
            'gruppe': 'SYSTEM',
            'default': '',
            'show': True,
            'display_order': 999,
            'expert_mode': False,
            'searchable': True,
            'sortable': True
        }
    
    def _select_field_in_tree(self, gruppe_name: str, feld_guid: str):
        """
        Wählt ein Feld im Tree aus
        
        Args:
            gruppe_name: Name der Gruppe
            feld_guid: GUID des Feldes
        """
        # Tree durchsuchen
        for i in range(self.field_tree.topLevelItemCount()):
            gruppe_item = self.field_tree.topLevelItem(i)
            item_data = gruppe_item.data(0, Qt.UserRole)
            
            if item_data and item_data.get('gruppe_name') == gruppe_name:
                # Richtige Gruppe gefunden, nun Feld suchen
                for j in range(gruppe_item.childCount()):
                    feld_item = gruppe_item.child(j)
                    feld_data = feld_item.data(0, Qt.UserRole)
                    
                    if feld_data and feld_data.get('feld_guid') == feld_guid:
                        # Feld gefunden → auswählen
                        self.field_tree.setCurrentItem(feld_item)
                        gruppe_item.setExpanded(True)
                        logger.info(f"  ✅ Feld {feld_guid[:8]} ausgewählt")
                        return
        
        logger.warning(f"  ⚠️ Feld {feld_guid} nicht im Tree gefunden")
        
    def _setup_ui(self):
        """Baut die UI auf"""
        logger.info("🔧 Baue View-Editor UI auf...")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Modus-Auswahl Header
        mode_layout = QHBoxLayout()
        mode_label = QLabel("📋 Modus:")
        mode_label.setFont(QFont("Arial", 10, QFont.Bold))
        mode_layout.addWidget(mode_label)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Normal View", "Template"])
        self.mode_combo.setCurrentIndex(1 if self.edit_mode == 'template' else 0)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self.mode_combo.setEnabled(False)  # Deaktiviert - automatische Erkennung
        mode_layout.addWidget(self.mode_combo)
        
        # Info-Label
        self.mode_info_label = QLabel()
        self.mode_info_label.setStyleSheet("color: #666; font-style: italic;")
        self._update_mode_info_label()
        mode_layout.addWidget(self.mode_info_label)
        
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
        # Tab-Widget erstellen
        self.tabs = QTabWidget()
        
        # Tab 1: ROOT-Felder
        self.tab_root = self._create_root_tab()
        self.tabs.addTab(self.tab_root, "Basis")
        
        # Tab 2: Felder & Controls
        self.tab_fields = self._create_fields_tab()
        self.tabs.addTab(self.tab_fields, "Felder & Controls")
        
        layout.addWidget(self.tabs)
        
        # Speichern-Button
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        self.save_button = QPushButton("💾 Speichern")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 20px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.save_button.clicked.connect(self._save_all)
        save_layout.addWidget(self.save_button)
        
        layout.addLayout(save_layout)
        
        logger.info("✅ View-Editor UI aufgebaut")
        
    def _on_mode_changed(self, index):
        """Handler: Modus geändert"""
        old_mode = self.edit_mode
        self.edit_mode = 'template' if index == 1 else 'view'
        logger.info(f"🔄 Modus gewechselt: {old_mode} → {self.edit_mode}")
        
        # Info-Label aktualisieren
        self._update_mode_info_label()
        
        # Tab 2 neu laden (andere Struktur)
        self._refresh_field_list()
        
    def _update_mode_info_label(self):
        """Aktualisiert das Modus-Info-Label"""
        if self.edit_mode == 'template':
            self.mode_info_label.setText(f"✨ Template-Modus ({self.table_name})")
        else:
            # ✅ Views haben VIEW_NAME, Frames haben HEADER_TEXT oder ROOT_TABLE
            root_data = self.data.get('ROOT', {})
            name = (root_data.get('VIEW_NAME') or 
                   root_data.get('HEADER_TEXT') or 
                   root_data.get('ROOT_TABLE') or 
                   'Unbenannt')
            self.mode_info_label.setText(f"📄 {self.table_name}: {name}")
        
    def get_widget(self):
        """
        Gibt das Widget für Einbettung im Dialog zurück
        
        Returns:
            QWidget: Dieses Widget selbst
        """
        return self
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 20px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.save_button.clicked.connect(self._save_all)
        save_layout.addWidget(self.save_button)
        
        layout.addLayout(save_layout)
        
        logger.info("✅ View-Editor UI aufgebaut")
        
    def _create_root_tab(self):
        """Tab 1: ROOT-Felder bearbeiten mit +/- Buttons"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header mit Buttons
        header_layout = QHBoxLayout()
        header_label = QLabel("📋 Basis-Eigenschaften")
        header_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        add_prop_btn = QPushButton("+ Eigenschaft")
        add_prop_btn.clicked.connect(self._add_root_property)
        header_layout.addWidget(add_prop_btn)
        
        remove_prop_btn = QPushButton("- Eigenschaft")
        remove_prop_btn.clicked.connect(self._remove_root_property)
        header_layout.addWidget(remove_prop_btn)
        
        layout.addLayout(header_layout)
        
        # Scroll-Bereich
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.root_scroll_content = QWidget()
        self.root_form_layout = QFormLayout(self.root_scroll_content)
        
        self.root_widgets = {}
        self._rebuild_root_form()
        
        scroll.setWidget(self.root_scroll_content)
        layout.addWidget(scroll)
        
        return widget
    
    def _rebuild_root_form(self):
        """Baut ROOT-Formular neu auf"""
        # Altes Layout leeren
        while self.root_form_layout.count():
            child = self.root_form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.root_widgets = {}
        
        # Alle Keys sammeln: Template + zusätzliche aus view_data['ROOT']
        all_keys = set(self.root_controls.keys()) | set(self.data.get('ROOT', {}).keys())
        
        # Nach display_order sortieren (Template-Keys zuerst, dann alphabetisch)
        def sort_key(key):
            if key in self.root_controls:
                return (0, self.root_controls[key].get('display_order', 999), key)
            else:
                return (1, 999, key)  # Zusätzliche Keys am Ende
        
        sorted_keys = sorted(all_keys, key=sort_key)
        
        for control_key in sorted_keys:
            # Control-Definition holen (falls im Template)
            control = self.root_controls.get(control_key, {
                'label': control_key,
                'control_type': 'text',
                'readonly': False
            })
            label = control['label']
            control_type = control.get('control_type', 'text')
            # Problem 5: Alle Felder editierbar (außer explizit readonly wie VIEW_GUID)
            readonly = control.get('readonly', False)
            
            # Widget erstellen
            if control_type == 'checkbox':
                widget_input = QCheckBox()
                # Default-Wert aus Template verwenden, falls Feld nicht existiert
                default_value = control.get('default_value', False)
                value = self.data['ROOT'].get(control_key, default_value)
                widget_input.setChecked(bool(value))
                
                # Signal: Änderungen direkt in view_data schreiben
                widget_input.stateChanged.connect(
                    lambda state, key=control_key: self.data['ROOT'].__setitem__(key, bool(state))
                )
                
                # Spezial-Signal für NO_DATA: Struktur generieren
                if control_key == 'NO_DATA':
                    widget_input.stateChanged.connect(self._on_no_data_changed)
            elif control_type == 'combo':
                widget_input = QComboBox()
                widget_input.setEditable(False)
                options = control.get('options', [])
                widget_input.addItems(options)
                # Default-Wert aus Template verwenden
                default_value = control.get('default_value', '')
                value = self.data['ROOT'].get(control_key, default_value)
                index = widget_input.findText(str(value))
                if index >= 0:
                    widget_input.setCurrentIndex(index)
                
                # Signal: Änderungen direkt in view_data schreiben
                widget_input.currentTextChanged.connect(
                    lambda text, key=control_key: self.data['ROOT'].__setitem__(key, text)
                )
            else:
                widget_input = QLineEdit()
                # Default-Wert aus Template verwenden
                default_value = control.get('default_value', '')
                value = self.data['ROOT'].get(control_key, default_value)
                widget_input.setText(str(value))
                widget_input.setReadOnly(readonly)
                
                # Signal: Änderungen direkt in view_data schreiben
                if not readonly:
                    widget_input.textChanged.connect(
                        lambda text, key=control_key: self.data['ROOT'].__setitem__(key, text)
                    )
            
            self.root_widgets[control_key] = widget_input
            self.root_form_layout.addRow(f"{label}:", widget_input)
    
    def _add_root_property(self):
        """Fügt neue ROOT-Eigenschaft hinzu"""
        from PyQt5.QtWidgets import QInputDialog, QMessageBox
        
        # Key abfragen
        key, ok = QInputDialog.getText(
            self,
            "Neue Eigenschaft",
            "Eigenschafts-Name (z.B. 'CUSTOM_FIELD'):"
        )
        
        if not ok or not key.strip():
            return
        
        key = key.strip().upper()
        
        if key in self.data['ROOT']:
            QMessageBox.warning(self, "Warnung", f"Eigenschaft '{key}' existiert bereits!")
            return
        
        # Wert abfragen
        value, ok = QInputDialog.getText(
            self,
            "Wert",
            f"Wert für '{key}':"
        )
        
        if not ok:
            value = ''
        
        # In view_data eintragen
        self.data['ROOT'][key] = value
        
        # Formular neu aufbauen (zeigt neue Eigenschaft an)
        self._rebuild_root_form()
        
        logger.info(f"✅ ROOT-Eigenschaft '{key}' hinzugefügt")
    
    def _remove_root_property(self):
        """Entfernt ROOT-Eigenschaft"""
        from PyQt5.QtWidgets import QInputDialog, QMessageBox
        
        if not self.data['ROOT']:
            QMessageBox.warning(self, "Warnung", "Keine Eigenschaften vorhanden!")
            return
        
        # Liste aller Keys
        keys = list(self.data['ROOT'].keys())
        
        key, ok = QInputDialog.getItem(
            self,
            "Eigenschaft löschen",
            "Eigenschaft wählen:",
            keys,
            0,
            False
        )
        
        if not ok:
            return
        
        # Bestätigung
        reply = QMessageBox.question(
            self,
            "Löschen bestätigen",
            f"Eigenschaft '{key}' wirklich löschen?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Löschen
        del self.data['ROOT'][key]
        
        # Formular neu aufbauen
        self._rebuild_root_form()
        
        logger.info(f"🗑️ ROOT-Eigenschaft '{key}' gelöscht")
        
    def _create_fields_tab(self):
        """Tab 2: Felder & Controls (Split-View)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Splitter: Links Feldliste, Rechts Control-Editor
        splitter = QSplitter(Qt.Horizontal)
        
        # === LINKE SEITE: Feldliste ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Header
        left_header = QLabel("📋 Feld-Hierarchie")
        left_header.setFont(QFont("Arial", 12, QFont.Bold))
        left_layout.addWidget(left_header)
        
        # Custom TreeWidget mit Drag & Drop Validierung
        self.field_tree = FieldTreeWidget()
        self.field_tree.setHeaderHidden(True)
        self.field_tree.setDragDropMode(QTreeWidget.InternalMove)
        self.field_tree.itemClicked.connect(self._on_tree_item_clicked)
        # Callback für Reorder-Event setzen
        self.field_tree.reorder_callback = self._on_items_reordered
        left_layout.addWidget(self.field_tree)
        
        # Buttons für Felder
        field_button_layout = QHBoxLayout()
        
        self.add_field_button = QPushButton("+ Feld")
        self.add_field_button.clicked.connect(self._add_field)
        field_button_layout.addWidget(self.add_field_button)
        
        self.remove_field_button = QPushButton("- Feld")
        self.remove_field_button.clicked.connect(self._remove_field)
        field_button_layout.addWidget(self.remove_field_button)
        
        left_layout.addLayout(field_button_layout)
        
        splitter.addWidget(left_widget)
        
        # === RECHTE SEITE: Control-Editor ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Header
        self.right_header = QLabel("Wähle ein Feld aus")
        self.right_header.setFont(QFont("Arial", 12, QFont.Bold))
        right_layout.addWidget(self.right_header)
        
        # Control-Editor (wird dynamisch befüllt)
        self.control_editor_scroll = QScrollArea()
        self.control_editor_scroll.setWidgetResizable(True)
        self.control_editor_content = QWidget()
        self.control_editor_layout = QVBoxLayout(self.control_editor_content)
        self.control_editor_scroll.setWidget(self.control_editor_content)
        right_layout.addWidget(self.control_editor_scroll)
        
        splitter.addWidget(right_widget)
        
        # Splitter-Verhältnis: 1:2
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # Feldliste initialisieren
        self._refresh_field_list()
        
        return widget
        
    def _refresh_field_list(self):
        """Aktualisiert TreeView mit hierarchischer Struktur via Pfad-System"""
        self.field_tree.clear()
        
        # ✅ NEUE LINEARE STRUKTUR: Alle Gruppen außer ROOT zeigen
        gruppen = self._get_all_gruppen()
        
        if not gruppen:
            item = QTreeWidgetItem(["Keine Gruppen vorhanden (nur ROOT)"])
            item.setFlags(Qt.NoItemFlags)
            self.field_tree.addTopLevelItem(item)
            return
        
        logger.info(f"📂 Lade {len(gruppen)} Gruppen: {gruppen}")
        
        # Durchlaufe alle Gruppen (außer ROOT)
        for gruppe_name in sorted(gruppen):
            # Felder dieser Gruppe holen
            felder_dict = self._get_gruppe_felder(gruppe_name)
            
            logger.info(f"📂 Gruppe '{gruppe_name}': {len(felder_dict)} Felder")
            
            # Icon basierend auf Gruppenname
            icon = {
                'TEMPLATES': '🔧',
                'ROOT_CONTROLS': '⚙️', 
                'CONTROL_PROPERTIES': '🎨',
                'PERSONDATEN': '👤',
                'FINANZDATEN': '💰',
                'SYS_MENUDATEN': '📋',
                'DE-DE': '🇩🇪',
                'US-EN': '🇺🇸',
                'FR-FR': '🇫🇷'
            }.get(gruppe_name, '📁')
            
            # Parent-Item für diese Gruppe
            parent_item = QTreeWidgetItem([f"{icon} {gruppe_name} ({len(felder_dict)} Felder)"])
            parent_item.setData(0, Qt.UserRole, {
                'type': 'gruppe', 
                'gruppe_name': gruppe_name
            })
            parent_item.setExpanded(True)
            self.field_tree.addTopLevelItem(parent_item)
            
            # Felder als Child-Items (sortiert nach display_order wenn vorhanden)
            sorted_felder = sorted(
                felder_dict.items(),
                key=lambda x: x[1].get('display_order', 999) if isinstance(x[1], dict) else 999
            )
            
            for feld_guid, feld_data in sorted_felder:
                # Label als Name + erste 8 Zeichen der GUID
                if isinstance(feld_data, dict):
                    feld_label = feld_data.get('label', feld_data.get('name', 'Unbenannt'))
                else:
                    feld_label = str(feld_data)[:50]  # Primitive Werte (Strings, Numbers)
                
                guid_short = feld_guid[:8] if len(str(feld_guid)) > 8 else str(feld_guid)
                display_text = f"📄 {feld_label} ({guid_short})"
                
                child_item = QTreeWidgetItem([display_text])
                child_item.setData(0, Qt.UserRole, {
                    'type': 'feld',
                    'gruppe_name': gruppe_name,
                    'feld_guid': feld_guid
                })
                parent_item.addChild(child_item)
                
        logger.info(f"  ✅ {len(gruppen)} Gruppen mit Feldern geladen")
                
    def _on_tree_item_clicked(self, item, column):
        """Handler: Tree-Item angeklickt (lineare Struktur)"""
        if not item:
            return
            
        item_data = item.data(0, Qt.UserRole)
        if not item_data:
            return
            
        item_type = item_data.get('type')
        
        # ✅ NEUE LINEARE STRUKTUR
        if item_type == 'gruppe':
            # Gruppe angeklickt → Info anzeigen
            gruppe_name = item_data['gruppe_name']
            logger.info(f"📁 Gruppe ausgewählt: {gruppe_name}")
            
            icon = {
                'TEMPLATES': '🔧',
                'ROOT_CONTROLS': '⚙️',
                'CONTROL_PROPERTIES': '🎨',
                'PERSONDATEN': '👤',
                'SYS_MENUDATEN': '📋',
                'DE-DE': '🇩🇪'
            }.get(gruppe_name, '📁')
            
            self.right_header.setText(f"{icon} {gruppe_name}")
            self._clear_control_editor()
            return
            
        elif item_type == 'feld':
            # Einzelnes Feld angeklickt → Zeige Feld-Editor
            gruppe_name = item_data['gruppe_name']
            feld_guid = item_data['feld_guid']
            logger.info(f"📄 Feld ausgewählt: {gruppe_name}.{feld_guid}")
            
            # Feld-Daten aus Gruppe holen
            felder = self._get_gruppe_felder(gruppe_name)
            feld_data = felder.get(feld_guid, {})
            
            # Header aktualisieren
            if isinstance(feld_data, dict):
                feld_label = feld_data.get('label', feld_data.get('name', 'Unbenannt'))
            else:
                feld_label = str(feld_data)[:50]
            
            guid_short = str(feld_guid)[:8] if len(str(feld_guid)) > 8 else str(feld_guid)
            
            self.right_header.setText(f"📄 {feld_label} ({guid_short})")
            
            # Feld-Editor anzeigen
            self._build_single_field_editor(gruppe_name, feld_guid, feld_data)
    
    def _build_template_control_editor(self, meta_key, item_key, item_data):
        """Baut Editor für Template-Control (TEMPLATES, ROOT_CONTROLS, CONTROL_PROPERTIES)"""
        self._clear_control_editor()
        
        logger.info(f"🔧 Baue Template-Control-Editor: {meta_key}.{item_key}")
        
        if not isinstance(item_data, dict):
            # Kein Dict → einfacher Wert
            info_label = QLabel(f"Wert: {item_data}")
            self.control_editor_layout.addWidget(info_label)
            self.control_editor_layout.addStretch()
            return
        
        # Dict → Alle Felder anzeigen
        form_layout = QFormLayout()
        widgets = {}
        
        for field_key, field_value in sorted(item_data.items()):
            label = QLabel(field_key)
            
            # Widget basierend auf Wert-Typ
            if isinstance(field_value, bool):
                widget = QCheckBox()
                widget.setChecked(field_value)
            elif isinstance(field_value, (int, float)):
                widget = QSpinBox()
                widget.setRange(-999999, 999999)
                widget.setValue(int(field_value))
            elif isinstance(field_value, list):
                widget = QLineEdit()
                widget.setText(', '.join(map(str, field_value)))
                widget.setPlaceholderText("Komma-getrennte Liste")
            elif isinstance(field_value, dict):
                widget = QLineEdit()
                widget.setText(json.dumps(field_value, ensure_ascii=False))
                widget.setPlaceholderText("JSON-Objekt")
            else:
                widget = QLineEdit()
                widget.setText(str(field_value) if field_value is not None else '')
            
            widgets[field_key] = widget
            form_layout.addRow(label, widget)
        
        # Form in Layout einfügen
        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        self.control_editor_layout.addWidget(form_widget)
        self.control_editor_layout.addStretch()
        
        # Speichern bei Änderung
        def save_template_changes():
            for field_key, widget in widgets.items():
                if isinstance(widget, QCheckBox):
                    item_data[field_key] = widget.isChecked()
                elif isinstance(widget, QSpinBox):
                    item_data[field_key] = widget.value()
                elif isinstance(widget, QLineEdit):
                    text = widget.text().strip()
                    if field_key in item_data and isinstance(item_data[field_key], list):
                        item_data[field_key] = [s.strip() for s in text.split(',') if s.strip()]
                    elif field_key in item_data and isinstance(item_data[field_key], dict):
                        try:
                            item_data[field_key] = json.loads(text)
                        except json.JSONDecodeError:
                            logger.warning(f"⚠️ Ungültiges JSON für {field_key}: {text}")
                    else:
                        item_data[field_key] = text
            logger.info(f"💾 Template-Control gespeichert: {meta_key}.{item_key}")
        
        # Signals verbinden
        for widget in widgets.values():
            if isinstance(widget, QCheckBox):
                widget.stateChanged.connect(save_template_changes)
            elif isinstance(widget, QSpinBox):
                widget.valueChanged.connect(save_template_changes)
            elif isinstance(widget, QLineEdit):
                widget.textChanged.connect(save_template_changes)
        
        logger.info(f"  ✅ Template-Control-Editor aufgebaut mit {len(widgets)} Feldern")
    
    def _clear_control_editor(self):
        """Leert die rechte Seite (Control-Editor)"""
        while self.control_editor_layout.count():
            child = self.control_editor_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
    def _build_control_editor(self, field_type):
        """Baut Control-Editor für gewähltes Feld"""
        # Alte Widgets entfernen
        while self.control_editor_layout.count():
            child = self.control_editor_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # control_widgets für diesen field_type zurücksetzen
        if hasattr(self, 'control_widgets') and field_type in self.control_widgets:
            self.control_widgets[field_type] = {}
                
        # View-Table und Daten holen
        view_table = self._get_table_name()
        table_key = view_table.upper()
        metadaten = self.data['METADATEN'].get(table_key, {})
        controls_dict = metadaten.get(field_type, {})
        
        # Controls anzeigen
        for control_key, control_data in controls_dict.items():
            group = self._create_control_group(field_type, control_key, control_data)
            self.control_editor_layout.addWidget(group)
            
        # Buttons für Controls
        button_layout = QHBoxLayout()
        
        add_button = QPushButton(f"+ Control zu {field_type}")
        add_button.clicked.connect(lambda: self._add_control(field_type))
        button_layout.addWidget(add_button)
        
        button_layout.addStretch()
        self.control_editor_layout.addLayout(button_layout)
        
        # Stretch am Ende
        self.control_editor_layout.addStretch()
        
    def _build_single_field_editor(self, gruppe_name, feld_guid, feld_data):
        """
        Baut Feld-Editor für EINZELNES Feld (lineare Struktur)
        
        Args:
            gruppe_name: Name der Gruppe (z.B. "PERSONDATEN", "TEMPLATES")
            feld_guid: GUID des Feldes
            feld_data: Feld-Daten (dict oder primitiver Wert)
        """
        # Alte Widgets entfernen
        while self.control_editor_layout.count():
            child = self.control_editor_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # GroupBox für Feld erstellen
        group = self._create_field_group(gruppe_name, feld_guid, feld_data)
        self.control_editor_layout.addWidget(group)
        
        # Stretch am Ende
        self.control_editor_layout.addStretch()
        
    def _on_items_reordered(self):
        """Handler: Items per Drag & Drop neu sortiert"""
        logger.info("🔄 Controls neu sortiert per Drag & Drop")
        
        # View-Table holen
        view_table = self._get_table_name()
        if not view_table:
            return
            
        table_key = view_table.upper()
        
        # Durch alle Parent-Items (controls/standard_controls) iterieren
        for i in range(self.field_tree.topLevelItemCount()):
            parent_item = self.field_tree.topLevelItem(i)
            parent_data = parent_item.data(0, Qt.UserRole)
            
            if not parent_data or parent_data.get('type') != 'folder':
                continue
                
            field_type = parent_data['field_type']
            
            # Durch alle Child-Items iterieren und display_order aktualisieren
            for j in range(parent_item.childCount()):
                child_item = parent_item.child(j)
                child_data = child_item.data(0, Qt.UserRole)
                
                if not child_data or child_data.get('type') != 'control':
                    continue
                    
                control_key = child_data['control_key']
                
                # display_order in Daten aktualisieren
                if table_key in self.data['METADATEN']:
                    if field_type in self.data['METADATEN'][table_key]:
                        if control_key in self.data['METADATEN'][table_key][field_type]:
                            self.data['METADATEN'][table_key][field_type][control_key]['display_order'] = j
                            logger.info(f"  ✅ {control_key}.display_order = {j}")
                            
        logger.info("✅ display_order für alle Controls aktualisiert")
        
    def _update_display_order_from_tree(self):
        """Aktualisiert display_order aus TreeView-Reihenfolge (für Speichern)"""
        logger.info("🔄 Aktualisiere display_order aus TreeView...")
        
        # View-Table holen
        view_table = self._get_table_name()
        if not view_table:
            return
            
        table_key = view_table.upper()
        
        # Durch alle Parent-Items (controls/standard_controls) iterieren
        for i in range(self.field_tree.topLevelItemCount()):
            parent_item = self.field_tree.topLevelItem(i)
            parent_data = parent_item.data(0, Qt.UserRole)
            
            if not parent_data or parent_data.get('type') != 'folder':
                continue
                
            field_type = parent_data['field_type']
            
            # Durch alle Child-Items iterieren und display_order aktualisieren
            for j in range(parent_item.childCount()):
                child_item = parent_item.child(j)
                child_data = child_item.data(0, Qt.UserRole)
                
                if not child_data or child_data.get('type') != 'control':
                    continue
                    
                control_key = child_data['control_key']
                
                # display_order in Daten aktualisieren
                if table_key in self.data['METADATEN']:
                    if field_type in self.data['METADATEN'][table_key]:
                        if control_key in self.data['METADATEN'][table_key][field_type]:
                            self.data['METADATEN'][table_key][field_type][control_key]['display_order'] = j
                            
        logger.info("  ✅ display_order aus Tree übernommen")
        
    def _create_field_group(self, gruppe_name, feld_guid, feld_data):
        """
        Erstellt GroupBox für einzelnes Feld (lineare Struktur)
        
        Args:
            gruppe_name: Name der Gruppe
            feld_guid: GUID des Feldes
            feld_data: Feld-Daten (dict oder primitiver Wert)
        """
        # Wenn Feld kein Dict ist, zeige nur Wert
        if not isinstance(feld_data, dict):
            group = QGroupBox(f"Feld: {feld_guid}")
            layout = QFormLayout(group)
            
            # Einfacher Editor für primitiven Wert
            value_edit = QLineEdit(str(feld_data))
            value_edit.textChanged.connect(
                lambda text: self._on_primitive_field_changed(gruppe_name, feld_guid, text)
            )
            layout.addRow("Wert:", value_edit)
            
            return group
        
        # Dict-Feld: Alle Properties anzeigen
        feld_label = feld_data.get('label', feld_data.get('name', feld_guid))
        group = QGroupBox(f"Feld: {feld_label}")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QFormLayout(group)
        
        # Alle Properties des Feldes anzeigen (sortiert nach display_order wenn vorhanden)
        sorted_props = sorted(
            feld_data.items(),
            key=lambda item: item[1].get('display_order', 999) if isinstance(item[1], dict) and 'display_order' in item[1] else 999
        )
        
        for property_key, property_value in sorted_props:
            # Label für Property
            label_text = property_key.replace('_', ' ').title()
            
            # Widget basierend auf Typ erstellen
            if isinstance(property_value, bool):
                widget_input = QCheckBox()
                widget_input.setChecked(property_value)
                widget_input.stateChanged.connect(
                    lambda state, gn=gruppe_name, fg=feld_guid, pk=property_key: 
                    self._on_field_property_changed(gn, fg, pk, state == Qt.Checked)
                )
            elif isinstance(property_value, int):
                widget_input = QSpinBox()
                widget_input.setRange(-999999, 999999)
                widget_input.setValue(property_value)
                widget_input.valueChanged.connect(
                    lambda val, gn=gruppe_name, fg=feld_guid, pk=property_key: 
                    self._on_field_property_changed(gn, fg, pk, val)
                )
            elif isinstance(property_value, dict):
                # Nested Dict - zeige als JSON
                widget_input = QLineEdit()
                widget_input.setText(json.dumps(property_value, ensure_ascii=False))
                widget_input.textChanged.connect(
                    lambda text, gn=gruppe_name, fg=feld_guid, pk=property_key: 
                    self._on_field_property_changed(gn, fg, pk, self._parse_json_safe(text))
                )
            else:
                # String oder anderer Typ
                widget_input = QLineEdit()
                widget_input.setText(str(property_value) if property_value is not None else '')
                widget_input.textChanged.connect(
                    lambda text, gn=gruppe_name, fg=feld_guid, pk=property_key: 
                    self._on_field_property_changed(gn, fg, pk, text)
                )
            
            layout.addRow(f"{label_text}:", widget_input)
        
        return group
    
    def _parse_json_safe(self, text):
        """Parst JSON sicher, gibt bei Fehler den Text zurück"""
        try:
            return json.loads(text)
        except:
            return text
    
    def _on_primitive_field_changed(self, gruppe_name, feld_guid, value):
        """Handler: Primitives Feld wurde geändert"""
        if gruppe_name in self.data:
            self.data[gruppe_name][feld_guid] = value
            logger.info(f"  ✏️ {gruppe_name}.{feld_guid} = {value}")
    
    def _on_field_property_changed(self, gruppe_name, feld_guid, property_key, value):
        """Handler: Feld-Property wurde geändert (lineare Struktur)"""
        if gruppe_name in self.data and feld_guid in self.data[gruppe_name]:
            if isinstance(self.data[gruppe_name][feld_guid], dict):
                self.data[gruppe_name][feld_guid][property_key] = value
                logger.info(f"  ✏️ {gruppe_name}.{feld_guid}.{property_key} = {value}")
    
    def _parse_json_safe(self, text):
        """Parst JSON sicher, gibt Original bei Fehler zurück"""
        try:
            return json.loads(text)
        except:
            return text
    
    def _on_field_property_changed(self, gruppe_name, feld_guid, property_key, value):
        """Handler: Feld-Property wurde geändert → sofort in data schreiben"""
        if gruppe_name in self.data and feld_guid in self.data[gruppe_name]:
            self.data[gruppe_name][feld_guid][property_key] = value
            logger.info(f"  ✏️ {gruppe_name}.{feld_guid}.{property_key} = {value}")
    
    def _on_primitive_field_changed(self, gruppe_name, feld_guid, value):
        """Handler: Primitives Feld wurde geändert"""
        if gruppe_name in self.data:
            self.data[gruppe_name][feld_guid] = value
            logger.info(f"  ✏️ {gruppe_name}.{feld_guid} = {value}")
                
            layout.addRow(f"{label}:", widget_input)
            
            # Widget speichern für späteren Zugriff
            if not hasattr(self, 'control_widgets'):
                self.control_widgets = {}
            if field_type not in self.control_widgets:
                self.control_widgets[field_type] = {}
            if control_key not in self.control_widgets[field_type]:
                self.control_widgets[field_type][control_key] = {}
            self.control_widgets[field_type][control_key][property_key] = widget_input
        
        return group
        
    def _on_control_property_changed(self, field_type, control_key, property_key, value):
        """Handler: Control-Property wurde geändert → sofort in view_data schreiben"""
        # View-Table holen
        view_table = self._get_table_name()
        if not view_table:
            logger.warning("⚠️ VIEW_TABLE nicht gesetzt - Änderung nicht gespeichert")
            return
            
        table_key = view_table.upper()
        
        # Pfad zu Property sicherstellen
        if table_key not in self.data['METADATEN']:
            self.data['METADATEN'][table_key] = {}
        if field_type not in self.data['METADATEN'][table_key]:
            self.data['METADATEN'][table_key][field_type] = {}
        if control_key not in self.data['METADATEN'][table_key][field_type]:
            self.data['METADATEN'][table_key][field_type][control_key] = {}
            
        # Wert schreiben
        self.data['METADATEN'][table_key][field_type][control_key][property_key] = value
        
        logger.info(f"  ✏️ {control_key}.{property_key} = {value}")
    
    def _create_configs_editor(self, field_type, control_key, control_data):
        """
        Erstellt Editor für configs-Struktur (dropdown, help, viewtable).
        
        Struktur:
        configs: {
          dropdown: {table, key, feld, gruppe},
          help: {table, key, feld, gruppe},
          viewtable: {table, key, feld}
        }
        """
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Configs-Daten holen oder initialisieren
        configs = control_data.get('configs', {})
        
        # Dropdown Config
        dropdown_group = QGroupBox("Dropdown Config")
        dropdown_layout = QFormLayout(dropdown_group)
        
        dropdown_data = configs.get('dropdown', {})
        
        dd_table = QLineEdit(dropdown_data.get('table', ''))
        dd_table.setPlaceholderText('z.B. dropdowndaten')
        dd_table.textChanged.connect(
            lambda text: self._on_config_changed(field_type, control_key, 'dropdown', 'table', text)
        )
        dropdown_layout.addRow("Tabelle:", dd_table)
        
        dd_key = QLineEdit(dropdown_data.get('key', ''))
        dd_key.setPlaceholderText('GUID des Dropdown-Datensatzes')
        dd_key.textChanged.connect(
            lambda text: self._on_config_changed(field_type, control_key, 'dropdown', 'key', text)
        )
        dropdown_layout.addRow("Key (GUID):", dd_key)
        
        dd_feld = QLineEdit(dropdown_data.get('feld', ''))
        dd_feld.setPlaceholderText('z.B. anrede, waehrung')
        dd_feld.textChanged.connect(
            lambda text: self._on_config_changed(field_type, control_key, 'dropdown', 'feld', text)
        )
        dropdown_layout.addRow("Feld:", dd_feld)
        
        dd_gruppe = QLineEdit(dropdown_data.get('gruppe', ''))
        dd_gruppe.setPlaceholderText('Optional: z.B. DEU, ENG')
        dd_gruppe.textChanged.connect(
            lambda text: self._on_config_changed(field_type, control_key, 'dropdown', 'gruppe', text)
        )
        dropdown_layout.addRow("Gruppe:", dd_gruppe)
        
        main_layout.addWidget(dropdown_group)
        
        # Help Config
        help_group = QGroupBox("Help Config")
        help_layout = QFormLayout(help_group)
        
        help_data = configs.get('help', {})
        
        help_table = QLineEdit(help_data.get('table', ''))
        help_table.setPlaceholderText('z.B. beschreibungen')
        help_table.textChanged.connect(
            lambda text: self._on_config_changed(field_type, control_key, 'help', 'table', text)
        )
        help_layout.addRow("Tabelle:", help_table)
        
        help_key = QLineEdit(help_data.get('key', ''))
        help_key.setPlaceholderText('GUID des Hilfe-Datensatzes')
        help_key.textChanged.connect(
            lambda text: self._on_config_changed(field_type, control_key, 'help', 'key', text)
        )
        help_layout.addRow("Key (GUID):", help_key)
        
        help_feld = QLineEdit(help_data.get('feld', ''))
        help_feld.setPlaceholderText('z.B. PERSONDATEN_PERSDATEN_ANREDE')
        help_feld.textChanged.connect(
            lambda text: self._on_config_changed(field_type, control_key, 'help', 'feld', text)
        )
        help_layout.addRow("Feld:", help_feld)
        
        help_gruppe = QLineEdit(help_data.get('gruppe', ''))
        help_gruppe.setPlaceholderText('Optional: z.B. DEU, ENG')
        help_gruppe.textChanged.connect(
            lambda text: self._on_config_changed(field_type, control_key, 'help', 'gruppe', text)
        )
        help_layout.addRow("Gruppe:", help_gruppe)
        
        main_layout.addWidget(help_group)
        
        # Viewtable Config
        viewtable_group = QGroupBox("Viewtable Config")
        viewtable_layout = QFormLayout(viewtable_group)
        
        viewtable_data = configs.get('viewtable', {})
        
        vt_table = QLineEdit(viewtable_data.get('table', ''))
        vt_table.setPlaceholderText('Tabelle (sys_viewdaten/sys_framedaten)')
        vt_table.textChanged.connect(
            lambda text: self._on_config_changed(field_type, control_key, 'viewtable', 'table', text)
        )
        viewtable_layout.addRow("Tabelle:", vt_table)
        
        vt_key = QLineEdit(viewtable_data.get('key', ''))
        vt_key.setPlaceholderText('View-GUID')
        vt_key.textChanged.connect(
            lambda text: self._on_config_changed(field_type, control_key, 'viewtable', 'key', text)
        )
        viewtable_layout.addRow("Key (GUID):", vt_key)
        
        vt_feld = QLineEdit(viewtable_data.get('feld', ''))
        vt_feld.setPlaceholderText('Optional: Spezifisches Feld')
        vt_feld.textChanged.connect(
            lambda text: self._on_config_changed(field_type, control_key, 'viewtable', 'feld', text)
        )
        viewtable_layout.addRow("Feld:", vt_feld)
        
        main_layout.addWidget(viewtable_group)
        
        return container
    
    def _on_config_changed(self, field_type, control_key, config_type, config_field, value):
        """Handler: Config-Wert wurde geändert → sofort in view_data schreiben"""
        view_table = self._get_table_name()
        if not view_table:
            logger.warning("⚠️ VIEW_TABLE nicht gesetzt - Änderung nicht gespeichert")
            return
            
        table_key = view_table.upper()
        
        # Pfad sicherstellen
        if table_key not in self.data['METADATEN']:
            self.data['METADATEN'][table_key] = {}
        if field_type not in self.data['METADATEN'][table_key]:
            self.data['METADATEN'][table_key][field_type] = {}
        if control_key not in self.data['METADATEN'][table_key][field_type]:
            self.data['METADATEN'][table_key][field_type][control_key] = {}
        if 'configs' not in self.data['METADATEN'][table_key][field_type][control_key]:
            self.data['METADATEN'][table_key][field_type][control_key]['configs'] = {}
        if config_type not in self.data['METADATEN'][table_key][field_type][control_key]['configs']:
            self.data['METADATEN'][table_key][field_type][control_key]['configs'][config_type] = {}
        
        # Wert schreiben
        self.data['METADATEN'][table_key][field_type][control_key]['configs'][config_type][config_field] = value
        
        logger.info(f"  ✏️ {control_key}.configs.{config_type}.{config_field} = {value}")
        
    def _add_field(self):
        """✅ LINEARE STRUKTUR: Fügt neues Feld zur ausgewählten Gruppe hinzu"""
        import uuid
        
        # Ausgewähltes Item holen
        current_item = self.field_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warnung", "Bitte wähle zuerst eine Gruppe aus!")
            return
            
        # Item-Daten holen
        item_data = current_item.data(0, Qt.UserRole)
        if not item_data:
            return
        
        item_type = item_data.get('type')
        
        # Wenn Feld ausgewählt, zur Gruppe (Parent) wechseln
        if item_type == 'feld':
            current_item = current_item.parent()
            item_data = current_item.data(0, Qt.UserRole)
            item_type = item_data.get('type')
        
        # Muss eine Gruppe sein
        if item_type != 'gruppe':
            QMessageBox.warning(self, "Warnung", "Bitte wähle eine Gruppe aus!")
            return
        
        gruppe_name = item_data['gruppe_name']
        logger.info(f"➕ Füge neues Feld zu Gruppe '{gruppe_name}' hinzu")
        
        # Neue GUID für das Feld generieren
        neue_guid = str(uuid.uuid4())
        
        # Template für diese Gruppe holen (aus TEMPLATES Gruppe, falls vorhanden)
        template = self._get_template_for_gruppe(gruppe_name)
        
        # Neues Feld mit Template-Werten erstellen
        neues_feld = template.copy()
        neues_feld['label'] = f'Neues Feld {neue_guid[:8]}'
        
        # Feld in data hinzufügen
        if gruppe_name not in self.data:
            self.data[gruppe_name] = {}
        
        self.data[gruppe_name][neue_guid] = neues_feld
        
        logger.info(f"  ✅ Feld {neue_guid} zu Gruppe '{gruppe_name}' hinzugefügt")
        logger.info(f"  📋 Template verwendet: {list(template.keys())[:5]}...")
        
        # Tree-View aktualisieren
        self._refresh_field_list()
        
        # Neues Feld im Tree auswählen
        self._select_field_in_tree(gruppe_name, neue_guid)
        
    def _remove_field(self):
        """✅ LINEARE STRUKTUR: Entfernt ausgewähltes Feld"""
        # Ausgewähltes Item holen
        current_item = self.field_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warnung", "Bitte wähle zuerst ein Feld aus!")
            return
            
        # Item-Daten holen
        item_data = current_item.data(0, Qt.UserRole)
        if not item_data:
            return
        
        item_type = item_data.get('type')
        
        # Muss ein Feld sein (keine Gruppe)
        if item_type != 'feld':
            QMessageBox.warning(self, "Warnung", "Bitte wähle ein Feld zum Löschen aus (keine Gruppe)!")
            return
        
        gruppe_name = item_data['gruppe_name']
        feld_guid = item_data['feld_guid']
        
        # Feld-Label für Anzeige holen
        feld_data = self.data.get(gruppe_name, {}).get(feld_guid, {})
        feld_label = feld_data.get('label', feld_guid[:8]) if isinstance(feld_data, dict) else str(feld_guid)[:8]
        
        # Löschen bestätigen
        reply = QMessageBox.question(
            self,
            "Feld löschen",
            f"Feld '{feld_label}' aus Gruppe '{gruppe_name}' wirklich löschen?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Aus data entfernen
        if gruppe_name in self.data and feld_guid in self.data[gruppe_name]:
            del self.data[gruppe_name][feld_guid]
            logger.info(f"🗑️ Feld '{feld_label}' ({feld_guid}) aus Gruppe '{gruppe_name}' gelöscht")
        
        # TreeView aktualisieren
            self._refresh_field_list()
            
            # Editor leeren
            while self.control_editor_layout.count():
                child = self.control_editor_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                    
            self.right_header.setText("Wähle ein Feld aus")
            return
        
        # VIEW-MODUS
        # Nur Controls können gelöscht werden, keine Folder
        if item_type != 'control':
            QMessageBox.warning(
                self,
                "Warnung",
                "Bitte wähle ein Control zum Löschen aus (nicht den Folder)!"
            )
            return
            
        field_type = item_data['field_type']
        control_key = item_data['control_key']
        
        # Löschen bestätigen
        reply = QMessageBox.question(
            self,
            "Control löschen",
            f"Control '{control_key}' wirklich löschen?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        # Aus View-Daten entfernen
        view_table = self._get_table_name()
        table_key = view_table.upper()
        
        if table_key in self.data['METADATEN']:
            if field_type in self.data['METADATEN'][table_key]:
                if control_key in self.data['METADATEN'][table_key][field_type]:
                    del self.data['METADATEN'][table_key][field_type][control_key]
                    logger.info(f"🗑️ Control '{control_key}' gelöscht")
                    
        # TreeView aktualisieren
        self._refresh_field_list()
        
        # Editor leeren
        while self.control_editor_layout.count():
            child = self.control_editor_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        self.right_header.setText("Wähle ein Feld aus")
        
    def _add_template_item(self, meta_key):
        """Fügt neues Item zu Template-Folder hinzu (TEMPLATES, ROOT_CONTROLS, CONTROL_PROPERTIES)"""
        logger.info(f"➕ Füge Template-Item zu {meta_key} hinzu")
        
        # Item-Key (Name) eingeben
        item_key, ok = QInputDialog.getText(
            self,
            "Template-Item hinzufügen",
            f"Name für neues {meta_key}-Item:",
            QLineEdit.Normal,
            ""
        )
        
        if not ok or not item_key.strip():
            return
        
        item_key = item_key.strip()
        
        # Prüfen ob Key bereits existiert
        if meta_key in self.data['METADATEN']:
            if item_key in self.data['METADATEN'][meta_key]:
                QMessageBox.warning(
                    self,
                    "Warnung",
                    f"Item '{item_key}' existiert bereits in {meta_key}!"
                )
                return
        
        # Standard-Struktur basierend auf meta_key
        if meta_key == 'TEMPLATES':
            # Template für neue Templates: Kopiere view_text als Basis
            if 'view_text' in self.data['METADATEN'][meta_key]:
                new_item_data = self.data['METADATEN'][meta_key]['view_text'].copy()
            else:
                new_item_data = {
                    'table': '',
                    'gruppe': '',
                    'feld': '',
                    'label': '',
                    'tooltip': '',
                    'control_type': 'text',
                    'width': 150,
                    'visible': True,
                    'sortable': True,
                    'filterable': True,
                    'editable': False,
                    'alignment': 'left',
                    'display_order': 0
                }
        elif meta_key == 'ROOT_CONTROLS':
            # Standard ROOT_CONTROL Struktur
            new_item_data = {
                'label': item_key,
                'control_type': 'text',
                'readonly': False,
                'display_order': 999,
                'muss': False,
                'default_value': '',
                'options': []
            }
        elif meta_key == 'CONTROL_PROPERTIES':
            # Standard CONTROL_PROPERTY Struktur
            new_item_data = {
                'label': item_key,
                'control_type': 'text',
                'readonly': False,
                'display_order': 999
            }
        else:
            # Fallback: Leeres Dict
            new_item_data = {}
        
        # Item hinzufügen
        if meta_key not in self.data['METADATEN']:
            self.data['METADATEN'][meta_key] = {}
            
        self.data['METADATEN'][meta_key][item_key] = new_item_data
        logger.info(f"✅ Template-Item '{item_key}' zu {meta_key} hinzugefügt")
        
        # TreeView aktualisieren
        self._refresh_field_list()
        
        # Neues Item im Tree suchen und auswählen
        for i in range(self.field_tree.topLevelItemCount()):
            folder_item = self.field_tree.topLevelItem(i)
            folder_data = folder_item.data(0, Qt.UserRole)
            if folder_data and folder_data.get('meta_key') == meta_key:
                # Folder gefunden, Kind suchen
                for j in range(folder_item.childCount()):
                    child_item = folder_item.child(j)
                    child_data = child_item.data(0, Qt.UserRole)
                    if child_data and child_data.get('item_key') == item_key:
                        self.field_tree.setCurrentItem(child_item)
                        self._on_tree_item_clicked(child_item, 0)
                        break
                break
        
    def _add_control(self, field_type):
        """Fügt neues Control zu Feld hinzu"""
        # Template auswählen
        templates = list(self.templates.keys())
        template_name, ok = QInputDialog.getItem(
            self,
            "Template wählen",
            "Template:",
            templates,
            0,
            False
        )
        
        if not ok:
            return
            
        # Template kopieren (KOMPLETTE Kopie mit allen Properties!)
        template_data = self.templates[template_name].copy()
        
        # GUID als Key generieren
        import uuid
        control_guid = str(uuid.uuid4())
        
        # In View-Daten einfügen
        view_table = self._get_table_name()
        table_key = view_table.upper()
        
        if table_key not in self.data['METADATEN']:
            self.data['METADATEN'][table_key] = {}
        if field_type not in self.data['METADATEN'][table_key]:
            self.data['METADATEN'][table_key][field_type] = {}
            
        # Template-Daten mit GUID als Key speichern
        self.data['METADATEN'][table_key][field_type][control_guid] = template_data
        
        logger.info(f"✅ Control '{control_guid}' ({template_name}) zu {field_type} hinzugefügt")
        
        # TreeView und Editor aktualisieren
        self._refresh_field_list()
        self._build_control_editor(field_type)
        
    def _on_no_data_changed(self, state):
        """
        Handler: NO_DATA Checkbox geändert
        
        Wenn NO_DATA auf false gesetzt wird (Qt.Unchecked):
        - Erstelle controls und standard_controls Struktur
        - Füge DUMMY-Control zu standard_controls hinzu
        
        Wenn NO_DATA auf true gesetzt wird (Qt.Checked):
        - Nichts tun (Controls bleiben erhalten)
        """
        is_no_data = (state == Qt.Checked)
        
        logger.info(f"🔄 NO_DATA geändert auf: {is_no_data}")
        
        if not is_no_data:
            # NO_DATA = false → Struktur generieren
            logger.info("  📦 Generiere Datenstruktur...")
            
            # VIEW_TABLE holen
            view_table = self._get_table_name()
            if not view_table:
                QMessageBox.warning(
                    self,
                    "Warnung",
                    "VIEW_TABLE muss zuerst gesetzt werden!"
                )
                # Checkbox zurücksetzen
                if 'NO_DATA' in self.root_widgets:
                    self.root_widgets['NO_DATA'].setChecked(True)
                return
                
            table_key = view_table.upper()
            logger.info(f"  📋 Tabellen-Key: {table_key}")
            
            # METADATEN[TABLE_KEY] erstellen wenn nicht vorhanden
            if table_key not in self.data['METADATEN']:
                self.data['METADATEN'][table_key] = {}
                logger.info(f"  ✅ METADATEN[{table_key}] erstellt")
                
            # controls erstellen wenn nicht vorhanden
            if 'controls' not in self.data['METADATEN'][table_key]:
                self.data['METADATEN'][table_key]['controls'] = {}
                logger.info(f"  ✅ controls erstellt")
                
            # standard_controls erstellen wenn nicht vorhanden
            if 'standard_controls' not in self.data['METADATEN'][table_key]:
                self.data['METADATEN'][table_key]['standard_controls'] = {}
                logger.info(f"  ✅ standard_controls erstellt")
                
                # DUMMY-Control hinzufügen
                dummy_control = {
                    "gruppe": "SYSTEM",
                    "feld": "DUMMY",
                    "name": "Dummy",
                    "type": "string",
                    "default": "keine Daten",
                    "dropdown": None,
                    "control_type": "base",
                    "expert_mode": True,
                    "show": False,
                    "display_order": 0,
                    "expert_order": 0,
                    "searchable": True,
                    "sortable": True,
                    "sortDirection": "asc",
                    "sortByOriginal": False,
                    "filterType": "contains"
                }
                self.data['METADATEN'][table_key]['standard_controls']['dummy'] = dummy_control
                logger.info(f"  ✅ DUMMY-Control zu standard_controls hinzugefügt")
                
            # Feldliste aktualisieren
            self._refresh_field_list()
            
            QMessageBox.information(
                self,
                "Struktur generiert",
                f"Datenstruktur für '{view_table}' wurde erstellt:\n\n"
                f"✅ controls (leer)\n"
                f"✅ standard_controls (mit DUMMY)"
            )
        else:
            # NO_DATA = true → Nichts tun
            logger.info("  ℹ️ NO_DATA auf true gesetzt - Controls bleiben erhalten")
        
    def _save_all(self):
        """Speichert alle Änderungen"""
        logger.info("💾 Speichere View-Daten...")
        
        try:
            # SCHRITT 0: display_order aus TreeView aktualisieren (für Drag & Drop)
            self._update_display_order_from_tree()
            
            # ROOT-Felder aus Widgets übernehmen
            for control_key, widget in self.root_widgets.items():
                if isinstance(widget, QCheckBox):
                    self.data['ROOT'][control_key] = widget.isChecked()
                elif isinstance(widget, QComboBox):
                    self.data['ROOT'][control_key] = widget.currentText()
                else:
                    self.data['ROOT'][control_key] = widget.text()
            
            # SCHRITT 0.5: Prüfe ob METADATEN leer ist und erstelle Struktur mit Dummies
            view_table = self._get_table_name()
            if view_table:
                table_key = view_table.upper()
                
                # Wenn METADATEN leer oder Tabelle nicht vorhanden
                if not self.data.get('METADATEN') or table_key not in self.data['METADATEN']:
                    logger.info(f"  📦 Erstelle Basis-Struktur für Tabelle '{table_key}'...")
                    
                    if 'METADATEN' not in self.data:
                        self.data['METADATEN'] = {}
                    
                    # Struktur mit controls und standard_controls erstellen
                    self.data['METADATEN'][table_key] = {
                        'controls': {
                            'dummy': {
                                'gruppe': 'SYSTEM',
                                'feld': 'DUMMY',
                                'label': 'DUMMY (bitte löschen)',
                                'display_order': 0,
                                'type': 'text',
                                'show': False,
                                'expert_mode': False
                            }
                        },
                        'standard_controls': {
                            'dummy': {
                                'gruppe': 'SYSTEM',
                                'feld': 'DUMMY_STD',
                                'label': 'DUMMY STD (bitte löschen)',
                                'display_order': 0,
                                'type': 'text',
                                'show': False,
                                'expert_mode': False
                            }
                        }
                    }
                    
                    logger.info(f"  ✅ Basis-Struktur mit controls/standard_controls erstellt")
                    
            # WICHTIG: Control-Daten sind BEREITS in view_data durch Signal-Handling!
            # Kein Auslesen der Widgets mehr nötig - würde zu "deleted widget" Fehler führen
            logger.info("  📋 Control-Daten bereits durch Signal-Handling in view_data geschrieben")
            
            # display_order aus TreeView aktualisieren (falls geändert)
            self._update_display_order_from_tree()
            
            # In Datenbank speichern
            self.edit_db.data = self.data
            self.edit_db.save_all_values()
            
            logger.info("✅ View-Daten gespeichert")
            
            # Signal emittieren
            self.save_completed.emit()
            
            QMessageBox.information(self, "Erfolg", "View-Daten erfolgreich gespeichert!")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern:\n{e}")
