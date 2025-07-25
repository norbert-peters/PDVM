# pdvm_view_data_manager.py
"""
Moderner View-Data-Manager für saubere Trennung von UI und Datenlogik.
Implementiert das Manager-Pattern für effiziente Datenverarbeitung.
"""

import logging
from typing import Dict, List, Any, Optional
from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)

class PdvmViewDataManager:
    """
    Manager für View-Daten mit sauberer Trennung von UI und Datenlogik.
    Effiziente Datenbeschaffung und -aufbereitung für UI-Komponenten.
    """
    
    def __init__(self, view_guid: str, user_guid: Optional[str] = None):
        """
        Initialisiert den View-Data-Manager.
        
        Args:
            view_guid: GUID der View-Konfiguration
            user_guid: Optional: Benutzer-GUID für benutzerabhängige Daten
        """
        self.view_guid = view_guid
        self.user_guid = user_guid
        self.view_config = None
        self.table_name = None
        self.fields_config = []
        self.raw_data = []
        self.processed_data = []
        
        # Zentrale Datenbank-Instanz für Dropdown-Operationen
        self.central_db = PdvmCentralDatenbank()
        
        # Datenbank-Manager wird nach View-Konfiguration initialisiert
        self.db_manager = None
        
        # View-Konfiguration laden
        self._load_view_configuration()
        
        # Daten initial laden
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
            
            # Tabellennamen extrahieren
            self.table_name = self.view_config.get("table_name")
            if not self.table_name:
                raise ValueError("Kein table_name in View-Konfiguration gefunden")
            
            # Feld-Konfigurationen extrahieren
            self.fields_config = self.view_config.get("fields", [])
            if not self.fields_config:
                raise ValueError("Keine Feld-Konfigurationen in View gefunden")
            
            logger.info(f"✅ View-Konfiguration geladen: {self.table_name} mit {len(self.fields_config)} Feldern")
            
            # Datenbank-Manager für die Zieltabelle initialisieren
            self.db_manager = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name=self.table_name
            )
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der View-Konfiguration: {e}")
            raise
    
    def load_data(self, stichtag: Optional[float] = None):
        """
        Lädt die View-Daten und bereitet sie für die UI auf.
        
        Args:
            stichtag: Optionaler Stichtag für historische Daten
        """
        try:
            if stichtag is None:
                from pd_datetime import Pdvm_DateTime
                dt_inst = Pdvm_DateTime("DEU")
                stichtag = dt_inst.PdvmDateTimeNow()
            
            # Datenbank-Manager für die Zieltabelle
            data_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name=self.table_name
            )
            
            # EFFIZIENT: Alle Daten mit einer Abfrage laden und auflösen
            self.processed_data = data_db.get_value_view(self.view_config, stichtag)
            
            # Zusätzliche Datenaufbereitung (wie Display-Felder für GUIDs)
            self._add_display_data()
            
            logger.info(f"📊 View-Manager: {len(self.processed_data)} Datensätze geladen und verarbeitet")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der View-Daten: {e}")
            raise
    
    def _add_display_data(self):
        """Fügt zusätzliche Display-Informationen zu den Daten hinzu (z.B. für GUID-Verweise)."""
        # Hier können zukünftig weitere Display-Anreicherungen implementiert werden
        # z.B. User-Namen aus GUIDs, berechnete Felder, etc.
        logger.debug(f"🔍 Display-Daten aufbereitet für {len(self.processed_data)} Datensätze")
    
    def get_data(self) -> List[Dict[str, Any]]:
        """
        Gibt die verarbeiteten Daten zurück.
        
        Returns:
            Liste der verarbeiteten Datensätze
        """
        return self.processed_data
    
    def get_fields_config(self) -> List[Dict[str, Any]]:
        """
        Gibt die Feld-Konfigurationen zurück.
        
        Returns:
            Liste der Feld-Konfigurationen
        """
        return self.fields_config
    
    def get_field_names(self) -> List[str]:
        """
        Gibt die Namen aller konfigurierten Felder zurück.
        
        Returns:
            Liste der Feldnamen
        """
        return [field.get("feld", "") for field in self.fields_config]
    
    def get_dropdown_fields(self) -> List[str]:
        """
        Gibt die Namen aller Dropdown-Felder zurück.
        
        Returns:
            Liste der Dropdown-Feldnamen
        """
        dropdown_fields = []
        for field_config in self.fields_config:
            if field_config.get("type") == "dropdown":
                dropdown_fields.append(field_config.get("feld", ""))
        return dropdown_fields
    
    def get_dropdown_options(self, field_name: str) -> Dict[str, str]:
        """
        Holt Dropdown-Optionen für ein Feld DIREKT aus der zentralen Datenbank.
        
        Args:
            field_name: Name des Feldes
            
        Returns:
            Dict mit Key->Display-Text Mapping
        """
        try:
            # Feld-Konfiguration finden
            field_config = None
            for config in self.fields_config:
                if config.get("feld") == field_name:
                    field_config = config
                    break
            
            if not field_config or field_config.get("type") != "dropdown":
                return {}
            
            # Dropdown-Konfiguration holen (unterstützt sowohl 'lookup' als auch 'dropdown')
            dropdown_config = field_config.get("lookup") or field_config.get("dropdown", {})
            
            if not dropdown_config:
                return {}
            
            # ZENTRALE METHODE nutzen: Dropdown-Optionen direkt aus PdvmCentralDatenbank
            return self.central_db.get_dropdown_options_from_data(
                table_name=self.table_name,
                field_name=field_name,
                dropdown_config=dropdown_config
            )
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Holen der Dropdown-Optionen für {field_name}: {e}")
            return {}
    
    def get_table_info(self) -> Dict[str, Any]:
        """
        Gibt Informationen über die View-Tabelle zurück.
        
        Returns:
            Dict mit Tabellen-Informationen
        """
        return {
            "table_name": self.table_name,
            "view_guid": self.view_guid,
            "field_count": len(self.fields_config),
            "record_count": len(self.processed_data),
            "dropdown_fields": self.get_dropdown_fields()
        }
    
    def search(self, search_term: str, fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Sucht in den Daten nach einem Begriff.
        
        Args:
            search_term: Suchbegriff
            fields: Optional: Liste der zu durchsuchenden Felder
            
        Returns:
            Liste der gefundenen Datensätze
        """
        if not search_term:
            return self.processed_data
        
        search_fields = fields or self.get_field_names()
        results = []
        
        for record in self.processed_data:
            for field_name in search_fields:
                if field_name in record:
                    field_value = str(record[field_name]).lower()
                    if search_term.lower() in field_value:
                        results.append(record)
                        break
        
        logger.debug(f"🔍 Suche nach '{search_term}': {len(results)} Treffer")
        return results
    
    def filter_data(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Filtert die Daten nach den angegebenen Kriterien.
        
        Args:
            filters: Dict mit Filter-Kriterien {field_name: filter_criteria}
            
        Returns:
            Liste der gefilterten Datensätze
        """
        if not filters:
            return self.processed_data
        
        filtered_data = []
        
        for record in self.processed_data:
            matches_all_filters = True
            
            for field_name, filter_criteria in filters.items():
                if not self._record_matches_filter(record, field_name, filter_criteria):
                    matches_all_filters = False
                    break
            
            if matches_all_filters:
                filtered_data.append(record)
        
        logger.debug(f"🔍 Filter angewendet: {len(filtered_data)} von {len(self.processed_data)} Datensätzen")
        return filtered_data
    
    def _record_matches_filter(self, record: Dict[str, Any], field_name: str, filter_criteria: Any) -> bool:
        """
        Prüft ob ein Datensatz die Filter-Kriterien erfüllt.
        
        Args:
            record: Datensatz
            field_name: Feldname
            filter_criteria: Filter-Kriterien
            
        Returns:
            True wenn Datensatz dem Filter entspricht
        """
        if field_name not in record:
            return False
        
        field_value = record[field_name]
        
        # Dropdown-Filter (Set von erlaubten Keys)
        if isinstance(filter_criteria, dict) and "selected_keys" in filter_criteria:
            selected_keys = filter_criteria["selected_keys"]
            if not selected_keys:  # Leere Auswahl = alle anzeigen
                return True
            
            # Für Dropdown-Filter wird der RAW-Wert (Key) verwendet
            check_value = str(field_value) if field_value is not None else ""
            
            # Prüfe ob Wert in ausgewählten Keys
            return check_value in selected_keys
        
        # Text-Filter (contains)
        elif isinstance(filter_criteria, str):
            if not field_value:
                return filter_criteria == ""
            return filter_criteria.lower() in str(field_value).lower()
        
        return True
    
    def refresh(self, stichtag: Optional[float] = None):
        """
        Lädt die Daten neu.
        
        Args:
            stichtag: Optionaler neuer Stichtag
        """
        logger.info("🔄 View-Data-Manager: Lade Daten neu...")
        self.load_data(stichtag)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Gibt Statistiken über die geladenen Daten zurück.
        
        Returns:
            Dict mit Statistiken
        """
        return {
            "table_name": self.table_name,
            "view_guid": self.view_guid,
            "total_records": len(self.processed_data),
            "total_fields": len(self.fields_config),
            "dropdown_fields": len(self.get_dropdown_fields()),
            "field_names": self.get_field_names()
        }
    
    def get_display_value(self, field_name: str, raw_value: Any) -> str:
        """
        Konvertiert einen Raw-Wert in den Display-Wert (für Dropdown-Felder etc.).
        
        Args:
            field_name: Name des Feldes
            raw_value: Raw-Wert aus der Datenbank
            
        Returns:
            Display-Wert (übersetzt falls Dropdown)
        """
        if raw_value is None:
            return ""
        
        try:
            # Prüfe ob es ein Dropdown-Feld ist
            field_config = None
            for config in self.fields_config:
                if config.get("feld") == field_name:
                    field_config = config
                    break
            
            if field_config and field_config.get("type") == "dropdown":
                # Dropdown-Konfiguration holen
                dropdown_config = field_config.get("lookup") or field_config.get("dropdown", {})
                
                if dropdown_config:
                    # ZENTRALE METHODE nutzen: Display-Wert direkt aus PdvmCentralDatenbank
                    display_value = self.central_db.get_dropdown_display_value(
                        raw_value=str(raw_value),
                        field_name=field_name,
                        dropdown_config=dropdown_config
                    )
                    return display_value
            
            # Standardfall: Raw-Wert als String
            return str(raw_value)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Konvertieren des Display-Werts für {field_name}: {e}")
            return str(raw_value)
    
    def get_dropdown_raw_value(self, field_name: str, display_value: str) -> str:
        """
        Konvertiert einen Display-Wert zurück zum Raw-Wert (für Filter etc.).
        
        Args:
            field_name: Name des Feldes
            display_value: Display-Wert (übersetzt)
            
        Returns:
            Raw-Wert (Key)
        """
        try:
            dropdown_options = self.get_dropdown_options(field_name)
            
            # Suche den Key zum Display-Wert
            for key, value in dropdown_options.items():
                if value == display_value:
                    return key
            
            # Fallback: Display-Wert ist bereits der Raw-Wert
            return display_value
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Konvertieren des Raw-Werts für {field_name}: {e}")
            return display_value
