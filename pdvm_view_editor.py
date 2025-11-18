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
        
        # Frame-Daten (Metadaten für Editor) bereits in framedaten_db
        self._load_frame_data()
        
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
        
    def _load_frame_data(self):
        """Lädt Frame-Daten (Editor-Metadaten) aus framedaten_db"""
        logger.info(f"📂 Lade Frame-Daten: {self.frame_guid}")
        
        # Daten bereits in framedaten_db geladen
        self.frame_data = self.framedaten_db.data
        
        # ROOT_CONTROLS extrahieren
        self.root_controls = self.frame_data.get('METADATEN', {}).get('ROOT_CONTROLS', [])
        self.control_properties = self.frame_data.get('METADATEN', {}).get('CONTROL_PROPERTIES', [])
        
        logger.info(f"  ✅ Frame-Daten geladen: {len(self.root_controls)} ROOT-Controls")
        
    def _load_templates(self):
        """Lädt Control-Templates aus bereits geladener Instanz"""
        logger.info(f"📂 Hole Control-Templates")
        
        # Daten sind bereits geladen (Constructor mit template_guid)
        self.templates = self.template_db.data.get('METADATEN', {}).get('TEMPLATES', {})
        
        logger.info(f"  ✅ {len(self.templates)} Templates geladen: {list(self.templates.keys())}")
        
    def _setup_ui(self):
        """Baut die UI auf"""
        logger.info("🔧 Baue View-Editor UI auf...")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
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
        """Tab 1: ROOT-Felder bearbeiten"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Scroll-Bereich für Felder
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        form_layout = QFormLayout(scroll_content)
        
        # ROOT-Controls dynamisch erstellen
        self.root_widgets = {}
        
        for control in sorted(self.root_controls, key=lambda x: x.get('display_order', 999)):
            control_key = control['control_key']
            label = control['label']
            control_type = control.get('control_type', 'text')
            readonly = control.get('readonly', False)
            
            # Widget erstellen
            if control_type == 'checkbox':
                widget_input = QCheckBox()
                value = self.view_data['ROOT'].get(control_key, False)
                widget_input.setChecked(bool(value))
                
                # Signal für NO_DATA: Struktur generieren wenn auf false gesetzt
                if control_key == 'NO_DATA':
                    widget_input.stateChanged.connect(self._on_no_data_changed)
            else:
                widget_input = QLineEdit()
                value = self.view_data['ROOT'].get(control_key, '')
                widget_input.setText(str(value))
                widget_input.setReadOnly(readonly)
            
            self.root_widgets[control_key] = widget_input
            form_layout.addRow(f"{label}:", widget_input)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return widget
        
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
                control_name = control_data.get('name', control_key)
                child_item = QTreeWidgetItem([f"📄 {control_name}"])
                child_item.setData(0, Qt.UserRole, {
                    'type': 'control',
                    'field_type': field_type,
                    'control_key': control_key
                })
                parent_item.addChild(child_item)
                
    def _on_tree_item_clicked(self, item, column):
        """Handler: Tree-Item angeklickt"""
        if not item:
            return
            
        item_data = item.data(0, Qt.UserRole)
        if not item_data:
            return
            
        item_type = item_data.get('type')
        
        if item_type == 'folder':
            # Folder angeklickt → Zeige alle Controls
            field_type = item_data['field_type']
            logger.info(f"📁 Folder ausgewählt: {field_type}")
            self.right_header.setText(f"📁 {field_type}")
            self._build_control_editor(field_type)
            
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
            control_name = control_data.get('name', control_key)
            
            self.right_header.setText(f"📄 {control_name}")
            
            # Nur dieses eine Control anzeigen
            self._build_single_control_editor(field_type, control_key, control_data)
        
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
        
        # Control-Properties anzeigen
        for prop in sorted(self.control_properties, key=lambda x: x.get('display_order', 999)):
            property_key = prop['property']
            label = prop['label']
            prop_control_type = prop.get('control_type', 'text')
            
            # Widget erstellen
            if prop_control_type == 'checkbox':
                widget_input = QCheckBox()
                value = control_data.get(property_key, False)
                widget_input.setChecked(bool(value))
            elif prop_control_type == 'number':
                widget_input = QSpinBox()
                widget_input.setRange(0, 999)
                value = control_data.get(property_key, 0)
                widget_input.setValue(int(value))
            elif prop_control_type == 'dropdown':
                widget_input = QComboBox()
                options = prop.get('options', [])
                widget_input.addItems(options)
                value = control_data.get(property_key, '')
                index = widget_input.findText(str(value))
                if index >= 0:
                    widget_input.setCurrentIndex(index)
            else:
                widget_input = QLineEdit()
                value = control_data.get(property_key, '')
                widget_input.setText(str(value) if value is not None else '')
                
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
        
    def _add_field(self):
        """Fügt neues Control zum ausgewählten Folder hinzu"""
        # Ausgewähltes Item holen
        current_item = self.field_tree.currentItem()
        if not current_item:
            QMessageBox.warning(
                self,
                "Warnung",
                "Bitte wähle zuerst einen Folder (controls/standard_controls) aus!"
            )
            return
            
        # Item-Daten holen
        item_data = current_item.data(0, Qt.UserRole)
        if not item_data:
            return
            
        # Wenn Control ausgewählt, zum Parent wechseln
        if item_data.get('type') == 'control':
            current_item = current_item.parent()
            item_data = current_item.data(0, Qt.UserRole)
            
        if item_data.get('type') != 'folder':
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
        """Entfernt ausgewähltes Control"""
        # Ausgewähltes Item holen
        current_item = self.field_tree.currentItem()
        if not current_item:
            QMessageBox.warning(
                self,
                "Warnung",
                "Bitte wähle zuerst ein Control aus!"
            )
            return
            
        # Item-Daten holen
        item_data = current_item.data(0, Qt.UserRole)
        if not item_data:
            return
            
        # Nur Controls können gelöscht werden, keine Folder
        if item_data.get('type') != 'control':
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
        
    def _add_control(self, field_type):
        """Fügt neues Control zu Feld hinzu"""
        # Control-Key abfragen
        control_key, ok = QInputDialog.getText(
            self,
            "Neues Control",
            "Control-Key (z.B. 'familienname'):"
        )
        
        if not ok or not control_key.strip():
            return
            
        control_key = control_key.strip().lower()
        
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
            
        # Template kopieren
        template_data = self.templates[template_name].copy()
        
        # In View-Daten einfügen
        view_table = self.view_data['ROOT'].get('VIEW_TABLE', '')
        table_key = view_table.upper()
        
        if table_key not in self.view_data['METADATEN']:
            self.view_data['METADATEN'][table_key] = {}
        if field_type not in self.view_data['METADATEN'][table_key]:
            self.view_data['METADATEN'][table_key][field_type] = {}
            
        self.view_data['METADATEN'][table_key][field_type][control_key] = template_data
        
        logger.info(f"✅ Control '{control_key}' zu {field_type} hinzugefügt")
        
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
                else:
                    self.view_data['ROOT'][control_key] = widget.text()
                    
            # Control-Widgets übernehmen
            if hasattr(self, 'control_widgets'):
                view_table = self.view_data['ROOT'].get('VIEW_TABLE', '')
                table_key = view_table.upper()
                
                for field_type, controls in self.control_widgets.items():
                    for control_key, properties in controls.items():
                        for property_key, widget in properties.items():
                            if isinstance(widget, QCheckBox):
                                value = widget.isChecked()
                            elif isinstance(widget, QSpinBox):
                                value = widget.value()
                            elif isinstance(widget, QComboBox):
                                value = widget.currentText()
                            else:
                                value = widget.text()
                                
                            # In View-Daten schreiben
                            if table_key in self.view_data['METADATEN']:
                                if field_type in self.view_data['METADATEN'][table_key]:
                                    if control_key in self.view_data['METADATEN'][table_key][field_type]:
                                        self.view_data['METADATEN'][table_key][field_type][control_key][property_key] = value
            
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
