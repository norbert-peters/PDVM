"""
PDVM Config Editor Widget
=========================

Spezialisiertes Widget für Dropdown/Help-Konfigurationen im System-Editor.

ARCHITEKTUR:
1. Tabellen-Auswahl (sys_dropdowndaten, sys_beschreibungen)
2. Key-Auswahl → UID + Name aus gewählter Tabelle
3. Feld-Auswahl → Felder aus DEFAULT_LANGUAGE Gruppe
4. Gruppe-Override (optional) → Sprach-Override

VERWENDUNG:
    config_widget = PdvmConfigEditorWidget(config_type='dropdown', parent=self)
    config = config_widget.get_config()
    # Returns: {"table": "...", "key": "...", "feld": "...", "gruppe": "..."}
"""

import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QGroupBox, QLineEdit)
from PyQt5.QtCore import pyqtSignal
import json

from pdvm_central_systemsteuerung import get_gcs
from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)


class PdvmConfigEditorWidget(QWidget):
    """
    Widget für Dropdown/Help-Konfiguration im System-Editor
    
    LINEARER ABLAUF:
    1. Tabelle wählen (dropdown: sys_dropdowndaten, help: sys_beschreibungen)
    2. Key wählen aus Tabelle (UID des Datensatzes)
    3. Feld wählen aus DEFAULT_LANGUAGE Gruppe
    4. Optional: Gruppe override (Sprache)
    
    Signals:
        config_changed: Emittiert bei Änderungen der Konfiguration
    """
    
    config_changed = pyqtSignal(dict)  # Neue Config
    
    def __init__(self, config_type='dropdown', initial_config=None, parent=None):
        """
        Args:
            config_type: 'dropdown' oder 'help'
            initial_config: Vorhandene Config (dict) oder None
            parent: Parent Widget
        """
        super().__init__(parent)
        
        self.config_type = config_type
        self.gcs = get_gcs()
        
        # Cache für geladene Daten
        self._table_data_cache = {}  # {table_name: PdvmCentralDatenbank}
        self._current_table_data = None
        
        self._init_ui()
        
        # Initial Config laden falls vorhanden
        if initial_config:
            self.set_config(initial_config)
        
        logger.info(f"✅ ConfigEditorWidget initialisiert: Typ={config_type}")
    
    def _init_ui(self):
        """UI aufbauen - Linear von oben nach unten"""
        layout = QVBoxLayout(self)
        
        # GroupBox für bessere Struktur
        group = QGroupBox(f"{self.config_type.title()}-Konfiguration")
        group_layout = QVBoxLayout()
        
        # === 1. TABELLEN-AUSWAHL ===
        table_layout = QHBoxLayout()
        table_layout.addWidget(QLabel("Tabelle:"))
        
        self.table_combo = QComboBox()
        if self.config_type == 'dropdown':
            self.table_combo.addItems(['sys_dropdowndaten'])
        else:  # help
            self.table_combo.addItems(['sys_beschreibungen'])
        
        self.table_combo.currentTextChanged.connect(self._on_table_changed)
        table_layout.addWidget(self.table_combo)
        
        group_layout.addLayout(table_layout)
        
        # === 2. KEY-AUSWAHL (UID + Name) ===
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("Datensatz:"))
        
        self.key_combo = QComboBox()
        self.key_combo.currentTextChanged.connect(self._on_key_changed)
        key_layout.addWidget(self.key_combo)
        
        # Button: Datensätze neu laden
        reload_btn = QPushButton("🔄 Neu laden")
        reload_btn.clicked.connect(self._load_table_records)
        key_layout.addWidget(reload_btn)
        
        group_layout.addLayout(key_layout)
        
        # === 3. FELD-AUSWAHL (aus DEFAULT_LANGUAGE) ===
        feld_layout = QHBoxLayout()
        feld_layout.addWidget(QLabel("Feld:"))
        
        self.feld_combo = QComboBox()
        self.feld_combo.currentTextChanged.connect(self._emit_config_changed)
        feld_layout.addWidget(self.feld_combo)
        
        group_layout.addLayout(feld_layout)
        
        # === 4. GRUPPE-OVERRIDE (optional) ===
        gruppe_layout = QHBoxLayout()
        gruppe_layout.addWidget(QLabel("Sprache (override):"))
        
        self.gruppe_edit = QLineEdit()
        self.gruppe_edit.setPlaceholderText("Leer = DEFAULT_LANGUAGE verwenden")
        self.gruppe_edit.textChanged.connect(self._emit_config_changed)
        gruppe_layout.addWidget(self.gruppe_edit)
        
        group_layout.addLayout(gruppe_layout)
        
        # === INFO-BEREICH ===
        self.info_label = QLabel("ℹ️ Wählen Sie eine Tabelle aus")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: gray; font-style: italic;")
        group_layout.addWidget(self.info_label)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        layout.addStretch()
        
        # Initial: Tabelle laden
        if self.table_combo.count() > 0:
            self._on_table_changed(self.table_combo.currentText())
    
    def _on_table_changed(self, table_name):
        """Tabelle gewählt → Datensätze laden"""
        if not table_name:
            return
        
        logger.info(f"🔧 Lade Datensätze aus {table_name}...")
        self._load_table_records()
    
    def _load_table_records(self):
        """
        Lädt alle Datensätze aus der gewählten Tabelle.
        
        STRATEGIE:
        1. Hole alle UIDs aus Tabelle (via PdvmDatenbank)
        2. Für jede UID: Lade ROOT → BESCHREIBUNG_NAME
        3. Baue Dropdown: "Name (UID)" für Auswahl
        """
        table_name = self.table_combo.currentText()
        if not table_name:
            return
        
        try:
            # Cache prüfen
            if table_name in self._table_data_cache:
                logger.debug(f"📋 Verwende gecachte Daten für {table_name}")
            
            # SCHRITT 1: Alle UIDs aus Tabelle holen
            from pdvm_datenbank import PdvmDatenbank
            db = PdvmDatenbank(table_name)
            
            # ✅ EINFACH: alle_lesen() liefert uid + name aus daten.ROOT.name
            records = db.alle_lesen()
            
            # Nach Name sortieren
            records.sort(key=lambda r: r.get('name', ''))
            
            self.key_combo.clear()
            self.key_combo.addItem("Bitte Datensatz wählen...", userData=None)
            
            if records:
                for record in records:
                    uid = record['uid']
                    name = record.get('name', '') or f"Datensatz {uid[:8]}"
                    
                    display_text = f"{name} ({uid[:8]}...)"
                    self.key_combo.addItem(display_text, userData=uid)
                
                self.info_label.setText(f"✅ {len(records)} Datensätze geladen aus {table_name}")
            else:
                self.info_label.setText(f"⚠️ Keine Datensätze in {table_name} gefunden")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Datensätze: {e}", exc_info=True)
            self.info_label.setText(f"❌ Fehler: {e}")
    
    def _on_key_changed(self, display_text):
        """
        Datensatz gewählt → Felder aus DEFAULT_LANGUAGE laden
        """
        uid = self.key_combo.currentData()
        if not uid:
            self.feld_combo.clear()
            return
        
        logger.info(f"🔧 Lade Felder für Datensatz {uid}...")
        
        try:
            table_name = self.table_combo.currentText()
            
            # Datensatz aus DB laden
            db = PdvmCentralDatenbank(table_name, uid)
            
            # ROOT laden für DEFAULT_LANGUAGE
            root_data = db.get_value_by_group('ROOT')
            if not root_data:
                logger.warning(f"⚠️ Keine ROOT-Daten für {uid}")
                return
            
            default_language = root_data.get('DEFAULT_LANGUAGE', 'DE-DE')
            logger.info(f"📋 DEFAULT_LANGUAGE: {default_language}")
            
            # Sprach-Gruppe laden
            language_data = db.get_value_by_group(default_language)
            if not language_data:
                logger.warning(f"⚠️ Keine Daten für Sprache {default_language}")
                return
            
            # Felder extrahieren (alle GUIDs → name)
            self.feld_combo.clear()
            self.feld_combo.addItem("Bitte Feld wählen...", userData=None)
            
            for guid, field_data in language_data.items():
                field_name = field_data.get('name', guid)
                field_label = field_data.get('label', field_name)
                display = f"{field_label} ({field_name})"
                self.feld_combo.addItem(display, userData=field_name)
            
            self.info_label.setText(f"✅ {self.feld_combo.count()-1} Felder verfügbar")
            
            # Cache speichern
            self._current_table_data = db
            
            # Config-Changed emittieren
            self._emit_config_changed()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Felder: {e}", exc_info=True)
            self.info_label.setText(f"❌ Fehler: {e}")
    
    def _emit_config_changed(self):
        """Config geändert → Signal emittieren"""
        config = self.get_config()
        if config.get('key') and config.get('feld'):
            self.config_changed.emit(config)
    
    def get_config(self) -> dict:
        """
        Aktuelle Konfiguration als Dictionary zurückgeben
        
        Returns:
            dict: {"table": "...", "key": "...", "feld": "...", "gruppe": "..."}
        """
        return {
            "table": self.table_combo.currentText(),
            "key": self.key_combo.currentData(),
            "feld": self.feld_combo.currentData(),
            "gruppe": self.gruppe_edit.text() or ""
        }
    
    def set_config(self, config: dict):
        """
        Config setzen (für Laden bestehender Konfiguration)
        
        Args:
            config: Dictionary mit table, key, feld, gruppe
        """
        if not config:
            return
        
        # Tabelle setzen
        table = config.get('table', '')
        idx = self.table_combo.findText(table)
        if idx >= 0:
            self.table_combo.setCurrentIndex(idx)
        
        # Key setzen (nach Laden der Datensätze)
        key = config.get('key', '')
        if key:
            # TODO: Key im Combo finden und setzen
            pass
        
        # Feld setzen
        feld = config.get('feld', '')
        if feld:
            # TODO: Feld im Combo finden und setzen
            pass
        
        # Gruppe setzen
        gruppe = config.get('gruppe', '')
        self.gruppe_edit.setText(gruppe)
        
        logger.info(f"✅ Config gesetzt: {config}")


if __name__ == '__main__':
    """Test des Widgets"""
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Test-Widget
    widget = PdvmConfigEditorWidget(config_type='dropdown')
    widget.show()
    
    # Signal-Test
    def on_config_changed(config):
        print(f"Config geändert: {config}")
    
    widget.config_changed.connect(on_config_changed)
    
    sys.exit(app.exec_())
