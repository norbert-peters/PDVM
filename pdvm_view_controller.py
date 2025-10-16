# pdvm_view_controller.py
"""
🎮 PDVM View Controller - SAUBERE ARCHITEKTUR (Option B)

VERANTWORTLICHKEITEN:
- Koordiniert UI, Manager und Datenbank
- Verarbeitet Benutzer-Aktionen (Filter, Sortierung, Suche)
- Verbindet UI mit Daten-Layer
- Enthält Business-Logik

ARCHITEKTUR:
┌─────────────────────┐
│ PdvmViewController  │ ← Controller (Steuerung/Logik)
├─────────────────────┤
│ PdvmViewUI          │ ← Display (Darstellung)
├─────────────────────┤
│ PdvmViewManager     │ ← Daten/Matrix-Verwaltung
└─────────────────────┘

MIGRATION VON:
- PdvmViewDialog (alte Klasse mit gemischten Verantwortlichkeiten)
"""

import logging
from PyQt5.QtWidgets import QWidget, QMessageBox
from pdvm_central_datenbank import PdvmCentralDatenbank
from pdvm_central_systemsteuerung import get_gcs

# V3 Filter-System
from schnellsuche_manager import SchnellsucheManager
from einfach_filter_manager import EinfachFilterManager

logger = logging.getLogger(__name__)

