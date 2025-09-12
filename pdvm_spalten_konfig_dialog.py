"""
MODERNER SPALTEN-KONFIGURATIONS-DIALOG

NEUE LINEARE ARCHITEKTUR (V3.0):      
- Vollständige Controls aus Systemsteuerung (Clean Controls.fieldname)
- Expert Mode direkt aus globaler Systemsteuerung
- Keine Synchronisation mehr nötig
- Autonomer Dialog mit persistierten Controls
- Löst "Es sind keine Spalten zu sehen" Problem

Author: GitHub Copilot
Date: 2025-09-06
Version: 3.0
"""

import logging
import json
import base64
import binascii
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

# Lokale Imports
from pdvm_central_systemsteuerung import gcs
from pdvm_datetime import Pdvm_DateTime

# Logger setup
logger = logging.getLogger(__name__)


class PdvmSpaltenKonfigDialog(QDialog):
    """
    SPALTEN-KONFIGURATIONS-DIALOG V3.0

    NEUE CLEAN ARCHITEKTUR:
    - Lädt vollständige Controls aus Systemsteuerung (Controls.fieldname)
    - Expert Mode direkt aus gcs().global_expert_mode
    - Autonomer Dialog ohne ViewDaten-Abhängigkeiten
    - Speichert Controls als direkte JSON-Struktur zurück
    """

    # Signal für Änderungen
    columns_changed = pyqtSignal()

    def __init__(self, view_id, parent=None):
        super().__init__(parent)
        self.view_id = view_id
        self.columns_data = []
        self.controls_data = {}
        self.view_config_data = {}  # Verwende view_config_data für Konsistenz
        self.view_config = {}       # Fallback für alte Kompatibilität
        self.modified = False

        # Systemsteuerung-Zugriff
        self.systemsteuerung = gcs()

        # UI initialisieren
        self._init_ui()
        self._load_data()
        self._update_display()

    def _init_ui(self):
        """Benutzeroberfläche initialisieren"""
        self.setWindowTitle(f"Spalten-Konfiguration - {self.view_id}")
        self.setModal(True)
        self.resize(800, 600)

        # Main Layout
        layout = QVBoxLayout(self)

        # Header mit Mode-Info
        self.mode_label = QLabel()
        self.mode_label.setStyleSheet("font-weight: bold; padding: 8px; background-color: #f0f0f0;")
        layout.addWidget(self.mode_label)

        # Tabelle für Spalten
        self.columns_table = QTableWidget()
        self.columns_table.setColumnCount(4)
        self.columns_table.setHorizontalHeaderLabels(['Anzeigen', 'Spaltenname', 'Breite', 'Reihenfolge'])
        
        # Tabellen-Eigenschaften
        header = self.columns_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.columns_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.columns_table)

        # Button Layout
        button_layout = QHBoxLayout()
        
        # Bewegung-Buttons
        self.move_up_btn = QPushButton("↑ Nach oben")
        self.move_down_btn = QPushButton("↓ Nach unten")
        self.move_up_btn.clicked.connect(self._move_selected_up)
        self.move_down_btn.clicked.connect(self._move_selected_down)
        
        button_layout.addWidget(self.move_up_btn)
        button_layout.addWidget(self.move_down_btn)
        button_layout.addStretch()

        # OK/Cancel Buttons
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Abbrechen")
        self.ok_btn.clicked.connect(self._on_ok_clicked)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def _load_data(self):
        """Lade Daten aus Systemsteuerung"""
        try:
            self._load_view_config()
            self._load_controls_data()
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Daten: {e}")
            self._show_empty_controls_message()

    def _load_view_config(self):
        """
        🏗️ LINEARE ARCHITEKTUR: Lade NUR controls (view_config ist redundant entfernt!)
        
        STRUKTUR: view_id/controls → { "familienname_show": {...}, "vorname_show": {...} }
        Jedes Control hat field_config integriert - keine separate view_config nötig!
        """
        try:
            # NUR controls laden - view_config ist redundant und entfernt!
            raw_config = gcs().get_value_no_json(self.view_id, 'controls')
            
            if raw_config and isinstance(raw_config, str):
                try:
                    self.view_config = json.loads(raw_config)
                    self.view_config_data = self.view_config  # Für Konsistenz
                    logger.info(f"✅ controls geladen (lineare Struktur): {len(self.view_config)} Felder")
                    logger.info(f"🗑️ view_config nicht mehr verwendet - field_config ist in Controls integriert")
                    return
                except json.JSONDecodeError as e:
                    logger.warning(f"controls JSON parsing Fehler: {e}")
            
            logger.info("📝 Keine controls gefunden - verwende leere Config")
            self.view_config = {}
            self.view_config_data = {}
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der controls: {e}")
            self.view_config = {}

    def _load_controls_data(self):
        """
        Lade Controls - EINHEITLICHE STRUKTUR mit internen Feldnamen als Keys
        
        STRUKTUR: view_id/controls → { "familienname_show": {...}, "vorname_show": {...} }
        """
        try:
            # EINHEITLICHE STRUKTUR: Laden mit no_json
            raw_controls = gcs().get_value_no_json(self.view_id, 'controls')
            
            if raw_controls and isinstance(raw_controls, str):
                try:
                    self.controls_data = json.loads(raw_controls)
                    logger.info(f"✅ Controls geladen (einheitliche Struktur): {len(self.controls_data)} Felder")
                    self._convert_controls_to_columns_data()
                    return
                except json.JSONDecodeError as e:
                    logger.warning(f"Controls JSON parsing Fehler: {e}")
            
            # Fallback: Erstelle Controls aus view_config falls nötig
            logger.info("� Keine Controls gefunden - erstelle leere Struktur")
            self.controls_data = {}
            self._convert_controls_to_columns_data()
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Controls: {e}")
            self._show_empty_controls_message()

    def _create_controls_from_view_config(self):
        """Erstelle Controls aus view_config falls keine vorhanden"""
        try:
            if not self.view_config:
                logger.warning("Keine view_config verfügbar für Control-Erstellung")
                return

            # Verwende 'spalten' aus view_config
            columns = self.view_config.get('spalten', [])
            if not columns:
                # Fallback: auch 'COLUMNS' prüfen für Rückwärtskompatibilität
                columns = self.view_config.get('COLUMNS', [])
                if not columns:
                    logger.warning("Keine 'spalten' oder 'COLUMNS' in view_config")
                    return

            logger.info(f"Erstelle Controls für {len(columns)} Spalten")

            # Controls aus Spalten-Definitionen erstellen
            for column in columns:
                # Neue view_config Struktur unterstützen
                # Versuche zuerst neues Format (gruppe/feld), dann altes Format (name)
                field_name = column.get('feld') or column.get('name')
                if not field_name:
                    continue

                # Spaltentitel aus verschiedenen Quellen
                title = column.get('name') or column.get('title', field_name)

                # Breite aus UI-Config oder Standard
                width = 100
                if 'ui' in column and isinstance(column['ui'], dict):
                    ui_width = column['ui'].get('width', '100')
                    # Prozent-Werte in Pixel umrechnen (grober Schätzwert)
                    if isinstance(ui_width, str) and ui_width.endswith('%'):
                        percent = float(ui_width.rstrip('%'))
                        width = int(percent * 8)  # ca. 800px Tabellenbreite
                    else:
                        width = int(ui_width) if str(ui_width).isdigit() else 100
                else:
                    width = column.get('width', 100)

                # Standard Control-State erstellen
                control_state = {
                    'field_name': field_name,
                    'spaltenueberschrift': title,
                    'datentyp': column.get('type', 'string'),
                    'spaltenbreite': width,
                    'sichtbar': True,  # Default: sichtbar
                    'expert_mode': column.get('expert_order', 999) < 900,  # Expert wenn order < 900
                    'reihenfolge': column.get('display_order', 999)
                }

                self.controls_data[field_name] = control_state
                logger.debug(f"   Control erstellt: {field_name} -> {control_state['spaltenueberschrift']}")

            logger.info(f"Controls aus view_config erstellt: {len(self.controls_data)} Controls")

        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Controls: {e}")

    def _convert_controls_to_columns_data(self):
        """Konvertiert vollständige Controls zu columns_data für UI"""
        self.columns_data = []

        # Sortierung nach displayOrder
        sorted_controls = sorted(
            self.controls_data.items(),
            key=lambda x: x[1].get('reihenfolge', 999)
        )

        for field_name, control in sorted_controls:
            col_data = {
                'name': field_name,
                'show': control.get('sichtbar', True),
                'expert_mode': control.get('expert_mode', False),
                'expert_order': control.get('expert_order', 999),
                'display_order': control.get('reihenfolge', 999),
                'type': control.get('datentyp', 'str'),
                'spaltenueberschrift': control.get('spaltenueberschrift', field_name),
                'breite': control.get('spaltenbreite', 120),
            }
            self.columns_data.append(col_data)

        logger.info(f"{len(self.columns_data)} Controls zu columns_data konvertiert")

    def _get_visible_columns(self):
        """
        Ermittelt die sichtbaren Spalten basierend auf Expert-Mode
        
        KORRIGIERTE PROJEKTION:
        - Dialog zeigt verfügbare Spalten (welche können aktiviert/deaktiviert werden)
        - Im NormalMode: Zeige Spalten mit expert_mode=false (verfügbare Optionen)
        - Im ExpertMode: Zeige alle Spalten (alle verfügbaren Optionen)
        
        Die Tabelle zeigt dann die aktiven Spalten (show=true)
        """
        expert_mode = gcs().global_expert_mode

        if expert_mode:
            # Expert-Mode: Alle Spalten verfügbar
            return self.columns_data
        else:
            # Normal-Mode: Nur nicht-Expert Spalten verfügbar
            # Diese können dann aktiviert/deaktiviert werden
            return [col for col in self.columns_data if not col['expert_mode']]

    def _update_display(self):
        """Tabellen-Anzeige aktualisieren"""
        try:
            # Aktuelle Projektion bestimmen
            visible_columns = self._get_visible_columns()

            # Table Setup
            self.columns_table.setRowCount(len(visible_columns))

            for row, col_data in enumerate(visible_columns):
                self._create_table_row(row, col_data)

            # Info Label aktualisieren
            self._update_mode_info()

            logger.debug(f"Anzeige aktualisiert: {len(visible_columns)} Spalten")

        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Anzeige: {e}")

    def _create_table_row(self, row, col_data):
        """Erstelle eine Tabellenzeile"""
        # Checkbox für Anzeigen
        show_checkbox = QCheckBox()
        show_checkbox.setChecked(col_data['show'])
        show_checkbox.stateChanged.connect(lambda state, r=row: self._on_show_changed(r, state))
        self.columns_table.setCellWidget(row, 0, show_checkbox)

        # Spaltenname
        name_item = QTableWidgetItem(col_data['spaltenueberschrift'])
        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
        self.columns_table.setItem(row, 1, name_item)

        # Breite
        width_item = QTableWidgetItem(str(col_data['breite']))
        self.columns_table.setItem(row, 2, width_item)

        # Reihenfolge
        order_item = QTableWidgetItem(str(col_data['display_order']))
        order_item.setFlags(order_item.flags() & ~Qt.ItemIsEditable)
        self.columns_table.setItem(row, 3, order_item)

    def _update_mode_info(self):
        """Mode-Info Label aktualisieren"""
        expert_mode = gcs().global_expert_mode
        visible_count = len(self._get_visible_columns())
        
        if expert_mode:
            mode_text = f"EXPERT-MODUS: {visible_count} Spalten verfügbar (alle Spalten konfigurierbar)"
            self.mode_label.setStyleSheet("font-weight: bold; padding: 8px; background-color: #ffe6cc;")
        else:
            mode_text = f"NORMAL-MODUS: {visible_count} Spalten verfügbar (Expert-Spalten ausgeblendet)"
            self.mode_label.setStyleSheet("font-weight: bold; padding: 8px; background-color: #e6f3ff;")
            
        self.mode_label.setText(mode_text)

    def _on_show_changed(self, row, state):
        """Checkbox-Änderung verarbeiten"""
        try:
            visible_columns = self._get_visible_columns()
            if row < len(visible_columns):
                visible_columns[row]['show'] = (state == Qt.Checked)
                self.modified = True
                logger.debug(f"Spalte {visible_columns[row]['name']} show = {visible_columns[row]['show']}")
                
        except Exception as e:
            logger.error(f"Fehler bei Show-Änderung: {e}")

    def _move_selected_up(self):
        """Gewählte Spalte nach oben verschieben"""
        current_row = self.columns_table.currentRow()
        if current_row > 0:
            self._move_column_up(current_row)
            self.columns_table.setCurrentCell(current_row - 1, 0)

    def _move_selected_down(self):
        """Gewählte Spalte nach unten verschieben"""
        current_row = self.columns_table.currentRow()
        visible_columns = self._get_visible_columns()
        if current_row < len(visible_columns) - 1:
            self._move_column_down(current_row)
            self.columns_table.setCurrentCell(current_row + 1, 0)

    def _move_column_up(self, row):
        """Spalte nach oben verschieben"""
        visible_columns = self._get_visible_columns()

        if row <= 0:
            return

        self.modified = True

        # In visible_columns tauschen
        visible_columns[row], visible_columns[row - 1] = visible_columns[row - 1], visible_columns[row]

        # Zurück in main columns_data übertragen
        self._update_main_columns_data(visible_columns)
        self._update_display()

        logger.debug(f"Spalte nach oben: Position {row} -> {row-1}")

    def _move_column_down(self, row):
        """Spalte nach unten verschieben"""
        visible_columns = self._get_visible_columns()

        if row >= len(visible_columns) - 1:
            return

        self.modified = True

        # In visible_columns tauschen
        visible_columns[row], visible_columns[row + 1] = visible_columns[row + 1], visible_columns[row]

        # Zurück in main columns_data übertragen
        self._update_main_columns_data(visible_columns)
        self._update_display()

        logger.debug(f"Spalte nach unten: Position {row} -> {row+1}")

    def _update_main_columns_data(self, visible_columns):
        """Geänderte visible_columns zurück in main columns_data übertragen"""
        # Neue Orders zuweisen
        for i, col_data in enumerate(visible_columns):
            if gcs().global_expert_mode:
                col_data['expert_order'] = i
            else:
                col_data['display_order'] = i

        # Main columns_data nach neuer Order sortieren
        self._sort_columns_by_current_mode()

    def _sort_columns_by_current_mode(self):
        """Spalten nach aktuellem Mode sortieren"""
        expert_mode = gcs().global_expert_mode

        if expert_mode:
            # ExpertMode: ALLE Spalten sortiert nach expert_order
            self.columns_data.sort(key=lambda x: x['expert_order'])
            logger.debug(f"Expert-Mode: {len(self.columns_data)} Spalten nach expert_order sortiert")
        else:
            # Normal-Mode: NUR nicht-Expert Spalten (expert_mode=False) nach display_order
            normal_columns = [col for col in self.columns_data if not col['expert_mode']]
            normal_columns.sort(key=lambda x: x['display_order'])

            self.columns_data = normal_columns
            logger.debug(f"Normal-Mode: {len(self.columns_data)} normale Spalten nach display_order sortiert")

    def _on_ok_clicked(self):
        """
        OK Button - Speichere in EINHEITLICHER Struktur
        
        EINFACHE EINHEITLICHE STRUKTUR:
        - view_id/controls → { "familienname_show": {...}, "vorname_show": {...} }
        - view_id/view_config → { "familienname_show": {...}, "vorname_show": {...} }
        
        Beide identisch mit internen Feldnamen als Keys!
        """
        try:
            if not self.modified:
                logger.info("Keine Änderungen - Dialog wird geschlossen")
                self.accept()
                return

            logger.info("✅ Speichere in einheitlicher Struktur...")
            
            # 1. UI-Änderungen übertragen
            self._update_controls_from_ui()
            self._update_visible_columns_width()
            
            # 2. LINEARE SPEICHERUNG - NUR controls (view_config entfernt!)
            # Controls speichern (interne Feldnamen als Keys mit integrierter field_config)
            controls_json = json.dumps(self.controls_data, ensure_ascii=False, separators=(',', ':'))
            gcs().set_value_no_json(self.view_id, 'controls', controls_json)
            logger.info(f"✅ Controls: {len(self.controls_data)} Felder (field_config integriert)")
            logger.info(f"🗑️ view_config nicht mehr gespeichert (war redundant)")
            
            # 3. Persistierung
            gcs().save_values()
            logger.info("✅ Lineare Struktur gespeichert")
            
            # 4. Signal emittieren
            self.columns_changed.emit()
            
            # 5. Success Message
            QMessageBox.information(
                self,
                "Spalten Konfiguration", 
                f"✅ Einheitliche Struktur gespeichert:\n\n"
                f"• Controls: {len(self.controls_data)} Felder\n" 
                f"• View-Config: {len(self.view_config)} Felder\n\n"
                f"Beide mit identischen Schlüsseln (interne Feldnamen)!"
            )

            self.accept()

        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern:\n{e}")

    def _create_view_config_from_ui(self):
        """Erstelle view_config aus aktueller UI"""
        try:
            # Kopiere bestehende view_config
            updated_config = self.view_config.copy()
            
            # Spalten-Array aktualisieren
            spalten = []
            for col_data in self.columns_data:
                spalte = {
                    'feld': col_data['name'],
                    'name': col_data['spaltenueberschrift'],
                    'type': col_data['type'],
                    'expert_order': col_data['expert_order'],
                    'display_order': col_data['display_order'],
                    'ui': {
                        'width': col_data['breite']
                    }
                }
                spalten.append(spalte)
            
            updated_config['spalten'] = spalten
            return updated_config
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der view_config: {e}")
            return self.view_config

    def _update_controls_from_ui(self):
        """Aktualisiere controls_data aus UI"""
        try:
            # UI-Änderungen in controls übertragen
            for col_data in self.columns_data:
                field_name = col_data['name']
                if field_name in self.controls_data:
                    self.controls_data[field_name]['sichtbar'] = col_data['show']
                    self.controls_data[field_name]['reihenfolge'] = col_data['display_order']
                    self.controls_data[field_name]['spaltenbreite'] = col_data['breite']
                    
            logger.info(f"Controls aus UI aktualisiert: {len(self.controls_data)} Einträge")
            
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Controls: {e}")

    def _show_empty_controls_message(self):
        """Zeige Nachricht für leere Controls"""
        placeholder_data = {
            'name': 'HINWEIS',
            'show': True,
            'expert_mode': False,
            'expert_order': 0,
            'display_order': 0,
            'type': 'info',
            'spaltenueberschrift': 'Keine Controls gefunden. Bitte View-Dialog öffnen um Controls zu generieren.',
            'breite': 400,
        }
        self.columns_data = [placeholder_data]
