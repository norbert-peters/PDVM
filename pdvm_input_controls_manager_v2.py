"""
PDVM Input-Controls Manager V2 - AUTONOM & Matrix-basiert

🎯 VOLLSTÄNDIG AUTONOM VON VIEW!

EMPFÄNGT VOM DIALOG:
1. framedaten_db - Für ROOT_TABLE, HEADER_TEXT, METADATEN
2. selected_guid - Für welchen Datensatz editieren
3. Signal bei Stichtag-Wechsel (via GCS)

ARCHITEKTUR:
- Instanzen-Pool: DB-Instanzen (können von mehreren Controls genutzt werden)
- Controls-Matrix: Liste mit Controls + Metadata (Order, Tab, etc.)
- Command-Pattern: Durchläuft Matrix und sendet Kommandos an Controls

DESIGN-PRINZIPIEN:
1. Manager verwaltet ALLE Instanzen (Pool)
2. Manager verwaltet ALLE Controls (Matrix)
3. Commands werden LINEAR durch Matrix geschickt
4. Keine verschachtelten IFs, nur Schleifen + Kommandos
5. GCS-Integration: Stichtag + Neues Abdatum DIREKT aus GCS

ABLAUF:
1. INIT: Instanzen-Pool + Controls-Matrix aufbauen (aus METADATEN!)
2. RENDER: Alle Controls durchlaufen → render()
3. SAVE: Alle Controls durchlaufen → save(neues_abdatum) → save_all_values()
4. REFRESH: Alle Controls durchlaufen → refresh()

METADATEN-FORMAT (OPTION 3):
Gruppe: METADATEN in framedaten.db
  PERSONDATEN_PERSDATEN_ANREDE: {source_path: "root", label: "Anrede", type: "dropdown", ...}
  PERSONDATEN_PERSDATEN_FAMILIENNAME: {source_path: "root", label: "Familienname", ...}
  ...

AUTOR: Norbert Peters
DATUM: 22.10.2025 (korrigiert nach Benutzer-Feedback)
VERSION: 2.0 (Autonom, Metadaten-basiert)
"""

import logging
from typing import Dict, List, Optional
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QPushButton, QHBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal, QObject

from global_gcs import gcs
from pdvm_central_datenbank import PdvmCentralDatenbank
from pdvm_datetime import Pdvm_DateTime, PdvmDateTimeUtils
from pdvm_date_time_picker import PdvmDateTimePicker
from pdvm_input_control_v2 import PdvmInputControlV2, create_control_from_config
from PyQt5.QtWidgets import QLabel, QTabWidget

logger = logging.getLogger(__name__)


