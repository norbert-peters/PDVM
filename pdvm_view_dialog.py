"""
PdvmViewDialog - Vereinfachte Dialog-basierte View-Architektur

Architektur:
- Dialog = autonome Anwendung + kompletter Datenmanager
- Display = nur UI-Verantwortung 
- Lineare Ausführung ohne komplexe Widget/Manager-Struktur
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                            QTableWidgetItem, QHeaderView, QPushButton, QLabel, 
                            QMenu, QAction, QMessageBox, QToolButton, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

# GLOBALE IMPORTS: Direkter Zugriff auf zentrale Systemsteuerung
import pdvm_central_systemsteuerung_global as gcs_global
from pdvm_central_systemsteuerung_global import gcs  # Direkter Alias
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
    Autonomer View-Dialog mit integriertem Datenmanagement
    
    Ablauf:
    1. Aufruf über call_daten (view_guid, user_guid, title)
    2. Dialog = Dateninstanz + alle Manager-Funktionen
    3. Display wird durch Dialog gesteuert
    """
    
    def __init__(self, call_daten, parent=None):
        """
        Initialisierung des autonomen View-Dialogs
        
        Args:
            call_daten: Enthält view_guid, user_guid, title
            parent: Parent-Widget
        """
        self.call_daten = call_daten
        self.parent = parent
        
        # 🔍 1. TITEL-VALIDATION: Prüfung auf erforderliche Daten
        self.view_guid = call_daten.get("view_guid")
        self.user_guid = call_daten.get("user_guid")
        self.title = call_daten.get("title")
        
        # Fehlerbehandlung für fehlende erforderliche Daten
        error_messages = []
        if not self.view_guid:
            error_messages.append("❌ Keine view_guid in call_daten gefunden")
        if not self.user_guid:
            error_messages.append("❌ Keine user_guid in call_daten gefunden")
        if not self.title:
            error_messages.append("❌ Kein Titel in call_daten gefunden")
            
        if error_messages:
            error_text = "\n".join(error_messages)
            logger.error(f"Validation Error: {error_text}")
            QMessageBox.critical(parent, "Fehlende Daten", 
                               f"Die Ausgabe kann nicht erfolgen:\n\n{error_text}")
            raise ValueError(error_text)
        
        # Zentrale Systemsteuerung - Direkter Zugriff (KEINE Fallbacks!)
        if not gcs_global.is_initialized():
            error_msg = "❌ Zentrale Systemsteuerung nicht initialisiert - Login fehlt!"
            logger.error(error_msg)
            QMessageBox.critical(parent, "System Error", error_msg)
            raise RuntimeError(error_msg)
        
        logger.info(f"🔹 PdvmViewDialog initialisiert - View: {self.view_guid}, User: {self.user_guid}")
        
        # Datenbank-Instanzen
        self.view_db = PdvmCentralDatenbank()  # Für View-Daten mit Performance-Optimierung
        
        # Daten-Container
        self.view_config = None
        self.controls_config = None
        self.all_data_records = []
        self.display_matrix = []
        
        # 🚀 PERFORMANCE-OPTIMIERUNG: Smart Data Caching
        self.cached_all_data = None      # Cache für alle gelesenen Datensätze
        self.cached_view_config = None   # Cache für View-Konfiguration
        self.cached_controls_config = None  # Cache für Controls-Konfiguration
        self.cache_timestamp = None      # Zeitstempel des Caches
        self.cache_view_guid = None      # View-GUID für Cache-Validierung
        
        # UI-Container
        self.display = None
        
        # Initialisierung starten
        self._initialize_dialog()
    
    @property
    def gcs(self):
        """Property für direkten Zugriff auf globale Systemsteuerung"""
        return gcs_global.get_central_systemsteuerung()
    
    def _create_base_data(self):
        """🔧 Basisdaten erstellen - robuste View-Konfiguration laden mit set_data Performance"""
        logger.info("🔧 Erstelle Basisdaten...")
        
        # View-Konfiguration laden mit optimierter PdvmCentralDatenbank
        try:
            view_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="viewdaten", 
                guid=self.view_guid,
                historisch=False  # View-Konfigurationen sind meist statisch
            )
            
            # 🚀 PERFORMANCE: VIEW_TABLE ermitteln mit get_static_value
            view_table = view_db.get_static_value(gruppe='ROOT', feld='VIEW_TABLE')
            if not view_table:
                # Fallback: Versuche andere mögliche Felder
                view_table = view_db.get_static_value(gruppe='ROOT', feld='view_table')
                if not view_table:
                    # Standard-Fallback für Tests
                    view_table = "persondaten"
                    logger.warning(f"⚠️ VIEW_TABLE nicht gefunden - verwende Fallback: {view_table}")
            
            # 🚀 PERFORMANCE: ViewDaten-Metadaten mit get_static_value laden
            view_metadaten = view_db.get_static_value(gruppe='METADATEN', feld=view_table.upper())
            if not view_metadaten or 'felder' not in view_metadaten:
                # Fallback: Standard-Felder für persondaten erstellen
                logger.warning("⚠️ ViewDaten-Felder nicht gefunden - erstelle Standard-Fallback")
                view_metadaten = {
                    'felder': [
                        {'feld': 'VORNAME', 'name': 'Vorname', 'type': 'string', 'gruppe': 'PERSDATEN'},
                        {'feld': 'NAME', 'name': 'Nachname', 'type': 'string', 'gruppe': 'PERSDATEN'},
                        {'feld': 'GEBURTSDATUM', 'name': 'Geburtsdatum', 'type': 'date', 'gruppe': 'PERSDATEN'},
                        {'feld': 'STATUS', 'name': 'Status', 'type': 'string', 'gruppe': 'PERSDATEN'}
                    ]
                }
                
            # View-Config zusammenstellen
            self.view_config = {
                'ROOT': {'view_table': view_table},
                'spalten': view_metadaten['felder']
            }
            
            logger.info(f"✅ View-Konfiguration geladen: Tabelle '{view_table}', {len(self.view_config['spalten'])} Spalten")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der View-Konfiguration: {e}")
            # Notfall-Fallback: Minimale Konfiguration
            self.view_config = {
                'ROOT': {'view_table': 'persondaten'},
                'spalten': [
                    {'feld': 'VORNAME', 'name': 'Vorname', 'type': 'string', 'gruppe': 'PERSDATEN'},
                    {'feld': 'NAME', 'name': 'Nachname', 'type': 'string', 'gruppe': 'PERSDATEN'}
                ]
            }
            logger.warning("⚠️ Verwende Notfall-Fallback Konfiguration")
    
    def _load_all_data_records(self):
        """
        🎯 PERFORMANCE-OPTIMIERTE DATENLADUNG mit set_data für Matrix-Views
        
        Lädt ALLE Rohdatensätze und verwendet set_data für Performance-optimierte
        Matrix-Operationen ohne redundante DB-Zugriffe
        """
        logger.info("🔹 Lade alle Rohdatensätze (Performance-optimiert)...")
        
        try:
            # View-Datenbank für die spezifische Tabelle
            table_name = self.view_config['ROOT']['view_table']
            view_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name=table_name,
                historisch=True  # Für Stichtag-basierte Auswertungen
            )
            
            # 🚀 PERFORMANCE: get_all_records für optimierte Datenladung
            self.raw_records = view_db.get_all_records()
            
            if self.raw_records:
                logger.info(f"✅ {len(self.raw_records)} Rohdatensätze geladen - optimiert für Matrix-Views")
                
                # 🚀 ZUSÄTZLICHE PERFORMANCE-OPTIMIERUNG: 
                # Erstelle PdvmCentralDatenbank-Instanzen mit set_data für jeden Datensatz
                self.optimized_instances = []
                for record in self.raw_records:
                    instance = PdvmCentralDatenbank.create_with_data(
                        guid=record["uid"],
                        daten=record["daten"],
                        db_name="PdvmManager.db",
                        table_name=table_name,
                        historisch=True
                    )
                    self.optimized_instances.append(instance)
                
                logger.info(f"🚀 Performance-Instanzen erstellt: {len(self.optimized_instances)} - KEINE DB-Zugriffe mehr bei get_value!")
            else:
                logger.warning("⚠️ Keine Datensätze gefunden")
                self.raw_records = []
                self.optimized_instances = []
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Datensätze: {e}")
            self.raw_records = []
            self.optimized_instances = []
    
    def _build_display_matrix(self):
        """
        🔧 PERFORMANCE-OPTIMIERTE MATRIX-ERSTELLUNG mit Memory-basierten get_value Operationen
        
        Verwendet die optimized_instances für alle get_value Aufrufe - 
        KEINE DB-Zugriffe mehr während Matrix-Erstellung!
        """
        logger.info("🔧 Erstelle Display-Matrix (Performance-optimiert)...")
        
        current_stichtag = gcs.stichtag
        logger.info(f"📅 Verwende Stichtag: {current_stichtag}")
        
        self.display_matrix = []
        
        if not self.optimized_instances:
            logger.warning("⚠️ Keine optimierten Instanzen verfügbar")
            return
        
        logger.info(f"📊 Verarbeite {len(self.optimized_instances)} Instanzen (Memory-basiert)...")
        
        # Für jede optimierte Instanz Matrix-Zeile erstellen
        for instance_idx, instance in enumerate(self.optimized_instances):
            row_data = {}
            
            try:
                # STEP 1: System-Spalten füllen
                row_data['uid_original'] = instance.guid
                row_data['uid_show'] = instance.guid[:8] + "..." if len(instance.guid) > 8 else instance.guid
                
                # STEP 2: Alle View-Felder mit get_value füllen (Memory-Operation!)
                if 'spalten' in self.view_config:
                    for feld_config in self.view_config['spalten']:
                        feldname = feld_config.get("feld", "")
                        feld_name = feldname.lower()
                        feld_type = feld_config.get("type", "string")
                        gruppe = feld_config.get("gruppe", "PERSDATEN")
                        
                        if feldname:
                            # 🚀 PERFORMANCE: get_value aus Memory-Daten (KEIN DB-Zugriff!)
                            original_wert = instance.get_value(gruppe, feldname, current_stichtag)
                            
                            # _original Felder
                            row_data[f'{feld_name}_original'] = original_wert
                            
                            # _show Felder mit Formatierung
                            if feld_type == 'date' and isinstance(original_wert, (int, float)) and original_wert > 0:
                                try:
                                    from pdvm_datetime import Pdvm_DateTime
                                    dt_formatter = Pdvm_DateTime("DEU")
                                    dt_formatter.PdvmDateTime = original_wert
                                    formatted_value = dt_formatter.Date_formatted
                                    row_data[f'{feld_name}_show'] = formatted_value
                                except Exception as e:
                                    row_data[f'{feld_name}_show'] = str(original_wert)
                            else:
                                row_data[f'{feld_name}_show'] = original_wert
                
                # STEP 3: Dummy-Spalte
                row_data['dummy'] = ''
                
                self.display_matrix.append(row_data)
                
                if instance_idx % 10 == 0:  # Alle 10 Datensätze loggen
                    logger.debug(f"📋 Zeile {instance_idx + 1}: {len(row_data)} Felder gefüllt (Memory)")
                
            except Exception as e:
                logger.warning(f"⚠️ Fehler bei Instanz {instance.guid}: {e}")
                continue
        
        logger.info(f"✅ Performance-Matrix erstellt: {len(self.display_matrix)} Zeilen × {len(row_data) if self.display_matrix else 0} Spalten (Memory-basiert)")
    
    def _initialize_dialog(self):
        """Performance-optimierte Initialisierung"""
        logger.info("🔹 Starte Performance-optimierte Dialog-Initialisierung...")
        
        # 1. Basisdaten erstellen
        self._create_base_data()
        
        # 2. Alle Datensätze laden (mit Performance-Instanzen)  
        self._load_all_data_records()
        
        # 3. Display-Matrix für aktuellen Stichtag erstellen
        self._build_display_matrix()
        
        # 4. UI-Display erstellen und zeigen
        self._create_and_show_display()
        
        logger.info("✅ Performance-optimierte Dialog-Initialisierung abgeschlossen")
    
    def _create_and_show_display(self):
        """UI-Display als Widget erstellen"""
        logger.info("🔹 Erstelle UI-Display...")
        
        self.display = PdvmViewDisplay(self)
        
        logger.info("✅ Display erstellt")
    
    def get_display_widget(self):
        """Widget für Integration in Arbeitsbereich zurückgeben"""
        if not self.display:
            self._create_and_show_display()
        return self.display
    
    def reload(self):
        """🔄 PERFORMANCE-RELOAD: Matrix neu aufbauen mit bereits geladenen Instanzen"""
        logger.info("🔄 Performance-Reload wegen Stichtag-Änderung...")
        
        try:
            # Nur Matrix neu erstellen - Instanzen bleiben im Memory!
            self._build_display_matrix()
            
            # UI-Display aktualisieren
            if self.display:
                self.display.refresh_table()
                logger.info("✅ Performance-Reload erfolgreich abgeschlossen")
            else:
                logger.warning("⚠️ Kein Display für Reload verfügbar")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Performance-Reload: {e}")


