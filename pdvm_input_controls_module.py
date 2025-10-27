# pdvm_input_controls_module.py
# -*- coding: utf-8 -*-
"""
🎯 PDVM INPUT CONTROLS MODULE - Erstes Edit-Modul für GenerellerDialog

MODULARER ANSATZ:
- Einfache API: __init__(framedaten_db, selected_guid)
- Eigenständiges Widget mit get_widget()
- Linear und übersichtlich
- GCS via globalen Import (nicht als Parameter!)

VERANTWORTLICHKEITEN:
- Header anzeigen
- GUID anzeigen
- Später: Input-Controls aufbauen

Version: 1.0.0 (Neu - Modularer Ansatz)
"""

import logging
from typing import Optional, Dict, Any, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QLineEdit, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject

from global_gcs import gcs  # ← Globaler GCS-Import!
from pdvm_central_datenbank import PdvmCentralDatenbank
from pdvm_datetime import Pdvm_DateTime
from pdvm_date_time_picker import PdvmDateTimePicker

logger = logging.getLogger(__name__)


class PdvmInputControl(QWidget):
    """
    Gekapseltes Input-Control Widget
    
    Zeigt:
    - Label (Feldname)
    - Wert (aus DB)
    - Abdatum (formatiert)
    
    Später:
    - Editierbar
    - Validierung
    - Plausibilitätsprüfung
    """
    
    def __init__(self, field_key: str, field_config: dict, db_instance, parent=None):
        """
        Args:
            field_key: Schlüssel (TABELLE_GRUPPE_FELD)
            field_config: Feld-Konfiguration aus Metadaten
            db_instance: PdvmCentralDatenbank Instanz für Datenzugriff
            parent: Parent-Widget
        """
        super().__init__(parent)
        
        self.field_key = field_key
        self.field_config = field_config
        self.db_instance = db_instance
        
        # Key parsen: TABELLE_GRUPPE_FELD
        parts = field_key.split('_')
        if len(parts) >= 3:
            self.table = parts[0]  # z.B. "PERSONDATEN"
            self.gruppe = parts[1].upper()  # z.B. "PERSDATEN"
            self.feld = '_'.join(parts[2:]).upper()  # z.B. "FAMILIENNAME"
        else:
            logger.error(f"❌ Ungültiger Field-Key: {field_key}")
            self.table = self.gruppe = self.feld = "UNKNOWN"
        
        # AUTONOME DATENHALTUNG
        self.original_value = None   # Aus DB geladen (roh)
        self.current_value = None    # Aktueller Wert (roh)
        self.is_dirty = False        # Geändert?
        
        # STATISCHE ABDATUM-INSTANZ (wird nur beim Init erstellt!)
        from pdvm_datetime import Pdvm_DateTime
        self.abdatum_instanz = Pdvm_DateTime(gcs.field_value('country'))
        self.abdatum_instanz.PdvmDateTime = gcs.st_inst.PdvmDateTime  # Stichtag
        logger.debug(f"  📅 Abdatum-Instanz erstellt für {self.field_key}: {self.abdatum_instanz.FormTimeStamp}")
        
        # Wert und Abdatum aus DB laden
        self.wert = None
        self.abdatum = None
        self._load_value()
        
        # UI erstellen
        self._create_ui()
    
    def _load_value(self):
        """
        Lädt Wert und Abdatum aus Datenbank (AUTONOM)
        
        Verwendet die STATISCHE Abdatum-Instanz (self.abdatum_instanz)
        Diese wird nur beim __init__ erstellt und ändert sich nie!
        
        get_value() gibt zurück:
        - wert: Der Wert zu diesem Abdatum
        - abdatum: Das TATSÄCHLICHE Abdatum, wann der Wert gespeichert wurde
        """
        if not self.db_instance:
            logger.warning(f"⚠️ Keine DB-Instanz für {self.field_key} → Control wird schreibgeschützt")
            self.wert = None
            self.abdatum = None
            self.original_value = None
            self.current_value = None
            return
        
        try:
            # Wert laden mit STATISCHER Abdatum-Instanz!
            # Diese enthält den Stichtag und ändert sich nie!
            self.wert, self.abdatum = self.db_instance.get_value(
                self.gruppe,
                self.feld,
                self.abdatum_instanz.PdvmDateTime  # ← STATISCH (Stichtag)!
            )
            
            # AUTONOMIE: Original-Werte speichern
            self.original_value = self.wert
            self.current_value = self.wert
            
            logger.debug(f"  📊 {self.field_key}: wert={str(self.wert)[:30]}, abdatum={self.abdatum}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden von {self.field_key}: {e}")
            self.wert = None
            self.abdatum = None
            self.original_value = None
            self.current_value = None
    
    def refresh(self):
        """
        REFRESH-Kommando: Wert aus Instanz neu laden und UI aktualisieren
        
        Wird vom Manager aufgerufen nach save_all_values()
        """
        logger.debug(f"  🔄 Refresh: {self.field_key}")
        
        # Wert neu laden (aus Instanz)
        self._load_value()
        
        # UI aktualisieren
        if hasattr(self, 'value_label'):
            # Wert formatieren
            display_value = str(self.wert) if self.wert is not None else "(leer)"
            if len(display_value) > 50:
                display_value = display_value[:47] + "..."
            
            self.value_label.setText(display_value)
            
            # Tooltip mit Abdatum aktualisieren
            if self.abdatum:
                from pdvm_datetime import Pdvm_DateTime
                dt = Pdvm_DateTime(gcs.field_value('country'))
                dt.PdvmDateTime = float(self.abdatum)
                tooltip = f"Abdatum: {dt.FormTimeStamp}"
                self.value_label.setToolTip(tooltip)
            
        # is_dirty zurücksetzen (da neu geladen)
        self.is_dirty = False
        logger.debug(f"  ✅ Refresh abgeschlossen: {self.field_key}")
    
    def _create_ui(self):
        """Erstellt UI für Input-Control"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # === LABEL (Feldname) ===
        label_text = self.field_config.get('label', self.feld)
        label = QLabel(label_text + ":")
        label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #2c3e50;
                min-width: 150px;
                max-width: 150px;
            }
        """)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label)
        
        # === WERT (abhängig vom Type) ===
        field_type = self.field_config.get('type', 'text')
        
        # SCHREIBSCHUTZ: Wenn keine DB-Instanz vorhanden
        is_readonly = (self.db_instance is None)
        
        if field_type == 'text':
            # Type: text → QLineEdit (editierbar oder schreibgeschützt)
            wert_text = str(self.wert) if self.wert is not None else ""
            wert_edit = QLineEdit(wert_text)
            
            if is_readonly:
                # SCHREIBGESCHÜTZT
                wert_edit.setReadOnly(True)
                wert_edit.setStyleSheet("""
                    QLineEdit {
                        color: #95a5a6;
                        padding: 5px;
                        background-color: #ecf0f1;
                        border: 1px solid #bdc3c7;
                        border-radius: 3px;
                        min-width: 200px;
                    }
                """)
                wert_edit.setPlaceholderText("(keine Zuordnung)")
            else:
                # EDITIERBAR
                wert_edit.setStyleSheet("""
                    QLineEdit {
                        color: #34495e;
                        padding: 5px;
                        background-color: white;
                        border: 1px solid #3498db;
                        border-radius: 3px;
                        min-width: 200px;
                    }
                """)
                wert_edit.textChanged.connect(self._on_value_changed)
            
            layout.addWidget(wert_edit)
            self.value_widget = wert_edit
            
        elif field_type == 'date':
            # Type: date → PdvmDateTimePicker
            dt_instance = Pdvm_DateTime(gcs.field_value('country'))
            if self.wert:
                try:
                    dt_instance.PdvmDateTime = float(self.wert)
                except:
                    pass
            
            # display_val aus Config holen (z.B. "only_date", "all")
            display_val = self.field_config.get('display_val', 'only_date')
            
            if is_readonly:
                # SCHREIBGESCHÜTZT: Nur als Label anzeigen
                wert_text = dt_instance.FormTimeStamp if self.wert else "(keine Zuordnung)"
                wert_label = QLabel(wert_text)
                wert_label.setStyleSheet("""
                    QLabel {
                        color: #95a5a6;
                        padding: 5px;
                        background-color: #ecf0f1;
                        border: 1px solid #bdc3c7;
                        border-radius: 3px;
                        min-width: 200px;
                    }
                """)
                layout.addWidget(wert_label)
                self.value_widget = wert_label
            else:
                # EDITIERBAR: DateTimePicker
                date_picker = PdvmDateTimePicker(
                    parent=self,
                    pdvm_datetime=dt_instance,
                    display=display_val
                )
                layout.addWidget(date_picker)
                self.value_widget = date_picker
            
        else:
            # Andere Types: Read-Only Label (vorerst)
            wert_text = str(self.wert) if self.wert is not None else ""
            wert_label = QLabel(wert_text)
            wert_label.setStyleSheet("""
                QLabel {
                    color: #34495e;
                    padding: 5px;
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 3px;
                    min-width: 200px;
                }
            """)
            wert_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            layout.addWidget(wert_label)
            self.value_widget = wert_label
        
        # === SCHREIBSCHUTZ-HINWEIS ===
        if is_readonly:
            readonly_hint = QLabel("🔒")
            readonly_hint.setStyleSheet("""
                QLabel {
                    color: #95a5a6;
                    font-size: 16px;
                }
            """)
            readonly_hint.setToolTip("Keine Zuordnung vorhanden - Feld ist schreibgeschützt")
            layout.addWidget(readonly_hint)
        
        # === RESET-BUTTON (pro Control) ===
        if not is_readonly:
            self.reset_button = QPushButton("↶")
            self.reset_button.setToolTip("Änderungen zurücksetzen")
            self.reset_button.setStyleSheet("""
                QPushButton {
                    background-color: #95a5a6;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 3px;
                    padding: 5px;
                    max-width: 30px;
                    min-width: 30px;
                }
                QPushButton:hover {
                    background-color: #7f8c8d;
                }
            """)
            self.reset_button.setVisible(False)  # Initial versteckt
            self.reset_button.clicked.connect(self.reset_to_original)
            layout.addWidget(self.reset_button)
        else:
            self.reset_button = None
        
        # === ABDATUM ===
        if self.abdatum:
            # Formatieren mit Pdvm_DateTime
            dt = Pdvm_DateTime(gcs.field_value('country'))
            try:
                dt.PdvmDateTime = float(self.abdatum)
                abdatum_text = dt.FormTimeStamp
            except:
                abdatum_text = str(self.abdatum)
            
            abdatum_label = QLabel(f"📅 {abdatum_text}")
            abdatum_label.setStyleSheet("""
                QLabel {
                    color: #7f8c8d;
                    font-size: 10px;
                    font-style: italic;
                    padding: 3px;
                }
            """)
            layout.addWidget(abdatum_label)
        
        layout.addStretch()
    
    def _on_value_changed(self, new_value=None):
        """
        Wird aufgerufen wenn Wert geändert wird
        
        AUTONOME Dirty-Tracking-Logik:
        - Aktualisiert current_value
        - Setzt is_dirty Flag
        - Zeigt visuelles Feedback
        """
        # Storage-Wert holen (type-spezifisch)
        self.current_value = self.get_storage_value()
        
        # Dirty-Flag setzen
        self.is_dirty = (self.current_value != self.original_value)
        
        # Visuelles Feedback
        self._update_visual_dirty_state()
        
        logger.debug(f"  🔄 {self.field_key}: dirty={self.is_dirty}, current={str(self.current_value)[:30]}")
    
    # ========================================================================
    # AUTONOME METHODEN (Type-spezifisch)
    # ========================================================================
    
    def get_display_value(self):
        """
        Holt ANGEZEIGTEN Wert aus Widget
        
        Type-spezifisch:
        - text: QLineEdit.text()
        - date: PdvmDateTimePicker → PdvmDateTime
        - dropdown: QComboBox.currentText()
        """
        if isinstance(self.value_widget, QLineEdit):
            return self.value_widget.text()
        
        elif hasattr(self.value_widget, 'get_pdvm_datetime'):
            # PdvmDateTimePicker
            self.value_widget.save()  # Initial → pdvm_datetime
            return self.value_widget.get_pdvm_datetime().PdvmDateTime
        
        # Weitere Types später...
        else:
            # Fallback: text()
            if hasattr(self.value_widget, 'text'):
                return self.value_widget.text()
            return None
    
    def get_storage_value(self):
        """
        Konvertiert Display → Storage (falls nötig)
        
        Bei den meisten Types ist Display == Storage
        """
        return self.get_display_value()
    
    def set_display_value(self, value):
        """
        Setzt ANGEZEIGTEN Wert im Widget
        
        Type-spezifisch:
        - text: QLineEdit.setText()
        - date: PdvmDateTimePicker aktualisieren
        - dropdown: QComboBox.setCurrentIndex()
        """
        if isinstance(self.value_widget, QLineEdit):
            self.value_widget.setText(str(value) if value is not None else "")
        
        elif hasattr(self.value_widget, 'get_pdvm_datetime'):
            # PdvmDateTimePicker
            if value:
                dt = self.value_widget.get_pdvm_datetime()
                dt.PdvmDateTime = float(value)
                self.value_widget.refresh_from_instance()
        
        # Weitere Types später...
    
    def save_to_db(self, neues_abdatum):
        """
        AUTONOMES SPEICHERN
        
        Nur aufrufen wenn is_dirty == True!
        
        Returns:
            bool: Erfolg
        """
        if not self.db_instance:
            logger.warning(f"⚠️ {self.field_key}: Kein Speichern möglich (schreibgeschützt)")
            return False
        
        try:
            storage_value = self.get_storage_value()
            
            # In DB speichern (noch nicht committen!)
            self.db_instance.set_value(
                self.gruppe,
                self.feld,
                storage_value,
                neues_abdatum
            )
            
            # Nach Speichern: Original aktualisieren
            self.original_value = storage_value
            self.current_value = storage_value
            self.is_dirty = False
            
            # Visuelles Feedback zurücksetzen
            self._update_visual_dirty_state()
            
            logger.info(f"  💾 {self.field_key}: Gespeichert mit Abdatum {neues_abdatum}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern von {self.field_key}: {e}")
            return False
    
    def reset_to_original(self):
        """AUTONOMES ZURÜCKSETZEN"""
        logger.info(f"  ↶ {self.field_key}: Zurücksetzen auf Original")
        
        # Widget auf Original-Wert setzen
        self.set_display_value(self.original_value)
        
        # Status zurücksetzen
        self.current_value = self.original_value
        self.is_dirty = False
        
        # Visuelles Feedback
        self._update_visual_dirty_state()
    
    def _update_visual_dirty_state(self):
        """Visuelles Feedback für Dirty-Status"""
        if self.is_dirty:
            # Gelber Hintergrund
            self.setStyleSheet("""
                QWidget {
                    background-color: #fff3cd;
                    border-left: 3px solid #ffc107;
                    padding-left: 5px;
                }
            """)
            if self.reset_button:
                self.reset_button.setVisible(True)
        else:
            # Normal
            self.setStyleSheet("")
            if self.reset_button:
                self.reset_button.setVisible(False)


