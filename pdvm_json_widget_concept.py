# -*- coding: utf-8 -*-
"""
PdvmJsonWidget - Konzept für strukturierten JSON-Editor

Dieses Widget ermöglicht das Editieren strukturierter JSON-Daten wie:
- Framedaten (ICs, Metadaten)
- Viewdaten (Views, Parameter)
- Andere strukturierte Konfigurationsdaten

Grundprinzipien:
1. Schema-basierte Editierung (Grundstruktur vorgeben)
2. Dropdown-Parameter für bestimmte Felder
3. Dynamische Bereiche (ICs, gleichartige Pakete)
4. Automatische IC-Generierung
5. Frame3-Integration
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QTreeWidget, QTreeWidgetItem, QPushButton, QSplitter,
    QDialog, QLineEdit, QComboBox, QTextEdit, QLabel,
    QFrame, QMessageBox, QTabWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
import json
import uuid

logger = logging.getLogger(__name__)

class PdvmJsonWidget(QWidget):
    """
    Hauptwidget für strukturierte JSON-Editierung
    
    Verwendet PdvmDialogWidget als Basis:
    - ViewGuid über Framedaten für Auswahl
    - Mode 1 für Editierung
    """
    
    data_changed = pyqtSignal()  # Signal wenn Daten geändert wurden
    
    def __init__(self, schema, initial_data=None, parent=None):
        super().__init__(parent)
        
        # Schema für Datenstruktur
        self.schema = schema
        self.data = initial_data if initial_data is not None else {}
        
        # UI-Komponenten
        self.tree_widget = None
        self.detail_widget = None
        
        self.init_ui()
        if self.schema:
            self.load_schema()
        if self.data:
            self.load_data()
    
    def init_ui(self):
        """Initialisiert das UI mit Baum-Detail-Ansicht"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("JSON-Struktur Editor")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)
        
        # Splitter für Baum + Detail
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Linke Seite: Baum-Ansicht der Struktur
        self.tree_widget = PdvmJsonTreeWidget(self)
        self.tree_widget.item_selected.connect(self.on_item_selected)
        splitter.addWidget(self.tree_widget)
        
        # Rechte Seite: Detail-Editor
        self.detail_widget = PdvmJsonDetailWidget(self)
        self.detail_widget.value_changed.connect(self.on_value_changed)
        splitter.addWidget(self.detail_widget)
        
        # Verhältnis 1:2 (Baum:Detail)
        splitter.setSizes([300, 600])
        
        # Buttons
        button_layout = QHBoxLayout()
        
        btn_add = QPushButton("Bereich hinzufügen")
        btn_add.clicked.connect(self.add_section)
        button_layout.addWidget(btn_add)
        
        btn_validate = QPushButton("Validieren")
        btn_validate.clicked.connect(self.validate_data)
        button_layout.addWidget(btn_validate)
        
        btn_save = QPushButton("Speichern")
        btn_save.clicked.connect(self.save_data)
        button_layout.addWidget(btn_save)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def load_schema(self):
        """Lädt das Schema für die Datenstruktur"""
        # Schema ist bereits im Konstruktor gesetzt
        if self.schema and self.tree_widget:
            self.tree_widget.load_data(self.data, self.schema)
    
    def get_framedaten_schema(self):
        """Schema für Framedaten-Editierung"""
        return {
            "type": "object",
            "properties": {
                "metadata": {
                    "type": "object",
                    "properties": {
                        "root_table": {"type": "string", "dropdown": ["persondaten", "finanzdaten", "unternehmen"]},
                        "view_guid": {"type": "string", "format": "uuid"},
                        "viewtable": {
                            "type": "object",
                            "properties": {
                                "guid": {"type": "string", "format": "uuid"}
                            }
                        }
                    }
                },
                "input_controls": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"},
                            "type": {"type": "string", "dropdown": ["text", "datetime", "dropdown", "viewtable"]},
                            "label": {"type": "string"},
                            "abdatum": {"type": "boolean"},
                            "historical": {"type": "boolean"},
                            "guid_source": {"type": "string"},
                            "dropdown": {"type": "string"},
                            "help": {"type": "string"}
                        },
                        "required": ["key", "type", "label"]
                    }
                }
            },
            "required": ["metadata", "input_controls"]
        }
    
    def get_viewdaten_schema(self):
        """Schema für Viewdaten-Editierung"""
        return {
            "type": "object",
            "properties": {
                "view_name": {"type": "string"},
                "description": {"type": "string"},
                "filters": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field": {"type": "string"},
                            "operator": {"type": "string", "dropdown": ["=", "!=", "LIKE", ">", "<"]},
                            "value": {"type": "string"}
                        }
                    }
                },
                "columns": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field": {"type": "string"},
                            "title": {"type": "string"},
                            "width": {"type": "integer"},
                            "sortable": {"type": "boolean"}
                        }
                    }
                }
            }
        }
    
    def get_default_schema(self):
        """Standard-Schema für generische JSON-Editierung"""
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": True
        }
    
    def load_data(self):
        """Lädt die aktuellen JSON-Daten"""
        if self.tree_widget and self.schema:
            self.tree_widget.load_data(self.data, self.schema)
    
    def get_sample_data(self):
        """Beispiel-Daten für Demonstration"""
        return {
            "metadata": {
                "root_table": "persondaten",
                "view_guid": "0d10a0d0-b1a5-4544-b284-e8a09ca979b5",
                "viewtable": {
                    "guid": "86aa89c0-43e3-4317-8df6-03dee6f63689"
                }
            },
            "input_controls": [
                {
                    "key": "persondaten_PERSDATEN_ANREDE",
                    "type": "dropdown",
                    "label": "Anrede",
                    "abdatum": True,
                    "historical": True,
                    "dropdown": "dropdowndaten",
                    "help": "beschreibungen"
                },
                {
                    "key": "persondaten_PERSDATEN_VORNAME",
                    "type": "text",
                    "label": "Vorname",
                    "abdatum": True,
                    "historical": True,
                    "help": "beschreibungen"
                }
            ]
        }
    
    def on_item_selected(self, path, value, schema_def):
        """Callback wenn ein Item im Baum ausgewählt wird"""
        self.detail_widget.show_item(path, value, schema_def)
    
    def on_value_changed(self, path, new_value):
        """Callback wenn ein Wert geändert wird"""
        self.set_value_at_path(self.data, path, new_value)
        self.tree_widget.update_item(path, new_value)
        self.data_changed.emit()
    
    def get_json_data(self):
        """Gibt die aktuellen JSON-Daten zurück"""
        return self.data
    
    def set_value_at_path(self, data, path, value):
        """Setzt einen Wert an einem bestimmten Pfad in den Daten"""
        parts = path.split('.')
        current = data
        for part in parts[:-1]:
            if '[' in part and ']' in part:
                # Array-Index
                key, index_str = part.split('[')
                index = int(index_str.rstrip(']'))
                current = current[key][index]
            else:
                current = current[part]
        
        final_key = parts[-1]
        if '[' in final_key and ']' in final_key:
            key, index_str = final_key.split('[')
            index = int(index_str.rstrip(']'))
            current[key][index] = value
        else:
            current[final_key] = value
    
    def add_section(self):
        """Fügt einen neuen Bereich hinzu"""
        # TODO: Dialog zur Auswahl des Bereichstyps
        dialog = AddSectionDialog(self.schema, self)
        if dialog.exec_() == QDialog.Accepted:
            section_type, section_data = dialog.get_section_data()
            self.add_section_to_data(section_type, section_data)
    
    def add_section_to_data(self, section_type, section_data):
        """Fügt Bereichsdaten zu den Hauptdaten hinzu"""
        if section_type == "input_control":
            if "input_controls" not in self.data:
                self.data["input_controls"] = []
            self.data["input_controls"].append(section_data)
            self.tree_widget.load_data(self.data, self.schema)
    
    def validate_data(self):
        """Validiert die Daten gegen das Schema"""
        # TODO: JSON-Schema-Validierung
        errors = []
        self.validate_object(self.data, self.schema, "", errors)
        
        if errors:
            error_msg = "Validierungsfehler:\n" + "\n".join(errors)
            QMessageBox.warning(self, "Validierung", error_msg)
        else:
            QMessageBox.information(self, "Validierung", "Daten sind valide!")
    
    def validate_object(self, data, schema, path, errors):
        """Rekursive Validierung eines Objekts"""
        # Vereinfachte Validierung - kann erweitert werden
        if schema.get("type") == "object":
            required = schema.get("required", [])
            for req_field in required:
                if req_field not in data:
                    errors.append(f"{path}.{req_field}: Pflichtfeld fehlt")
    
    def save_data(self):
        """Speichert die Daten"""
        # TODO: Speicherung in Datenbank
        try:
            json_str = json.dumps(self.data, indent=2)
            logger.info(f"Daten würden gespeichert werden:\n{json_str}")
            QMessageBox.information(self, "Speichern", "Daten erfolgreich gespeichert!")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern: {e}")


