"""
PDVM View-Editor - Editor für sys_viewdaten

ARCHITEKTUR:
- Tab 1: ROOT-Felder (VIEW_TABLE, NO_DATA)
- Tab 2: Felder & Controls (Split-View mit Feldliste + Control-Editor)

VERWENDUNG:
    editor = PdvmViewEditor(
        view_guid="abc-123",
        frame_guid="3be5d463-c0ea-4b71-b486-f2d9f647d527"
    )
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


class PdvmViewEditor(QWidget):
    """
    View-Editor für sys_viewdaten
    
    Signals:
        save_completed: Emittiert nach erfolgreichem Speichern
        refresh_requested: Emittiert wenn View neu geladen werden soll
    """
    
    save_completed = pyqtSignal()
    refresh_requested = pyqtSignal()
    
    def __init__(self, framedaten_db, selected_guid, main_app=None, gcs=None, parent=None):
        """
        Initialisierung View-Editor
        
        Args:
            framedaten_db: PdvmCentralDatenbank Instanz für sys_framedaten
            selected_guid: GUID des zu bearbeitenden View-Datensatzes
            main_app: Referenz zur Hauptanwendung (optional)
            gcs: Global Control System (optional, wird sonst geholt)
            parent: Parent-Widget
        """
        super().__init__(parent)
        
        logger.info(f"🔧 PdvmViewEditor initialisiert")
        logger.info(f"  📋 View-GUID: {selected_guid}")
        
        self.view_guid = selected_guid
        self.main_app = main_app
        self.gcs = gcs if gcs else get_gcs()
        
        # Modus automatisch erkennen (Template vs. normale View)
        self.edit_mode = 'template' if selected_guid == '55555555-5555-5555-5555-555555555555' else 'view'
        logger.info(f"  🎯 Edit-Modus: {self.edit_mode.upper()}")
        
        # Framedaten-Instanz übernehmen
        self.framedaten_db = framedaten_db
        
        # Frame-GUID aus framedaten_db extrahieren
        self.frame_guid = self.framedaten_db.guid
        logger.info(f"  🖼️ Frame-GUID: {self.frame_guid}")
        
        # Datenbank-Instanzen mit GUID initialisieren
        self.view_db = PdvmCentralDatenbank('sys_viewdaten', self.view_guid)
        self.template_db = PdvmCentralDatenbank('sys_viewdaten', '55555555-5555-5555-5555-555555555555')
        
        # View-Daten laden (passiert automatisch im Constructor)
        self._load_view_data()
        
        # Templates laden (passiert automatisch im Constructor)
        self._load_templates()
        
        # UI aufbauen
        self._setup_ui()
        
    def _load_view_data(self):
        """Holt View-Daten aus bereits geladener Instanz"""
        logger.info(f"📂 Hole View-Daten: {self.view_guid}")
        
        # Daten sind bereits geladen (Constructor)
        self.view_data = self.view_db.data
        
        # Struktur validieren
        if 'ROOT' not in self.view_data:
            self.view_data['ROOT'] = {}
        if 'METADATEN' not in self.view_data:
            self.view_data['METADATEN'] = {}
            
        logger.info(f"  ✅ View-Daten geladen: {self.view_data.get('ROOT', {}).get('VIEW_TABLE', 'N/A')}")
        
    def _load_templates(self):
        """Lädt Control-Templates UND Control-Properties aus Template-DB"""
        logger.info(f"📂 Hole Control-Templates")
        
        # Daten sind bereits geladen (Constructor mit template_guid)
        template_metadaten = self.template_db.data.get('METADATEN', {})
        
        # ROOT_CONTROLS aus Template laden
        self.root_controls = template_metadaten.get('ROOT_CONTROLS', {})
        
        # Templates für neue Controls
        self.templates = template_metadaten.get('TEMPLATES', {})
        
        # Control-Properties für Editor
        self.control_properties = template_metadaten.get('CONTROL_PROPERTIES', {})
        
        logger.info(f"  ✅ {len(self.root_controls)} ROOT-Controls aus Template geladen")
        logger.info(f"  ✅ {len(self.templates)} Templates geladen: {list(self.templates.keys())}")
        logger.info(f"  ✅ {len(self.control_properties)} Control-Properties geladen")
        
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
            self.mode_info_label.setText("✨ Template-Bearbeitungsmodus (GUID: 55555...)")
        else:
            view_name = self.view_data.get('ROOT', {}).get('VIEW_NAME', 'Unbenannt')
            self.mode_info_label.setText(f"📄 View: {view_name}")
        
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
        all_keys = set(self.root_controls.keys()) | set(self.view_data.get('ROOT', {}).keys())
        
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
                value = self.view_data['ROOT'].get(control_key, default_value)
                widget_input.setChecked(bool(value))
                
                # Signal: Änderungen direkt in view_data schreiben
                widget_input.stateChanged.connect(
                    lambda state, key=control_key: self.view_data['ROOT'].__setitem__(key, bool(state))
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
                value = self.view_data['ROOT'].get(control_key, default_value)
                index = widget_input.findText(str(value))
                if index >= 0:
                    widget_input.setCurrentIndex(index)
                
                # Signal: Änderungen direkt in view_data schreiben
                widget_input.currentTextChanged.connect(
                    lambda text, key=control_key: self.view_data['ROOT'].__setitem__(key, text)
                )
            else:
                widget_input = QLineEdit()
                # Default-Wert aus Template verwenden
                default_value = control.get('default_value', '')
                value = self.view_data['ROOT'].get(control_key, default_value)
                widget_input.setText(str(value))
                widget_input.setReadOnly(readonly)
                
                # Signal: Änderungen direkt in view_data schreiben
                if not readonly:
                    widget_input.textChanged.connect(
                        lambda text, key=control_key: self.view_data['ROOT'].__setitem__(key, text)
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
        
        if key in self.view_data['ROOT']:
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
        self.view_data['ROOT'][key] = value
        
        # Formular neu aufbauen (zeigt neue Eigenschaft an)
        self._rebuild_root_form()
        
        logger.info(f"✅ ROOT-Eigenschaft '{key}' hinzugefügt")
    
    def _remove_root_property(self):
        """Entfernt ROOT-Eigenschaft"""
        from PyQt5.QtWidgets import QInputDialog, QMessageBox
        
        if not self.view_data['ROOT']:
            QMessageBox.warning(self, "Warnung", "Keine Eigenschaften vorhanden!")
            return
        
        # Liste aller Keys
        keys = list(self.view_data['ROOT'].keys())
        
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
        del self.view_data['ROOT'][key]
        
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
        """Aktualisiert TreeView mit hierarchischer Struktur"""
        self.field_tree.clear()
        
        # TEMPLATE-MODUS: METADATEN-Ebenen zeigen
        if self.edit_mode == 'template':
            self._refresh_template_list()
            return
        
        # VIEW-MODUS: Normale Tabellen-Struktur
        # View-Table holen
        view_table = self.view_data['ROOT'].get('VIEW_TABLE', '')
        if not view_table:
            return
            
        # Tabellen-Key (GROSSBUCHSTABEN)
        table_key = view_table.upper()
        
        # Felder aus METADATEN
        metadaten = self.view_data['METADATEN'].get(table_key, {})
        
        if not metadaten:
            # Noch keine Felder - Hinweis anzeigen
            item = QTreeWidgetItem(["Keine Felder definiert"])
            item.setFlags(Qt.NoItemFlags)
            self.field_tree.addTopLevelItem(item)
            return
            
        # Hierarchische Struktur aufbauen
        for field_type in ['controls', 'standard_controls']:
            if field_type not in metadaten:
                continue
                
            # Parent-Item für controls/standard_controls
            parent_item = QTreeWidgetItem([f"📁 {field_type}"])
            parent_item.setData(0, Qt.UserRole, {'type': 'folder', 'field_type': field_type})
            parent_item.setExpanded(True)  # Automatisch aufgeklappt
            self.field_tree.addTopLevelItem(parent_item)
            
            # Controls als Child-Items (sortiert nach display_order)
            controls_dict = metadaten[field_type]
            sorted_controls = sorted(
                controls_dict.items(),
                key=lambda x: x[1].get('display_order', 999)
            )
            
            for control_key, control_data in sorted_controls:
                # Label als Name + erste 8 Zeichen der GUID
                control_label = control_data.get('label', 'Unbenannt')
                guid_short = control_key[:8] if len(control_key) > 8 else control_key
                display_text = f"📄 {control_label} ({guid_short})"
                
                child_item = QTreeWidgetItem([display_text])
                child_item.setData(0, Qt.UserRole, {
                    'type': 'control',
                    'field_type': field_type,
                    'control_key': control_key
                })
                parent_item.addChild(child_item)
                
    def _refresh_template_list(self):
        """Zeigt Template-Struktur: METADATEN-Ebenen (TEMPLATES, ROOT_CONTROLS, CONTROL_PROPERTIES)"""
        logger.info("🔧 Lade Template-Struktur...")
        
        metadaten = self.view_data.get('METADATEN', {})
        
        if not metadaten:
            item = QTreeWidgetItem(["Keine METADATEN vorhanden"])
            item.setFlags(Qt.NoItemFlags)
            self.field_tree.addTopLevelItem(item)
            return
        
        # Zeige METADATEN-Ebenen: TEMPLATES, ROOT_CONTROLS, CONTROL_PROPERTIES
        for meta_key in ['TEMPLATES', 'ROOT_CONTROLS', 'CONTROL_PROPERTIES']:
            if meta_key not in metadaten:
                continue
            
            # Parent-Item für METADATEN-Ebene
            icon = {'TEMPLATES': '🔧', 'ROOT_CONTROLS': '⚙️', 'CONTROL_PROPERTIES': '🎨'}.get(meta_key, '📁')
            parent_item = QTreeWidgetItem([f"{icon} {meta_key}"])
            parent_item.setData(0, Qt.UserRole, {'type': 'template_folder', 'meta_key': meta_key})
            parent_item.setExpanded(True)
            self.field_tree.addTopLevelItem(parent_item)
            
            # Controls/Items darunter
            items_dict = metadaten[meta_key]
            sorted_items = sorted(items_dict.items())
            
            for item_key, item_data in sorted_items:
                # Label als Name
                if isinstance(item_data, dict):
                    item_label = item_data.get('label', item_key)
                else:
                    item_label = item_key
                
                display_text = f"📄 {item_label}"
                
                child_item = QTreeWidgetItem([display_text])
                child_item.setData(0, Qt.UserRole, {
                    'type': 'template_control',
                    'meta_key': meta_key,
                    'item_key': item_key
                })
                parent_item.addChild(child_item)
                
        logger.info(f"  ✅ Template-Struktur geladen: {len(metadaten)} Ebenen")
                
    def _on_tree_item_clicked(self, item, column):
        """Handler: Tree-Item angeklickt"""
        if not item:
            return
            
        item_data = item.data(0, Qt.UserRole)
        if not item_data:
            return
            
        item_type = item_data.get('type')
        
        # TEMPLATE-MODUS: Template-Folders und Template-Controls
        if item_type == 'template_folder':
            # Template-Folder angeklickt → Info anzeigen
            meta_key = item_data['meta_key']
            logger.info(f"📁 Template-Folder ausgewählt: {meta_key}")
            icon = {'TEMPLATES': '🔧', 'ROOT_CONTROLS': '⚙️', 'CONTROL_PROPERTIES': '🎨'}.get(meta_key, '📁')
            self.right_header.setText(f"{icon} {meta_key}")
            self._clear_control_editor()
            return
            
        elif item_type == 'template_control':
            # Template-Control angeklickt → Editor anzeigen
            meta_key = item_data['meta_key']
            item_key = item_data['item_key']
            logger.info(f"📄 Template-Control ausgewählt: {meta_key}.{item_key}")
            
            # Header aktualisieren
            metadaten = self.view_data['METADATEN'].get(meta_key, {})
            item_data_dict = metadaten.get(item_key, {})
            item_label = item_data_dict.get('label', item_key) if isinstance(item_data_dict, dict) else item_key
            
            icon = {'TEMPLATES': '🔧', 'ROOT_CONTROLS': '⚙️', 'CONTROL_PROPERTIES': '🎨'}.get(meta_key, '📄')
            self.right_header.setText(f"{icon} {item_label}")
            
            # Template-Control Editor anzeigen
            self._build_template_control_editor(meta_key, item_key, item_data_dict)
            return
        
        # VIEW-MODUS: Normale Folders und Controls
        if item_type == 'folder':
            # Folder angeklickt → NICHTS anzeigen rechts (keine Editor-Felder)
            field_type = item_data['field_type']
            logger.info(f"📁 Folder ausgewählt: {field_type}")
            self.right_header.setText(f"📁 {field_type}")
            
            # Rechte Seite leeren
            self._clear_control_editor()
            
        elif item_type == 'control':
            # Einzelnes Control angeklickt → Zeige nur dieses Control
            field_type = item_data['field_type']
            control_key = item_data['control_key']
            logger.info(f"📄 Control ausgewählt: {field_type}.{control_key}")
            
            # Header aktualisieren
            view_table = self.view_data['ROOT'].get('VIEW_TABLE', '')
            table_key = view_table.upper()
            metadaten = self.view_data['METADATEN'].get(table_key, {})
            control_data = metadaten.get(field_type, {}).get(control_key, {})
            control_label = control_data.get('label', 'Unbenannt')
            guid_short = control_key[:8] if len(control_key) > 8 else control_key
            
            self.right_header.setText(f"📄 {control_label} ({guid_short})")
            
            # Nur dieses eine Control anzeigen
            self._build_single_control_editor(field_type, control_key, control_data)
    
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
        view_table = self.view_data['ROOT'].get('VIEW_TABLE', '')
        table_key = view_table.upper()
        metadaten = self.view_data['METADATEN'].get(table_key, {})
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
        
    def _build_single_control_editor(self, field_type, control_key, control_data):
        """Baut Control-Editor für EINZELNES Control"""
        # Alte Widgets entfernen
        while self.control_editor_layout.count():
            child = self.control_editor_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # GroupBox für Control erstellen
        group = self._create_control_group(field_type, control_key, control_data)
        self.control_editor_layout.addWidget(group)
        
        # Stretch am Ende
        self.control_editor_layout.addStretch()
        
    def _on_items_reordered(self):
        """Handler: Items per Drag & Drop neu sortiert"""
        logger.info("🔄 Controls neu sortiert per Drag & Drop")
        
        # View-Table holen
        view_table = self.view_data['ROOT'].get('VIEW_TABLE', '')
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
                if table_key in self.view_data['METADATEN']:
                    if field_type in self.view_data['METADATEN'][table_key]:
                        if control_key in self.view_data['METADATEN'][table_key][field_type]:
                            self.view_data['METADATEN'][table_key][field_type][control_key]['display_order'] = j
                            logger.info(f"  ✅ {control_key}.display_order = {j}")
                            
        logger.info("✅ display_order für alle Controls aktualisiert")
        
    def _update_display_order_from_tree(self):
        """Aktualisiert display_order aus TreeView-Reihenfolge (für Speichern)"""
        logger.info("🔄 Aktualisiere display_order aus TreeView...")
        
        # View-Table holen
        view_table = self.view_data['ROOT'].get('VIEW_TABLE', '')
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
                if table_key in self.view_data['METADATEN']:
                    if field_type in self.view_data['METADATEN'][table_key]:
                        if control_key in self.view_data['METADATEN'][table_key][field_type]:
                            self.view_data['METADATEN'][table_key][field_type][control_key]['display_order'] = j
                            
        logger.info("  ✅ display_order aus Tree übernommen")
        
    def _create_control_group(self, field_type, control_key, control_data):
        """Erstellt GroupBox für einzelnes Control"""
        group = QGroupBox(f"Control: {control_key}")
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
        
        # Control-Properties anzeigen (jetzt Dictionary mit property_key als Key)
        # Sortieren nach display_order
        sorted_props = sorted(
            self.control_properties.items(),
            key=lambda item: item[1].get('display_order', 999)
        )
        
        for property_key, prop in sorted_props:
            label = prop['label']
            prop_control_type = prop.get('control_type', 'text')
            
            # SPEZIAL: configs als nested Editor
            if property_key == 'configs':
                configs_widget = self._create_configs_editor(field_type, control_key, control_data)
                layout.addRow(f"{label}:", configs_widget)
                continue
            
            # Widget erstellen
            if prop_control_type == 'checkbox':
                widget_input = QCheckBox()
                value = control_data.get(property_key, False)
                widget_input.setChecked(bool(value))
                # Signal: Änderung → sofort in view_data schreiben
                widget_input.stateChanged.connect(
                    lambda state, ft=field_type, ck=control_key, pk=property_key: 
                    self._on_control_property_changed(ft, ck, pk, state == Qt.Checked)
                )
            elif prop_control_type == 'number':
                widget_input = QSpinBox()
                widget_input.setRange(0, 9999)
                value = control_data.get(property_key, 0)
                widget_input.setValue(int(value))
                # Signal: Wert geändert → sofort in view_data schreiben
                widget_input.valueChanged.connect(
                    lambda val, ft=field_type, ck=control_key, pk=property_key: 
                    self._on_control_property_changed(ft, ck, pk, val)
                )
            elif prop_control_type == 'dropdown':
                widget_input = QComboBox()
                options = prop.get('options', [])
                widget_input.addItems(options)
                value = control_data.get(property_key, '')
                index = widget_input.findText(str(value))
                if index >= 0:
                    widget_input.setCurrentIndex(index)
                # Signal: Text geändert → sofort in view_data schreiben
                widget_input.currentTextChanged.connect(
                    lambda text, ft=field_type, ck=control_key, pk=property_key: 
                    self._on_control_property_changed(ft, ck, pk, text)
                )
            else:
                widget_input = QLineEdit()
                value = control_data.get(property_key, '')
                widget_input.setText(str(value) if value is not None else '')
                # Signal: Text editiert → sofort in view_data schreiben
                widget_input.textChanged.connect(
                    lambda text, ft=field_type, ck=control_key, pk=property_key: 
                    self._on_control_property_changed(ft, ck, pk, text)
                )
                
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
        view_table = self.view_data['ROOT'].get('VIEW_TABLE', '')
        if not view_table:
            logger.warning("⚠️ VIEW_TABLE nicht gesetzt - Änderung nicht gespeichert")
            return
            
        table_key = view_table.upper()
        
        # Pfad zu Property sicherstellen
        if table_key not in self.view_data['METADATEN']:
            self.view_data['METADATEN'][table_key] = {}
        if field_type not in self.view_data['METADATEN'][table_key]:
            self.view_data['METADATEN'][table_key][field_type] = {}
        if control_key not in self.view_data['METADATEN'][table_key][field_type]:
            self.view_data['METADATEN'][table_key][field_type][control_key] = {}
            
        # Wert schreiben
        self.view_data['METADATEN'][table_key][field_type][control_key][property_key] = value
        
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
        vt_table.setPlaceholderText('z.B. sys_viewdaten')
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
        view_table = self.view_data['ROOT'].get('VIEW_TABLE', '')
        if not view_table:
            logger.warning("⚠️ VIEW_TABLE nicht gesetzt - Änderung nicht gespeichert")
            return
            
        table_key = view_table.upper()
        
        # Pfad sicherstellen
        if table_key not in self.view_data['METADATEN']:
            self.view_data['METADATEN'][table_key] = {}
        if field_type not in self.view_data['METADATEN'][table_key]:
            self.view_data['METADATEN'][table_key][field_type] = {}
        if control_key not in self.view_data['METADATEN'][table_key][field_type]:
            self.view_data['METADATEN'][table_key][field_type][control_key] = {}
        if 'configs' not in self.view_data['METADATEN'][table_key][field_type][control_key]:
            self.view_data['METADATEN'][table_key][field_type][control_key]['configs'] = {}
        if config_type not in self.view_data['METADATEN'][table_key][field_type][control_key]['configs']:
            self.view_data['METADATEN'][table_key][field_type][control_key]['configs'][config_type] = {}
        
        # Wert schreiben
        self.view_data['METADATEN'][table_key][field_type][control_key]['configs'][config_type][config_field] = value
        
        logger.info(f"  ✏️ {control_key}.configs.{config_type}.{config_field} = {value}")
        
    def _add_field(self):
        """Fügt neues Control/Item zum ausgewählten Folder hinzu"""
        # Ausgewähltes Item holen
        current_item = self.field_tree.currentItem()
        if not current_item:
            msg = "Bitte wähle zuerst einen Folder aus!" if self.edit_mode == 'template' else "Bitte wähle zuerst einen Folder (controls/standard_controls) aus!"
            QMessageBox.warning(self, "Warnung", msg)
            return
            
        # Item-Daten holen
        item_data = current_item.data(0, Qt.UserRole)
        if not item_data:
            return
        
        item_type = item_data.get('type')
        
        # TEMPLATE-MODUS
        if self.edit_mode == 'template':
            # Wenn Template-Control ausgewählt, zum Parent wechseln
            if item_type == 'template_control':
                current_item = current_item.parent()
                item_data = current_item.data(0, Qt.UserRole)
                item_type = item_data.get('type')
                
            if item_type != 'template_folder':
                QMessageBox.warning(
                    self,
                    "Warnung",
                    "Bitte wähle einen Template-Folder aus (TEMPLATES, ROOT_CONTROLS, etc.)!"
                )
                return
                
            meta_key = item_data['meta_key']
            self._add_template_item(meta_key)
            return
        
        # VIEW-MODUS
        # Wenn Control ausgewählt, zum Parent wechseln
        if item_type == 'control':
            current_item = current_item.parent()
            item_data = current_item.data(0, Qt.UserRole)
            item_type = item_data.get('type')
            
        if item_type != 'folder':
            QMessageBox.warning(
                self,
                "Warnung",
                "Bitte wähle einen Folder (controls/standard_controls) aus!"
            )
            return
            
        field_type = item_data['field_type']
        
        # Jetzt Control hinzufügen
        self._add_control(field_type)
        
    def _remove_field(self):
        """Entfernt ausgewähltes Control/Item"""
        # Ausgewähltes Item holen
        current_item = self.field_tree.currentItem()
        if not current_item:
            QMessageBox.warning(
                self,
                "Warnung",
                "Bitte wähle zuerst ein Control/Item aus!"
            )
            return
            
        # Item-Daten holen
        item_data = current_item.data(0, Qt.UserRole)
        if not item_data:
            return
        
        item_type = item_data.get('type')
        
        # TEMPLATE-MODUS
        if self.edit_mode == 'template':
            # Nur Template-Controls können gelöscht werden, keine Folder
            if item_type != 'template_control':
                QMessageBox.warning(
                    self,
                    "Warnung",
                    "Bitte wähle ein Template-Item zum Löschen aus (nicht den Folder)!"
                )
                return
                
            meta_key = item_data['meta_key']
            item_key = item_data['item_key']
            
            # Löschen bestätigen
            reply = QMessageBox.question(
                self,
                "Template-Item löschen",
                f"Template-Item '{item_key}' wirklich löschen?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
                
            # Aus METADATEN entfernen
            if meta_key in self.view_data['METADATEN']:
                if item_key in self.view_data['METADATEN'][meta_key]:
                    del self.view_data['METADATEN'][meta_key][item_key]
                    logger.info(f"🗑️ Template-Item '{item_key}' aus {meta_key} gelöscht")
                    
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
        view_table = self.view_data['ROOT'].get('VIEW_TABLE', '')
        table_key = view_table.upper()
        
        if table_key in self.view_data['METADATEN']:
            if field_type in self.view_data['METADATEN'][table_key]:
                if control_key in self.view_data['METADATEN'][table_key][field_type]:
                    del self.view_data['METADATEN'][table_key][field_type][control_key]
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
        if meta_key in self.view_data['METADATEN']:
            if item_key in self.view_data['METADATEN'][meta_key]:
                QMessageBox.warning(
                    self,
                    "Warnung",
                    f"Item '{item_key}' existiert bereits in {meta_key}!"
                )
                return
        
        # Standard-Struktur basierend auf meta_key
        if meta_key == 'TEMPLATES':
            # Template für neue Templates: Kopiere view_text als Basis
            if 'view_text' in self.view_data['METADATEN'][meta_key]:
                new_item_data = self.view_data['METADATEN'][meta_key]['view_text'].copy()
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
        if meta_key not in self.view_data['METADATEN']:
            self.view_data['METADATEN'][meta_key] = {}
            
        self.view_data['METADATEN'][meta_key][item_key] = new_item_data
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
        view_table = self.view_data['ROOT'].get('VIEW_TABLE', '')
        table_key = view_table.upper()
        
        if table_key not in self.view_data['METADATEN']:
            self.view_data['METADATEN'][table_key] = {}
        if field_type not in self.view_data['METADATEN'][table_key]:
            self.view_data['METADATEN'][table_key][field_type] = {}
            
        # Template-Daten mit GUID als Key speichern
        self.view_data['METADATEN'][table_key][field_type][control_guid] = template_data
        
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
            view_table = self.view_data['ROOT'].get('VIEW_TABLE', '')
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
            if table_key not in self.view_data['METADATEN']:
                self.view_data['METADATEN'][table_key] = {}
                logger.info(f"  ✅ METADATEN[{table_key}] erstellt")
                
            # controls erstellen wenn nicht vorhanden
            if 'controls' not in self.view_data['METADATEN'][table_key]:
                self.view_data['METADATEN'][table_key]['controls'] = {}
                logger.info(f"  ✅ controls erstellt")
                
            # standard_controls erstellen wenn nicht vorhanden
            if 'standard_controls' not in self.view_data['METADATEN'][table_key]:
                self.view_data['METADATEN'][table_key]['standard_controls'] = {}
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
                self.view_data['METADATEN'][table_key]['standard_controls']['dummy'] = dummy_control
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
                    self.view_data['ROOT'][control_key] = widget.isChecked()
                elif isinstance(widget, QComboBox):
                    self.view_data['ROOT'][control_key] = widget.currentText()
                else:
                    self.view_data['ROOT'][control_key] = widget.text()
            
            # SCHRITT 0.5: Prüfe ob METADATEN leer ist und erstelle Struktur mit Dummies
            view_table = self.view_data['ROOT'].get('VIEW_TABLE', '')
            if view_table:
                table_key = view_table.upper()
                
                # Wenn METADATEN leer oder Tabelle nicht vorhanden
                if not self.view_data.get('METADATEN') or table_key not in self.view_data['METADATEN']:
                    logger.info(f"  📦 Erstelle Basis-Struktur für Tabelle '{table_key}'...")
                    
                    if 'METADATEN' not in self.view_data:
                        self.view_data['METADATEN'] = {}
                    
                    # Struktur mit controls und standard_controls erstellen
                    self.view_data['METADATEN'][table_key] = {
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
            self.view_db.data = self.view_data
            self.view_db.save_all_values()
            
            logger.info("✅ View-Daten gespeichert")
            
            # Signal emittieren
            self.save_completed.emit()
            
            QMessageBox.information(self, "Erfolg", "View-Daten erfolgreich gespeichert!")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern:\n{e}")
