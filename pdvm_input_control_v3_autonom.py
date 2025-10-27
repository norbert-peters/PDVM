"""
PDVM Input-Control V3 - VOLLSTÄNDIG AUTONOM

ARCHITEKTUR-PRINZIP:
- Jedes Control ist VOLLSTÄNDIG autonom
- Control beschafft sich SELBST seine Instanz
- Keine zentrale Instanzen-Verwaltung mehr
- Einfache, lineare Logik

AUTONOME INSTANZ-BESCHAFFUNG:
1. source_path = "root" → Direkt root_instance verwenden
2. source_path verschachtelt:
   - GUID aus ROOT holen (stichtaggenau!)
   - Keine GUID → Control wird read_only
   - GUID vorhanden → Instanz aus Cache oder neu erstellen

INSTANZ-CACHE:
- Klassen-Variable für alle Controls
- Cache-Key: (tabelle, guid)
- Verhindert doppelte Instanzen

READ-ONLY LOGIK:
1. Keine zugeordnete Instanz → IMMER read_only
2. Explizites read_only=True aus Metadaten → read_only
3. Sonst → editierbar

AUTOR: Norbert Peters
DATUM: 22.10.2025
VERSION: 3.0 (Autonome Instanz-Beschaffung)
"""

import logging
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt5.QtCore import Qt

from global_gcs import gcs
from pdvm_datetime import Pdvm_DateTime
from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)