class PdvmJsonTreeWidget(QTreeWidget):
    """Baum-Widget zur Anzeige der JSON-Struktur"""
    
    item_selected = pyqtSignal(str, object, object)  # path, value, schema
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHeaderLabels(["Feld", "Wert"])
        self.itemClicked.connect(self.on_item_clicked)
        
        self.data = {}
        self.schema = {}
    
    def load_data(self, data, schema):
        """Lädt Daten in den Baum"""
        self.clear()
        self.data = data
        self.schema = schema
        
        self.build_tree_recursive(data, schema, None, "")
        self.expandAll()
    
    def build_tree_recursive(self, data, schema, parent_item, path):
        """Baut den Baum rekursiv auf"""
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                item = QTreeWidgetItem([key, self.format_value(value)])
                item.setData(0, Qt.UserRole, current_path)
                
                if parent_item:
                    parent_item.addChild(item)
                else:
                    self.addTopLevelItem(item)
                
                # Schema für dieses Feld
                field_schema = {}
                if schema and "properties" in schema:
                    field_schema = schema["properties"].get(key, {})
                
                # Rekursion für verschachtelte Strukturen
                if isinstance(value, (dict, list)):
                    self.build_tree_recursive(value, field_schema, item, current_path)
        
        elif isinstance(data, list):
            for i, value in enumerate(data):
                current_path = f"{path}[{i}]"
                item = QTreeWidgetItem([f"[{i}]", self.format_value(value)])
                item.setData(0, Qt.UserRole, current_path)
                
                if parent_item:
                    parent_item.addChild(item)
                else:
                    self.addTopLevelItem(item)
                
                # Schema für Array-Items
                items_schema = schema.get("items", {}) if schema else {}
                
                if isinstance(value, (dict, list)):
                    self.build_tree_recursive(value, items_schema, item, current_path)
    
    def format_value(self, value):
        """Formatiert einen Wert für die Anzeige"""
        if isinstance(value, (dict, list)):
            return f"({type(value).__name__})"
        elif isinstance(value, str) and len(value) > 50:
            return value[:47] + "..."
        else:
            return str(value)
    
    def on_item_clicked(self, item):
        """Callback wenn ein Item geklickt wird"""
        path = item.data(0, Qt.UserRole)
        if path:
            value = self.get_value_at_path(self.data, path)
            schema_def = self.get_schema_at_path(self.schema, path)
            self.item_selected.emit(path, value, schema_def)
    
    def get_value_at_path(self, data, path):
        """Holt einen Wert an einem bestimmten Pfad"""
        parts = path.split('.')
        current = data
        for part in parts:
            if '[' in part and ']' in part:
                key, index_str = part.split('[')
                index = int(index_str.rstrip(']'))
                current = current[key][index]
            else:
                current = current[part]
        return current
    
    def get_schema_at_path(self, schema, path):
        """Holt die Schema-Definition an einem bestimmten Pfad"""
        parts = path.split('.')
        current = schema
        for part in parts:
            if '[' in part and ']' in part:
                # Array-Item - verwende items-Schema
                current = current.get("items", {})
            else:
                current = current.get("properties", {}).get(part, {})
        return current
    
    def update_item(self, path, new_value):
        """Aktualisiert ein Item im Baum"""
        # TODO: Item finden und aktualisieren
        pass


