# -*- coding: utf-8 -*-
# pdvm_central_datenbank.py

import sqlite3
import json
import logging
from typing import Any, Dict, Optional

from pd_datetime import Pdvm_DateTime

from pd_datetime import Pdvm_DateTime

logger = logging.getLogger(__name__)


class ColumnControl:
    """
    Control-Struktur für Spalten-Management.
    Verwaltet Reihenfolge, Eigenschaften und Verarbeitung aller Spalten.
    """
    def __init__(self):
        self.columns = []  # Liste von ColumnInfo-Objekten in der korrekten Reihenfolge
        self.column_map = {}  # Schneller Zugriff nach Name
    
    def add_column(self, name: str, column_type: str, order: int, **kwargs):
        """Fügt eine Spalte zur Control hinzu"""
        column_info = {
            'name': name,  # Spaltenname, z.B. 'vorname_original'
            'type': column_type,
            'order': order,
            'original_field': kwargs.get('original_field'),
            'field_config': kwargs.get('field_config'),
            'is_auto_generated': kwargs.get('is_auto_generated', False),
            'gruppe': kwargs.get('gruppe'),
            'feld': kwargs.get('feld'),
            'anzeige': kwargs.get('anzeige'),
            'show': kwargs.get('show', False),
            'expert': kwargs.get('expert', False),
            'header_name': name,  # explizit für Header-Zeile 2 im Expert-Mode
        }
        self.columns.append(column_info)
        self.column_map[name] = column_info
        
    def sort_columns(self):
        """Sortiert die Spalten nach der Order"""
        self.columns.sort(key=lambda x: x['order'])
        
    def get_ordered_column_names(self):
        """Gibt die Spaltennamen in der korrekten Reihenfolge zurück"""
        return [col['name'] for col in self.columns]
        
    def get_column_info(self, name: str):
        """Gibt die Informationen einer Spalte zurück"""
        return self.column_map.get(name)


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
        Zentrale View-Methode: Gibt (controls, daten)-Tuple zurück.
        controls: ColumnControl-Objekt mit Spaltenstruktur
        daten: Liste von Dicts mit optimaler Spaltenstruktur
        """
        # try entfernt: kein except/finally vorhanden
        from pd_datetime import Pdvm_DateTime
        if stichtag is None:
            dt_inst = Pdvm_DateTime("DEU")
            stichtag = dt_inst.PdvmDateTimeNow()
        
        # DateTime-Instanz für Datumsübersetzungen
        dt_formatter = Pdvm_DateTime("DEU")
        
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
        # Mit Initialisierung der Klasse wird die historisch-Logik gesetzt.
        # Wir nehmen an, dass alle Datensätze in der View-Tabelle das gleiche historisch-Flag haben.
#        if alle_datensaetze and len(alle_datensaetze) > 0:
#            first_row = alle_datensaetze[0]
#            # historisch ist normalerweise in row["historisch"] gespeichert, falls PdvmDatenbank es liefert
#            self.historisch = bool(first_row.get("historisch", False))
#        else:
#            self.historisch = False  # Fallback
        
        logger.info(f"📊 get_value_view: Verarbeite {len(alle_datensaetze)} Datensätze für {len(felder)} Felder")
        logger.info("🔧 KLARE 4-SCHRITT ARCHITEKTUR: 1.Controls 2.Original-Daten 3.Show-Daten 4.Rückgabe")
        
        # SCHRITT 1: SPALTEN-STRUKTUR erstellen (alle _original, dann alle _show, dann dummy)
        column_structure = self._create_column_control(felder)
        logger.info(f"🏗️ Control-Struktur erstellt: {len(column_structure.columns)} Spalten (inkl. Dummy)")
        logger.info(f"📋 Reihenfolge: System → Original → Auto-Original → Show → Auto-Show → Dummy")
        
        all_column_names = [col['name'] for col in column_structure.columns]
        logger.info(f"📋 Spaltennamen: {all_column_names}")

        # SCHRITT 2: Alle Datensätze verarbeiten - nur _original Spalten befüllen
        result = []
        for row_data in alle_datensaetze:
            guid = row_data.get("uid")
            if not guid:
                continue

            # JSON-Daten aus der bereits geladenen Zeile direkt in self.data setzen
            raw_data = row_data.get("daten", {})
            if isinstance(raw_data, str):
                try:
                    self.data = json.loads(raw_data)
                except Exception as e:
                    logger.error(f"❌ Fehler beim Parsen von JSON für GUID {guid}: {e}. Überspringe diesen Datensatz.")
                    continue
            else:
                self.data = raw_data

            # Record mit allen Spalten initialisieren
            record = {col_name: "" for col_name in all_column_names}
            
            # SCHRITT 2A: System-Original-Spalten befüllen
            record["uid_original"] = guid
            
            # SCHRITT 2B: Feld-Original-Spalten befüllen (inkl. Zusatzspalten)
            self._fill_all_original_columns(record, column_structure, dt_formatter, stichtag)
            
            result.append(record)
        
        # SCHRITT 3: Alle _show Spalten befüllen (basierend auf _original Werten)
        for record in result:
            self._fill_all_show_columns(record, column_structure, dt_formatter, stichtag)
        
        # SCHRITT 4: Dummy-Spalte und finale Rückgabe
        for record in result:
            record["dummy"] = "keine Daten"

        all_column_names = [col['name'] for col in column_structure.columns]
        if not result:
            logger.warning("⚠️ Keine gültigen Datensätze nach JSON-Parsing, gebe leere Zeile mit allen Spalten zurück.")
            empty = {col: "" for col in all_column_names}
            logger.info(f"🔎 get_value_view Rückgabe (nur Spalten): {list(empty.keys())}")
            return [empty]

        logger.info(f"🔎 get_value_view Rückgabe: Spalten={all_column_names}")
        if result:
            logger.info(f"🔎 get_value_view Beispiel-Datensatz: {result[0]}")
        return (column_structure, result)

    def _fill_all_original_columns(self, record: dict, column_structure, dt_formatter, stichtag: float):
        """
        SCHRITT 2: Alle _original Spalten befüllen (Haupt- und Zusatzspalten)
        """
        for col in column_structure.columns:
            col_name = col['name']
            
            # Nur _original Spalten verarbeiten (außer uid_original, das ist schon gesetzt)
            if not col_name.endswith("_original") or col_name == "uid_original":
                continue
                
            col_type = col.get('type', '')
            
            if col_type == "original":
                # Haupt-Original-Spalte (z.B. geburtsdatum_original)
                feld = col.get('feld') or col.get('original_field')
                gruppe = col.get('gruppe', 'DATEN')
                if feld:
                    wert_dict = self.get_value(gruppe, str(feld).upper(), stichtag)
                    val = wert_dict.get("wert")
                    record[col_name] = val
                    
                    # Falls Datumsfeld: Zusatzspalten direkt befüllen
                    field_config = col.get('field_config', {})
                    if field_config.get('type') == 'date' and isinstance(val, (int, float)) and val > 0:
                        self._fill_date_additional_original_columns(record, feld, val, dt_formatter, stichtag)
                else:
                    record[col_name] = None
                    
            elif col_type == "date_plus":
                # Zusatzspalten für Datum werden von _fill_date_additional_original_columns befüllt
                # Falls nicht befüllt, leer lassen
                if col_name not in record or record[col_name] == "":
                    record[col_name] = ""

    def _fill_date_additional_original_columns(self, record: dict, feld_name: str, original_wert: Any, dt_formatter, stichtag: float):
        """
        Befüllt alle Zusatzspalten für ein Datumsfeld (_alter_original, _jahr_original, etc.)
        """
        try:
            if not isinstance(original_wert, (int, float)) or original_wert <= 0:
                # Leere Werte für alle Zusatzspalten
                for zusatz in ["alter", "jahr", "monat", "tag"]:
                    record[f"{feld_name.lower()}_{zusatz}_original"] = ""
                return
            
            # Datum setzen
            dt_formatter.PdvmDateTime = original_wert
            dt_stichtag = Pdvm_DateTime("DEU")
            dt_stichtag.PdvmDateTime = stichtag
            
            # Werte berechnen
            alter = dt_stichtag.Year - dt_formatter.Year
            jahr = dt_formatter.Year
            monat = dt_formatter.Month
            tag = dt_formatter.Day
            
            # Original-Zusatzspalten befüllen
            record[f"{feld_name.lower()}_alter_original"] = alter
            record[f"{feld_name.lower()}_jahr_original"] = jahr
            record[f"{feld_name.lower()}_monat_original"] = monat
            record[f"{feld_name.lower()}_tag_original"] = tag
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Befüllen der Original-Zusatzspalten für {feld_name}: {e}")
            # Fallback: Leere Werte
            for zusatz in ["alter", "jahr", "monat", "tag"]:
                record[f"{feld_name.lower()}_{zusatz}_original"] = ""

    def _fill_all_show_columns(self, record: dict, column_structure, dt_formatter, stichtag: float):
        """
        SCHRITT 3: Alle _show Spalten befüllen (basierend auf _original Werten)
        """
        # System-Show-Spalte
        record["uid_show"] = record["uid_original"][:8] + "..." if record["uid_original"] else ""
        
        for col in column_structure.columns:
            col_name = col['name']
            
            # Nur _show Spalten verarbeiten (außer uid_show, das ist schon gesetzt)
            if not col_name.endswith("_show") or col_name == "uid_show":
                continue
                
            col_type = col.get('type', '')
            original_col_name = col_name.replace("_show", "_original")
            original_wert = record.get(original_col_name)
            
            if col_type == "show":
                # Haupt-Show-Spalte
                field_config = col.get('field_config', {})
                self._fill_single_show_column(record, col_name, original_wert, field_config, dt_formatter)
                
            elif col_type == "date_plus":
                # Zusatz-Show-Spalten für Datum
                self._fill_date_additional_show_column(record, col_name, original_wert, dt_formatter)

    def _fill_single_show_column(self, record: dict, col_name: str, original_wert: Any, field_config: dict, dt_formatter):
        """
        Befüllt eine einzelne _show Spalte basierend auf dem Original-Wert
        """
        try:
            field_type = field_config.get("type", "string")
            
            if field_type == "dropdown":
                # Dropdown-Übersetzung
                record[col_name] = self._translate_dropdown_value(original_wert, field_config.get("dropdown", {}))
                
            elif field_type == "date":
                # Datum formatieren
                if isinstance(original_wert, (int, float)) and original_wert > 0:
                    dt_formatter.PdvmDateTime = original_wert
                    record[col_name] = dt_formatter.Date
                else:
                    record[col_name] = ""
                    
            else:
                # String oder andere Typen
                record[col_name] = str(original_wert) if original_wert is not None else ""
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Befüllen der Show-Spalte {col_name}: {e}")
            record[col_name] = ""

    def _fill_date_additional_show_column(self, record: dict, col_name: str, original_wert: Any, dt_formatter):
        """
        Befüllt eine Zusatz-Show-Spalte für Datum (formatiert für Anzeige)
        """
        try:
            if col_name.endswith("_alter_show"):
                record[col_name] = str(original_wert) if original_wert not in ("", None) else ""
                
            elif col_name.endswith("_jahr_show"):
                record[col_name] = str(original_wert) if original_wert not in ("", None) else ""
                
            elif col_name.endswith("_monat_show"):
                # Monatsname (deutscher Text)
                if isinstance(original_wert, int) and 1 <= original_wert <= 12:
                    monat_namen = ["", "Januar", "Februar", "März", "April", "Mai", "Juni", 
                                  "Juli", "August", "September", "Oktober", "November", "Dezember"]
                    record[col_name] = monat_namen[original_wert]
                else:
                    record[col_name] = str(original_wert) if original_wert not in ("", None) else ""
                    
            elif col_name.endswith("_tag_show"):
                record[col_name] = str(original_wert) if original_wert not in ("", None) else ""
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Befüllen der Zusatz-Show-Spalte {col_name}: {e}")
            record[col_name] = ""

    def _create_column_control(self, felder: list) -> ColumnControl:
        """
        Erstellt die Control-Struktur mit einheitlicher Namensgebung und Kopfzeilen-Logik.
        - Feldname (klein) für _original/_show
        - 'name' als Anzeigeüberschrift (show), bei original: '(Original)' anhängen
        - Zusatzfelder: 'Alter', 'Jahr', 'Monat', 'Tag'
        - Im Expert-Mode: 2 Kopfzeilen (Zeile 1: name, Zeile 2: feldname)
        """
        control = ColumnControl()
        order = 0

        # System-Spalten zuerst
        control.add_column(
            "uid_original", "system", order,
            field_config={"anzeige": "ID (Original)", "label": "uid_original"},
            gruppe=None, feld=None, anzeige="ID (Original)",
            show=False, expert=True
        )
        order += 1
        control.add_column(
            "uid_show", "system", order,
            field_config={"anzeige": "ID", "label": "uid_show"},
            gruppe=None, feld=None, anzeige="ID",
            show=True, expert=False
        )
        order += 1


        for feld_config in felder:
            feldname_gross = feld_config["feld"]
            feld_name = feldname_gross.lower()
            feld_type = feld_config.get("type", "string")
            gruppe = feld_config.get("gruppe", "DATEN")
            anzeige = feld_config.get("name") or feld_name.capitalize()

            # Original-Spalte (Expert-Mode: label = feld_name (klein))
            orig_label = feld_name  # <--- Feldname klein für die zweite Zeile im Header
            orig_anzeige = f"{anzeige} (Original)"
            orig_field_config = dict(feld_config)
            orig_field_config["anzeige"] = orig_anzeige
            orig_field_config["label"] = orig_label
            control.add_column(
                f"{feld_name}_original",
                "original",
                order,
                original_field=feld_name,
                field_config=orig_field_config,
                gruppe=gruppe,
                feld=feld_name,
                anzeige=orig_anzeige,
                show=False,
                expert=True
            )
            order += 1

            # Zusatzfelder für Datum
            if feld_type == "date":
                for zusatz, zusatz_label in zip(
                    ["alter", "jahr", "monat", "tag"],
                    ["Alter", "Jahr", "Monat", "Tag"]):
                    col_name = f"{feld_name}_{zusatz}_original"
                    auto_field_config = dict(feld_config)
                    auto_field_config["anzeige"] = f"{anzeige} {zusatz_label} (Original)"
                    auto_field_config["label"] = f"{feldname_gross}_{zusatz}"
                    control.add_column(
                        col_name,
                        "date_plus",
                        order,
                        original_field=feld_name,
                        field_config=auto_field_config,
                        is_auto_generated=True,
                        gruppe=gruppe,
                        feld=feld_name,
                        anzeige=auto_field_config["anzeige"],
                        show=False,
                        expert=True
                    )
                    order += 1

            # Show-Spalte (label = feldname_gross)
            show_field_config = dict(feld_config)
            show_field_config["anzeige"] = anzeige
            show_field_config["label"] = feldname_gross
            control.add_column(
                f"{feld_name}_show",
                "show",
                order,
                original_field=feld_name,
                field_config=show_field_config,
                gruppe=gruppe,
                feld=feld_name,
                anzeige=anzeige,
                show=True,
                expert=False
            )
            order += 1

            # Zusatzfelder für Datum (show)
            if feld_type == "date":
                for zusatz, zusatz_label in zip(
                    ["alter", "jahr", "monat", "tag"],
                    ["Alter", "Jahr", "Monat", "Tag"]):
                    col_name = f"{feld_name}_{zusatz}_show"
                    auto_field_config = dict(feld_config)
                    auto_field_config["anzeige"] = f"{anzeige} {zusatz_label}"
                    auto_field_config["label"] = f"{feldname_gross}_{zusatz}"
                    control.add_column(
                        col_name,
                        "date_plus",
                        order,
                        original_field=feld_name,
                        field_config=auto_field_config,
                        is_auto_generated=True,
                        gruppe=gruppe,
                        feld=feld_name,
                        anzeige=auto_field_config["anzeige"],
                        show=True,
                        expert=False
                    )
                    order += 1

        # Dummy-Spalte immer am Ende hinzufügen
        control.add_column(
            "dummy", "dummy", order,
            field_config={"anzeige": "Keine Daten", "label": "dummy"},
            gruppe=None, feld=None, anzeige="Keine Daten",
            show=False, expert=False
        )
        order += 1

        # Control sortieren
        control.sort_columns()

        logger.info(f"🏗️ Control-Struktur erstellt: {len(control.columns)} Spalten (inkl. Dummy)")
        logger.info("📋 Reihenfolge: System → Original → Auto-Original → Show → Auto-Show → Dummy")
        logger.info(f"📋 Spaltennamen: {[col['name'] for col in control.columns]}")
        return control

    def _translate_dropdown_cached(self, wert: Any, field_config: dict, 
                                 dropdown_cache: dict, guid: str) -> str:
        """
        Übersetzt Dropdown-Werte mit Cache (nur einmal pro GUID laden).
        """
        if not wert:
            return ""

        dropdown_config = field_config.get("dropdown_config")
        if not dropdown_config:
            dropdown_config = field_config.get("dropdown", {})
        if not dropdown_config:
            msg = f"FEHLER: Dropdown-Konfiguration fehlt für Feld {field_config.get('feld', '')}"
            logger.error(msg)
            raise ValueError(msg)

        # Cache-Key erstellen
        cache_key = f"{guid}_{dropdown_config.get('table', '')}_{dropdown_config.get('gruppe', '')}"

        if cache_key not in dropdown_cache:
            # Dropdown-Daten laden und cachen
            dropdown_cache[cache_key] = self._load_dropdown_data(dropdown_config, guid)

        dropdown_data = dropdown_cache[cache_key]
        if not dropdown_data:
            msg = f"FEHLER: Keine Dropdown-Daten geladen für Feld {field_config.get('feld', '')}"
            logger.error(msg)
            raise ValueError(msg)

        return dropdown_data.get(str(wert), f"FEHLER: Kein Mapping für Wert '{wert}'")

    def _load_dropdown_data(self, dropdown_config: dict, guid: str) -> dict:
        """
        Lädt Dropdown-Daten für Übersetzungen.
        """
        try:
            table_name = dropdown_config.get("table")
            guid = dropdown_config.get("key")
            value_field = dropdown_config.get("value")

            if not (table_name and guid and value_field):
                raise ValueError(f"Ungültige Dropdown-Konfiguration: {dropdown_config}")

            # Lade den Datensatz mit der GUID aus der Tabelle
            dropdown_db = PdvmCentralDatenbank(db_name=self.db_name, table_name=table_name, guid=guid)
            dropdown_data = dropdown_db.lesen()
            mapping = {}
            if dropdown_data and "ROOT" in dropdown_data:
                group_data = dropdown_data["ROOT"].get(value_field, {})
                werte = group_data.get("werte", [])
                for eintrag in werte:
                    key = str(eintrag.get("key"))
                    display = eintrag.get("de") or eintrag.get("en") or key
                    if key:
                        mapping[key] = display
            if not mapping:
                logger.warning(f"Keine Dropdown-Mappings gefunden für {table_name}/{guid}/{value_field}")
            return mapping
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Dropdown-Daten: {e}")
            raise

    def _create_show_value(self, original_wert: Any, feld_config: dict, dt_formatter, stichtag: float) -> str:
        """
        Erstellt den aufbereiteten Show-Wert basierend auf Feldtyp und Konfiguration.
        
        Args:
            original_wert: Der Original-Rohwert
            feld_config: Feld-Konfiguration mit type, dropdown_config etc.
            dt_formatter: PdvmDateTime-Instanz für Datumsformatierung
            stichtag: Aktueller Stichtag
            
        Returns:
            str: Aufbereiteter Anzeigewert
        """
        try:
            if original_wert is None:
                return ""

            feld_type = feld_config.get("type", "string")

            if feld_type == "date":
                # Datum mit PdvmDateTime formatieren
                if isinstance(original_wert, (int, float)) and original_wert > 0:
                    dt_formatter.PdvmDateTime = original_wert
                    return dt_formatter.Date
                return str(original_wert) if original_wert else ""

            elif feld_type == "dropdown":
                # Dropdown-Übersetzung
                dropdown_config = feld_config.get("dropdown_config")
                if not dropdown_config:
                    dropdown_config = feld_config.get("dropdown", {})
                if not dropdown_config:
                    msg = f"FEHLER: Dropdown-Konfiguration fehlt für Feld {feld_config.get('feld', '')}"
                    logger.error(msg)
                    raise ValueError(msg)
                try:
                    return self._translate_dropdown_value(original_wert, dropdown_config)
                except Exception as e:
                    msg = f"FEHLER: Dropdown-Übersetzung fehlgeschlagen für Feld {feld_config.get('feld', '')}: {e}"
                    logger.error(msg)
                    raise

            else:
                # String oder andere Typen: Als String zurückgeben
                return str(original_wert) if original_wert else ""

        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des Show-Werts: {e}")
            return f"FEHLER: {e}" if e else str(original_wert) if original_wert else ""

    def _add_complete_date_columns(self, record: dict, feld_name: str, original_wert: Any, 
                                  dt_formatter, stichtag: float):
        """
        Fügt ALLE Datums-Spalten hinzu: Original UND Show-Versionen.
        Ersetzt _add_date_show_columns mit vollständiger Spalten-Architektur.
        
        Args:
            record: Der Datensatz-Record (wird modifiziert)
            feld_name: Name des Datums-Feldes (kleinbuchstaben)
            original_wert: Der Original-Datumswert
            dt_formatter: PdvmDateTime-Instanz
            stichtag: Aktueller Stichtag
        """
        try:
            if not isinstance(original_wert, (int, float)) or original_wert <= 0:
                # ALLE Spalten mit leeren Werten initialisieren
                date_cols = [
                    f"{feld_name}_alter_original", f"{feld_name}_alter_show",
                    f"{feld_name}_jahr_original", f"{feld_name}_jahr_show",
                    f"{feld_name}_monat_original", f"{feld_name}_monat_show",
                    f"{feld_name}_tag_original", f"{feld_name}_tag_show"
                ]
                for col in date_cols:
                    record[col] = ""
                return
            
            # Datum setzen
            dt_formatter.PdvmDateTime = original_wert
            
            # Alter berechnen (basierend auf Stichtag)
            dt_stichtag = Pdvm_DateTime("DEU")
            dt_stichtag.PdvmDateTime = stichtag
            alter = dt_stichtag.Year - dt_formatter.Year
            
            # Jahr, Monat, Tag extrahieren
            jahr = dt_formatter.Year
            monat = dt_formatter.Month
            tag = dt_formatter.Day
            # Deutscher Monatsname
            monat_namen = ["", "Januar", "Februar", "März", "April", "Mai", "Juni", 
                          "Juli", "August", "September", "Oktober", "November", "Dezember"]
            monat_name = monat_namen[monat] if 1 <= monat <= 12 else str(monat)
            
            # ORIGINAL-Spalten (Zahlen-Werte für Sortierung/Filterung)
            record[f"{feld_name}_alter_original"] = alter if alter is not None else 0
            record[f"{feld_name}_jahr_original"] = jahr
            record[f"{feld_name}_monat_original"] = monat
            record[f"{feld_name}_tag_original"] = tag
            
            # SHOW-Spalten (Formatierte Anzeige für Benutzer)
            record[f"{feld_name}_alter_show"] = str(alter) if alter is not None else ""
            record[f"{feld_name}_jahr_show"] = str(jahr)
            record[f"{feld_name}_monat_show"] = monat_name  # z.B. "Januar"
            record[f"{feld_name}_tag_show"] = str(tag)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der Datums-Spalten für {feld_name}: {e}")
            # Fallback: Alle Spalten leer
            date_cols = [
                f"{feld_name}_alter_original", f"{feld_name}_alter_show",
                f"{feld_name}_jahr_original", f"{feld_name}_jahr_show",
                f"{feld_name}_monat_original", f"{feld_name}_monat_show",
                f"{feld_name}_tag_original", f"{feld_name}_tag_show"
            ]
            for col in date_cols:
                record[col] = ""

    def _create_column_structure(self, felder: list) -> dict:
        """
        Erstellt die komplette Spalten-Struktur ohne Doppelungen.
        OPTIMIERTE REIHENFOLGE: System → Original-Felder → Automatische Original-Spalten → Show-Spalten
        
        Args:
            felder: Liste der Feld-Konfigurationen
            
        Returns:
            dict: Spalten-Struktur mit allen benötigten Spalten in korrekter Reihenfolge
        """
        structure = {}
        
        # System-Spalten (immer vorhanden)
        structure["uid_original"] = {"type": "system", "order": 0}
        structure["uid_show"] = {"type": "system", "order": 1}
        
        order_counter = 2
        
        # SCHRITT 1: Alle Original-Spalten (inkl. automatische Datum-Spalten)
        for feld_config in felder:
            feld_name = feld_config["feld"].lower()
            feld_type = feld_config.get("type", "string")
            
            # Basis Original-Spalte
            original_col = f"{feld_name}_original"
            if original_col not in structure:
                structure[original_col] = {
                    "type": "original", 
                    "field_type": feld_type,
                    "field_config": feld_config,
                    "order": order_counter
                }
                order_counter += 1
            
            # Automatische Original-Spalten für Datum-Felder (direkt nach dem Basis-Datum)
            if feld_type == "date":
                date_original_cols = [
                    f"{feld_name}_alter_original",
                    f"{feld_name}_jahr_original", 
                    f"{feld_name}_monat_original",
                    f"{feld_name}_tag_original"
                ]
                
                for col in date_original_cols:
                    if col not in structure:
                        structure[col] = {
                            "type": "date_original",
                            "field_type": "integer",
                            "parent_field": feld_name,
                            "field_config": feld_config,
                            "order": order_counter
                        }
                        order_counter += 1
        
        # SCHRITT 2: Alle Show-Spalten (inkl. automatische Datum-Show-Spalten)
        for feld_config in felder:
            feld_name = feld_config["feld"].lower()
            feld_type = feld_config.get("type", "string")
            
            # Basis Show-Spalte
            show_col = f"{feld_name}_show"
            if show_col not in structure:
                structure[show_col] = {
                    "type": "show", 
                    "field_type": feld_type,
                    "field_config": feld_config,
                    "order": order_counter
                }
                order_counter += 1
            
            # Automatische Show-Spalten für Datum-Felder (direkt nach dem Basis-Show)
            if feld_type == "date":
                date_show_cols = [
                    f"{feld_name}_alter_show",
                    f"{feld_name}_jahr_show", 
                    f"{feld_name}_monat_show",
                    f"{feld_name}_tag_show"
                ]
                
                for col in date_show_cols:
                    if col not in structure:
                        structure[col] = {
                            "type": "date_show",
                            "field_type": "string",
                            "parent_field": feld_name,
                            "field_config": feld_config,
                            "order": order_counter
                        }
                        order_counter += 1
        
        logger.info(f"🏗️ Spalten-Struktur erstellt: {len(structure)} Spalten in optimaler Reihenfolge")
        logger.info("📋 Reihenfolge: System → Original-Felder → Auto-Original → Show-Felder → Auto-Show")
        return structure

    def _create_record_with_structure(self, guid: str, felder: list, column_structure: dict, 
                                    dt_formatter, stichtag: float) -> dict:
        """
        Erstellt einen Datensatz basierend auf der definierten Spalten-Struktur.
        OPTIMIERT: Schleifenverarbeitung entsprechend der Spalten-Reihenfolge.
        
        Args:
            guid: GUID des Datensatzes
            felder: Liste der Feld-Konfigurationen  
            column_structure: Definierte Spalten-Struktur
            dt_formatter: PdvmDateTime-Instanz
            stichtag: Aktueller Stichtag
            
        Returns:
            dict: Vollständig befüllter Datensatz
        """
        # Datensatz mit allen Spalten initialisieren
        record = {}
        
        # Alle Spalten in korrekter Reihenfolge initialisieren
        sorted_columns = sorted(column_structure.items(), key=lambda x: x[1]["order"])
        for col_name, col_info in sorted_columns:
            record[col_name] = None  # Initialer Wert
        
        # System-Spalten befüllen
        record["uid_original"] = guid
        record["uid_show"] = guid[:8] + "..."
        
        # Einmaliger DB-Zugriff für alle Felder
        field_data = {}
        for feld_config in felder:
            feld_name = feld_config["feld"].lower()
            feld_gruppe = feld_config.get("gruppe", "ROOT")
            feld_type = feld_config.get("type", "string")
            
            # DB-Zugriff
            feld_gruppe_upper = feld_gruppe.upper()
            feld_name_upper = feld_config["feld"].upper()
            
            result_dict = self.get_value(feld_gruppe_upper, feld_name_upper, stichtag)
            original_wert = result_dict.get("wert") if result_dict else None
            
            field_data[feld_name] = {
                "original": original_wert,
                "config": feld_config,
                "type": feld_type
            }
        
        # SPALTEN-REIHENFOLGE VERARBEITUNG: Direkt durch sortierte Spalten-Struktur
        for col_name, col_info in sorted_columns:
            col_type = col_info["type"]
            
            if col_type == "system":
                # System-Spalten bereits befüllt
                continue
                
            elif col_type == "original":
                # Basis Original-Spalte
                field_name = col_name.replace("_original", "")
                if field_name in field_data:
                    record[col_name] = field_data[field_name]["original"]
                    
            elif col_type == "date_original":
                # Automatische Original-Datum-Spalte
                parent_field = col_info["parent_field"]
                if parent_field in field_data:
                    original_wert = field_data[parent_field]["original"]
                    self._fill_single_date_original_column(
                        record, col_name, parent_field, original_wert, dt_formatter, stichtag
                    )
                    
            elif col_type == "show":
                # Basis Show-Spalte
                field_name = col_name.replace("_show", "")
                if field_name in field_data:
                    data = field_data[field_name]
                    show_wert = self._create_show_value(
                        data["original"], data["config"], dt_formatter, stichtag
                    )
                    record[col_name] = show_wert
                    
            elif col_type == "date_show":
                # Automatische Show-Datum-Spalte
                parent_field = col_info["parent_field"]
                if parent_field in field_data:
                    original_wert = field_data[parent_field]["original"]
                    self._fill_single_date_show_column(
                        record, col_name, parent_field, original_wert, dt_formatter, stichtag
                    )
        
        return record

    def _fill_single_date_original_column(self, record: dict, col_name: str, parent_field: str, 
                                        original_wert: Any, dt_formatter, stichtag: float):
        """
        Befüllt eine einzelne automatische Original-Datum-Spalte.
        
        Args:
            record: Der Datensatz-Record (wird modifiziert)
            col_name: Name der zu befüllenden Spalte (z.B. "geburtsdatum_alter_original")
            parent_field: Name des Parent-Datums-Feldes (z.B. "geburtsdatum")
            original_wert: Der Original-Datumswert
            dt_formatter: PdvmDateTime-Instanz
            stichtag: Aktueller Stichtag
        """
        try:
            if not isinstance(original_wert, (int, float)) or original_wert <= 0:
                record[col_name] = 0 if "_alter_" in col_name else ""
                return
            
            # Datum setzen
            dt_formatter.PdvmDateTime = original_wert
            
            # Spezifischen Wert je nach Spalten-Typ
            if col_name.endswith("_alter_original"):
                dt_stichtag = Pdvm_DateTime("DEU")
                dt_stichtag.PdvmDateTime = stichtag
                alter = dt_stichtag.Year - dt_formatter.Year
                record[col_name] = alter if alter is not None else 0
                
            elif col_name.endswith("_jahr_original"):
                record[col_name] = dt_formatter.Year
                
            elif col_name.endswith("_monat_original"):
                record[col_name] = dt_formatter.Month
                
            elif col_name.endswith("_tag_original"):
                record[col_name] = dt_formatter.Day
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Befüllen der Original-Datum-Spalte {col_name}: {e}")
            record[col_name] = 0 if "_alter_" in col_name else ""

    def _fill_single_date_show_column(self, record: dict, col_name: str, parent_field: str, 
                                    original_wert: Any, dt_formatter, stichtag: float):
        """
        Befüllt eine einzelne automatische Show-Datum-Spalte.
        
        Args:
            record: Der Datensatz-Record (wird modifiziert)
            col_name: Name der zu befüllenden Spalte (z.B. "geburtsdatum_alter_show")
            parent_field: Name des Parent-Datums-Feldes (z.B. "geburtsdatum")
            original_wert: Der Original-Datumswert
            dt_formatter: PdvmDateTime-Instanz
            stichtag: Aktueller Stichtag
        """
        try:
            if not isinstance(original_wert, (int, float)) or original_wert <= 0:
                record[col_name] = ""
                return
            
            # Datum setzen
            dt_formatter.PdvmDateTime = original_wert
            
            # Spezifischen Anzeige-Wert je nach Spalten-Typ
            if col_name.endswith("_alter_show"):
                dt_stichtag = Pdvm_DateTime("DEU")
                dt_stichtag.PdvmDateTime = stichtag
                alter = dt_stichtag.Year - dt_formatter.Year
                record[col_name] = str(alter) if alter is not None else ""
                
            elif col_name.endswith("_jahr_show"):
                record[col_name] = str(dt_formatter.Year)
                
            elif col_name.endswith("_monat_show"):
                monat_namen = ["", "Januar", "Februar", "März", "April", "Mai", "Juni", 
                              "Juli", "August", "September", "Oktober", "November", "Dezember"]
                monat = dt_formatter.Month
                monat_name = monat_namen[monat] if 1 <= monat <= 12 else str(monat)
                record[col_name] = monat_name  # Deutscher Monatsname
                
            elif col_name.endswith("_tag_show"):
                record[col_name] = str(dt_formatter.Day)
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Befüllen der Show-Datum-Spalte {col_name}: {e}")
            record[col_name] = ""

    def _translate_dropdown_value(self, original_wert: Any, dropdown_config: dict) -> str:
        """
        Übersetzt einen Dropdown-Wert basierend auf der Konfiguration.
        
        Args:
            original_wert: Der Original-Schlüsselwert
            dropdown_config: Dropdown-Konfiguration mit table, key, value
            
        Returns:
            str: Übersetzter Anzeigewert oder Original-Wert als Fallback
        """
        try:
            if not original_wert or not dropdown_config:
                return str(original_wert) if original_wert else ""

            table_name = dropdown_config.get("table")
            guid = dropdown_config.get("key")
            value_field = dropdown_config.get("value")

            if table_name and guid and value_field:
                # Lade den Datensatz mit der GUID aus der Tabelle
                dropdown_db = PdvmCentralDatenbank(db_name=self.db_name, table_name=table_name, guid=guid)
                dropdown_data = dropdown_db.lesen()
                if dropdown_data and "ROOT" in dropdown_data:
                    group_data = dropdown_data["ROOT"].get(value_field, {})
                    werte = group_data.get("werte", [])
                    for eintrag in werte:
                        if str(eintrag.get("key")) == str(original_wert):
                            # Bevorzugt Deutsch, sonst Englisch, sonst Key
                            return eintrag.get("de") or eintrag.get("en") or str(original_wert)
                # Wenn keine Übersetzung gefunden, gib den Originalwert zurück
                return str(original_wert)

            # Fallback: Original-Wert zurückgeben
            return str(original_wert)

        except Exception as e:
            logger.error(f"❌ Fehler beim Übersetzen des Dropdown-Werts {original_wert}: {e}")
            return str(original_wert) if original_wert else ""

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
