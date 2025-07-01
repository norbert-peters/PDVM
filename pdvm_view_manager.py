# pdvm_view_manager.py
import json
from typing import Optional, Dict, List, Tuple
from datetime import date
from pd_datetime import Pdvm_DateTime
from pdvm_central_datenbank import PdvmCentralDatenbank
import logging

logger = logging.getLogger(__name__)
SYSTEM_USER_ID = "00000000-0000-0000-0000-000000000000"


def has_content(eintrag: dict, suchfelder: List[str], debug: bool = False) -> bool:
    """
    Prüft, ob ein Eintrag in mindestens einem der Suchfeldern nicht leer ist.
    """
    for feld in suchfelder:
        wert = eintrag.get(feld)
        if debug:
            logging.debug(f"Prüfe Feld '{feld}': Wert = {wert!r}")
        if wert is None:
            continue
        if isinstance(wert, str) and wert.strip() == "":
            continue
        if isinstance(wert, (list, dict)) and not wert:
            continue
        return True
    return False


class PdvmViewManager:
    def __init__(self, call_daten: dict):
        logging.info("PdvmViewManager initialisiert.")
        self.call_daten = call_daten

        # 1) user_guid & view_guid extrahieren
        self.user_guid = call_daten.get("user_guid")
        self.view_guid = call_daten.get("view_guid")
        if isinstance(self.view_guid, dict):
            self.view_guid = self.view_guid.get("wert")
        self.mode = call_daten.get("mode", None)

        # 2) View-Metadaten aus "viewdaten" lesen
        view_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="viewdaten",
            guid=self.view_guid
        )
        logger.debug(f"View GUID: {self.view_guid}")
        raw_view = view_db.lesen() or {}
        logger.debug(f"raw_view: {raw_view}")
        root_view = raw_view.get("ROOT", {})
        logger.debug(f"root_view: {root_view}")

        # 3) view_table, history etc. aus ROOT auslesen
        vt = root_view.get("view_table")
        logger.debug(f"view_table:{ root_view.get("view_table")}")
        if not vt:
            raise ValueError(f"View '{self.view_guid}' hat keine view_table definiert.")
        self.view_table = vt
        self.root_history = bool(root_view.get("history", False))
        self.historisch = bool(root_view.get("historisch", False))
        self.display_width = root_view.get("display_width", "100%")

        # Metadata
        raw_metadata = raw_view.get("metadata", {})
        self.metadata = {k.lower(): v for k, v in raw_metadata.items()}
        vt_key = self.view_table.lower()
        if vt_key not in self.metadata:
            self.metadata[vt_key] = {"felder": []}

        # 4) Zeitverwaltung
        self.dt_instance = Pdvm_DateTime("DEU")
        self.current_time = self.dt_instance.PdvmDateTimeNow()
        # zentraler ST Instanz statt float
        self.st_inst: Pdvm_DateTime = call_daten.get('stichtag_inst', self.dt_instance)
        self.stichtag = float(self.st_inst.PdvmDateTime)

        # 5) Steuerungsdaten
        steuerung_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="systemsteuerung",
            guid=SYSTEM_USER_ID
        )
        self.steuerung_data_sys = steuerung_db.lesen() or {}

        user_ctrl_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="systemsteuerung",
            guid=self.user_guid
        )
        self.steuerung_data_user = user_ctrl_db.lesen() or {}

        # 6) Temp-View Cache
        self.user_view_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="benutzerviews",
            guid=None
        )
        self.user_view_data: Dict[str, List[dict]] = {}

        # 7) Lookup-Daten
        self.lookup_data: Dict[str, List[dict]] = root_view.get("lookups", {})




    def get_view_definition(self, table: str) -> dict:
        fields = self.metadata.get(table, {}).get("felder", [])
        return {
            "columns": [
                {
                    "name":       f.get("name", f.get("feld")),
                    "type":       f.get("type", "string"),
                    "searchable": f.get("ui", {}).get("searchable", False),
                    "sortable":   f.get("ui", {}).get("sortable", False),
                    "filterType": f.get("ui", {}).get("filterType", "contains"),
                    "selectable": f.get("ui", {}).get("selectable", True),
                    "lookup":     f.get("lookup"),
                }
                for f in fields
            ]
        }

    def get_temp_view(self, table: str) -> List[dict]:
        self._aktualisiere_temp_view()
        return self.user_view_data.get(table, [])

    def get_lookup_options(self, lookup_def: dict) -> List:
        if not lookup_def:
            return []
        tbl = lookup_def.get("table")
        val_field = lookup_def.get("value")
        return [row.get(val_field) for row in self.lookup_data.get(tbl, [])]

    def get_lookup_display_value(self, lookup_def: dict, key) -> str:
        logging.debug(f"get_lookup_display_value: {lookup_def}, key={key}")
        if not lookup_def or key is None:
            return ""
        tbl = lookup_def.get("table")
        tbl_id = lookup_def.get("key")
        val_key = lookup_def.get("value")
        if not tbl or not tbl_id or not val_key:
            return str(key)

        tbl_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name=tbl,
            guid=tbl_id
        )
        raw = tbl_db.lesen() or {}
        root_raw = raw.get("ROOT", {})
        inner = root_raw.get(val_key, {}) or {}
        werte = inner.get("werte", []) if isinstance(inner, dict) else []
        candidates = [w for w in werte if w.get("key") == key]
        if not candidates:
            return str(key)
        if self.historisch:
            valid = [w for w in candidates if float(w.get("abdatum", 0)) <= self.stichtag]
            best = max(valid, key=lambda w: float(w.get("abdatum", 0))) if valid else candidates[0]
        else:
            best = candidates[0]
        return best.get("de", str(key))

    def pdvm_to_date(self, pdvm_value: float) -> date:
        self.dt_instance.PdvmDateTime = pdvm_value
        return self.dt_instance.Date

    def _aktualisiere_temp_view(self):
        """
        Erzeugt oder lädt den gecachten View basierend auf Stichtag-Instanz.
        """
        table = self.view_table
        # Globale Steuerungsdaten
        ts_ctrl = self.steuerung_data_sys.get(table, {}).get("last_change")
        # Benutzersteuerdaten für diese View
        user_entry = self.steuerung_data_user.setdefault(self.view_guid, {})
        ts_user = user_entry.get("last_created_at")
        cache_key = f"{self.user_guid}_{self.view_guid}"

        # Entscheidung, ob neu gebaut werden muss
        rebuild = (
            ts_user is None
            or ts_ctrl is None
            or ts_ctrl > ts_user
            or user_entry.get("stichtag") != self.st_inst.PdvmDateTime
            or table not in self.user_view_data
        )

        if rebuild:
            # Neu erzeugen
            data = self._erzeuge_view_daten(table) or []
            self.user_view_data[table] = data

            # Cache speichern
            payload = {"ROOT": {table: data}}
            self.user_view_db.guid = cache_key
            self.user_view_db.data = payload
            self.user_view_db.speichern(cache_key, payload)

            # Benutzersteuerdaten aktualisieren
            user_entry.update({
                "last_created_at": self.current_time,
                "stichtag":        self.st_inst.PdvmDateTime,
                "last_accessed":   self.current_time,
                "status":          "ready",
                "row_count":       len(data)
            })
            # Persist
            PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="systemsteuerung",
                guid=self.user_guid
            ).speichern(self.user_guid, self.steuerung_data_user)

            logging.info(f"Neu erstellt {len(data)} Einträge für '{table}'.")
        else:
            # Aus Cache laden
            raw_cached = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="benutzerviews",
                guid=cache_key
            ).lesen() or {}
            data = raw_cached.get("ROOT", {}).get(table, []) or []
            self.user_view_data[table] = data

            # Zugriffsdaten aktualisieren
            user_entry["last_accessed"] = self.current_time
            PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="systemsteuerung",
                guid=self.user_guid
            ).speichern(self.user_guid, self.steuerung_data_user)

            logging.info(f"Geladen {len(data)} zwischengespeicherte Einträge für '{table}'.")

    def _erzeuge_view_daten(self, table):
        fields = self.metadata.get(table, {}).get("felder", [])

        all_ds = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name=table,
            guid=None
        ).lesen_alle() or []
        view_data = []
        skipped = 0
        searchable = [f.get("name", f.get("feld")) for f in fields if f.get("ui", {}).get("searchable")]
        for ds in all_ds:
            uid = ds.get("uid")
            if uid == SYSTEM_USER_ID:
                continue

            # --------------- Neu: wir nehmen alle Keys außer "uid" ---------------
            data = {k: v for k, v in ds.items() if k != "uid"}
            # --------------------------------------------------------------------


            entry = {"GUID": uid}

            for f in fields:
                grp = f.get("gruppe", "").upper()
                fld = f.get("feld", "").upper()
                name = f.get("name", fld)

                if self.historisch:
                    val = self._get_value(grp, fld, data, self.stichtag)
                else:
                    val = self._get_value_only(grp, fld, data)
                entry[name] = val

                if f.get("type") == "date" and val is not None:
                    self.dt_instance.PdvmDateTime = float(val)
                    d, m, y = self.dt_instance.Day, self.dt_instance.Month, self.dt_instance.Year
                    entry[f"{name}_tag"] = f"{d:02d}"
                    entry[f"{name}_monat"] = f"{m:02d}"
                    entry[f"{name}_jahr"] = str(y)

            if searchable and not has_content(entry, searchable):
                skipped += 1
                continue
            view_data.append(entry)
        if not view_data:
            logging.warning(f"Keine Daten für View '{table}' gefunden.")
            return None
        else:
            logging.info(f"View '{table}' erstellt mit {len(view_data)} Einträgen, {skipped} übersprungen.")
            return view_data

    def _get_value(self, gruppe, feld, daten, ab_zeit):
        grp = daten.get(gruppe, {}) or {}
        valr = grp.get(feld, {}) or {}
        if not isinstance(valr, dict):
            return None
        times = [float(t) for t in valr.keys() if float(t) <= float(ab_zeit)]
        if not times:
            return None
        best = format(max(times), ".5f")
        return valr.get(best)

    def _get_value_only(self, gruppe, feld, daten):
        grp = daten.get(gruppe, {}) or {}
        val = grp.get(feld)
        if isinstance(val, dict):
            times = sorted(float(t) for t in val.keys())
            if not times:
                return None
            key = format(times[-1], ".5f")
            return val.get(key)
        return val

    def query_view(
        self,
        table: str,
        filters: Optional[Dict[str, dict]] = None,
        sort: Optional[List[Tuple[str, str]]] = None,
        page: int = 0,
        page_size: int = 50
    ) -> Tuple[List[dict], int]:
        data = self.get_temp_view(table)
        if filters:
            data = self._apply_filters(data, filters)
        if sort:
            for col, d in reversed(sort):
                non_null = [r for r in data if r.get(col) is not None]
                nulls = [r for r in data if r.get(col) is None]
                non_null.sort(key=lambda r: r.get(col), reverse=(d == "desc"))
                data = non_null + nulls
        total = len(data)
        start = page * page_size
        end = start + page_size
        return data[start:end], total

    def _apply_filters(self, data: List[dict], filters: Dict[str, dict]) -> List[dict]:
        out = []
        for row in data:
            ok = True
            for col, f in filters.items():
                v = row.get(col)
                t = f.get("type")
                if t == "contains" and f.get("value", "").lower() not in str(v or "").lower():
                    ok = False
                elif t == "dropdown" and v != f.get("value"):
                    ok = False
                elif t == "dateRange":
                    row_date = self.pdvm_to_date(float(v)) if v is not None else None
                    fr, to = f.get("from"), f.get("to")
                    if row_date is None or (fr and row_date < fr) or (to and row_date > to):
                        ok = False
                if not ok:
                    break
            if ok:
                out.append(row)
        return out
