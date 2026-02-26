"""
PDVM System Editor V3 - VEREINFACHT für Administrator
======================================================

LAYOUT (3 Spalten wie Menu-Editor):
- Spalte 1: Gruppen (ROOT separat, dann alle anderen)
- Spalte 2: Felder der ausgewählten Gruppe
- Spalte 3: Properties des ausgewählten Feldes

STRUKTUR (flach):
- ROOT: Direkte Properties (TABLE, NAME, etc.)
- Gruppen: Enthalten Felder mit GUIDs
- Felder: Properties (name, label, type, display_order, etc.)

VERWENDUNG:
- Funktioniert mit ALLEN Tabellen (sys_*, persondaten, etc.)
- 55555... Templates
- 66666... Dictionaries
- Normale Datensätze

Erstellt: 18.12.2025
"""

import sys
import json
import logging
from typing import Dict, Optional, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QFormLayout, QLineEdit, QTextEdit, QPushButton, QLabel, 
    QSplitter, QMessageBox, QApplication, QDialog, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from pdvm_central_datenbank import PdvmCentralDatenbank
from pdvm_central_systemsteuerung import get_gcs

logger = logging.getLogger(__name__)


class PdvmSystemEditorSimple(QWidget):
    """
    Vereinfachter System-Editor mit 3-Spalten Layout.
    
    Spalte 1: Gruppen (ROOT + alle anderen)
    Spalte 2: Felder der Gruppe
    Spalte 3: Properties des Feldes
    """
    
    def __init__(self, table_name: str, record_uid: str, parent=None):
        """
        Args:
            table_name: z.B. 'sys_framedaten', 'persondaten'
            record_uid: UID des Datensatzes (z.B. 66666...)
        """
        super().__init__(parent)
        
        self.table_name = table_name
        self.record_uid = record_uid
        self.gcs = get_gcs()
        
        # Datenbank
        self.db = PdvmCentralDatenbank(table_name, record_uid)
        
        # Daten laden
        self.data = {}
        self._load_data()
        
        # UI erstellen
        self._init_ui()
        
        # Daten anzeigen
        self._refresh_tree()
    
    def __init__(self, table_name: str, record_uid: str, parent=None):
        """
        Args:
            table_name: z.B. 'sys_framedaten', 'persondaten'
            record_uid: UID des Datensatzes (z.B. 66666...)
        """
        super().__init__(parent)
        
        self.table_name = table_name
        self.record_uid = record_uid
        self.gcs = get_gcs()
        
        # Datenbank
        self.db = PdvmCentralDatenbank(table_name, record_uid)
        
        # Daten laden
        self.data = {}
        self._load_data()
        
        # Aktuell ausgewähltes
        self.current_gruppe = None
        self.current_feld_guid = None
        
        # Property Widgets
        self.property_widgets = {}
        
        # UI erstellen
        self._init_ui()
        
        # Gruppen-Liste füllen
        self._refresh_gruppen_liste()
    
    def _load_data(self):
        """Lädt Dictionary-Datensatz aus PdvmCentralDatenbank (Instanz-basiert)"""
        try:
            # PdvmCentralDatenbank ist INSTANZ-basiert (eine GUID = ein Datensatz)
            # Wir holen ALLE Properties dieser Instanz direkt aus self.db.data
            logger.info(f"📂 Lade Dictionary aus {self.table_name}.{self.record_uid[:8]}...")
            
            # Die Daten sind bereits in self.db.data geladen (JSON-Struktur)
            if hasattr(self.db, 'data') and isinstance(self.db.data, dict):
                self.data = self.db.data
                
                # Log für jede Gruppe
                for gruppe_name, gruppe_data in self.data.items():
                    if gruppe_name == 'ROOT':
                        logger.info(f"  ✅ ROOT: {len(gruppe_data)} Properties")
                    elif isinstance(gruppe_data, dict):
                        logger.info(f"  ✅ {gruppe_name}: {len(gruppe_data)} Felder")
                
                logger.info(f"✅ Dictionary geladen: {len(self.data)} Gruppen")
            else:
                logger.warning(f"⚠️ Keine data in DB-Instanz vorhanden")
                self.data = {}
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden: {e}")
            logger.exception("Traceback:")
            self.data = {}
    
    def _init_ui(self):
        """Erstellt 3-Spalten Layout"""
        layout = QVBoxLayout()
        
        # Header
        header = QLabel(f"<h2>{self.table_name}</h2><p>UID: {self.record_uid[:8]}...</p>")
        layout.addWidget(header)
        
        # 3-Spalten Splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # === SPALTE 1: GRUPPEN ===
        gruppen_widget = QWidget()
        gruppen_layout = QVBoxLayout(gruppen_widget)
        gruppen_layout.addWidget(QLabel("<b>Gruppen</b>"))
        
        self.gruppen_liste = QListWidget()
        self.gruppen_liste.itemClicked.connect(self._on_gruppe_selected)
        gruppen_layout.addWidget(self.gruppen_liste)
        
        splitter.addWidget(gruppen_widget)
        
        # === SPALTE 2: FELDER ===
        felder_widget = QWidget()
        felder_layout = QVBoxLayout(felder_widget)
        felder_layout.addWidget(QLabel("<b>Felder</b>"))
        
        self.felder_liste = QListWidget()
        self.felder_liste.itemClicked.connect(self._on_feld_selected)
        felder_layout.addWidget(self.felder_liste)
        
        splitter.addWidget(felder_widget)
        
        # === SPALTE 3: PROPERTIES ===
        properties_widget = QWidget()
        properties_layout = QVBoxLayout(properties_widget)
        properties_layout.addWidget(QLabel("<b>Properties</b>"))
        
        # Scroll-Area für Properties
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        self.properties_container = QWidget()
        self.properties_layout = QFormLayout(self.properties_container)
        scroll.setWidget(self.properties_container)
        
        properties_layout.addWidget(scroll)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_save = QPushButton("💾 Speichern")
        self.btn_save.clicked.connect(self._save_data)
        btn_layout.addWidget(self.btn_save)
        
        self.btn_reload = QPushButton("🔄 Neu laden")
        self.btn_reload.clicked.connect(self._reload_data)
        btn_layout.addWidget(self.btn_reload)
        
        btn_layout.addStretch()
        
        properties_layout.addLayout(btn_layout)
        
        splitter.addWidget(properties_widget)
        
        # Splitter Größen
        splitter.setSizes([300, 400, 500])
        
        layout.addWidget(splitter)
        self.setLayout(layout)
    
    def _refresh_gruppen_liste(self):
        """Füllt Gruppen-Liste"""
        self.gruppen_liste.clear()
        
        if not self.data:
            return
        
        # ROOT separat (wenn vorhanden)
        if "ROOT" in self.data:
            item = QListWidgetItem("🔹 ROOT")
            item.setData(Qt.UserRole, "ROOT")
            item.setForeground(QColor("blue"))
            item.setFont(QFont("Arial", 10, QFont.Bold))
            self.gruppen_liste.addItem(item)
        
        # Alle anderen Gruppen
        for gruppe_name in sorted(self.data.keys()):
            if gruppe_name == "ROOT":
                continue
            
            item = QListWidgetItem(f"📁 {gruppe_name}")
            item.setData(Qt.UserRole, gruppe_name)
            item.setForeground(QColor("darkgreen"))
            self.gruppen_liste.addItem(item)
    
    def _on_gruppe_selected(self, item):
        """Gruppe ausgewählt → Felder anzeigen"""
        self.current_gruppe = item.data(Qt.UserRole)
        self._refresh_felder_liste()
        
        # Properties löschen
        self._clear_properties()
    
    def _refresh_felder_liste(self):
        """Füllt Felder-Liste für ausgewählte Gruppe (unterstützt Dictionary + Persondaten)"""
        self.felder_liste.clear()
        
        if not self.current_gruppe or self.current_gruppe not in self.data:
            return
        
        gruppe_data = self.data[self.current_gruppe]
        
        # ROOT: Direkte Properties (keine Felder)
        if self.current_gruppe == "ROOT":
            if isinstance(gruppe_data, dict):
                for key, value in gruppe_data.items():
                    item = QListWidgetItem(f"{key}: {str(value)[:50]}")
                    item.setData(Qt.UserRole, key)
                    self.felder_liste.addItem(item)
            return
        
        # Normale Gruppe: Prüfe Struktur-Typ
        if not isinstance(gruppe_data, dict):
            return
        
        # AUTO-ERKENNUNG: Dictionary-Struktur (GUIDs) vs. Persondaten (Feldnamen)
        for feld_id, feld_data in gruppe_data.items():
            # Versuche zu erkennen ob GUID oder Feldname
            is_guid = '-' in str(feld_id) and len(str(feld_id)) > 30
            
            if is_guid and isinstance(feld_data, dict) and 'name' in feld_data:
                # DICTIONARY-STRUKTUR: GUID → {name, label, type, ...}
                feld_name = feld_data.get('name', '???')
                item = QListWidgetItem(f"⚙️ {feld_name} ({feld_id[:8]}...)")
                item.setData(Qt.UserRole, feld_id)
                self.felder_liste.addItem(item)
            else:
                # PERSONDATEN-STRUKTUR: Feldname → {timestamp: wert}
                # Zeige Feldname direkt
                item = QListWidgetItem(f"📋 {feld_id}")
                item.setData(Qt.UserRole, feld_id)
                self.felder_liste.addItem(item)
    
    def _on_feld_selected(self, item):
        """Feld ausgewählt → Properties anzeigen"""
        if self.current_gruppe == "ROOT":
            # ROOT Property
            prop_name = item.data(Qt.UserRole)
            self._show_root_property(prop_name)
        else:
            # Normales Feld
            self.current_feld_guid = item.data(Qt.UserRole)
            self._show_feld_properties()
    
    def _show_root_property(self, prop_name: str):
        """Zeigt ROOT Property (einfacher Wert)"""
        self._clear_properties()
        
        if "ROOT" not in self.data:
            return
        
        value = self.data["ROOT"].get(prop_name, "")
        
        # Einfaches Textfeld
        widget = QLineEdit(str(value))
        widget.textChanged.connect(lambda text, pn=prop_name: self._on_root_property_changed(pn, text))
        
        self.properties_layout.addRow(f"<b>{prop_name}</b>:", widget)
        self.property_widgets[prop_name] = widget
    
    def _show_feld_properties(self):
        """Zeigt ALLE Properties eines Feldes (komplett dynamisch)
        
        Unterstützt zwei Strukturen:
        1. Dictionary: {GUID: {name: "X", label: "Y", type: "Z"}}
        2. Persondaten: {FELDNAME: {timestamp: wert}}
        """
        self._clear_properties()
        
        if not self.current_gruppe or not self.current_feld_guid:
            return
        
        if self.current_gruppe not in self.data:
            return
        
        gruppe_data = self.data[self.current_gruppe]
        if self.current_feld_guid not in gruppe_data:
            return
        
        feld_data = gruppe_data[self.current_feld_guid]
        
        if not isinstance(feld_data, dict):
            return
        
        # Auto-Detect: Dictionary vs Persondaten
        # Persondaten: Alle Keys sehen aus wie Timestamps (numeric oder "2025043.0")
        is_persondaten = all(
            self._looks_like_timestamp(key) 
            for key in feld_data.keys() 
            if key  # Skip empty keys
        )
        
        if is_persondaten:
            # 📋 PERSONDATEN-STRUKTUR: {timestamp: wert}
            label = QLabel(f"<b>Historische Werte für {self.current_feld_guid}:</b>")
            self.properties_layout.addRow(label)
            
            # Sortiert nach Timestamp (neueste zuerst)
            for timestamp in sorted(feld_data.keys(), reverse=True):
                wert = feld_data[timestamp]
                
                # Timestamp formatieren (PdvmDateTime-Style)
                try:
                    ts_float = float(timestamp)
                    # Simple Formatierung: YYYYDDD.HHMMSS
                    jahr = int(ts_float // 1000)
                    tag_des_jahres = int(ts_float % 1000)
                    stunden_frac = (ts_float % 1) * 100000
                    stunden = int(stunden_frac // 10000)
                    minuten = int((stunden_frac % 10000) // 100)
                    sekunden = int(stunden_frac % 100)
                    ts_label = f"{jahr}-{tag_des_jahres:03d} {stunden:02d}:{minuten:02d}:{sekunden:02d}"
                except:
                    ts_label = str(timestamp)
                
                widget = QLineEdit(str(wert))
                widget.textChanged.connect(
                    lambda text, ts=timestamp: self._on_persondaten_changed(ts, text)
                )
                self.properties_layout.addRow(f"🕐 {ts_label}:", widget)
                self.property_widgets[timestamp] = widget
        else:
            # ⚙️ DICTIONARY-STRUKTUR: {name: "X", label: "Y", type: "Z"}
            # ALLE Properties anzeigen (KEINE Ausnahmen!)
            for prop_name, prop_value in sorted(feld_data.items()):
                # Widget basierend auf Datentyp
                if isinstance(prop_value, list) or isinstance(prop_value, dict):
                    # Komplexe Strukturen als JSON-Text
                    widget = QTextEdit(json.dumps(prop_value, indent=2, ensure_ascii=False))
                    widget.setMaximumHeight(150)
                    # QTextEdit: Signal anders verbinden (kein Parameter)
                    widget.textChanged.connect(
                        lambda w=widget, pn=prop_name: self._on_property_changed(pn, w.toPlainText())
                    )
                elif isinstance(prop_value, bool):
                    widget = QLineEdit(str(prop_value))
                    widget.textChanged.connect(
                        lambda text, pn=prop_name: self._on_property_changed(pn, text)
                    )
                elif isinstance(prop_value, (int, float)):
                    widget = QLineEdit(str(prop_value))
                    widget.textChanged.connect(
                        lambda text, pn=prop_name: self._on_property_changed(pn, text)
                    )
                elif isinstance(prop_value, str) and len(prop_value) > 100:
                    widget = QTextEdit(prop_value)
                    widget.setMaximumHeight(100)
                    widget.textChanged.connect(
                        lambda w=widget, pn=prop_name: self._on_property_changed(pn, w.toPlainText())
                    )
                else:
                    # Default: String oder None
                    widget = QLineEdit(str(prop_value) if prop_value is not None else "")
                    widget.textChanged.connect(
                        lambda text, pn=prop_name: self._on_property_changed(pn, text)
                    )
                
                self.properties_layout.addRow(f"<b>{prop_name}</b>:", widget)
                self.property_widgets[prop_name] = widget
    
    def _clear_properties(self):
        """Löscht Properties-Anzeige"""
        while self.properties_layout.count():
            child = self.properties_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                while child.layout().count():
                    subchild = child.layout().takeAt(0)
                    if subchild.widget():
                        subchild.widget().deleteLater()
        
        self.property_widgets.clear()
    
    def _on_root_property_changed(self, prop_name: str, value: str):
        """ROOT Property geändert"""
        if "ROOT" not in self.data:
            self.data["ROOT"] = {}
        
        self.data["ROOT"][prop_name] = value
    
    def _looks_like_timestamp(self, key: str) -> bool:
        """Prüft ob ein Key wie ein Timestamp aussieht (PdvmDateTime Format)"""
        try:
            # PdvmDateTime: YYYYDDD.HHMMSS (z.B. "2025043.0")
            key_str = str(key)
            if '.' in key_str:
                parts = key_str.split('.')
                if len(parts) == 2:
                    jahr_tag = parts[0]
                    # Format: mindestens 4 Stellen (Jahr) + bis zu 3 Stellen (Tag)
                    if len(jahr_tag) >= 4 and jahr_tag.isdigit():
                        return True
            return False
        except:
            return False
    
    def _on_persondaten_changed(self, timestamp: str, value: str):
        """Persondaten-Wert geändert (historische Daten)"""
        if not self.current_gruppe or not self.current_feld_guid:
            return
        
        if self.current_gruppe not in self.data:
            return
        
        if self.current_feld_guid not in self.data[self.current_gruppe]:
            return
        
        # Wert aktualisieren (String-Wert, da historische Daten)
        self.data[self.current_gruppe][self.current_feld_guid][timestamp] = value
        logger.info(f"✏️ {self.current_gruppe}.{self.current_feld_guid} @ {timestamp} = {value}")
    
    def _on_property_changed(self, prop_name: str, value: str):
        """Feld-Property geändert (mit intelligenter Typ-Erkennung)"""
        if not self.current_gruppe or not self.current_feld_guid:
            return
        
        if self.current_gruppe not in self.data:
            return
        
        if self.current_feld_guid not in self.data[self.current_gruppe]:
            return
        
        # Original-Wert holen für Typ-Erkennung
        feld_data = self.data[self.current_gruppe][self.current_feld_guid]
        old_value = feld_data.get(prop_name)
        
        # Intelligente Typ-Konvertierung basierend auf Original-Typ
        converted_value = value
        
        if isinstance(old_value, bool):
            converted_value = value.lower() in ['true', '1', 'yes', 'ja']
        elif isinstance(old_value, int):
            try:
                converted_value = int(value)
            except ValueError:
                logger.warning(f"⚠️ Ungültiger int-Wert: {value}")
                return
        elif isinstance(old_value, float):
            try:
                converted_value = float(value)
            except ValueError:
                logger.warning(f"⚠️ Ungültiger float-Wert: {value}")
                return
        elif isinstance(old_value, (list, dict)):
            # JSON-Parsing für komplexe Strukturen
            try:
                converted_value = json.loads(value)
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Ungültiges JSON für {prop_name}: {e}")
                return
        # else: String bleibt String
        
        # Wert aktualisieren
        feld_data[prop_name] = converted_value
        logger.info(f"✏️ {self.current_gruppe}.{self.current_feld_guid[:8]}...{prop_name} = {converted_value} (Typ: {type(converted_value).__name__})")
    
    def _save_data(self):
        """Speichert Dictionary-Struktur zurück in Datenbank"""
        try:
            logger.info(f"💾 Speichere Dictionary: {len(self.data)} Gruppen")
            
            # Speichere jede Gruppe separat
            for gruppe_name, gruppe_data in self.data.items():
                if gruppe_name == 'ROOT':
                    # ROOT: Direkte Properties
                    for prop_name, prop_value in gruppe_data.items():
                        self.db.set_value('ROOT', prop_name, prop_value)
                        logger.info(f"  💾 ROOT.{prop_name} = {prop_value}")
                else:
                    # Andere Gruppen: Setze komplette Gruppe
                    self.db.set_value(gruppe_name, None, gruppe_data)
                    logger.info(f"  💾 {gruppe_name}: {len(gruppe_data)} Felder")
            
            # Alles speichern
            self.db.save_all_values()
            logger.info(f"✅ Dictionary gespeichert!")
            
            QMessageBox.information(self, "✅ Gespeichert", f"Dictionary erfolgreich gespeichert!\n{len(self.data)} Gruppen")
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Fehler", f"Fehler beim Speichern:\n{e}")
            logger.error(f"❌ Save-Fehler: {e}", exc_info=True)
    
    def _reload_data(self):
        """Lädt Daten neu"""
        self._load_data()
        self._refresh_gruppen_liste()
        self._clear_properties()
        self.felder_liste.clear()
        QMessageBox.information(self, "🔄 Neu geladen", "Daten neu geladen!")
    
    def get_widget(self):
        """Gibt Widget zurück (für pdvm_genereller_dialog Integration)"""
        return self


# ========================================
# DIALOG-WRAPPER
# ========================================
class PdvmSystemEditorDialog(QDialog):
    """Dialog-Wrapper für System-Editor"""
    
    def __init__(self, table_name: str, record_uid: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"System Editor - {table_name}")
        self.setModal(True)
        self.resize(1400, 800)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.editor = PdvmSystemEditorSimple(table_name, record_uid, self)
        layout.addWidget(self.editor)


# ========================================
# TEST
# ========================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Test mit 66666... Dictionary
    dialog = PdvmSystemEditorDialog("sys_mandanten", "66666666-6666-6666-6666-666666666666")
    dialog.show()
    
    sys.exit(app.exec_())
