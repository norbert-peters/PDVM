# -*- coding: utf-8 -*-
# pdvm_central_datenbank.py - BEREINIGTE LINEARE VERSION
"""
Business-Logic-Layer für strukturierte Datenverwaltung.

ARCHITEKTUR:
- Nutzt pdvm_datenbank.py für alle DB-Operationen (KEINE eigene DB-Logik)
- Linear: get_value/set_value für Gruppe/Feld-basierte Zugriffe
- Automatische Zeitstempel-Verwaltung für historische Daten
- Fokus auf Business-Logik, nicht auf JSON-Parsing oder DB-Details

BEREINIGT:
- Alle Reparatur-Mechanismen entfernt
- Redundante DB-Methoden eliminiert  
- Nur eine get/set-Methode pro Konzept
- Lineare Datenflüsse ohne komplexe Parsing-Logik
"""

import logging
from typing import Any, Dict, Optional, List
from pdvm_datenbank import PdvmDatenbank
from pdvm_datetime import Pdvm_DateTime

logger = logging.getLogger(__name__)


class PdvmCentralDatenbank:
    """
    Business-Logic-Layer für strukturierte Datenverwaltung.
    
    Verwaltet Daten in Gruppe/Feld-Struktur mit optionaler Zeithistorie.
    Nutzt PdvmDatenbank für alle Persistierung - KEINE eigene DB-Logik.
    """

    def __init__(
        self,
        table_name: str = "menudaten",
        guid: Optional[str] = None
    ):
        """
        Initialisiert die Business-Logic-Schicht.
        
        Args:
            table_name: Name der Tabelle
            guid: GUID des Datensatzes (falls None, muss später gesetzt werden)
        """
        self.table_name = table_name
        self.guid = guid
        
        # Basis-Datenbankschicht initialisieren (ohne db_name Parameter)
        self._database = PdvmDatenbank(
            table_name=table_name
        )
        
        # Datenbank-Name aus der PdvmDatenbank-Instanz abrufen
        self.db_name = self._database.db_name
        
        # Historisch-Status aus PdvmDatenbank abrufen
        self.historisch = self._database.get_historisch_status()
        
        # Daten-Cache (wird bei Bedarf geladen)
        self.data: Dict[str, Any] = {}
        self._data_loaded = False
        
        # Automatische Initialisierung falls GUID vorhanden
        if self.guid:
            self._load_data()
        
        logger.info(f"PdvmCentralDatenbank initialisiert: {table_name}.{guid} (historisch: {self.historisch})")

    @classmethod
    def create_with_data(
        cls,
        guid: str,
        daten: Dict[str, Any],
        table_name: str = "menudaten"
    ):
        """
        Factory-Methode: Erstellt Instanz mit bereits geladenen Daten.
        
        PERFORMANCE-OPTIMIERUNG für Views:
        Wenn Daten bereits aus der DB geladen sind (z.B. aus lesen_alle()),
        kann eine Instanz direkt mit diesen Daten erstellt werden, ohne
        erneuten DB-Zugriff.
        
        Args:
            guid: GUID des Datensatzes
            daten: Bereits geladene Daten (Dictionary)
            table_name: Name der Tabelle
        """
        # Instanz ohne automatisches Laden erstellen
        instance = cls(
            table_name=table_name,
            guid=None  # Erst None, dann über set_data setzen
        )
        
        # Daten direkt setzen
        instance.set_data(daten, guid)
        
        logger.debug(f"Instanz mit Daten erstellt: {guid} ({len(daten)} Gruppen)")
        return instance

    def _load_data(self):
        """Lädt Daten aus der Datenbank in den Cache."""
        if not self.guid:
            raise ValueError("GUID muss gesetzt sein um Daten zu laden")
        
        loaded_data = self._database.lesen(self.guid)
        if loaded_data is not None:
            self.data = loaded_data
        else:
            # Neuer Datensatz - leere Struktur erstellen
            self.data = {}
        
        self._data_loaded = True
        logger.debug(f"Daten geladen für GUID {self.guid}: {len(self.data)} Gruppen")

    def _ensure_data_loaded(self):
        """Stellt sicher, dass Daten geladen sind."""
        if not self._data_loaded:
            self._load_data()

    def _get_current_timestamp(self) -> float:
        """
        Erstellt aktuellen Zeitstempel für historische Daten.
        
        Returns:
            float: Zeitstempel im PDVM-Format
        """
        dt_instance = Pdvm_DateTime("DEU")  # TODO: Land aus Systemsteuerung holen
        return dt_instance.PdvmDateTimeNow()

    def set_guid(self, guid: str):
        """
        Setzt neue GUID und lädt entsprechende Daten.
        
        Args:
            guid: Neue GUID
        """
        if self.guid != guid:
            self.guid = guid
            self._data_loaded = False
            self.data = {}
            if guid:
                self._load_data()
            logger.debug(f"GUID gewechselt zu: {guid}")

    def set_data(self, daten: Dict[str, Any], guid: str = None):
        """
        Setzt Daten direkt in die Instanz ohne DB-Zugriff.
        
        PERFORMANCE-OPTIMIERUNG für Views:
        Wenn alle Daten bereits geladen sind (z.B. aus lesen_alle()), 
        können sie direkt in die Instanz gesetzt werden, um erneute 
        DB-Zugriffe zu vermeiden.
        
        Args:
            daten: Dictionary mit den Daten (entspricht der 'daten' Spalte aus der DB)
            guid: Optional - GUID des Datensatzes (falls nicht bereits gesetzt)
        """
        try:
            # GUID setzen falls übergeben
            if guid is not None and self.guid != guid:
                self.guid = guid
                logger.debug(f"GUID über set_data gesetzt: {guid}")
            
            # Daten direkt setzen - verschiedene Formate unterstützen
            if isinstance(daten, dict):
                self.data = daten.copy()  # Kopie erstellen für Isolation
                logger.debug(f"Dict-Daten direkt gesetzt: {len(self.data)} Gruppen")
            elif isinstance(daten, str):
                # Falls als JSON-String übergeben, parsen (sollte selten vorkommen)
                try:
                    import json
                    self.data = json.loads(daten)
                    logger.debug(f"JSON-String geparst und gesetzt: {len(self.data)} Gruppen")
                except json.JSONDecodeError as e:
                    logger.error(f"Fehler beim JSON-Parsing in set_data: {e}")
                    self.data = {}
            else:
                logger.error(f"Ungültiger Datentyp in set_data: {type(daten)}")
                self.data = {}
            
            # Markiere Daten als geladen
            self._data_loaded = True
            
            logger.debug(f"set_data erfolgreich: GUID={self.guid}, Gruppen={list(self.data.keys())}")
            
        except Exception as e:
            logger.error(f"Fehler in set_data: {e}")
            self.data = {}
            self._data_loaded = False

    def get_value(self, gruppe: str, feld: str, ab_zeit: Optional[float] = None) -> Any:
        """
        Liest einen Wert aus der Gruppe/Feld-Struktur.
        
        Args:
            gruppe: Name der Gruppe
            feld: Name des Feldes
            ab_zeit: Zeitpunkt für historische Daten (None = aktuell)
            
        Returns:
            Any: Der Wert oder None wenn nicht gefunden
        """
        self._ensure_data_loaded()
        
        if gruppe not in self.data:
            return None
        
        gruppe_data = self.data[gruppe]
        if not isinstance(gruppe_data, dict):
            return None
        
        if feld not in gruppe_data:
            return None
        
        feld_data = gruppe_data[feld]
        
        # Für historische Daten: Zeitbasierte Auswahl
        if self.historisch and isinstance(feld_data, dict) and ab_zeit is not None:
            # Finde den passenden Zeitstempel
            best_time = None
            for timestamp in feld_data.keys():
                try:
                    ts_float = float(timestamp)
                    if ts_float <= ab_zeit:
                        if best_time is None or ts_float > best_time:
                            best_time = ts_float
                except (ValueError, TypeError):
                    continue
            
            if best_time is not None:
                # Verwende den ursprünglichen String-Schlüssel
                for timestamp in feld_data.keys():
                    try:
                        if float(timestamp) == best_time:
                            return feld_data[timestamp]
                    except (ValueError, TypeError):
                        continue
                return None
            else:
                return None
        
        # Nicht-historisch oder aktueller Wert
        if self.historisch and isinstance(feld_data, dict):
            # Neueste Zeit finden
            latest_time = None
            for timestamp in feld_data.keys():
                try:
                    ts_float = float(timestamp)
                    if latest_time is None or ts_float > latest_time:
                        latest_time = ts_float
                except (ValueError, TypeError):
                    continue
            
            if latest_time is not None:
                # Verwende den ursprünglichen String-Schlüssel
                for timestamp in feld_data.keys():
                    try:
                        if float(timestamp) == latest_time:
                            return feld_data[timestamp]
                    except (ValueError, TypeError):
                        continue
        
        # Direkter Wert
        return feld_data

    def get_static_value(self, gruppe: str, feld: str) -> Any:
        """
        Vereinfachte statische Wertabfrage nur für nicht-historische Daten.
        
        Geht davon aus, dass die Instanz bereits Daten geladen hat.
        Keine Prüfungen - direkter Zugriff für Performance.
        
        Args:
            gruppe: Name der Gruppe
            feld: Name des Feldes
            
        Returns:
            Any: Der direkte Wert
            
        Raises:
            ValueError: Wenn historische Tabelle
        """
        # Prüfe ob historische Tabelle
        if self.historisch:
            raise ValueError("❌ get_static_value kann nicht auf historische Tabellen angewendet werden")
            
        # Direkter Zugriff auf geladene Daten
        feld_data = self.data[gruppe][feld]
        
        # Legacy-Kompatibilität: Prüfe auf 'wert'-Dict-Struktur
        if isinstance(feld_data, dict) and 'wert' in feld_data:
            return feld_data['wert']
            
        return feld_data

    def set_value(self, gruppe: str, feld: str, wert: Any, ab_zeit: Optional[float] = None):
        """
        Setzt einen Wert in der Gruppe/Feld-Struktur.
        
        Args:
            gruppe: Name der Gruppe
            feld: Name des Feldes  
            wert: Der zu setzende Wert
            ab_zeit: Zeitpunkt für historische Daten (None = jetzt)
        """
        self._ensure_data_loaded()
        
        # Gruppe sicherstellen
        if gruppe not in self.data:
            self.data[gruppe] = {}
        
        if not isinstance(self.data[gruppe], dict):
            self.data[gruppe] = {}
        
        # Zeitstempel für historische Daten
        if self.historisch:
            if ab_zeit is None:
                ab_zeit = self._get_current_timestamp()
            
            # Feld als Zeitstempel-Dictionary strukturieren
            if feld not in self.data[gruppe]:
                self.data[gruppe][feld] = {}
            elif not isinstance(self.data[gruppe][feld], dict):
                # Bestehenden Wert in historische Struktur konvertieren
                old_value = self.data[gruppe][feld]
                self.data[gruppe][feld] = {str(ab_zeit): old_value}
            
            self.data[gruppe][feld][str(ab_zeit)] = wert
        else:
            # Direkter Wert
            self.data[gruppe][feld] = wert
        
        logger.debug(f"Wert gesetzt: {gruppe}.{feld} = {type(wert).__name__}")

    def get_all_values(self) -> Dict[str, Any]:
        """
        Gibt alle Daten zurück.
        
        Returns:
            Dict: Vollständige Datenstruktur
        """
        self._ensure_data_loaded()
        return self.data.copy()

    def save_all_values(self):
        """Speichert alle Daten in die Datenbank."""
        if not self.guid:
            raise ValueError("GUID muss gesetzt sein um Daten zu speichern")
        
        self._database.speichern(self.guid, self.data)
        logger.info(f"Alle Daten gespeichert für GUID {self.guid}")

    def delete_group(self, gruppe: str):
        """
        Löscht eine komplette Gruppe.
        
        Args:
            gruppe: Name der zu löschenden Gruppe
        """
        self._ensure_data_loaded()
        
        if gruppe in self.data:
            del self.data[gruppe]
            logger.debug(f"Gruppe gelöscht: {gruppe}")

    def delete_field(self, gruppe: str, feld: str):
        """
        Löscht ein Feld aus einer Gruppe.
        
        Args:
            gruppe: Name der Gruppe
            feld: Name des zu löschenden Feldes
        """
        self._ensure_data_loaded()
        
        if gruppe in self.data and isinstance(self.data[gruppe], dict):
            if feld in self.data[gruppe]:
                del self.data[gruppe][feld]
                logger.debug(f"Feld gelöscht: {gruppe}.{feld}")

    def get_groups(self) -> List[str]:
        """
        Gibt alle Gruppennamen zurück.
        
        Returns:
            List[str]: Liste der Gruppennamen
        """
        self._ensure_data_loaded()
        return list(self.data.keys())

    def get_fields(self, gruppe: str) -> List[str]:
        """
        Gibt alle Feldnamen einer Gruppe zurück.
        
        Args:
            gruppe: Name der Gruppe
            
        Returns:
            List[str]: Liste der Feldnamen
        """
        self._ensure_data_loaded()
        
        if gruppe not in self.data:
            return []
        
        gruppe_data = self.data[gruppe]
        if not isinstance(gruppe_data, dict):
            return []
        
        return list(gruppe_data.keys())

    def create_new_record(self) -> str:
        """
        Erstellt einen neuen Datensatz mit automatischer GUID.
        
        Returns:
            str: Die neue GUID
        """
        new_guid = self._database.anlegen({})
        self.set_guid(new_guid)
        return new_guid

    def delete_record(self):
        """Löscht den aktuellen Datensatz aus der Datenbank."""
        if not self.guid:
            raise ValueError("GUID muss gesetzt sein um Datensatz zu löschen")
        
        success = self._database.loeschen(self.guid)
        if success:
            self.data = {}
            self._data_loaded = False
            logger.info(f"Datensatz gelöscht: {self.guid}")
        return success

    def get_all_records(self) -> List[Dict[str, Any]]:
        """
        Gibt alle Datensätze der Tabelle zurück.
        
        Returns:
            List[Dict]: Liste aller Datensätze mit uid, daten, last_modified
        """
        return self._database.alle_lesen()

    def get_table_info(self) -> Dict[str, Any]:
        """
        Gibt Informationen über die Tabelle zurück.
        
        Returns:
            Dict: Tabellen-Statistiken
        """
        base_info = self._database.get_table_info()
        base_info.update({
            'current_guid': self.guid,
            'data_loaded': self._data_loaded,
            'groups_count': len(self.data) if self._data_loaded else 0
        })
        return base_info
