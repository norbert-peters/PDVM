# -*- coding: utf-8 -*-
"""
PdvmPropertyInputControl - Autonomes Property-Input-Widget

TEMPLATE-GESTEUERT:
- Erhält control_def aus ROOT_CONTROLS (Template 55555...)
- Konfiguriert sich selbst basierend auf Control-Definition
- Steuert Label, Type, Format, Validierung, read_only, etc.

FEATURES:
- Label links, Input rechts (horizontales Layout)
- Type-basierte Widgets (string, int, float, bool, dropdown, etc.)
- read_only → Widget.setReadOnly(True) + graue Hintergrundfarbe
- display_order für Sortierung
- Dropdown-Options aus configs.dropdown
- Signal value_changed(property_name, new_value)

VERWENDUNG:
    control_def = {
        "name": "TABLE",
        "label": "Tabelle",
        "type": "string",
        "read_only": True,
        "display_order": 0
    }
    property_ic = PdvmPropertyInputControl(control_def, current_value)
    property_ic.value_changed.connect(self._on_property_changed)
"""

import logging
from typing import Any, Optional, Dict
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QLineEdit, QSpinBox, 
    QDoubleSpinBox, QCheckBox, QComboBox, QTextEdit
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPalette, QColor
from pdvm_central_systemsteuerung import get_gcs

logger = logging.getLogger(__name__)