class PdvmViewController:
    """
    Controller für View-Operationen
    
    VERANTWORTLICHKEITEN:
    - Initialisierung und Koordination
    - Daten laden und verarbeiten
    - Filter-/Sortier-/Such-Operationen koordinieren
    - Events von UI entgegennehmen und verarbeiten
    - Manager und UI synchronisieren
    """
    
    def __init__(self, call_daten, parent=None):
        """
        Initialisiert den View-Controller
        
        Args:
            call_daten: Dict mit view_guid, title, first_call, test_mode
            parent: Parent-Widget (MainAppComplete)
        """
        logger.info("🎮 === PdvmViewController INITIALISIERUNG ===")
        
        # Core-Attribute aus call_daten
        self.view_guid = call_daten.get("view_guid")
        self.frame_guid = call_daten.get("frame_guid")  # Für View-Neustart bei Reset!
        self.title = call_daten.get("title", "Unbekannte View")
        self.first_call = call_daten.get("first_call", False)
        self.reset = call_daten.get("reset", False)
        self.test_mode = call_daten.get("test_mode", False)
        self.parent = parent
        
        # Validation
        if not self.view_guid:
            error = "❌ Keine view_guid in call_daten!"
            logger.error(error)
            raise ValueError(error)
        
        logger.info(f"📋 View-GUID: {self.view_guid}")
        logger.info(f"📋 Titel: {self.title}")
        logger.info(f"📋 First Call: {self.first_call}")
        logger.info(f"📋 Test Mode: {self.test_mode}")
        
        # GCS Zugriff
        self.gcs = get_gcs()
        if not self.gcs:
            error = "❌ GCS nicht initialisiert!"
            logger.error(error)
            raise RuntimeError(error)
        
        # Komponenten (werden in initialize() erstellt)
        self.ui = None  # PdvmViewUI
        self.matrix_manager = None  # PdvmViewMatrixManager - MATRIX-PIPELINE
        
        # View-Konfiguration
        self.view_config = None
        self.controls_config = None
        self.table_name = None
        
        # Daten-Container
        self.raw_records = []
        self.optimized_instances = []
        self.all_controls = {}  # Vollständige Control-Konfigurationen
        
        # Filter/Sortierung (LEGACY - wird durch Matrix Manager ersetzt)
        self.linear_filter = None
        self.sorting_manager = None
        
        # Sortierungs-State für Filter-Pipeline (Legacy)
        self.current_sort_column = None
        self.current_sort_reverse = False
        
        # ✅ Sortierung ist AUTONOM in Matrix-Pipeline!
        # ✅ Sort-Config wird bei rebuild_pipeline() direkt aus GCS geholt
        # ✅ KEIN self.current_sort_config mehr nötig!
        
        logger.info("✅ Controller-Basis initialisiert")
    
    def initialize(self):
        """
        Hauptinitialisierung - LINEAR mit MATRIX-PIPELINE
        
        ABLAUF:
        0. Reset-Flag prüfen (falls gesetzt → Abgleich überspringen)
        1. View-Daten laden
        2. Controls generieren und speichern
        3. Projektionen initialisieren
        4. Daten laden (Instanzen)
        5. MATRIX MANAGER initialisieren
        6. MATRIX-PIPELINE: BasisMatrix erstellen
        7. MATRIX-PIPELINE: Filter/Sort durchlaufen
        8. UI erstellen
        9. Filter/Sortierung verbinden (Legacy-Kompatibilität)
        """
        logger.info("🚀 Starte lineare Controller-Initialisierung mit Matrix-Pipeline...")
        
        try:
            # 0. Reset-Flag prüfen und ggf. setzen
            if self.gcs and hasattr(self.gcs, 'db'):
                reset_flag, _ = self.gcs.db.get_value(self.view_guid, '_reset_controls_flag')
                if reset_flag:
                    logger.info("🚩 Reset-Flag erkannt - Controls werden NEU generiert (OHNE Abgleich)")
                    self.reset = True
                    
                    # Flag sofort löschen (wird nur einmal verwendet)
                    self.gcs.db.set_value(self.view_guid, '_reset_controls_flag', None)
                    self.gcs.db.save_all_values()
            
            # 1. View-Daten laden
            self._load_viewdata()
            
            # 2. Controls generieren
            self._generate_and_save_controls()
            
            # 3. Projektionen initialisieren
            self._initialize_projections()
            
            # 4. Daten laden (Instanzen)
            self._load_data()
            
            # 5. Matrix Manager initialisieren
            self._initialize_matrix_manager()
            
            # 6. BasisMatrix erstellen
            self._build_basis_matrix()
            
            # 7. Matrix-Pipeline durchlaufen
            # ✅ Pipeline holt Sort-Config AUTONOM aus GCS (wie Filter!)
            self._run_matrix_pipeline()
            
            # 8. UI erstellen
            self._create_ui()
            
            # 9. Filter/Sortierung verbinden (Legacy)
            self._initialize_filter_and_sort()
            
            # 10. Stichtag-Signal verbinden
            self._connect_stichtag_signal()
            
            logger.info("✅ Controller-Initialisierung abgeschlossen")
            return True
            
        except Exception as e:
            logger.error(f"❌ Controller-Initialisierung fehlgeschlagen: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _load_viewdata(self):
        """1. ViewDaten laden"""
        logger.info("📂 SCHRITT 1: ViewDaten laden...")
        
        try:
            view_db = PdvmCentralDatenbank(
                table_name="viewdaten",
                guid=self.view_guid
            )
            
            # ROOT-Daten
            root_data = view_db.get_static_value(gruppe='ROOT', feld='VIEW_TABLE')
            if not root_data:
                raise ValueError(f"ROOT.VIEW_TABLE nicht gefunden für {self.view_guid}")
            
            self.table_name = root_data
            
            # METADATEN
            metadaten = view_db.get_static_value(gruppe='METADATEN', feld=root_data.upper())
            if not metadaten:
                raise ValueError(f"METADATEN.{root_data.upper()} nicht gefunden")
            
            if 'controls' not in metadaten:
                raise ValueError("controls nicht in METADATEN gefunden")
            
            if 'standard_control' not in metadaten or 'dummy' not in metadaten['standard_control']:
                raise ValueError("standard_control.dummy nicht gefunden")
            
            # View-Config zusammenstellen
            self.view_config = {
                'ROOT': {'view_table': root_data},
                'controls': metadaten['controls'],
                'standard_control': metadaten['standard_control']
            }
            
            logger.info(f"✅ ViewDaten geladen: Tabelle '{root_data}', {len(self.view_config['controls'])} Controls")
            
        except Exception as e:
            logger.error(f"❌ ViewDaten-Ladung fehlgeschlagen: {e}")
            raise
    
    def _generate_and_save_controls(self):
        """2. Controls linear generieren"""
        logger.info("🔧 SCHRITT 2: Controls generieren...")
        
        all_controls = {}
        
        # SCHRITT 1: _original Controls aus ViewDaten
        for control_key, control_data in self.view_config['controls'].items():
            original_key = f"{control_key}_original"
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
                    all_controls[expanded_key]['type'] = f"date{suffix}"
                    all_controls[expanded_key]['show'] = False
        
        logger.info(f"  ✅ {len([k for k in all_controls if k.endswith('_original')])} Original Controls")
        
        # SCHRITT 2: _show Controls
        original_controls = {k: v for k, v in all_controls.items() if k.endswith('_original')}
        for original_key, original_control in original_controls.items():
            show_key = original_key.replace('_original', '_show')
            all_controls[show_key] = original_control.copy()
            all_controls[show_key]['control_type'] = 'show'
            all_controls[show_key]['show'] = True
            all_controls[show_key]['expert_mode'] = False
        
        logger.info(f"  ✅ {len([k for k in all_controls if k.endswith('_show')])} Show Controls")
        
        # SCHRITT 3: Dummy
        dummy_data = self.view_config['standard_control']['dummy']
        all_controls['dummy'] = dummy_data.copy()
        all_controls['dummy']['control_type'] = 'dummy'
        
        logger.info("  ✅ Dummy Control erstellt")
        
        # SCHRITT 4: Benutzer-Werte aus GCS laden (falls vorhanden)
        if not self.reset:
            try:
                existing_gcs_controls = self.gcs.db.get_static_value(
                    gruppe=self.view_guid,
                    feld='controls'
                )
                
                if existing_gcs_controls:
                    logger.info("  📋 Lade Benutzer-spezifische Werte aus GCS...")
                    
                    # Fehlende Controls hinzufügen
                    for control_key in all_controls:
                        if control_key not in existing_gcs_controls:
                            existing_gcs_controls[control_key] = all_controls[control_key].copy()
                    
                    # Benutzer-Werte übernehmen (Whitelist)
                    allowed_user_params = ['expert_mode', 'show', 'expert_order', 'display_order', 
                                          'sortable', 'sortDirection', 'sortByOriginal']
                    
                    for control_key, control_config in all_controls.items():
                        if control_key in existing_gcs_controls:
                            gcs_control = existing_gcs_controls[control_key]
                            for prop_key in allowed_user_params:
                                if prop_key in gcs_control:
                                    control_config[prop_key] = gcs_control[prop_key]
                    
                    logger.info("  ✅ Benutzer-Werte übernommen")
                else:
                    logger.info("  ✅ Keine bestehenden Controls (erste Ausführung)")
                    
            except Exception as e:
                logger.info(f"  ℹ️ Keine GCS Controls gefunden: {e}")
        else:
            logger.info("  🔄 Reset-Modus - Benutzer-Werte übersprungen")
        
        # SCHRITT 5: Controls in beide DBs speichern
        self.gcs.db.set_value(
            gruppe=self.view_guid,
            feld='controls',
            wert=all_controls
        )
        self.gcs.db.save_all_values()
        
        # In Systemsteuerung-DB speichern
        import json
        for control_key, control_config in all_controls.items():
            try:
                control_json = json.dumps(control_config, ensure_ascii=False)
                self.gcs._db.set_value(self.view_guid, control_key, control_json)
            except Exception as e:
                logger.warning(f"⚠️ Fehler bei {control_key}: {e}")
        
        logger.info(f"  ✅ {len(all_controls)} Controls in beide DBs gespeichert")
        
        # Speichere all_controls für Matrix Manager
        self.all_controls = all_controls
        self.controls_config = all_controls
        
        # SCHRITT 6: Projektions-Tabellen in GCS aufbauen (für Dialog-Zugriff)
        # Dialog braucht Zugriff auf Projektionen für Filter-Felder
        self.gcs._build_projection_tables(self.view_guid)
        logger.info("  ✅ Projektions-Tabellen in GCS berechnet (für Dialog-Zugriff)")
        
        # Lokale Referenz für schnellen Zugriff
        self.projection_tables = {
            'table_standard': self.gcs.get_projection_table(self.view_guid, 'table_standard'),
            'table_expert': self.gcs.get_projection_table(self.view_guid, 'table_expert'),
            'search_standard': self.gcs.get_projection_table(self.view_guid, 'search_standard'),
            'search_expert': self.gcs.get_projection_table(self.view_guid, 'search_expert'),
            'change_standard': self.gcs.get_projection_table(self.view_guid, 'change_standard'),
            'change_expert': self.gcs.get_projection_table(self.view_guid, 'change_expert'),
            'sort_standard': self.gcs.get_projection_table(self.view_guid, 'sort_standard'),
            'sort_expert': self.gcs.get_projection_table(self.view_guid, 'sort_expert')
        }
    
    def _initialize_projections(self):
        """3. Projektionen initialisieren"""
        logger.info("🔧 SCHRITT 3: Projektionen initialisieren...")
        
        try:
            basis_columns = []
            for control_key, control_config in self.controls_config.items():
                if control_config.get('control_type') in ['original', 'show']:
                    basis_col = {
                        'name': control_key,
                        'expertOrder': control_config.get('expert_order', 999),
                        'displayOrder': control_config.get('display_order', 999),
                        'show': control_config.get('show', False),
                        'spaltenueberschrift': control_config.get('name', control_key)
                    }
                    basis_columns.append(basis_col)
            
            logger.info(f"✅ {len(basis_columns)} Projektions-Spalten initialisiert (Live-Berechnung)")
            
        except Exception as e:
            logger.error(f"❌ Projektions-Initialisierung fehlgeschlagen: {e}")
            raise
    
    def _load_data(self):
        """4. Daten laden"""
        logger.info("📂 SCHRITT 4: Daten laden...")
        
        try:
            data_db = PdvmCentralDatenbank(table_name=self.table_name)
            self.raw_records = data_db.get_all_records()
            
            # Performance-Instanzen erstellen
            self.optimized_instances = []
            for record in self.raw_records:
                instance = PdvmCentralDatenbank.create_with_data(
                    guid=record["uid"],
                    daten=record["daten"],
                    table_name=self.table_name
                )
                self.optimized_instances.append(instance)
            
            logger.info(f"✅ {len(self.optimized_instances)} Datensätze geladen")
            
        except Exception as e:
            logger.error(f"❌ Datenladung fehlgeschlagen: {e}")
            self.raw_records = []
            self.optimized_instances = []
    
    def _initialize_matrix_manager(self):
        """5. Matrix Manager initialisieren"""
        logger.info("🎯 SCHRITT 5: Matrix Manager initialisieren...")
        
        try:
            from pdvm_view_matrix_manager import PdvmViewMatrixManager
            
            self.matrix_manager = PdvmViewMatrixManager(
                view_guid=self.view_guid,
                gcs=self.gcs,
                controller=self  # Für Projektions-Zugriff (view-spezifisch!)
            )
            
            logger.info("✅ Matrix Manager initialisiert (mit Controller-Referenz)")
            
            # V3 Filter-System: Manager initialisieren
            self.schnellsuche_manager = SchnellsucheManager(
                view_guid=self.view_guid,
                matrix_manager=self.matrix_manager
            )
            logger.info("✅ SchnellsucheManager initialisiert")
            
            self.einfach_filter_manager = EinfachFilterManager(
                view_guid=self.view_guid,
                matrix_manager=self.matrix_manager,
                controller=self  # NEU: Controller-Referenz für UI-Refresh
            )
            logger.info("✅ EinfachFilterManager initialisiert")
            
        except Exception as e:
            logger.error(f"❌ Matrix Manager Initialisierung fehlgeschlagen: {e}")
            raise
    
    def _build_basis_matrix(self):
        """6. BasisMatrix aus Instanzen erstellen"""
        logger.info("🏗️ SCHRITT 6: BasisMatrix erstellen...")
        
        try:
            if not self.matrix_manager:
                raise RuntimeError("Matrix Manager nicht initialisiert!")
            
            if not self.optimized_instances:
                logger.warning("⚠️ Keine Instanzen zum Befüllen der BasisMatrix!")
                return
            
            if not self.all_controls:
                raise RuntimeError("Controls nicht verfügbar!")
            
            # BasisMatrix initialisieren
            self.matrix_manager.initialize_basis_matrix(
                instances=self.optimized_instances,
                all_controls=self.all_controls
            )
            
            logger.info("✅ BasisMatrix erstellt")
            
        except Exception as e:
            logger.error(f"❌ BasisMatrix-Erstellung fehlgeschlagen: {e}")
            raise
    
    def _run_matrix_pipeline(self):
        """
        Matrix-Pipeline durchlaufen (Filter → Sort → Gruppierung)
        
        🆕 AUTONOME PIPELINE:
        - Pipeline holt Sort-Config SELBST aus GCS (wie Filter!)
        - KEINE Übergabe von Config - Pipeline ist autonom!
        - Config wird bei rebuild_pipeline() aus GCS geladen
        """
        logger.info("🔄 SCHRITT 7: Matrix-Pipeline durchlaufen...")
        
        try:
            if not self.matrix_manager:
                raise RuntimeError("Matrix Manager nicht initialisiert!")
            
            # NEUE Pipeline verwenden - kompletter Start mit BASIS!
            from pdvm_pipeline import get_pipeline
            pipeline = get_pipeline(self.view_guid, self.matrix_manager)
            pipeline.run('BASIS')  # ← Kompletter Start: BASIS→FILTER→SORT→PROJECT
            
            logger.info(f"  📊 BasisMatrix: {len(self.matrix_manager.basis_matrix)} Zeilen")
            logger.info(f"  � Pipeline: BASIS→FILTER→SORT→PROJECT abgeschlossen")
            
            logger.info("✅ Matrix-Pipeline durchlaufen")
            
        except Exception as e:
            logger.error(f"❌ Matrix-Pipeline fehlgeschlagen: {e}")
            raise
    
    def _create_ui(self):
        """8. UI erstellen"""
        logger.info("🎨 SCHRITT 8: UI erstellen...")
        
        try:
            from pdvm_view_ui import PdvmViewUI
            
            # UI erstellen (baut Widgets auf)
            self.ui = PdvmViewUI(
                controller=self,
                parent=self.parent
            )
            logger.info("✅ UI-Widgets erstellt")
            
            # Signal-Verbindungen
            self.ui.search_requested.connect(self._handle_search)
            self.ui.filter_requested.connect(self._handle_filter_request)
            self.ui.sort_requested.connect(self._handle_sort_request)
            logger.info("✅ UI-Signals verbunden")
            
            # ✅ V3: Schnellsuche-UI laden (falls gespeichert)
            self._load_schnellsuche_ui()
            
            # JETZT ERST Daten an UI übergeben (nach Widget-Setup)
            self.refresh_ui_from_matrix()
            
            logger.info("✅ UI erstellt und Daten übergeben")
            
        except Exception as e:
            logger.error(f"❌ UI-Erstellung fehlgeschlagen: {e}")
            raise
    
    def _load_schnellsuche_ui(self):
        """
        Lädt gespeicherte Schnellsuche in UI-Textfeld
        
        Wird nach UI-Erstellung aufgerufen, um gespeicherten Suchtext anzuzeigen.
        """
        logger.info("📥 Lade Schnellsuche-UI aus GCS...")
        
        try:
            if not self.ui or not hasattr(self.ui, 'search_input'):
                logger.warning("⚠️ UI oder search_input nicht verfügbar")
                return
            
            # V3: SchnellsucheManager hat load_schnellsuche_ui()
            search_text = self.schnellsuche_manager.load_schnellsuche_ui()
            
            if search_text:
                self.ui.search_input.setText(search_text)
                logger.info(f"✅ Schnellsuche-UI geladen: '{search_text}'")
            else:
                logger.info("ℹ️ Keine gespeicherte Schnellsuche vorhanden")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Schnellsuche-UI: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _initialize_filter_and_sort(self):
        """9. Filter initialisieren (NICHT MEHR NÖTIG - Pipeline ist autonom!)"""
        logger.info("🔧 SCHRITT 9: Filter initialisieren...")
        
        # ✅ Filter-System ist AUTONOM in Pipeline!
        # ✅ SchnellsucheManager, EinfachFilterManager, KomplexFilterManager
        #    werden direkt von den Dialogen verwendet
        # ✅ Pipeline holt s_string + s_source aus app_db
        logger.info("  ✅ Filter-Manager via Dialoge (AUTONOM)")
        
        # ✅ Sortierung ist AUTONOM in Matrix-Pipeline!
        # ✅ Sort-Config wird bei rebuild_pipeline() aus GCS geholt
        logger.info("  ✅ Sortierung via Matrix Manager (AUTONOM aus GCS)")
    
    def _connect_stichtag_signal(self):
        """10. Stichtag-Signal mit View verbinden"""
        logger.info("🔧 SCHRITT 10: Stichtag-Signal verbinden...")
        
        try:
            if self.gcs and hasattr(self.gcs, 'stichtag_manager'):
                stichtag_mgr = self.gcs.stichtag_manager
                
                # Signal verbinden: Bei Stichtag-Änderung → reload_with_stichtag
                stichtag_mgr.stichtag_changed.connect(self.reload_with_stichtag)
                
                logger.info("  ✅ Stichtag-Signal verbunden → reload_with_stichtag()")
                logger.info(f"  📅 Aktueller Stichtag: {self.gcs.stichtag}")
            else:
                logger.warning("  ⚠️ Kein Stichtag-Manager in GCS gefunden")
                
        except Exception as e:
            logger.warning(f"⚠️ Stichtag-Signal Verbindung: {e}")
    
    def _get_columns_from_controls(self):
        """Basis-Spalten aus Controls ableiten"""
        columns = []
        
        for control_key, control_config in self.controls_config.items():
            if control_config.get('control_type') in ['original', 'show']:
                col = {
                    'name': control_key,
                    'label': control_config.get('name', control_key),
                    'type': control_config.get('type', 'string'),
                    'show': control_config.get('show', False),
                    'expert_mode': control_config.get('expert_mode', False),
                    'expert_order': control_config.get('expert_order', 999),
                    'display_order': control_config.get('display_order', 999)
                }
                columns.append(col)
        
        return columns
    
    def get_widget(self):
        """Widget für Hauptanwendung zurückgeben"""
        if self.ui:
            return self.ui.get_widget()
        return None
    
    def refresh(self):
        """
        View neu laden (Zahnrad-Menü)
        
        MATRIX-PIPELINE KOMPLETT NEU DURCHLAUFEN:
        1. BasisMatrix neu erstellen (aktueller Stichtag aus GCS)
        2. Filter anwenden
        3. Sort anwenden
        4. Projektion anwenden
        5. UI aktualisieren
        
        Diese Methode wird vom Zahnrad-Menü "🔄 Aktualisieren" aufgerufen.
        """
        logger.info("🔄 === VIEW REFRESH (Zahnrad-Menü) ===")
        
        try:
            # Hole aktuellen Stichtag aus GCS
            current_stichtag = self.gcs.stichtag if self.gcs else None
            logger.info(f"  📅 Aktueller Stichtag: {current_stichtag}")
            
            # SCHRITT 1: BasisMatrix komplett neu erstellen
            logger.info("  🔧 SCHRITT 1: BasisMatrix neu erstellen...")
            self._build_basis_matrix()
            
            # SCHRITT 2: Matrix-Pipeline durchlaufen
            logger.info("  🔧 SCHRITT 2: Matrix-Pipeline durchlaufen...")
            self._run_matrix_pipeline()
            
            # SCHRITT 3: UI aktualisieren
            logger.info("  🔧 SCHRITT 3: UI aktualisieren...")
            self.refresh_ui_from_matrix()
            
            logger.info("✅ View Refresh abgeschlossen")
            
        except Exception as e:
            logger.error(f"❌ View Refresh fehlgeschlagen: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def reset_controls_to_default(self):
        """
        Controls auf Standard zurücksetzen - View komplett neu laden
        
        WORKFLOW:
        1. Altes UI-Widget aus Parent-Layout entfernen
        2. Reset-Flag setzen
        3. Komplett neu initialisieren (wie beim ersten Start)
        4. Neues UI-Widget in Parent-Layout einfügen
        """
        logger.info("=== CONTROLS RESET TO DEFAULT ===")
        
        try:
            # SCHRITT 1: Altes UI-Widget aus Parent-Layout entfernen
            logger.info("  Entferne altes UI-Widget aus Parent-Layout...")
            if self.ui and self.parent and hasattr(self.parent, 'content_layout'):
                # Widget aus Layout entfernen
                self.parent.content_layout.removeWidget(self.ui)
                self.ui.close()
                self.ui.deleteLater()
                self.ui = None
                logger.info("  Altes UI-Widget entfernt")
            
            # SCHRITT 2: Reset-Flag setzen
            logger.info("  Setze Reset-Flag...")
            self.reset = True
            
            # SCHRITT 3: View komplett neu initialisieren
            logger.info("  Initialisiere View komplett neu...")
            self.initialize()
            
            # SCHRITT 4: Neues UI-Widget in Parent-Layout einfügen
            logger.info("  Füge neues UI-Widget in Parent-Layout ein...")
            if self.ui and self.parent and hasattr(self.parent, 'content_layout'):
                self.parent.content_layout.addWidget(self.ui)
                logger.info("  Neues UI-Widget eingefügt")
            
            logger.info("Controls erfolgreich auf Standard zurückgesetzt - View neu geladen")
            
        except Exception as e:
            logger.error(f"Controls-Reset fehlgeschlagen: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    def reload_with_stichtag(self, new_stichtag):
        """
        Reload bei Stichtag-Änderung
        
        MATRIX-PIPELINE KOMPLETT NEU DURCHLAUFEN:
        1. BasisMatrix neu erstellen (mit neuem Stichtag)
        2. Filter anwenden
        3. Sort anwenden
        4. Projektion anwenden
        5. UI aktualisieren
        
        Args:
            new_stichtag: Neuer Stichtag als float (z.B. 2025043.0)
        """
        logger.info(f"🗓️ === STICHTAG-RELOAD: {new_stichtag} ===")
        
        try:
            # GCS Stichtag sollte bereits aktualisiert sein durch StichtagManager
            # Wir prüfen nur zur Sicherheit
            if self.gcs and hasattr(self.gcs, 'stichtag'):
                logger.info(f"  📅 GCS Stichtag: {self.gcs.stichtag}")
            
            # SCHRITT 1: BasisMatrix komplett neu erstellen mit neuem Stichtag
            logger.info("  🔧 SCHRITT 1: BasisMatrix neu erstellen...")
            self._build_basis_matrix()
            
            # SCHRITT 2: Matrix-Pipeline durchlaufen
            logger.info("  🔧 SCHRITT 2: Matrix-Pipeline durchlaufen...")
            self._run_matrix_pipeline()
            
            # SCHRITT 3: UI aktualisieren
            logger.info("  🔧 SCHRITT 3: UI aktualisieren...")
            self.refresh_ui_from_matrix()
            
            logger.info("✅ Stichtag-Reload abgeschlossen")
            
        except Exception as e:
            logger.error(f"❌ Stichtag-Reload fehlgeschlagen: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def refresh_projection_only(self):
        """
        Nur Projektion neu anwenden (für Spalten-Verwaltung)
        
        EFFIZIENTER WORKFLOW:
        1. Controls aus GCS neu laden (wurden vom Dialog geändert)
        2. Projektions-Tabellen neu berechnen (aus geänderten Controls)
        3. Projektion auf bestehende SortMatrix anwenden
        4. UI aktualisieren
        
        KEINE BasisMatrix/Filter/Sort Rebuild!
        Verwendet für: Spalten-Verwaltung, Expert-Mode Toggle
        """
        logger.info("🔄 === PROJECTION-ONLY REFRESH ===")
        
        try:
            # SCHRITT 1: Controls aus GCS neu laden
            logger.info("  📥 SCHRITT 1: Controls aus GCS neu laden...")
            if self.gcs and hasattr(self.gcs, 'db'):
                updated_controls, _ = self.gcs.db.get_value(self.view_guid, 'controls')
                if updated_controls:
                    self.all_controls = updated_controls
                    logger.info(f"  ✅ {len(self.all_controls)} Controls neu geladen")
                else:
                    logger.warning("  ⚠️ Keine Controls aus GCS geladen - verwende bestehende")
            
            # SCHRITT 2: Projektions-Tabellen neu berechnen
            logger.info("  📊 SCHRITT 2: Projektions-Tabellen neu berechnen...")
            self._build_projection_tables()
            
            # SCHRITT 3: Projektion auf bestehende SortMatrix anwenden
            logger.info("  🎯 SCHRITT 3: Projektion anwenden...")
            self.refresh_ui_from_matrix()
            
            logger.info("✅ Projection-Only Refresh abgeschlossen")
            
        except Exception as e:
            logger.error(f"❌ Projection-Only Refresh fehlgeschlagen: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def refresh_ui_from_pipeline(self):
        """
        UI aus Pipeline aktualisieren - VOLLSTÄNDIG AUTONOM!
        
        Pipeline liefert:
        - Projizierte Matrix-Daten
        - Sichtbare Spalten
        - Aktuellen Suchtext für Schnellsuche-Feld
        """
        logger.info(f"🎨 UI-Update aus Pipeline")
        
        try:
            if not self.ui:
                logger.error("❌ UI nicht verfügbar!")
                return
            
            # Pipeline holen
            from pdvm_pipeline import get_pipeline
            pipeline = get_pipeline(self.view_guid, self.matrix_manager)
            
            # Projizierte Daten aus Pipeline holen
            matrix_project, visible_columns = pipeline.get_projected_data()
            search_text = pipeline.get_search_text()
            
            logger.info(f"📊 {len(matrix_project)} Zeilen, {len(visible_columns)} Spalten")
            logger.info(f"🔍 Suchtext: '{search_text}'" if search_text else "📋 Suchfeld leer")
            
            # Schnellsuche-Feld aktualisieren
            if hasattr(self.ui, 'search_field'):
                if search_text:
                    self.ui.search_field.setText(search_text)
                else:
                    self.ui.search_field.clear()
            
            # Matrix-Daten in UI anzeigen
            self.ui.set_data_from_matrix(matrix_project, visible_columns, self.all_controls)
            
            logger.info("✅ UI-Update fertig")
            
        except Exception as e:
            logger.error(f"❌ UI-Update fehlgeschlagen: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def refresh_ui_from_matrix(self):
        """
        UI aus Matrix Manager aktualisieren (Legacy-Methode)
        
        Ruft refresh_ui_from_pipeline() auf
        """
        self.refresh_ui_from_pipeline()
    
    # === EVENT HANDLER ===
    
    def on_filter_requested(self, filter_type, filter_config):
        """
        Filter anwenden (von UI aufgerufen)
        
        🆕 PERSISTENTE SORTIERUNG:
        - Filter ändert nur FilterMatrix
        - Sortierung wird DANACH automatisch angewendet (via _run_matrix_pipeline)
        - self.current_sort_config bleibt erhalten!
        """
        logger.info(f"🔍 Filter angefordert: {filter_type}")
        
        if self.linear_filter:
            try:
                self.linear_filter.execute_filter_linear(filter_type, filter_config)
                
                # Nach Filter: Matrix neu laden
                # ✅ _run_matrix_pipeline() verwendet automatisch self.current_sort_config!
                self.refresh()
                
                logger.info("✅ Filter + Sortierung angewendet")
            except Exception as e:
                logger.error(f"❌ Filter-Fehler: {e}")
    
    def on_sort_requested(self, sort_config):
        """
        Sortierung anwenden (von UI aufgerufen nach Dialog)
        
        🆕 AUTONOME PIPELINE:
        1. Config ist BEREITS in GCS gespeichert (vom Dialog)
        2. Pipeline neu durchlaufen - holt Config AUTONOM aus GCS
        3. UI aktualisieren
        
        Args:
            sort_config: Liste von {'column_key', 'direction', 'is_group'}
                        (wird NICHT verwendet - nur für Logging)
        """
        logger.info(f"📊 Sortierung angefordert: {len(sort_config)} Spalten")
        
        try:
            # Logging (Config ist bereits in GCS gespeichert vom Dialog!)
            for idx, cfg in enumerate(sort_config):
                group_marker = " [GRUPPE]" if cfg.get('is_group') else ""
                logger.info(f"  {idx+1}. {cfg['column_key']} → {cfg['direction']}{group_marker}")
            
            # Matrix-Pipeline neu durchlaufen (holt Config AUTONOM aus GCS!)
            self._run_matrix_pipeline()
            
            # UI aktualisieren
            self.refresh_ui_from_matrix()
            
            logger.info("✅ Sortierung angewendet (Pipeline holte Config aus GCS)")
            
        except Exception as e:
            logger.error(f"❌ Sortier-Fehler: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def on_column_visibility_changed(self, column_name, visible):
        """Spalten-Sichtbarkeit geändert (von UI aufgerufen)"""
        logger.info(f"👁️ Spalte '{column_name}': visible={visible}")
        
        # Control in GCS aktualisieren
        if column_name in self.controls_config:
            self.controls_config[column_name]['show'] = visible
            self.gcs.db.set_value(
                gruppe=self.view_guid,
                feld='controls',
                wert=self.controls_config
            )
            self.gcs.db.save_all_values()
            
            # Projektions-Tabellen neu berechnen (on-demand aus geänderten Controls)
            self._build_projection_tables()
            logger.info("  ✅ Projektionen neu berechnet nach Control-Änderung")
    
    # ============================================================================
    # PROJEKTIONS-SYSTEM - VIEW-SPEZIFISCH, NICHT PERSISTENT
    # ============================================================================
    
    def _build_projection_tables(self):
        """
        Wrapper für GCS-Projektions-Tabellen Aufbau.
        Baut Projektionen in GCS (für Dialog-Zugriff) und holt lokale Kopie.
        """
        try:
            # Baue Projektions-Tabellen in GCS (für Dialog-Zugriff)
            self.gcs._build_projection_tables(self.view_guid)
            logger.info(f"✅ Projektions-Tabellen in GCS aufgebaut")
            
            # Lokale Referenz für schnellen Zugriff
            self.projection_tables = {
                'table_standard': self.gcs.get_projection_table(self.view_guid, 'table_standard'),
                'table_expert': self.gcs.get_projection_table(self.view_guid, 'table_expert'),
                'search_standard': self.gcs.get_projection_table(self.view_guid, 'search_standard'),
                'search_expert': self.gcs.get_projection_table(self.view_guid, 'search_expert'),
                'change_standard': self.gcs.get_projection_table(self.view_guid, 'change_standard'),
                'change_expert': self.gcs.get_projection_table(self.view_guid, 'change_expert'),
                'sort_standard': self.gcs.get_projection_table(self.view_guid, 'sort_standard'),
                'sort_expert': self.gcs.get_projection_table(self.view_guid, 'sort_expert')
            }
            
            logger.info(f"✅ Projektions-Tabellen lokal referenziert:")
            logger.info(f"  📊 Table Standard: {len(self.projection_tables['table_standard'])} Spalten")
            logger.info(f"  📊 Table Expert: {len(self.projection_tables['table_expert'])} Spalten")
            logger.info(f"  🔍 Search Standard: {len(self.projection_tables['search_standard'])} Spalten")
            logger.info(f"  🔍 Search Expert: {len(self.projection_tables['search_expert'])} Spalten")
            logger.info(f"  🔧 Change Standard: {len(self.projection_tables['change_standard'])} Spalten")
            logger.info(f"  🔧 Change Expert: {len(self.projection_tables['change_expert'])} Spalten")
            logger.info(f"  🔄 Sort Standard: {len(self.projection_tables['sort_standard'])} Spalten")
            logger.info(f"  🔄 Sort Expert: {len(self.projection_tables['sort_expert'])} Spalten")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aufbau der Projektions-Tabellen: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Fallback: Leere Projektionen
            self.projection_tables = {
                'table_standard': [],
                'table_expert': [],
                'search_standard': [],
                'search_expert': [],
                'change_standard': [],
                'change_expert': [],
                'sort_standard': [],
                'sort_expert': []
            }
    
    def get_projection_table(self, table_name: str):
        """
        Gibt eine Projektions-Tabelle zurück.
        
        Args:
            table_name: Name der Tabelle (z.B. 'table_standard', 'table_expert')
        
        Returns:
            Liste von Spalten-Keys
        """
        if not hasattr(self, 'projection_tables'):
            logger.warning("⚠️ Projektions-Tabellen noch nicht berechnet - berechne jetzt...")
            self._build_projection_tables()
        
        return self.projection_tables.get(table_name, [])
    
    # ===== FILTER & SUCHE HANDLER =====
    
    def _handle_search(self, search_text):
        """
        Handler für Schnellsuche (Suchzeile über View)
        
        Speichert Suchtext - wird über Button ausgeführt
        """
        logger.info(f"🔍 Suchtext eingegeben: '{search_text}'")
        self.pending_search_text = search_text
    
    def execute_search(self):
        """
        Schnellsuche ausführen - EINFACH mit Pipeline!
        
        1. Suchtext aus UI holen
        2. SchnellsucheManager.execute_schnellsuche() → setzt DB + ruft pipeline.run('FILTER')
        3. UI aktualisieren aus Pipeline
        """
        # Suchtext aus UI lesen
        search_text = getattr(self, 'pending_search_text', '')
        
        if not search_text and self.ui and hasattr(self.ui, 'search_input'):
            search_text = self.ui.search_input.text().strip()
        
        logger.info(f"🔍 Schnellsuche: '{search_text}'")
        
        try:
            # SchnellsucheManager macht: DB setzen + pipeline.run('FILTER')
            success = self.schnellsuche_manager.execute_schnellsuche(search_text)
            
            if success:
                # UI aktualisieren aus Pipeline
                self.refresh_ui_from_pipeline()
                logger.info(f"✅ Schnellsuche fertig")
            else:
                logger.error(f"❌ Schnellsuche fehlgeschlagen")
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self.ui if self.ui else None,
                    "Schnellsuche fehlgeschlagen",
                    f"Die Schnellsuche konnte nicht ausgeführt werden.\n\nSuchtext: '{search_text}'"
                )
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Schnellsuche: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self.ui if self.ui else None,
                "Fehler bei Schnellsuche",
                f"Es ist ein Fehler aufgetreten:\n\n{str(e)}"
            )
    
    def _handle_filter_request(self, filter_type, filter_config):
        """
        Handler für Filter-Anfragen aus Menü
        
        Args:
            filter_type: 'simple', 'complex', 'reset'
            filter_config: Filter-Konfiguration
        """
        logger.info(f"🔍 Filter-Anfrage: {filter_type}")
        
        if filter_type == 'reset':
            logger.info("🗑️ Filter zurücksetzen - V3 FilterResetManager")
            
            try:
                # ✅ V3: FilterResetManager für ALLE Filter-Löschungen
                from filter_reset_manager import get_filter_reset_manager
                reset_manager = get_filter_reset_manager(self.view_guid, self.matrix_manager)
                success = reset_manager.reset_all_filters()
                
                if success:
                    # UI aktualisieren
                    self.refresh_ui_from_matrix()
                    logger.info("✅ Alle Filter zurückgesetzt")
                    
                    # Erfolgsmeldung
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.information(
                        self.ui if self.ui else None,
                        "Filter zurückgesetzt",
                        "Alle aktiven Filter wurden erfolgreich entfernt."
                    )
                else:
                    logger.error("❌ Filter-Reset fehlgeschlagen")
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.warning(
                        self.ui if self.ui else None,
                        "Fehler",
                        "Beim Zurücksetzen der Filter ist ein Fehler aufgetreten."
                    )
                    
            except Exception as e:
                logger.error(f"❌ Fehler beim Filter-Reset: {e}")
                import traceback
                logger.error(traceback.format_exc())
                
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self.ui if self.ui else None,
                    "Fehler",
                    f"Kritischer Fehler beim Zurücksetzen der Filter:\n\n{str(e)}"
                )
            
            return
        
        # Sichtbare Spalten und Controls holen
        visible_columns = self.get_projection_table('table_expert' if self.gcs.expert_mode else 'table_standard')
        
        if filter_type == 'simple':
            # Einfacher Filter-Dialog
            from pdvm_simple_filter_dialog import show_simple_filter_dialog
            
            filter_data = show_simple_filter_dialog(
                parent=self.ui,
                view_guid=self.view_guid,
                visible_columns=visible_columns,
                column_control=self.all_controls
            )
            
            if filter_data:
                self._apply_simple_filter(filter_data)
        
        elif filter_type == 'complex':
            # Komplexer Filter-Dialog
            from pdvm_complex_filter_dialog import show_complex_filter_dialog
            
            filter_data = show_complex_filter_dialog(
                parent=self.ui,
                view_guid=self.view_guid,
                visible_columns=visible_columns,
                column_control=self.all_controls
            )
            
            if filter_data:
                self._apply_complex_filter(filter_data)
    
    def _apply_simple_filter(self, filter_data):
        """
        EINFACH: Erstellt Filter-Funktion und ruft Matrix Manager auf
        """
        logger.info(f"🔍 Wende einfachen Filter an: {len(filter_data)} Felder")
        
        try:
            # Sichtbare Spalten
            visible_columns = self.get_projection_table('table_expert' if self.gcs.expert_mode else 'table_standard')
            
            # Filter-Funktion erstellen
            def simple_filter(row_data):
                for field_key, field_filter in filter_data.items():
                    value_to_search = field_filter['value'].lower()
                    is_positive = (field_filter['mode'] == 'positive')
                    
                    if field_key not in row_data:
                        continue
                    
                    # Array-Wert holen (WERT = Index 0)
                    cell = row_data[field_key]
                    if isinstance(cell, list) and len(cell) > 0:
                        wert = cell[0]  # WERT
                    else:
                        wert = cell
                    
                    field_str = str(wert).lower() if wert is not None else ''
                    contains = value_to_search in field_str
                    
                    if is_positive and not contains:
                        return False
                    if not is_positive and contains:
                        return False
                
                return True
            
            # EINFACHER Aufruf: Matrix Manager macht alles!
            self.matrix_manager.apply_custom_filter(simple_filter, visible_columns)
            
            # UI aktualisieren
            self.refresh_ui_from_matrix()
            
            logger.info(f"✅ Einfacher Filter angewendet")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anwenden des einfachen Filters: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _apply_complex_filter(self, filter_data):
        """
        EINFACH: Erstellt Filter-Funktion und ruft Matrix Manager auf
        """
        logger.info(f"🔍 Wende komplexen Filter an: {len(filter_data)} Felder")
        
        try:
            from pdvm_complex_filter_dialog import SearchCondition
            
            # Sichtbare Spalten
            visible_columns = self.get_projection_table('table_expert' if self.gcs.expert_mode else 'table_standard')
            
            # Filter-Funktion erstellen
            def complex_filter(row_data):
                for field_key, field_filter in filter_data.items():
                    conditions = [SearchCondition.from_dict(c) for c in field_filter['conditions']]
                    
                    if not conditions:
                        continue
                    
                    if field_key not in row_data:
                        return False
                    
                    # Array-Wert holen (WERT = Index 0)
                    cell = row_data[field_key]
                    if isinstance(cell, list) and len(cell) > 0:
                        wert = cell[0]  # WERT
                    else:
                        wert = cell
                    
                    field_str = str(wert).lower() if wert is not None else ''
                    
                    field_result = None
                    for cond in conditions:
                        match = self._evaluate_condition(field_str, cond)
                        
                        if cond.logic_operator == 'FIRST':
                            field_result = match
                        elif cond.logic_operator == 'AND':
                            field_result = field_result and match
                        elif cond.logic_operator == 'OR':
                            field_result = field_result or match
                    
                    if not field_result:
                        return False
                
                return True
            
            # EINFACHER Aufruf: Matrix Manager macht alles!
            self.matrix_manager.apply_custom_filter(complex_filter, visible_columns)
            
            # UI aktualisieren
            self.refresh_ui_from_matrix()
            
            logger.info(f"✅ Komplexer Filter angewendet")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anwenden des komplexen Filters: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _evaluate_condition(self, field_str, condition):
        """
        Evaluiert eine einzelne SearchCondition
        
        Args:
            field_str: Feldwert als String (lowercase)
            condition: SearchCondition
        
        Returns:
            bool: Bedingung erfüllt?
        """
        search_value = condition.value.lower()
        operator = condition.operator_type
        
        # Operator anwenden
        if operator == 'enthält':
            match = search_value in field_str
        elif operator == 'beginnt mit':
            match = field_str.startswith(search_value)
        elif operator == 'endet mit':
            match = field_str.endswith(search_value)
        elif operator == 'ist gleich':
            match = field_str == search_value
        elif operator == 'ist leer':
            match = len(field_str) == 0
        elif operator == '>':
            try:
                match = float(field_str) > float(search_value)
            except:
                match = field_str > search_value
        elif operator == '<':
            try:
                match = float(field_str) < float(search_value)
            except:
                match = field_str < search_value
        elif operator == '>=':
            try:
                match = float(field_str) >= float(search_value)
            except:
                match = field_str >= search_value
        elif operator == '<=':
            try:
                match = float(field_str) <= float(search_value)
            except:
                match = field_str <= search_value
        else:
            match = False
        
        # Negation anwenden
        if condition.negation == 'NOT':
            match = not match
        
        return match
    
    def _handle_sort_request(self, sort_config):
        """
        Handler für Sortierungs-Anfragen (Header-Klick ODER Dialog)
        
        Args:
            sort_config: 
                SINGLE-SORT (Header-Klick): {
                    'column': 'familienname_show',
                    'direction': 'asc' oder 'desc'
                }
                MULTI-SORT (Dialog): [
                    {'column_key': 'anrede_show', 'direction': 'asc', 'is_group': False},
                    {'column_key': 'familienname_show', 'direction': 'desc', 'is_group': False}
                ]
        """
        logger.info(f"📊 Sortierungs-Anfrage: {sort_config}")
        
        try:
            # Prüfen: Liste (Multi-Sort) oder Dict (Single-Sort)?
            if isinstance(sort_config, list):
                # MULTI-SORT aus Dialog (kann Gruppierung enthalten!)
                logger.info(f"🔢 Multi-Sort mit {len(sort_config)} Spalten")
                
                # PHASE 3: Trenne Gruppierungs-Spalten von Sortier-Spalten
                group_columns = []
                sort_columns = []
                
                for col in sort_config:
                    column_key = col.get('column_key')  # Dialog nutzt 'column_key'
                    control = self.controls_config.get(column_key, {})
                    is_group = col.get('is_group', False)  # ⭐ NEU: Gruppierungs-Flag
                    
                    col_config = {
                        'column': column_key,  # Matrix Manager nutzt 'column'
                        'direction': col.get('direction', 'asc'),
                        'use_original': control.get('sortByOriginal', False)
                    }
                    
                    if is_group:
                        group_columns.append(col_config)
                        logger.info(f"  📊 Gruppierungs-Spalte: {column_key}")
                    else:
                        sort_columns.append(col_config)
                        logger.info(f"  🔄 Sortier-Spalte: {column_key}")
                
                # Prüfe ob Gruppierung aktiv
                if group_columns:
                    # GRUPPIERUNG + SORTIERUNG
                    logger.info(f"📊 GRUPPIERUNG: {len(group_columns)} Ebenen + {len(sort_columns)} Sort-Spalten")
                    full_sort_config = {
                        'type': 'grouping',  # ⭐ NEU: Typ-Marker
                        'group_columns': group_columns,
                        'sort_columns': sort_columns
                    }
                else:
                    # NUR SORTIERUNG (keine Gruppierung)
                    logger.info(f"🔄 Multi-Sort: {len(sort_columns)} Spalten (KEINE Gruppierung)")
                    full_sort_config = {
                        'type': 'multi_sort',
                        'columns': sort_columns
                    }
                
            else:
                # SINGLE-SORT von Header-Klick (NIE Gruppierung)
                column_key = sort_config['column']
                control = self.controls_config.get(column_key, {})
                use_original = control.get('sortByOriginal', False)
                
                # Erweiterte Config mit use_original
                full_sort_config = {
                    'type': 'single_sort',  # ⭐ NEU: Typ-Marker
                    'column': column_key,
                    'direction': sort_config['direction'],
                    'use_original': use_original
                }
                
                logger.info(f"🔄 Single-Sort: {column_key} {sort_config['direction']}")
            
            # Persistieren in App-DB
            self.gcs._app_db.set_value(self.view_guid, 'sort', full_sort_config)
            logger.info(f"💾 Config persistiert")
            
            # Matrix Manager anwenden (unterschiedliche Methoden je nach Typ)
            config_type = full_sort_config.get('type', 'unknown')
            
            if config_type == 'grouping':
                # PHASE 3: Gruppierung anwenden
                logger.info(f"📊 Wende Gruppierung an...")
                self.matrix_manager.apply_grouping(
                    group_columns=full_sort_config['group_columns'],
                    sort_columns=full_sort_config['sort_columns']
                )
            else:
                # Normale Sortierung (single oder multi)
                logger.info(f"🔄 Wende Sortierung an...")
                self.matrix_manager.apply_sort_config(full_sort_config)
            
            # UI aktualisieren
            self.refresh_ui_from_matrix()
            
            logger.info(f"✅ {'Gruppierung' if config_type == 'grouping' else 'Sortierung'} angewendet")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anwenden der Sortierung: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def reset_sort(self):
        """
        Sortierung zurücksetzen (aus Zahnrad-Menü)
        
        🆕 AUTONOME PIPELINE:
        1. Sort-Config in GCS löschen
        2. Pipeline neu durchlaufen (holt Config autonom - findet None)
        3. UI aktualisieren
        """
        logger.info(f"🔄 Sortierung zurücksetzen")
        
        try:
            # 1. Sort-Config in GCS löschen
            self.gcs._app_db.set_value(self.view_guid, 'sort', None)
            self.gcs._app_db.save_all_values()  # 💾 CRITICAL: Commit to database!
            logger.info(f"  🗑️ Sort-Config in GCS gelöscht")
            
            # 2. Matrix-Pipeline neu durchlaufen (holt Config autonom - findet None = keine Sortierung)
            self._run_matrix_pipeline()
            
            # 3. UI aktualisieren
            self.refresh_ui_from_matrix()
            
            logger.info(f"✅ Sortierung zurückgesetzt - Original-Reihenfolge (Pipeline holte None aus GCS)")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Zurücksetzen der Sortierung: {e}")
            import traceback
            logger.error(traceback.format_exc())
