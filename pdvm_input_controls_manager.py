"""
PDVM Input-Controls Manager - FINALE PRODUKTIVE VERSION

🎯 KONZEPT: MANAGER IST NUR NOCH KOORDINATOR

ARCHITEKTUR:
- Manager erstellt NUR ROOT-Instanz
- Controls sind VOLLSTÄNDIG AUTONOM (beschaffen eigene Instanz)
- Manager ist nur noch Koordinator (render/save/refresh)

VERANTWORTLICHKEITEN:
1. ROOT-Instanz erstellen
2. Metadaten laden
3. Controls erstellen (mit autonomer Instanz-Beschaffung)
4. Kommandos koordinieren (render/save/refresh)
5. UI zusammenbauen (Tabs, Buttons, etc.)

AUTOR: Norbert Peters
DATUM: 28.10.2025
VERSION: 1.0 (Konsolidiert aus V3)
"""

import logging
from typing import List
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QPushButton, 
                             QHBoxLayout, QMessageBox, QLabel, QTabWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QObject

from pdvm_central_systemsteuerung import get_gcs
from pdvm_central_datenbank import PdvmCentralDatenbank
from pdvm_datetime import Pdvm_DateTime
from pdvm_date_time_picker import PdvmDateTimePicker
from pdvm_input_control import PdvmInputControlV4  # ✅ V2-Version!

logger = logging.getLogger(__name__)


