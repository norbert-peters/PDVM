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
from typing import Optional, Dict, Any
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
        self.db_instances: Dict[str, PdvmCentralDatenbank] = {}
        
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
            
            # In Instanzen-Manager speichern (Großbuchstaben als Key!)
            self.db_instances[self.root_table.upper()] = root_instance
            
            logger.info(f"  ✅ ROOT-Instanz erstellt: {self.root_table.upper()} ({table_name}.{self.selected_guid})")
            
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
    
    def _get_or_create_instance(self, table_name: str) -> Optional[PdvmCentralDatenbank]:
        """
        Holt oder erstellt Instanz für Tabelle (dynamisch)
        
        Args:
            table_name: Tabellenname (in GROSSBUCHSTABEN!)
        
        Returns:
            PdvmCentralDatenbank Instanz oder None
        """
        # Prüfe ob bereits vorhanden
        if table_name in self.db_instances:
            return self.db_instances[table_name]
        
        logger.info(f"  🔧 Erstelle neue Instanz für Tabelle: {table_name}")
        
        try:
            # Tabelle in Kleinbuchstaben für DB
            table_lower = table_name.lower()
            
            # GUID für neue Tabelle (vorerst None - wird später implementiert)
            # TODO: GUID aus Verknüpfungen/Relationen holen
            instance_guid = None
            
            # Instanz erstellen
            instance = PdvmCentralDatenbank(
                table_name=table_lower,
                guid=instance_guid
            )
            
            # Speichern
            self.db_instances[table_name] = instance
            
            logger.info(f"  ✅ Instanz erstellt: {table_name} ({table_lower}.{instance_guid})")
            
            return instance
            
        except Exception as e:
            logger.error(f"  ❌ Fehler beim Erstellen der Instanz für {table_name}: {e}")
            return None
    
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
            if not self.metadaten:
                # Keine Metadaten
                no_data_label = QLabel("⚠️ Keine Input-Controls in Metadaten gefunden.")
                no_data_label.setStyleSheet("color: #888; font-style: italic; padding: 20px;")
                content_layout.addWidget(no_data_label)
                logger.warning("  ⚠️ Keine Metadaten zum Rendern vorhanden")
            else:
                # Controls rendern (sortiert nach Key)
                rendered_count = 0
                sorted_keys = sorted(self.metadaten.keys())
                
                for field_key in sorted_keys:
                    field_config = self.metadaten[field_key]
                    
                    # Key parsen: TABELLE_GRUPPE_FELD
                    parts = field_key.split('_')
                    if len(parts) < 3:
                        logger.warning(f"  ⚠️ Ungültiger Field-Key: {field_key}")
                        continue
                    
                    table_name = parts[0].upper()  # GROSSBUCHSTABEN!
                    
                    # Instanz holen oder erstellen
                    db_instance = self._get_or_create_instance(table_name)
                    
                    if not db_instance:
                        logger.warning(f"  ⚠️ Keine Instanz für {field_key} (table={table_name})")
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
                        logger.debug(f"  ✅ Control gerendert: {field_key}")
                    except Exception as e:
                        logger.error(f"  ❌ Fehler beim Rendern von {field_key}: {e}")
                
                logger.info(f"  ✅ {rendered_count} Input-Controls gerendert")
            
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