class PdvmInputControlsModule(QObject):
    """
    Input-Controls Modul für GenerellerDialog
    
    EINFACHE API:
    - __init__(framedaten_db, selected_guid)
    - get_widget() → QWidget
    - GCS via globalen Import
    
    PHASE 1: Header + GUID anzeigen
    PHASE 2: Input-Controls aufbauen (später)
    
    SIGNALS:
    - refresh_requested: Wird emittiert, wenn Dialog refreshed werden soll
    """
    
    # Signal für Refresh-Request
    refresh_requested = pyqtSignal()
    
    def __init__(self, framedaten_db, selected_guid: str):
        """
        Initialisiert Input-Controls Modul
        
        Args:
            framedaten_db: PdvmCentralDatenbank Instanz für Framedaten
            selected_guid: GUID des ausgewählten Datensatzes
        """
        super().__init__()  # QObject initialisieren
        
        logger.info("🎯 === PDVM INPUT CONTROLS MODULE INITIALISIERUNG ===")
        logger.info(f"  📋 Selected GUID: {selected_guid}")
        
        self.framedaten_db = framedaten_db
        self.selected_guid = selected_guid
        # gcs via globalen Import verfügbar!
        
        # Instanzen-Manager für dynamische DB-Zugriffe
        # Key-Format: {TABELLE}_{GUID} für eindeutige Zuordnung
        self.db_instances: Dict[str, PdvmCentralDatenbank] = {}
        
        # Controls-Metadaten mit Order (für Sortierung)
        self.controls_meta: List[Dict[str, Any]] = []
        
        # AUTONOME CONTROLS-LISTE
        self.controls: List[PdvmInputControl] = []  # Alle erstellten Controls
        
        # ROOT-Tabelle und Metadaten
        self.root_table = None
        self.metadaten = {}
        
        # Header-Text aus Framedaten laden
        self._load_header()
        
        # ROOT-Tabelle aus Framedaten laden
        self._load_root_table()
        
        # ROOT-Instanz erstellen
        self._create_root_instance()
        
        # Metadaten laden
        self._load_metadaten()
        
        # === 3-PHASEN LINEARE VERARBEITUNG ===
        logger.info("🔄 Starte 3-Phasen-Verarbeitung...")
        
        # PHASE 1: Controls mit Order aufbauen
        self._prepare_controls()
        
        # PHASE 2: Alle benötigten Instanzen erstellen
        self._prepare_instances()
        
        # PHASE 3: Rendern erfolgt in get_widget()
        
        logger.info("✅ InputControlsModule initialisiert")
    
    def _load_root_table(self):
        """Lädt ROOT_TABLE aus Framedaten"""
        try:
            self.root_table, _ = self.framedaten_db.get_value('ROOT', 'ROOT_TABLE')
            
            # Fallback
            if not self.root_table:
                self.root_table, _ = self.framedaten_db.get_value('ROOT', 'root_table')
            
            if not self.root_table:
                raise ValueError("ROOT_TABLE nicht in Framedaten gefunden!")
            
            logger.info(f"  📋 ROOT-Table: {self.root_table}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der ROOT_TABLE: {e}")
            raise
    
    def _create_root_instance(self):
        """Erstellt Instanz für ROOT-Tabelle"""
        try:
            logger.info("  🔧 Erstelle ROOT-Instanz...")
            
            # ROOT-Tabelle in Kleinbuchstaben für DB
            table_name = self.root_table.lower()
            
            # Instanz erstellen
            root_instance = PdvmCentralDatenbank(
                table_name=table_name,
                guid=self.selected_guid
            )
            
            # In Instanzen-Manager speichern
            # Key-Format: {TABELLE}_{GUID} (wie alle anderen Instanzen)
            instance_key = f"{self.root_table.upper()}_{self.selected_guid}"
            self.db_instances[instance_key] = root_instance
            
            logger.info(f"  ✅ ROOT-Instanz erstellt: {instance_key}")
            logger.info(f"     Tabelle: {table_name} | GUID: {self.selected_guid}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der ROOT-Instanz: {e}")
            raise
    
    def _load_metadaten(self):
        """Lädt Metadaten aus Framedaten"""
        try:
            logger.info("  📂 Lade Metadaten...")
            
            # Metadaten aus Gruppe laden (Großbuchstaben!)
            self.metadaten = self.framedaten_db.get_gruppe('METADATEN')
            
            # Fallback
            if not self.metadaten:
                logger.warning("    ⚠️ Gruppe 'METADATEN' nicht gefunden, versuche 'Metadaten'...")
                self.metadaten = self.framedaten_db.get_gruppe('Metadaten')
            
            if not self.metadaten:
                logger.warning("  ⚠️ Keine Metadaten gefunden!")
                self.metadaten = {}
            else:
                logger.info(f"  ✅ {len(self.metadaten)} Input-Controls in Metadaten gefunden")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Metadaten: {e}")
            self.metadaten = {}
    
    # ========================================================================
    # 3-PHASEN LINEARE VERARBEITUNG
    # ========================================================================
    
    def _prepare_controls(self):
        """
        PHASE 1: Baut Control-Metadaten mit Order auf
        
        Logik:
        - source_path = 'root' → Order 1000
        - source_path = 'root_GRUPPE' → Order 2000, 2001, 2002...
        - Später: User kann Order ändern (Expert Mode)
        """
        logger.info("📋 PHASE 1: Controls mit Order aufbauen...")
        
        if not self.metadaten:
            logger.warning("  ⚠️ Keine Metadaten vorhanden!")
            return
        
        base_order = 1000  # ROOT-Controls
        extended_order = 2000  # Andere Controls
        
        for field_key, field_config in self.metadaten.items():
            # Source-Path aus Config (Default: 'root')
            source_path = field_config.get('source_path', 'root')
            
            # Order berechnen
            if source_path == 'root':
                order = base_order
                base_order += 1  # Nächstes ROOT-Control
            else:
                # root_GRUPPE → höhere Order
                order = extended_order
                extended_order += 1
            
            # Control-Metadaten speichern
            control_meta = {
                'field_key': field_key,
                'field_config': field_config,
                'source_path': source_path,
                'order': order
            }
            self.controls_meta.append(control_meta)
            
            logger.debug(f"  📝 Control: {field_key} | source_path: {source_path} | order: {order}")
        
        # Nach Order sortieren
        self.controls_meta.sort(key=lambda x: x['order'])
        
        logger.info(f"  ✅ {len(self.controls_meta)} Controls vorbereitet (sortiert nach Order)")
    
    def _prepare_instances(self):
        """
        PHASE 2: Baut alle benötigten DB-Instanzen auf
        
        Logik:
        - ROOT-Instanz bereits vorhanden (mit selected_guid)
        - Für jedes Control: Prüfe source_path
          * source_path = 'root' → ROOT-Instanz verwenden
          * source_path = 'root_GRUPPE' → GUID aus ROOT holen → Neue Instanz
        - Instance-Key: {TABELLE}_{GUID}
        """
        logger.info("🔧 PHASE 2: DB-Instanzen aufbauen...")
        
        if not self.controls_meta:
            logger.warning("  ⚠️ Keine Controls vorhanden!")
            return
        
        instances_created = 0
        
        for control_meta in self.controls_meta:
            source_path = control_meta['source_path']
            field_key = control_meta['field_key']
            field_config = control_meta['field_config']
            
            logger.info(f"  🔍 Processing Control: {field_key}")
            logger.info(f"     source_path: {source_path}")
            
            # Tabelle aus Field-Key extrahieren
            parts = field_key.split('_')
            if len(parts) < 3:
                logger.warning(f"  ⚠️ Ungültiger field_key: {field_key}")
                continue
            
            table_name = parts[0]  # z.B. "FINANZWESEN"
            gruppe = parts[1].upper()  # z.B. "FINANZWESEN"
            
            logger.info(f"     table: {table_name}, gruppe: {gruppe}")
            
            if source_path == 'root':
                # ROOT-Instanz verwenden (bereits vorhanden)
                instance_key = f"{self.root_table.upper()}_{self.selected_guid}"
                logger.debug(f"  🔗 {field_key} → ROOT-Instanz ({instance_key})")
                continue
            
            # source_path = 'root_GRUPPE' → GUID holen
            # Format: root_PERSDATEN
            if not source_path.startswith('root_'):
                logger.warning(f"  ⚠️ Ungültiger source_path: {source_path}")
                continue
            
            # Gruppe aus source_path extrahieren
            source_gruppe = source_path[5:]  # Nach "root_"
            
            # FELDSCHLÜSSEL: {GRUPPE}-{TABELLE} (aus field_key berechnet)
            # Beispiel: FINANZDATEN_FINANZDATEN_KONTOINHABER → FINANZDATEN-FINANZDATEN
            feld_schluessel = f"{gruppe}-{table_name}".upper()
            
            logger.debug(f"  � Suche GUID: {source_gruppe}.{feld_schluessel}")
            
            # GUID aus ROOT-Instanz holen
            try:
                root_instance_key = f"{self.root_table.upper()}_{self.selected_guid}"
                root_instance = self.db_instances.get(root_instance_key)
                
                if not root_instance:
                    logger.error(f"  ❌ ROOT-Instanz nicht gefunden: {root_instance_key}")
                    continue
                
                # GUID aus ROOT holen
                stichtag = gcs.st_inst.PdvmDateTime
                result = root_instance.get_value(source_gruppe, feld_schluessel, stichtag)
                
                if isinstance(result, tuple):
                    guid, abdatum = result
                else:
                    guid = result
                
                if not guid:
                    logger.warning(f"  ⚠️ Keine GUID gefunden: {source_gruppe}.{feld_schluessel}")
                    logger.warning(f"     → Control wird schreibgeschützt angezeigt (keine Zuordnung)")
                    # WICHTIG: NICHT continue - Control soll trotzdem angezeigt werden!
                    # Stattdessen merken, dass keine Instanz verfügbar ist
                    # → In _get_instance_for_control() wird dann None zurückgegeben
                    # → In PdvmInputControl wird das Control schreibgeschützt
                    continue
                
                # Instance-Key: TABELLE_GUID
                instance_key = f"{table_name.upper()}_{guid}"
                
                # Prüfe ob Instanz bereits existiert
                if instance_key in self.db_instances:
                    logger.debug(f"  ♻️ Instanz bereits vorhanden: {instance_key}")
                    continue
                
                # Neue Instanz erstellen
                instance = PdvmCentralDatenbank(
                    table_name=table_name.lower(),
                    guid=guid
                )
                
                self.db_instances[instance_key] = instance
                instances_created += 1
                
                logger.info(f"  ✅ Instanz erstellt: {instance_key}")
                logger.debug(f"     source_path: {source_path} | Feld: {source_gruppe}.{feld_schluessel}")
                
            except Exception as e:
                logger.error(f"  ❌ Fehler bei Instanz-Erstellung: {field_key}")
                logger.error(f"     {e}")
                continue
        
        logger.info(f"  ✅ {instances_created} neue Instanzen erstellt")
        logger.info(f"  📊 Gesamt: {len(self.db_instances)} Instanzen verfügbar")
    
    def _get_instance_for_control(self, control_meta: Dict[str, Any]) -> Optional[PdvmCentralDatenbank]:
        """
        Holt die passende DB-Instanz für ein Control
        
        Args:
            control_meta: Control-Metadaten (field_key, source_path, etc.)
        
        Returns:
            PdvmCentralDatenbank Instanz oder None
        """
        field_key = control_meta['field_key']
        source_path = control_meta['source_path']
        field_config = control_meta['field_config']
        
        # Tabelle aus Field-Key
        parts = field_key.split('_')
        if len(parts) < 3:
            logger.warning(f"⚠️ Ungültiger field_key: {field_key}")
            return None
        
        table_name = parts[0]
        gruppe = parts[1].upper()
        
        if source_path == 'root':
            # ROOT-Instanz
            instance_key = f"{self.root_table.upper()}_{self.selected_guid}"
            return self.db_instances.get(instance_key)
        
        # Andere Instanz → GUID aus source_path holen
        if not source_path.startswith('root_'):
            logger.warning(f"⚠️ Ungültiger source_path: {source_path}")
            return None
        
        source_gruppe = source_path[5:]
        
        # FELDSCHLÜSSEL: {GRUPPE}-{TABELLE} (aus field_key berechnet)
        feld_schluessel = f"{gruppe}-{table_name}".upper()
        
        try:
            # GUID aus ROOT holen
            root_instance_key = f"{self.root_table.upper()}_{self.selected_guid}"
            root_instance = self.db_instances.get(root_instance_key)
            
            if not root_instance:
                logger.error(f"❌ ROOT-Instanz nicht gefunden: {root_instance_key}")
                return None
            
            stichtag = gcs.st_inst.PdvmDateTime
            result = root_instance.get_value(source_gruppe, feld_schluessel, stichtag)
            
            if isinstance(result, tuple):
                guid, _ = result
            else:
                guid = result
            
            if not guid:
                logger.error(f"❌ Keine GUID gefunden: {source_gruppe}.{feld_schluessel}")
                return None
            
            # Instanz holen
            instance_key = f"{table_name.upper()}_{guid}"
            return self.db_instances.get(instance_key)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Holen der Instanz: {e}")
            return None
    
    # ========================================================================
    # ALTE METHODE (wird nicht mehr verwendet)
    # ========================================================================
    
    # _get_or_create_instance() ENTFERNT - ersetzt durch _prepare_instances()
    
    # ========================================================================
    # UI HELPER METHODEN
    # ========================================================================
    
    def _load_header(self):
        """Lädt Header-Text aus Framedaten"""
        try:
            self.header_text, _ = self.framedaten_db.get_value('ROOT', 'HEADER_TEXT')
            
            # Fallback falls nicht gefunden
            if not self.header_text:
                logger.warning("  ⚠️ HEADER_TEXT nicht gefunden, versuche Fallback...")
                self.header_text, _ = self.framedaten_db.get_value('ROOT', 'header_text')
            
            # Default falls immer noch nichts
            if not self.header_text:
                self.header_text = "Edit-Bereich"
                logger.warning("  ⚠️ Kein Header gefunden, verwende Default")
            
            logger.info(f"  📋 Header: {self.header_text}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Headers: {e}")
            self.header_text = "Edit-Bereich"
    
    def get_widget(self) -> QWidget:
        """
        Gibt Widget mit Input-Controls zurück
        
        PHASE 3: Input-Controls rendern
        
        Returns:
            QWidget mit vollständigem Edit-Bereich
        """
        logger.info("🎨 Erstelle Input-Controls Widget...")
        
        try:
            # Haupt-Container
            container = QWidget()
            main_layout = QVBoxLayout(container)
            main_layout.setContentsMargins(20, 10, 20, 5)  # Oben: 10, Unten: 5 statt 20
            main_layout.setSpacing(10)  # 10 statt 15
            
            # === KOPFZEILE: NEUES ABDATUM + AUSGEWÄHLTER DATENSATZ ===
            # Alles in einer horizontalen Zeile für mehr Platz
            header_container = QWidget()
            header_layout = QHBoxLayout(header_container)
            header_layout.setContentsMargins(5, 5, 5, 5)  # Kompaktere Margins
            header_layout.setSpacing(20)
            
            # LINKS: Neues Abdatum
            abdatum_label = QLabel("🕒 Neues Abdatum:")
            abdatum_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    color: #2c3e50;
                    font-size: 12px;
                }
            """)
            header_layout.addWidget(abdatum_label)
            
            # === NEUES ABDATUM (ZENTRAL AUS GCS - WIE STICHTAG!) ===
            logger.info("  📅 === NEUES ABDATUM INITIALISIERUNG ===")
            
            # ZENTRALE INSTANZ: Direkt aus GCS verwenden (systemweit gültig!)
            # Die Instanz wurde bereits in GCS.__init__() initialisiert und geladen
            # Keine lokale Instanz mehr - nur noch Referenz!
            logger.info(f"    ✅ Verwende zentrale GCS-Instanz: gcs.neues_abdatum_inst")
            logger.info(f"       📅 Aktueller Wert: {gcs.neues_abdatum_inst.FormTimeStamp}")
            logger.info(f"       🔢 Raw PdvmDateTime: {gcs.neues_abdatum_inst.PdvmDateTime}")
            
            # DateTimePicker mit ZENTRALER INSTANZ erstellen
            self.abdatum_picker = PdvmDateTimePicker(
                parent=header_container,
                pdvm_datetime=gcs.neues_abdatum_inst,  # ← ZENTRALE INSTANZ!
                display="all",
                display_time_short=False,
                default_date=gcs.neues_abdatum_inst.PdvmDateTime
            )
            logger.info(f"    ✅ DateTimePicker mit zentraler GCS-Instanz initialisiert")
            logger.info("  ✅ Neues Abdatum Initialisierung abgeschlossen")
            header_layout.addWidget(self.abdatum_picker)
            
            # RECHTS: Ausgewählter Datensatz (GUID)
            guid_inner_container = QWidget()
            guid_inner_layout = QVBoxLayout(guid_inner_container)
            guid_inner_layout.setContentsMargins(0, 0, 0, 0)
            guid_inner_layout.setSpacing(2)
            
            guid_label_header = QLabel("📋 Ausgewählter Datensatz:")
            guid_label_header.setStyleSheet("""
                QLabel {
                    font-size: 11px;
                    font-weight: bold;
                    color: #34495e;
                }
            """)
            guid_inner_layout.addWidget(guid_label_header)
            
            guid_label_value = QLabel(self.selected_guid)
            guid_label_value.setStyleSheet("""
                QLabel {
                    font-size: 10px;
                    color: #7f8c8d;
                    font-family: 'Courier New', monospace;
                    padding: 5px;
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 3px;
                }
            """)
            guid_label_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            guid_inner_layout.addWidget(guid_label_value)
            
            header_layout.addWidget(guid_inner_container)
            header_layout.addStretch()
            
            main_layout.addWidget(header_container)
            
            # Trennlinie nach Header
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            separator.setStyleSheet("background-color: #bdc3c7;")
            main_layout.addWidget(separator)
            
            # === SCROLL-AREA FÜR INPUT-CONTROLS ===
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QScrollArea.NoFrame)
            
            # Content-Widget
            content = QWidget()
            content_layout = QVBoxLayout(content)
            content_layout.setContentsMargins(5, 5, 5, 5)
            content_layout.setSpacing(10)
            
            # === INPUT-CONTROLS RENDERN ===
            # PHASE 3: Controls in sortierter Reihenfolge rendern
            if not self.controls_meta:
                # Keine Controls
                no_data_label = QLabel("⚠️ Keine Input-Controls in Metadaten gefunden.")
                no_data_label.setStyleSheet("color: #888; font-style: italic; padding: 20px;")
                content_layout.addWidget(no_data_label)
                logger.warning("  ⚠️ Keine Controls zum Rendern vorhanden")
            else:
                logger.info(f"🎨 PHASE 3: Rendern von {len(self.controls_meta)} Controls...")
                rendered_count = 0
                
                # Controls BEREITS SORTIERT (nach Order)!
                for control_meta in self.controls_meta:
                    field_key = control_meta['field_key']
                    field_config = control_meta['field_config']
                    
                    # Passende Instanz holen (kann None sein!)
                    db_instance = self._get_instance_for_control(control_meta)
                    
                    if not db_instance:
                        logger.warning(f"  ⚠️ Keine Instanz für {field_key} → Control wird SCHREIBGESCHÜTZT angezeigt")
                        # WICHTIG: Trotzdem Control erstellen, aber ohne Instanz!
                        # → PdvmInputControl wird schreibgeschützt sein
                    
                    # Input-Control erstellen (IMMER, auch ohne Instanz!)
                    try:
                        control = PdvmInputControl(
                            field_key=field_key,
                            field_config=field_config,
                            db_instance=db_instance  # Kann None sein!
                        )
                        content_layout.addWidget(control)
                        
                        # WICHTIG: Control in Liste speichern!
                        self.controls.append(control)
                        
                        rendered_count += 1
                        
                        if db_instance:
                            logger.debug(f"  ✅ Control gerendert: {field_key} (Order: {control_meta['order']})")
                        else:
                            logger.debug(f"  🔒 Control gerendert (schreibgeschützt): {field_key} (Order: {control_meta['order']})")
                    except Exception as e:
                        logger.error(f"  ❌ Fehler beim Rendern von {field_key}: {e}")
                
                logger.info(f"  ✅ {rendered_count} Input-Controls gerendert (sortiert nach Order)")
            
            content_layout.addStretch()
            
            # Content in ScrollArea
            scroll.setWidget(content)
            main_layout.addWidget(scroll)
            
            # === TRENNLINIE VOR BUTTONS ===
            separator_bottom = QFrame()
            separator_bottom.setFrameShape(QFrame.HLine)
            separator_bottom.setFrameShadow(QFrame.Sunken)
            separator_bottom.setStyleSheet("background-color: #bdc3c7;")
            main_layout.addWidget(separator_bottom)
            
            # === BUTTON-LEISTE ===
            button_container = QWidget()
            button_layout = QHBoxLayout(button_container)
            button_layout.setContentsMargins(10, 5, 10, 5)  # Oben/Unten: 5 statt 10
            button_layout.setSpacing(10)
            
            # SPEICHERN Button
            speichern_btn = QPushButton("💾 Speichern")
            speichern_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    font-weight: bold;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #229954;
                }
                QPushButton:pressed {
                    background-color: #1e8449;
                }
            """)
            # DEBUG: Signal-Verbindung
            logger.info("  🔗 Verbinde Speichern-Button Signal...")
            try:
                speichern_btn.clicked.connect(self._on_speichern_clicked)
                logger.info("  ✅ Speichern-Button Signal verbunden")
            except Exception as e:
                logger.error(f"  ❌ Fehler beim Verbinden des Speichern-Buttons: {e}")
            button_layout.addWidget(speichern_btn)
            
            # ABBRECHEN Button
            abbrechen_btn = QPushButton("❌ Abbrechen")
            abbrechen_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    font-weight: bold;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
                QPushButton:pressed {
                    background-color: #a93226;
                }
            """)
            abbrechen_btn.clicked.connect(self._on_abbrechen_clicked)
            button_layout.addWidget(abbrechen_btn)
            
            button_layout.addStretch()
            
            # EINSTELLUNGEN Button (nur bei Admin-Mode)
            if gcs.mode == 'admin':
                einstellungen_btn = QPushButton("⚙️ Einstellungen")
                einstellungen_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #34495e;
                        color: white;
                        font-weight: bold;
                        padding: 10px 20px;
                        border: none;
                        border-radius: 5px;
                        min-width: 120px;
                    }
                    QPushButton:hover {
                        background-color: #2c3e50;
                    }
                    QPushButton:pressed {
                        background-color: #1c2833;
                    }
                """)
                einstellungen_btn.clicked.connect(self._on_einstellungen_clicked)
                button_layout.addWidget(einstellungen_btn)
                logger.info("  ⚙️ Einstellungen-Button hinzugefügt (Admin-Mode)")
            
            main_layout.addWidget(button_container)
            
            logger.info("✅ Input-Controls Widget erstellt (Phase 2: Controls mit Wert + Abdatum)")
            return container
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des Widgets: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Fallback: Error-Widget
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel(f"❌ Fehler beim Laden des Edit-Bereichs:\n{str(e)}")
            error_label.setStyleSheet("color: red; padding: 20px;")
            error_layout.addWidget(error_label)
            return error_widget
    
    def save_neues_abdatum(self):
        """
        Speichert das "Neues Abdatum" in GCS Systemsteuerung
        
        Sollte aufgerufen werden:
        - Beim Schließen des Dialogs
        - Vor dem Speichern von Änderungen
        """
        if not hasattr(self, 'abdatum_picker'):
            return
        
        try:
            # Abdatum aus DateTimePicker holen
            self.abdatum_picker.save()  # Speichert von initial → pdvm_datetime
            abdatum_value = self.neues_abdatum_dt.PdvmDateTime
            
            # In GCS Systemsteuerung speichern - USER-SPEZIFISCH!
            user_guid = gcs.user_guid
            gcs._db.set_value(user_guid, 'neues_abdatum', abdatum_value)
            gcs._db.save_all_values()
            
            logger.info(f"✅ Neues Abdatum gespeichert: {self.neues_abdatum_dt.FormTimeStamp} ({user_guid}.neues_abdatum)")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern des Abdatums: {e}")
    
    def get_neues_abdatum(self) -> float:
        """
        Gibt das aktuelle "Neues Abdatum" als Float zurück
        
        ZENTRALE INSTANZ: Holt Wert direkt aus GCS (systemweit gültig!)
        
        Returns:
            Pdvm_DateTime als Float (z.B. 20250605.123456)
        """
        if not hasattr(self, 'abdatum_picker'):
            # Fallback: Direkt aus GCS
            logger.warning("  ⚠️ Picker nicht initialisiert - Wert direkt aus GCS")
            return gcs.neues_abdatum
        
        try:
            # Wert aus ZENTRALER GCS-Instanz holen
            abdatum_value = gcs.neues_abdatum_inst.PdvmDateTime
            
            logger.debug(f"    🔍 get_neues_abdatum(): {abdatum_value} ({gcs.neues_abdatum_inst.FormTimeStamp})")
            
            return abdatum_value
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen des Abdatums: {e}")
            import traceback
            logger.error(traceback.format_exc())
            from pdvm_datetime import PdvmDateTimeUtils
            return PdvmDateTimeUtils.PdvmDateTimeNow
    
    # ========================================================================
    # BUTTON HANDLER
    # ========================================================================
    
    def _on_speichern_clicked(self):
        """
        Handler für SPEICHERN Button
        
        LINEARE SPEICHERUNG:
        1. Durchlaufe dirty Controls
        2. Jedes Control speichert sich selbst
        3. Batch-Commit auf alle Instanzen
        4. Bestätigungsfenster
        5. Refresh
        """
        # ULTRA SICHTBARES DEBUG-LOG
        print("\n" + "="*80)
        print("🚨 🚨 🚨 SPEICHERN-BUTTON WURDE GEKLICKT! 🚨 🚨 🚨")
        print("="*80 + "\n")
        
        logger.info("💾 === SPEICHERN GESTARTET ===")
        logger.info(f"  📋 self.controls vorhanden: {hasattr(self, 'controls')}")
        if hasattr(self, 'controls'):
            logger.info(f"  📋 Anzahl Controls: {len(self.controls)}")
        
        try:
            # [1] Neues Abdatum holen UND in GCS speichern (IMMER - auch ohne Änderungen!)
            # WIE BEIM STICHTAG: picker.save() → gcs.update_neues_abdatum()
            logger.info("  📅 === SCHRITT 1: NEUES ABDATUM VERARBEITEN ===")
            
            # 1a: Picker → GCS-Instanz übertragen
            if hasattr(self, 'abdatum_picker'):
                logger.info(f"    🔹 VOR save():")
                logger.info(f"       - GCS PdvmDateTime = {gcs.neues_abdatum_inst.PdvmDateTime}")
                logger.info(f"       - GCS FormTimeStamp = {gcs.neues_abdatum_inst.FormTimeStamp}")
                logger.info(f"       - Picker.initial   = {self.abdatum_picker.initial.PdvmDateTime}")
                
                # KRITISCH: save() überträgt von Picker.initial → gcs.neues_abdatum_inst
                self.abdatum_picker.save()
                
                logger.info(f"    🔹 NACH save():")
                logger.info(f"       - GCS PdvmDateTime = {gcs.neues_abdatum_inst.PdvmDateTime}")
                logger.info(f"       - GCS FormTimeStamp = {gcs.neues_abdatum_inst.FormTimeStamp}")
                logger.info(f"       - Picker.initial   = {self.abdatum_picker.initial.PdvmDateTime}")
            else:
                logger.warning("    ⚠️ abdatum_picker nicht vorhanden!")
            
            # 1b: Wert aus GCS-Instanz holen
            neues_abdatum = self.get_neues_abdatum()
            logger.info(f"  🕒 Neues Abdatum für Speicherung: {neues_abdatum}")
            logger.info(f"     Formatiert: {gcs.neues_abdatum_inst.FormTimeStamp}")
            
            # 1c: In GCS persistent speichern (WIE update_stichtag()!)
            try:
                logger.info(f"  💾 Speichere in GCS via update_neues_abdatum()...")
                gcs.update_neues_abdatum()
                logger.info(f"  ✅ Neues Abdatum in GCS persistent gespeichert!")
            except Exception as e:
                logger.error(f"  ❌ Fehler beim Speichern in GCS: {e}")
            
            # [2] Dirty Controls sammeln (OHNE Abdatum-Picker!)
            # Der abdatum_picker wird separat behandelt und zählt NICHT als Datenänderung
            dirty_controls = [c for c in self.controls if c.is_dirty and c != self.abdatum_picker]
            
            logger.info(f"  📝 {len(dirty_controls)} geänderte Datenfelder gefunden (Abdatum nicht mitgezählt)")
            
            if not dirty_controls:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(
                    None,
                    "Keine Datenänderungen",
                    "Es wurden keine Datenänderungen vorgenommen.\n\n"
                    f"✅ Das Neue Abdatum wurde jedoch gesetzt:\n{gcs.neues_abdatum_inst.FormTimeStamp}"
                )
                logger.info("  ℹ️ Keine Datenänderungen, aber Abdatum wurde persistent gespeichert")
                return
            
            # [3] Jedes Control speichert sich selbst
            changes = []
            for control in dirty_controls:
                success = control.save_to_db(neues_abdatum)
                if success:
                    changes.append({
                        'label': control.field_config.get('label', control.feld),
                        'field': control.field_key,
                        'old': control.original_value,
                        'new': control.current_value
                    })
            
            # [4] BATCH: Alle Instanzen committen
            logger.info(f"  💾 === SCHRITT 4: BATCH-COMMIT ===")
            logger.info(f"    📦 Committe {len(self.db_instances)} Instanzen...")
            for instance_key, instance in self.db_instances.items():
                instance.save_all_values()
                logger.debug(f"    ✅ {instance_key}")
            
            # [5] Bestätigungsfenster
            logger.info(f"  📋 === SCHRITT 5: BESTÄTIGUNG ===")
            self._show_save_confirmation(changes, neues_abdatum)
            
            # [6] Refresh (AUTONOM - ohne Dialog-Refresh!)
            logger.info(f"  🔄 === SCHRITT 6: REFRESH ===")
            self.refresh_controls()  # ← Nur Controls refreshen, NICHT Dialog!
            
            logger.info("✅ === SPEICHERN ABGESCHLOSSEN ===")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                None,
                "Fehler beim Speichern",
                f"Beim Speichern ist ein Fehler aufgetreten:\n\n{str(e)}"
            )
    
    def _on_abbrechen_clicked(self):
        """
        Handler für ABBRECHEN Button
        
        LINEARES ABBRECHEN:
        1. Bestätigung einholen
        2. Jedes dirty Control setzt sich selbst zurück
        3. Fertig (kein Refresh nötig, Controls aktualisieren sich selbst)
        """
        logger.info("❌ === ABBRECHEN GESTARTET ===")
        
        try:
            # [1] Dirty Controls zählen
            dirty_controls = [c for c in self.controls if c.is_dirty]
            
            if not dirty_controls:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(
                    None,
                    "Keine Änderungen",
                    "Es wurden keine Änderungen vorgenommen."
                )
                return
            
            # [2] Bestätigung einholen
            from PyQt5.QtWidgets import QMessageBox
            result = QMessageBox.question(
                None,
                "Änderungen verwerfen?",
                f"Möchten Sie {len(dirty_controls)} geänderte Feld(er) zurücksetzen?\n\n"
                "Alle Änderungen gehen verloren!",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if result != QMessageBox.Yes:
                logger.info("  ℹ️ Abbrechen vom Benutzer abgelehnt")
                return
            
            # [3] Jedes Control setzt sich selbst zurück
            logger.info(f"  ↶ Setze {len(dirty_controls)} Controls zurück...")
            for control in dirty_controls:
                control.reset_to_original()
            
            logger.info("✅ === ABBRECHEN ABGESCHLOSSEN ===")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Abbrechen: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def refresh_controls(self):
        """
        REFRESH-Kommando: Alle Controls neu laden (nach save_all_values)
        
        LINEAR DURCHLAUF:
        1. Neues Abdatum aus GCS neu laden
        2. Neues Abdatum Picker aktualisieren
        3. Alle Controls durchlaufen → refresh()
        
        Wird aufgerufen nach:
        - save_all_values() (nach Speichern)
        - Stichtag-Änderung
        """
        logger.info("🔄 === REFRESH CONTROLS ===")
        
        try:
            # [1] Neues Abdatum aus GCS aktualisieren (ZENTRALE INSTANZ!)
            # Die Instanz ist bereits in GCS - kein Load nötig, Referenz ist live!
            logger.info("  📅 SCHRITT 1: Neues Abdatum aus GCS (zentrale Instanz)")
            logger.info(f"    ✅ Aktueller Wert: {gcs.neues_abdatum_inst.FormTimeStamp}")
            
            # [2] Picker aktualisieren (refresh)
            if hasattr(self, 'abdatum_picker'):
                logger.info("  🔄 SCHRITT 2: Picker aktualisieren...")
                # Picker hat Referenz auf GCS-Instanz - nur Display refreshen
                self.abdatum_picker.update_display()
                logger.info(f"    ✅ Picker aktualisiert")
            
            # [3] Alle Controls durchlaufen (LINEAR!)
            logger.info(f"  🔄 SCHRITT 3: {len(self.controls)} Controls aktualisieren...")
            for control in self.controls:
                control.refresh()  # Jedes Control lädt Wert neu aus Instanz
            
            logger.info("✅ === REFRESH ABGESCHLOSSEN ===")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Refresh: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _on_einstellungen_clicked(self):
        """
        Handler für EINSTELLUNGEN Button (nur Admin-Mode)
        
        TODO: Implementierung in separatem Schritt
        - Dialog für Feld-Einstellungen
        - Sichtbarkeit, Reihenfolge, Validierung
        - Metadaten bearbeiten
        """
        logger.info("⚙️ EINSTELLUNGEN Button geklickt (Admin-Mode)")
        logger.info("  ⚠️ Funktionalität wird in separatem Schritt implementiert")
        
        # Platzhalter: Zeige Info-Message
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(
            None,
            "Einstellungen (Admin)",
            "Diese Funktionalität wird im nächsten Schritt implementiert.\n\n"
            "Geplant:\n"
            "- Feld-Reihenfolge ändern\n"
            "- Sichtbarkeit konfigurieren\n"
            "- Validierungs-Regeln festlegen\n"
            "- Metadaten bearbeiten"
        )
    
    def _show_save_confirmation(self, changes, neues_abdatum):
        """
        Zeigt Bestätigungsfenster nach erfolgreichem Speichern
        
        Args:
            changes: Liste von Änderungen
            neues_abdatum: Verwendetes Abdatum
        """
        from PyQt5.QtWidgets import QMessageBox
        
        # Abdatum formatieren
        dt = Pdvm_DateTime(gcs.field_value('country'))
        dt.PdvmDateTime = float(neues_abdatum)
        abdatum_formatted = dt.FormTimeStamp
        
        # Nachricht zusammenbauen
        message = f"✅ {len(changes)} Feld(er) erfolgreich gespeichert!\n\n"
        message += f"🕒 Abdatum: {abdatum_formatted}\n\n"
        message += "Geänderte Felder:\n"
        
        for change in changes[:10]:  # Max 10 anzeigen
            message += f"  • {change['label']}\n"
        
        if len(changes) > 10:
            message += f"  ... und {len(changes) - 10} weitere\n"
        
        QMessageBox.information(
            None,
            "Erfolgreich gespeichert",
            message
        )
    
    def _trigger_refresh(self):
        """
        Triggert Refresh des gesamten Dialogs
        
        Emittiert refresh_requested Signal, das vom Dialog empfangen wird
        """
        logger.info("  🔄 Emittiere refresh_requested Signal...")
        self.refresh_requested.emit()
        logger.info("  ✅ Signal emittiert")