class PdvmInputControlsManager(QObject):
    """
    Finaler Manager für autonome Input-Controls
    
    VERANTWORTLICHKEITEN:
    - ROOT-Instanz erstellen
    - Metadaten laden
    - Controls erstellen (AUTONOM!)
    - Kommandos koordinieren (render/save/refresh)
    - UI zusammenbauen
    
    SIGNALS:
    - refresh_requested: Bei Stichtag-Änderung
    """
    
    refresh_requested = pyqtSignal()
    save_completed = pyqtSignal()  # NEU: Nach erfolgreichem Speichern
    
    def __init__(self, framedaten_db, selected_guid: str, frame_guid: str = None, main_app=None, gcs=None):
        """
        Args:
            framedaten_db: Framedaten-DB (für ROOT_TABLE, HEADER, METADATEN)
                          Die DB-Instanz IST bereits für die Frame-GUID - keine redundante Speicherung!
            selected_guid: GUID des ausgewählten Datensatzes
            frame_guid: DEPRECATED - wird ignoriert (framedaten_db ist die DB für diese Frame)
            main_app: OPTIONAL - Referenz zur MainApp (für spätere Erweiterungen)
            gcs: OPTIONAL - GCS-Instanz (wenn None, wird get_gcs() verwendet)
        """
        super().__init__()
        
        logger.info("🎯 === INPUT CONTROLS MANAGER V3 (AUTONOM) ===")
        
        self.framedaten_db = framedaten_db
        self.selected_guid = selected_guid
        self.main_app = main_app  # ✅ Speichern (aktuell ungenutzt, für Kompatibilität)
        
        # V2: GCS holen (entweder als Parameter oder via get_gcs)
        self.gcs = gcs if gcs is not None else get_gcs()
        if not self.gcs:
            raise RuntimeError("❌ GCS nicht initialisiert!")
        
        logger.info(f"  📋 Selected-GUID: {self.selected_guid}")
        
        # ROOT-INSTANZ (NUR DIESE EINE!)
        self.root_instance = None
        
        # CONTROLS-LISTE (Matrix ohne Instanzen!)
        self.controls = []
        
        # NEUES ABDATUM (für Speichern) - INIT aus GCS (wie V2)
        self._initialize_neues_abdatum()
        
        # UI-KOMPONENTEN
        self.main_widget = None
        self.tab_widget = None
        self.abdatum_picker = None
        self.save_button = None
        self.settings_button = None  # Nur Admin-Modus
    
    # =========================================================================
    # HAUPTMETHODE: Widget erstellen
    # =========================================================================
    
    def get_widget(self) -> QWidget:
        """
        Erstellt Widget mit allen Controls (ULTRA EINFACH!)
        
        ABLAUF:
        1. Framedaten laden (ROOT_TABLE, HEADER, METADATEN)
        2. ROOT-Instanz erstellen (NUR DIESE EINE!)
        3. Controls erstellen (AUTONOM!)
        4. UI zusammenbauen (Tabs, Buttons, etc.)
        5. Alle Controls rendern
        
        Returns:
            QWidget mit allen Controls
        """
        logger.info("🏗️ Widget-Erstellung gestartet")
        
        try:
            # [1] FRAMEDATEN LADEN
            header_text, root_table, controls_meta = self._load_framedaten_and_meta()
            
            # [2] ROOT-INSTANZ ERSTELLEN (NUR DIESE!)
            self._create_root_instance(root_table)
            
            # [3] CONTROLS ERSTELLEN (AUTONOM!)
            self._build_controls_matrix(controls_meta)
            
            # [4] UI ZUSAMMENBAUEN
            self._create_ui(header_text)
            
            # [5] ALLE CONTROLS RENDERN
            self._render_all_controls()
            
            logger.info("✅ Widget-Erstellung abgeschlossen")
            return self.main_widget
            
        except Exception as e:
            logger.error(f"❌ FEHLER bei Widget-Erstellung: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Fehler-Widget erstellen
            error_widget = QWidget()
            error_layout = QVBoxLayout()
            error_label = QLabel(f"❌ FEHLER beim Laden:\n\n{str(e)}")
            error_label.setStyleSheet("""
                QLabel {
                    color: red;
                    padding: 20px;
                    font-family: monospace;
                    font-size: 12pt;
                }
            """)
            error_layout.addWidget(error_label)
            error_widget.setLayout(error_layout)
            
            return error_widget
    
    # =========================================================================
    # KOMMANDOS (Koordination)
    # =========================================================================
    
    def save_all_controls(self) -> bool:
        """
        Speichert ALLE Controls (LINEAR durch Liste)
        
        Returns:
            True wenn erfolgreich, False bei Fehler
        """
        logger.info("💾 === SAVE ALL CONTROLS ===")
        
        # Neues Abdatum aus GCS holen
        neues_abdatum = self._get_neues_abdatum()
        
        if not neues_abdatum:
            QMessageBox.warning(
                None,
                "Speichern nicht möglich",
                "Kein gültiges Abdatum gesetzt!"
            )
            return False
        
        logger.info(f"  📅 Neues Abdatum: {neues_abdatum}")
        
        # [1] Alle Controls durchlaufen → save()
        saved_count = 0
        for control in self.controls:
            if control.save(neues_abdatum):
                saved_count += 1
        
        logger.info(f"  ✅ {saved_count} Controls gespeichert")
        
        # [2] DB-Commit (alle Instanzen!)
        try:
            # ROOT-Instanz speichern
            self.root_instance.save_all_values()
            
            # Cache-Instanzen speichern
            for instance in PdvmInputControlV4._instance_cache.values():
                instance.save_all_values()
            
            logger.info("  ✅ Alle DB-Instanzen committed")
            
        except Exception as e:
            logger.error(f"  ❌ Fehler beim DB-Commit: {e}")
            return False
        
        # [3] Alle Controls refreshen
        self.refresh_all_controls()
        
        return True
    
    def refresh(self):
        """
        PUBLIC Refresh-Methode (von Controls nach Historie-Dialog aufgerufen)
        
        Ruft intern refresh_all_controls() auf.
        """
        logger.info("🔄 === REFRESH (von Control aufgerufen) ===")
        self.refresh_all_controls()
    
    def refresh_all_controls(self):
        """
        Refresht ALLE Controls (LINEAR durch Liste)
        
        WICHTIG: Cache wird NICHT geleert, da Instanzen alle
                 historischen Daten enthalten!
        """
        logger.info("🔄 === REFRESH ALL CONTROLS ===")
        
        # Alle Controls durchlaufen → refresh()
        # Controls holen Werte mit neuem Stichtag aus bestehenden Instanzen
        for control in self.controls:
            control.refresh()
        
        logger.info("  ✅ Alle Controls refreshed")
    
    def stichtag_changed(self):
        """
        Handler für Stichtag-Änderung (von außen aufgerufen)
        
        WICHTIG: Cache wird NICHT geleert, da Instanzen alle
                 historischen Daten enthalten!
                 
        Controls lösen ihre Instanz NEU auf, da sich die GUID
        zum neuen Stichtag geändert haben könnte!
        """
        logger.info("📅 === STICHTAG GEÄNDERT ===")
        
        # Alle Controls refreshen
        # Jedes Control:
        # 1. Löst Instanz NEU auf (GUID könnte sich geändert haben!)
        # 2. Lädt Wert mit neuem Stichtag aus Instanz
        self.refresh_all_controls()
        
        logger.info("  ✅ Stichtag-Refresh abgeschlossen")
    
    def rebuild_controls(self):
        """
        KOMPLETTER NEUAUFBAU der Controls (wie bei Stichtag-Änderung)
        
        ABLAUF (identisch zu get_widget()):
        1. Controls-Liste leeren
        2. Root-Instanz neu laden
        3. Controls neu erstellen
        4. UI komplett neu aufbauen
        5. In bestehendes main_widget einhängen
        
        VERWENDET FÜR:
        - Nach Historie-Dialog (Werte wurden in DB geändert)
        - Kompletter Refresh wenn refresh() nicht ausreicht
        """
        logger.info("🔄 === REBUILD CONTROLS (Kompletter Neuaufbau) ===")
        
        try:
            # [1] Alte Controls löschen
            logger.info("  🗑️ Alte Controls entfernen...")
            self.controls.clear()
            
            # [2] Root-Instanz neu laden (wichtig für aktualisierte Daten!)
            logger.info("  📥 Root-Instanz neu laden...")
            header_text, root_table, controls_meta = self._load_framedaten_and_meta()
            self.root_instance = PdvmCentralDatenbank(root_table, self.selected_guid)
            self.root_instance._load_data()  # Daten aus DB laden
            logger.info(f"  ✅ Root-Instanz neu geladen: {root_table}.{self.selected_guid}")
            
            # [3] Controls neu erstellen
            logger.info("  🔨 Controls neu erstellen...")
            self._create_controls(controls_meta)
            logger.info(f"  ✅ {len(self.controls)} Controls neu erstellt")
            
            # [4] UI komplett neu aufbauen
            logger.info("  🎨 UI neu aufbauen...")
            self._create_ui(header_text)
            logger.info("  ✅ UI neu erstellt")
            
            # [5] Altes Widget durch neues ersetzen
            if self.main_widget and hasattr(self, 'parent') and self.parent():
                # Main-Widget hat Parent → Layout aktualisieren
                parent = self.parent()
                parent_layout = parent.layout()
                if parent_layout:
                    # Altes Widget entfernen
                    while parent_layout.count():
                        item = parent_layout.takeAt(0)
                        if item.widget():
                            item.widget().deleteLater()
                    
                    # Neues Widget hinzufügen
                    parent_layout.addWidget(self.main_widget)
                    logger.info("  ✅ UI in Parent-Layout aktualisiert")
            
            logger.info("✅ Rebuild Controls abgeschlossen")
            
        except Exception as e:
            logger.error(f"❌ Rebuild Controls fehlgeschlagen: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    # =========================================================================
    # INTERNE METHODEN
    # =========================================================================
    
    def _initialize_neues_abdatum(self):
        """
        Initialisiert Neues Abdatum aus ZENTRALER GCS-INSTANZ (wie Stichtag!)
        
        WICHTIG: Keine lokale Instanz mehr - nur Referenz auf self.gcs.neues_abdatum_inst!
        """
        logger.info("  📅 === NEUES ABDATUM INITIALISIERUNG ===")
        
        # ZENTRALE INSTANZ: Direkt aus GCS verwenden (systemweit gültig!)
        # Die Instanz wurde bereits in self.gcs.__init__() initialisiert und geladen
        logger.info(f"    ✅ Verwende zentrale GCS-Instanz: self.gcs.neues_abdatum_inst")
        logger.info(f"       📅 Aktueller Wert: {self.gcs.neues_abdatum_inst.FormTimeStamp}")
        logger.info(f"       🔢 Raw PdvmDateTime: {self.gcs.neues_abdatum_inst.PdvmDateTime}")
        
        logger.info("  ✅ Neues Abdatum Initialisierung abgeschlossen")
    
    def _load_framedaten_and_meta(self) -> tuple:
        """
        Lädt Framedaten und Metadaten
        
        Returns:
            (header_text, root_table, controls_meta_list)
        """
        logger.info("📂 Lade Framedaten und Metadaten")
        
        try:
            # [1] HEADER_TEXT
            header_text, _ = self.framedaten_db.get_value('ROOT', 'HEADER_TEXT')
            if not header_text:
                header_text = "Datenbearbeitung"
            
            # [2] ROOT_TABLE
            root_table, _ = self.framedaten_db.get_value('ROOT', 'ROOT_TABLE')
            if not root_table:
                raise ValueError("ROOT_TABLE nicht gefunden!")
            
            # [3] TAB-KONFIGURATION (wie V2)
            self._load_tab_config()
            
            # [4] METADATEN
            controls_meta = self._load_controls_meta()
            
            logger.info(f"  ✅ Header: {header_text}")
            logger.info(f"  ✅ ROOT_TABLE: {root_table}")
            logger.info(f"  ✅ Controls: {len(controls_meta)}")
            
            return header_text, root_table, controls_meta
            
        except Exception as e:
            logger.error(f"  ❌ Fehler beim Laden der Framedaten: {e}")
            raise
    
    def _load_tab_config(self):
        """
        Lädt Tab-Konfiguration aus Framedaten (wie V2)
        
        FRAMEDATEN-FELDER:
        - ROOT.EDIT_TABS: Anzahl der Tabs (Int)
        - ROOT.EDIT_TAB_LABEL_01: Label für Tab 1
        - ROOT.EDIT_TAB_LABEL_02: Label für Tab 2
        """
        try:
            edit_tabs, _ = self.framedaten_db.get_value('ROOT', 'EDIT_TABS')
            self.num_tabs = int(edit_tabs) if edit_tabs else 1
        except:
            self.num_tabs = 1
        
        # Tab-Labels laden
        self.tab_config = {}
        for i in range(1, self.num_tabs + 1):
            field_name = f"EDIT_TAB_LABEL_{i:02d}"
            try:
                label, _ = self.framedaten_db.get_value('ROOT', field_name)
                self.tab_config[i] = label if label else f"Tab {i}"
            except:
                self.tab_config[i] = f"Tab {i}"
        
        logger.info(f"  ✅ {self.num_tabs} Tab(s): {list(self.tab_config.values())}")
    
    def _load_controls_meta(self) -> List[dict]:
        """
        Lädt Metadaten aus framedaten.db (wie V2)
        
        GRUPPE: METADATEN
        FELDER: <FIELD_KEY> (z.B. "PERSONDATEN_PERSDATEN_FAMILIENNAME")
        WERTE: JSON-String mit Metadaten
        
        Returns:
            Liste mit Metadaten-Dicts
        """
        import json
        
        controls_meta = []
        
        try:
            # Gruppe METADATEN holen (wie V2)
            metadaten = self.framedaten_db.get_gruppe('METADATEN')
            
            if not metadaten:
                logger.warning("  ⚠️ Gruppe 'METADATEN' nicht gefunden!")
                return []
            
            # Über alle Fields iterieren
            for field_key, field_config in metadaten.items():
                # Field-Key Format: TABELLE_GRUPPE_FELD
                parts = field_key.split('_')
                if len(parts) < 3:
                    logger.warning(f"  ⚠️ Ungültiger field_key: {field_key}")
                    continue
                
                # Extrahiere Gruppe und Feld
                gruppe = parts[1].upper()
                feld = '_'.join(parts[2:]).upper()
                
                # Extrahiere Attribute
                if isinstance(field_config, dict):
                    label = field_config.get('label', feld.capitalize())
                    source_path = field_config.get('source_path', 'root')
                    tab = field_config.get('tab', 1)
                    order = field_config.get('order', len(controls_meta))
                else:
                    label = feld.capitalize()
                    source_path = 'root'
                    tab = 1
                    order = len(controls_meta)
                
                # Control-Metadaten hinzufügen
                controls_meta.append({
                    'field_key': field_key,
                    'gruppe': gruppe,
                    'feld': feld,
                    'label': label,
                    'order': order,
                    'tab': tab,
                    'source_path': source_path,
                    'field_config': field_config
                })
            
            # Nach Order sortieren
            controls_meta.sort(key=lambda x: x.get('order', 0))
            
            logger.info(f"  ✅ {len(controls_meta)} Metadaten geladen")
            
        except Exception as e:
            logger.error(f"  ❌ Fehler beim Laden der Metadaten: {e}")
        
        return controls_meta
    
    def _create_root_instance(self, root_table: str):
        """
        Erstellt ROOT-Instanz (NUR DIESE EINE!)
        
        Args:
            root_table: Name der ROOT-Tabelle
        """
        logger.info(f"📦 Erstelle ROOT-Instanz: {root_table}")
        
        try:
            self.root_instance = PdvmCentralDatenbank(root_table, self.selected_guid)
            logger.info(f"  ✅ ROOT-Instanz: {root_table}_{self.selected_guid[:8]}...")
        except Exception as e:
            logger.error(f"  ❌ Fehler beim Erstellen der ROOT-Instanz: {e}")
            raise
    
    def _build_controls_matrix(self, controls_meta: List[dict]):
        """
        Erstellt Controls (AUTONOM!)
        
        ULTRA EINFACH: Controls beschaffen sich SELBST ihre Instanz!
        
        Args:
            controls_meta: Liste mit Metadaten
        """
        logger.info(f"🏗️ Erstelle {len(controls_meta)} Controls (AUTONOM)")
        
        for meta in controls_meta:
            try:
                # Control V4 erstellen (Type-basiert!)
                control = PdvmInputControlV4(
                    root_instance=self.root_instance,
                    meta=meta,
                    manager=self,  # Manager-Referenz für Refresh
                    gcs=self.gcs  # ✅ V2: GCS durchreichen!
                )
                
                self.controls.append(control)
                
            except Exception as e:
                logger.error(f"  ❌ Fehler beim Erstellen von Control {meta.get('field_key')}: {e}")
        
        logger.info(f"  ✅ {len(self.controls)} Controls erstellt")
    
    def _create_ui(self, header_text: str):
        """
        Erstellt UI-Struktur (Tabs, Buttons, etc.)
        
        Args:
            header_text: Header-Text für Widget
        """
        logger.info("🎨 Erstelle UI-Struktur")
        
        # Main-Widget
        self.main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Tab-Widget (für Controls)
        self.tab_widget = QTabWidget()
        self._add_controls_to_tabs()
        main_layout.addWidget(self.tab_widget)
        
        # === BUTTONS: Abdatum + Einstellungen + Speichern (Punkt 4) ===
        buttons_layout = self._create_buttons_layout()
        main_layout.addLayout(buttons_layout)
        
        self.main_widget.setLayout(main_layout)
        
        logger.info("  ✅ UI-Struktur erstellt")
    
    def _add_controls_to_tabs(self):
        """Fügt Controls zu Tabs hinzu"""
        # Nach Tabs gruppieren
        tabs_dict = {}
        
        for control in self.controls:
            tab_num = control.tab if hasattr(control, 'tab') else 1
            
            if tab_num not in tabs_dict:
                tabs_dict[tab_num] = []
            
            tabs_dict[tab_num].append(control)
        
        # Tabs erstellen
        for tab_num, tab_controls in sorted(tabs_dict.items()):
            # Tab-Label aus Config holen (wie V2)
            tab_label = self.tab_config.get(tab_num, f"Tab {tab_num}")
            
            tab_widget = QWidget()
            tab_layout = QVBoxLayout()
            
            # Controls hinzufügen (nach Order sortiert)
            for control in sorted(tab_controls, key=lambda c: c.order):
                tab_layout.addWidget(control)
            
            tab_layout.addStretch()
            
            # Scroll-Area
            scroll = QScrollArea()
            scroll.setWidget(tab_widget)
            scroll.setWidgetResizable(True)
            tab_widget.setLayout(tab_layout)
            
            # Tab hinzufügen mit STRING-Label
            self.tab_widget.addTab(scroll, tab_label)
    
    def _create_buttons_layout(self) -> QHBoxLayout:
        """Erstellt Button-Leiste (Punkt 4: Abdatum + Einstellungen + Speichern)"""
        buttons_layout = QHBoxLayout()
        
        # Label "Neues Abdatum"
        abdatum_label = QLabel("Neues Abdatum:")
        abdatum_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        buttons_layout.addWidget(abdatum_label)
        
        # Neues Abdatum Picker (ZENTRALE GCS-INSTANZ!)
        self.abdatum_picker = PdvmDateTimePicker(
            parent=self.main_widget,
            pdvm_datetime=self.gcs.neues_abdatum_inst,  # ← ZENTRALE INSTANZ!
            display="all",
            display_time_short=False,
            default_date=self.gcs.neues_abdatum_inst.PdvmDateTime
        )
        buttons_layout.addWidget(self.abdatum_picker)
        
        # Einstellungen-Button (nur im Admin-Modus)
        mode = self.gcs.field_value('mode')
        if mode == 'admin':
            self.settings_button = QPushButton("⚙️ Einstellungen")
            self.settings_button.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 5px 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            self.settings_button.clicked.connect(self._open_settings_dialog)
            buttons_layout.addWidget(self.settings_button)
        
        buttons_layout.addStretch()
        
        # Save-Button
        self.save_button = QPushButton("💾 Speichern")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.save_button.clicked.connect(self.save_all)  # Direkt zu save_all
        buttons_layout.addWidget(self.save_button)
        
        return buttons_layout
    
    def _render_all_controls(self):
        """Rendert ALLE Controls (LINEAR durch Liste)"""
        logger.info("🎨 Rendere alle Controls")
        
        for control in self.controls:
            control.render()
        
        logger.info("  ✅ Alle Controls gerendert")
    
    def save_all(self):
        """
        Speichert alle Controls (wie V2) - Feature 1: Abdatum-Persistenz
        
        ABLAUF:
        1. Neues Abdatum aus Picker speichern
        2. Dirty Controls sammeln
        3. Alle dirty Controls → save(neues_abdatum)
        4. Alle Instanzen committen
        5. Neues Abdatum in GCS speichern (PERSISTENZ!)
        6. Controls refreshen
        7. Bestätigung
        """
        logger.info("💾 === SAVE_ALL: Speichern GESTARTET ===")
        
        try:
            # [1] Neues Abdatum aus Picker speichern (ZENTRALE GCS-INSTANZ!)
            logger.info("  📅 SCHRITT 1: Neues Abdatum verarbeiten...")
            
            if self.abdatum_picker:
                self.abdatum_picker.save()  # Picker → self.gcs.neues_abdatum_inst
                logger.info(f"    🔹 Picker gespeichert: {self.gcs.neues_abdatum_inst.FormTimeStamp}")
            
            neues_abdatum = self.gcs.neues_abdatum_inst.PdvmDateTime
            logger.info(f"  🕒 Neues Abdatum: {neues_abdatum}")
            
            # [2] Dirty Controls sammeln
            # WICHTIG: c ist PdvmInputControlV4 (Container), c.input_type ist PdvmInputType* (mit is_dirty())
            dirty_controls = [c for c in self.controls if c.input_type and c.input_type.is_dirty()]
            
            if not dirty_controls:
                # AUCH WENN KEINE DATEN: Abdatum TROTZDEM persistent machen!
                logger.info("  💾 Keine Datenänderungen, aber Abdatum wird gespeichert...")
                try:
                    self.gcs.update_neues_abdatum()
                    logger.info(f"    ✅ Neues Abdatum gespeichert: {self.gcs.neues_abdatum_inst.FormTimeStamp}")
                except Exception as e:
                    logger.error(f"    ❌ Fehler beim Speichern in GCS: {e}")
                
                QMessageBox.information(
                    None,
                    "Keine Datenänderungen",
                    "Es wurden keine Datenänderungen vorgenommen.\n\n"
                    f"✅ Das Neue Abdatum wurde jedoch gesetzt:\n{self.gcs.neues_abdatum_inst.FormTimeStamp}"
                )
                logger.info("  ℹ️ Keine Datenänderungen, aber Abdatum persistent gespeichert")
                return
            
            logger.info(f"  📝 SCHRITT 2: {len(dirty_controls)} dirty Controls gefunden")
            
            # [3] Alle dirty Controls → save()
            logger.info("  💾 SCHRITT 3: Controls speichern...")
            changes = []
            for control in dirty_controls:
                success = control.save(neues_abdatum)
                
                if success and control.input_type:
                    changes.append({
                        'label': control.label_text,
                        'old': control.input_type.original_value,
                        'new': control.input_type.current_value
                    })
            
            logger.info(f"    ✅ {len(changes)} Controls gespeichert")
            
            # [4] ROOT-Instanz committen
            logger.info("  💾 SCHRITT 4: ROOT-Instanz committen...")
            if self.root_instance:
                self.root_instance.save_all_values()
            
            # [5] Neues Abdatum in GCS speichern (WIE update_stichtag()!)
            logger.info("  💾 SCHRITT 5: Neues Abdatum in GCS speichern...")
            try:
                self.gcs.update_neues_abdatum()
                logger.info(f"    ✅ Neues Abdatum gespeichert: {self.gcs.neues_abdatum_inst.FormTimeStamp}")
            except Exception as e:
                logger.error(f"    ❌ Fehler beim Speichern in GCS: {e}")
            
            # [6] Signal emittieren für kompletten Neuaufbau
            logger.info("  � SCHRITT 6: Signal 'save_completed' emittieren...")
            self.save_completed.emit()
            
            # [7] Bestätigung
            logger.info("  📋 SCHRITT 7: Bestätigung anzeigen...")
            QMessageBox.information(
                None,
                "Speichern erfolgreich",
                f"✅ {len(changes)} Änderungen wurden erfolgreich gespeichert."
            )
            
            logger.info("✅ === SAVE_ALL: Speichern ABGESCHLOSSEN ===")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.critical(
                None,
                "Fehler beim Speichern",
                f"❌ Fehler beim Speichern:\n\n{str(e)}"
            )
    
    def _open_settings_dialog(self):
        """Öffnet Einstellungen-Dialog (Feature 2) - TODO vollständige Implementation"""
        logger.info("⚙️ Einstellungen-Dialog öffnen...")
        
        try:
            # Projektion aus Controls erstellen
            current_projection = {}
            for control in self.controls:
                field_key = control.field_key if hasattr(control, 'field_key') else '?'
                current_projection[field_key] = {
                    'tab': control.tab if hasattr(control, 'tab') else 1,
                    'order': control.order if hasattr(control, 'order') else 0
                }
            
            logger.info(f"  📋 Aktuelle Projektion: {len(current_projection)} Einträge")
            
            # TODO: Vollständiger Settings-Dialog
            QMessageBox.information(
                None,
                "Einstellungen",
                f"⚙️ Einstellungen-Dialog (TODO)\n\n"
                f"Aktuell: {len(current_projection)} Controls\n"
                f"Tabs: {self.num_tabs}\n\n"
                "Hier können Sie später:\n"
                "• Controls zwischen Tabs verschieben\n"
                "• Reihenfolge der Controls ändern\n"
                "• Einstellungen persistieren"
            )
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Öffnen des Einstellungen-Dialogs: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _get_neues_abdatum(self) -> float:
        """
        Holt neues Abdatum aus GCS
        
        Returns:
            Float-Wert des neuen Abdatums
        """
        try:
            neues_abdatum, _ = self.gcs._db.get_value('EDIT', 'NEUES_ABDATUM')
            return float(neues_abdatum)
        except Exception as e:
            logger.error(f"❌ Fehler beim Holen des neuen Abdatums: {e}")
            return None
    
    def _on_save_clicked(self):
        """Handler für Save-Button"""
        # [1] Abdatum-Picker in GCS speichern
        self.abdatum_picker.save_datetime_to_gcs('EDIT', 'NEUES_ABDATUM')
        
        # [2] Alle Controls speichern
        success = self.save_all_controls()
        
        if success:
            QMessageBox.information(
                None,
                "Erfolgreich gespeichert",
                "Alle Änderungen wurden erfolgreich gespeichert!"
            )
        else:
            QMessageBox.warning(
                None,
                "Speichern fehlgeschlagen",
                "Beim Speichern ist ein Fehler aufgetreten!"
            )

