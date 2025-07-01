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
        guid: Optional[str] = None
#        historisch: bool = False
    ):
        self.db_name = db_name
        self.table_name = table_name
        logger.info(f"🔹 Initialisiere PdvmCentralDatenbank für {self.table_name} in {self.db_name}."  )
        self.guid = guid
        logger.info(f"🔹 GUID gesetzt auf {self.guid}.")
    #    self.historisch = historisch  --- wird auomatisch aus der Tabelle abgeleitet


        # Im Konstruktor prüfen wir, ob die Tabelle existiert, und laden (falls GUID gegeben) die Daten
        self._ensure_table_exists()

        # Wenn eine GUID übergeben wurde, lade das JSON‐Diktat in self.data;
        # sonst setze self.data auf {} (für get_value_all o.ä.).
        self.data: Dict[str, Any] = {}
        if self.guid:
            logger.info(f"🔹 Lade Daten für GUID {self.guid} aus Tabelle {self.table_name}.")
            raw = self._lesen_rogue(self.guid)  # "roh" aus DB als JSON-String bzw. dict
            if raw is None:
                # Falls kein Eintrag, data bleibt leer
                self.data = {}
            else:
                self.data = raw

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
        Gibt eine Liste von Diktaten zurück: jeweils
          {"uid": <guid>, "<GRUPPE1>": <Daten-Dict oder JSON-String>, ...}
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {self.table_name}")
        rows = cursor.fetchall()
        cols = [col[0] for col in cursor.description]
        conn.close()

        result = []
        for row in rows:
            entry = {cols[i]: row[i] for i in range(len(cols))}
            # Spalte "daten" liegt in entry["daten"] als JSON-String oder dict
            raw = entry.get("daten", {})
            if isinstance(raw, str):
                try:
                    data_dict = json.loads(raw)
                except:
                    data_dict = {}
            else:
                data_dict = raw
            # Wir ersetzen entry["daten"] durch den gepackten Dict-Inhalt:
            entry = {"uid": entry["uid"], **data_dict}
            result.append(entry)
        return result

    def speichern(self, guid: str, daten: Dict[str, Any]):
        """
        Speichert oder aktualisiert den Eintrag (guid, daten).
        'daten' ist ein Python-Dict, das wir in JSON umwandeln und in Tabelle schreiben.
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        json_str = json.dumps(daten)
        # Prüfen, ob schon existiert
        cursor.execute(f"SELECT COUNT(*) FROM {self.table_name} WHERE uid = ?", (guid,))
        exists = cursor.fetchone()[0] > 0

        if exists:
            cursor.execute(f"UPDATE {self.table_name} SET daten = ? WHERE uid = ?", (json_str, guid))
        else:
            cursor.execute(f"INSERT INTO {self.table_name} (uid, daten) VALUES (?, ?)", (guid, json_str))

        conn.commit()
        conn.close()

    def loeschen(self, guid: str):
        """
        Löscht einen Datensatz anhand der GUID.
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {self.table_name} WHERE uid = ?", (guid,))
        conn.commit()
        conn.close()

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
            print(f"[DEBUG] PdvmCentralDatenbank.set_value: Vorher self.data[{gruppe}][{feld}]={self.data[gruppe][feld]}")
            self.data[gruppe][feld][ts_key] = wert
            print(f"[DEBUG] PdvmCentralDatenbank.set_value: Nachher self.data[{gruppe}][{feld}]={self.data[gruppe][feld]}")
        # 3) Nicht-historischer Zweig
        else:
            # ab_zeit wird ignoriert, Wert als Skalar gespeichert
            print(f"[DEBUG] PdvmCentralDatenbank.set_value: (nicht historisch) Vorher self.data[{gruppe}][{feld}]={self.data[gruppe].get(feld, 'N/A')}")
            self.data[gruppe][feld] = wert
            print(f"[DEBUG] PdvmCentralDatenbank.set_value: (nicht historisch) Nachher self.data[{gruppe}][{feld}]={self.data[gruppe][feld]}")

    def read_guid(self, guid: str):
        """
        Liest die Daten für die angegebene GUID und setzt self.guid und self.data entsprechend neu.
        """
        old_guid = self.guid
        self.guid = guid
        self.data = self._lesen_rogue(guid) or {}
        print(f"[DEBUG] PdvmCentralDatenbank.read_guid: Tabelle={self.table_name}, alte GUID={old_guid}, neue GUID={guid}, geladene Daten={self.data}")

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