class PdvmPropertyInputControl(QWidget):
    """
    Autonomes Property-Input-Widget basierend auf Template-Control-Definition.
    
    Signals:
        value_changed: Emitted wenn Wert geändert wurde (property_name: str, new_value: Any)
    """
    
    # Signal wenn Wert sich ändert
    value_changed = pyqtSignal(str, object)  # (property_name, new_value)
    
    def __init__(self, control_def: Dict[str, Any], current_value: Any = None, parent=None):
        """
        Initialisiert Property Input Control aus Template-Definition.
        
        Args:
            control_def: Control-Definition aus ROOT_CONTROLS (Template)
                         Format: {"name": "...", "label": "...", "type": "...", "read_only": bool, ...}
            current_value: Aktueller Wert des Properties (optional)
            parent: Parent Widget
        """
        super().__init__(parent)
        
        self.control_def = control_def
        self.property_name = control_def.get('name', 'unknown')
        self.property_type = control_def.get('type', 'string')
        self.is_read_only = control_def.get('read_only', False)
        self.current_value = current_value
        
        # Widget für Eingabe (wird in _create_input_widget erstellt)
        self.input_widget = None
        
        # UI erstellen
        self._init_ui()
        
        # Wert setzen (nach UI-Erstellung)
        if current_value is not None:
            self.set_value(current_value)
        
        logger.debug(f"PropertyInputControl erstellt: {self.property_name} (type={self.property_type}, read_only={self.is_read_only})")
    
    def _init_ui(self):
        """Erstellt UI-Struktur: Label + Input-Widget."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Label erstellen
        label_text = self.control_def.get('label', self.property_name)
        label = QLabel(f"{label_text}:")
        label.setMinimumWidth(150)  # Feste Breite für Alignment
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Optional: read_only Label visuell markieren
        if self.is_read_only:
            label.setStyleSheet("color: gray; font-style: italic;")
        
        layout.addWidget(label)
        
        # Input-Widget basierend auf Type erstellen
        self.input_widget = self._create_input_widget()
        
        # read_only anwenden
        if self.is_read_only:
            self._apply_read_only()
        
        layout.addWidget(self.input_widget)
        
        # Maximale Breite für Input-Widget (kompakter)
        if hasattr(self.input_widget, 'setMaximumWidth'):
            self.input_widget.setMaximumWidth(400)  # Nicht zu breit!
        
        layout.addStretch()  # Rechts expandieren (nach Input-Widget)
    
    def _create_input_widget(self) -> QWidget:
        """
        Erstellt Input-Widget basierend auf property_type.
        
        Returns:
            QWidget: Type-spezifisches Input-Widget
        """
        prop_type = self.property_type.lower()
        
        # STRING: QLineEdit
        if prop_type in ['string', 'text']:
            widget = QLineEdit()
            widget.setMinimumWidth(250)
            
            # max_length aus Control-Def
            max_length = self.control_def.get('max_length')
            if max_length:
                widget.setMaxLength(max_length)
            
            # Signal verbinden
            widget.textChanged.connect(lambda text: self._on_value_changed(text))
            
            return widget
        
        # INT: QSpinBox
        elif prop_type == 'int':
            widget = QSpinBox()
            widget.setMinimumWidth(150)
            
            # min/max aus Control-Def
            widget.setMinimum(self.control_def.get('min', -999999))
            widget.setMaximum(self.control_def.get('max', 999999))
            
            # Signal verbinden
            widget.valueChanged.connect(lambda value: self._on_value_changed(value))
            
            return widget
        
        # FLOAT: QDoubleSpinBox
        elif prop_type == 'float':
            widget = QDoubleSpinBox()
            widget.setMinimumWidth(150)
            
            # min/max/decimals aus Control-Def
            widget.setMinimum(self.control_def.get('min', -999999.0))
            widget.setMaximum(self.control_def.get('max', 999999.0))
            widget.setDecimals(self.control_def.get('decimals', 2))
            
            # Signal verbinden
            widget.valueChanged.connect(lambda value: self._on_value_changed(value))
            
            return widget
        
        # BOOL / CHECKBUTTON: QCheckBox
        elif prop_type in ['bool', 'checkbutton']:
            widget = QCheckBox()
            
            # Signal verbinden
            widget.stateChanged.connect(lambda state: self._on_value_changed(state == Qt.Checked))
            
            return widget
        
        # DROPDOWN: QComboBox (Options aus configs.dropdown)
        elif prop_type == 'dropdown':
            # ✅ V3.0: Prüfe ob configs.dropdown eine Config-Struktur enthält
            configs = self.control_def.get('configs', {})
            dropdown_config = configs.get('dropdown') if isinstance(configs, dict) else None
            
            # Prüfe ob dropdown_config eine V3-Config ist (dict mit table, key, feld)
            if isinstance(dropdown_config, dict) and 'table' in dropdown_config:
                # ✅ V3.0 DROPDOWN mit OPTIONS aus Config
                logger.info(f"  📋 V3.0 Dropdown-Config erkannt für '{self.property_name}'")
                
                try:
                    # Options aus V3-Config laden
                    gcs = get_gcs()
                    if gcs:
                        options_list = gcs.get_dropdown_options_v3(dropdown_config)
                        
                        if options_list:
                            # QComboBox mit Options aus V3-System
                            widget = QComboBox()
                            widget.setMinimumWidth(200)
                            
                            # Options hinzufügen (edit_list Format: [{"key": "w", "value": "Frau"}, ...])
                            for option in options_list:
                                key = option.get('key', '')
                                value = option.get('value', key)
                                widget.addItem(value, userData=key)  # Display=value, Data=key
                            
                            # Signal verbinden → Key als Wert (nicht Display-Text!)
                            widget.currentIndexChanged.connect(
                                lambda idx: self._on_value_changed(widget.itemData(idx) if idx >= 0 else None)
                            )
                            
                            logger.debug(f"  ✅ V3.0 Dropdown mit {len(options_list)} Options erstellt")
                            return widget
                        else:
                            logger.warning(f"  ⚠️ Keine Options aus V3-Config geladen")
                    else:
                        logger.warning(f"  ⚠️ GCS nicht verfügbar für V3-Dropdown")
                
                except Exception as e:
                    logger.error(f"  ❌ Fehler beim Laden von V3-Dropdown-Options: {e}")
            
            # Legacy: Versuche Options-Liste aus configs.dropdown zu laden
            options = self._load_dropdown_options()
            
            if options:
                # Options gefunden → QComboBox
                widget = QComboBox()
                widget.setMinimumWidth(200)
                widget.addItems(options)
                
                # Layout-Style anwenden
                gcs = get_gcs()
                if gcs and hasattr(gcs, 'layout'):
                    style = gcs.layout.get_stylesheet('QComboBox')
                    if style:
                        widget.setStyleSheet(style)
                
                # Signal verbinden
                widget.currentTextChanged.connect(lambda text: self._on_value_changed(text))
                
                logger.debug(f"  Dropdown erstellt mit {len(options)} Options")
                return widget
            else:
                # Keine Options → Fallback auf QLineEdit
                logger.warning(f"  Keine Dropdown-Options gefunden für '{self.property_name}' → Fallback auf QLineEdit")
                widget = QLineEdit()
                widget.setMinimumWidth(250)
                
                # Layout-Style anwenden
                gcs = get_gcs()
                if gcs and hasattr(gcs, 'layout'):
                    style = gcs.layout.get_stylesheet('QLineEdit')
                    if style:
                        widget.setStyleSheet(style)
                
                widget.textChanged.connect(lambda text: self._on_value_changed(text))
                return widget
        
        # MULTILINE: QTextEdit
        elif prop_type == 'multiline':
            widget = QTextEdit()
            widget.setMinimumWidth(300)
            widget.setMaximumHeight(100)
            
            # Layout-Style anwenden
            gcs = get_gcs()
            if gcs and hasattr(gcs, 'layout'):
                style = gcs.layout.get_stylesheet('QTextEdit')
                if style:
                    widget.setStyleSheet(style)
            
            # Signal verbinden
            widget.textChanged.connect(lambda: self._on_value_changed(widget.toPlainText()))
            
            return widget
        
        # FORMAT_TEXT: Button → öffnet Rich-Text-Editor
        elif prop_type == 'format_text':
            from PyQt5.QtWidgets import QPushButton
            
            widget = QPushButton("📝 Text bearbeiten...")
            widget.setMinimumWidth(200)
            
            # HTML-Content speichern (wird bei set_value gesetzt)
            widget.html_content = ""
            
            # Signal verbinden → öffnet Editor-Dialog
            widget.clicked.connect(lambda: self._open_format_text_editor(widget))
            
            return widget
        
        # EDIT_LIST: Button → öffnet Listen-Editor
        elif prop_type == 'edit_list':
            from PyQt5.QtWidgets import QPushButton
            
            widget = QPushButton("📋 Liste bearbeiten...")
            widget.setMinimumWidth(200)
            
            # Listen-Daten speichern (wird bei set_value gesetzt)
            widget.list_data = []
            
            # Signal verbinden → öffnet Listen-Editor-Dialog
            widget.clicked.connect(lambda: self._open_list_editor(widget))
            
            return widget
        
        # DEFAULT: QLineEdit
        else:
            logger.warning(f"  Unbekannter Type '{prop_type}' für Property '{self.property_name}' → Fallback auf QLineEdit")
            widget = QLineEdit()
            widget.setMinimumWidth(250)
            widget.textChanged.connect(lambda text: self._on_value_changed(text))
            return widget
    
    def _load_dropdown_options(self) -> list:
        """
        Lädt Dropdown-Options aus configs.dropdown.
        
        FORMAT in Template:
            "configs": {
                "dropdown": ["Option1", "Option2", "Option3"]
            }
        
        Returns:
            list: Liste der Options oder leere Liste wenn nicht gefunden
        """
        try:
            # configs.dropdown aus Control-Def holen
            configs = self.control_def.get('configs', {})
            
            if isinstance(configs, dict):
                dropdown_options = configs.get('dropdown', [])
                
                if isinstance(dropdown_options, list) and dropdown_options:
                    return dropdown_options
            
            # Fallback: Prüfe ob 'options' direkt in control_def (Legacy)
            options = self.control_def.get('options', [])
            if isinstance(options, list) and options:
                logger.debug(f"  Verwende Legacy 'options' für '{self.property_name}'")
                return options
            
            return []
            
        except Exception as e:
            logger.error(f"  Fehler beim Laden von Dropdown-Options: {e}")
            return []
    
    def _apply_read_only(self):
        """Wendet read_only auf Input-Widget an (deaktiviert + grauer Hintergrund)."""
        if not self.input_widget:
            return
        
        # Je nach Widget-Type unterschiedlich
        if isinstance(self.input_widget, (QLineEdit, QTextEdit)):
            self.input_widget.setReadOnly(True)
            
            # Grauer Hintergrund für read_only
            palette = self.input_widget.palette()
            palette.setColor(QPalette.Base, QColor(240, 240, 240))
            self.input_widget.setPalette(palette)
        
        elif isinstance(self.input_widget, (QSpinBox, QDoubleSpinBox, QComboBox)):
            self.input_widget.setEnabled(False)
            
            # Grauer Hintergrund
            self.input_widget.setStyleSheet("background-color: #f0f0f0;")
        
        elif isinstance(self.input_widget, QCheckBox):
            self.input_widget.setEnabled(False)
        
        logger.debug(f"  read_only angewendet auf '{self.property_name}'")
    
    def _on_value_changed(self, new_value: Any):
        """
        Handler wenn Wert im Input-Widget geändert wurde.
        
        Args:
            new_value: Neuer Wert (Type abhängig vom Widget)
        """
        # Aktuellen Wert speichern
        self.current_value = new_value
        
        # Signal emittieren
        self.value_changed.emit(self.property_name, new_value)
        
        logger.debug(f"  Wert geändert: {self.property_name} = {new_value}")
    
    def get_value(self) -> Any:
        """
        Gibt aktuellen Wert des Input-Widgets zurück.
        
        Returns:
            Any: Aktueller Wert (Type abhängig vom Widget)
        """
        if not self.input_widget:
            return None
        
        # ✅ V3.0: Config-Editor-Widget
        from pdvm_config_editor_widget import PdvmConfigEditorWidget
        if isinstance(self.input_widget, PdvmConfigEditorWidget):
            return self.input_widget.get_config()
        
        # Je nach Widget-Type
        if isinstance(self.input_widget, QLineEdit):
            return self.input_widget.text()
        
        elif isinstance(self.input_widget, QTextEdit):
            return self.input_widget.toPlainText()
        
        elif isinstance(self.input_widget, (QSpinBox, QDoubleSpinBox)):
            return self.input_widget.value()
        
        elif isinstance(self.input_widget, QCheckBox):
            return self.input_widget.isChecked()
        
        elif isinstance(self.input_widget, QComboBox):
            return self.input_widget.currentText()
        
        # FORMAT_TEXT: Button → gib HTML-Content zurück
        elif hasattr(self.input_widget, 'html_content'):
            return getattr(self.input_widget, 'html_content', '')
        
        # EDIT_LIST: Button → gib Listen-Daten zurück
        elif hasattr(self.input_widget, 'list_data'):
            return getattr(self.input_widget, 'list_data', [])
        
        return None
    
    def set_value(self, value: Any):
        """
        Setzt Wert im Input-Widget.
        
        Args:
            value: Neuer Wert (Type abhängig vom Widget)
        """
        if not self.input_widget:
            return
        
        try:
            # ✅ V3.0: Config-Editor-Widget
            from pdvm_config_editor_widget import PdvmConfigEditorWidget
            if isinstance(self.input_widget, PdvmConfigEditorWidget):
                if isinstance(value, dict):
                    self.input_widget.set_config(value)
                return
            
            # Je nach Widget-Type
            if isinstance(self.input_widget, QLineEdit):
                self.input_widget.setText(str(value) if value is not None else '')
            
            elif isinstance(self.input_widget, QTextEdit):
                self.input_widget.setPlainText(str(value) if value is not None else '')
            
            elif isinstance(self.input_widget, QSpinBox):
                self.input_widget.setValue(int(value) if value is not None else 0)
            
            elif isinstance(self.input_widget, QDoubleSpinBox):
                self.input_widget.setValue(float(value) if value is not None else 0.0)
            
            elif isinstance(self.input_widget, QCheckBox):
                self.input_widget.setChecked(bool(value))
            
            elif isinstance(self.input_widget, QComboBox):
                # ✅ V3.0: Setze nach KEY (userData), nicht nach Display-Text
                # Suche nach Index mit matching userData (key)
                found_index = -1
                for i in range(self.input_widget.count()):
                    item_data = self.input_widget.itemData(i)
                    if item_data == value:  # Vergleiche mit key
                        found_index = i
                        break
                
                if found_index >= 0:
                    self.input_widget.setCurrentIndex(found_index)
                else:
                    # Fallback: Versuche Display-Text (Legacy-Kompatibilität)
                    index = self.input_widget.findText(str(value))
                    if index >= 0:
                        self.input_widget.setCurrentIndex(index)
                    else:
                        # Wert nicht gefunden → setze ersten Eintrag
                        if self.input_widget.count() > 0:
                            self.input_widget.setCurrentIndex(0)
            
            # FORMAT_TEXT: Button → speichere HTML-Content
            elif hasattr(self.input_widget, 'html_content'):
                self.input_widget.html_content = str(value) if value is not None else ''
            
            # EDIT_LIST: Button → speichere Listen-Daten
            elif hasattr(self.input_widget, 'list_data'):
                self.input_widget.list_data = value if isinstance(value, list) else []
                # Button-Text aktualisieren
                count = len(self.input_widget.list_data)
                if count > 0:
                    self.input_widget.setText(f"📋 Liste bearbeiten ({count} Einträge)")
                else:
                    self.input_widget.setText("📋 Liste bearbeiten...")
            
            self.current_value = value
            
        except Exception as e:
            logger.error(f"Fehler beim Setzen des Wertes für '{self.property_name}': {e}")
    
    def _open_format_text_editor(self, button_widget):
        """
        Öffnet Format-Text-Editor-Dialog für format_text Type.
        
        Args:
            button_widget: Der Button der geklickt wurde
        """
        from pdvm_format_text_editor import PdvmFormatTextEditor
        
        # Aktuellen HTML-Content holen
        current_html = getattr(button_widget, 'html_content', '')
        
        # Editor-Dialog öffnen
        editor = PdvmFormatTextEditor(current_html, self)
        
        if editor.exec_():
            # HTML übernommen
            new_html = editor.get_html()
            button_widget.html_content = new_html
            
            # Signal emittieren
            self._on_value_changed(new_html)
            
            logger.info(f"✅ Format-Text gespeichert für '{self.property_name}' ({len(new_html)} Zeichen)")
    
    def _open_list_editor(self, button_widget):
        """
        Öffnet Listen-Editor-Dialog für edit_list Type.
        
        Args:
            button_widget: Der Button der geklickt wurde
        """
        from pdvm_list_editor import PdvmListEditor
        
        # Aktuelle Listen-Daten holen
        current_data = getattr(button_widget, 'list_data', [])
        
        # Listen-Name aus Property-Config holen (optional, für Template-Auswahl)
        list_name = self.control_def.get('list_name', None)
        
        # Wenn list_name nicht gesetzt, verwende property_name
        if not list_name:
            list_name = self.property_name
        
        # Tabellen-Name für Template-Zugriff (optional)
        table_name = self.control_def.get('table_name', None)
        
        # Editor-Dialog öffnen (KORRIGIERTE Parameter-Reihenfolge!)
        editor = PdvmListEditor(
            list_name=list_name,
            initial_data=current_data,
            table_name=table_name,
            parent=self
        )
        
        if editor.exec_():
            # Listen-Daten übernommen
            new_data = editor.get_data()
            button_widget.list_data = new_data
            
            # Button-Text aktualisieren (zeigt Anzahl der Einträge)
            count = len(new_data)
            if count > 0:
                button_widget.setText(f"📋 Liste bearbeiten ({count} Einträge)")
            else:
                button_widget.setText("📋 Liste bearbeiten...")
            
            # Signal emittieren
            self._on_value_changed(new_data)
            
            logger.info(f"✅ Listen-Daten gespeichert für '{self.property_name}' ({count} Einträge)")
    
    def get_display_order(self) -> int:
        """
        Gibt display_order aus Control-Definition zurück.
        
        Returns:
            int: display_order (Standard: 999)
        """
        order = self.control_def.get('display_order', 999)
        
        # Sichere Konvertierung zu int
        if order == '' or order is None:
            return 999
        
        try:
            return int(order)
        except (ValueError, TypeError):
            return 999
    
    def is_required(self) -> bool:
        """
        Prüft ob Property required ist.
        
        Returns:
            bool: True wenn required
        """
        return self.control_def.get('required', False)
    
    def validate(self) -> tuple[bool, str]:
        """
        Validiert aktuellen Wert gegen Control-Definition.
        
        Returns:
            tuple: (is_valid: bool, error_message: str)
        """
        current_value = self.get_value()
        
        # Required-Check
        if self.is_required():
            if current_value is None or (isinstance(current_value, str) and not current_value.strip()):
                return False, f"'{self.control_def.get('label', self.property_name)}' ist ein Pflichtfeld"
        
        # Type-spezifische Validierung
        if self.property_type == 'int':
            min_val = self.control_def.get('min')
            max_val = self.control_def.get('max')
            
            if min_val is not None and current_value < min_val:
                return False, f"Wert muss mindestens {min_val} sein"
            
            if max_val is not None and current_value > max_val:
                return False, f"Wert darf maximal {max_val} sein"
        
        elif self.property_type == 'float':
            min_val = self.control_def.get('min')
            max_val = self.control_def.get('max')
            
            if min_val is not None and current_value < min_val:
                return False, f"Wert muss mindestens {min_val} sein"
            
            if max_val is not None and current_value > max_val:
                return False, f"Wert darf maximal {max_val} sein"
        
        elif self.property_type in ['string', 'text']:
            max_length = self.control_def.get('max_length')
            
            if max_length and len(str(current_value)) > max_length:
                return False, f"Maximale Länge: {max_length} Zeichen"
        
        # Validierung erfolgreich
        return True, ""