class PdvmJsonDetailWidget(QWidget):
    """Detail-Widget zur Bearbeitung einzelner Felder"""
    
    value_changed = pyqtSignal(str, object)  # path, new_value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_path = ""
        self.current_value = None
        self.current_schema = {}
        
        self.init_ui()
    
    def init_ui(self):
        """Initialisiert das UI"""
        layout = QVBoxLayout(self)
        
        # Pfad-Anzeige
        self.path_label = QLabel("Kein Feld ausgewählt")
        self.path_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.path_label)
        
        # Container für Editoren
        self.editor_frame = QFrame()
        self.editor_layout = QVBoxLayout(self.editor_frame)
        layout.addWidget(self.editor_frame)
        
        layout.addStretch()
    
    def show_item(self, path, value, schema_def):
        """Zeigt ein Item zur Bearbeitung an"""
        self.current_path = path
        self.current_value = value
        self.current_schema = schema_def
        
        self.path_label.setText(f"Feld: {path}")
        
        # Alten Editor entfernen
        self.clear_editor()
        
        # Neuen Editor erstellen
        self.create_editor(value, schema_def)
    
    def clear_editor(self):
        """Entfernt den aktuellen Editor"""
        while self.editor_layout.count():
            child = self.editor_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def create_editor(self, value, schema_def):
        """Erstellt den passenden Editor für den Wert"""
        field_type = schema_def.get("type", "string")
        dropdown_options = schema_def.get("dropdown")
        
        if dropdown_options:
            # Dropdown-Editor
            editor = QComboBox()
            editor.setEditable(True)
            # TODO: Dropdown-Optionen laden
            editor.addItems(dropdown_options if isinstance(dropdown_options, list) else [])
            if value:
                editor.setCurrentText(str(value))
            editor.currentTextChanged.connect(
                lambda text: self.value_changed.emit(self.current_path, text)
            )
        
        elif field_type == "boolean":
            # Boolean-Editor (Checkbox)
            editor = QComboBox()
            editor.addItems(["false", "true"])
            editor.setCurrentText(str(value).lower())
            editor.currentTextChanged.connect(
                lambda text: self.value_changed.emit(self.current_path, text == "true")
            )
        
        elif field_type in ["object", "array"]:
            # Strukturierte Daten - nur Anzeige
            editor = QTextEdit()
            editor.setPlainText(json.dumps(value, indent=2))
            editor.setReadOnly(True)
        
        else:
            # Text-Editor
            editor = QLineEdit()
            editor.setText(str(value) if value is not None else "")
            editor.textChanged.connect(
                lambda text: self.value_changed.emit(self.current_path, text)
            )
        
        self.editor_layout.addWidget(QLabel("Wert:"))
        self.editor_layout.addWidget(editor)
        
        # Schema-Info anzeigen
        if schema_def:
            info_text = QTextEdit()
            info_text.setPlainText(json.dumps(schema_def, indent=2))
            info_text.setMaximumHeight(100)
            info_text.setReadOnly(True)
            self.editor_layout.addWidget(QLabel("Schema:"))
            self.editor_layout.addWidget(info_text)