class PdvmInputControlsManagerV2(QObject):
    """
    Manager für Input-Controls mit Matrix-basierter Steuerung
    
    VERANTWORTLICHKEITEN:
    - Instanzen-Pool aufbauen und verwalten
    - Controls-Matrix aufbauen
    - Kommandos an alle Controls senden (RENDER/SAVE/REFRESH)
    - Neues Abdatum verwalten (aus GCS)
    - Widget mit allen Controls erstellen
    
    SIGNALS:
    - refresh_requested: Wird bei Bedarf emittiert (z.B. nach Stichtag-Änderung)
    """
    
    # Signal für Refresh-Request
    refresh_requested = pyqtSignal()
    
    def __init__(self, framedaten_db, selected_guid: str, frame_guid: str = None):
        """
        AUTONOM - Braucht NUR framedaten_db + selected_guid!
        
        Args:
            framedaten_db: PdvmCentralDatenbank Instanz für Framedaten
                          (enthält ROOT_TABLE, HEADER_TEXT, METADATEN)
            selected_guid: GUID des ausgewählten Datensatzes
            frame_guid: Optional - GUID des Frames für Persistierung (Default: aus framedaten_db)
        
        GCS-Zugriff:
        - Stichtag: gcs.st_inst.PdvmDateTime
        - Neues Abdatum: gcs._db.get_value('EDIT', 'NEUES_ABDATUM')
        """
        super().__init__()
        
        logger.info("🎯 === PDVM INPUT CONTROLS MANAGER V2 INITIALISIERUNG ===")
        
        self.framedaten_db = framedaten_db
        self.selected_guid = selected_guid
        
        # Frame-GUID für Persistierung (aus framedaten_db oder übergeben)
        if frame_guid:
            self.frame_guid = frame_guid
        else:
            try:
                self.frame_guid, _ = framedaten_db.get_value('ROOT', 'FRAME_GUID')
                if not self.frame_guid:
                    raise ValueError("FRAME_GUID nicht in Framedaten gefunden!")
            except Exception as e:
                logger.error(f"❌ Fehler beim Laden der FRAME_GUID: {e}")
                self.frame_guid = "DEFAULT_FRAME"  # Fallback
        
        # Instanzen-Pool (DB-Instanzen)
        self.instances: Dict[str, PdvmCentralDatenbank] = {}
        
        # Controls-Matrix (Liste mit Metadata)
        self.controls_matrix: List[dict] = []
        
        # Tab-Konfiguration (aus Framedaten)
        self.tab_config: Dict[int, str] = {}  # {1: "Tab 1", 2: "Tab 2", ...}
        self.num_tabs: int = 1
        
        # Neues Abdatum (aus GCS)
        self.neues_abdatum_dt: Optional[Pdvm_DateTime] = None
        self.abdatum_picker: Optional[PdvmDateTimePicker] = None
        
        # UI-Referenzen
        self.widget: Optional[QWidget] = None
        self.controls_container: Optional[QWidget] = None
        self.tab_widget: Optional[QTabWidget] = None  # Nur wenn mehrere Tabs
        
        logger.info(f"  📋 Selected GUID: {self.selected_guid}")
        logger.info("✅ Manager initialisiert (Instanzen + Controls werden bei get_widget() aufgebaut)")
    
    # =========================================================================
    # PUBLIC API
    # =========================================================================
    
    def get_widget(self) -> QWidget:
        """
        Erstellt Widget mit allen Controls
        
        ABLAUF:
        1. Framedaten + Metadaten laden
        2. Instanzen-Pool aufbauen
        3. Controls-Matrix aufbauen
        4. Neues Abdatum initialisieren
        5. UI erstellen
        6. RENDER-Kommando an alle Controls senden
        
        Returns:
            QWidget mit allen Controls
        """
        logger.info("🎨 === GET_WIDGET: Erstelle Input-Controls Widget ===")
        
        try:
            # [1] Framedaten + Metadaten laden
            header_text, root_table, controls_meta = self._load_framedaten_and_meta()
            
            # [2] Instanzen-Pool aufbauen
            self._build_instances_pool(root_table, controls_meta)
            
            # [3] Controls-Matrix aufbauen
            self._build_controls_matrix(controls_meta)
            
            # [4] Neues Abdatum initialisieren
            self._initialize_neues_abdatum()
            
            # [5] UI erstellen
            self.widget = self._create_ui(header_text)
            
            # [6] RENDER-Kommando an alle Controls
            self._render_all_controls()
            
            logger.info("✅ Input-Controls Widget erstellt")
            return self.widget
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des Widgets: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def save_all(self):
        """
        KOMMANDO: Alle Controls speichern
        
        ABLAUF:
        1. Neues Abdatum aus GCS holen
        2. Dirty Controls sammeln
        3. Alle dirty Controls durchlaufen → save(neues_abdatum)
        4. Alle Instanzen committen (save_all_values)
        5. Neues Abdatum in GCS speichern
        6. REFRESH-Kommando an alle Controls
        7. Bestätigungsfenster anzeigen
        """
        logger.info("💾 === SAVE_ALL: Speichern GESTARTET ===")
        
        try:
            # [1] Neues Abdatum aus GCS holen
            logger.info("  📅 SCHRITT 1: Neues Abdatum verarbeiten...")
            
            # Picker in Pdvm_DateTime speichern
            if self.abdatum_picker:
                self.abdatum_picker.save()
                logger.info(f"    🔹 Picker gespeichert: {self.neues_abdatum_dt.FormTimeStamp}")
            
            neues_abdatum = self.neues_abdatum_dt.PdvmDateTime
            logger.info(f"  🕒 Neues Abdatum: {neues_abdatum}")
            
            # [2] Dirty Controls sammeln
            dirty_controls = [
                item for item in self.controls_matrix 
                if item['control'].is_dirty
            ]
            
            if not dirty_controls:
                QMessageBox.information(
                    None,
                    "Keine Änderungen",
                    "Es wurden keine Änderungen vorgenommen."
                )
                logger.info("  ℹ️ Keine Änderungen zum Speichern")
                return
            
            logger.info(f"  📝 SCHRITT 2: {len(dirty_controls)} dirty Controls gefunden")
            
            # [3] Alle dirty Controls durchlaufen → save()
            logger.info("  💾 SCHRITT 3: Controls speichern...")
            changes = []
            for item in dirty_controls:
                control = item['control']
                success = control.save(neues_abdatum)
                
                if success:
                    changes.append({
                        'label': control.label_text,
                        'old': control.original_value,
                        'new': control.current_value
                    })
            
            logger.info(f"    ✅ {len(changes)} Controls gespeichert")
            
            # [4] Alle Instanzen committen
            logger.info("  💾 SCHRITT 4: Instanzen committen...")
            for instance_key, instance in self.instances.items():
                instance.save_all_values()
                logger.debug(f"    ✅ {instance_key}")
            
            # [5] Neues Abdatum in GCS speichern
            logger.info("  💾 SCHRITT 5: Neues Abdatum in GCS speichern...")
            try:
                gcs._db.set_value('EDIT', 'NEUES_ABDATUM', neues_abdatum)
                gcs._db.save_all_values()
                logger.info(f"    ✅ Neues Abdatum gespeichert: {neues_abdatum}")
            except Exception as e:
                logger.error(f"    ❌ Fehler beim Speichern in GCS: {e}")
            
            # [6] REFRESH-Kommando
            logger.info("  🔄 SCHRITT 6: Controls refreshen...")
            self.refresh_all()
            
            # [7] Bestätigungsfenster
            logger.info("  📋 SCHRITT 7: Bestätigung anzeigen...")
            self._show_save_confirmation(changes, neues_abdatum)
            
            logger.info("✅ === SAVE_ALL: Speichern ABGESCHLOSSEN ===")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.critical(
                None,
                "Fehler beim Speichern",
                f"Ein Fehler ist aufgetreten:\n\n{str(e)}"
            )
    
    def refresh_all(self):
        """
        KOMMANDO: Alle Controls refreshen
        
        ABLAUF:
        1. Neues Abdatum aus GCS neu laden
        2. Neues Abdatum Picker aktualisieren
        3. Alle Controls durchlaufen → refresh()
        """
        logger.info("🔄 === REFRESH_ALL: Controls aktualisieren ===")
        
        try:
            # [1] Neues Abdatum aus GCS neu laden
            logger.info("  📅 SCHRITT 1: Neues Abdatum aus GCS laden...")
            neues_abdatum_value = None
            try:
                neues_abdatum_value, _ = gcs._db.get_value('EDIT', 'NEUES_ABDATUM')
            except Exception as e:
                logger.warning(f"    ⚠️ Fehler beim GCS-Lesen: {e}")
            
            if neues_abdatum_value is not None:
                self.neues_abdatum_dt.PdvmDateTime = float(neues_abdatum_value)
                logger.info(f"    ✅ Geladen: {self.neues_abdatum_dt.FormTimeStamp}")
            else:
                # Fallback
                self.neues_abdatum_dt.PdvmDateTime = PdvmDateTimeUtils.PdvmDateTimeNow
                logger.warning(f"    ⚠️ Fallback: {self.neues_abdatum_dt.FormTimeStamp}")
            
            # [2] Picker aktualisiert sich AUTOMATISCH
            # (arbeitet direkt mit neues_abdatum_dt Instanz - kein load() nötig!)
            logger.info(f"  ✅ SCHRITT 2: Picker aktualisiert automatisch → {self.neues_abdatum_dt.FormTimeStamp}")
            
            # [3] Alle Controls durchlaufen → refresh()
            logger.info(f"  🔄 SCHRITT 3: {len(self.controls_matrix)} Controls refreshen...")
            for item in self.controls_matrix:
                item['control'].refresh()
            
            logger.info("✅ === REFRESH_ALL: Aktualisierung ABGESCHLOSSEN ===")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Refresh: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    # =========================================================================
    # INTERNE METHODEN (Private)
    # =========================================================================
    
    def _load_framedaten_and_meta(self):
        """
        Lädt Framedaten + Metadaten (OPTION 3)
        
        AUTONOM - Input-Controls sind vollständig unabhängig von View!
        
        Lädt:
        1. ROOT_TABLE aus framedaten.db ROOT.ROOT_TABLE
        2. HEADER_TEXT aus framedaten.db ROOT.HEADER_TEXT
        3. METADATEN aus framedaten.db Gruppe METADATEN
        
        Metadaten-Format (pro Control):
        {
            "PERSONDATEN_PERSDATEN_ANREDE": {
                "source_path": "root",
                "historical": true,
                "display_ti_ab_short": true,
                "label": "Anrede",
                "tooltip": "Anrede bitte auswählen",
                "type": "dropdown",
                "dropdown_config": {...},
                ...
            },
            ...
        }
        """
        logger.info("  📂 Lade Framedaten + Metadaten (OPTION 3)...")
        
        # === 1. ROOT_TABLE aus Framedaten ===
        try:
            root_table, _ = self.framedaten_db.get_value('ROOT', 'ROOT_TABLE')
        except:
            raise ValueError("ROOT_TABLE nicht in Framedaten gefunden!")
        
        # === 2. HEADER_TEXT aus Framedaten ===
        try:
            header_text, _ = self.framedaten_db.get_value('ROOT', 'HEADER_TEXT')
        except:
            header_text = "Input Controls"
        
        # === 2b. Tab-Konfiguration laden ===
        self._load_tab_config()
        
        # === 3. METADATEN aus Gruppe METADATEN ===
        try:
            metadaten = self.framedaten_db.get_gruppe('METADATEN')
        except:
            logger.warning("    ⚠️ Gruppe 'METADATEN' nicht gefunden!")
            metadaten = {}
        
        # === 4. Metadaten in Controls-Liste umwandeln ===
        controls_meta = []
        for field_key, field_config in metadaten.items():
            # Field-Key Format: TABELLE_GRUPPE_FELD
            # Beispiel: PERSONDATEN_PERSDATEN_ANREDE
            parts = field_key.split('_')
            if len(parts) < 3:
                logger.warning(f"    ⚠️ Ungültiger field_key: {field_key}")
                continue
            
            # Extrahiere Gruppe und Feld
            gruppe = parts[1].upper()
            feld = '_'.join(parts[2:]).upper()
            
            # Extrahiere Attribute aus field_config
            if isinstance(field_config, dict):
                label = field_config.get('label', feld.capitalize())
                source_path = field_config.get('source_path', 'root')
                # NEU: Tab und Order aus Metadaten
                tab = field_config.get('tab', 1)  # Default: Tab 1
                order = field_config.get('order', len(controls_meta))  # Default: Reihenfolge
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
        
        # === 5. Projektion laden (aus app_db oder Default) ===
        controls_meta = self._apply_projection(controls_meta)
        
        logger.info(f"    📋 Header: {header_text}")
        logger.info(f"    📋 ROOT-Table: {root_table}")
        logger.info(f"    📋 Tabs: {self.num_tabs} ({list(self.tab_config.values())})")
        logger.info(f"    ✅ {len(controls_meta)} Controls geladen + projiziert")
        
        return header_text, root_table, controls_meta
    
    def _load_tab_config(self):
        """
        Lädt Tab-Konfiguration aus Framedaten
        
        FRAMEDATEN-FELDER:
        - ROOT.EDIT_TABS: Anzahl der Tabs (Int)
        - ROOT.EDIT_TAB_LABEL_01: Label für Tab 1
        - ROOT.EDIT_TAB_LABEL_02: Label für Tab 2
        - ...
        
        Wenn EDIT_TABS = 1 oder nicht vorhanden → Nur 1 Tab (kein QTabWidget)
        Wenn EDIT_TABS > 1 → QTabWidget mit entsprechenden Tabs
        """
        logger.info("  📑 Lade Tab-Konfiguration...")
        
        try:
            edit_tabs, _ = self.framedaten_db.get_value('ROOT', 'EDIT_TABS')
            self.num_tabs = int(edit_tabs) if edit_tabs else 1
        except:
            self.num_tabs = 1
            logger.info("    ℹ️ EDIT_TABS nicht gefunden → Standard: 1 Tab")
        
        # Tab-Labels laden
        self.tab_config = {}
        for i in range(1, self.num_tabs + 1):
            field_name = f"EDIT_TAB_LABEL_{i:02d}"
            try:
                label, _ = self.framedaten_db.get_value('ROOT', field_name)
                self.tab_config[i] = label if label else f"Tab {i}"
            except:
                self.tab_config[i] = f"Tab {i}"
        
        logger.info(f"    ✅ {self.num_tabs} Tab(s) konfiguriert: {list(self.tab_config.values())}")
    
    def _apply_projection(self, controls_meta: list) -> list:
        """
        Wendet Projektion auf Controls an (Tab + Order)
        
        LOGIK:
        1. Persistente Projektion aus app_db laden (frame_guid.FRAME_PROJ)
        2. Falls vorhanden: Tab + Order aus Projektion überschreiben
        3. Falls nicht vorhanden: Default aus Metadaten verwenden
        4. Nach Tab + Order sortieren
        
        PROJEKTION-FORMAT (JSON):
        {
            "PERSONDATEN_PERSDATEN_ANREDE": {"tab": 1, "order": 1},
            "PERSONDATEN_PERSDATEN_FAMILIENNAME": {"tab": 1, "order": 2},
            "FINANZDATEN_FINANZDATEN_KONTOINHABER": {"tab": 2, "order": 1},
            ...
        }
        
        Returns:
            controls_meta mit aktualisierten tab + order Werten (sortiert)
        """
        logger.info("  🎯 Anwende Projektion (Tab + Order)...")
        
        # Projektion aus app_db laden
        projection_json, _ = gcs._app_db.get_value(self.frame_guid, 'FRAME_PROJ')
        
        if projection_json:
            try:
                import json
                projection = json.loads(projection_json)
                logger.info(f"    📋 Persistente Projektion geladen ({len(projection)} Einträge)")
                
                # Tab + Order aus Projektion überschreiben
                for meta in controls_meta:
                    field_key = meta['field_key']
                    if field_key in projection:
                        proj_data = projection[field_key]
                        meta['tab'] = proj_data.get('tab', meta['tab'])
                        meta['order'] = proj_data.get('order', meta['order'])
                        logger.debug(f"      🔹 {field_key}: Tab={meta['tab']}, Order={meta['order']}")
                
            except Exception as e:
                logger.warning(f"    ⚠️ Fehler beim Laden der Projektion: {e}")
                logger.info("    ℹ️ Verwende Default aus Metadaten")
        else:
            logger.info("    ℹ️ Keine persistente Projektion → Verwende Default aus Metadaten")
        
        # Nach Tab + Order sortieren
        controls_meta.sort(key=lambda x: (x['tab'], x['order']))
        
        logger.info(f"    ✅ Projektion angewendet + sortiert")
        return controls_meta
    
    def _build_instances_pool(self, root_table: str, controls_meta: list):
        """
        Baut Instanzen-Pool auf (inkl. verschachtelte Instanzen!)
        
        LOGIK:
        1. ROOT-Instanz mit selected_guid
        2. Für jedes Control mit source_path != 'root':
           - Parse source_path: "root_GRUPPE" oder "root_GRUPPE1_GRUPPE2_..."
           - Hole GUID aus vorheriger Instanz
           - Erstelle neue Instanz
        
        SOURCE_PATH-FORMAT:
        - "root" → ROOT-Instanz (persondaten mit selected_guid)
        - "root_PERSDATEN" → Suche in ROOT unter (PERSDATEN, {TABELLE}-{GRUPPE})
        - "root_PERSDATEN_WEITERE" → Mehrstufig (erst in ROOT, dann weiter)
        
        BEISPIEL:
        Field-Key: FINANZDATEN_FINANZDATEN_KONTOINHABER
        source_path: "root_PERSDATEN"
        
        → Suche in ROOT-Instanz:
           Gruppe: PERSDATEN
           Feld: FINANZDATEN-FINANZDATEN (erste 2 Teile von Field-Key mit -)
        → Ergebnis: GUID für Finanzdaten
        → Erstelle Instanz: FINANZDATEN_{guid}
        """
        logger.info("  🔧 Baue Instanzen-Pool...")
        
        # === 1. ROOT-Instanz ===
        root_instance = PdvmCentralDatenbank(root_table, self.selected_guid)
        root_key = f"{root_table.upper()}_{self.selected_guid}"
        self.instances[root_key] = root_instance
        self.instances['ROOT'] = root_instance  # Alias für einfachen Zugriff
        logger.info(f"    ✅ ROOT: {root_key}")
        
        # === 2. Verschachtelte Instanzen aus Controls sammeln ===
        for meta in controls_meta:
            source_path = meta.get('source_path', 'root')
            field_key = meta.get('field_key', '')
            
            # Root-Controls überspringen (bereits vorhanden)
            if source_path == 'root':
                continue
            
            # === Parse source_path ===
            # Format: "root_GRUPPE1_GRUPPE2_..."
            # Jeder Schritt (außer root) ist: TABELLE_GRUPPE
            path_parts = source_path.split('_')
            
            if path_parts[0] != 'root':
                logger.warning(f"    ⚠️ Ungültiger source_path (muss mit 'root' beginnen): {source_path}")
                continue
            
            # Nur ein Schritt nach root? (z.B. "root_PERSDATEN")
            if len(path_parts) < 2:
                logger.warning(f"    ⚠️ source_path zu kurz: {source_path}")
                continue
            
            # === Field-Key parsen für Tabelle + Gruppe ===
            # Format: TABELLE_GRUPPE_FELD (z.B. FINANZDATEN_FINANZDATEN_KONTOINHABER)
            field_parts = field_key.split('_')
            if len(field_parts) < 3:
                logger.warning(f"    ⚠️ Ungültiger field_key: {field_key}")
                continue
            
            target_table = field_parts[0].upper()  # FINANZDATEN
            target_gruppe = field_parts[1].upper()  # FINANZDATEN
            
            # === Instanz-Key berechnen ===
            # EINFACHE VERSION (nur ein Schritt): root_GRUPPE
            if len(path_parts) == 2:
                # Pfad: root_PERSDATEN
                lookup_gruppe = path_parts[1].upper()  # PERSDATEN
                
                # Feld-Schlüssel: TABELLE-GRUPPE (z.B. FINANZDATEN-FINANZDATEN)
                lookup_feld = f"{target_table}-{target_gruppe}"
                
                # === GUID aus ROOT-Instanz holen (STICHTAGGENAU!) ===
                try:
                    # KRITISCH: Verwende GCS-Stichtag für Auflösung
                    stichtag = gcs.st_inst.PdvmDateTime
                    
                    # DEBUG: Zeige Lookup-Details
                    logger.debug(f"    🔍 Suche GUID: {lookup_gruppe}.{lookup_feld} (Stichtag: {stichtag})")
                    
                    result = root_instance.get_value(lookup_gruppe, lookup_feld, stichtag)
                    
                    if isinstance(result, tuple):
                        guid, abdatum = result
                        logger.debug(f"       → GUID gefunden: {guid} (Abdatum: {abdatum})")
                    else:
                        guid = result
                        logger.debug(f"       → GUID gefunden: {guid}")
                    
                    if not guid or guid == "":
                        logger.warning(f"    ⚠️ Keine GUID gefunden: {lookup_gruppe}.{lookup_feld} (Stichtag: {stichtag})")
                        logger.warning(f"       → Control '{field_key}' wird OHNE Instanz erstellt (read-only)")
                        # NICHT continue! Control wird trotzdem erstellt, aber ohne Instanz
                        # → Control wird in _build_controls_matrix automatisch read-only
                    else:
                        # === Instanz erstellen ===
                        instance_key = f"{target_table}_{guid}"
                        
                        # Prüfe ob bereits vorhanden
                        if instance_key in self.instances:
                            logger.debug(f"    ♻️ Instanz bereits vorhanden: {instance_key}")
                            continue
                        
                        # Neue Instanz erstellen
                        new_instance = PdvmCentralDatenbank(target_table, guid)
                        self.instances[instance_key] = new_instance
                        logger.info(f"    ✅ Verschachtelt: {instance_key} (aus {lookup_gruppe}.{lookup_feld})")
                    
                except Exception as e:
                    logger.error(f"    ❌ Fehler beim Erstellen von Instanz für {field_key}: {e}")
                    continue
            else:
                # MEHRSTUFIGE PFADE (später implementieren)
                logger.warning(f"    ⚠️ Mehrstufige Pfade noch nicht unterstützt: {source_path}")
                continue
        
        logger.info(f"  ✅ Instanzen-Pool aufgebaut: {len(self.instances)} Instanzen")
    
    def _build_controls_matrix(self, controls_meta: list):
        """
        Baut Controls-Matrix auf mit korrekter Instanz-Zuordnung
        
        LOGIK:
        Für jedes Control:
        1. Ermittle Ziel-Tabelle aus field_key (erste Komponente)
        2. Suche passende Instanz im Pool (nach Tabellen-Name)
        3. Falls nicht gefunden: Verwende ROOT (schreibgeschützt)
        """
        logger.info("  🔧 Baue Controls-Matrix...")
        
        for meta in controls_meta:
            field_key = meta.get('field_key', '')
            source_path = meta.get('source_path', 'root')
            
            # === Ziel-Tabelle aus field_key ermitteln ===
            # Format: TABELLE_GRUPPE_FELD
            field_parts = field_key.split('_')
            if len(field_parts) < 3:
                logger.warning(f"    ⚠️ Ungültiger field_key: {field_key}")
                continue
            
            target_table = field_parts[0].upper()
            
            # === Instanz finden ===
            db_instance = None
            instance_key = None
            
            # Suche passende Instanz (nach Tabellen-Präfix)
            for key, instance in self.instances.items():
                if key.startswith(f"{target_table}_") or key == 'ROOT':
                    # Prüfe ob Tabellen-Name passt
                    if key == 'ROOT' and source_path == 'root':
                        instance_key = key
                        db_instance = instance
                        break
                    elif key.startswith(f"{target_table}_"):
                        instance_key = key
                        db_instance = instance
                        break
            
            # Fallback: ROOT-Instanz (schreibgeschützt)
            if not db_instance:
                logger.warning(f"    ⚠️ Keine Instanz gefunden für {field_key}, verwende ROOT")
                instance_key = 'ROOT'
                db_instance = self.instances.get('ROOT')
            else:
                logger.debug(f"    ✅ Instanz zugeordnet: {field_key} → {instance_key}")
            
            # === Control erstellen ===
            control = create_control_from_config(
                instance_key=instance_key,
                db_instance=db_instance,
                config=meta,
                parent=None  # Parent wird später gesetzt
            )
            
            # In Matrix einfügen (mit field_key für Projektion!)
            self.controls_matrix.append({
                'control': control,
                'field_key': field_key,  # WICHTIG für Projektion!
                'order': meta.get('order', 0),
                'tab': meta.get('tab', 1),
                'instance_key': instance_key
            })
        
        # Matrix nach Order sortieren
        self.controls_matrix.sort(key=lambda x: x['order'])
        
        logger.info(f"  ✅ Controls-Matrix aufgebaut: {len(self.controls_matrix)} Controls (sortiert)")
    
    def _initialize_neues_abdatum(self):
        """Initialisiert Neues Abdatum aus GCS"""
        logger.info("  📅 === NEUES ABDATUM INITIALISIERUNG ===")
        
        # Pdvm_DateTime Instanz erstellen
        self.neues_abdatum_dt = Pdvm_DateTime(gcs.field_value('country'))
        logger.info("    🔹 SCHRITT 1: Pdvm_DateTime Instanz erstellt")
        
        # GCS lesen
        neues_abdatum_value = None
        try:
            neues_abdatum_value, _ = gcs._db.get_value('EDIT', 'NEUES_ABDATUM')
        except Exception as e:
            logger.warning(f"    ⚠️ Fehler beim GCS-Lesen: {e}")
        
        if neues_abdatum_value is not None:
            # GCS-Wert vorhanden
            self.neues_abdatum_dt.PdvmDateTime = float(neues_abdatum_value)
            logger.info(f"    ✅ SCHRITT 2: Aus GCS geladen: {self.neues_abdatum_dt.FormTimeStamp}")
        else:
            # Fallback + SOFORT speichern!
            self.neues_abdatum_dt.PdvmDateTime = PdvmDateTimeUtils.PdvmDateTimeNow
            logger.info(f"    ℹ️ SCHRITT 2a: Fallback: {self.neues_abdatum_dt.FormTimeStamp}")
            
            try:
                gcs._db.set_value('EDIT', 'NEUES_ABDATUM', self.neues_abdatum_dt.PdvmDateTime)
                gcs._db.save_all_values()
                logger.info(f"    💾 SCHRITT 2b: Fallback in GCS gespeichert")
            except Exception as e:
                logger.error(f"    ❌ Fehler beim Speichern: {e}")
        
        logger.info("  ✅ Neues Abdatum Initialisierung abgeschlossen")
    
    def _create_ui(self, header_text: str) -> QWidget:
        """Erstellt UI mit Header + Tabs/ScrollArea für Controls + Admin-Button"""
        logger.info("  🎨 Erstelle UI...")
        
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # === HEADER mit Neues Abdatum Picker + Einstellungen-Button (nur im Admin-Modus) ===
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Label "Neues Abdatum"
        abdatum_label = QLabel("Neues Abdatum:")
        abdatum_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        header_layout.addWidget(abdatum_label)
        
        # Neues Abdatum Picker
        self.abdatum_picker = PdvmDateTimePicker(
            parent=header_container,
            pdvm_datetime=self.neues_abdatum_dt,
            display="all",
            display_time_short=False,
            default_date=self.neues_abdatum_dt.PdvmDateTime
        )
        header_layout.addWidget(self.abdatum_picker)
        
        # Einstellungen-Button (nur im Admin-Modus)
        mode = gcs.field_value('mode')
        if mode == 'admin':
            settings_button = QPushButton("⚙️ Einstellungen")
            settings_button.setStyleSheet("""
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
            settings_button.clicked.connect(self._open_settings_dialog)
            header_layout.addWidget(settings_button)
        
        header_layout.addStretch()
        
        main_layout.addWidget(header_container)
        
        # === TABS oder SINGLE SCROLLAREA ===
        if self.num_tabs > 1:
            # Mehrere Tabs → QTabWidget
            self.tab_widget = QTabWidget()
            
            # Tabs erstellen
            for tab_num in range(1, self.num_tabs + 1):
                tab_label = self.tab_config.get(tab_num, f"Tab {tab_num}")
                
                # ScrollArea für diesen Tab
                scroll = QScrollArea()
                scroll.setWidgetResizable(True)
                scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                
                # Container für Controls
                tab_container = QWidget()
                tab_layout = QVBoxLayout(tab_container)
                tab_layout.setContentsMargins(0, 0, 0, 0)
                tab_layout.setSpacing(5)
                
                scroll.setWidget(tab_container)
                self.tab_widget.addTab(scroll, tab_label)
            
            main_layout.addWidget(self.tab_widget)
            
            logger.info(f"    ✅ QTabWidget mit {self.num_tabs} Tabs erstellt")
        else:
            # Nur 1 Tab → Einzelne ScrollArea
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            self.controls_container = QWidget()
            controls_layout = QVBoxLayout(self.controls_container)
            controls_layout.setContentsMargins(0, 0, 0, 0)
            controls_layout.setSpacing(5)
            
            scroll.setWidget(self.controls_container)
            main_layout.addWidget(scroll)
            
            logger.info("    ✅ Einzelne ScrollArea erstellt (1 Tab)")
        
        # === BUTTONS ===
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        save_button = QPushButton("💾 Speichern")
        save_button.clicked.connect(self.save_all)
        buttons_layout.addWidget(save_button)
        
        buttons_layout.addStretch()
        
        main_layout.addWidget(buttons_container)
        
        logger.info("  ✅ UI erstellt")
        return widget
    
    def _render_all_controls(self):
        """
        RENDER-Kommando an alle Controls + Platzierung in Tabs
        
        LOGIK:
        - Bei num_tabs > 1: Controls nach Tab-Nummer in entsprechende Tabs platzieren
        - Bei num_tabs == 1: Alle Controls in controls_container platzieren
        """
        logger.info(f"  🎨 RENDER: {len(self.controls_matrix)} Controls...")
        
        if self.num_tabs > 1:
            # Mehrere Tabs: Controls nach Tab-Nummer verteilen
            for item in self.controls_matrix:
                control = item['control']
                tab_num = item.get('tab', 1)  # Default: Tab 1
                
                # Tab-Index berechnen (1-basiert → 0-basiert)
                tab_index = tab_num - 1
                
                # Tab-Container holen
                if 0 <= tab_index < self.tab_widget.count():
                    scroll_widget = self.tab_widget.widget(tab_index)
                    tab_container = scroll_widget.widget()
                    
                    # Parent setzen
                    control.setParent(tab_container)
                    
                    # RENDER-Kommando
                    control.render()
                    
                    # Zu Tab-Layout hinzufügen
                    tab_container.layout().addWidget(control)
                    
                    logger.debug(f"    🔹 Control '{item.get('instance_key', '?')}' → Tab {tab_num}")
                else:
                    logger.warning(f"    ⚠️ Ungültiger Tab-Index {tab_index} für Control")
            
            # Stretch am Ende JEDES Tabs
            for tab_index in range(self.tab_widget.count()):
                scroll_widget = self.tab_widget.widget(tab_index)
                tab_container = scroll_widget.widget()
                tab_container.layout().addStretch()
                
        else:
            # Nur 1 Tab: Alle Controls in controls_container
            for item in self.controls_matrix:
                control = item['control']
                
                # Parent setzen
                control.setParent(self.controls_container)
                
                # RENDER-Kommando
                control.render()
                
                # Zu Layout hinzufügen
                self.controls_container.layout().addWidget(control)
            
            # Stretch am Ende
            self.controls_container.layout().addStretch()
        
        logger.info(f"  ✅ {len(self.controls_matrix)} Controls gerendert")
    
    def _open_settings_dialog(self):
        """
        Öffnet Einstellungen-Dialog für Tab + Order Anpassung (nur Admin-Modus!)
        
        ABLAUF:
        1. Aktuelle Projektion aus controls_matrix erstellen
        2. Dialog öffnen (modal - blockiert bis geschlossen)
        3. Geänderte Projektion aus Dialog holen
        4. In app_db persistieren (frame_guid.FRAME_PROJ)
        5. Widget neu aufbauen (get_widget())
        """
        logger.info("⚙️ === EINSTELLUNGEN-DIALOG ÖFFNEN ===")
        
        try:
            # Projektion aus aktueller Matrix erstellen
            current_projection = {}
            for item in self.controls_matrix:
                field_key = item.get('field_key', '?')
                current_projection[field_key] = {
                    'tab': item.get('tab', 1),
                    'order': item.get('order', 0)
                }
            
            logger.info(f"  📋 Aktuelle Projektion: {len(current_projection)} Einträge")
            
            # TODO: Dialog öffnen
            # from pdvm_input_controls_settings_dialog import PdvmInputControlsSettingsDialog
            # dialog = PdvmInputControlsSettingsDialog(current_projection, self.tab_config)
            # result = dialog.exec_()
            # 
            # if result == QDialog.Accepted:
            #     new_projection = dialog.get_projection()
            #     self._save_projection(new_projection)
            #     self._rebuild_ui()
            
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
    
    def _save_projection(self, projection: dict):
        """
        Speichert Projektion in app_db
        
        Args:
            projection: Dict mit {field_key: {"tab": int, "order": int}}
        """
        logger.info("💾 Speichere Projektion in app_db...")
        
        import json
        projection_json = json.dumps(projection)
        
        gcs._app_db.set_value(self.frame_guid, 'FRAME_PROJ', projection_json)
        gcs._app_db.save_all_values()
        
        logger.info(f"  ✅ Projektion gespeichert ({len(projection)} Einträge)")
    
    def _show_save_confirmation(self, changes: list, neues_abdatum: float):
        """Zeigt Bestätigungsfenster nach erfolgreichem Speichern"""
        message = f"✅ {len(changes)} Feld(er) erfolgreich gespeichert!\n\n"
        message += f"🕒 Abdatum: {self.neues_abdatum_dt.FormTimeStamp}\n\n"
        message += "Geänderte Felder:\n"
        
        for change in changes[:10]:  # Max 10 anzeigen
            old_val = str(change['old'])[:20] if change['old'] else "(leer)"
            new_val = str(change['new'])[:20] if change['new'] else "(leer)"
            message += f"  • {change['label']}: {old_val} → {new_val}\n"
        
        if len(changes) > 10:
            message += f"  ... und {len(changes) - 10} weitere Feld(er)"
        
        QMessageBox.information(
            None,
            "Erfolgreich gespeichert",
            message
        )
