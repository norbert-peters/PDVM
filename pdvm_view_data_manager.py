"""
Vollständig überarbeiteter View-Data-Manager
Implementiert die neue Architektur mit Original/Show-Spalten-Konzept
"""

import logging
from typing import Dict, List, Any, Optional
from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)

class PdvmViewDataManager:
    def get_column_labels(self) -> dict:
        """
        Gibt ein Mapping {spaltenname: label/anzeige/name} für alle Spalten aus der Controlstruktur zurück.
        """
        labels = {}
        if self.control and hasattr(self.control, 'columns'):
            for col in self.control.columns:
                name = col.get('name')
                field_cfg = col.get('field_config', {})
                # Mapping: zuerst 'anzeige', dann 'label', dann 'name', dann interner Name
                label = field_cfg.get('anzeige') or field_cfg.get('label') or field_cfg.get('name') or name
                labels[name] = label
        return labels
    """
    View-Data-Manager mit korrekter Original/Show-Spalten-Architektur
    Architektur:
    1. Für jedes Feld gibt es Original- und Show-Spalten
    2. Original-Spalten: Rohdaten aus DB (für Sortierung wenn sortByOriginal=true)
    3. Show-Spalten: Aufbereitete Daten für Anzeige (für Filter und Standardsortierung)
    4. Spezielle Spalten: Alter, Jahr, Monat, Tag (immer aufgebaut, unabhängig von Parametern)
    5. Filter arbeiten standardmäßig auf Show-Spalten (außer bei Datum-Zeitraum-Modus)
    """
    def __init__(self, view_guid: str, user_guid: Optional[str] = None):
        self.view_guid = view_guid
        self.user_guid = user_guid
        self.view_config = None
        self.table_name = None
        self.fields_config = []
        self.original_data = []  # Original-Daten mit Original/Show-Spalten
        self.processed_data = []  # Verarbeitete Daten für UI
        # View-Parameter
        self.show_YMD = False
        self.show_alter = False
        self.sort_by_original = {}  # field_name -> bool
        # Zentrale Datenbank-Instanz mit richtiger Tabelle
        self.central_db = None
        self.db_manager = None
        # Benutzer-Einstellungen
        self.user_settings = {}
        # Initialisierung
        self._load_view_configuration()
        self._load_user_settings()
        # Nach Laden der View-Konfiguration: zentrale DB-Instanz mit Tabelle initialisieren
        if self.table_name:
            self.central_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name=self.table_name
            )
        self.load_data()

    def _load_view_configuration(self):
        """Lädt die View-Konfiguration aus der Datenbank."""
        try:
            view_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="viewdaten",
                guid=self.view_guid
            )
            self.view_config = view_db.lesen()
            if not self.view_config:
                raise ValueError(f"View-Konfiguration nicht gefunden für GUID: {self.view_guid}")
            # ROOT-Konfiguration extrahieren
            root_config = self.view_config.get("ROOT", {})
            self.table_name = root_config.get("view_table")
            if not self.table_name:
                raise ValueError("Kein view_table in ROOT-Konfiguration gefunden")
            # Feld-Konfigurationen extrahieren
            metadata = self.view_config.get("metadata", {})
            table_metadata = metadata.get(self.table_name, {})
            self.fields_config = table_metadata.get("felder", [])
            # View-Parameter laden
            self.show_YMD = root_config.get("show_YMD", False)
            self.show_alter = root_config.get("show_alter", False)
            # Sortierungs-Einstellungen pro Feld
            for field_config in self.fields_config:
                field_name = field_config.get("feld")
                if field_name:
                    self.sort_by_original[field_name] = field_config.get("sortByOriginal", False)
            logger.info(f"✅ View-Konfiguration geladen: {self.table_name}")
            logger.info(f"📊 Parameter: show_YMD={self.show_YMD}, show_alter={self.show_alter}")
            logger.info(f"🔢 Felder mit Original-Sortierung: {[k for k, v in self.sort_by_original.items() if v]}")
            # Datenbank-Manager für Zieltabelle
            self.db_manager = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name=self.table_name
            )
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der View-Konfiguration: {e}")
            raise

    def _load_user_settings(self):
        """Lädt Benutzer-Einstellungen aus systemsteuerung"""
        try:
            if not self.user_guid:
                return
            sys_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="systemsteuerung",
                guid=self.user_guid
            )
            user_data = sys_db.lesen() or {}
            self.user_settings = user_data.get(self.view_guid, {})
            logger.info(f"📋 Benutzer-Einstellungen geladen für View {self.view_guid}")
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Laden der Benutzer-Einstellungen: {e}")
            self.user_settings = {}

    def save_user_settings(self, settings: Dict[str, Any]):
        """Speichert Benutzer-Einstellungen in systemsteuerung"""
        try:
            if not self.user_guid:
                return
            sys_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="systemsteuerung",
                guid=self.user_guid
            )
            user_data = sys_db.lesen() or {}
            user_data[self.view_guid] = settings
            sys_db.speichern(self.user_guid, user_data)
            self.user_settings = settings
            logger.info(f"💾 Benutzer-Einstellungen gespeichert für View {self.view_guid}")
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Benutzer-Einstellungen: {e}")

    def load_data(self, stichtag: Optional[float] = None):
        """
        Lädt Daten und Controlstruktur über die zentrale get_value_view() Methode.
        Erwartet Rückgabe als (controls, daten) Tuple.
        """
        try:
            if stichtag is None:
                from pd_datetime import Pdvm_DateTime
                dt_inst = Pdvm_DateTime("DEU")
                stichtag = dt_inst.PdvmDateTimeNow()
            # Daten und Controls gemeinsam laden
            logger.info(f"🔄 Lade Daten für View {self.view_guid} am Stichtag {stichtag}...")
            result = self.central_db.get_value_view(
                view_config=self.view_config,
                stichtag=stichtag
            )
            if not isinstance(result, tuple) or len(result) != 2:
                logger.error(f"❌ get_value_view muss (controls, daten) Tuple liefern, bekam: {type(result)}")
                self.control = None
                self.original_data = []
                self.processed_data = []
                return
            controls, daten = result
            self.control = controls
            self.original_data = daten
            self.processed_data = daten.copy() if isinstance(daten, list) else list(daten)
            logger.info(f"✅ Controlstruktur geladen: {len(self.control.columns) if self.control and hasattr(self.control, 'columns') else 0} Spalten")
            logger.info(f"✅ Daten geladen: {len(self.original_data)} Datensätze")
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Daten: {e}")
            self.original_data = []
            self.processed_data = []
            self.control = None

    def get_data(self) -> List[Dict[str, Any]]:
        """Gibt die verarbeiteten Daten zurück"""
        return self.processed_data

    def get_original_data(self) -> List[Dict[str, Any]]:
        """Gibt die Original-Daten zurück"""
        return self.original_data

    def get_fields_config(self) -> List[Dict[str, Any]]:
        """Gibt die Feld-Konfigurationen zurück"""
        return self.fields_config

    def get_field_config(self, field_name: str) -> Dict[str, Any]:
        """Gibt die Konfiguration für ein bestimmtes Feld zurück"""
        for field_config in self.fields_config:
            if field_config.get("feld") == field_name:
                return field_config
        return {}

    def get_field_names(self) -> List[str]:
        """Gibt alle konfigurierten Feldnamen zurück"""
        return [field["feld"] for field in self.fields_config if "feld" in field]

    def get_visible_columns(self) -> List[str]:
        """
        Gibt ALLE Spaltennamen aus der Controlstruktur zurück (also alle *_original, *_show, ...)
        """
        if self.control and hasattr(self.control, 'columns'):
            return [col['name'] for col in self.control.columns]
        return []

    def get_sort_column_for_field(self, field_name: str) -> str:
        """
        Bestimmt die Spalte für Sortierung basierend auf sortByOriginal-Einstellung
        """
        if self.sort_by_original.get(field_name, False):
            return f"{field_name}_original"
        else:
            return f"{field_name}_show"

    def get_filter_column_for_field(self, field_name: str, filter_mode: str = "standard") -> str:
        """
        Bestimmt die Spalte für Filterung
        Args:
            field_name: Feldname
            filter_mode: "standard" (Show-Spalte) oder "zeitraum" (Original-Spalte für Datum)
        """
        field_config = self.get_field_config(field_name)
        field_type = field_config.get("type")
        # Datum-Felder im Zeitraum-Modus verwenden Original-Spalte
        if field_type == "date" and filter_mode == "zeitraum":
            return f"{field_name}_original"
        # Standard: Show-Spalte für Filter
        return f"{field_name}_show"

    def get_dropdown_options(self, field_name: str) -> Dict[str, str]:
        """Holt Dropdown-Optionen für ein Feld"""
        try:
            field_config = self.get_field_config(field_name)
            if not field_config or field_config.get("type") != "dropdown":
                return {}
            dropdown_config = field_config.get("dropdown", {})
            if not dropdown_config:
                return {}
            return self.central_db.get_dropdown_options(
                field_name=field_name,
                dropdown_config=dropdown_config
            )
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Dropdown-Optionen für {field_name}: {e}")
            return {}

    def get_table_info(self) -> str:
        """Gibt Info-String über die geladene Tabelle zurück"""
        return f"Tabelle: {self.table_name}, Felder: {len(self.fields_config)}, Datensätze: {len(self.original_data)}"

    def refresh(self, stichtag: Optional[float] = None):
        """Lädt Daten neu (z.B. bei Stichtag-Wechsel oder Aktualisieren)"""
        logger.info("🔄 Daten werden neu geladen...")
        self.load_data(stichtag)

    def get_user_setting(self, key: str, default=None):
        """Holt eine Benutzer-Einstellung"""
        return self.user_settings.get(key, default)

    def set_user_setting(self, key: str, value: Any):
        """Setzt eine Benutzer-Einstellung (noch nicht gespeichert)"""
        self.user_settings[key] = value
