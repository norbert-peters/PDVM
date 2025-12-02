# -*- coding: utf-8 -*-
# v2_pdvm_central_datenbank.py - V2.0 VERSION (KOPIE VON pdvm_central_datenbank.py)
"""
V2.0 Business-Logic-Layer - Identisch mit pdvm_central_datenbank.py
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
        table_name: str = "sys_menudaten",
        guid: Optional[str] = None,
        no_save: bool = False
    ):
        """
        V2.0: Initialisiert die Business-Logic-Schicht.
        
        DB-Pfad wird aus GCS geholt (gcs.db_path) - zentrale Konfiguration!
        
        Args:
            table_name: Name der Tabelle (Standard: sys_menudaten)
            guid: GUID des Datensatzes (falls None, muss später gesetzt werden)
            no_save: Wenn True, verhindert save_all_values() die Persistierung (für temporäre Strukturen wie Menü-Rendering)
        """
        self.table_name = table_name
        self.guid = guid
        self.no_save = no_save  # Sicherheitsschalter für temporäre Daten
        
        # Basis-Datenbankschicht initialisiert sich selbst aus GCS
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
        
        logger.info(f"PdvmCentralDatenbank initialisiert: {table_name}.{guid} (historisch: {self.historisch}, no_save: {no_save})")

    @classmethod
    def create_with_data(
        cls,
        guid: str,
        daten: Dict[str, Any],
        table_name: str = "sys_menudaten"
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
            Tuple[Any, Optional[float]]: (wert, abdatum) oder (wert, None) wenn nicht historisch
        """
        self._ensure_data_loaded()
        
        if gruppe not in self.data:
            return None, None
        
        gruppe_data = self.data[gruppe]
        if not isinstance(gruppe_data, dict):
            return None, None
        
        if feld not in gruppe_data:
            return None, None
        
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
                            return feld_data[timestamp], best_time
                    except (ValueError, TypeError):
                        continue
                return None, None
            else:
                return None, None
        
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
                            return feld_data[timestamp], latest_time
                    except (ValueError, TypeError):
                        continue
        
        # Direkter Wert - für nicht-historische Daten
        return feld_data, None
    
    def get_field(self, gruppe: str, feld: str) -> Dict[float, Any]:
        """
        Liest ALLE historischen Werte eines Feldes (alle Zeitstempel).
        
        Analog zu get_gruppe(), aber für ein einzelnes Feld.
        Liefert alle historischen Einträge zurück.
        
        Args:
            gruppe: Name der Gruppe
            feld: Name des Feldes
            
        Returns:
            Dict[float, Any]: Dictionary mit allen historischen Werten
                             Format: {timestamp: wert, timestamp2: wert2, ...}
                             Sortiert nach Zeitstempel (neueste zuerst)
                             
        Beispiel:
            >>> db = PdvmCentralDatenbank('persondaten', 'guid-123')
            >>> historie = db.get_field('PERSDATEN', 'FAMILIENNAME')
            >>> for timestamp, wert in historie.items():
            >>>     dt = Pdvm_DateTime("DEU")
            >>>     dt.PdvmDateTime = timestamp
            >>>     print(f"{dt.FormTimeStamp}: {wert}")
        """
        self._ensure_data_loaded()
        
        if gruppe not in self.data:
            logger.warning(f"Gruppe '{gruppe}' nicht gefunden in {self.table_name}.{self.guid}")
            return {}
        
        gruppe_data = self.data[gruppe]
        
        if not isinstance(gruppe_data, dict):
            logger.warning(f"Gruppe '{gruppe}' ist kein Dictionary: {type(gruppe_data)}")
            return {}
        
        if feld not in gruppe_data:
            logger.warning(f"Feld '{feld}' nicht in Gruppe '{gruppe}' gefunden")
            return {}
        
        feld_data = gruppe_data[feld]
        
        # Wenn historische Tabelle: feld_data ist bereits {timestamp: wert} Dictionary
        if isinstance(feld_data, dict):
            # Sortiere nach Zeitstempel (neueste zuerst)
            sorted_data = dict(sorted(feld_data.items(), key=lambda x: float(x[0]), reverse=True))
            return sorted_data
        else:
            # Nicht-historische Tabelle: Nur ein Wert vorhanden
            # Gebe trotzdem als Dictionary zurück (mit Dummy-Timestamp 0)
            logger.warning(f"Feld '{feld}' ist nicht historisch, liefere Einzelwert")
            return {0.0: feld_data}

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
            
        # Gruppe existiert?
        if gruppe not in self.data:
            logger.warning(f"⚠️ Gruppe '{gruppe}' nicht gefunden - erstelle leer")
            self.data[gruppe] = {}
        
        # Feld existiert?
        if feld not in self.data[gruppe]:
            logger.info(f"📋 Feld '{feld}' in Gruppe '{gruppe}' nicht gefunden - erstelle leeres Dict")
            self.data[gruppe][feld] = {}
            return {}
        
        # Direkter Zugriff auf geladene Daten
        feld_data = self.data[gruppe][feld]
        
        # Legacy-Kompatibilität: Prüfe auf 'wert'-Dict-Struktur
        if isinstance(feld_data, dict) and 'wert' in feld_data:
            return feld_data['wert']
            
        return feld_data
    
    def get_value_by_group(self, gruppe: str) -> Dict[str, Any]:
        """
        Holt ALLE Felder einer Gruppe.
        
        Konvertiert automatisch Legacy 'wert'-Struktur zu bereinigten Daten.
        Funktioniert für historische UND nicht-historische Tabellen.
        
        Args:
            gruppe: Name der Gruppe (z.B. 'VERTIKAL', 'GRUND', 'METADATEN')
            
        Returns:
            Dict[str, Any]: Dictionary mit {feld: wert} für alle Felder der Gruppe
                           Legacy-Strukturen werden automatisch konvertiert
            
        Example:
            >>> # Menü-System
            >>> items = db.get_value_by_group('VERTIKAL')
            >>> # items = {'guid-1': {...}, 'guid-2': {...}}
            
            >>> # Metadaten
            >>> metadaten = db.get_value_by_group('METADATEN')
            >>> # metadaten = {'titel': 'Personen', 'beschreibung': '...'}
        """
        self._ensure_data_loaded()
        
        if gruppe not in self.data:
            logger.warning(f"⚠️ Gruppe nicht gefunden: {gruppe}")
            return {}
        
        gruppe_data = self.data[gruppe]
        
        if not isinstance(gruppe_data, dict):
            logger.warning(f"⚠️ Gruppe '{gruppe}' ist kein Dictionary: {type(gruppe_data)}")
            return {}
        
        # Konvertiere Legacy 'wert'-Struktur wenn nötig
        result = {}
        for feld, feld_data in gruppe_data.items():
            if isinstance(feld_data, dict) and 'wert' in feld_data:
                # Legacy-Struktur: {'wert': actual_value, ...}
                result[feld] = feld_data['wert']
            else:
                # Moderne Struktur oder direkte Werte
                result[feld] = feld_data
        
        return result

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
                self.data[gruppe][feld] = {ab_zeit: old_value}  # Float-Key
            
            # WICHTIG: Float-Key verwenden (konsistent mit convert_from_time)
            self.data[gruppe][feld][ab_zeit] = wert
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
        """
        Speichert alle Daten in die Datenbank.
        
        SICHERHEITSSCHALTER: Wenn no_save=True wurde, wird nichts gespeichert.
        Dies verhindert Persistierung von temporären Strukturen (z.B. Menü-Rendering mit Templates).
        """
        if self.no_save:
            logger.debug(f"⚠️ save_all_values() übersprungen (no_save=True) für {self.table_name}.{self.guid}")
            return
        
        if not self.guid:
            raise ValueError("GUID muss gesetzt sein um Daten zu speichern")
        
        # Float-Keys → String-Keys für JSON-Speicherung
        import allgemeines as all
        data_to_save = all.convert_to_time(self.data)
        
        self._database.speichern(self.guid, data_to_save)
        
        logger.info(f"Alle Daten gespeichert für GUID {self.guid}")

    def set_group(self, gruppe: str, gruppe_data: Dict[str, Any]):
        """
        Setzt oder ersetzt eine komplette Gruppe mit allen Feldern.
        
        Args:
            gruppe: Name der Gruppe
            gruppe_data: Dictionary mit allen Feldern der Gruppe
        """
        self._ensure_data_loaded()
        
        if not isinstance(gruppe_data, dict):
            raise ValueError(f"gruppe_data muss ein Dictionary sein, nicht {type(gruppe_data)}")
        
        self.data[gruppe] = gruppe_data.copy()
        logger.debug(f"Gruppe gesetzt: {gruppe} mit {len(gruppe_data)} Feldern")

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
        Template-basierte Initialisierung mit ROOT_CONTROLS aus Template (55555...).
        
        Returns:
            str: Die neue GUID
            
        Raises:
            ValueError: Wenn Template oder ROOT_CONTROLS fehlen
        """
        # 1. Template-GUID (55555...)
        template_guid = '55555555-5555-5555-5555-555555555555'
        
        # 2. Template laden und ROOT_CONTROLS prüfen
        try:
            template_db = PdvmCentralDatenbank(self.table_name, template_guid)
            root_controls = template_db.get_value_by_group('ROOT_CONTROLS')
            
            if not root_controls:
                raise ValueError(f"Template {template_guid} hat keine ROOT_CONTROLS Gruppe!")
            
            # 3. Prüfe ob TABLE und SELF_GUID in ROOT_CONTROLS vorhanden sind
            has_table = any(ctrl.get('name') == 'TABLE' for ctrl in root_controls.values())
            has_self_guid = any(ctrl.get('name') == 'SELF_GUID' for ctrl in root_controls.values())
            
            if not has_table or not has_self_guid:
                raise ValueError(
                    f"ROOT_CONTROLS müssen TABLE und SELF_GUID enthalten!\n"
                    f"Gefunden: TABLE={has_table}, SELF_GUID={has_self_guid}"
                )
            
            logger.info(f"✅ Template validiert: {len(root_controls)} ROOT_CONTROLS")
            
        except Exception as e:
            logger.error(f"❌ Template-Validierung fehlgeschlagen: {e}")
            raise ValueError(f"Kann keinen neuen Datensatz anlegen: {e}")
        
        # 4. Leeren Datensatz in DB anlegen → GUID wird automatisch generiert
        new_guid = self._database.anlegen({})
        logger.info(f"📦 Leerer Datensatz angelegt mit GUID: {new_guid}")
        
        # 5. Instanz auf neue GUID setzen
        self.set_guid(new_guid)
        
        # 6. Stichtag aus GCS holen (für ab_zeit Parameter)
        from pdvm_central_systemsteuerung import get_gcs
        gcs = get_gcs()
        stichtag = gcs.st_inst.PdvmDateTime if gcs else 1001.0
        
        # 7. ROOT-Gruppe dynamisch aus ROOT_CONTROLS aufbauen
        # WICHTIG: ALLE Properties aus ROOT_CONTROLS werden angelegt!
        for control_guid, control_def in root_controls.items():
            prop_name = control_def.get('name')
            if not prop_name:
                logger.warning(f"⚠️ Control {control_guid} hat keinen 'name' - übersprungen")
                continue
            
            # Default-Wert aus Control-Definition holen
            ctrl_type = control_def.get('type', 'string')
            default = control_def.get('default', '')
            
            # Type-basierte Defaults wenn kein expliziter Default vorhanden
            if ctrl_type in ['bool', 'checkbutton']:
                value = default if isinstance(default, bool) else False
            elif ctrl_type == 'int':
                value = default if isinstance(default, int) else 0
            elif ctrl_type == 'float':
                value = default if isinstance(default, float) else 0.0
            else:
                value = default if default else ''
            
            # Property in ROOT-Gruppe setzen (mit Stichtag)
            self.set_value('ROOT', prop_name, value, stichtag)
        
        # 8. TABLE und SELF_GUID mit den RICHTIGEN Werten überschreiben
        self.set_value('ROOT', 'TABLE', self.table_name, stichtag)
        self.set_value('ROOT', 'SELF_GUID', new_guid, stichtag)
        
        logger.info(f"✅ ROOT-Gruppe aufgebaut aus ROOT_CONTROLS:")
        logger.info(f"   TABLE={self.table_name}")
        logger.info(f"   SELF_GUID={new_guid}")
        logger.info(f"   Stichtag={'aus GCS' if stichtag else 'aktuell'}")
        logger.info(f"   Alle Properties: {list(self.data.get('ROOT', {}).keys())}")
        
        # 9. Alles in DB speichern
        self.save_all_values()
        
        logger.info(f"✅ Neuer Datensatz vollständig angelegt und gespeichert: {new_guid}")
        
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

    def get_name(self, guid: Optional[str] = None) -> Optional[str]:
        """
        Liest den 'name' Wert für eine GUID.
        
        Args:
            guid: GUID des Datensatzes (falls None, wird self.guid verwendet)
            
        Returns:
            str|None: Name-Wert oder None wenn nicht gefunden
        """
        target_guid = guid if guid else self.guid
        
        if not target_guid:
            raise ValueError("GUID muss gesetzt sein (self.guid oder Parameter)")
        
        return self._database.get_name(target_guid)

    def set_name(self, name_value: str, guid: Optional[str] = None) -> bool:
        """
        Setzt den 'name' Wert für eine GUID.
        
        Args:
            name_value: Neuer Name-Wert
            guid: GUID des Datensatzes (falls None, wird self.guid verwendet)
            
        Returns:
            bool: True wenn erfolgreich, False wenn GUID nicht existiert
        """
        target_guid = guid if guid else self.guid
        
        if not target_guid:
            raise ValueError("GUID muss gesetzt sein (self.guid oder Parameter)")
        
        return self._database.set_name(target_guid, name_value)
