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
    Autonomer View-Dialog mit integriertem Datenmanagement
    
    Ablauf:
    1. Aufruf über call_daten (view_guid, title, first_call) - user_guid kommt aus GCS
    2. Dialog = Dateninstanz + alle Manager-Funktionen
    3. Display wird durch Dialog gesteuert
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
        
        # user_guid aus GCS holen
        self.user_guid = get_gcs().user_guid
        
        logger.info(f"🔹 PdvmViewDialog initialisiert - View: {self.view_guid}, User: {self.user_guid}, First Call: {self.first_call}")
        
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
        return get_gcs()
    
    def _create_base_data(self):
        """🔧 Basisdaten erstellen - robuste View-Konfiguration laden mit neuer ViewDaten-Struktur"""
        logger.info("🔧 Erstelle Basisdaten...")
        
        # View-Konfiguration laden mit optimierter PdvmCentralDatenbank
        try:
            view_db = PdvmCentralDatenbank(
                table_name="viewdaten", 
                guid=self.view_guid
            )
            
            # 🚀 NEUE STRUKTUR: Vollständige ViewDaten laden
            root_data = view_db.get_static_value(gruppe='ROOT', feld='VIEW_TABLE')
            if not root_data:
                error_msg = f"❌ ROOT.VIEW_TABLE nicht gefunden für view_guid: {self.view_guid}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 🚀 NEUE STRUKTUR: METADATEN mit controls und standard_control laden
            metadaten = view_db.get_static_value(gruppe='METADATEN', feld=root_data.upper())
            if not metadaten or 'controls' not in metadaten:
                error_msg = f"❌ METADATEN.{root_data.upper()}.controls nicht gefunden für view_guid: {self.view_guid}"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            # View-Config für neue Struktur zusammenstellen
            self.view_config = {
                'ROOT': {'view_table': root_data},
                'controls': metadaten['controls'],
                'standard_control': metadaten.get('standard_control', {})
            }
            
            logger.info(f"✅ View-Konfiguration geladen: Tabelle '{root_data}', {len(self.view_config['controls'])} Base-Controls")
            
            # 🔧 CONTROLS-VERARBEITUNG: Schritt 1-7 implementieren mit neuer Struktur
            self._process_controls_config()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der View-Konfiguration: {e}")
            # KEIN FALLBACK MEHR - Fehler weiterleiten!
            raise RuntimeError(f"View-Konfiguration konnte nicht geladen werden für view_guid '{self.view_guid}': {e}")
    
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
                table_name=table_name  # Kein db_name Parameter!
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
                        table_name=table_name  # Kein db_name oder historisch Parameter!
                    )
                    self.optimized_instances.append(instance)
                
                logger.info(f"🚀 Performance-Instanzen erstellt: {len(self.optimized_instances)} - KEINE DB-Zugriffe mehr bei get_value!")
            else:
                logger.warning("⚠️ Verwende Notfall-Fallback Konfiguration")
        
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Rohdatensätze: {e}")
            self.raw_records = []
            self.optimized_instances = []
            raise RuntimeError(f"Datenladung fehlgeschlagen: {e}")
    
    def _process_controls_config(self):
        """
        🔧 CONTROLS-VERARBEITUNG: Implementierung der Schritte 1-7
        
        1. Prüfung des Aufbaus der Controls über die viewdaten
        2. Controls werden in der GCS unter Gruppe=view_guid und Feld=controls abgelegt
        3. Synchronisation mit bestehenden GCS Controls
        4. Controls aus GCS übernehmen (3.1)
        5. Controls in GCS zurückspeichern (3.2) 
        6. Controls über GCS bereitstellen
        7. ViewDialog fit machen
        """
        logger.info("🔧 Starte Controls-Verarbeitung...")
        
        # SCHRITT 1: Controls-Struktur aus viewdaten prüfen und generieren
        generated_controls = self._generate_controls_from_viewdata()
        logger.info(f"✅ Schritt 1: {len(generated_controls)} Controls aus viewdaten generiert")
        
        # SCHRITT 2: Bestehende Controls aus GCS laden
        gcs = get_gcs()
        try:
            existing_controls = gcs._db.get_static_value(gruppe=self.view_guid, feld='controls')
            logger.info(f"✅ Schritt 2: {len(existing_controls)} bestehende Controls aus GCS geladen")
            
            # SCHRITT 3 & 4: Controls-Synchronisation (3.1)
            synchronized_controls = self._synchronize_controls(generated_controls, existing_controls)
            logger.info(f"✅ Schritt 3+4: Controls synchronisiert - {len(synchronized_controls)} Controls")
            
        except KeyError:
            logger.info("✅ Schritt 2: View-GUID noch nicht in GCS vorhanden - überspringe Synchronisation")
            # Keine Synchronisation notwendig, verwende direkt generierte Controls
            synchronized_controls = generated_controls
            logger.info(f"✅ Schritt 3+4: Übersprungen - verwende {len(synchronized_controls)} generierte Controls")
        
        # SCHRITT 5: Controls in GCS zurückspeichern (3.2)
        gcs._db.set_value(gruppe=self.view_guid, feld='controls', wert=synchronized_controls)
        
        # 🔥 KRITISCH: Daten persistent speichern!
        gcs._db.save_all_values()
        logger.info("✅ Schritt 5: Controls in GCS gespeichert und persistent gemacht")
        
        # SCHRITT 6: Controls über GCS bereitstellen
        self.controls_config = synchronized_controls
        logger.info("✅ Schritt 6: Controls über GCS bereitgestellt")
        
        logger.info("✅ Controls-Verarbeitung abgeschlossen")
    
    def _generate_controls_from_viewdata(self):
        """🔧 Vollständige Controls-Generierung mit neuer ViewDaten-Struktur
        
        Schritt 1: Original Controls aus ViewDaten.controls
        Schritt 2: Show Controls (Kopien der Original Controls)
        Schritt 3: Dummy Control aus ViewDaten.standard_control.dummy
        """
        logger.info("🔧 Generiere Controls aus ViewDaten (neue Struktur)...")
        
        if not self.view_config:
            logger.error("❌ Keine view_config verfügbar für Controls-Generierung")
            return
        
        # 🚀 SCHRITT 1: Original Controls aus ViewDaten-Struktur erstellen
        original_controls = self._create_original_controls_from_viewdata()
        logger.info(f"✅ Schritt 1: {len(original_controls)} Original Controls erstellt")
        
        # 🚀 SCHRITT 2: Show Controls - Kopien mit show=True
        show_controls = self._create_show_controls_from_original_viewdata(original_controls)
        logger.info(f"✅ Schritt 2: {len(show_controls)} Show Controls erstellt")
        
        # 🚀 SCHRITT 3: Dummy Control aus standard_control
        dummy_control = self._create_dummy_control_from_viewdata()
        logger.info(f"✅ Schritt 3: Dummy Control erstellt")
        
        # Alle Controls zusammenführen
        all_controls = {**original_controls, **show_controls, **dummy_control}
        
        # 🚀 SCHRITT 4: Controls mit persistenten Parametern versehen
        self._add_control_parameters_from_gcs(all_controls)
        logger.info(f"✅ Schritt 4: Control-Parameter aus GCS geladen")
        
        # Controls in GCS speichern
        self.save_all_values()
        
        logger.info(f"✅ Controls-Generierung abgeschlossen: {len(all_controls)} Controls total")
        return all_controls
    
    def _create_original_controls_from_viewdata(self):
        """🔧 SCHRITT 1: Original Controls aus ViewDaten.controls erstellen"""
        controls = {}
        
        # Controls aus ViewDaten.controls verarbeiten
        viewdata_controls = self.view_config.get('controls', {})
        
        for control_key, control_config in viewdata_controls.items():
            # Original Control mit _original Suffix
            original_key = f"{control_key}_original"
            
            # Direkte Übernahme aller Eigenschaften aus ViewDaten
            controls[original_key] = {
                'feld': control_key,
                'gruppe': control_config.get('gruppe', 'SYSTEM'),
                'name': control_config.get('name', control_key.title()),
                'type': control_config.get('type', 'string'),
                'default': control_config.get('default', ''),
                'dropdown': control_config.get('dropdown'),
                'control_type': control_config.get('control_type', 'base'),
                'expert_mode': control_config.get('expert_mode', True),
                'show': False,  # Original Controls sind immer show=False
                'display_order': control_config.get('display_order', 0),
                'expert_order': control_config.get('expert_order', 0),
                'searchable': control_config.get('searchable', True),
                'sortable': control_config.get('sortable', True),
                'sortDirection': control_config.get('sortDirection', 'asc'),
                'sortByOriginal': control_config.get('sortByOriginal', False),
                'filterType': control_config.get('filterType', 'contains')
            }
            
            # 🚀 DATUM-EXPANSION: Bei type=date automatisch weitere Controls
            if control_config.get('type') == 'date':
                base_config = controls[original_key].copy()
                
                # Alter Original
                controls[f"{control_key}_alter_original"] = {
                    **base_config,
                    'feld': f"{control_key}_alter",
                    'name': f"{base_config['name']} (Alter)",
                    'type': 'string',
                    'sortByOriginal': True
                }
                
                # Jahr Original
                controls[f"{control_key}_jahr_original"] = {
                    **base_config,
                    'feld': f"{control_key}_jahr",
                    'name': f"{base_config['name']} (Jahr)",
                    'type': 'string',
                    'sortByOriginal': True
                }
                
                # Monat Original
                controls[f"{control_key}_monat_original"] = {
                    **base_config,
                    'feld': f"{control_key}_monat",
                    'name': f"{base_config['name']} (Monat)",
                    'type': 'string',
                    'sortByOriginal': True
                }
                
                # Tag Original
                controls[f"{control_key}_tag_original"] = {
                    **base_config,
                    'feld': f"{control_key}_tag",
                    'name': f"{base_config['name']} (Tag)",
                    'type': 'string',
                    'sortByOriginal': True
                }
        
        logger.info(f"✅ Original Controls erstellt: {len(controls)} Controls")
        return controls
    
    def _create_show_controls_from_original_viewdata(self, original_controls):
        """🔧 SCHRITT 2: Show Controls aus Original Controls erzeugen"""
        show_controls = {}
        
        for original_key, original_control in original_controls.items():
            if original_key.endswith('_original'):
                # Show Key erstellen
                show_key = original_key.replace('_original', '_show')
                
                # Kopie mit show=True
                show_controls[show_key] = original_control.copy()
                show_controls[show_key]['show'] = True
        
        logger.info(f"✅ Show Controls erstellt: {len(show_controls)} Controls")
        return show_controls
    
    def _create_dummy_control_from_viewdata(self):
        """🔧 SCHRITT 3: Dummy Control aus ViewDaten.standard_control.dummy"""
        dummy_control = {}
        
        # Dummy aus ViewDaten.standard_control laden
        standard_control = self.view_config.get('standard_control', {})
        dummy_config = standard_control.get('dummy', {})
        
        if dummy_config:
            dummy_control['dummy'] = {
                'feld': 'dummy',
                'gruppe': dummy_config.get('gruppe', 'SYSTEM'),
                'name': dummy_config.get('name', 'Dummy'),
                'type': dummy_config.get('type', 'string'),
                'default': dummy_config.get('default', 'keine Daten'),
                'dropdown': dummy_config.get('dropdown'),
                'control_type': dummy_config.get('control_type', 'base'),
                'expert_mode': dummy_config.get('expert_mode', True),
                'show': False,
                'display_order': dummy_config.get('display_order', 0),
                'expert_order': dummy_config.get('expert_order', 0),
                'searchable': dummy_config.get('searchable', True),
                'sortable': dummy_config.get('sortable', True),
                'sortDirection': dummy_config.get('sortDirection', 'asc'),
                'sortByOriginal': dummy_config.get('sortByOriginal', False),
                'filterType': dummy_config.get('filterType', 'contains')
            }
        else:
            # Fallback Dummy Control
            dummy_control['dummy'] = {
                'feld': 'dummy',
                'gruppe': 'SYSTEM',
                'name': 'Dummy',
                'type': 'string',
                'default': 'keine Daten',
                'dropdown': None,
                'control_type': 'base',
                'expert_mode': True,
                'show': False,
                'display_order': 0,
                'expert_order': 0,
                'searchable': True,
                'sortable': True,
                'sortDirection': 'asc',
                'sortByOriginal': False,
                'filterType': 'contains'
            }
        
        logger.info(f"✅ Dummy Control erstellt")
        return dummy_control
    
    def _add_control_parameters_from_gcs(self, all_controls):
        """🔧 SCHRITT 4: Control-Parameter aus GCS laden und überschreiben"""
        # GCS-Parameter laden wenn vorhanden
        try:
            saved_controls = self.get_value(gruppe='view_guid', feld='controls')
            if saved_controls:
                for control_key, control_config in all_controls.items():
                    if control_key in saved_controls:
                        # Nur bestimmte Parameter aus GCS übernehmen
                        gcs_control = saved_controls[control_key]
                        control_config['expert_mode'] = gcs_control.get('expert_mode', control_config['expert_mode'])
                        control_config['show'] = gcs_control.get('show', control_config['show'])
                        control_config['display_order'] = gcs_control.get('display_order', control_config['display_order'])
                        control_config['expert_order'] = gcs_control.get('expert_order', control_config['expert_order'])
                        
                logger.info(f"✅ Control-Parameter aus GCS geladen und überschrieben")
        except Exception as e:
            logger.warning(f"⚠️ Keine gespeicherten Control-Parameter gefunden: {e}")
        
        # Alle Controls in der Instanz speichern
        self.set_value(gruppe='view_guid', feld='controls', wert=all_controls)
    # Alte Methoden entfernt - werden durch neue ViewDaten-Struktur ersetzt
    
    # NEUE ARCHITEKTUR: ViewDaten-basierte Control-Generierung
    
    def _create_original_controls_from_viewdata(self):
        """🔧 SCHRITT 1: Original Controls aus ViewDaten.controls erstellen"""
        controls = {}
        
        # Controls aus ViewDaten.controls verarbeiten
        viewdata_controls = self.view_config.get('controls', {})
        
        for control_key, control_config in viewdata_controls.items():
            # Original Control mit _original Suffix
            original_key = f"{control_key}_original"
            
            # Direkte Übernahme aller Eigenschaften aus ViewDaten
            controls[original_key] = {
                'feld': control_key,
                'gruppe': control_config.get('gruppe', 'SYSTEM'),
                'name': control_config.get('name', control_key.title()),
                'type': control_config.get('type', 'string'),
                'default': control_config.get('default', ''),
                'dropdown': control_config.get('dropdown'),
                'control_type': control_config.get('control_type', 'base'),
                'expert_mode': control_config.get('expert_mode', True),
                'show': False,  # Original Controls sind immer show=False
                'display_order': control_config.get('display_order', 0),
                'expert_order': control_config.get('expert_order', 0),
                'searchable': control_config.get('searchable', True),
                'sortable': control_config.get('sortable', True),
                'sortDirection': control_config.get('sortDirection', 'asc'),
                'sortByOriginal': control_config.get('sortByOriginal', False),
                'filterType': control_config.get('filterType', 'contains')
            }
            
            # 🚀 DATUM-EXPANSION: Bei type=date automatisch weitere Controls
            if control_config.get('type') == 'date':
                base_config = controls[original_key].copy()
                
                # Alter Original
                controls[f"{control_key}_alter_original"] = {
                    **base_config,
                    'feld': f"{control_key}_alter",
                    'name': f"{base_config['name']} (Alter)",
                    'type': 'string',
                    'sortByOriginal': True
                }
                
                # Jahr Original
                controls[f"{control_key}_jahr_original"] = {
                    **base_config,
                    'feld': f"{control_key}_jahr",
                    'name': f"{base_config['name']} (Jahr)",
                    'type': 'string',
                    'sortByOriginal': True
                }
                
                # Monat Original
                controls[f"{control_key}_monat_original"] = {
                    **base_config,
                    'feld': f"{control_key}_monat",
                    'name': f"{base_config['name']} (Monat)",
                    'type': 'string',
                    'sortByOriginal': True
                }
                
                # Tag Original
                controls[f"{control_key}_tag_original"] = {
                    **base_config,
                    'feld': f"{control_key}_tag",
                    'name': f"{base_config['name']} (Tag)",
                    'type': 'string',
                    'sortByOriginal': True
                }
        
        logger.info(f"✅ Original Controls erstellt: {len(controls)} Controls")
        return controls
    
    def _create_show_controls_from_original_viewdata(self, original_controls):
        """🔧 SCHRITT 2: Show Controls aus Original Controls erzeugen"""
        show_controls = {}
        
        for original_key, original_control in original_controls.items():
            if original_key.endswith('_original'):
                # Show Key erstellen
                show_key = original_key.replace('_original', '_show')
                
                # Kopie mit show=True
                show_controls[show_key] = original_control.copy()
                show_controls[show_key]['show'] = True
        
        logger.info(f"✅ Show Controls erstellt: {len(show_controls)} Controls")
        return show_controls
    
    def _create_dummy_control_from_viewdata(self):
        """🔧 SCHRITT 3: Dummy Control aus ViewDaten.standard_control.dummy"""
        dummy_control = {}
        
        # Dummy aus ViewDaten.standard_control laden
        standard_control = self.view_config.get('standard_control', {})
        dummy_config = standard_control.get('dummy', {})
        
        if dummy_config:
            dummy_control['dummy'] = {
                'feld': 'dummy',
                'gruppe': dummy_config.get('gruppe', 'SYSTEM'),
                'name': dummy_config.get('name', 'Dummy'),
                'type': dummy_config.get('type', 'string'),
                'default': dummy_config.get('default', 'keine Daten'),
                'dropdown': dummy_config.get('dropdown'),
                'control_type': dummy_config.get('control_type', 'base'),
                'expert_mode': dummy_config.get('expert_mode', True),
                'show': False,
                'display_order': dummy_config.get('display_order', 0),
                'expert_order': dummy_config.get('expert_order', 0),
                'searchable': dummy_config.get('searchable', True),
                'sortable': dummy_config.get('sortable', True),
                'sortDirection': dummy_config.get('sortDirection', 'asc'),
                'sortByOriginal': dummy_config.get('sortByOriginal', False),
                'filterType': dummy_config.get('filterType', 'contains')
            }
        else:
            # Fallback Dummy Control
            dummy_control['dummy'] = {
                'feld': 'dummy',
                'gruppe': 'SYSTEM',
                'name': 'Dummy',
                'type': 'string',
                'default': 'keine Daten',
                'dropdown': None,
                'control_type': 'base',
                'expert_mode': True,
                'show': False,
                'display_order': 0,
                'expert_order': 0,
                'searchable': True,
                'sortable': True,
                'sortDirection': 'asc',
                'sortByOriginal': False,
                'filterType': 'contains'
            }
        
        logger.info(f"✅ Dummy Control erstellt")
        return dummy_control
    
    def _add_control_parameters_from_gcs(self, all_controls):
        """🔧 SCHRITT 4: Control-Parameter aus GCS laden und überschreiben"""
        # GCS-Parameter laden wenn vorhanden
        try:
            saved_controls = self.get_value(gruppe='view_guid', feld='controls')
            if saved_controls:
                for control_key, control_config in all_controls.items():
                    if control_key in saved_controls:
                        # Nur bestimmte Parameter aus GCS übernehmen
                        gcs_control = saved_controls[control_key]
                        control_config['expert_mode'] = gcs_control.get('expert_mode', control_config['expert_mode'])
                        control_config['show'] = gcs_control.get('show', control_config['show'])
                        control_config['display_order'] = gcs_control.get('display_order', control_config['display_order'])
                        control_config['expert_order'] = gcs_control.get('expert_order', control_config['expert_order'])
                        
                logger.info(f"✅ Control-Parameter aus GCS geladen und überschrieben")
        except Exception as e:
            logger.warning(f"⚠️ Keine gespeicherten Control-Parameter gefunden: {e}")
        
        # Alle Controls in der Instanz speichern
        self.set_value(gruppe='view_guid', feld='controls', wert=all_controls)
    
    def _synchronize_controls(self, generated_controls, existing_controls):
        """
        SCHRITT 3+4: Controls-Synchronisation (3.1)
        
        Übernimmt Daten aus existing_controls in generated_controls.
        Arbeitet mit der 3-stufigen Control-Struktur (_original, _show, dummy).
        """
        synchronized = {}
        
        for control_key, generated_control in generated_controls.items():
            # Kopie des generierten Controls erstellen
            sync_control = generated_control.copy()
            
            # Wenn existing_control vorhanden, Werte übernehmen
            if control_key in existing_controls:
                existing_control = existing_controls[control_key]
                
                # Nur bestimmte Eigenschaften übernehmen (nicht die Basis-Struktur)
                sync_properties = ['visible', 'width', 'sortable', 'filterable']
                for prop in sync_properties:
                    if prop in existing_control:
                        sync_control[prop] = existing_control[prop]
                        
                logger.debug(f"🔄 Control '{control_key}' aus GCS synchronisiert")
            else:
                logger.debug(f"🆕 Control '{control_key}' neu generiert")
                
            synchronized[control_key] = sync_control
        
        # Prüfung: Stelle sicher, dass alle 3 Control-Typen vorhanden sind
        control_types = {'original': 0, 'show': 0, 'dummy': 0}
        for control in synchronized.values():
            control_type = control.get('control_type', 'unknown')
            if control_type in control_types:
                control_types[control_type] += 1
        
        logger.info(f"🔍 Control-Verteilung: {control_types['original']} Original, {control_types['show']} Show, {control_types['dummy']} Dummy")
        
        return synchronized
    
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
                table_name=table_name  # Kein db_name Parameter!
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
                        table_name=table_name  # Kein db_name oder historisch Parameter!
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
        
        gcs = get_gcs()
        logger.info(f"📅 Verwende Stichtag direkt aus st_inst: {gcs.st_inst.PdvmDateTime}")
        
        self.display_matrix = []
        
        if not self.optimized_instances:
            logger.warning("⚠️ Keine optimierten Instanzen verfügbar")
            return
        
        logger.info(f"📊 Verarbeite {len(self.optimized_instances)} Instanzen (Memory-basiert)...")
        logger.info(f"🔍 DEBUG: View-Konfiguration Spalten: {len(self.view_config.get('spalten', []))}")
        
        # Für jede optimierte Instanz Matrix-Zeile erstellen
        for instance_idx, instance in enumerate(self.optimized_instances):
            row_data = {}
            
            try:
                # STEP 1: System-Spalten füllen
                row_data['uid_original'] = instance.guid
                row_data['uid_show'] = instance.guid[:8] + "..." if len(instance.guid) > 8 else instance.guid
                
                logger.debug(f"🔍 DEBUG: Zeile {instance_idx} - GUID: {instance.guid}")
                
                # STEP 2: Alle View-Felder mit get_value füllen (Memory-Operation!)
                if 'spalten' in self.view_config:
                    for feld_config in self.view_config['spalten']:
                        feldname = feld_config.get("feld", "")
                        feld_name = feldname.lower()
                        feld_type = feld_config.get("type", "string")
                        gruppe = feld_config.get("gruppe", "PERSDATEN")
                        
                        if feldname:
                            # 🚀 PERFORMANCE: get_value aus Memory-Daten (KEIN DB-Zugriff!)
                            # Stichtag direkt aus GCS st_inst verwenden - immer aktuell!
                            original_wert = instance.get_value(gruppe, feldname, gcs.st_inst.PdvmDateTime)
                            
                            logger.debug(f"🔍 DEBUG: Feld {feldname} -> {original_wert}")
                            
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
                
                if instance_idx == 0:  # Erste Zeile detailliert loggen
                    logger.info(f"🔍 DEBUG: Erste Zeile Daten: {row_data}")
                
                if instance_idx % 10 == 0:  # Alle 10 Datensätze loggen
                    logger.debug(f"📋 Zeile {instance_idx + 1}: {len(row_data)} Felder gefüllt (Memory)")
                
            except Exception as e:
                logger.warning(f"⚠️ Fehler bei Instanz {instance.guid}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                continue
        
        logger.info(f"✅ Performance-Matrix erstellt: {len(self.display_matrix)} Zeilen × {len(row_data) if self.display_matrix else 0} Spalten (Memory-basiert)")
        logger.info(f"🔍 DEBUG: Matrix Inhalt: {self.display_matrix[:2] if self.display_matrix else 'LEER'}")
    
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
        gcs = get_gcs()
        expert_action.setChecked(gcs.expert_mode)
        settings_menu.addAction(expert_action)
        
        settings_menu.addSeparator()
        
        # 🔧 CONTROLS-OPTIONEN
        # Spalten-Konfiguration
        columns_action = QAction("📋 Spalten konfigurieren", self)
        columns_action.triggered.connect(self._configure_columns)
        settings_menu.addAction(columns_action)
        
        # Controls zurücksetzen
        reset_controls_action = QAction("🔄 Controls zurücksetzen", self)
        reset_controls_action.triggered.connect(self._reset_controls)
        settings_menu.addAction(reset_controls_action)
        
        self.settings_button.setMenu(settings_menu)
    
    def _configure_columns(self):
        """Spalten-Konfiguration öffnen"""
        try:
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, QSpinBox, QLabel, QPushButton
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Spalten konfigurieren")
            dialog.setModal(True)
            dialog.resize(400, 300)
            
            layout = QVBoxLayout(dialog)
            
            # Controls anzeigen
            controls_widgets = {}
            
            if hasattr(self.view_dialog, 'controls_config') and self.view_dialog.controls_config:
                for control_key, control in self.view_dialog.controls_config.items():
                    control_layout = QHBoxLayout()
                    
                    # Sichtbarkeit
                    visible_cb = QCheckBox(control.get('name', control_key))
                    visible_cb.setChecked(control.get('visible', True))
                    control_layout.addWidget(visible_cb)
                    
                    # Breite
                    control_layout.addWidget(QLabel("Breite:"))
                    width_spin = QSpinBox()
                    width_spin.setRange(50, 500)
                    width_spin.setValue(control.get('width', 100))
                    control_layout.addWidget(width_spin)
                    
                    layout.addLayout(control_layout)
                    
                    controls_widgets[control_key] = {
                        'visible': visible_cb,
                        'width': width_spin
                    }
            
            # Buttons
            button_layout = QHBoxLayout()
            
            ok_button = QPushButton("OK")
            ok_button.clicked.connect(lambda: self._save_column_config(controls_widgets, dialog))
            button_layout.addWidget(ok_button)
            
            cancel_button = QPushButton("Abbrechen")
            cancel_button.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_button)
            
            layout.addLayout(button_layout)
            
            dialog.exec_()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Öffnen der Spalten-Konfiguration: {e}")
    
    def _save_column_config(self, controls_widgets, dialog):
        """Spalten-Konfiguration speichern"""
        try:
            # Controls aktualisieren
            for control_key, widgets in controls_widgets.items():
                if control_key in self.view_dialog.controls_config:
                    self.view_dialog.controls_config[control_key]['visible'] = widgets['visible'].isChecked()
                    self.view_dialog.controls_config[control_key]['width'] = widgets['width'].value()
            
            # In GCS speichern
            gcs = get_gcs()
            gcs._db.set_value(
                gruppe=self.view_dialog.view_guid, 
                feld='controls', 
                wert=self.view_dialog.controls_config
            )
            
            # 🔥 KRITISCH: Daten persistent speichern!
            gcs._db.save_all_values()
            
            # Tabelle neu aufbauen
            self.refresh_table()
            
            dialog.accept()
            logger.info("✅ Spalten-Konfiguration gespeichert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Spalten-Konfiguration: {e}")
    
    def _reset_controls(self):
        """Controls auf Standard zurücksetzen"""
        try:
            from PyQt5.QtWidgets import QMessageBox
            
            reply = QMessageBox.question(
                self, 
                "Controls zurücksetzen", 
                "Sollen alle Spalten-Einstellungen auf Standard zurückgesetzt werden?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Controls aus GCS löschen
                gcs = get_gcs()
                gcs._db.set_value(
                    gruppe=self.view_dialog.view_guid, 
                    feld='controls', 
                    wert={}
                )
                
                # 🔥 KRITISCH: Daten persistent speichern!
                gcs._db.save_all_values()
                
                # View Dialog neu initialisieren
                self.view_dialog._process_controls_config()
                
                # Tabelle neu aufbauen
                self.refresh_table()
                
                logger.info("✅ Controls zurückgesetzt")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Zurücksetzen der Controls: {e}")
    
    def update_header_text(self):
        """Header-Text aktualisieren"""
        header_text = self.view_dialog.title
        
        # Im Expert-Mode Stichtag hinzufügen
        gcs = get_gcs()
        if gcs.expert_mode:
            stichtag = gcs.st_inst.PdvmDateTime
            header_text += f" (Stichtag: {stichtag})"
        
        self.header_label.setText(header_text)
    
    def refresh_table(self):
        """Tabelle neu aufbauen"""
        self._refresh_table()
        self.update_header_text()
    
    def _refresh_table(self):
        """Tabelle mit Daten füllen - Controls-basierte Spaltenauswahl"""
        try:
            # Einfache Tabellendarstellung für Performance-Test
            matrix = self.view_dialog.display_matrix
            
            logger.info(f"🔍 DEBUG: Matrix hat {len(matrix) if matrix else 0} Zeilen")
            if matrix:
                logger.info(f"🔍 DEBUG: Erste Zeile Schlüssel: {list(matrix[0].keys())}")
            
            if not matrix:
                self.table.setRowCount(0)
                self.table.setColumnCount(0)
                self.status_label.setText("Keine Daten verfügbar")
                logger.warning("⚠️ Keine Matrix-Daten für Tabelle verfügbar")
                return
            
            # 🔧 CONTROLS-BASIERTE SPALTENAUSWAHL
            visible_columns = self._get_visible_columns_from_controls(matrix)
            
            logger.info(f"🔍 DEBUG: Sichtbare Spalten aus Controls: {visible_columns}")
            
            # Tabelle konfigurieren
            self.table.setRowCount(len(matrix))
            self.table.setColumnCount(len(visible_columns))
            
            # 🔧 CONTROLS-BASIERTE HEADER-LABELS
            header_labels = self._get_header_labels_from_controls(visible_columns)
            self.table.setHorizontalHeaderLabels(header_labels)
            
            # Daten einfügen
            for row_idx, row_data in enumerate(matrix):
                for col_idx, col_name in enumerate(visible_columns):
                    value = row_data.get(col_name, '')
                    item = QTableWidgetItem(str(value))
                    self.table.setItem(row_idx, col_idx, item)
            
            # 🔧 CONTROLS-BASIERTE SPALTENBREITEN
            self._apply_column_widths_from_controls(visible_columns)
            
            # Status aktualisieren
            self.status_label.setText(f"{len(matrix)} Datensätze, {len(visible_columns)} Spalten")
            
            logger.info(f"✅ Tabelle aktualisiert: {len(matrix)} Zeilen × {len(visible_columns)} Spalten (Controls-basiert)")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der Tabelle: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.status_label.setText(f"Fehler: {e}")
    
    def _get_visible_columns_from_controls(self, matrix):
        """Sichtbare Spalten basierend auf Controls-Konfiguration ermitteln"""
        if not matrix:
            return []
            
        all_columns = list(matrix[0].keys())
        visible_columns = []
        
        # Wenn Controls verfügbar sind, diese verwenden
        if hasattr(self.view_dialog, 'controls_config') and self.view_dialog.controls_config:
            # Expert-Mode prüfen
            gcs = get_gcs()
            current_expert_mode = gcs.expert_mode
            
            for control_key, control in self.view_dialog.controls_config.items():
                # Prüfe ob Control angezeigt werden soll
                should_show = False
                
                if current_expert_mode:
                    # Expert-Mode: Alle Controls mit visible=True anzeigen
                    should_show = control.get('visible', False)
                else:
                    # Normal-Mode: Nur Controls mit show=True anzeigen
                    should_show = control.get('show', False)
                
                if should_show and control_key in all_columns:
                    visible_columns.append(control_key)
            
            # Sortierung nach display_order oder expert_order
            if visible_columns:
                order_field = 'expert_order' if current_expert_mode else 'display_order'
                visible_columns.sort(key=lambda col: self.view_dialog.controls_config.get(col, {}).get(order_field, 999))
        else:
            # Fallback: Alle _show Spalten
            visible_columns = [col for col in all_columns if col.endswith('_show')]
            
        logger.debug(f"🔍 Controls-Filter: Expert={current_expert_mode if 'gcs' in locals() else 'N/A'}, Sichtbar={len(visible_columns)}")
        return visible_columns
    
    def _get_header_labels_from_controls(self, visible_columns):
        """Header-Labels basierend auf Controls-Konfiguration erstellen"""
        header_labels = []
        
        for col_name in visible_columns:
            if (hasattr(self.view_dialog, 'controls_config') and 
                self.view_dialog.controls_config and 
                col_name in self.view_dialog.controls_config):
                
                control = self.view_dialog.controls_config[col_name]
                header_labels.append(control.get('name', col_name))
            else:
                # Fallback: Spaltenname verwenden
                header_labels.append(col_name)
                    
        return header_labels
    
    def _apply_column_widths_from_controls(self, visible_columns):
        """Spaltenbreiten basierend auf Controls-Konfiguration anwenden"""
        for col_idx, col_name in enumerate(visible_columns):
            if (hasattr(self.view_dialog, 'controls_config') and 
                self.view_dialog.controls_config and 
                col_name in self.view_dialog.controls_config):
                
                control = self.view_dialog.controls_config[col_name]
                width = control.get('width', 100)
                self.table.setColumnWidth(col_idx, width)
            else:
                # Fallback: Automatische Spaltenbreite
                self.table.resizeColumnToContents(col_idx)
