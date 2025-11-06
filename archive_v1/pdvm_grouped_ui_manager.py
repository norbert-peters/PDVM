# -*- coding: utf-8 -*-
"""
PDVM Grouped UI Manager
Implementiert echte UI-Gruppierung mit Tabs, Accordion und Sections
"""
import os
import sys
import logging
from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QScrollArea,
    QGroupBox, QFormLayout, QLabel, QPushButton, QFrame, 
    QSizePolicy, QSpacerItem, QStackedWidget,
    QSplitter, QTreeWidget, QTreeWidgetItem, QLineEdit, QComboBox,
    QSpinBox, QCheckBox, QDateTimeEdit, QTextEdit, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QFont, QPalette, QColor

# Import der optimierten Datenstruktur
from pdvm_optimized_data_manager import OptimizedDataManager, GroupDefinition

# Logger Setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class CollapsibleGroupBox(QGroupBox):
    """Ein zusammenklappbares GroupBox Widget"""
    
    toggled = pyqtSignal(bool)
    
    def __init__(self, title="", collapsed=False, parent=None):
        super().__init__(title, parent)
        self.setCheckable(True)
        self.setChecked(not collapsed)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                margin: 3px 0px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QGroupBox::indicator {
                width: 13px;
                height: 13px;
            }
            QGroupBox::indicator:unchecked {
                image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==);
            }
        """)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.content_widget)
        
        self.toggled.connect(self.on_toggled)
        self.content_widget.setVisible(not collapsed)
    
    def on_toggled(self, checked):
        """Handler für Zusammenklappen/Aufklappen"""
        self.content_widget.setVisible(checked)
        self.toggled.emit(checked)
    
    def addWidget(self, widget):
        """Fügt ein Widget zum Inhalt hinzu"""
        self.content_layout.addWidget(widget)
    
    def addLayout(self, layout):
        """Fügt ein Layout zum Inhalt hinzu"""
        self.content_layout.addLayout(layout)


class TabContainerWidget(QWidget):
    """Tab-Container mit eingebetteten gruppierten Frames"""
    
    def __init__(self, frame_layout, optimized_manager, parent=None):
        super().__init__(parent)
        self.frame_layout = frame_layout
        self.optimized_manager = optimized_manager
        self.tab_widgets = {}  # tab_id -> widget
        self.field_widgets = {}  # field_id -> widget
        
        self.setup_ui()
    
    def setup_ui(self):
        """Erstellt die Tab-Container-Oberfläche"""
        layout = QVBoxLayout(self)
        
        # Tab Widget erstellen
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Tabs erstellen
        for tab_def in self.frame_layout.tabs:
            self.create_tab(tab_def)
        
        self.setLayout(layout)
    
    def create_tab(self, tab_def):
        """Erstellt einen einzelnen Tab mit gruppiertem Frame"""
        # Tab-Widget erstellen
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        
        # Gruppen für diesen Tab holen
        groups = self.optimized_manager.get_groups_for_tab(tab_def.tab_id)
        
        if groups:
            # Gruppiertes UI für diesen Tab erstellen
            group_style = tab_def.grouping_style or "sections"
            
            grouped_widget = GroupedInputWidget(group_style)
            
            # Gruppen und Felder hinzufügen
            for group in groups:
                group_fields = self.optimized_manager.get_fields_in_group(group.get('group_id', ''))
                grouped_widget.add_group(group.get('group_id', ''), group.get('title', ''), group_fields)
            
            # Widget zum Layout hinzufügen
            tab_layout.addWidget(grouped_widget)
            
            # Field widgets sammeln
            if hasattr(grouped_widget, 'field_widgets'):
                self.field_widgets.update(grouped_widget.field_widgets)
        
        # Tab hinzufügen
        self.tab_widget.addTab(tab_widget, tab_def.title)
        self.tab_widgets[tab_def.tab_id] = tab_widget
    
    def get_all_field_values(self):
        """Sammelt alle Feldwerte aus allen Tabs"""
        values = {}
        for field_id, widget in self.field_widgets.items():
            if hasattr(widget, 'text'):
                values[field_id] = widget.text()
            elif hasattr(widget, 'currentText'):
                values[field_id] = widget.currentText()
            elif hasattr(widget, 'isChecked'):
                values[field_id] = widget.isChecked()
            elif hasattr(widget, 'value'):
                values[field_id] = widget.value()
        return values
    
    def set_field_values(self, values):
        """Setzt Feldwerte in allen Tabs"""
        for field_id, value in values.items():
            if field_id in self.field_widgets:
                widget = self.field_widgets[field_id]
                if hasattr(widget, 'setText'):
                    widget.setText(str(value))
                elif hasattr(widget, 'setCurrentText'):
                    widget.setCurrentText(str(value))
                elif hasattr(widget, 'setChecked'):
                    widget.setChecked(bool(value))
                elif hasattr(widget, 'setValue'):
                    widget.setValue(value)

class GroupedInputWidget(QWidget):
    """Widget für gruppierte Eingabefelder basierend auf einem Gruppierungsstil"""
    
    field_changed = pyqtSignal(str, object)  # field_key, value
    
    def __init__(self, group_style="sections", parent=None):
        super().__init__(parent)
        self.group_style = group_style  # sections, tabs, accordion, inline
        self.field_widgets = {}  # field_key -> widget
        self.groups_data = {}  # group_id -> group_definition
        self.fields_data = {}  # field_key -> field_configuration
        
        self.setup_ui()
    
    def setup_ui(self):
        """Initialisiert die UI basierend auf dem Gruppierungsstil"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        
        if self.group_style == "tabs":
            self.container = QTabWidget()
            self.container.setTabPosition(QTabWidget.North)
        elif self.group_style == "accordion":
            self.container = QScrollArea()
            self.container.setWidgetResizable(True)
            self.accordion_widget = QWidget()
            self.accordion_layout = QVBoxLayout(self.accordion_widget)
            self.container.setWidget(self.accordion_widget)
        elif self.group_style == "sections":
            self.container = QScrollArea()
            self.container.setWidgetResizable(True)
            self.sections_widget = QWidget()
            self.sections_layout = QVBoxLayout(self.sections_widget)
            self.container.setWidget(self.sections_widget)
        else:  # inline
            self.container = QWidget()
            self.inline_layout = QVBoxLayout(self.container)
        
        self.main_layout.addWidget(self.container)
    
    def configure_from_optimized_data(self, frame_config: Dict[str, Any]):
        """
        Konfiguriert das Widget basierend auf optimierten Frame-Daten
        
        Args:
            frame_config: Frame-Konfiguration aus OptimizedDataManager
        """
        self.groups_data = frame_config.get("groups", {})
        self.fields_data = {field["field_key"]: field for field in frame_config.get("fields", [])}
        
        # Felder nach Gruppen organisieren
        groups_with_fields = {}
        for field_config in frame_config.get("fields", []):
            group_id = field_config.get("group_id", "default")
            if group_id not in groups_with_fields:
                groups_with_fields[group_id] = []
            groups_with_fields[group_id].append(field_config)
        
        # Gruppen nach Sortierreihenfolge sortieren
        sorted_groups = sorted(
            groups_with_fields.items(),
            key=lambda x: self.groups_data.get(x[0], {}).get("sort_order", 999)
        )
        
        # UI für jede Gruppe erstellen
        for group_id, group_fields in sorted_groups:
            group_def = self.groups_data.get(group_id, {})
            self.create_group_ui(group_id, group_def, group_fields)
        
        # Stretchbereiche hinzufügen
        if self.group_style in ["sections", "accordion"]:
            if self.group_style == "sections":
                self.sections_layout.addStretch()
            else:
                self.accordion_layout.addStretch()
    
    def create_group_ui(self, group_id: str, group_def: Dict[str, Any], fields: List[Dict[str, Any]]):
        """
        Erstellt die UI für eine Gruppe
        
        Args:
            group_id: ID der Gruppe
            group_def: Gruppendefinition
            fields: Liste der Felder in dieser Gruppe
        """
        group_label = group_def.get("label", group_id.replace("_", " ").title())
        group_icon = group_def.get("icon", "")
        if group_icon:
            group_label = f"{group_icon} {group_label}"
        
        # Felder nach Sortierreihenfolge sortieren
        sorted_fields = sorted(fields, key=lambda f: f.get("sort_order", 999))
        
        if self.group_style == "tabs":
            self.create_tab_group(group_id, group_label, sorted_fields)
        elif self.group_style == "accordion":
            self.create_accordion_group(group_id, group_label, group_def, sorted_fields)
        elif self.group_style == "sections":
            self.create_section_group(group_id, group_label, sorted_fields)
        else:  # inline
            self.create_inline_group(group_id, group_label, sorted_fields)
    
    def create_tab_group(self, group_id: str, group_label: str, fields: List[Dict[str, Any]]):
        """Erstellt einen Tab für die Gruppe"""
        tab_widget = QWidget()
        tab_layout = QFormLayout(tab_widget)
        tab_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        for field_config in fields:
            self.add_field_to_layout(tab_layout, field_config)
        
        # Stretch-Widget hinzufügen
        stretch_widget = QWidget()
        stretch_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        tab_layout.addRow(stretch_widget)
        
        self.container.addTab(tab_widget, group_label)
    
    def create_accordion_group(self, group_id: str, group_label: str, group_def: Dict[str, Any], fields: List[Dict[str, Any]]):
        """Erstellt eine Accordion-Sektion für die Gruppe"""
        collapsible = group_def.get("collapsible", True)
        initially_collapsed = group_def.get("initially_collapsed", False)
        
        if collapsible:
            group_box = CollapsibleGroupBox(group_label, initially_collapsed)
        else:
            group_box = QGroupBox(group_label)
        
        group_layout = QFormLayout()
        group_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        for field_config in fields:
            self.add_field_to_layout(group_layout, field_config)
        
        if collapsible:
            group_box.content_layout.addLayout(group_layout)
        else:
            group_box.setLayout(group_layout)
        
        self.accordion_layout.addWidget(group_box)
    
    def create_section_group(self, group_id: str, group_label: str, fields: List[Dict[str, Any]]):
        """Erstellt eine Section für die Gruppe"""
        group_box = QGroupBox(group_label)
        group_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #c0c0c0;
                border-radius: 3px;
                margin: 5px 0px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        group_layout = QFormLayout(group_box)
        group_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        for field_config in fields:
            self.add_field_to_layout(group_layout, field_config)
        
        self.sections_layout.addWidget(group_box)
    
    def create_inline_group(self, group_id: str, group_label: str, fields: List[Dict[str, Any]]):
        """Erstellt eine Inline-Gruppe (alle Felder in einem Layout)"""
        # Trennlinie mit Label
        if len(self.field_widgets) > 0:  # Nicht beim ersten Durchgang
            separator = QFrame()
            separator.setFrameStyle(QFrame.HLine | QFrame.Sunken)
            self.inline_layout.addWidget(separator)
        
        group_label_widget = QLabel(group_label)
        group_label_widget.setStyleSheet("font-weight: bold; color: #2c5aa0; margin: 5px 0px;")
        self.inline_layout.addWidget(group_label_widget)
        
        for field_config in fields:
            self.add_field_to_layout(self.inline_layout, field_config)
    
    def add_field_to_layout(self, layout, field_config: Dict[str, Any]):
        """
        Fügt ein Feld zu einem Layout hinzu
        
        Args:
            layout: Das Layout (QFormLayout oder QVBoxLayout)
            field_config: Feld-Konfiguration
        """
        field_key = field_config["field_key"]
        field_type = field_config.get("field_type", "text")
        label_text = field_config.get("label", field_key)
        tooltip = field_config.get("tooltip", "")
        required = field_config.get("required", False)
        readonly = field_config.get("readonly", False)
        
        # Pflichtfeld-Markierung
        if required:
            label_text += " *"
        
        # Eingabe-Widget erstellen basierend auf Typ
        input_widget = self.create_input_widget(field_type, field_config)
        
        if tooltip:
            input_widget.setToolTip(tooltip)
        
        if readonly:
            input_widget.setEnabled(False)
        
        # Widget-Breite setzen
        ui_width_value = field_config.get("ui_width_value")
        if ui_width_value:
            input_widget.setFixedWidth(ui_width_value)
        
        # Einrückung anwenden
        ui_indent = field_config.get("ui_indent", 0)
        if ui_indent > 0:
            indent_label = "    " * (ui_indent // 20)  # 20px = 4 Leerzeichen
            label_text = indent_label + label_text
        
        # Widget speichern
        self.field_widgets[field_key] = input_widget
        
        # Change-Handler verbinden
        self.connect_change_handler(input_widget, field_key, field_type)
        
        # Zu Layout hinzufügen
        if isinstance(layout, QFormLayout):
            layout.addRow(label_text, input_widget)
        else:  # QVBoxLayout für inline
            field_container = QWidget()
            field_layout = QHBoxLayout(field_container)
            field_layout.setContentsMargins(20, 2, 5, 2)  # Einrückung für inline
            
            field_label = QLabel(label_text)
            field_label.setMinimumWidth(120)
            field_layout.addWidget(field_label)
            field_layout.addWidget(input_widget)
            field_layout.addStretch()
            
            layout.addWidget(field_container)
    
    def create_input_widget(self, field_type: str, field_config: Dict[str, Any]) -> QWidget:
        """
        Erstellt das passende Eingabe-Widget für den Feldtyp
        
        Args:
            field_type: Typ des Feldes
            field_config: Feld-Konfiguration
            
        Returns:
            Das passende Eingabe-Widget
        """
        if field_type == "text":
            widget = QLineEdit()
            
        elif field_type == "number":
            widget = QSpinBox()
            widget.setRange(-999999, 999999)
            min_val = field_config.get("min_value")
            max_val = field_config.get("max_value")
            if min_val is not None:
                widget.setMinimum(int(min_val))
            if max_val is not None:
                widget.setMaximum(int(max_val))
                
        elif field_type == "boolean":
            widget = QCheckBox()
            
        elif field_type == "datetime":
            widget = QDateTimeEdit()
            widget.setDisplayFormat("dd.MM.yyyy hh:mm")
            widget.setCalendarPopup(True)
            
        elif field_type == "dropdown":
            widget = QComboBox()
            # Dropdown-Optionen aus Konfiguration laden
            dropdown_config = field_config.get("dropdown_config", {})
            if dropdown_config.get("source_static_values"):
                for key, value in dropdown_config["source_static_values"].items():
                    widget.addItem(value, key)
            else:
                # Placeholder für Datenbank-Dropdowns
                widget.addItem("Lädt...", None)
                
        elif field_type == "viewtable":
            # Placeholder für ViewTable - würde normalerweise spezielles Widget verwenden
            widget = QLineEdit()
            widget.setPlaceholderText("ViewTable-Feld")
            
        else:  # Fallback
            widget = QLineEdit()
        
        return widget
    
    def connect_change_handler(self, widget: QWidget, field_key: str, field_type: str):
        """Verbindet Change-Handler für verschiedene Widget-Typen"""
        if isinstance(widget, QLineEdit):
            widget.textChanged.connect(lambda value: self.field_changed.emit(field_key, value))
        elif isinstance(widget, QSpinBox):
            widget.valueChanged.connect(lambda value: self.field_changed.emit(field_key, value))
        elif isinstance(widget, QCheckBox):
            widget.toggled.connect(lambda value: self.field_changed.emit(field_key, value))
        elif isinstance(widget, QComboBox):
            widget.currentTextChanged.connect(lambda value: self.field_changed.emit(field_key, widget.currentData()))
        elif isinstance(widget, QDateTimeEdit):
            widget.dateTimeChanged.connect(lambda value: self.field_changed.emit(field_key, value.toString()))
    
    def set_field_value(self, field_key: str, value: Any):
        """Setzt den Wert eines Feldes"""
        widget = self.field_widgets.get(field_key)
        if not widget:
            return
        
        if isinstance(widget, QLineEdit):
            widget.setText(str(value) if value else "")
        elif isinstance(widget, QSpinBox):
            widget.setValue(int(value) if value else 0)
        elif isinstance(widget, QCheckBox):
            widget.setChecked(bool(value))
        elif isinstance(widget, QComboBox):
            index = widget.findData(value)
            if index >= 0:
                widget.setCurrentIndex(index)
        # Weitere Widget-Typen nach Bedarf...
    
    def get_field_value(self, field_key: str) -> Any:
        """Holt den Wert eines Feldes"""
        widget = self.field_widgets.get(field_key)
        if not widget:
            return None
        
        if isinstance(widget, QLineEdit):
            return widget.text()
        elif isinstance(widget, QSpinBox):
            return widget.value()
        elif isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QComboBox):
            return widget.currentData()
        elif isinstance(widget, QDateTimeEdit):
            return widget.dateTime().toString()
        
        return None
    
    def get_all_values(self) -> Dict[str, Any]:
        """Holt alle Feld-Werte"""
        return {field_key: self.get_field_value(field_key) for field_key in self.field_widgets.keys()}
    
    def set_all_values(self, values: Dict[str, Any]):
        """Setzt alle Feld-Werte"""
        for field_key, value in values.items():
            self.set_field_value(field_key, value)
    
    def add_group(self, group_id: str, group_title: str, fields: List[Dict]):
        """
        Fügt eine Gruppe mit Feldern hinzu (vereinfachte Schnittstelle)
        
        Args:
            group_id: ID der Gruppe
            group_title: Titel der Gruppe
            fields: Liste der Feld-Konfigurationen
        """
        # Gruppe zur internen Datenstruktur hinzufügen
        self.groups_data[group_id] = {
            "title": group_title,
            "sort_order": len(self.groups_data)
        }
        
        # Felder hinzufügen und mit field_key versehen
        for field in fields:
            field_id = field.get('field_id', '')
            field_config = field.copy()
            field_config['field_key'] = field_id
            field_config['group_id'] = group_id
            self.fields_data[field_id] = field_config
        
        # UI für diese Gruppe erstellen
        self.create_group_ui(group_id, self.groups_data[group_id], fields)


