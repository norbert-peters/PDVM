# pdvm_input_manager.py
# -*- coding: utf-8 -*-

import logging
import allgemeines as all
import json
from typing import List, Dict, Tuple, Any

from pd_datetime import Pdvm_DateTime, PdvmDateTimeUtils
from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)
logger.info("🔹 PdvmInputManager gestartet")

SYSTEM_USER_ID = "00000000-0000-0000-0000-000000000000"
TEMPLATE_GUID = "11111111-1111-1111-1111-111111111111"



class FieldMeta:
    def __init__(self, key: str, cfg: dict):
        self.key = key
        self.tooltip = cfg.get("tooltip", "")
        self.label = cfg.get("label", key)
        self.type = cfg.get("type", "text")
        self.historical = cfg.get("historical", False)
        self.has_abdatum = bool(cfg.get("abdatum", False))
        self.display_val = cfg.get("display_val", "all")
        self.display_ab = cfg.get("display_ab", "all")
        self.display_ti_val_short = cfg.get("display_ti_val_short", False)
        self.display_ti_ab_short = cfg.get("display_ti_ab_short", False)

        # UI widths
        self.ui_width_label = cfg.get("ui_width_label")
        self.ui_width_value = cfg.get("ui_width_value")
        self.ui_width_button = cfg.get("ui_width_button")
        self.ui_indent_ab = cfg.get("ui_indent_ab")

        # default widths
        self.width_label = cfg.get("width_label")
        self.width_control = cfg.get("width_control")
        self.width_button = cfg.get("width_button")
        self.width_indent_ab = cfg.get("width_indent_ab")
        self.width_frame = cfg.get("width_frame")

        # lookup dropdown definition
        self.dropdown_def = cfg.get("dropdown", {})
        self.dropdown_section = self.dropdown_def.get("value")
        self.dropdown_options = []

        # help definition
        self.help_def = cfg.get("help", {})
        self.help_text = ""
        self.help_header = ""
        # viewtable support
        if cfg.get("type") == "viewtable":
            self.viewtable_guid = None
            if "viewtable" in cfg and isinstance(cfg["viewtable"], dict):
                self.viewtable_guid = cfg["viewtable"].get("guid")
        else:
            self.viewtable_guid = None

