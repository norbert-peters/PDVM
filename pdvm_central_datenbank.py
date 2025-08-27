# -*- coding: utf-8 -*-
# pdvm_central_datenbank.py

import sqlite3
import json
import logging
from typing import Any, Dict, Optional

from pdvm_datetime import Pdvm_DateTime

logger = logging.getLogger(__name__)


class PdvmCentralDatenbank:
    """
    Zentralisierte Klasse für alle Tabellenzugriffe (historisch oder nicht).
    __init__ lädt den Datensatz (JSON) aus der angegebenen Tabelle und GUID,
    und parst ihn in self.data (als reines Python-dict).
    Methoden wie get_value und get_value_all liefern – falls gewünscht –
    nur den „gültigen" Wert für einen gegebenen Stichtag (bei historischer Tabelle).
    
    ARCHITEKTUR-BEREINIGUNG:
    Diese Klasse bildet immer die Werte aus der Spalte 'daten' zu einer GUID 
    aus der Spalte 'uid' ab. Kein Aufruf an sich selbst darf darin stattfinden,
    um die Klarheit zu bewahren.
    """

    SYSTEM_USER_ID = "00000000-0000-0000-0000-000000000000"

    def __init__(
        self,
        db_name: str = "PdvmManager.db",
        table_name: str = "menudaten",
        guid: Optional[str] = None,
        path: Optional[str] = None,
        source_path: Optional[str] = None
    ):
        """
        Nach der Initialisierung ist jede Instanz eindeutig für (table, guid, path).
        Nach der Zuordnung zu den InputControls (ICs) wird die GUID im Tabellennamen nicht mehr benötigt.
        Um Daten für eine andere GUID bereitzustellen, wird read_guid(guid) verwendet.
        Es dürfen keine doppelten Instanzen für dieselbe (table, guid, path) erzeugt werden.
        """
        self.db_name = db_name
        self.table_name = table_name
        self.path = path
        self.source_path = source_path  # Eindeutiger Pfad für Instanzzuordnung
        logger.info(f"🔹 Initialisiere PdvmCentralDatenbank für {self.table_name} in {self.db_name} (path={self.path}).")
        logger.info(f"🔹 source_path gesetzt auf {self.source_path}.")
        self.guid = guid
        logger.info(f"🔹 GUID gesetzt auf {self.guid}.")
        # Im Konstruktor prüfen wir, ob die Tabelle existiert, und laden (falls GUID gegeben) die Daten
        self._ensure_table_exists()
        # Wenn eine GUID übergeben wurde, lade das JSON‐Diktat in self.data;
        # sonst setze self.data auf {} (für get_value_all o.ä.).
        self.data: Dict[str, Any] = {}
        
        # Historisch-Merkmal IMMER ermitteln - aus PdvmDatenbank-verwalteter Systemsteuerung
        self.historisch = self._ermittle_historisch_kennzeichen()
        logger.info(f"🔹 Historisch-Merkmal ermittelt: {self.historisch}")
        
        if self.guid:
            logger.info(f"🔹 Lade Daten für GUID {self.guid} aus Tabelle {self.table_name}.")
            raw = self._lesen_rogue(self.guid)  # "roh" aus DB als JSON-String bzw. dict
            if raw is None:
                # Falls kein Eintrag, data bleibt leer
                self.data = {}
            else:
                self.data = raw
        # Nach der Initialisierung sollte die Instanz für (table, guid, path) eindeutig sein.
        # Nach der IC-Zuordnung wird die GUID im Tabellennamen nicht mehr benötigt.
        # Für Datenwechsel: self.read_guid(guid)

    def set_data(self, daten: Dict[str, Any], guid: str = None):
        """
        NEUE OPTIMIERUNG: Setzt die Daten direkt ohne erneuten Datenbank-Zugriff.
        
        Diese Methode ermöglicht es, bereits geladene Daten aus einer anderen Quelle
        (z.B. einer Liste aller Datensätze) direkt in diese Instanz zu laden,
        ohne einen neuen Datenbank-Zugriff durchzuführen.
        
        Args:
            daten: Dictionary mit den Daten (entspricht der 'daten' Spalte aus der DB)
            guid: Optional - GUID des Datensatzes (falls nicht bereits gesetzt)
        """
        try:
            # Daten direkt setzen
            if isinstance(daten, dict):
                self.data = daten
            elif isinstance(daten, str):
                # Falls als JSON-String übergeben, parsen
                try:
                    self.data = json.loads(daten)
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Fehler beim JSON-Parsing in set_data: {e}")
                    self.data = {}
            else:
                logger.error(f"❌ Ungültiger Datentyp in set_data: {type(daten)}")
                self.data = {}
            
            # GUID setzen falls übergeben
            if guid:
                self.guid = guid
            
            logger.debug(f"✅ Daten direkt gesetzt für GUID {self.guid} in {self.table_name}")
            logger.debug(f"   📋 Gruppen: {list(self.data.keys()) if isinstance(self.data, dict) else 'Keine Dict-Struktur'}")
            
        except Exception as e:
            logger.error(f"❌ Fehler in set_data: {e}")
            self.data = {} 
    
    def read_guid(self, guid: str) -> Dict[str, Any]:
        """
        Lädt die Daten für eine andere GUID in diese Instanz.
        
        ALTERNATIVE ZU set_data: Verwendet Datenbank-Zugriff (traditionelle Methode)
        """
        try:
            raw = self._lesen_rogue(guid)
            if raw is None:
                self.data = {}
            else:
                self.data = raw
            
            logger.debug(f"✅ Daten für GUID {guid} aus Datenbank geladen")
            return self.data
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der GUID {guid}: {e}")
            self.data = {}
            return {}

    def _ensure_table_exists(self):
        """
        Legt die Tabelle an, falls sie nicht existiert. Das Schema ist:
            uid           TEXT    PRIMARY KEY,
            daten         TEXT    NOT NULL,
            name          TEXT,
            historisch    INTEGER NOT NULL          DEFAULT 0,
            last_modified TEXT    NOT NULL          DEFAULT '',
            source_hash   TEXT                      DEFAULT '',
            stichtag      TEXT    NOT NULL          DEFAULT 9999365.0
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        query = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            uid           TEXT    PRIMARY KEY,
            daten         TEXT    NOT NULL,
            name          TEXT,
            historisch    INTEGER NOT NULL
                                DEFAULT 0,
            last_modified TEXT    NOT NULL
                                DEFAULT '',
            source_hash   TEXT    DEFAULT '',
            stichtag      TEXT    NOT NULL
                                DEFAULT 9999365.0
        )
        """
        cursor.execute(query)
        conn.commit()
        conn.close()

    def _ermittle_historisch_kennzeichen(self) -> bool:
        """
        Ermittelt das historische Kennzeichen direkt aus der aktuellen Tabelle.
        
        ARCHITEKTUR:
        - Jede Tabelle hat eine Spalte 'historisch'
        - SYSTEM_USER_ID-Datensatz in derselben Tabelle enthält das historische Kennzeichen
        - Keine Abhängigkeit zur systemsteuerung-Tabelle
        - Jede Tabelle verwaltet ihr eigenes historisches Kennzeichen
        """
        try:
            # Direkt aus der aktuellen Tabelle den SYSTEM_USER_ID-Datensatz lesen
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(f"SELECT historisch FROM {self.table_name} WHERE uid = ?", (self.SYSTEM_USER_ID,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                historisch = bool(row[0])
                logger.info(f"🔹 Historisch-Kennzeichen für {self.table_name} aus eigenem SYSTEM_USER_ID-Datensatz: {historisch}")
                return historisch
            else:
                logger.info(f"🔹 Kein SYSTEM_USER_ID-Datensatz in {self.table_name} gefunden - verwende False")
                return False
            
        except Exception as e:
            logger.warning(f"🔹 Fehler beim Ermitteln des historisch-Kennzeichens aus {self.table_name}: {e}")
            return False

    def _lesen_rogue(self, guid: str) -> Optional[Any]:
        """
        Liest aus SQLite die Spalte 'daten' (Text) für die gegebene GUID.
        Gibt None zurück, falls nicht existent, sonst den rohen String.
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(f"SELECT daten, name, historisch, last_modified, stichtag FROM {self.table_name} WHERE uid = ?", (guid,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            self.satzbezeichnung = row[1]  # Name aus der DB abgeleitet
            self.guid = guid  # GUID setzen
            self.last_modified = row[3]  # last_modified aus der DB abgeleitet
            self.stichtag = row[4]  # stichtag aus der DB abgeleitet
            # WICHTIG: historisch wird NICHT überschrieben - wurde bereits im Konstruktor ermittelt!
            
            # Prüfen, ob row[0] ein JSON-String ist oder bereits ein dict
            if isinstance(row[0], str):
                try:
                    return json.loads(row[0])  # Versuche, es als JSON zu parsen
                except json.JSONDecodeError:
                    logger.error(f"JSONDecodeError beim Parsen von {row[0]}")
                    return None
            return row[0]

    class DropdownGroup:
        def __init__(self, gruppe, options=None):
            self.gruppe = gruppe
            self.options = options if options is not None else []

    def get_fields(self):
        """
        Gibt alle Gruppen/Felder zurück, die in self.data liegen.
        Für Dropdowns: Gibt eine Liste von Objekten mit Attributen 'gruppe' (Gruppenname) und 'options' (Liste der Optionen).
        """
        if hasattr(self, 'data') and isinstance(self.data, dict):
            result = []
            for gruppe in self.data.keys():
                # Versuche, Optionen für diese Gruppe zu extrahieren (falls vorhanden)
                options = []
                gruppe_dict = self.data.get(gruppe, {})
                if isinstance(gruppe_dict, str):
                    try:
                        gruppe_dict = json.loads(gruppe_dict)
                    except Exception:
                        gruppe_dict = {}
                # Sammle alle Feldnamen als Optionen, falls sinnvoll
                if isinstance(gruppe_dict, dict):
                    options = list(gruppe_dict.keys())
                result.append(self.DropdownGroup(gruppe, options))
            return result
        return []

    def get_value(self, gruppe: str, feld: str, ab_zeit: Optional[float] = None) -> Dict[str, Any]:
        """
        Liefert genau einen Wert für (gruppe, feld). Falls historisch=True, wird:
          - ab_zeit: float oder None
            • wenn None, dann PdvmDateTimeNow() verwendet.
            • sonst jene ab_zeit.
          - Rückgabe‐Format: {"wert": <Skalar>, "ab_zeit": <timestamp>} oder {} falls nicht vorhanden.

        Bei historisch=False wird ab_zeit stets ignoriert – es
        wird dann einfach der aktuell gespeicherte Wert ausgegeben.
        """
        # 1) Falls data leer ist, keine Daten zum Auslesen
        if not self.data:
            logger.debug(f"→ get_value({self.table_name}.{self.guid}, {gruppe}.{feld}, {ab_zeit}): keine Daten geladen.")
            return {}

        # 2) Hole zuerst alles zu dieser Gruppe
        grp_dict = self.data.get(gruppe)
        if grp_dict is None:
            logger.debug(f"→ get_value: Gruppe '{gruppe}' nicht gefunden in {self.table_name}.{self.guid}.")
            return {}

        # Falls grp_dict als JSON‐String abgelegt ist, parsen
        if isinstance(grp_dict, str):
            try:
                grp_dict = json.loads(grp_dict)
            except:
                grp_dict = {}

        # 3) Hole den rohen Feld‐Eintrag
        raw_val = grp_dict.get(feld)
        if raw_val is None:
            logger.debug(f"→ get_value: Feld '{feld}' nicht vorhanden in Gruppe '{gruppe}'.")
            return {}

        # Falls raw_val als JSON‐String abgelegt ist, parsen
        if isinstance(raw_val, str):
            try:
                raw_val = json.loads(raw_val)
            except:
                # Wenn es kein JSON ist, gehen wir davon aus, dass es ein Skalar ist
                raw_val = raw_val

        # 4) Aktuellen Pdvm-Timestamp ermitteln, falls historisch und ab_zeit nicht gesetzt
        if self.historisch:
            if ab_zeit is None:
                dt_inst = Pdvm_DateTime("DEU")
                ab_zeit = dt_inst.PdvmDateTimeNow()
            else:
                ab_zeit = float(ab_zeit)

        # 5) Jetzt unterscheiden wir: historisch vs. nicht historisch
        if self.historisch:
            # raw_val muss ein dict sein, in dem Keys = Zeitstempel (Strings), Werte = Skalar.
            if not isinstance(raw_val, dict):
                # Sollte nicht vorkommen, aber defensiv abfangen
                logger.warning(f"→ get_value: Erwartete Dict (historisch), bekam {type(raw_val)}; gebe als Skalar zurück.")
                return {"wert": raw_val, "ab_zeit": ab_zeit}

            # Schlüssel in raw_val sind Strings repräsentierend Float‐Zeitstempel, z. B. "2025059.00000"
            # Filtere nur jene Zeitstempel, die <= ab_zeit sind
            gültige_zeiten = []
            for ts_str in raw_val.keys():
                try:
                    ts = float(ts_str)
                except:
                    continue
                if ts <= ab_zeit:
                    gültige_zeiten.append(ts)

            if not gültige_zeiten:
                return {}

            # Nimm den max‐Zeitstempel
            max_ts = max(gültige_zeiten)
            max_key = format(max_ts, ".5f")
            wert = raw_val.get(max_key)
            return {"wert": wert, "ab_zeit": max_ts}

        else:
            # NICHT-historisch: raw_val kann:
            #   a) ein reiner Skalar sein, z.B. "Mannheimer"
            #   b) oder (falls versehentlich historisch abgelegt) ein dict:
            if isinstance(raw_val, dict):
                # Dann wählen wir einfach denjenigen Eintrag mit dem maximalen Schlüssel,
                # ohne Rücksicht auf ab_zeit (nur den jeweils aktuellsten Daten).
                try:
                    zeit_keys = [float(ts_str) for ts_str in raw_val.keys()]
                    max_ts = max(zeit_keys)
                    max_key = format(max_ts, ".5f")
                    wert = raw_val.get(max_key)
                    return {"wert": wert, "ab_zeit": max_ts}
                except:
                    # Wenn etwas schiefläuft, geben wir das first-value zurück
                    first_val = next(iter(raw_val.values()), None)
                    return {"wert": first_val, "ab_zeit": 0.0}
            else:
                # Skalar: kein dict
                return {"wert": raw_val, "ab_zeit": 0.0}

    def get_value_all(self, gruppe: str, feld: str) -> Dict[float, Any]:
        """
        Liefert alle historischen Einträge für (gruppe, feld) als Dict:
            { float(zeitstempel) : <wert>, ... }
        Falls nicht historisch, geben wir {0.0: skalar} zurück (damit wenigstens ein Wert da ist).
        """
        if not self.data:
            return {}

        grp_dict = self.data.get(gruppe)
        if grp_dict is None:
            return {}

        if isinstance(grp_dict, str):
            try:
                grp_dict = json.loads(grp_dict)
            except:
                grp_dict = {}

        raw_val = grp_dict.get(feld)
        if raw_val is None:
            return {}

        if isinstance(raw_val, str):
            try:
                raw_val = json.loads(raw_val)
            except:
                # reiner Skalar
                return {0.0: raw_val}

        if isinstance(raw_val, dict):
            out: Dict[float, Any] = {}
            for ts_str, w in raw_val.items():
                try:
                    ts = float(ts_str)
                except:
                    continue
                out[ts] = w
            return out

        # Sonst (Skalar):
        return {0.0: raw_val}

    def lesen(self) -> Dict[str, Any]:
        """
        Liest mit self.guid den gesamten 'daten'-Eintrag.
        Gibt ein Dict zurück, in dem Top-Level‐Keys die Gruppennamen sind.
        """
        return self.data or {}

    def lesen_alle(self) -> Optional[list]:
        """
        Liest **alle** Zeilen (alle GUIDs) aus der Tabelle self.table_name.
        Verwendet PdvmDatenbank für den Datenzugriff (statt direkter SQL-Abfragen).
        Gibt eine Liste von Diktaten zurück: jeweils
          {"uid": <guid>, "<GRUPPE1>": <Daten-Dict oder JSON-String>, ...}
        """
        # Über PdvmDatenbank alle Datensätze laden (statt direkter SQL-Zugriffe)
        from pdvm_datenbank import PdvmDatenbank
        data_db = PdvmDatenbank(db_name=self.db_name, table_name=self.table_name)
        rows = data_db.lesen_alle()
        if not rows:
            logger.warning(f"⚠️ Keine Datensätze in Tabelle {self.table_name} gefunden")
            return []

        result = []
        for row in rows:
            # Spalte "daten" liegt in row["daten"] als JSON-String oder dict
            raw = row.get("daten", {})
            if isinstance(raw, str):
                try:
                    data_dict = json.loads(raw)
                except:
                    data_dict = {}
            else:
                data_dict = raw
            # Wir ersetzen row["daten"] durch den gepackten Dict-Inhalt:
            entry = {"uid": row["uid"], **data_dict}
            result.append(entry)
        return result
    
    def lesen_alle_ohne_system(self, limit: int = None) -> Optional[list]:
        """
        NEUE OPTIMIERUNG: Liest alle Datensätze außer SYSTEM_USER_ID.
        
        Diese Methode ist optimal für den ViewDatenManager, da sie:
        1. Alle relevanten Datensätze in einem Zug lädt
        2. SYSTEM_USER_ID automatisch filtert
        3. Optional ein Limit anwendet für Performance
        4. Die Daten bereits aufbereitet zurückgibt
        
        Args:
            limit: Maximale Anzahl Datensätze (None = alle)
            
        Returns:
            Liste von aufbereiteten Datensätzen:
            [{"uid": guid, "daten_dict": {...}, "raw_data": row}, ...]
        """
        try:
            # Über PdvmDatenbank alle Datensätze laden
            from pdvm_datenbank import PdvmDatenbank
            data_db = PdvmDatenbank(db_name=self.db_name, table_name=self.table_name)
            rows = data_db.lesen_alle()
            
            if not rows:
                logger.warning(f"⚠️ Keine Datensätze in Tabelle {self.table_name} gefunden")
                return []

            result = []
            processed_count = 0
            
            for row in rows:
                # SYSTEM_USER_ID überspringen
                if row.get("uid") == self.SYSTEM_USER_ID:
                    continue
                
                # Limit prüfen
                if limit and processed_count >= limit:
                    break
                
                # Daten aufbereiten
                raw = row.get("daten", {})
                if isinstance(raw, str):
                    try:
                        data_dict = json.loads(raw)
                    except json.JSONDecodeError:
                        logger.warning(f"⚠️ JSON-Parsing-Fehler für GUID {row.get('uid')}")
                        data_dict = {}
                else:
                    data_dict = raw
                
                # Aufbereiteter Eintrag
                entry = {
                    "uid": row["uid"],
                    "daten_dict": data_dict,  # Aufbereitete Daten für set_data()
                    "raw_data": row          # Original-Row-Daten falls benötigt
                }
                result.append(entry)
                processed_count += 1
            
            logger.info(f"✅ {len(result)} Datensätze (ohne SYSTEM_ID) aus {self.table_name} geladen{f' (limitiert auf {limit})' if limit else ''}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden aller Datensätze aus {self.table_name}: {e}")
            return []

    def speichern(self, guid: str, daten: Dict[str, Any]):
        """
        Speichert oder aktualisiert den Eintrag (guid, daten).
        Verwendet PdvmDatenbank für den Datenzugriff (statt direkter SQL-Abfragen).
        'daten' ist ein Python-Dict, das wir in JSON umwandeln und in Tabelle schreiben.
        """
        # Über PdvmDatenbank speichern (statt direkter SQL-Zugriffe)
        from pdvm_datenbank import PdvmDatenbank
        data_db = PdvmDatenbank(db_name=self.db_name, table_name=self.table_name)
        data_db.speichern(guid, daten)
        logger.debug(f"✅ Datensatz {guid} erfolgreich in {self.table_name} gespeichert")

    def loeschen(self, guid: str):
        """
        Löscht einen Datensatz anhand der GUID.
        Verwendet PdvmDatenbank für den Datenzugriff (statt direkter SQL-Abfragen).
        """
        # Über PdvmDatenbank löschen (statt direkter SQL-Zugriffe)
        from pdvm_datenbank import PdvmDatenbank
        data_db = PdvmDatenbank(db_name=self.db_name, table_name=self.table_name)
        data_db.loeschen(guid)
        logger.debug(f"✅ Datensatz {guid} erfolgreich aus {self.table_name} gelöscht")

    def save_values(self):
        """
        Speichert (update) die Instanz in der Datenbank.
        """
        logging.info(f"🔹 Datensatz mit GUID {self.guid} wird in der Datenbank gespeichert.")
        self.speichern(self.guid, self.data)
        logging.info(f"🔹 gespeicherte Daten: {json.dumps(self.data, indent=4)} ")

    def _normalize_historic_keys(self, gruppe: str, feld: str):
        """
        Normalisiert alle Zeitstempel-Keys im Dict auf 5 Nachkommastellen.
        NUTZT ZENTRALE PdvmDateTime String-Formatierung für Konsistenz!
        """
        if gruppe in self.data and feld in self.data[gruppe] and isinstance(self.data[gruppe][feld], dict):
            orig_dict = self.data[gruppe][feld]
            norm_dict = {}
            for k, v in list(orig_dict.items()):
                try:
                    kf = float(k)
                    # ZENTRALE FORMATIERUNG: Verwende PdvmDateTime für konsistente String-Formatierung
                    temp_dt = Pdvm_DateTime("DEU")
                    temp_dt.PdvmDateTime = kf
                    norm_key = temp_dt.PdvmDateTimeStr
                except Exception:
                    norm_key = str(k)
                if norm_key not in norm_dict:
                    norm_dict[norm_key] = v
                if norm_key != k:
                    del orig_dict[k]
            self.data[gruppe][feld] = norm_dict

    def set_value(self, gruppe: str, feld: str, wert: Any, ab_zeit: Optional[float] = None):
        """
        Zentrale Methode zum Setzen eines Werts in self.data.
        - Das UI/der Manager übergibt IMMER wert + ab_zeit (float, z.B. 1001.0 für nicht-historische Felder).
        - Die Entscheidung, ob ab_zeit verwendet wird, liegt ausschließlich hier:
            * Wenn self.historisch==True: Wert wird unter ab_zeit (als Key, 5 Nachkommastellen) gespeichert.
            * Wenn self.historisch==False: Wert wird als Skalar gespeichert, ab_zeit wird ignoriert.
        - Persistiert wird erst mit save_values().
        """
        print(f"[DEBUG] PdvmCentralDatenbank.set_value: gruppe={gruppe}, feld={feld}, wert={wert}, ab_zeit={ab_zeit}, self_id={id(self)}")
        
        # Prüfe ob der Wert tatsächlich geändert wird
        old_value = None
        value_changed = False
        
        # 1) Gruppe anlegen, falls nicht vorhanden
        if gruppe not in self.data or self.data.get(gruppe) is None:
            self.data[gruppe] = {}
        
        # 2) Historischer Zweig
        if self.historisch:
            # Falls ab_zeit nicht übergeben, aktuellen Pdvm‒Timestamp verwenden
            if ab_zeit is None:
                # ZENTRALE UTILITIES: Verwende PdvmDateTimeUtils Properties direkt
                from pdvm_datetime import PdvmDateTimeUtils
                ab_zeit = PdvmDateTimeUtils.PdvmDateTimeNow
                ts_key = PdvmDateTimeUtils.PdvmDateTimeNowStr
            else:
                ab_zeit = float(ab_zeit)
                # ZENTRALE FORMATIERUNG: Erstelle temporäres PdvmDateTime für einheitliche String-Formatierung
                temp_dt = Pdvm_DateTime("DEU")
                temp_dt.PdvmDateTime = ab_zeit
                ts_key = temp_dt.PdvmDateTimeStr
            
            # Feld‒Dict anlegen, falls nicht vorhanden
            if feld not in self.data[gruppe] or not isinstance(self.data[gruppe][feld], dict):
                self.data[gruppe][feld] = {}
            self._normalize_historic_keys(gruppe, feld)
            
            # Prüfe auf Änderung
            old_value = self.data[gruppe][feld].get(ts_key)
            value_changed = old_value != wert
            
            print(f"[DEBUG] PdvmCentralDatenbank.set_value: ZENTRALE FORMATIERUNG ab_zeit={ab_zeit} -> ts_key='{ts_key}'")
            print(f"[DEBUG] PdvmCentralDatenbank.set_value: Vorher self.data[{gruppe}][{feld}]={self.data[gruppe][feld]}")
            self.data[gruppe][feld][ts_key] = wert
            print(f"[DEBUG] PdvmCentralDatenbank.set_value: Nachher self.data[{gruppe}][{feld}]={self.data[gruppe][feld]}")
        
        # 3) Nicht-historischer Zweig
        else:
            # Prüfe auf Änderung
            old_value = self.data[gruppe].get(feld)
            value_changed = old_value != wert
            # ab_zeit wird ignoriert, Wert als Skalar gespeichert
            print(f"[DEBUG] PdvmCentralDatenbank.set_value: (nicht historisch) Vorher self.data[{gruppe}][{feld}]={self.data[gruppe].get(feld, 'N/A')}")
            self.data[gruppe][feld] = wert
            print(f"[DEBUG] PdvmCentralDatenbank.set_value: (nicht historisch) Nachher self.data[{gruppe}][{feld}]={self.data[gruppe][feld]}")
            # Logging für ExpertMode-Änderung
            if feld == "ExpertMode":
                logger.debug(f"[ExpertMode] set_value: Gruppe={gruppe}, Wert={wert}, old_value={old_value}")
        
        # Dirty-Flag setzen wenn sich der Wert geändert hat
        if value_changed:
            self._dirty = True
            print(f"[DEBUG] PdvmCentralDatenbank.set_value: Dirty-Flag gesetzt für {gruppe}.{feld} (alt: {old_value}, neu: {wert})")
        else:
            print(f"[DEBUG] PdvmCentralDatenbank.set_value: Kein Wert-Änderung für {gruppe}.{feld} (bleibt: {wert})")

    def read_guid(self, guid: str):
        """
        Liest die Daten für die angegebene GUID und setzt self.guid und self.data entsprechend neu.
        Lädt nur dann aus der Datenbank, wenn sich die GUID tatsächlich geändert hat.
        """
        old_guid = self.guid
        if old_guid == guid:
            print(f"[DEBUG] PdvmCentralDatenbank.read_guid: Tabelle={self.table_name}, GUID unverändert ({guid}), kein Reload nötig")
            return
        
        self.guid = guid
        self.data = self._lesen_rogue(guid) or {}
        # Dirty-Flag zurücksetzen nach erfolgreichem Laden
        self._dirty = False
        print(f"[DEBUG] PdvmCentralDatenbank.read_guid: Tabelle={self.table_name}, alte GUID={old_guid}, neue GUID={guid}, geladene Daten={self.data}, dirty=False")

    def lesen_gruppe(self, gruppe: str) -> dict:
        """
        Gibt die Daten einer bestimmten Gruppe unter der aktuellen GUID zurück.
        """
        return self.data.get(gruppe, {})

    def speichern_gruppe(self, gruppe: str, daten: dict):
        """
        Speichert nur die angegebene Gruppe unter der aktuellen GUID.
        """
        self.data[gruppe] = daten
        self.save_values()

    def get_viewtable_guid(self, gruppe: str, feld: str) -> str:
        """
        Gibt die GUID zurück, die im angegebenen Gruppe/Feld als Verweis gespeichert ist.
        Liefert None, wenn kein Verweis existiert.
        """
        gruppe_data = self.data.get(gruppe, {})
        feld_data = gruppe_data.get(feld, {})
        if isinstance(feld_data, dict) and feld_data:
            # Nimm den Wert mit dem höchsten Zeitstempel (wie bei historischen Feldern)
            max_key = max(feld_data.keys(), key=lambda k: float(k))
            return feld_data[max_key]
        elif isinstance(feld_data, str):
            return feld_data
        return None

    def delete_value(self, gruppe: str, feld: str, ab_zeit: float) -> bool:
        """
        Löscht einen historischen Wert (Key = Zeitstempel) aus der Datenstruktur im RAM.
        Persistiert wird erst mit save_values().
        """
        if gruppe not in self.data:
            return False
        feld_dict = self.data[gruppe].get(feld)
        if not isinstance(feld_dict, dict):
            return False
        ts_key = format(float(ab_zeit), ".5f")
        if ts_key in feld_dict:
            del feld_dict[ts_key]
            if feld_dict:
                self.data[gruppe][feld] = feld_dict
            else:
                self.data[gruppe][feld] = ""
            return True
        return False

    def get_static_value(self, gruppe: str, feld: str):
        """
        Gibt den Wert für (gruppe, feld) direkt zurück (ohne Zeitstempel-Logik).
        Liefert None, falls nicht vorhanden.
        """
        if not self.data:
            return None
        grp_dict = self.data.get(gruppe)
        if grp_dict is None:
            return None
        if isinstance(grp_dict, str):
            try:
                grp_dict = json.loads(grp_dict)
            except:
                grp_dict = {}
        return grp_dict.get(feld)

    def is_dirty(self) -> bool:
        """
        Gibt True zurück, wenn die Instanz ungespeicherte Änderungen hat.
        """
        return getattr(self, '_dirty', False)

    def save(self):
        """
        Speichert die aktuellen Änderungen der Instanz in die Datenbank.
        """
        if hasattr(self, '_dirty') and self._dirty:
            # Echte Persistenz-Logik einbauen
            if self.guid:
                self.save_values()  # Verwende die existierende save_values Methode
                self._dirty = False
                logger.info(f"[PdvmCentralDatenbank] Instanz für GUID {self.guid} erfolgreich gespeichert.")
            else:
                logger.warning(f"[PdvmCentralDatenbank] Kann nicht speichern - keine GUID gesetzt.")
        else:
            logger.debug(f"[PdvmCentralDatenbank] Keine Änderungen zu speichern für GUID {self.guid}.")

#    def reload_instance_from_db(self, table: str, guid: str):
#        """
#        Lädt die Instanz mit der angegebenen GUID neu aus der Datenbank.
#        """
#        logger.info(f"[PdvmCentralDatenbank] Reload aus DB für {table}.{guid}")
#        if guid:
#            raw = self._lesen_rogue(guid)
#            if raw is not None:
#                self.data = raw
#                self.guid = guid
#                self._dirty = False
