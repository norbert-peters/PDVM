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
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt

from global_gcs import gcs  # ← Globaler GCS-Import!
from pdvm_central_datenbank import PdvmCentralDatenbank
from pdvm_datetime import Pdvm_DateTime

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
        
        # Wert und Abdatum aus DB laden
        self.wert = None
        self.abdatum = None
        self._load_value()
        
        # UI erstellen
        self._create_ui()
    
    def _load_value(self):
        """Lädt Wert und Abdatum aus Datenbank"""
        if not self.db_instance:
            logger.warning(f"⚠️ Keine DB-Instanz für {self.field_key}")
            return
        
        try:
            # Stichtag von GCS holen
            stichtag = gcs.st_inst.PdvmDateTime
            
            # Wert laden (stichtagsgenau!)
            self.wert, self.abdatum = self.db_instance.get_value(
                self.gruppe,
                self.feld,
                stichtag
            )
            
            logger.debug(f"  📊 {self.field_key}: wert={str(self.wert)[:30]}, abdatum={self.abdatum}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden von {self.field_key}: {e}")
            self.wert = None
            self.abdatum = None
    
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
        
        # === WERT ===
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


class PdvmInputControlsModule:
    """
    Input-Controls Modul für GenerellerDialog
    
    EINFACHE API:
    - __init__(framedaten_db, selected_guid)
    - get_widget() → QWidget
    - GCS via globalen Import
    
    PHASE 1: Header + GUID anzeigen
    PHASE 2: Input-Controls aufbauen (später)
    """
    
    def __init__(self, framedaten_db, selected_guid: str):
        """
        Initialisiert Input-Controls Modul
        
        Args:
            framedaten_db: PdvmCentralDatenbank Instanz für Framedaten
            selected_guid: GUID des ausgewählten Datensatzes
        """
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
            
            # Tabelle aus Field-Key extrahieren
            parts = field_key.split('_')
            if len(parts) < 3:
                logger.warning(f"  ⚠️ Ungültiger field_key: {field_key}")
                continue
            
            table_name = parts[0]  # z.B. "FINANZWESEN"
            gruppe = parts[1].upper()  # z.B. "FINANZWESEN"
            
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
            
            # GUID aus ROOT-Instanz holen
            # Feldschlüssel-Format: {GRUPPE}-{TABELLE} (uppercase!)
            feld_schluessel = f"{gruppe}-{table_name}".upper()
            
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
        feld_schluessel = f"{gruppe}-{table_name}".upper()
        
        try:
            # GUID aus ROOT holen
            root_instance_key = f"{self.root_table.upper()}_{self.selected_guid}"
            root_instance = self.db_instances.get(root_instance_key)
            
            if not root_instance:
                return None
            
            stichtag = gcs.st_inst.PdvmDateTime
            result = root_instance.get_value(source_gruppe, feld_schluessel, stichtag)
            
            if isinstance(result, tuple):
                guid, _ = result
            else:
                guid = result
            
            if not guid:
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
        
        PHASE 2: Input-Controls rendern
        
        Returns:
            QWidget mit vollständigem Edit-Bereich
        """
        logger.info("🎨 Erstelle Input-Controls Widget...")
        
        try:
            # Haupt-Container
            container = QWidget()
            main_layout = QVBoxLayout(container)
            main_layout.setContentsMargins(20, 20, 20, 20)
            main_layout.setSpacing(15)
            
            # === HEADER ===
            header_label = QLabel(self.header_text)
            header_label.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: #2c3e50;
                    padding: 10px;
                    background-color: #ecf0f1;
                    border-radius: 5px;
                }
            """)
            header_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(header_label)
            
            # === TRENNLINIE ===
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            separator.setStyleSheet("background-color: #bdc3c7;")
            main_layout.addWidget(separator)
            
            # === GUID ANZEIGE ===
            guid_container = QWidget()
            guid_layout = QVBoxLayout(guid_container)
            guid_layout.setContentsMargins(10, 10, 10, 10)
            guid_layout.setSpacing(5)
            
            guid_label_header = QLabel("📋 Ausgewählter Datensatz:")
            guid_label_header.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    color: #34495e;
                }
            """)
            guid_layout.addWidget(guid_label_header)
            
            guid_label_value = QLabel(self.selected_guid)
            guid_label_value.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #7f8c8d;
                    font-family: 'Courier New', monospace;
                    padding: 10px;
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 3px;
                }
            """)
            guid_label_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            guid_layout.addWidget(guid_label_value)
            
            main_layout.addWidget(guid_container)
            
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
                    
                    # Passende Instanz holen
                    db_instance = self._get_instance_for_control(control_meta)
                    
                    if not db_instance:
                        logger.warning(f"  ⚠️ Keine Instanz für {field_key}")
                        continue
                    
                    # Input-Control erstellen
                    try:
                        control = PdvmInputControl(
                            field_key=field_key,
                            field_config=field_config,
                            db_instance=db_instance
                        )
                        content_layout.addWidget(control)
                        rendered_count += 1
                        logger.debug(f"  ✅ Control gerendert: {field_key} (Order: {control_meta['order']})")
                    except Exception as e:
                        logger.error(f"  ❌ Fehler beim Rendern von {field_key}: {e}")
                
                logger.info(f"  ✅ {rendered_count} Input-Controls gerendert (sortiert nach Order)")
            
            content_layout.addStretch()
            
            # Content in ScrollArea
            scroll.setWidget(content)
            main_layout.addWidget(scroll)
            
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