class PdvmInputManager:
    def get_data_instance(self, feld_key: str):
        """
        Liefert die zentrale Dateninstanz für einen Feld-Key wie 'persondaten_PERSDATEN_ANREDE'.
        Das Mapping wird beim Initialisieren über self._build_instance_dict() aufgebaut.
        """
        # Normalisiere den Key auf Klein/Großschreibung wie im Mapping
        parts = feld_key.split('_')
        if len(parts) < 3:
            return None
        table = parts[0].lower()
        gruppe = parts[1].upper()
        # Das Mapping ist (table, gruppe) → Instanz
        key = (table, gruppe)
        inst = self.instance_dict.get(key)
        if inst is None:
            # Debug-Ausgabe für Fehleranalyse
            import logging
            logging.getLogger(__name__).error(f"[get_data_instance] Keine Instanz für Key={key} (feld_key={feld_key}) im Mapping: {list(self.instance_dict.keys())}")
        return inst
    def __init__(self, *args, **kwargs):
        super().__init__() if hasattr(super(), "__init__") else None
        # Zentrale Mappings für Abdatum- und Value-Instanzen
        self.abdatum_instance_map = {}  # key: feld_key, value: Pdvm_DateTime
        self.value_instance_map = {}    # key: feld_key, value: Pdvm_DateTime (nur type:datetime)

    def _ensure_instance_maps(self):
        if not hasattr(self, 'abdatum_instance_map') or self.abdatum_instance_map is None:
            self.abdatum_instance_map = {}
        if not hasattr(self, 'value_instance_map') or self.value_instance_map is None:
            self.value_instance_map = {}

    def register_abdatum_instance(self, key: str, inst: 'Pdvm_DateTime'):
        self._ensure_instance_maps()
        self.abdatum_instance_map[key] = inst

    def get_abdatum_instance(self, key: str):
        self._ensure_instance_maps()
        return self.abdatum_instance_map.get(key)

    def register_value_instance(self, key: str, inst: 'Pdvm_DateTime'):
        self._ensure_instance_maps()
        self.value_instance_map[key] = inst

    def get_value_instance(self, key: str):
        self._ensure_instance_maps()
        return self.value_instance_map.get(key)

    def assert_abdatum_instance(self, key: str):
        self._ensure_instance_maps()
        if key not in self.abdatum_instance_map:
            logger.error(f"[PdvmInputManager] Keine Abdatum-Instanz für {key} registriert!")
            raise RuntimeError(f"Abdatum-Instanz für {key} fehlt!")
        return self.abdatum_instance_map[key]

    def assert_value_instance(self, key: str):
        self._ensure_instance_maps()
        if key not in self.value_instance_map:
            logger.error(f"[PdvmInputManager] Keine Value-Instanz für {key} registriert!")
            raise RuntimeError(f"Value-Instanz für {key} fehlt!")
        return self.value_instance_map[key]
    def translate_dropdown_value(self, meta, key, lang="de"):
        """
        Übersetzt einen Dropdown-Key in den angezeigten Wert (z.B. 'm' -> 'Herr').
        Sucht in den Metadaten nach passenden Optionen.
        """
        opts = []
        if hasattr(meta, 'dropdown_options') and meta.dropdown_options:
            opts = meta.dropdown_options
        elif hasattr(meta, 'dropdown_def') and meta.dropdown_def:
            # Versuche, Optionen aus der Instanz zu holen (vereinfachte Fallback-Logik)
            # Hier ggf. erweitern, falls du eine zentrale Optionstabelle hast
            pass
        for opt in opts:
            if opt.get('key') == key:
                return opt.get(lang, opt.get('de', key))
        return str(key)
    # Entfernt: reload_instance, da Instanzverwaltung wie zuvor zentral bleibt
    def get_or_load_instance(self, table: str, guid: str):
        """
        Liefert eine zentrale Instanz für (table, guid). Holt sie aus dem Cache oder lädt sie neu.
        """
        key = (table, guid)
        if not hasattr(self, 'instance_dict'):
            self.instance_dict = {}
        if key not in self.instance_dict:
            self.instance_dict[key] = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name=table,
                guid=guid
            )
        return self.instance_dict[key]
    def _normalize_framedaten_keys(self, data: dict) -> dict:
        """
        Normalisiert alle Keys in den Framedaten auf tabelle.lower()_GRUPPE.FELD
        (nur Top-Level und 1. Ebene, wie in deiner Struktur üblich)
        """
        new_data = {}
        for grp_key, grp_val in data.items():
            # Gruppe bleibt wie sie ist (z.B. PERSDATEN, ANSCHRIFT_PERSON, ...)
            if not isinstance(grp_val, dict):
                new_data[grp_key] = grp_val
                continue
            new_grp = grp_key.upper()
            new_data[new_grp] = {}
            for fld_key, fld_val in grp_val.items():
                # Feld kann Bindestriche enthalten, aber keine weiteren Unterstriche
                # Wir normalisieren nur, falls der Key das Muster tabelle_gruppe_feld hat
                parts = fld_key.split("_")
                if len(parts) >= 3:
                    table = parts[0].lower()
                    grp = parts[1].upper()
                    fld = "_".join(parts[2:])
                    norm_key = f"{table}_{grp}_{fld}"
                else:
                    norm_key = fld_key
                new_data[new_grp][norm_key] = fld_val
        return new_data

    def normalize_key(self, key: str) -> str:
        """
        Normalisiert einen Key auf tabelle_gruppe_feld:
        - Tabelle: lower
        - Gruppe: upper
        - Feld: upper
        """
        parts = key.split("_")
        if len(parts) < 3:
            return key
        table = parts[0].lower()
        grp = parts[1].upper()
        fld = "_".join(parts[2:]).upper()
        return f"{table}_{grp}_{fld}"

    def normalize_dict_keys(self, d: dict) -> dict:
        """
        Gibt ein neues Dict zurück, in dem alle Keys normalisiert sind.
        (rekursiv für verschachtelte Dicts, falls nötig)
        """
        new_d = {}
        for k, v in d.items():
            norm_k = self.normalize_key(k)
            if isinstance(v, dict):
                new_d[norm_k] = self.normalize_dict_keys(v)
            else:
                new_d[norm_k] = v
        return new_d

    def _build_instance_dict(self):
        """
        Baut ein Dictionary {(table, gruppe): Instanz} für alle in den Metadaten vorkommenden Kombinationen auf.
        Loggt alle erzeugten Instanzen mit Tabelle, Gruppe und GUID.
        """
        self.instance_dict = {}
        combos = set()
        # Sammle alle tabelle_gruppe aus den Metadaten
        for field in self.fields.keys():
            parts = field.split("_")
            if len(parts) < 3:
                continue
            table = parts[0].lower()
            grp = parts[1].upper()
            combos.add((table, grp))
        # Ergänze: Instanzen für alle Dropdown- und Help-Tabellen/Groups
        for fm in self.fields.values():
            # Dropdown-Instanzen
            d = getattr(fm, 'dropdown_def', None)
            if fm.type == "dropdown" and d:
                dd_table = d.get("table", "").lower()
                dd_key = d.get("key", None)
                guid = dd_key  # Korrekt: GUID ist direkt der Key aus der Definition
                if dd_table and guid:
                    self.instance_dict[(dd_table, guid)] = PdvmCentralDatenbank(
                        db_name="PdvmManager.db",
                        table_name=dd_table,
                        guid=guid
                    )
                    logger.debug(f"[INSTANZ-ERZEUGUNG] (Dropdown) Tabelle={dd_table}, GUID={guid}, Gruppe=ROOT")
            # Help-Instanzen
            h = getattr(fm, 'help_def', None)
            if h:
                help_table = h.get("table", "").lower()
                help_key = h.get("key", None)
                guid = help_key  # Die GUID ist der help_key
                if help_table and guid:
                    self.instance_dict[(help_table, guid)] = PdvmCentralDatenbank(
                        db_name="PdvmManager.db",
                        table_name=help_table,
                        guid=guid
                    )
                    logger.debug(f"[INSTANZ-ERZEUGUNG] (Help) Tabelle={help_table}, GUID={guid}")
                    continue
        # Fallback für alle übrigen Kombis
        for table, grp in combos:
            if (table, grp) in self.instance_dict:
                continue
            if table == self.root_table.lower():
                guid = self.root_guid
            else:
                # Versuche GUID aus Root-Verweis zu ermitteln
                root_grp = self.root.data.get(grp, {})
                guid = None
                for k, v in root_grp.items():
                    if k.lower().startswith(table) and isinstance(v, dict):
                        if v:
                            max_key = max(v.keys(), key=lambda x: float(x))
                            guid = v[max_key]
                if not guid:
                    guid = TEMPLATE_GUID
            logger.debug(f"[INSTANZ-ERZEUGUNG] Tabelle={table}, Gruppe={grp}, GUID={guid}")
            self.instance_dict[(table, grp)] = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name=table,
                guid=guid
            )
            # Debug: Zeige geladene Daten
            logger.debug(f"[INSTANZ-DATEN] {table}[{guid}] = {self.instance_dict[(table, grp)].lesen()}")

    def _init_all_instances(self):
        """
        Initialisiert alle Instanzen rekursiv und baut das Mapping-Dict auf.
        """
        self._build_instance_dict()
        # self.instances wird nicht mehr verwendet

    def __init__(self, call_data: dict):
        self.call_data = call_data
        self.st_inst = call_data['stichtag_inst']
        self.stichtag = self.st_inst.PdvmDateTime
        frame_guid = call_data.get("frame_guid")
        if not frame_guid:
            raise ValueError("🔴 Keine frame_guid in call_data gefunden")
        frm_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="framedaten",
            guid=frame_guid
        )
        raw_frame = frm_db.lesen() or {}
        for section in list(raw_frame.keys()):
            # Nur Metadaten normalisieren, nicht ROOT!
            if section.lower() == "metadaten" and isinstance(raw_frame[section], dict):
                raw_frame[section] = self.normalize_dict_keys(raw_frame[section])
        root_frame = raw_frame.get("ROOT", {})
        logger.debug(f"[PdvmInputManager] Root-Frame-Daten: {json.dumps(root_frame, indent=2, ensure_ascii=False)}")    
        self.root_table = root_frame.get("root_table")
        if not self.root_table:
            raise ValueError("🔴 Keine root_table in den Framedaten gefunden")
        self.root_guid = call_data.get("root_guid")
        if not self.root_guid:
            raise ValueError("🔴 Keine root_guid in call_data gefunden")
        self.root = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name=self.root_table,
            guid=self.root_guid
        )
        self.root.data = self.normalize_dict_keys(self.root.data)
        md = raw_frame.get("Metadaten", {})
        self.fields: Dict[str, FieldMeta] = {
            k: FieldMeta(k, v) for k, v in md.items()
        }
        # UI-Defaults
        self.width_frame = root_frame.get("width_frame", 600)
        self.width_label = root_frame.get("width_label", 150)
        self.width_control = root_frame.get("width_control", 200)
        self.width_button = root_frame.get("width_button", 100)
        # width_indent_ab robust übernehmen (auch wenn 0 oder explizit gesetzt)
        if "width_indent_ab" in root_frame:
            self.width_indent_ab = root_frame["width_indent_ab"]
        else:
            self.width_indent_ab = 50
        logger.debug(f"[PdvmInputManager] width_indent_ab aus Framedaten: {root_frame.get('width_indent_ab')}, im Manager: {self.width_indent_ab}")
        logger.debug(f"[PdvmInputManager] UI-Größen: frame={self.width_frame}, label={self.width_label}, control={self.width_control}, button={self.width_button}, indent_ab={self.width_indent_ab}")
        self.header_text = root_frame.get("header_text", "Eingabemaske")
        self.display_st = root_frame.get("display_st", "all")
        self.display_time_short = root_frame.get("display_time_short", False)
        self.language = self.call_data.get("language", "de")
        # Instanzen initialisieren
        self._init_all_instances()
        logger.info("🔹 PdvmInputManager initialisiert")

    def _get_instance(self, table: str, grp: str, guid: str = None) -> Any:
        # Debug: Zeige alle Keys der Instanz-Dict
        logger.debug(f"[INSTANZ-KEYS] Verfügbare Keys in instance_dict: {list(self.instance_dict.keys())}")
        # Ermittle Instanz-Key with GUID (falls angegeben, sonst Root-GUID)
        if guid is None:
            if table == self.root_table.lower():
                guid = self.root_guid
            else:
                # Versuche GUID aus Root-Verweis zu ermitteln
                root_grp = self.root.data.get(grp, {})
                guid_dict = root_grp.get(f"{table.upper()}-{grp}", {})
                guid = None
                if isinstance(guid_dict, dict) and guid_dict:
                    max_key = max(guid_dict.keys(), key=lambda k: float(k))
                    guid = guid_dict[max_key]
                if not guid:
                    guid = TEMPLATE_GUID
        key = (table, grp)
        inst = self.instance_dict.get(key)
        logger.debug(f"[INSTANZ-LOOKUP] Suche Instanz für Key={key}: {'Gefunden' if inst else 'Nicht gefunden'}")
        return inst

    def get_dropdown_options(self, meta):
        """Liefert die Dropdown-Optionen für ein FeldMeta-Objekt stichtagsgenau über die zentrale Instanz."""
        d = getattr(meta, 'dropdown_def', None)
        if not d:
            return []
        table = d["table"].lower()
        guid = d.get("key", None)
        section = getattr(meta, 'dropdown_section', None) or d.get("value") or next(iter(d.values()), None)
        if not section:
            logger.warning(f"[Dropdown-Options] Kein Section/Feldname für Dropdown {meta.key}")
            return []
        inst = self.instance_dict.get((table, guid))
        if not inst:
            logger.warning(f"[Dropdown-Options] Keine Instanz für ({table}, {guid})")
            return []
        # Debug: Logge die verfügbaren Felder in der Instanz
        root_keys = list(getattr(inst, 'data', {}).get('ROOT', {}).keys())
        logger.debug(f"[Dropdown-Options] Instanz ({table}, {guid}) - ROOT-Keys: {root_keys}, section: {section}")
        data = inst.get_static_value('ROOT', section)
        logger.debug(f"[Dropdown-Options] Instanz ({table}, {guid}) - Daten für Feld '{section}': {data}")
        opts = []
        if isinstance(data, dict):
            opts = data.get("werte", []) or []
        elif isinstance(data, list):
            opts = data
        # Historische Filterung
        if getattr(meta, 'historical', False):
            opts = [o for o in opts if float(o.get("abdatum", 0)) <= self.st_inst.PdvmDateTime]
        logger.debug(f"[Dropdown-Options] Instanz ({table}, {guid}) - Optionen: {opts}")
        return sorted(opts, key=lambda o: float(o.get("abdatum", 0)))

    def get_help_text(self, meta, lang=None):
        """Liefert den Hilfetext für ein FeldMeta-Objekt über die zentrale Instanz."""
        h = getattr(meta, 'help_def', None)
        if not h:
            return ""
        help_table = h.get("table", "").lower()
        help_guid = h.get("key", None)
        help_value = h.get("value", None)
        logger.debug(f"[Help-Text] Suche Hilfe für ({help_table}, {help_guid}) mit Wert {help_value} und Sprache {lang}")
        if not (help_table and help_guid and help_value):
            return ""
        inst = self.instance_dict.get((help_table, help_guid))
        if not inst:
            logger.warning(f"[Help-Text] Keine Instanz für ({help_table}, {help_guid})")
            return ""
        val = inst.get_static_value('ROOT', help_value)
        logger.debug(f"[Help-Text] Hilfe-Daten: {val} - zu welcher ID {inst.guid} geladen")
        if not val:
            return ""
        if lang and isinstance(val, dict) and lang in val:
            return val[lang]
        return val.get("text", "")

    def get_help_header(self, meta, lang=None):
        h = getattr(meta, 'help_def', None)
        if not h:
            return ""
        help_table = h.get("table", "").lower()
        help_guid = h.get("key", None)
        help_value = h.get("value", None)
        if not (help_table and help_guid and help_value):
            return ""
        inst = self.instance_dict.get((help_table, help_guid))
        if not inst:
            return ""
        val = inst.get_static_value('ROOT', help_value)
        if not val:
            return ""
        if lang and isinstance(val, dict) and lang in val:
            return val[lang]
        return val.get("header", "")

    def translate_dropdown_value(self, meta, key, lang=None):
        """Übersetzt einen Dropdown-Key über die zentrale Instanz (optional sprachspezifisch)."""
        opts = self.get_dropdown_options(meta)
        for o in opts:
            if o.get("key") == key:
                if lang and lang in o:
                    return o[lang]
                return o.get("text", key)
        return key

    def get_fields(self) -> List[FieldMeta]:
        return list(self.fields.values())

    def _normalize_key(self, key: str):
        # Normalisiert einen Key auf (tabelle.lower(), gruppe.upper(), feld original)
        parts = key.split("_")
        if len(parts) < 3:
            return key, '', ''
        table = parts[0].lower()
        grp = parts[1].upper()
        fld = "_".join(parts[2:])
        return table, grp, fld

    def _normalize_key_from_view(self, key: str):
        """
        Extracts the correct (table, group) from a viewtable field key, which may be in the form 'root_PERSONDATEN_finanzdaten_GUID' or similar.
        Returns (table, group, field) with normalization (table.lower(), group.upper(), "").
        """
        # Normalisiert einen Key von Viewtable auf (tabelle.lower(), gruppe.upper(), feld original)
        # Beispiel: 'persondaten_PERDATEN_FINANZDATEN-FINANZDATEN' -> ('persondaten', 'PERDATEN', 'FINANZDATEN-FINANZDATEN')
        # Hier wird angenommen, dass der Key immer mindestens 3 Teile hat: tabelle_gruppe_feld
        table, grp, fld = self._normalize_key(key)  # Nutzt die normale Normalisierung
        parts = fld.split("-")
        if len(parts) < 2:
            return table, grp, fld
        else:
            # Wenn es Bindestriche gibt, nehmen wir den ersten Teil als Feld
            table = parts[0].lower()
            grp = parts[1].upper()
            fld = ""
        return table, grp, fld

    def get_value(self, key: str) -> Tuple[Any, float]:
        """
        Liefert immer (wert, ab_zeit) – für alle Typen. Für nicht-historische Felder ist ab_zeit immer 1001.0.
        """
        table, grp, fld = self._normalize_key(key)
        inst = self._get_instance(table, grp)
        if not inst:
            return "", 1001.0
        # Für alle Tabellen außer benutzerdaten: immer mit Stichtag (historisch)
        if table != "benutzerdaten":
            res = inst.get_value(grp, fld.upper(), self.st_inst.PdvmDateTime) or {}
        else:
            res = inst.get_value(grp, fld.upper()) or {}
        wert = res.get("wert", "")
        ab_zeit = float(res.get("ab_zeit", 1001.0))
        # Template-Logik: Wenn Instanz ist Template und Feld fehlt, lege es leer an und speichere
        if inst.guid == TEMPLATE_GUID and not res:
            # Leeres Feld anlegen
            if table != "benutzerdaten":
                inst.set_value(grp, fld.upper(), "", self.st_inst.PdvmDateTime)
            else:
                inst.set_value(grp, fld.upper(), "")
            inst.speichern(TEMPLATE_GUID, inst.data)
            wert = ""
            ab_zeit = self.st_inst.PdvmDateTime if table != "benutzerdaten" else 1001.0
        return wert, ab_zeit

    def get_value_all(self, key: str) -> Dict[Any, Any]:
        table, grp, fld = self._normalize_key(key)
        inst = self._get_instance(table, grp)
        if not inst:
            return {}
        return inst.get_value_all(grp, fld.upper()) or {}

    def set_value(self, key: str, value: Any, abdatum: float):
        """
        Setzt immer (wert, abdatum) – für alle Typen. Für nicht-historische Felder wird abdatum ignoriert.
        """
        table, grp, fld = self._normalize_key(key)
        inst = self._get_instance(table, grp)
        print(f"[DEBUG] PdvmInputManager.set_value: key={key}, value={value}, abdatum={abdatum}, inst_id={id(inst)}")
        # Für alle Typen: immer Wert + Ab-Datum übergeben
        if inst:
            print(f"[DEBUG] PdvmInputManager.set_value: Vorher inst.data[{grp}][{fld.upper()}]={inst.data.get(grp, {}).get(fld.upper(), 'N/A')}")
            inst.set_value(grp, fld.upper(), value, abdatum)
            print(f"[DEBUG] PdvmInputManager.set_value: Nachher inst.data[{grp}][{fld.upper()}]={inst.data.get(grp, {}).get(fld.upper(), 'N/A')}")

    def delete_value(self, key: str, abdatum: float) -> bool:
        table, grp, fld = self._normalize_key(key)
        inst = self._get_instance(table, grp)
        if not inst:
            return False
        grp_dict = inst.data.get(grp, {})
        field_dict = grp_dict.get(fld.upper())
        if not isinstance(field_dict, dict):
            return False
        ts_key = format(float(abdatum), ".5f")
        if ts_key in field_dict:
            del field_dict[ts_key]
            inst.data[grp][fld.upper()] = field_dict
            inst.save_values()
            logger.info(f"🔹 Historischen Eintrag gelöscht: {key} @ {ts_key}")
            return True
        return False

    def save_all(self):
        """
        Speichert alle Instanzen im Mapping genau einmal (inkl. Root und verknüpfte Instanzen).
        """
        for key, inst in self.instance_dict.items():
            logger.debug(f"🔹 Speichere Instanz {key} mit GUID {inst.guid}")
            inst.save_values()
        # last_root_guid in systemsteuerung setzen wie gehabt
        user_guid = self.call_data.get("user_guid")
        frame_guid = self.call_data.get("frame_guid")
        root_guid = getattr(self.root, "guid", None)
        if user_guid and frame_guid and root_guid:
            sys_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="systemsteuerung",
                guid=user_guid
            )
            raw = sys_db.lesen() or {}
            user_data = raw.get(user_guid, {}) if isinstance(raw.get(user_guid), dict) else {}
            frame_data = raw.get(frame_guid, {}) if isinstance(raw.get(frame_guid), dict) else {}
            frame_data["last_root_guid"] = root_guid
            sys_db.speichern(user_guid,{user_guid: user_data, frame_guid: frame_data})
 
    def reload_instance_guid(self, table: str, group: str, guid: str):
        """
        Lädt für die Instanz (table, group) die Daten der neuen GUID in die bestehende Instanz.
        """
        key = (table, group)
        inst = self.instance_dict.get(key)
        if inst:
            inst.read_guid(guid)

    def get_abdatum_for_field(self, key: str, abdatum: float = None) -> float:
        """
        Gibt für ein Feld immer das passende Ab-Datum zurück:
        - Wenn das Feld has_abdatum, wird das übergebene oder aktuelle Ab-Datum verwendet.
        - Sonst wird immer 1001.0 zurückgegeben.
        """
        meta = self.fields.get(key)
        if meta and meta.has_abdatum:
            return abdatum if abdatum is not None else self.st_inst.PdvmDateTime
        return 1001.0

    def validate_value(self, key: str, value: Any) -> bool:
        """
        Zentrale Validierung für ein Feld:
        - Pflichtfeldprüfung (optional: in Metadaten definieren)
        - Wertebereich (optional: in Metadaten definieren)
        - Typprüfung
        Rückgabe: True = gültig, False = ungültig
        """
        meta = self.fields.get(key)
        if not meta:
            return True
        # Pflichtfeldprüfung
        if getattr(meta, 'required', False) and (value is None or value == ""):
            return False
        # Wertebereich (optional)
        if hasattr(meta, 'min') and value is not None:
            try:
                if float(value) < float(meta.min):
                    return False
            except Exception:
                pass
        if hasattr(meta, 'max') and value is not None:
            try:
                if float(value) > float(meta.max):
                    return False
            except Exception:
                pass
        # Typprüfung (optional)
        # ...weitere Prüfungen möglich...
        return True

    def get_abdatum_instance_for_field(self, key: str):
        """
        Gibt die Pdvm_DateTime-Instanz für das Ab-Datum eines Feldes zurück (sofern vorhanden).
        Liefert None, falls keine Instanz gefunden wird.
        """
        table, grp, fld = self._normalize_key(key)
        inst = self._get_instance(table, grp)
        if not inst:
            return None
        # Annahme: Die Instanz hält das Ab-Datum als Pdvm_DateTime-Objekt pro Feld im Attribut abdatum_dict
        # oder als Property/Methode. Hier als Beispiel ein dict:
        abdatum_dict = getattr(inst, 'abdatum_dict', None)
        if abdatum_dict and fld.upper() in abdatum_dict:
            return abdatum_dict[fld.upper()]
        # Fallback: Falls Instanz direkt ein Attribut abdatum hat (z.B. für Einzel-Feld-Tabellen)
        if hasattr(inst, 'abdatum'):
            return getattr(inst, 'abdatum')
        return None

    def check_root_structure(self, required_fields: list, logger=None):
        """
        Utility: Prüft, ob alle geforderten Felder/Keys im ROOT der Instanz vorhanden sind und ob die Werte-Arrays korrekt sind.
        Gibt für fehlende oder fehlerhafte Felder ein Log/Print aus.
        """
        if logger is None:
            logger = logging.getLogger(__name__)
        root_data = getattr(self.root, 'data', {})
        root_section = root_data.get("ROOT", {})
        all_ok = True
        for field in required_fields:
            entry = root_section.get(field)
            if not entry:
                logger.error(f"[ROOT-PRÜFUNG] Feld '{field}' fehlt in ROOT!")
                all_ok = False
                continue
            if not isinstance(entry, dict):
                logger.error(f"[ROOT-PRÜFUNG] Feld '{field}' ist kein Dict!")
                all_ok = False
                continue
            werte = entry.get("werte")
            if not isinstance(werte, list):
                logger.error(f"[ROOT-PRÜFUNG] Feld '{field}' hat keine 'werte'-Liste!")
                all_ok = False
                continue
            # Optional: Prüfe, ob jeder Wert einen 'key' und ggf. Übersetzungen hat
            for idx, w in enumerate(werte):
                if "key" not in w:
                    logger.warning(f"[ROOT-PRÜFUNG] Feld '{field}', Wert {idx} fehlt 'key'!")
                # Optional: weitere Checks auf 'de', 'en', 'abdatum' etc.
        if all_ok:
            logger.info("[ROOT-PRÜFUNG] Alle geforderten Felder/Keys sind korrekt in ROOT vorhanden.")
        return all_ok