class PdvmViewDisplay(QWidget):
    """
    UI-Display für PdvmViewDialog als Arbeitsbereich-Widget
    Nur Verantwortung für Oberfläche, alle Daten kommen vom Dialog
    """
    
    def __init__(self, view_dialog):
        super().__init__(view_dialog.parent)
        self.view_dialog = view_dialog
        
        # Header-Label für dynamische Updates
        self.header_label = None
        
        self._setup_ui()
        self._refresh_table()
        self.update_header_text()
    
    def _setup_ui(self):
        """UI-Setup als Arbeitsbereich-Widget"""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)  # Keine Margins für Arbeitsbereich
        
        # Header-Bereich
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # Dynamischer Header-Text aus call_daten
        self.header_label = QLabel()
        header_font = QFont("Segoe UI", 12, QFont.Bold)
        self.header_label.setFont(header_font)
        self.header_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 8px;
                background-color: #ecf0f1;
                border-radius: 4px;
                border: 1px solid #bdc3c7;
            }
        """)
        header_layout.addWidget(self.header_label)
        
        header_layout.addStretch()
        
        # Settings-Button
        self.settings_button = QToolButton()
        self.settings_button.setText("⚙️")
        self.settings_button.setToolTip("Einstellungen")
        self.settings_button.setPopupMode(QToolButton.InstantPopup)
        
        self._create_settings_menu()
        header_layout.addWidget(self.settings_button)
        
        layout.addLayout(header_layout)
        
        # Tabelle
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)
        
        # Status-Zeile
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
    
    def _create_settings_menu(self):
        """Settings-Menü erstellen"""
        settings_menu = QMenu(self)
        
        # Expert-Mode Toggle
        expert_action = QAction("🔧 Expert-Mode", self)
        expert_action.setCheckable(True)
        expert_action.setChecked(gcs.expert_mode)
        settings_menu.addAction(expert_action)
        
        self.settings_button.setMenu(settings_menu)
    
    def update_header_text(self):
        """Header-Text aktualisieren"""
        header_text = self.view_dialog.title
        
        # Im Expert-Mode Stichtag hinzufügen
        if gcs.expert_mode:
            stichtag = gcs.stichtag
            header_text += f" (Stichtag: {stichtag})"
        
        self.header_label.setText(header_text)
    
    def refresh_table(self):
        """Tabelle neu aufbauen"""
        self._refresh_table()
        self.update_header_text()
    
    def _refresh_table(self):
        """Tabelle mit Daten füllen"""
        try:
            # Einfache Tabellendarstellung für Performance-Test
            matrix = self.view_dialog.display_matrix
            
            if not matrix:
                self.table.setRowCount(0)
                self.table.setColumnCount(0)
                self.status_label.setText("Keine Daten verfügbar")
                return
            
            # Spalten aus erstem Datensatz ermitteln
            columns = list(matrix[0].keys()) if matrix else []
            visible_columns = [col for col in columns if col.endswith('_show') or col == 'uid_show']
            
            # Tabelle konfigurieren
            self.table.setRowCount(len(matrix))
            self.table.setColumnCount(len(visible_columns))
            self.table.setHorizontalHeaderLabels(visible_columns)
            
            # Daten einfügen
            for row_idx, row_data in enumerate(matrix):
                for col_idx, col_name in enumerate(visible_columns):
                    value = row_data.get(col_name, '')
                    item = QTableWidgetItem(str(value))
                    self.table.setItem(row_idx, col_idx, item)
            
            # Status aktualisieren
            self.status_label.setText(f"{len(matrix)} Datensätze, {len(visible_columns)} Spalten")
            
            logger.info(f"✅ Tabelle aktualisiert: {len(matrix)} Zeilen × {len(visible_columns)} Spalten")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der Tabelle: {e}")
            self.status_label.setText(f"Fehler: {e}")
