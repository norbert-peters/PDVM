"""
PdvmViewDialog - SAUBERE LINEARE ARCHITEKTUR

Architektur-Prinzipien:
1. GCS über Property, nicht in __init__
2. Keine user_guid - alles über GCS
3. PdvmCentralDatenbank mit korrekten Parametern oder Fehler
4. ViewDaten komplett übernehmen, nicht einzeln kopieren
5. Kein Fallback für Dummy - Fehler wenn nicht in ViewDaten
6. Keine Duplikate - eine Methode pro Funktion
7. Linear: ViewDaten → Original Controls → Show Controls → Dummy → GCS speichern
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                            QTableWidgetItem, QHeaderView, QPushButton, QLabel, 
                            QMenu, QAction, QMessageBox, QToolButton, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

# GLOBALE IMPORTS: Direkter Zugriff auf zentrale Systemsteuerung  
from pdvm_central_systemsteuerung import get_gcs
import logging
import time
import json
import traceback

logger = logging.getLogger(__name__)

from pdvm_central_datenbank import PdvmCentralDatenbank
from pdvm_spalten_parameter_dialog import PdvmSpaltenParameterDialog
from pdvm_spalten_konfig_dialog import PdvmSpaltenKonfigDialog


class PdvmViewDialog:
    """
    SAUBERER Autonomer View-Dialog mit integriertem Datenmanagement
    
    LINEARE ARCHITEKTUR:
    1. Validation der call_daten
    2. ViewDaten laden mit korrekter PdvmCentralDatenbank
    3. Controls linear generieren: ViewDaten → _original → _show → dummy
    4. Controls in GCS speichern
    5. Daten laden und Matrix erstellen
    6. UI-Display erstellen
    """
    
    def __init__(self, call_daten, parent=None):
        """
        Initialisierung des autonomen View-Dialogs
        
        Args:
            call_daten: Enthält view_guid, title, first_call
            parent: Parent-Widget
        """
        self.call_daten = call_daten
        self.parent = parent
        
        # 🔍 1. TITEL-VALIDATION: Prüfung auf erforderliche Daten
        self.view_guid = call_daten.get("view_guid")
        self.title = call_daten.get("title")
        self.first_call = call_daten.get("first_call", False)
        
        # Fehlerbehandlung für fehlende erforderliche Daten
        error_messages = []
        if not self.view_guid:
            error_messages.append("❌ Keine view_guid in call_daten gefunden")
        if not self.title:
            error_messages.append("❌ Kein Titel in call_daten gefunden")
            
        if error_messages:
            error_text = "\n".join(error_messages)
            logger.error(f"Validation Error: {error_text}")
            QMessageBox.critical(parent, "Fehlende Daten", 
                               f"Die Ausgabe kann nicht erfolgen:\n\n{error_text}")
            raise ValueError(error_text)
        
        # Zentrale Systemsteuerung - Direkter Zugriff (KEINE Fallbacks!)
        if not get_gcs():
            error_msg = "❌ Zentrale Systemsteuerung nicht initialisiert - Login fehlt!"
            logger.error(error_msg)
            QMessageBox.critical(parent, "System Error", error_msg)
            raise RuntimeError(error_msg)
        
        logger.info(f"🔹 PdvmViewDialog initialisiert - View: {self.view_guid}, User: {self.gcs.user_guid}, First Call: {self.first_call}")
        
        # Daten-Container
        self.view_config = None
        self.controls_config = None
        self.all_data_records = []
        self.display_matrix = []
        
        # UI-Container
        self.display = None
        
        # Initialisierung starten
        self._initialize_dialog()
    
    @property
    def gcs(self):
        """Property für direkten Zugriff auf globale Systemsteuerung"""
        return get_gcs()
    
    def _initialize_dialog(self):
        """LINEARE Initialisierung"""
        logger.info("🔹 Starte LINEARE Dialog-Initialisierung...")
        
        # 1. ViewDaten laden
        self._load_viewdata()
        
        # 2. Controls linear generieren und speichern
        self._generate_and_save_controls()
        
        # 3. Daten laden
        self._load_data()
        
        # 4. Matrix erstellen
        self._build_matrix()
        
        # 5. UI erstellen
        self._create_ui()
        
        logger.info("✅ LINEARE Dialog-Initialisierung abgeschlossen")
    
    def _load_viewdata(self):
        """1. ViewDaten laden mit korrekter PdvmCentralDatenbank"""
        logger.info("🔧 Lade ViewDaten...")
        
        # KORREKTE PdvmCentralDatenbank-Initialisierung oder FEHLER
        try:
            view_db = PdvmCentralDatenbank(
                table_name="viewdaten", 
                guid=self.view_guid
            )
        except Exception as e:
            error_msg = f"❌ PdvmCentralDatenbank-Initialisierung fehlgeschlagen: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        try:
            # ROOT-Daten laden
            root_data = view_db.get_static_value(gruppe='ROOT', feld='VIEW_TABLE')
            if not root_data:
                raise ValueError(f"ROOT.VIEW_TABLE nicht gefunden für view_guid: {self.view_guid}")
            
            # METADATEN laden
            metadaten = view_db.get_static_value(gruppe='METADATEN', feld=root_data.upper())
            if not metadaten:
                raise ValueError(f"METADATEN.{root_data.upper()} nicht gefunden für view_guid: {self.view_guid}")
            
            if 'controls' not in metadaten:
                raise ValueError(f"METADATEN.{root_data.upper()}.controls nicht gefunden")
            
            if 'standard_control' not in metadaten or 'dummy' not in metadaten['standard_control']:
                raise ValueError(f"METADATEN.{root_data.upper()}.standard_control.dummy nicht gefunden - KEIN FALLBACK!")
            
            # View-Config zusammenstellen
            self.view_config = {
                'ROOT': {'view_table': root_data},
                'controls': metadaten['controls'],
                'standard_control': metadaten['standard_control']
            }
            
            logger.info(f"✅ ViewDaten geladen: Tabelle '{root_data}', {len(self.view_config['controls'])} Controls, Dummy vorhanden")
            
        except Exception as e:
            error_msg = f"ViewDaten-Ladung fehlgeschlagen für view_guid '{self.view_guid}': {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _generate_and_save_controls(self):
        """2. Controls linear generieren und in GCS speichern"""
        logger.info("🔧 Generiere Controls linear...")
        
        all_controls = {}
        
        # 2.1 Original Controls - KOMPLETT aus ViewDaten übernehmen
        for control_key, control_data in self.view_config['controls'].items():
            original_key = f"{control_key}_original"
            
            # KOMPLETTE Übernahme statt einzelner Eigenschaften
            all_controls[original_key] = control_data.copy()
            all_controls[original_key]['control_type'] = 'original'
            all_controls[original_key]['show'] = False
            
            # Datum-Expansion
            if control_data.get('type') == 'date':
                for suffix in ['_alter', '_jahr', '_monat', '_tag']:
                    expanded_key = f"{control_key}{suffix}_original"
                    all_controls[expanded_key] = control_data.copy()
                    all_controls[expanded_key]['feld'] = f"{control_key}{suffix}"
                    all_controls[expanded_key]['name'] = f"{control_data.get('name', control_key)} ({suffix[1:].title()})"
                    all_controls[expanded_key]['control_type'] = 'original'
                    all_controls[expanded_key]['show'] = False
        
        logger.info(f"✅ Original Controls erstellt: {len([k for k in all_controls if k.endswith('_original')])} Controls")
        
        # 2.2 Show Controls - Kopien der Original Controls
        original_controls = {k: v for k, v in all_controls.items() if k.endswith('_original')}
        for original_key, original_control in original_controls.items():
            show_key = original_key.replace('_original', '_show')
            all_controls[show_key] = original_control.copy()
            all_controls[show_key]['control_type'] = 'show'
            all_controls[show_key]['show'] = True
        
        logger.info(f"✅ Show Controls erstellt: {len([k for k in all_controls if k.endswith('_show')])} Controls")
        
        # 2.3 Dummy Control - KOMPLETT aus ViewDaten, KEIN FALLBACK
        dummy_data = self.view_config['standard_control']['dummy']
        all_controls['dummy'] = dummy_data.copy()
        all_controls['dummy']['control_type'] = 'dummy'
        
        logger.info(f"✅ Dummy Control erstellt")
        
        # 2.4 In GCS speichern
        self.gcs._db.set_value(
            gruppe=self.view_guid, 
            feld='controls', 
            wert=all_controls
        )
        self.gcs._db.save_all_values()
        
        self.controls_config = all_controls
        logger.info(f"✅ Controls gespeichert: {len(all_controls)} total")
    
    def _load_data(self):
        """3. Daten laden"""
        logger.info("🔧 Lade Daten...")
        
        try:
            table_name = self.view_config['ROOT']['view_table']
            data_db = PdvmCentralDatenbank(table_name=table_name)
            
            self.raw_records = data_db.get_all_records()
            
            # Performance-Instanzen erstellen
            self.optimized_instances = []
            for record in self.raw_records:
                instance = PdvmCentralDatenbank.create_with_data(
                    guid=record["uid"],
                    daten=record["daten"],
                    table_name=table_name
                )
                self.optimized_instances.append(instance)
            
            logger.info(f"✅ Daten geladen: {len(self.optimized_instances)} Instanzen")
            
        except Exception as e:
            logger.error(f"❌ Datenladung fehlgeschlagen: {e}")
            self.raw_records = []
            self.optimized_instances = []
    
    def _build_matrix(self):
        """4. Display-Matrix erstellen"""
        logger.info("🔧 Erstelle Matrix...")
        
        self.display_matrix = []
        
        for instance in self.optimized_instances:
            row_data = {}
            
            # Alle Controls durchgehen
            for control_key, control_config in self.controls_config.items():
                feld = control_config.get('feld')
                gruppe = control_config.get('gruppe', 'SYSTEM')
                
                if feld:
                    try:
                        value = instance.get_value(gruppe, feld, self.gcs.st_inst.PdvmDateTime)
                        row_data[control_key] = value
                    except:
                        row_data[control_key] = ''
                else:
                    row_data[control_key] = ''
            
            # Filter: Zeile nur hinzufügen wenn nicht alle Original-Felder leer sind
            if not self._all_original_fields_empty(row_data):
                self.display_matrix.append(row_data)
            else:
                logger.debug(f"⚠️ Zeile gefiltert (alle Original-Felder leer): {instance.guid}")
        
        logger.info(f"✅ Matrix erstellt: {len(self.display_matrix)} Zeilen (aus {len(self.optimized_instances)} Instanzen)")
    
    def _all_original_fields_empty(self, row_data):
        """Prüft ob alle Original-Felder einer Zeile leer/None sind"""
        # Sammle alle Original-Felder (enden mit '_original')
        original_fields = [key for key in row_data.keys() if key.endswith('_original')]
        
        if not original_fields:
            # Keine Original-Felder gefunden - Zeile behalten
            return False
        
        # Prüfe ob alle Original-Felder leer sind
        for field_key in original_fields:
            value = row_data.get(field_key)
            # Feld ist nicht leer wenn es einen Wert hat (nicht None, nicht leerer String, nicht 0 bei Zahlen)
            if value is not None and value != '' and value != 0:
                return False
        
        # Alle Original-Felder sind leer
        return True
    
    def _create_ui(self):
        """5. UI erstellen"""
        logger.info("🔧 Erstelle UI...")
        
        self.display = PdvmViewDisplay(self)
        
        logger.info("✅ UI erstellt")
    
    def get_display_widget(self):
        """Widget für Integration zurückgeben"""
        return self.display
    
    def reload(self):
        """Reload bei Stichtag-Änderung"""
        logger.info("🔄 Reload...")
        self._build_matrix()
        if self.display:
            self.display.refresh_table()


class PdvmViewDisplay(QWidget):
    """
    SAUBERES UI-Display für PdvmViewDialog
    """
    
    def __init__(self, view_dialog):
        super().__init__(view_dialog.parent)
        self.view_dialog = view_dialog
        self.header_label = None
        
        self._setup_ui()
        self.refresh_table()
    
    def _setup_ui(self):
        """UI-Setup"""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.header_label = QLabel(self.view_dialog.title)
        header_font = QFont("Segoe UI", 12, QFont.Bold)
        self.header_label.setFont(header_font)
        header_layout.addWidget(self.header_label)
        
        header_layout.addStretch()
        
        # Settings-Button
        self.settings_button = QToolButton()
        self.settings_button.setText("⚙️")
        header_layout.addWidget(self.settings_button)
        
        layout.addLayout(header_layout)
        
        # Tabelle
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)
        
        # Status
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
    
    def refresh_table(self):
        """Tabelle aktualisieren"""
        matrix = self.view_dialog.display_matrix
        
        if not matrix:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            self.status_label.setText("Keine Daten")
            return
        
        # Sichtbare Spalten ermitteln
        visible_columns = self._get_visible_columns()
        
        # Tabelle füllen
        self.table.setRowCount(len(matrix))
        self.table.setColumnCount(len(visible_columns))
        
        # Header
        headers = []
        for col in visible_columns:
            control = self.view_dialog.controls_config.get(col, {})
            headers.append(control.get('name', col))
        self.table.setHorizontalHeaderLabels(headers)
        
        # Daten
        for row_idx, row_data in enumerate(matrix):
            for col_idx, col_name in enumerate(visible_columns):
                value = row_data.get(col_name, '')
                item = QTableWidgetItem(str(value))
                self.table.setItem(row_idx, col_idx, item)
        
        # Status
        self.status_label.setText(f"{len(matrix)} Datensätze, {len(visible_columns)} Spalten")
    
    def _get_visible_columns(self):
        """Sichtbare Spalten ermitteln"""
        gcs = get_gcs()
        expert_mode = gcs.expert_mode
        
        visible = []
        for control_key, control in self.view_dialog.controls_config.items():
            if expert_mode:
                # Expert: alle mit visible=True
                if control.get('visible', False):
                    visible.append(control_key)
            else:
                # Normal: alle mit show=True
                if control.get('show', False):
                    visible.append(control_key)
        
        return visible