class PdvmInputControlV3(QWidget):
    """
    VOLLSTÄNDIG AUTONOMES Input-Control
    
    VERANTWORTLICHKEITEN:
    - Instanz SELBST beschaffen (aus ROOT oder verschachtelt)
    - Wert laden (mit GCS-Stichtag)
    - Wert anzeigen (mit Abdatum-Tooltip)
    - Änderungen tracken
    - Wert speichern (mit neuem Abdatum)
    
    ABHÄNGIGKEITEN:
    - root_instance: Nur ROOT-Instanz vom Manager
    - GCS: Stichtag + Neues Abdatum
    """
    
    # KLASSEN-CACHE für Instanzen (shared zwischen allen Controls)
    _instance_cache = {}  # {(tabelle, guid): instance}
    
    def __init__(self,
                 root_instance,
                 meta: dict,
                 manager=None,
                 parent=None):
        """
        Args:
            root_instance: ROOT-Instanz (vom Manager)
            meta: Metadaten-Dict mit allen Informationen
            manager: Referenz zum Manager (für Refresh nach Historie-Speichern)
            parent: Parent-Widget
        """
        super().__init__(parent)
        
        # ROOT-INSTANZ (vom Manager)
        self.root_instance = root_instance
        
        # MANAGER-REFERENZ (für Refresh)
        self.manager = manager
        
        # METADATEN
        self.field_key = meta.get('field_key', '')
        self.source_path = meta.get('source_path', 'root')
        self.label_text = meta.get('label', '')
        self.order = meta.get('order', 0)
        self.tab = meta.get('tab', 'default')
        
        # FIELD_CONFIG auswerten (wie V2) - Fix für Punkt 1 & 2
        field_config = meta.get('field_config', {})
        if isinstance(field_config, dict):
            self.meta_tooltip = field_config.get('tooltip', None)  # Punkt 1: Tooltip aus field_config
            self.read_only_meta = field_config.get('read_only', False)  # Punkt 2: read_only aus field_config
            self.historical = field_config.get('historical', False)  # Punkt 3: historical für History-Button
            self.help_config = field_config.get('help_config', None)  # NEU: Hilfe-Konfiguration
            self.control_type = field_config.get('type', 'text')  # NEU: Control-Type (default: text)
            self.display_val = field_config.get('display_val', None)  # NEU: Display-Format für Datum
            self.show_abdatum = field_config.get('abdatum', True)  # NEU: Abdatum anzeigen? (default: True)
            self.dropdown_config = field_config.get('dropdown_config', None)  # NEU: Dropdown-Konfiguration
        else:
            self.meta_tooltip = None
            self.read_only_meta = False
            self.historical = False
            self.help_config = None
            self.control_type = 'text'
            self.display_val = None
            self.show_abdatum = True
            self.dropdown_config = None
        
        # HILFE-INSTANZ (wird lazy erstellt wenn help_config vorhanden)
        self.help_instance = None
        
        # FIELD_KEY parsen (TABELLE_GRUPPE_FELD)
        field_parts = self.field_key.split('_')
        if len(field_parts) >= 3:
            self.tabelle = field_parts[0].upper()
            self.gruppe = field_parts[1].upper()
            self.feld = '_'.join(field_parts[2:]).upper()  # Rest ist Feldname
        else:
            logger.error(f"❌ Ungültiger field_key: {self.field_key}")
            self.tabelle = ""
            self.gruppe = ""
            self.feld = ""
        
        # ZUGEORDNETE INSTANZ (wird bei _resolve_instance() gesetzt)
        self.zugeordnete_instanz = None
        self.zugeordnete_guid = None
        
        # READ-ONLY FLAG (wird bei _resolve_instance() gesetzt)
        self.read_only = False
        
        # ABDATUM-INSTANZ (nur für Anzeige)
        self.abdatum_dt = Pdvm_DateTime(gcs.field_value('country'))
        
        # WERT-INSTANZ für type=datetime
        self.value_dt = None  # Pdvm_DateTime Instanz für Datum-Werte
        
        # DROPDOWN-INSTANZ für type=dropdown
        self.dropdown_instance = None  # PdvmCentralDatenbank für Dropdown-Daten
        self.dropdown_items = {}  # {display_value: stored_key}
        
        # DATEN
        self.wert = None
        self.abdatum_wert = None
        self.original_value = None
        self.current_value = None
        self.is_dirty = False
        
        # UI-WIDGETS
        self.label_widget = None
        self.value_label = None
        self.edit_widget = None  # QLineEdit für type=text
        self.date_picker = None  # PdvmDateTimePicker für type=datetime
        self.combo_box = None  # QComboBox für type=dropdown
        self.history_button = None
        self.help_button = None  # NEU: Hilfe-Button
        
        logger.debug(f"  📦 Control erstellt: {self.label_text} (source_path: {self.source_path})")
    
    # =========================================================================
    # KOMMANDO: RENDER
    # =========================================================================
    
    def render(self):
        """
        KOMMANDO: Erstmaliges Laden + UI erstellen
        
        ABLAUF (AUTONOM!):
        1. Instanz beschaffen (_resolve_instance)
        2. Dropdown-Instanz initialisieren (_init_dropdown_instance) - falls type=dropdown
        3. Wert laden (_load_value_from_db)
        4. UI erstellen (_create_ui)
        5. UI aktualisieren (_update_ui)
        """
        logger.debug(f"  🎨 RENDER: {self.label_text}")
        
        # [1] INSTANZ BESCHAFFEN (AUTONOM!)
        self._resolve_instance()
        
        # [2] DROPDOWN-INSTANZ (falls type=dropdown)
        if self.control_type == 'dropdown':
            self._init_dropdown_instance()
        
        # [3] WERT LADEN
        self._load_value_from_db()
        
        # [4] UI ERSTELLEN
        self._create_ui()
        
        # [5] UI AKTUALISIEREN
        self._update_ui()
    
    # =========================================================================
    # KOMMANDO: SAVE
    # =========================================================================
    
    def save(self, neues_abdatum: float) -> bool:
        """
        KOMMANDO: Wert speichern (wenn dirty)
        
        Args:
            neues_abdatum: Neues Abdatum (Float aus GCS)
        
        Returns:
            True wenn gespeichert, False sonst
        """
        # [1] DateTime-Controls: Picker nach Dirty-Status fragen
        if self.control_type == 'datetime' and self.date_picker:
            # 🔹 LINEARE LOGIK: Picker weiß selbst, ob er dirty ist!
            if self.date_picker.is_dirty():
                # Picker committen: self.initial → self.value_dt
                self.date_picker.save()
                
                # Current-Value aus value_dt aktualisieren
                self.current_value = self.value_dt.PdvmDateTime
                
                # Input Control als dirty markieren
                self.is_dirty = True
                
                logger.info(f"  🔍 DateTime Dirty erkannt: {self.label_text}")
                logger.info(f"      Neu: {self.current_value}")
        
        # [2] Nicht dirty? Skip!
        if not self.is_dirty:
            logger.debug(f"  ⏭️  SAVE (skipped): {self.label_text} - nicht dirty")
            return False
        
        # [3] Keine Instanz? Fehler!
        if not self.zugeordnete_instanz:
            logger.warning(f"  ⚠️ SAVE (failed): {self.label_text} - keine Instanz")
            return False
        
        try:
            # [4] Abdatum bestimmen: 
            #     - show_abdatum=False → gelesenes Abdatum verwenden (Geburtsdatum-Fall)
            #     - show_abdatum=True → neues Abdatum verwenden (normale Historie)
            if not self.show_abdatum and self.abdatum_wert:
                # AUSNAHME: Wert auf bestehendem Abdatum überschreiben (meist 1001.0)
                save_abdatum = self.abdatum_wert
                logger.info(f"  💾 SAVE (ohne neue Historie): {self.label_text}")
                logger.info(f"      Alt: {self.original_value} → Neu: {self.current_value}")
                logger.info(f"      Abdatum (wiederverwendet): {save_abdatum}")
            else:
                # NORMAL: Neues Abdatum → neue Historie
                save_abdatum = neues_abdatum
                logger.debug(f"  💾 SAVE: {self.label_text} = {self.current_value} (neues Abdatum: {save_abdatum})")
            
            # Wert speichern
            self.zugeordnete_instanz.set_value(
                self.gruppe,
                self.feld,
                self.current_value,
                save_abdatum
            )
            
            # Original-Wert aktualisieren
            self.original_value = self.current_value
            self.is_dirty = False
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ SAVE (error): {self.label_text} - {e}")
            return False
    
    # =========================================================================
    # KOMMANDO: REFRESH
    # =========================================================================
    
    def refresh(self):
        """
        KOMMANDO: Neu laden nach Stichtag-Wechsel
        
        ABLAUF (AUTONOM!):
        1. Instanz NEU auflösen (GUID könnte sich geändert haben!)
        2. Wert NEU laden (mit neuem Stichtag aus GCS)
        3. UI aktualisieren
        
        WICHTIG: Instanz-Cache wird NICHT geleert, da Instanzen
                 alle historischen Daten enthalten!
        """
        logger.debug(f"  🔄 REFRESH: {self.label_text}")
        
        # [1] INSTANZ NEU AUFLÖSEN (GUID könnte sich geändert haben!)
        #     Bei verschachtelten Controls: GUID wird mit neuem Stichtag abgefragt
        self._resolve_instance()
        
        # [2] WERT NEU LADEN (mit neuem Stichtag aus GCS!)
        #     Instanz enthält alle historischen Daten
        self._load_value_from_db()
        
        # [3] ZUSTAND ZURÜCKSETZEN
        self.is_dirty = False
        
        # [4] UI AKTUALISIEREN (inkl. Read-Only Status!)
        self._update_ui()
    
    # =========================================================================
    # AUTONOME INSTANZ-BESCHAFFUNG (KERNELEMENT!)
    # =========================================================================
    
    def _resolve_instance(self):
        """
        AUTONOM: Beschafft zugeordnete Instanz
        
        ABLAUF:
        1. source_path = "root" → root_instance verwenden
        2. source_path verschachtelt:
           - Source-Gruppe ermitteln (aus source_path)
           - Zuordnungsfeld ermitteln (TABELLE-GRUPPE aus field_key)
           - GUID aus ROOT holen (STICHTAGGENAU!)
           - Keine GUID → self.read_only = True
           - GUID vorhanden → Instanz aus Cache oder neu erstellen
        """
        # [FALL 1] ROOT-Control
        if self.source_path == 'root':
            logger.debug(f"    ✅ ROOT-Control: {self.label_text}")
            self.zugeordnete_instanz = self.root_instance
            self.zugeordnete_guid = self.root_instance.guid
            
            # Read-Only nur aus Meta
            self.read_only = self.read_only_meta
            return
        
        # [FALL 2] Verschachteltes Control
        logger.debug(f"    🔍 Verschachteltes Control: {self.label_text}")
        
        # [2.1] Source-Gruppe ermitteln (aus source_path)
        # Beispiel: "root_PERSDATEN" → "PERSDATEN"
        if '_' in self.source_path:
            source_gruppe = self.source_path.split('_')[1].upper()
        else:
            logger.error(f"    ❌ Ungültiger source_path: {self.source_path}")
            self.zugeordnete_instanz = None
            self.read_only = True
            return
        
        # [2.2] Zuordnungsfeld ermitteln (TABELLE-GRUPPE)
        # Beispiel: field_key = "FINANZDATEN_FINANZDATEN_KONTOINHABER"
        #          → zuordnungsfeld = "FINANZDATEN-FINANZDATEN"
        zuordnungsfeld = f"{self.tabelle}-{self.gruppe}"
        
        logger.debug(f"    🔍 Suche GUID: source_gruppe={source_gruppe}, zuordnungsfeld={zuordnungsfeld}")
        
        # [2.3] GUID aus ROOT holen (STICHTAGGENAU!)
        stichtag = gcs.st_inst.PdvmDateTime
        
        try:
            result = self.root_instance.get_value(source_gruppe, zuordnungsfeld, stichtag)
            
            # get_value kann (wert, abdatum) oder nur wert zurückgeben
            if isinstance(result, tuple):
                guid, guid_abdatum = result
            else:
                guid = result
                guid_abdatum = None
            
            logger.debug(f"    📋 GUID-Result: guid={guid}, abdatum={guid_abdatum}")
            
        except Exception as e:
            logger.error(f"    ❌ Fehler beim GUID-Abruf: {e}")
            guid = None
        
        # [2.4] GUID prüfen
        if not guid or guid == "":
            # KEINE GUID → READ-ONLY
            logger.warning(f"    ⚠️ Keine GUID gefunden für {self.label_text} → Read-Only")
            self.zugeordnete_instanz = None
            self.zugeordnete_guid = None
            self.read_only = True
            return
        
        # [2.5] GUID vorhanden → Instanz aus Cache oder neu erstellen
        logger.debug(f"    ✅ GUID gefunden: {guid}")
        self.zugeordnete_guid = guid
        self.zugeordnete_instanz = self._get_or_create_instance(self.tabelle, guid)
        
        # Read-Only nur aus Meta (Instanz ist vorhanden!)
        self.read_only = self.read_only_meta
    
    def _get_or_create_instance(self, tabelle: str, guid: str):
        """
        Holt Instanz aus Cache oder erstellt neue
        
        Args:
            tabelle: Tabellenname (z.B. "FINANZDATEN")
            guid: GUID (z.B. "74352176-bd00-...")
        
        Returns:
            PdvmCentralDatenbank Instanz
        """
        cache_key = (tabelle.upper(), guid)
        
        if cache_key in self._instance_cache:
            logger.debug(f"    ♻️ Instanz aus Cache: {tabelle}_{guid[:8]}...")
            return self._instance_cache[cache_key]
        
        # Neue Instanz erstellen
        logger.debug(f"    ✨ Neue Instanz: {tabelle}_{guid[:8]}...")
        instance = PdvmCentralDatenbank(tabelle, guid)
        self._instance_cache[cache_key] = instance
        
        return instance
    
    def _init_dropdown_instance(self):
        """
        🔹 DROPDOWN: Initialisiert Dropdown-Instanz und lädt ALLE Items
        
        STRUKTUR in DB (JSON):
        {
          "anrede": {
            "de-de": {"": "", "m": "Herr", "w": "Frau", "d": "Herr oder Frau"},
            "us-en": {"": "", "m": "Mr", "w": "Ms", "d": "Mr or Ms"}
          }
        }
        
        ABLAUF:
        1. dropdown_config auslesen (table, key, value)
        2. Instanz aus Cache holen oder neu erstellen
        3. Language aus GCS holen (z.B. "DEU" → "de-de")
        4. JSON aus Instanz laden: get_static_value(gruppe=value, feld=language)
        5. JSON parsen und alle Key→Display-Text Paare extrahieren
        """
        if not self.dropdown_config:
            logger.error(f"    ❌ DROPDOWN: Keine dropdown_config für {self.label_text}")
            return
        
        # [1] Config auslesen
        table = self.dropdown_config.get('table', '')
        key = self.dropdown_config.get('key', '')  # GUID der Dropdown-Tabelle
        value = self.dropdown_config.get('value', '')  # Gruppe (z.B. "anrede")
        
        if not table or not key or not value:
            logger.error(f"    ❌ DROPDOWN: Unvollständige Config für {self.label_text}")
            return
        
        logger.debug(f"    🔽 DROPDOWN-Init: table={table}, key={key}, value={value}")
        
        # [2] Instanz aus Cache oder neu erstellen
        cache_key = (table.upper(), key)
        
        if cache_key in self._instance_cache:
            logger.debug(f"    ♻️ Dropdown-Instanz aus Cache: {table}_{key[:8]}...")
            self.dropdown_instance = self._instance_cache[cache_key]
        else:
            logger.debug(f"    ✨ Neue Dropdown-Instanz: {table}_{key[:8]}...")
            self.dropdown_instance = PdvmCentralDatenbank(table, key)
            self._instance_cache[cache_key] = self.dropdown_instance
        
        # [3] Language aus GCS holen (DIREKT aus _u_db, keine Konvertierung!)
        try:
            language = gcs._u_db.get_static_value(gcs.user_guid, 'language')
            if not language:
                language = 'de-de'  # Fallback
            
            logger.debug(f"    🌐 Language: {language}")
        except Exception as e:
            logger.error(f"    ❌ Fehler beim Language-Abruf: {e}")
            language = 'de-de'
        
        # [4] JSON aus Instanz laden
        try:
            # get_static_value(gruppe=value, feld=language)
            # Gibt JSON-String zurück mit allen Keys und Display-Texten
            json_data = self.dropdown_instance.get_static_value(value, language)
            
            if not json_data:
                logger.warning(f"    ⚠️ Keine Dropdown-Daten für {value}/{language}")
                return
            
            # [5] JSON parsen
            import json
            dropdown_dict = json.loads(json_data) if isinstance(json_data, str) else json_data
            
            # dropdown_dict = {"": "", "m": "Herr", "w": "Frau", ...}
            for item_key, display_text in dropdown_dict.items():
                if item_key and display_text:  # Leere Keys überspringen
                    self.dropdown_items[display_text] = item_key
                    logger.debug(f"    ✅ Dropdown-Item: '{display_text}' → '{item_key}'")
            
            logger.info(f"    🔽 Dropdown geladen: {len(self.dropdown_items)} Items für {value}")
                
        except json.JSONDecodeError as e:
            logger.error(f"    ❌ JSON-Parse-Fehler: {e}")
        except Exception as e:
            logger.error(f"    ❌ Fehler beim Laden der Dropdown-Items: {e}")
    
    @classmethod
    def clear_instance_cache(cls):
        """
        Leert Instanz-Cache (nur bei Neustart/Reset)
        
        WICHTIG: Wird NICHT bei Stichtag-Wechsel benötigt,
                 da Instanzen alle historischen Daten enthalten!
        """
        count = len(cls._instance_cache)
        cls._instance_cache.clear()
        logger.info(f"🗑️ Instanz-Cache geleert ({count} Instanzen)")
    
    # =========================================================================
    # DATEN LADEN
    # =========================================================================
    
    def _load_value_from_db(self):
        """
        Lädt Wert aus zugeordneter Instanz
        
        WICHTIG: Verwendet STICHTAG von GCS!
        """
        if not self.zugeordnete_instanz:
            logger.warning(f"    ⚠️ Keine Instanz für {self.label_text} - Wert = None")
            self.wert = None
            self.abdatum_wert = None
            self.original_value = None
            self.current_value = None
            return
        
        try:
            stichtag = gcs.st_inst.PdvmDateTime
            
            # Wert laden (stichtagsgenau!)
            self.wert, self.abdatum_wert = self.zugeordnete_instanz.get_value(
                self.gruppe,
                self.feld,
                stichtag
            )
            
            # Original-Werte speichern (abhängig von type)
            if self.control_type == 'datetime':
                # Datum: Float-Wert in Pdvm_DateTime Instanz setzen
                if self.wert is not None:
                    if not self.value_dt:
                        self.value_dt = Pdvm_DateTime(gcs.field_value('country'))
                    self.value_dt.PdvmDateTime = float(self.wert)
                self.original_value = self.wert  # Float speichern
                self.current_value = self.wert
            else:
                # Text: Direkt übernehmen
                self.original_value = self.wert
                self.current_value = self.wert
            
            # Abdatum-Instanz für Anzeige aktualisieren
            if self.abdatum_wert:
                self.abdatum_dt.PdvmDateTime = float(self.abdatum_wert)
            
            if not self.show_abdatum:
                # Debug für Felder ohne Historie-UI
                logger.info(f"    📊 GELADEN (ohne neue Historie): {self.label_text}")
                logger.info(f"        Wert: {str(self.wert)[:50]}")
                logger.info(f"        Abdatum: {self.abdatum_dt.FormTimeStamp if self.abdatum_wert else 'None'}")
                logger.info(f"        Stichtag: {stichtag}")
            else:
                logger.debug(f"    📊 Geladen: wert={str(self.wert)[:30]}, abdatum={self.abdatum_dt.FormTimeStamp if self.abdatum_wert else 'None'}")
            
        except Exception as e:
            logger.error(f"    ❌ Fehler beim Laden von {self.label_text}: {e}")
            self.wert = None
            self.abdatum_wert = None
            self.original_value = None
            self.current_value = None
    
    # =========================================================================
    # UI ERSTELLEN
    # =========================================================================
    
    def _create_ui(self):
        """Erstellt UI-Komponenten"""
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(10)
        
        # [1] LABEL
        self.label_widget = QLabel(self.label_text)
        self.label_widget.setFixedWidth(150)
        self.label_widget.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #2c3e50;
                padding: 5px;
            }
        """)
        layout.addWidget(self.label_widget)
        
        # [2] EDIT WIDGET (abhängig von type)
        if self.control_type == 'datetime':
            # DATETIME: PdvmDateTimePicker (verwaltet eigene Pdvm_DateTime Instanz)
            from pdvm_date_time_picker import PdvmDateTimePicker
            
            # Pdvm_DateTime Instanz für Wert erstellen
            if not self.value_dt:
                self.value_dt = Pdvm_DateTime(gcs.field_value('country'))
            
            # DateTimePicker erstellen (display_val → display parameter)
            # display: "all" (default), "only_date", "only_time"
            display_mode = self.display_val if self.display_val else "all"
            self.date_picker = PdvmDateTimePicker(
                parent=self,
                pdvm_datetime=self.value_dt,
                display=display_mode
            )
            
            # Read-Only Status
            if self.read_only:
                self.date_picker.setEnabled(False)
            else:
                # 🔹 SIGNAL: Picker benachrichtigt bei Änderungen (für Dirty-Visualisierung)
                self.date_picker.valueChanged.connect(self._on_datetime_changed)
            
            layout.addWidget(self.date_picker)
        
        elif self.control_type == 'dropdown':
            # DROPDOWN: QComboBox mit Daten aus dropdown_instance
            from PyQt5.QtWidgets import QComboBox
            
            self.combo_box = QComboBox()
            self.combo_box.setMinimumWidth(200)
            
            # Items hinzufügen (aus self.dropdown_items)
            for display_text in sorted(self.dropdown_items.keys()):
                self.combo_box.addItem(display_text, self.dropdown_items[display_text])
            
            # Read-Only Status
            if self.read_only:
                self.combo_box.setEnabled(False)
                self.combo_box.setStyleSheet("""
                    QComboBox {
                        background-color: #ecf0f1;
                        border: 1px solid #bdc3c7;
                        border-radius: 3px;
                        padding: 5px;
                        color: #7f8c8d;
                    }
                """)
            else:
                self.combo_box.setStyleSheet("""
                    QComboBox {
                        background-color: white;
                        border: 1px solid #3498db;
                        border-radius: 3px;
                        padding: 5px;
                        color: #2c3e50;
                    }
                """)
                # Change-Handler nur wenn editierbar
                self.combo_box.currentIndexChanged.connect(self._on_dropdown_changed)
            
            layout.addWidget(self.combo_box)
            
        else:
            # TEXT (Default): QLineEdit
            self.edit_widget = QLineEdit()
            self.edit_widget.setMinimumWidth(200)
            
            # Read-Only Styling
            if self.read_only:
                self.edit_widget.setReadOnly(True)
                self.edit_widget.setStyleSheet("""
                    QLineEdit {
                        background-color: #ecf0f1;
                        border: 1px solid #bdc3c7;
                        border-radius: 3px;
                        padding: 5px;
                        color: #7f8c8d;
                    }
                """)
            else:
                self.edit_widget.setStyleSheet("""
                    QLineEdit {
                        background-color: white;
                        border: 1px solid #3498db;
                        border-radius: 3px;
                        padding: 5px;
                        color: #2c3e50;
                    }
                """)
                # Change-Handler nur wenn editierbar
                self.edit_widget.textChanged.connect(self._on_value_changed)
            
            layout.addWidget(self.edit_widget)
        
        # [4] HISTORIE-BUTTON (Punkt 3: wie V2 - nur wenn historical=True UND show_abdatum=True)
        if self.historical and self.show_abdatum:
            self.history_button = QPushButton("📜")
            self.history_button.setFixedSize(30, 30)
            self.history_button.setToolTip("Historie anzeigen")
            self.history_button.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-size: 14pt;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:disabled {
                    background-color: #bdc3c7;
                    color: #7f8c8d;
                }
            """)
            
            # Aktivierung wird in _update_ui() gesetzt (nach _resolve_instance)
            self.history_button.setEnabled(False)  # Erstmal disabled
            self.history_button.clicked.connect(self._open_history_dialog)
            layout.addWidget(self.history_button)
        
        # [5] HILFE-BUTTON (NEU: immer erstellen wenn help_config vorhanden)
        if self.help_config:
            self.help_button = QPushButton("❓")
            self.help_button.setFixedSize(30, 30)
            self.help_button.setToolTip("Hilfe anzeigen")
            self.help_button.setStyleSheet("""
                QPushButton {
                    background-color: #f39c12;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-size: 14pt;
                }
                QPushButton:hover {
                    background-color: #e67e22;
                }
            """)
            self.help_button.clicked.connect(self._open_help_dialog)
            layout.addWidget(self.help_button)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def _update_ui(self):
        """Aktualisiert UI mit aktuellen Werten"""
        # [1] READ-ONLY STATUS AKTUALISIEREN
        if self.control_type == 'datetime':
            # Date-Picker enable/disable
            if self.date_picker:
                self.date_picker.setEnabled(not self.read_only)
        
        elif self.control_type == 'dropdown':
            # ComboBox enable/disable
            if self.combo_box:
                self.combo_box.setEnabled(not self.read_only)
                
        else:
            # LineEdit read-only
            # EINFACH: self.read_only wurde in _resolve_instance() gesetzt
            if not self.edit_widget:
                return  # Kein Widget erstellt (Fehler in _create_ui)
            
            if self.read_only:
                self.edit_widget.setReadOnly(True)
                self.edit_widget.setStyleSheet("""
                    QLineEdit {
                        background-color: #ecf0f1;
                        border: 1px solid #bdc3c7;
                        border-radius: 3px;
                        padding: 5px;
                        color: #7f8c8d;
                    }
                """)
            else:
                self.edit_widget.setReadOnly(False)
                self.edit_widget.setStyleSheet("""
                    QLineEdit {
                        background-color: white;
                        border: 1px solid #3498db;
                        border-radius: 3px;
                        padding: 5px;
                        color: #2c3e50;
                    }
                """)
        
        # [2] HISTORIE-BUTTON AKTIVIERUNG (Punkt 3: wie V2 - enabled basierend auf Instanz)
        if self.history_button:
            # Button enabled wenn Instanz vorhanden
            self.history_button.setEnabled(self.zugeordnete_instanz is not None)
        
        # [3] Wert anzeigen (abhängig von type)
        if self.control_type == 'datetime':
            # Date-Picker: value_dt wurde in _load_value_from_db() gesetzt
            # Display aktualisieren damit Picker neuen Wert anzeigt
            if self.date_picker:
                self.date_picker.update_display()
        
        elif self.control_type == 'dropdown':
            # ComboBox: Richtigen Index setzen basierend auf current_value (key)
            if self.combo_box and self.current_value:
                # Finde Index des Items mit diesem key
                for i in range(self.combo_box.count()):
                    if self.combo_box.itemData(i) == self.current_value:
                        self.combo_box.blockSignals(True)
                        self.combo_box.setCurrentIndex(i)
                        self.combo_box.blockSignals(False)
                        break
        
        else:
            # LineEdit: Text setzen
            if self.edit_widget:
                display_value = str(self.current_value) if self.current_value is not None else ""
                self.edit_widget.blockSignals(True)
                self.edit_widget.setText(display_value)
                self.edit_widget.blockSignals(False)
        
        # [3b] Tooltip zusammenbauen (wie V2) - Feature 3
        tooltip_parts = []
        
        # Read-Only Status
        if not self.zugeordnete_instanz:
            tooltip_parts.append("🔒 SCHREIBGESCHÜTZT (keine Instanz - GUID nicht gefunden)")
        elif self.read_only:
            tooltip_parts.append("🔒 SCHREIBGESCHÜTZT (read_only=True in Metadaten)")
        
        # Abdatum (Feature 3!) - nur wenn show_abdatum=True
        if self.abdatum_wert and self.show_abdatum:
            tooltip_parts.append(f"💾 Abdatum: {self.abdatum_dt.FormTimeStamp}")
        
        # Metadaten-Tooltip (mit Trennlinien)
        if self.meta_tooltip:
            tooltip_parts.append("─" * 40)
            tooltip_parts.append(self.meta_tooltip)
            tooltip_parts.append("─" * 40)
        
        # Instanz-Info (V3: aus zugeordnete_instanz)
        if self.zugeordnete_instanz:
            instance_info = f"{self.tabelle}_{self.zugeordnete_guid[:8]}..."
            tooltip_parts.append(f"📂 Instanz: {instance_info}")
        else:
            tooltip_parts.append(f"📂 Instanz: ROOT ({self.root_instance.guid[:8]}...)")
        
        tooltip = "\n".join(tooltip_parts)
        
        # Tooltip auf entsprechendes Widget setzen
        if self.control_type == 'datetime' and self.date_picker:
            self.date_picker.setToolTip(tooltip)
        elif self.control_type == 'dropdown' and self.combo_box:
            self.combo_box.setToolTip(tooltip)
        elif self.edit_widget:
            self.edit_widget.setToolTip(tooltip)
    
    def _on_value_changed(self, text):
        """Handler für Wert-Änderungen (type=text)"""
        self.current_value = text
        self.is_dirty = (self.current_value != self.original_value)
        
        # Styling für dirty
        if self.is_dirty:
            self.edit_widget.setStyleSheet("""
                QLineEdit {
                    background-color: #fff9e6;
                    border: 2px solid #f39c12;
                    border-radius: 3px;
                    padding: 5px;
                    color: #2c3e50;
                }
            """)
    
    def _on_datetime_changed(self):
        """Handler für DateTime-Änderungen (type=datetime)"""
        # Picker ist dirty → Input Control ist dirty
        # 🔹 ORANGE RAHMEN: Picker stylt sich selbst via set_dirty_style()!
        self.is_dirty = True
    
    def _on_dropdown_changed(self, index):
        """Handler für Dropdown-Änderungen (type=dropdown)"""
        if index < 0:
            return  # Kein Item ausgewählt
        
        # Neuen Wert aus ComboBox holen (userData = key)
        self.current_value = self.combo_box.itemData(index)
        self.is_dirty = (self.current_value != self.original_value)
        
        # Styling für dirty
        if self.is_dirty:
            self.combo_box.setStyleSheet("""
                QComboBox {
                    background-color: #fff9e6;
                    border: 2px solid #f39c12;
                    border-radius: 3px;
                    padding: 5px;
                    color: #2c3e50;
                }
            """)
    
    # =========================================================================
    # HISTORIE-DIALOG
    # =========================================================================
    
    def _open_history_dialog(self):
        """Öffnet Historie-Dialog"""
        if not self.zugeordnete_instanz:
            logger.warning(f"  ⚠️ Keine Instanz für Historie: {self.label_text}")
            return
        
        logger.info(f"  📜 Öffne Historie: {self.label_text}")
        
        try:
            from pdvm_input_control_history_dialog import PdvmInputControlHistoryDialog
            
            dialog = PdvmInputControlHistoryDialog(
                label=self.label_text,
                gruppe=self.gruppe,
                feld=self.feld,
                db_instance=self.zugeordnete_instanz,
                control_type=self.control_type,  # NEU: Type weitergeben
                display_val=self.display_val,  # NEU: Display-Format weitergeben
                parent=self
            )
            
            # Dialog öffnen und auf Ergebnis warten
            result = dialog.exec_()
            
            # Wenn mit "Speichern" geschlossen (accept) → DIALOG REFRESHEN (wie Stichtag!)
            if result == dialog.Accepted:
                logger.info("  � Historie gespeichert → Dialog-Refresh (wie Stichtag-Wechsel)")
                
                # Parent-Dialog finden (wie bei Stichtag-Wechsel!)
                parent = self.parent()
                while parent:
                    # Prüfen ob parent ein Dialog mit refresh() Methode ist
                    if hasattr(parent, 'refresh') and callable(parent.refresh):
                        logger.info(f"  🔄 Rufe refresh() auf Parent-Dialog: {type(parent).__name__}")
                        parent.refresh()
                        logger.info("  ✅ Dialog-Refresh abgeschlossen")
                        break
                    parent = parent.parent()
                else:
                    logger.warning("  ⚠️ Kein Parent-Dialog mit refresh() gefunden! Fallback: Manager/Control refresh")
                    if self.manager:
                        self.manager.refresh_all_controls()
                    else:
                        self.refresh()
            
        except Exception as e:
            logger.error(f"  ❌ Fehler beim Öffnen des Historie-Dialogs: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    # =========================================================================
    # HILFE-DIALOG
    # =========================================================================
    
    def _open_help_dialog(self):
        """Öffnet Hilfe-Dialog mit Instanz-basierten Hilfedaten"""
        if not self.help_config:
            logger.warning(f"  ⚠️ Keine Hilfe-Konfiguration für: {self.label_text}")
            return
        
        logger.info(f"  ❓ Öffne Hilfe: {self.label_text}")
        
        try:
            # [1] Hilfe-Instanz lazy erstellen
            if not self.help_instance:
                table = self.help_config.get('table')
                guid = self.help_config.get('key')
                
                if not table or not guid:
                    logger.error(f"  ❌ Ungültige help_config: {self.help_config}")
                    return
                
                # Instance-Key für Cache
                instance_key = (table, guid)
                
                # Aus Cache holen oder neu erstellen
                if instance_key in self._instance_cache:
                    self.help_instance = self._instance_cache[instance_key]
                    logger.info(f"  📂 Hilfe-Instanz aus Cache: {table}.{guid}")
                else:
                    from pdvm_central_datenbank import PdvmCentralDatenbank
                    
                    logger.info(f"  🔧 Erstelle Hilfe-Instanz: {table}.{guid}")
                    # PdvmCentralDatenbank ermittelt historisch-Merkmal intern
                    self.help_instance = PdvmCentralDatenbank(table, guid)
                    self._instance_cache[instance_key] = self.help_instance
            
            # [2] Hilfe-Daten laden
            field_name = self.help_config.get('value')
            if not field_name:
                logger.error(f"  ❌ Kein Feldname in help_config: {self.help_config}")
                return
            
            # Hilfe-Daten aus ROOT-Gruppe laden (value = kompletter Feldname)
            logger.info(f"  📖 Lade Hilfedaten: ROOT.{field_name}")
            help_data = self.help_instance.get_static_value('ROOT', field_name)
            
            if not help_data:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(
                    self, 
                    "Keine Hilfe", 
                    f"Keine Hilfedaten für '{self.label_text}' verfügbar."
                )
                return
            
            # [3] Header und Text extrahieren
            header = help_data.get('header', 'Hilfe')
            text = help_data.get('text', 'Keine Hilfeinformationen verfügbar.')
            
            logger.info(f"  ✅ Hilfedaten geladen: {header}")
            
            # [4] Hilfe-Dialog anzeigen
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, header, text)
            
        except Exception as e:
            logger.error(f"  ❌ Fehler beim Öffnen des Hilfe-Dialogs: {e}")
            import traceback
            logger.error(traceback.format_exc())


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_control_from_config_v3(root_instance, meta: dict, manager=None, parent=None):
    """
    Factory-Funktion für Input-Controls V3 (AUTONOM)
    
    Args:
        root_instance: ROOT-Instanz (vom Manager)
        meta: Metadaten-Dict mit allen Informationen
        manager: Referenz zum Manager (für Refresh nach Historie-Speichern)
        parent: Parent-Widget
    
    Returns:
        PdvmInputControlV3 Instanz
    """
    return PdvmInputControlV3(
        root_instance=root_instance,
        meta=meta,
        manager=manager,
        parent=parent
    )