class GroupedUITestWindow(QWidget):
    """Test-Fenster für verschiedene Gruppierungs-Stile"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎨 Test: Gruppierte UI-Stile")
        self.resize(1200, 800)
        
        # Optimized Data Manager für Test-Daten
        from pdvm_optimized_data_manager import create_sample_optimized_structure
        self.data_manager = create_sample_optimized_structure()
        
        self.setup_ui()
        self.load_test_data()
    
    def setup_ui(self):
        """Initialisiert die Test-UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("🎯 Gruppierte UI-Stile - Optimierte Datenstruktur")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; background-color: #e3f2fd;")
        layout.addWidget(header)
        
        # Style-Auswahl
        style_layout = QHBoxLayout()
        
        self.btn_tabs = QPushButton("📑 Tabs")
        self.btn_tabs.clicked.connect(lambda: self.switch_style("tabs"))
        style_layout.addWidget(self.btn_tabs)
        
        self.btn_accordion = QPushButton("📁 Accordion")
        self.btn_accordion.clicked.connect(lambda: self.switch_style("accordion"))
        style_layout.addWidget(self.btn_accordion)
        
        self.btn_sections = QPushButton("📋 Sections")
        self.btn_sections.clicked.connect(lambda: self.switch_style("sections"))
        style_layout.addWidget(self.btn_sections)
        
        self.btn_inline = QPushButton("📄 Inline")
        self.btn_inline.clicked.connect(lambda: self.switch_style("inline"))
        style_layout.addWidget(self.btn_inline)
        
        style_layout.addStretch()
        
        self.btn_get_values = QPushButton("💾 Werte anzeigen")
        self.btn_get_values.clicked.connect(self.show_values)
        style_layout.addWidget(self.btn_get_values)
        
        layout.addLayout(style_layout)
        
        # Haupt-Container
        self.main_container = QStackedWidget()
        layout.addWidget(self.main_container)
        
        # Info-Bereich
        self.info_label = QLabel("ℹ️ Wählen Sie einen Gruppierungs-Stil aus den Buttons oben")
        self.info_label.setStyleSheet("padding: 10px; background-color: #f5f5f5; border: 1px solid #ddd;")
        layout.addWidget(self.info_label)
    
    def switch_style(self, style: str):
        """Wechselt den Gruppierungs-Stil"""
        # Alle vorherigen Widgets entfernen
        while self.main_container.count() > 0:
            widget = self.main_container.widget(0)
            self.main_container.removeWidget(widget)
            widget.deleteLater()
        
        # Neues Widget mit gewähltem Stil erstellen
        self.current_grouped_widget = GroupedInputWidget(style)
        
        # Mit Daten konfigurieren
        frame_config = self.data_manager.get_frame_configuration("framedaten_person")
        self.current_grouped_widget.configure_from_optimized_data(frame_config)
        
        # Change-Handler verbinden
        self.current_grouped_widget.field_changed.connect(self.on_field_changed)
        
        # Zum Container hinzufügen
        self.main_container.addWidget(self.current_grouped_widget)
        self.main_container.setCurrentWidget(self.current_grouped_widget)
        
        # Info aktualisieren
        style_descriptions = {
            "tabs": "📑 Tabs: Jede Gruppe wird als Tab dargestellt",
            "accordion": "📁 Accordion: Zusammenklappbare Gruppen-Bereiche",
            "sections": "📋 Sections: Separate Gruppen-Boxen",
            "inline": "📄 Inline: Alle Felder linear mit Gruppen-Trennung"
        }
        
        self.info_label.setText(
            f"✅ Aktiver Stil: {style_descriptions[style]}\n"
            f"Gruppen: {len(frame_config['groups'])} | "
            f"Felder: {len(frame_config['fields'])}"
        )
        
        logger.info(f"UI-Stil gewechselt zu: {style}")
    
    def load_test_data(self):
        """Lädt Test-Daten"""
        # Automatisch Tabs-Stil laden
        self.switch_style("sections")
    
    def on_field_changed(self, field_key: str, value: Any):
        """Handler für Feld-Änderungen"""
        logger.debug(f"Feld geändert: {field_key} = {value}")
    
    def show_values(self):
        """Zeigt alle aktuellen Werte an"""
        if hasattr(self, 'current_grouped_widget'):
            values = self.current_grouped_widget.get_all_values()
            
            values_text = "📊 Aktuelle Werte:\n\n"
            for field_key, value in values.items():
                values_text += f"• {field_key}: {value}\n"
            
            # Einfaches Info-Fenster
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "Aktuelle Werte", values_text)


def test_grouped_ui():
    """Testet die gruppierte UI"""
    app = QApplication(sys.argv)
    
    try:
        window = GroupedUITestWindow()
        window.show()
        
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.exception("Fehler beim Testen der gruppierten UI:")
        print(f"\nFehler: {e}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    test_grouped_ui()
