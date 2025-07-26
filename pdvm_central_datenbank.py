# -*- coding: utf-8 -*-
# pdvm_central_datenbank.py

import sqlite3
import json
import logging
from typing import Any, Dict, Optional

from pd_datetime import Pdvm_DateTime

logger = logging.getLogger(__name__)


class PdvmCentralDatenbank:
    """
    Zentralisierte Klasse für alle Tabellenzugriffe (historisch oder nicht).
    __init__ lädt den Datensatz (JSON) aus der angegebenen Tabelle und GUID,
    und parst ihn in self.data (als reines Python-dict).
    Methoden wie get_value und get_value_all liefern – falls gewünscht –
    nur den „gültigen“ Wert für einen gegebenen Stichtag (bei historischer Tabelle).
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
        
        # Historisch-Merkmal aus SYSTEM_USER_ID-Datensatz laden (falls keine GUID gesetzt)
        if not self.guid:
            logger.info(f"🔹 Keine GUID gesetzt - lade historisch-Merkmal aus SYSTEM_USER_ID {self.SYSTEM_USER_ID}")
            # Temporäre Verbindung nur für historisch-Merkmal
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(f"SELECT historisch FROM {self.table_name} WHERE uid = ?", (self.SYSTEM_USER_ID,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.historisch = bool(row[0])
                logger.info(f"🔹 Historisch-Merkmal aus System-Datensatz: {self.historisch}")
            else:
                self.historisch = False  # Fallback
                logger.info(f"🔹 Kein System-Datensatz gefunden - historisch=False (Fallback)")
        
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
#        logger.info(f"🔹 Lesen aus {self.table_name} für GUID {guid}.")
#        logger.info(f"🔹 gelesene Daten: {row[0]}")
#        logger.info(f"🔹 gelesen Namen: {row[1]}")
#        logger.info(f"🔹 gelesen HIST: {row[2]}")
#        logger.info(f"🔹 gelesen last_modified: {row[3]}")
#        logger.info(f"🔹 gelesen Stichtag: {row[4]}")
        if row:
            self.satzbezeichnung = row[1]  # Name aus der DB abgeleitet
            self.guid = guid  # GUID setzen
            self.last_modified = row[3]  # last_modified aus der DB abgeleitet
            self.stichtag = row[4]  # stichtag aus der DB abgeleitet
            self.historisch = bool(row[2])  # historisch aus der DB abgeleitet
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

        # --- TRACE: Logge den kompletten Feldinhalt, Stichtag und die spätere Ausgabe ---
#        logger.info(f"[TRACE:get_value] {self.table_name}.{self.guid} Gruppe={gruppe} Feld={feld} ab_zeit={ab_zeit} raw_val={raw_val}")

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
        try:
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
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Lesen aller Datensätze aus {self.table_name}: {e}")
            return []

    def speichern(self, guid: str, daten: Dict[str, Any]):
        """
        Speichert oder aktualisiert den Eintrag (guid, daten).
        Verwendet PdvmDatenbank für den Datenzugriff (statt direkter SQL-Abfragen).
        'daten' ist ein Python-Dict, das wir in JSON umwandeln und in Tabelle schreiben.
        """
        try:
            # Über PdvmDatenbank speichern (statt direkter SQL-Zugriffe)
            from pdvm_datenbank import PdvmDatenbank
            
            data_db = PdvmDatenbank(db_name=self.db_name, table_name=self.table_name)
            data_db.speichern(guid, daten)
            
            logger.debug(f"✅ Datensatz {guid} erfolgreich in {self.table_name} gespeichert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern von Datensatz {guid}: {e}")
            raise

    def loeschen(self, guid: str):
        """
        Löscht einen Datensatz anhand der GUID.
        Verwendet PdvmDatenbank für den Datenzugriff (statt direkter SQL-Abfragen).
        """
        try:
            # Über PdvmDatenbank löschen (statt direkter SQL-Zugriffe)
            from pdvm_datenbank import PdvmDatenbank
            
            data_db = PdvmDatenbank(db_name=self.db_name, table_name=self.table_name)
            data_db.loeschen(guid)
            
            logger.debug(f"✅ Datensatz {guid} erfolgreich aus {self.table_name} gelöscht")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Löschen von Datensatz {guid}: {e}")
            raise

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
        """
        if gruppe in self.data and feld in self.data[gruppe] and isinstance(self.data[gruppe][feld], dict):
            orig_dict = self.data[gruppe][feld]
            norm_dict = {}
            for k, v in list(orig_dict.items()):
                try:
                    kf = float(k)
                    norm_key = format(kf, ".5f")
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
                dt_inst = Pdvm_DateTime("DEU")
                ab_zeit = dt_inst.PdvmDateTimeNow()
            else:
                ab_zeit = float(ab_zeit)
            # Feld‒Dict anlegen, falls nicht vorhanden
            if feld not in self.data[gruppe] or not isinstance(self.data[gruppe][feld], dict):
                self.data[gruppe][feld] = {}
            self._normalize_historic_keys(gruppe, feld)
            ts_key = format(ab_zeit, ".5f")
            
            # Prüfe auf Änderung
            old_value = self.data[gruppe][feld].get(ts_key)
            value_changed = old_value != wert
            
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

    def set_viewtable_guid(self, gruppe: str, feld: str, guid: str, ab_zeit: float = None):
        """
        Setzt die GUID als Verweis im angegebenen Gruppe/Feld (mit optionalem Ab-Datum).
        """
        if gruppe not in self.data or self.data.get(gruppe) is None:
            self.data[gruppe] = {}
        if ab_zeit is None:
            from pd_datetime import Pdvm_DateTime
            ab_zeit = Pdvm_DateTime("DEU").PdvmDateTimeNow()
        ts_key = format(float(ab_zeit), ".5f")
        if feld not in self.data[gruppe] or not isinstance(self.data[gruppe][feld], dict):
            self.data[gruppe][feld] = {}
        self.data[gruppe][feld][ts_key] = guid
        self.save_values()

    def get_viewtables(self, tabelle: str, gruppe: str, guid: str) -> dict:
        """
        Sucht in der angegebenen Tabelle/Gruppe für die gegebene GUID alle Felder,
        die ein '-' im Namen haben (viewtable-Verweise), und gibt ein Dict zurück:
        { (table, gruppe): guid }
        Beispiel: 'FINANZDATEN-KONTO' -> {'finanzdaten', 'KONTO', <guid>}
        """
        # Instanz für die gewünschte Tabelle/GUID erzeugen
        inst = PdvmCentralDatenbank(db_name=self.db_name, table_name=tabelle, guid=guid)
        gruppe_data = inst.data.get(gruppe, {})
        result = {}
        for feld, val in gruppe_data.items():
            if '-' in feld:
                table, grp = feld.split('-', 1)
                # GUID aus Feld extrahieren (historisch: dict, sonst direkt)
                if isinstance(val, dict) and val:
                    max_key = max(val.keys(), key=lambda k: float(k))
                    ref_guid = val[max_key]
                elif isinstance(val, str):
                    ref_guid = val
                else:
                    ref_guid = None
                if ref_guid:
                    result[(table.lower(), grp.upper())] = ref_guid
        return result

    def get_abdatum_instance(self, gruppe: str, feld: str, ab_zeit: Optional[float] = None) -> Pdvm_DateTime:
        """
        Gibt eine temporäre Pdvm_DateTime-Instanz für das aktuelle Ab-Datum des Feldes zurück.
        Liest immer den aktuellen Wert aus der Instanz (stichtagsgenau).
        """
        value_dict = self.get_value(gruppe, feld, ab_zeit)
        abdatum = value_dict.get("ab_zeit", 1001.0)
        ab_inst = Pdvm_DateTime("DEU")
        ab_inst.PdvmDateTime = float(abdatum)
        return ab_inst

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
        TODO: Implementiere echte Dirty-Logik!
        """
        # Hier ggf. mit einem echten Dirty-Flag arbeiten
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

    def reload_instance_from_db(self, table: str, guid: str):
        """
        Lädt die Instanz mit der angegebenen GUID neu aus der Datenbank.
        TODO: Implementiere echte Reload-Logik!
        """
        logger.info(f"[PdvmCentralDatenbank] Reload aus DB für {table}.{guid} (Platzhalter).")
        # Hier echte Reload-Logik einbauen
        if guid:
            raw = self._lesen_rogue(guid)
            if raw is not None:
                self.data = raw
                self.guid = guid
                self._dirty = False

    def get_value_view(self, view_config: dict, stichtag: Optional[float] = None) -> list:
        """
        Zentrale View-Methode: Liest alle Datensätze der Tabelle und löst sie 
        basierend auf view_config in eine flache Struktur auf.
        
        Erstellt IMMER eine vollständige Basis mit:
        - Original-Spalten für alle Felder (FELD_original)
        - Show-Spalten für alle Felder (FELD_show) 
        - YMD/Alter-Spalten für alle Datumsfelder (automatisch bei type:date)
        
        Args:
            view_config: View-Konfiguration mit metadata und Feldliste
            stichtag: Optionaler Stichtag für historische Daten
            
        Returns:
            Liste von Dicts mit aufgelösten Feldwerten: [{'_guid': '...', 'FELD1': 'Wert', ...}, ...]
        """
        try:
            if stichtag is None:
                from pd_datetime import Pdvm_DateTime
                dt_inst = Pdvm_DateTime("DEU")
                stichtag = dt_inst.PdvmDateTimeNow()
            
            # 1. View-Konfiguration extrahieren
            if not view_config or "metadata" not in view_config:
                logger.error("❌ Ungültige view_config - metadata fehlt")
                return []
            
            table_name = view_config["ROOT"]["view_table"]
            felder = view_config["metadata"][table_name]["felder"]
            
            # 2. Alle Datensätze der VIEW-TABELLE laden (EINMAL!)
            from pdvm_datenbank import PdvmDatenbank
            data_db = PdvmDatenbank(db_name=self.db_name, table_name=table_name)
            alle_datensaetze = data_db.lesen_alle()
            
            if not alle_datensaetze:
                logger.warning(f"📊 Keine Datensätze in Tabelle {table_name} gefunden")
                return []
            
            # WICHTIG: historisch-Flag für View-Tabelle ermitteln (aus erstem Datensatz)
            if alle_datensaetze and len(alle_datensaetze) > 0:
                first_row = alle_datensaetze[0]
                # historisch ist normalerweise in row["historisch"] gespeichert, falls PdvmDatenbank es liefert
                self.historisch = bool(first_row.get("historisch", False))
            else:
                self.historisch = False  # Fallback
            
            # Spalten-Sichtbarkeit vorbereiten (falls nicht vorhanden, Standard verwenden)
            if "column_visibility" not in view_config:
                view_config["column_visibility"] = self.get_default_column_visibility(view_config)
                logger.info("📊 Standard-Spalten-Sichtbarkeit angewendet")
            
            logger.info(f"📊 get_value_view: Verarbeite {len(alle_datensaetze)} Datensätze für {len(felder)} Felder")
            
            # 3. Für jeden Datensatz alle gewünschten Felder auflösen
            result = []
            for row_data in alle_datensaetze:
                guid = row_data.get("uid")
                if not guid:
                    continue
                
                # JSON-Daten aus der bereits geladenen Zeile direkt in self.data setzen (SUPER-OPTIMIERUNG!)
                raw_data = row_data.get("daten", {})
                if isinstance(raw_data, str):
                    try:
                        self.data = json.loads(raw_data)
                    except:
                        self.data = {}
                else:
                    self.data = raw_data
                
                # Feldwerte für diesen Datensatz sammeln - VOLLSTÄNDIGE BASIS erstellen
                record = {"uid": guid, "_guid": guid}
                
                # IMMER alle Felder mit vollständiger Basis verarbeiten
                for feld_config in felder:
                    feld_name = feld_config["feld"]
                    feld_gruppe = feld_config.get("gruppe", "ROOT")  # Gruppe aus view_config verwenden
                    
                    # WICHTIG: Gruppen und Felder sind in der DB immer in GROSSBUCHSTABEN!
                    feld_gruppe_upper = feld_gruppe.upper()
                    feld_name_upper = feld_name.upper()
                    
                    # Direkter Zugriff über self.get_value mit bekannter Gruppe (SUPER-OPTIMIERT!)
                    result_dict = self.get_value(feld_gruppe_upper, feld_name_upper, stichtag)
                    wert = result_dict.get("wert") if result_dict else None
                    
                    # IMMER Original/Show-Spalten erstellen (vollständige Basis)
                    record[f"{feld_name}_original"] = wert
                    show_value = self._prepare_show_value_v3(wert, feld_config, stichtag)
                    record[f"{feld_name}_show"] = show_value
                    
                    # Standard-Feld erhält Show-Wert (für Kompatibilität)
                    record[feld_name] = show_value
                
                # IMMER YMD/Alter-Spalten für alle Datumsfelder erstellen
                self._add_date_columns_v3(record, felder, stichtag)
                
                # Spalten-Sichtbarkeit basierend auf view_config anwenden
                record = self._apply_column_visibility(record, view_config)
                
                result.append(record)
            
            logger.info(f"✅ {len(result)} Datensätze für View verarbeitet (Stichtag: {stichtag})")
            logger.info("� OPTIMIERT: Nur 1x Datenbank-Zugriff für alle Datensätze")
            logger.info("�🔧 Vollständige Basis: Original/Show-Spalten für alle Felder")
            logger.info("📅 Vollständige Basis: YMD/Alter-Spalten für alle Datumsfelder")
            logger.info("⚡ Kein doppeltes Lesen: JSON-Daten direkt aus geladenen Zeilen verwendet")
            return result
            
        except Exception as e:
            logger.error(f"❌ Fehler in get_value_view: {e}")
            return []

    # ====== ZENTRALE DROPDOWN-FUNKTIONALITÄT ======
    
    def get_dropdown_options_from_data(self, table_name: str, field_name: str, dropdown_config: dict) -> Dict[str, str]:
        """
        Zentrale Methode: Erzeugt Dropdown-Optionen basierend auf tatsächlich in der Tabelle vorhandenen Werten.
        
        Args:
            table_name: Name der Tabelle (z.B. "persondaten")
            field_name: Name des Feldes (z.B. "ANREDE") 
            dropdown_config: Konfiguration mit "table", "key", "value" für Übersetzungen
            
        Returns:
            Dict[str, str]: {key: display_text} Mapping aller in den Daten vorkommenden Werte
        """
        options = {}
        
        try:
            # 1. Alle tatsächlich vorhandenen Werte aus der Tabelle sammeln
            unique_values = self._collect_unique_values_from_table(table_name, field_name)
            logger.info(f"🔍 Gefundene eindeutige Werte in {table_name}.{field_name}: {unique_values}")
            
            if not unique_values:
                logger.warning(f"⚠️ Keine Werte für {field_name} in {table_name} gefunden")
                return options
            
            # 2. Übersetzungen für diese Werte laden
            dropdown_table = dropdown_config.get("table", "dropdowndaten")
            dropdown_key = dropdown_config.get("key")
            dropdown_group = dropdown_config.get("value", "ANREDE")
            
            if not dropdown_key:
                logger.warning(f"⚠️ Kein dropdown_key konfiguriert für {field_name}")
                # Fallback: Werte ohne Übersetzung verwenden
                for value in unique_values:
                    if value is not None:
                        options[str(value)] = str(value)
                return options
            
            # 3. Dropdown-Daten laden
            dropdown_db = PdvmCentralDatenbank(
                db_name=self.db_name,
                table_name=dropdown_table,
                guid=dropdown_key
            )
            
            dropdown_data = dropdown_db.lesen()
            translations = {}
            
            if dropdown_data and "ROOT" in dropdown_data:
                group_data = dropdown_data["ROOT"].get(dropdown_group, {})
                values = group_data.get("werte", [])
                
                # Übersetzungs-Mapping erstellen
                for entry in values:
                    key = entry.get("key", "")
                    display = entry.get("de", entry.get("en", key))
                    if key:
                        translations[key] = display
                
                logger.info(f"🔍 Übersetzungen geladen für {dropdown_group}: {len(translations)} Einträge")
            
            # 4. Nur die tatsächlich vorhandenen Werte mit Übersetzungen zurückgeben
            for value in unique_values:
                if value is not None:
                    str_value = str(value)
                    display_value = translations.get(str_value, str_value)
                    options[str_value] = display_value
                    logger.debug(f"🔍 Dropdown-Option: '{str_value}' → '{display_value}'")
            
            logger.info(f"✅ Dropdown-Optionen für {field_name} erstellt: {len(options)} Optionen basierend auf echten Daten")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der Dropdown-Optionen für {field_name}: {e}")
            # Fallback: Leeres Dict
            
        return options

    def _collect_unique_values_from_table(self, table_name: str, field_name: str) -> set:
        """
        Sammelt alle eindeutigen Werte für ein Feld aus einer Tabelle.
        Verwendet PdvmDatenbank für den Datenzugriff (statt direkter SQL-Abfragen).
        
        Args:
            table_name: Name der Tabelle
            field_name: Name des Feldes
            
        Returns:
            set: Alle eindeutigen Werte (ohne None/leere Strings)
        """
        unique_values = set()
        
        try:
            # Über PdvmDatenbank alle Datensätze laden (statt direkter SQL-Zugriffe)
            from pdvm_datenbank import PdvmDatenbank
            
            data_db = PdvmDatenbank(db_name=self.db_name, table_name=table_name)
            rows = data_db.lesen_alle()
            
            if not rows:
                logger.warning(f"⚠️ Keine Datensätze in Tabelle {table_name} gefunden")
                return unique_values
            
            logger.debug(f"🔍 Analysiere {len(rows)} Datensätze aus {table_name}")
            
            for row in rows:
                try:
                    # 'daten' Spalte extrahieren und JSON parsen
                    json_data = row.get('daten', '')
                    if isinstance(json_data, str):
                        data = json.loads(json_data)
                    else:
                        data = json_data
                    
                    # Durch alle Gruppen suchen
                    for group_name, group_data in data.items():
                        if isinstance(group_data, dict) and field_name in group_data:
                            field_data = group_data[field_name]
                            
                            if isinstance(field_data, dict):
                                # Historische Daten: Alle Werte aus dem Dict extrahieren
                                for timestamp, value in field_data.items():
                                    if value is not None and value != "":
                                        unique_values.add(value)
                            else:
                                # Direkter Wert
                                if field_data is not None and field_data != "":
                                    unique_values.add(field_data)
                    
                except (json.JSONDecodeError, TypeError) as e:
                    logger.debug(f"🔍 Überspringe ungültigen Datensatz: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Sammeln der Werte aus {table_name}: {e}")
        
        # None-Werte entfernen
        unique_values.discard(None)
        unique_values.discard("")
        
        logger.debug(f"🔍 Eindeutige Werte gefunden: {unique_values}")
        return unique_values

    def get_dropdown_display_value(self, raw_value: str, field_name: str, dropdown_config: dict) -> str:
        """
        Übersetzt einen Raw-Wert zu seinem Display-Text für Dropdown-Felder.
        
        Args:
            raw_value: Der rohe Wert aus der Datenbank
            field_name: Name des Feldes
            dropdown_config: Dropdown-Konfiguration
            
        Returns:
            str: Übersetzter Display-Text oder Raw-Wert als Fallback
        """
        if not raw_value:
            return ""
        
        try:
            dropdown_table = dropdown_config.get("table", "dropdowndaten")
            dropdown_key = dropdown_config.get("key")
            dropdown_group = dropdown_config.get("value", "ANREDE")
            
            if not dropdown_key:
                return str(raw_value)
            
            # Dropdown-Daten laden
            dropdown_db = PdvmCentralDatenbank(
                db_name=self.db_name,
                table_name=dropdown_table,
                guid=dropdown_key
            )
            
            dropdown_data = dropdown_db.lesen()
            
            if dropdown_data and "ROOT" in dropdown_data:
                group_data = dropdown_data["ROOT"].get(dropdown_group, {})
                values = group_data.get("werte", [])
                
                for entry in values:
                    key = entry.get("key", "")
                    display = entry.get("de", entry.get("en", key))
                    if key == str(raw_value):
                        logger.debug(f"🔍 Dropdown übersetzt: '{raw_value}' → '{display}'")
                        return display
            
            # Fallback: Raw-Wert zurückgeben
            logger.debug(f"🔍 Keine Übersetzung gefunden für '{raw_value}', verwende Raw-Wert")
            return str(raw_value)
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Dropdown-Übersetzung für {raw_value}: {e}")
            return str(raw_value)

    def _prepare_show_value_v3(self, original_value: Any, field_config: dict, stichtag: float) -> str:
        """
        V3-Feature: Bereitet Show-Werte auf (z.B. Dropdown-Texte, Formatierungen)
        """
        try:
            # Dropdown-Feld?
            if field_config.get("type") == "dropdown" and field_config.get("dropdown_config"):
                dropdown_config = field_config["dropdown_config"]
                show_value = self.get_dropdown_display_value(
                    raw_value=str(original_value),
                    field_name=field_config["feld"],
                    dropdown_config=dropdown_config
                )
                return show_value
            
            # Datum-Feld?
            elif field_config.get("type") == "date" and original_value:
                try:
                    # Datum formatieren
                    from pd_datetime import Pdvm_DateTime
                    dt_inst = Pdvm_DateTime("DEU")
                    if isinstance(original_value, (int, float)) and original_value > 0:
                        return dt_inst.format_date(original_value)
                except:
                    pass
            
            # Standard: Original-Wert als String
            return str(original_value) if original_value is not None else ""
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler bei Show-Value für {field_config.get('feld', 'unknown')}: {e}")
            return str(original_value) if original_value is not None else ""

    def _add_date_columns_v3(self, record: dict, felder: list, stichtag: float):
        """
        V3-Feature: Fügt IMMER YMD/Alter-Spalten für alle Datumsfelder hinzu
        (vollständige Basis - ViewManager entscheidet später was angezeigt wird)
        """
        try:
            from pd_datetime import Pdvm_DateTime
            dt_inst = Pdvm_DateTime("DEU")
            
            for field_config in felder:
                if field_config.get("type") == "date":
                    field_name = field_config.get("feld")
                    if not field_name:
                        continue
                    
                    # Original-Wert für Berechnung verwenden
                    if f"{field_name}_original" in record:
                        date_value = record[f"{field_name}_original"]
                    else:
                        date_value = record.get(field_name)
                    
                    if date_value and isinstance(date_value, (int, float)) and date_value > 0:
                        # IMMER YMD-Spalten hinzufügen (vollständige Basis)
                        try:
                            year, month, day = dt_inst.extract_ymd(date_value)
                            record[f"{field_name}_jahr"] = year
                            record[f"{field_name}_monat"] = month
                            record[f"{field_name}_tag"] = day
                        except Exception as e:
                            logger.debug(f"YMD-Extraktion fehlgeschlagen für {field_name}: {e}")
                        
                        # IMMER Alter-Spalte hinzufügen (vollständige Basis)
                        try:
                            alter = dt_inst.calculate_age(date_value, stichtag)
                            record[f"{field_name}_alter"] = alter
                        except Exception as e:
                            logger.debug(f"Alter-Berechnung fehlgeschlagen für {field_name}: {e}")
                                
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Hinzufügen der Datums-Spalten: {e}")

    def _apply_column_visibility(self, record: dict, view_config: dict) -> dict:
        """
        Wendet Spalten-Sichtbarkeit basierend auf view_config an.
        Nur Spalten mit show=true werden im finalen Record behalten.
        
        Args:
            record: Vollständiger Datensatz mit allen Spalten
            view_config: View-Konfiguration mit Spalten-Definitionen
            
        Returns:
            dict: Gefilterter Datensatz nur mit sichtbaren Spalten
        """
        try:
            filtered_record = {}
            
            # IMMER: System-Spalten behalten
            filtered_record["uid"] = record.get("uid")
            filtered_record["_guid"] = record.get("_guid")
            
            # View-Konfiguration auslesen
            table_name = view_config["ROOT"]["view_table"]
            felder = view_config["metadata"][table_name]["felder"]
            
            # Spalten-Visibility-Konfiguration (falls vorhanden)
            column_config = view_config.get("column_visibility", {})
            
            logger.debug(f"🔍 Spalten-Filter anwenden: {len(record)} → {len(filtered_record)} Spalten")
            
            for feld_config in felder:
                feld_name = feld_config["feld"]
                
                # Standard: Feld selbst anzeigen (falls nicht anders konfiguriert)
                show_main = column_config.get(feld_name, True)
                if show_main:
                    filtered_record[feld_name] = record.get(feld_name)
                
                # Original-Spalte anzeigen?
                show_original = column_config.get(f"{feld_name}_original", False)
                if show_original:
                    filtered_record[f"{feld_name}_original"] = record.get(f"{feld_name}_original")
                
                # Show-Spalte anzeigen?
                show_show = column_config.get(f"{feld_name}_show", False)
                if show_show:
                    filtered_record[f"{feld_name}_show"] = record.get(f"{feld_name}_show")
                
                # Datums-Spalten (YMD/Alter) anzeigen?
                if feld_config.get("type") == "date":
                    # Jahr/Monat/Tag
                    if column_config.get(f"{feld_name}_jahr", False):
                        filtered_record[f"{feld_name}_jahr"] = record.get(f"{feld_name}_jahr")
                    if column_config.get(f"{feld_name}_monat", False):
                        filtered_record[f"{feld_name}_monat"] = record.get(f"{feld_name}_monat")
                    if column_config.get(f"{feld_name}_tag", False):
                        filtered_record[f"{feld_name}_tag"] = record.get(f"{feld_name}_tag")
                    
                    # Alter
                    if column_config.get(f"{feld_name}_alter", False):
                        filtered_record[f"{feld_name}_alter"] = record.get(f"{feld_name}_alter")
            
            logger.debug(f"✅ Spalten-Filter: {len(filtered_record)} sichtbare Spalten")
            return filtered_record
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anwenden der Spalten-Sichtbarkeit: {e}")
            # Fallback: Vollständiger Record
            return record

    def get_default_column_visibility(self, view_config: dict) -> dict:
        """
        Erstellt eine Standard-Spalten-Sichtbarkeits-Konfiguration.
        
        Standard-Verhalten:
        - Haupt-Felder: sichtbar (show=true)
        - Original-Spalten: unsichtbar (show=false)  
        - Show-Spalten: unsichtbar (show=false)
        - YMD/Alter-Spalten: unsichtbar (show=false)
        
        Args:
            view_config: View-Konfiguration
            
        Returns:
            dict: Standard-Spalten-Sichtbarkeits-Konfiguration
        """
        try:
            column_visibility = {}
            
            # Flexible Behandlung verschiedener view_config Strukturen
            if "ROOT" in view_config and "metadata" in view_config:
                # Vollständige view_config Struktur
                table_name = view_config["ROOT"]["view_table"]
                felder = view_config["metadata"][table_name]["felder"]
            elif "fields" in view_config:
                # Einfache fields-basierte Struktur
                felder = [{"feld": field, "type": "string"} for field in view_config["fields"]]
            else:
                print("❌ Fehler beim Erstellen der Standard-Spalten-Sichtbarkeit: Unbekannte view_config Struktur")
                return {}
            
            for feld_config in felder:
                if isinstance(feld_config, str):
                    feld_name = feld_config
                    feld_type = "string"
                else:
                    feld_name = feld_config["feld"]
                    feld_type = feld_config.get("type", "string")
                
                # Standard: Haupt-Feld sichtbar
                column_visibility[feld_name] = True
                
                # Original/Show-Spalten: Standard unsichtbar (für Debugging/Entwicklung verfügbar)
                column_visibility[f"{feld_name}_original"] = False
                column_visibility[f"{feld_name}_show"] = False
                
                # Datums-Spalten: Standard unsichtbar
                if feld_type == "date":
                    column_visibility[f"{feld_name}_jahr"] = False
                    column_visibility[f"{feld_name}_monat"] = False
                    column_visibility[f"{feld_name}_tag"] = False
                    column_visibility[f"{feld_name}_alter"] = False
            
            logger.info(f"📊 Standard-Spalten-Sichtbarkeit erstellt: {len(column_visibility)} Spalten-Regeln")
            return column_visibility
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der Standard-Spalten-Sichtbarkeit: {e}")
            return {}