class AddSectionDialog(QDialog):
    """Dialog zum Hinzufügen neuer Bereiche"""
    
    def __init__(self, schema, parent=None):
        super().__init__(parent)
        self.schema = schema
        self.section_data = {}
        
        self.setWindowTitle("Bereich hinzufügen")
        self.setModal(True)
        self.resize(400, 300)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialisiert das UI"""
        layout = QVBoxLayout(self)
        
        # Bereichstyp-Auswahl
        layout.addWidget(QLabel("Bereichstyp:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["input_control", "filter", "column"])
        layout.addWidget(self.type_combo)
        
        # Eingabefelder für IC
        self.fields = {}
        
        layout.addWidget(QLabel("Key:"))
        self.fields['key'] = QLineEdit()
        layout.addWidget(self.fields['key'])
        
        layout.addWidget(QLabel("Type:"))
        self.fields['type'] = QComboBox()
        self.fields['type'].addItems(["text", "datetime", "dropdown", "viewtable"])
        layout.addWidget(self.fields['type'])
        
        layout.addWidget(QLabel("Label:"))
        self.fields['label'] = QLineEdit()
        layout.addWidget(self.fields['label'])
        
        # Buttons
        button_layout = QHBoxLayout()
        
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        button_layout.addWidget(btn_ok)
        
        btn_cancel = QPushButton("Abbrechen")
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)
        
        layout.addLayout(button_layout)
    
    def get_section_data(self):
        """Gibt die eingegebenen Bereichsdaten zurück"""
        section_type = self.type_combo.currentText()
        
        if section_type == "input_control":
            section_data = {
                "key": self.fields['key'].text(),
                "type": self.fields['type'].currentText(),
                "label": self.fields['label'].text(),
                "abdatum": True,
                "historical": True
            }
        else:
            section_data = {}
        
        return section_type, section_data


# Hauptfunktion für Tests
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    call_data = {
        'view_guid': '0d10a0d0-b1a5-4544-b284-e8a09ca979b5',
        'mode': 1,
        'data_type': 'framedaten'
    }
    
    widget = PdvmJsonWidget(call_data)
    widget.show()
    
    sys.exit(app.exec_())
