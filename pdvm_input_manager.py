# pdvm_input_manager.py
# -*- coding: utf-8 -*-

import logging
import json
from typing import List, Dict, Tuple, Any

from pd_datetime import Pdvm_DateTime
from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)

SYSTEM_USER_ID = "00000000-0000-0000-0000-000000000000"
TEMPLATE_GUID = "11111111-1111-1111-1111-111111111111"



class FieldMeta:
    def __init__(self, key: str, cfg: dict):
        self.key = key
        self.tooltip = cfg.get("tooltip", "")
        self.label = cfg.get("label", key)
        self.type = cfg.get("type", "text")
        self.historical = cfg.get("historical", False)
        self.abdatum = bool(cfg.get("abdatum", False))
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

        # viewtable definition
        self.viewtable_def = cfg.get("viewtable", {})
        self.viewtable_guid = self.viewtable_def.get("guid")  # ViewTable-GUID aus Framedaten

        # help definition
        self.help_def = cfg.get("help", {})
        self.help_text = ""
        self.help_header = ""
        # viewtable support (entfernt, wird wie Text behandelt)

class PdvmInputManager:
    def _debug_dump_metadaten(self, metadaten):
        logger.info("[Meta-Analyse] --- Übersicht aller Felder und Zuordnungen ---")
        for k, v in metadaten.items():
            table = k.split('_')[0].lower() if '_' in k else k.lower()
            source_path = v.get('source_path', None)
            dropdown = v.get('dropdown', {})
            helpdef = v.get('help', {})
            logger.info(f"[Meta-Analyse] Feld={k:40} | table={table:12} | source_path={str(source_path):8} | dropdown={dropdown.get('table','')} | help={helpdef.get('table','')}")
        logger.info("[Meta-Analyse] --- Ende Übersicht ---")
    def ensure_instance_for_guid(self, table: str, group: str, guid: str, path: str = None):
        """
        Stellt sicher, dass für (table, guid, path) eine Instanz mit gültiger Datenstruktur existiert.
        Falls nicht vorhanden, wird sie über den InstanceManager angelegt.
        """
        if not self.instance_manager:
            raise RuntimeError("[PdvmInputManager] InstanceManager nicht gesetzt!")
        inst = self.instance_manager.get_instance(table, path)
        if inst and getattr(inst, 'data', None):
            return  # Instanz mit Daten existiert
        # Falls Instanz leer, initialisiere Datenstruktur
        if inst is not None and not getattr(inst, 'data', None):
            inst.data = {group: {}}
            inst.speichern(guid, inst.data)
        import logging
        logging.info(f"[ensure_instance_for_guid] Neue Instanz für {table}, {group}, GUID={guid}, path={path} angelegt und gespeichert.")

    # Nach Instanz-/GUID-Update: Abdatum für jedes Feld neu bestimmen
    def update_abdatum_for_fields(self):
        """
        Aktualisiert das Abdatum für alle Felder nach einer Stichtag-Änderung.
        Geht durch alle registrierten Abdatum-Instanzen und holt den neuen Wert samt Abdatum.
        Prüft auch ViewTable-Verbindungen und lädt bei GUID-Änderung neue Daten.
        """
        # Sammle ViewTable-Referenz-Felder (die auf andere Tabellen verweisen)
        # ViewTable-Felder erkennt man am Bindestrich im Feldnamen (z.B. FINANZDATEN-FINANZDATEN)
        viewtable_ref_fields = {}
        for key, field in self.fields.items():
            parts = key.split('_')
            if len(parts) >= 3:
                table = parts[0].lower()
                grp = parts[1].upper()
                fld = '_'.join(parts[2:]).upper()
                if '-' in fld:  # ViewTable-Referenz-Feld
                    viewtable_ref_fields[key] = (table, grp, fld)
                    logger.debug(f"[ViewTable-Ref] Erkenne ViewTable-Referenz: {key} -> {table}.{grp}.{fld}")
        
        # Erst die normalen Felder aktualisieren
        for key, abdatum_inst in getattr(self, 'abdatum_instance_map', {}).items():
            try:
                value, abdatum = self.get_value(key)
                abdatum_inst.PdvmDateTime = abdatum
                logger.debug(f"[update_abdatum_for_fields] Feld {key}: Abdatum aktualisiert auf {abdatum}")
            except Exception as e:
                logger.error(f"[update_abdatum_for_fields] Fehler beim Aktualisieren von Feld {key}: {e}")
        
        # Jetzt ViewTable-GUIDs neu auflösen und bei Änderung read_guid() aufrufen
        for ref_key, (ref_table, ref_grp, ref_fld) in viewtable_ref_fields.items():
            try:
                # Hole die neue GUID für das Referenz-Feld (stichtagsabhängig)
                ref_value, ref_abdatum = self.get_value(ref_key)
                new_guid = ref_value
                
                if new_guid:
                    logger.debug(f"[ViewTable-Update] Feld {ref_key}: Neue GUID={new_guid}")
                    
                    # Bestimme die Tabelle der ViewTable (aus dem ersten Teil des Feldnamens)
                    viewtable_name = ref_fld.split('-')[0].lower()
                    logger.debug(f"[ViewTable-Update] ViewTable-Name: {viewtable_name}")
                    
                    # Finde alle Felder, die zu dieser ViewTable gehören
                    viewtable_fields = []
                    for field_key, field in self.fields.items():
                        field_parts = field_key.split('_')
                        if len(field_parts) >= 3:
                            field_table = field_parts[0].lower()
                            if field_table == viewtable_name:
                                viewtable_fields.append((field_key, field))
                                logger.debug(f"[ViewTable-Update] Gefunden ViewTable-Feld: {field_key}")
                    
                    # Aktualisiere alle ViewTable-Felder mit der neuen GUID
                    for vt_key, vt_field in viewtable_fields:
                        if hasattr(vt_field, 'data_instance'):
                            old_guid = getattr(vt_field.data_instance, 'guid', None)
                            if old_guid != new_guid:
                                logger.debug(f"[ViewTable-Update] Feld {vt_key}: GUID geändert von {old_guid} zu {new_guid}, lade neue Daten")
                                vt_field.data_instance.read_guid(new_guid)
                            else:
                                logger.debug(f"[ViewTable-Update] Feld {vt_key}: GUID unverändert ({new_guid})")
                        
            except Exception as e:
                logger.error(f"[ViewTable-Update] Fehler beim Aktualisieren von ViewTable-Feld {ref_key}: {e}")
        
        logger.debug(f"[update_abdatum_for_fields] Abgeschlossen: {len(viewtable_ref_fields)} ViewTable-Referenzen geprüft")
    def __init__(self, call_data: dict, instance_manager=None):
        # Felder-Dict initialisieren, damit es IMMER existiert (auch wenn leer)
        self.fields: Dict[str, FieldMeta] = {}
        # --- Schritt 1: Framedaten und Metadaten laden ---
        frame_guid = call_data.get("frame_guid")
        if not frame_guid:
            raise ValueError("[PdvmInputManager] frame_guid fehlt in call_data!")
        frm_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="framedaten",
            guid=frame_guid
        )
        raw_frame = frm_db.lesen()  # Lese die Framedaten aus der Datenbank
        if not raw_frame:
            raise ValueError("[PdvmInputManager] Keine Framedaten gefunden!")
        root_frame = raw_frame.get("ROOT", {})
        for section in list(raw_frame.keys()):
            # Nur Metadaten normalisieren, nicht ROOT!
            if section.lower() == "metadaten" and isinstance(raw_frame[section], dict):
                raw_frame[section] = self.normalize_dict_keys(raw_frame[section])
        md = raw_frame.get("Metadaten", {})
        logger.debug(f"[DEBUG] Metadaten im Konstruktor: Typ={type(md)}, Keys={list(md.keys()) if isinstance(md, dict) else md}")
        self._debug_dump_metadaten(md)
        if not md:
            logger.error("[PdvmInputManager] Keine Metadaten gefunden! Es werden keine Felder erzeugt.")

        # --- UI-Parameter und root_table setzen ---
        self.root_table = root_frame.get("root_table")
        if not self.root_table:
            raise ValueError("[PdvmInputManager] root_table fehlt in Framedaten!")
        self.header_text = root_frame.get("header_text", "Eingabemaske")
        self.display_st = root_frame.get("display_st", "all")
        self.display_time_short = root_frame.get("display_time_short", False)
        self.width_frame = root_frame.get("width_frame", 600)
        self.width_label = root_frame.get("width_label", 150)
        self.width_control = root_frame.get("width_control", 200)
        self.width_button = root_frame.get("width_button", 100)
        self.width_indent_ab = root_frame.get("width_indent_ab", 50)
        self.language = call_data.get("language", "de")
        self.call_data = call_data
        self.st_inst = call_data.get('stichtag_inst')

        # --- Root-Instanz-Handler (immer mit GUID) ---
        self.root_guid = call_data.get("root_guid")
        if not self.root_guid:
            raise ValueError("[PdvmInputManager] root_guid fehlt in call_data!")
        self.instance_manager = instance_manager
        if not self.instance_manager:
            raise RuntimeError("[PdvmInputManager] InstanceManager muss vor Initialisierung gesetzt werden!")
        # --- Root-Instanz wird EINMALIG erzeugt und bleibt für die Lebensdauer des InputWidgets konstant ---

        self._root = self.instance_manager.get_instance(self.root_table, 'root')
        if self._root is None:
            raise RuntimeError("[PdvmInputManager] Root-Instanz konnte nicht erzeugt werden! Prüfe InstanceManager und Metadaten.")
        self._root.guid = self.root_guid
        self._root.lesen()  # Daten laden

        # --- Felder aus Metadaten extrahieren ---
        feld_count = 0
        if md:
            for k, v in md.items():
                try:
                    k_lower = k.lower()
                    logger.debug(f"[DEBUG] Metadaten-Schleife: Bearbeite Feld {k_lower}")
                    meta = FieldMeta(k_lower, v)
                    # source_path MUSS in den Metadaten stehen
                    source_path = v.get('source_path')
                    if not source_path:
                        logger.warning(f"[InputManager] source_path fehlt für Feld {k_lower} in den Metadaten! Setze Fallback 'root'.")
                        source_path = 'root'
                    # Tabelle pro Feld korrekt bestimmen (aus Metadaten, sonst root_table)
                    table = v.get('table', self.root_table).lower() if v.get('table', self.root_table) else None
                    guid = self.root_guid
                    meta.data_instance = None
                    if hasattr(self, 'instance_manager') and self.instance_manager:
                        # Fehler, falls source_path None
                        if source_path is None:
                            raise RuntimeError(f"[InputManager] source_path ist None für Feld {k_lower} (table={table}) beim Metadaten-Initialisieren – dies ist ein Programmierfehler! Metadaten prüfen.")
                        meta.data_instance = self.instance_manager.get_instance(table, source_path)
                    # Dropdown-Instanz zuweisen (exakt nach Framedaten)
                    meta.dropdown_instance = None
                    if meta.dropdown_def:
                        dropdown_table = meta.dropdown_def.get("table") or meta.dropdown_def.get("tabelle")
                        dropdown_guid = meta.dropdown_def.get("key") or meta.dropdown_def.get("guid")
                        dropdown_source_path = meta.dropdown_def.get("source_path") or source_path
                        if not dropdown_source_path:
                            raise RuntimeError(f"[InputManager] source_path fehlt für Dropdown von Feld {k_lower} in den Metadaten!")
                        if dropdown_table and dropdown_guid and hasattr(self, 'instance_manager') and self.instance_manager:
                            # Fehler, falls dropdown_source_path None
                            if dropdown_source_path is None:
                                raise RuntimeError(f"[InputManager] dropdown_source_path ist None für Dropdown von Feld {k_lower} (table={dropdown_table}) – dies ist ein Programmierfehler! Metadaten prüfen.")
                            meta.dropdown_instance = self.instance_manager.get_instance(dropdown_table, dropdown_source_path)
                            logger.debug(f"[Zuweisung] Field={k_lower} Dropdown-Table={dropdown_table} GUID={dropdown_guid} source_path={dropdown_source_path} -> Instanz={meta.dropdown_instance}")
                    # Hilfe-Instanz zuweisen (exakt nach Framedaten)
                    meta.help_instance = None
                    if meta.help_def:
                        help_table = meta.help_def.get("table") or meta.help_def.get("tabelle")
                        help_guid = meta.help_def.get("key") or meta.help_def.get("guid")
                        help_source_path = meta.help_def.get("source_path") or source_path
                        if not help_source_path:
                            raise RuntimeError(f"[InputManager] source_path fehlt für Hilfe von Feld {k_lower} in den Metadaten!")
                        if help_table and help_guid and hasattr(self, 'instance_manager') and self.instance_manager:
                            # Fehler, falls help_source_path None
                            if help_source_path is None:
                                raise RuntimeError(f"[InputManager] help_source_path ist None für Hilfe von Feld {k_lower} (table={help_table}) – dies ist ein Programmierfehler! Metadaten prüfen.")
                            meta.help_instance = self.instance_manager.get_instance(help_table, help_source_path)
                    self.fields[k_lower] = meta
                    logger.debug(f"[DEBUG] Feld hinzugefügt: {k_lower}")
                    feld_count += 1
                except Exception as e:
                    logger.error(f"[DEBUG] Fehler beim Hinzufügen des Feldes {k}: {e}")
        
        if feld_count == 0:
            logger.error("[PdvmInputManager] Es wurden keine Felder erzeugt! Prüfe die Metadaten und Framedaten.")
        else:
            logger.info(f"[PdvmInputManager] {feld_count} Felder erfolgreich initialisiert.")

        # Instanzen initialisieren
        self._build_instance_dict()
    @property
    def root(self):
        """
        Die Root-Instanz (readonly):
        - Wird nur einmal beim Initialisieren gesetzt und darf nicht ersetzt werden.
        - Bleibt für die Lebensdauer des InputWidgets konstant.
        - Ein explizites Neuladen erfolgt nur über einen gezielten Refresh (z.B. Stichtag- oder GUID-Wechsel).
        """
        return self._root

    @root.setter
    def root(self, value):
        raise AttributeError("Die Root-Instanz darf nicht neu gesetzt werden! Sie bleibt für die Lebensdauer des InputWidgets konstant.")
    # Entfernt: zweiter, leerer __init__-Konstruktor, da dieser den eigentlichen Konstruktor überschreibt!

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

    # Instanzverwaltung erfolgt ausschließlich über den zentralen InstanceManager!
    # Diese Methode ist entfernt, alle Instanzen müssen über InstanceManager bezogen werden.
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
        Erzeugt für jedes Feld eine Instanz und weist sie direkt dem Feld zu.
        Nach der Initialisierung werden Instanzen nicht mehr über Keys gesucht, sondern direkt referenziert.
        Für viewtable-Felder wird die GUID dynamisch über das referenzierende Feld geholt.
        Die Root-Instanz (self.root) wird dabei immer nur einmal erzeugt und bleibt für die Lebensdauer des InputWidgets konstant.
        """
        for field in self.fields.values():
            parts = field.key.split("_")
            if len(parts) < 3:
                continue
            table = parts[0].lower()
            grp = parts[1].upper()
            
            # Für alle Felder der Root-Tabelle IMMER die bereits erzeugte Root-Instanz verwenden!
            if table == self.root_table.lower():
                field.data_instance = self.root
                field.data_guid = self.root_guid
                logger.debug(f"[INSTANZ-ZUWEISUNG] Root-Tabelle={table}, GUID={self.root_guid}, Field={field.key}, Instanz={field.data_instance}")
            else:
                # Für viewtable-Felder (erkennbar am '-' im Feldnamen): GUID dynamisch aus referenzierendem Feld holen
                source_path = 'root'  # Default
                guid = None
                
                # Suche nach referenzierendem viewtable-Feld in Root-Tabelle
                # Format: {root_table}_{GRUPPE}_{tabelle}-{gruppe} (case-sensitive)
                ref_key = f"{self.root_table.lower()}_{grp}_{table}-{grp.lower()}"
                ref_key_alt1 = f"{self.root_table.lower()}_{grp.upper()}_{table.upper()}-{grp.upper()}"
                ref_key_alt2 = f"{self.root_table.lower()}_{grp.upper()}_{grp.upper()}-{grp.upper()}"
                
                # Alle möglichen Referenz-Keys prüfen
                for potential_key in [ref_key, ref_key_alt1, ref_key_alt2]:
                    if potential_key in self.fields:
                        ref_key = potential_key
                        break
                else:
                    # Fallback: Alle Felder durchsuchen, die das Muster enthalten
                    for key in self.fields.keys():
                        if f"_{table}-" in key.lower() or f"_{grp.lower()}-" in key.lower():
                            ref_key = key
                            break
                
                if ref_key in self.fields:
                    # GUID aus referenzierendem Feld über Root-Instanz holen
                    try:
                        # Normalisiere den Referenz-Key um Gruppe und Feld zu extrahieren
                        parts = ref_key.split("_")
                        if len(parts) >= 3:
                            ref_table = parts[0].lower()
                            ref_grp = parts[1].upper()
                            ref_fld = "_".join(parts[2:]).upper()
                            
                            # Für viewtable-Felder: Das Feld beschreibt Tabelle-Gruppe (z.B. FINANZDATEN-FINANZDATEN)
                            # Extrahiere die Ziel-Tabelle und -Gruppe aus dem Feldnamen
                            if '-' in ref_fld:
                                fld_parts = ref_fld.split('-')
                                if len(fld_parts) == 2:
                                    target_table = fld_parts[0].lower()  # FINANZDATEN -> finanzdaten
                                    target_grp = fld_parts[1].upper()    # FINANZDATEN -> FINANZDATEN
                                    # Verwende die Ziel-Gruppe für den get_value Aufruf
                                    ref_grp = target_grp
                        else:
                            ref_table, ref_grp, ref_fld = ref_key, ref_key, ref_key
                        
                        # Hole die GUID direkt über die Root-Instanz mit Stichtag
                        root_inst = self.root
                        if root_inst:
                            ref_result = root_inst.get_value(ref_grp, ref_fld, self.st_inst.PdvmDateTime)
                            if isinstance(ref_result, dict) and 'wert' in ref_result:
                                guid = ref_result['wert']
                            elif isinstance(ref_result, tuple) and len(ref_result) >= 1:
                                guid = ref_result[0]
                            else:
                                guid = ref_result
                        else:
                            # Fallback: normale get_value Methode
                            ref_value = self.get_value(ref_key)
                            if isinstance(ref_value, dict) and 'wert' in ref_value:
                                guid = ref_value['wert']
                            elif isinstance(ref_value, tuple) and len(ref_value) >= 1:
                                guid = ref_value[0]
                            else:
                                guid = ref_value
                        logger.debug(f"[VIEWTABLE-GUID] Feld {field.key}: GUID={guid} aus Referenz-Feld {ref_key}")
                    except Exception as e:
                        logger.error(f"[VIEWTABLE-GUID] Fehler beim Holen der GUID für {field.key} aus {ref_key}: {e}")
                
                # source_path aus Metadaten holen (falls vorhanden)
                if hasattr(self, 'fields') and ref_key in self.fields:
                    ref_meta = self.fields[ref_key]
                    # source_path kann in verschiedenen Attributen stehen
                    for attr in ['source_path', 'guid_source']:
                        if hasattr(ref_meta, attr):
                            source_path = getattr(ref_meta, attr, 'root')
                            break
                
                # Instanz für Subinstanz erstellen oder holen
                if hasattr(self, 'instance_manager') and self.instance_manager:
                    field.data_instance = self.instance_manager.get_instance(table, source_path)
                    field.data_guid = guid
                    
                    # Bei viewtable-Feldern: Instanz mit aktueller GUID laden, falls GUID vorhanden
                    if guid and field.data_instance:
                        try:
                            field.data_instance.read_guid(guid)  # Daten für neue GUID aus DB laden
                            logger.debug(f"[INSTANZ-ZUWEISUNG] Viewtable-Tabelle={table}, GUID={guid}, Field={field.key}, source_path={source_path}, Instanz geladen")
                        except Exception as e:
                            logger.error(f"[INSTANZ-ZUWEISUNG] Fehler beim Laden der Instanz für {field.key} mit GUID {guid}: {e}")
                    
                    logger.debug(f"[INSTANZ-ZUWEISUNG] Sub/Dropdown/Help-Tabelle={table}, GUID={guid}, Field={field.key}, source_path={source_path}, Instanz={field.data_instance}")
                    
                    if field.data_instance is None:
                        logger.error(f"[INSTANZ-ZUWEISUNG] Keine Instanz gefunden für (table={table}, source_path={source_path})! Verfügbare InstanceManager-Keys: {list(self.instance_manager.instances.keys())}")
                else:
                    field.data_instance = None
                    field.data_guid = None
                    logger.debug(f"[INSTANZ-KEINE ZUWEISUNG] Tabelle={table}, Field={field.key} (kein InstanceManager)")


    # Entfernt: _init_all_instances, da nicht mehr benötigt

    # _get_instance entfernt, da Instanzen direkt im FieldMeta liegen und kein instance_dict mehr existiert

    def get_dropdown_options(self, meta):
        """Liefert die Dropdown-Optionen für ein FeldMeta-Objekt stichtagsgenau über die zentrale Instanz."""
        d = getattr(meta, 'dropdown_def', None)
        if not d:
            return []
        section = getattr(meta, 'dropdown_section', None) or d.get("value") or next(iter(d.values()), None)
        if not section:
            logger.warning(f"[Dropdown-Options] Kein Section/Feldname für Dropdown {meta.key}")
            return []
        # Für Dropdowns: dropdown_instance bevorzugen, sonst data_instance
        inst = getattr(meta, 'dropdown_instance', None) or getattr(meta, 'data_instance', None)
        if not inst:
            logger.warning(f"[Dropdown-Options] Keine Instanz für {meta.key}")
            return []
        # Debug: Logge die verfügbaren Felder in der Instanz
        root_keys = list(getattr(inst, 'data', {}).get('ROOT', {}).keys())
        logger.debug(f"[Dropdown-Options] Instanz für {meta.key} - ROOT-Keys: {root_keys}, section: {section}")
        data = inst.get_static_value('ROOT', section)
        logger.debug(f"[Dropdown-Options] Instanz für {meta.key} - Daten für Feld '{section}': {data}")
        opts = []
        if isinstance(data, dict):
            opts = data.get("werte", []) or []
        elif isinstance(data, list):
            opts = data
        # Historische Filterung
        if getattr(meta, 'historical', False):
            opts = [o for o in opts if float(o.get("abdatum", 0)) <= self.st_inst.PdvmDateTime]
        logger.debug(f"[Dropdown-Options] Instanz für {meta.key} - Optionen: {opts}")
        return sorted(opts, key=lambda o: float(o.get("abdatum", 0)))

    def get_help_text(self, meta, lang=None):
        """Liefert den Hilfetext für ein FeldMeta-Objekt über die zentrale Instanz."""
        h = getattr(meta, 'help_def', None)
        if not h:
            return ""
        help_instance = getattr(meta, 'help_instance', None)
        help_value = h.get("value", None)
        logger.debug(f"[Help-Text] Suche Hilfe für Instanz {help_instance} mit Wert {help_value} und Sprache {lang}")
        if not (help_instance and help_value):
            return ""
        val = help_instance.get_static_value('ROOT', help_value)
        logger.debug(f"[Help-Text] Hilfe-Daten: {val} - zu welcher ID {getattr(help_instance, 'guid', None)} geladen")
        if not val:
            return ""
        if lang and isinstance(val, dict) and lang in val:
            return val[lang]
        return val.get("text", "")

    def get_help_header(self, meta, lang=None):
        h = getattr(meta, 'help_def', None)
        if not h:
            return ""
        help_instance = getattr(meta, 'help_instance', None)
        help_value = h.get("value", None)
        if not (help_instance and help_value):
            return ""
        val = help_instance.get_static_value('ROOT', help_value)
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
        Für viewtable-Felder wird die spezielle Key-Normalisierung verwendet.
        Für viewtable-Felder: Die GUID wird immer aus der zugewiesenen Instanz gelesen und Daten werden nur bei GUID-Wechsel neu geladen.
        """
        meta = self.fields.get(key) if hasattr(self, 'fields') else None
        if not meta:
            return None, None
        inst = getattr(meta, 'data_instance', None)
        table, grp, fld = self._normalize_key(key)
        # Dynamische GUID-Beschaffung für Subinstanz-Felder (z.B. finanzdaten) entfällt, da keine stichtagsgenaue Anzeige/Reload mehr nötig ist.

        # --- ENDE aller Altlogik zu ref_key/guid ---
        if not inst:
            return None, None
        logger.debug(f"ÖÖÖÖÖÖÖ [PdvmInputManager.get_value] Normalisiere Key: {key} -> (table={table}, grp={grp}, fld={fld})")
        res = inst.get_value(grp, fld.upper(), self.st_inst.PdvmDateTime)
        logger.debug(f"[PdvmInputManager.get_value] Rückgabewert von inst.get_value({grp}, {fld.upper()}): {res} (Typ: {type(res)})")

        # --- Historische Felder: Dict mit Zeitstempeln als Keys ---
        if isinstance(res, dict) and all(self._is_float_key(k) for k in res.keys()):
            stichtag = self.st_inst.PdvmDateTime
            ts_keys = [float(k) for k in res.keys() if float(k) <= stichtag]
            if ts_keys:
                max_ts = max(ts_keys)
                wert = res[format(max_ts, ".5f")]
                ab_zeit = max_ts
                logger.debug(f"[PdvmInputManager.get_value] Historischer Wert gefunden: {wert} @ {ab_zeit}")
                return wert, ab_zeit
            else:
                return "", 1001.0

        # Standardfall: Dict mit 'wert' und 'ab_zeit'
        wert = res.get("wert", "")
        ab_zeit = float(res.get("ab_zeit", 1001.0))

        # Template-Logik: Wenn Instanz ist Template und Feld fehlt, lege es leer an und speichere
        if inst.guid == TEMPLATE_GUID and not res:
            # Leeres Feld anlegen (ohne ref_key-Logik)
            if table != "benutzerdaten":
                inst.set_value(grp, fld.upper(), "", self.st_inst.PdvmDateTime)
            else:
                inst.set_value(grp, fld.upper(), "")
            inst.speichern(TEMPLATE_GUID, inst.data)
            wert = ""
            ab_zeit = self.st_inst.PdvmDateTime if table != "benutzerdaten" else 1001.0
        return wert, ab_zeit

    def _is_float_key(self, k):
        try:
            float(k)
            return True
        except Exception:
            return False

    def get_value_all(self, key: str, use_viewtable_normalization: bool = False) -> dict:
        # Viewtable-Felder werden wie Text behandelt, keine Spezialbehandlung
        table, grp, fld = self._normalize_key(key)
        # Hole FieldMeta aus self.fields
        meta = self.fields.get(key)
        if not meta or not getattr(meta, 'data_instance', None):
            logger.error(f"[get_value_all] Keine Dateninstanz für Feld {key} (table={table}, grp={grp})")
            return {}
        inst = meta.data_instance
        return inst.get_value_all(grp, fld.upper()) or {}

    def set_value(self, key: str, value: Any, abdatum: float):
        """
        Setzt immer (wert, abdatum) – für alle Typen. Für nicht-historische Felder wird abdatum ignoriert.
        Instanz wird immer über den InstanceManager geholt.
        """
        table, grp, fld = self._normalize_key(key)
        # GUID bestimmen: Für Root-Tabelle root_guid, sonst ggf. aus FieldMeta
        guid = self.root_guid
        meta = self.fields.get(key)
        if meta and hasattr(meta, 'data_guid') and meta.data_guid:
            guid = meta.data_guid
        source_path = None
        meta = self.fields.get(key)
        if meta and hasattr(meta, 'guid_source') and meta.guid_source:
            source_path = meta.guid_source
        elif meta and hasattr(meta, 'meta') and isinstance(meta.meta, dict):
            source_path = meta.meta.get('guid_source')
        if table == (self.root_table or '').lower():
            source_path = 'root'
        
        print(f"[DEBUG] PdvmInputManager.set_value: key={key}, table={table}, guid={guid}, source_path={source_path}")
        
        # Für ViewTable-Felder: Verwende die data_instance direkt aus dem FieldMeta
        inst = None
        if meta and hasattr(meta, 'data_instance') and meta.data_instance:
            inst = meta.data_instance
            print(f"[DEBUG] PdvmInputManager.set_value: Verwende data_instance aus FieldMeta, inst_guid={getattr(inst, 'guid', 'N/A')}")
        else:
            inst = self.instance_manager.get_instance(table, source_path)
            print(f"[DEBUG] PdvmInputManager.set_value: Verwende InstanceManager, inst_guid={getattr(inst, 'guid', 'N/A')}")
        
        print(f"[DEBUG] PdvmInputManager.set_value: key={key}, value={value}, abdatum={abdatum}, inst_id={id(inst) if inst else None}")
        # Für alle Typen: immer Wert + Ab-Datum übergeben
        if inst:
            print(f"[DEBUG] PdvmInputManager.set_value: Vorher inst.data[{grp}][{fld.upper()}]={inst.data.get(grp, {}).get(fld.upper(), 'N/A')}")
            inst.set_value(grp, fld.upper(), value, abdatum)
            print(f"[DEBUG] PdvmInputManager.set_value: Nachher inst.data[{grp}][{fld.upper()}]={inst.data.get(grp, {}).get(fld.upper(), 'N/A')}")

        # SPEZIAL: Wenn das Feld eine GUID ist (z.B. viewtable/Relation), stelle sicher, dass die Zielinstanz existiert
        # Heuristik: Wenn der Feldname wie eine GUID aussieht und das Feld im Root ist
        import re
        guid_regex = re.compile(r"[0-9a-fA-F\-]{36}")
        if isinstance(value, str) and guid_regex.fullmatch(value):
            # Prüfe, ob für (table, grp, value) eine Instanz existiert, sonst anlegen
            self.ensure_instance_for_guid(table, grp, value)

    def delete_value(self, key: str, abdatum: float) -> bool:
        table, grp, fld = self._normalize_key(key)
        # GUID bestimmen: Für Root-Tabelle root_guid, sonst ggf. aus FieldMeta
        guid = self.root_guid
        meta = self.fields.get(key)
        if meta and hasattr(meta, 'data_guid') and meta.data_guid:
            guid = meta.data_guid
        source_path = None
        meta = self.fields.get(key)
        if meta and hasattr(meta, 'guid_source') and meta.guid_source:
            source_path = meta.guid_source
        elif meta and hasattr(meta, 'meta') and isinstance(meta.meta, dict):
            source_path = meta.meta.get('guid_source')
        if table == (self.root_table or '').lower():
            source_path = 'root'
        inst = self.instance_manager.get_instance(table, source_path)
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
            # Kein direktes Speichern! Nur Struktur anpassen, persistiert wird erst mit save_all
            logger.info(f"🔹 Historischen Eintrag aus Struktur entfernt (noch nicht gespeichert!): {key} @ {ts_key}")
            return True
        return False
    
    def delete_history_entry(self, field_key: str, timestamp: float) -> bool:
        """
        Löscht einen spezifischen History-Eintrag basierend auf dem Zeitstempel.
        Speziell für History-Dialog Lösch-Funktionalität.
        
        WICHTIG: Löscht nur aus der Instanz-Struktur, NICHT aus der Datenbank!
        Das save_all() soll nur über den Speicher-Button im InputFrame verwendet werden.
        
        Args:
            field_key: Der Feldschlüssel (z.B. "persondaten_persdaten_vorname")
            timestamp: Der Zeitstempel des zu löschenden Eintrags
        
        Returns:
            bool: True wenn erfolgreich gelöscht, False bei Fehler
        """
        try:
            # Prüfe ob genügend Einträge vorhanden sind (mindestens 2)
            history = self.get_history(field_key)
            if len(history) <= 1:
                print(f"[WARNING] delete_history_entry: Kann letzten Eintrag nicht löschen für {field_key}")
                return False
            
            # Verwende die bestehende delete_value Methode - die löscht nur aus der Instanz
            print(f"[DEBUG] delete_history_entry: Versuche Löschung für {field_key} @ {timestamp}")
            success = self.delete_value(field_key, timestamp)
            print(f"[DEBUG] delete_history_entry: delete_value Ergebnis: {success}")
            
            if success:
                print(f"[INFO] delete_history_entry: History-Eintrag aus Instanz gelöscht für {field_key} @ {timestamp}")
                print(f"[INFO] delete_history_entry: KEIN save_all() - Löschung nur im Speicher!")
                return True
            else:
                print(f"[ERROR] delete_history_entry: Löschung fehlgeschlagen für {field_key} @ {timestamp}")
                return False
                
        except Exception as e:
            print(f"[ERROR] delete_history_entry für {field_key}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def save_all(self):
        """
        Speichert nur relevante Instanzen (z.B. persondaten, finanzdaten) im Mapping genau einmal (inkl. Root und verknüpfte Instanzen).
        Dropdown-, Help- und System-Instanzen (dropdowndaten, beschreibungen, roottable) werden NICHT gespeichert.
        Doppelte Saves pro (table, guid) werden verhindert.
        """
        ausnahmen = ("dropdowndaten", "beschreibungen", "roottable")
        saved = set()
        for key, meta in self.instance_dict.items():
            table = None
            guid = None
            # key kann (table, grp) oder (table, guid) sein
            if isinstance(key, tuple):
                table = key[0]
            if 'guid' in meta:
                guid = meta['guid']
            if table in ausnahmen:
                logger.debug(f"⏩ Überspringe Instanz {key} (Tabelle {table})")
                continue
            if (table, guid) in saved:
                logger.debug(f"⏩ Instanz {key} (Tabelle {table}, GUID {guid}) wurde bereits gespeichert")
                continue
            inst = meta['instance']
            logger.debug(f"🔹 Speichere Instanz {key} mit GUID {getattr(inst, 'guid', None)}")
            inst.save_values()
            saved.add((table, guid))
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
 
            raw = sys_db.lesen() or {}
            user_data = raw.get(user_guid, {}) if isinstance(raw.get(user_guid), dict) else {}
            frame_data = raw.get(frame_guid, {}) if isinstance(raw.get(frame_guid), dict) else {}
            frame_data["last_root_guid"] = root_guid
            sys_db.speichern(user_guid,{user_guid: user_data, frame_guid: frame_data})
 
    def reload_instance_guid(self, table: str, group: str, guid: str, path: str = None):
        """
        Lädt für die Instanz (table, group, [path]) die Daten der neuen GUID in die bestehende Instanz.
        Instanz wird über den InstanceManager geholt.
        """
        inst = self.instance_manager.get_instance(table, path)
        if inst:
            inst.read_guid(guid)

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

    def get_control_object(self, meta, value=None, abdatum=None):
        """
        Erzeugt ein ControlObject für das gegebene Feld-Meta.
        value und abdatum können übergeben werden, ansonsten wird value=None, abdatum=None verwendet.
        """
        key = getattr(meta, 'key', None)
        def _get_meta_flag(meta, flag, default=False):
            if hasattr(meta, flag):
                return getattr(meta, flag, default)
            if isinstance(meta, dict):
                return meta.get(flag, default)
            return default
        # Bestimme Flags für historical und abdatum
        abdatum_flag = bool(_get_meta_flag(meta, 'abdatum'))
        history = bool(_get_meta_flag(meta, 'historical'))
        
        # show_abdatum und show_history nur wenn SOWOHL historical als auch abdatum gesetzt sind
        show_abdatum = history and abdatum_flag
        show_history = history and abdatum_flag
        
        abdatum_inst = self.get_abdatum_instance(key)
        if abdatum_inst is None:
            from pd_datetime import Pdvm_DateTime
            abdatum_inst = Pdvm_DateTime("DEU")
            abdatum_inst.PdvmDateTime = abdatum if abdatum is not None else 1001.0
            self.register_abdatum_instance(key, abdatum_inst)
        # Wert-Instanz für Datetime-Felder sicherstellen!
        value_inst = self.get_value_instance(key) if getattr(meta, 'type', None) == "datetime" else None
        if getattr(meta, 'type', None) == "datetime" and value_inst is None:
            from pd_datetime import Pdvm_DateTime
            value_inst = Pdvm_DateTime("DEU")
            value_inst.PdvmDateTime = value if value is not None else 1001.0
            self.register_value_instance(key, value_inst)
        label_width = getattr(meta, 'ui_width_label', None) or self.width_label
        value_width = getattr(meta, 'ui_width_value', None) or self.width_control
        button_width = getattr(meta, 'ui_width_button', None) or self.width_button
        indent_ab = getattr(meta, 'ui_indent_ab', None) or self.width_indent_ab
        frame_width = getattr(self, 'width_frame', 600) or 600
        help_text = self.get_help_text(meta, lang=self.language)
        help_header = self.get_help_header(meta, lang=self.language)
        display_value = self.get_display_value(meta, value)
        logger.debug(f"🔹 [PdvmInputManager] ControlObject für {key}: historical={history}, abdatum={abdatum_flag}, display_value={display_value}, show_abdatum={show_abdatum}, show_history={show_history}")

        return ControlObject(
            meta=meta,
            display_value=display_value,
            abdatum_inst=abdatum_inst,
            value_inst=value_inst,
            label_width=label_width,
            value_width=value_width,
            button_width=button_width,
            indent_ab=indent_ab,
            frame_width=frame_width,
            help_text=help_text,
            help_header=help_header,
            show_abdatum=show_abdatum,
            show_history=show_history,
            manager=self,
            key=key,
            data_instance=getattr(meta, 'data_instance', None)
        )
    
    def refresh_all_control_objects(self):
        """
        Refresht alle registrierten ControlObjects nach einer Stichtag-Änderung.
        Diese Methode sollte vom InputWidget aufgerufen werden, wenn sich der Stichtag ändert.
        """
        # Zuerst alle Abdatum-Instanzen aktualisieren
        self.update_abdatum_for_fields()
        
        # Dann eine Liste aller bekannten ControlObjects refreshen
        # (Diese müssen vom InputWidget registriert werden)
        if hasattr(self, '_control_objects'):
            for control_obj in self._control_objects:
                try:
                    control_obj.refresh()
                except Exception as e:
                    logger.error(f"[refresh_all_control_objects] Fehler beim Refreshen des ControlObjects: {e}")

    def unified_refresh(self, skip_stichtag_save=True, rebuild_ui_callback=None, force_complete_rebuild=False):
        """
        Einheitliche Refresh-Methode für alle Szenarien (Edit, History, ViewTable-Updates).
        Führt denselben Refresh durch wie der Button, aber ohne Stichtag zu speichern.
        
        Args:
            skip_stichtag_save: Wenn True, wird der Stichtag nicht gespeichert (für Edit/History)
                               Wenn False, wird wie beim Button-Refresh auch der Stichtag gespeichert
            rebuild_ui_callback: Optional - Callback-Funktion zum UI-Neuaufbau nach dem Refresh
            force_complete_rebuild: Wenn True, wird wie bei einem Neuaufruf komplett neu aufgebaut
        """
        logger.debug(f"[unified_refresh] Starte einheitlichen Refresh (skip_stichtag_save={skip_stichtag_save}, force_complete_rebuild={force_complete_rebuild})")
        
        if force_complete_rebuild:
            # Vollständige Neuinitialisierung wie bei einem Neuaufruf
            logger.debug("[unified_refresh] Führe vollständige Neuinitialisierung durch")
            
            # 1. WICHTIG: ViewTable-Instanzen zuerst zwingen neu zu laden
            self._refresh_viewtable_instances()
            
            # 2. Alle Instanzen neu laden (wie bei _on_new_guid)
            if hasattr(self, 'refresh_instances'):
                self.refresh_instances()
            
            # 3. UI komplett neu aufbauen über Callback
            if rebuild_ui_callback and callable(rebuild_ui_callback):
                try:
                    rebuild_ui_callback()
                    logger.debug("[unified_refresh] UI komplett neu aufgebaut")
                except Exception as e:
                    logger.error(f"[unified_refresh] Fehler beim kompletten UI-Neuaufbau: {e}")
        else:
            # Standard-Refresh wie vorher
            # 1. ViewTable-Instanzen aktualisieren bei GUID-Änderungen
            self._refresh_viewtable_instances()
            
            # 2. Stichtagsgenaue Instanzen neu laden (falls vorhanden)
            if hasattr(self, 'refresh_instances_for_stichtag'):
                self.refresh_instances_for_stichtag()
            
            # 3. Alle ControlObjects refreshen (inkl. Abdatum-Anzeige)
            self.refresh_all_control_objects()
            
            # 4. UI neu aufbauen falls Callback vorhanden
            if rebuild_ui_callback and callable(rebuild_ui_callback):
                try:
                    rebuild_ui_callback()
                    logger.debug("[unified_refresh] UI-Neuaufbau über Callback durchgeführt")
                except Exception as e:
                    logger.error(f"[unified_refresh] Fehler beim UI-Neuaufbau: {e}")
        
        logger.debug("[unified_refresh] Einheitlicher Refresh abgeschlossen")

    def _refresh_viewtable_instances(self):
        """
        Erkennt ViewTable-Referenz-Felder und lädt deren Instanzen bei geänderten GUIDs neu.
        Diese Methode prüft auf ungespeicherte Änderungen und bietet Speicherung an.
        """
        logger.debug("[_refresh_viewtable_instances] Starte ViewTable-Instanz-Refresh")
        
        # Finde alle ViewTable-Referenzfelder (Felder mit '-' im Namen in der Root-Tabelle)
        viewtable_refs = {}
        for key, field in self.fields.items():
            parts = key.split('_')
            if len(parts) >= 3:
                table, grp, fld = parts[0], parts[1], '_'.join(parts[2:])
                if table.lower() == self.root_table.lower() and '-' in fld:
                    # Das ist ein ViewTable-Referenzfeld
                    target_table = fld.split('-')[0].lower()
                    # Hole die aktuelle GUID für dieses Referenzfeld
                    current_guid, _ = self.get_value(key)
                    if current_guid:
                        viewtable_refs[target_table] = current_guid
                        logger.debug(f"[_refresh_viewtable_instances] ViewTable-Referenz: {key} -> {target_table} = {current_guid}")
        
        # Für jede ViewTable: Prüfe auf GUID-Änderungen und handle ungespeicherte Änderungen
        for target_table, new_guid in viewtable_refs.items():
            viewtable_fields = []
            for field_key, field_obj in self.fields.items():
                field_parts = field_key.split('_')
                if len(field_parts) >= 3 and field_parts[0].lower() == target_table:
                    viewtable_fields.append((field_key, field_obj))
            
            if viewtable_fields:
                logger.debug(f"[_refresh_viewtable_instances] ViewTable {target_table}: {len(viewtable_fields)} Felder gefunden")
                
                # Prüfe ob sich die GUID geändert hat
                first_field = viewtable_fields[0][1]  # Nimm das erste Feld als Referenz
                current_instance_guid = getattr(first_field.data_instance, 'guid', None) if first_field.data_instance else None
                
                if current_instance_guid != new_guid:
                    logger.debug(f"[_refresh_viewtable_instances] GUID-Änderung erkannt für {target_table}: {current_instance_guid} -> {new_guid}")
                    
                    # Prüfe auf ungespeicherte Änderungen in der aktuellen Instanz
                    has_unsaved_changes = False
                    if first_field.data_instance and hasattr(first_field.data_instance, 'is_dirty'):
                        has_unsaved_changes = first_field.data_instance.is_dirty()
                        logger.debug(f"[_refresh_viewtable_instances] Dirty-Check für {target_table}: {has_unsaved_changes}")
                    
                    # Wenn ungespeicherte Änderungen vorhanden sind, Benutzer fragen
                    if has_unsaved_changes:
                        logger.debug(f"[_refresh_viewtable_instances] Ungespeicherte Änderungen in {target_table} erkannt")
                        
                        # Dialog anzeigen - Speichern anbieten
                        save_decision = self._ask_user_save_before_reload(target_table, current_instance_guid, new_guid)
                        
                        if save_decision == "save":
                            # Speichern vor dem Neuladen
                            logger.debug(f"[_refresh_viewtable_instances] Speichere {target_table} vor Neuladen")
                            if hasattr(first_field.data_instance, 'save'):
                                first_field.data_instance.save()
                        elif save_decision == "cancel":
                            # Refresh abbrechen - keine Änderungen vornehmen
                            logger.debug(f"[_refresh_viewtable_instances] Refresh für {target_table} abgebrochen")
                            continue
                        # save_decision == "discard" -> Weiter ohne Speichern
                    
                    # Jetzt sicher neu laden (mit oder ohne vorheriges Speichern)
                    self._reload_viewtable_instance(target_table, new_guid, viewtable_fields)
                else:
                    logger.debug(f"[_refresh_viewtable_instances] Keine GUID-Änderung für {target_table}: {current_instance_guid}")
        
        logger.debug("[_refresh_viewtable_instances] ViewTable-Instanz-Refresh abgeschlossen")

    def _ask_user_save_before_reload(self, table_name, old_guid, new_guid):
        """
        Fragt den Benutzer, ob ungespeicherte Änderungen vor dem Neuladen gespeichert werden sollen.
        
        Returns:
            "save" - Speichern und dann neu laden
            "discard" - Verwerfen und neu laden  
            "cancel" - Refresh abbrechen
        """
        from PyQt5.QtWidgets import QMessageBox
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle("Ungespeicherte Änderungen")
        msg.setText(f"Die ViewTable '{table_name}' hat ungespeicherte Änderungen.")
        msg.setInformativeText(
            f"Die GUID hat sich geändert:\n"
            f"Alt: {old_guid}\n" 
            f"Neu: {new_guid}\n\n"
            f"Möchten Sie die Änderungen speichern bevor neue Daten geladen werden?"
        )
        
        save_btn = msg.addButton("Speichern", QMessageBox.AcceptRole)
        discard_btn = msg.addButton("Verwerfen", QMessageBox.DestructiveRole)  
        cancel_btn = msg.addButton("Abbrechen", QMessageBox.RejectRole)
        
        msg.setDefaultButton(save_btn)
        msg.exec_()
        
        if msg.clickedButton() == save_btn:
            return "save"
        elif msg.clickedButton() == discard_btn:
            return "discard"
        else:
            return "cancel"
    
    def _reload_viewtable_instance(self, target_table, new_guid, viewtable_fields):
        """
        Lädt eine ViewTable-Instanz sicher neu.
        """
        logger.debug(f"[_reload_viewtable_instance] Lade ViewTable {target_table} mit GUID {new_guid} neu")
        
        # Lade neue Daten für alle Felder dieser ViewTable
        for field_key, field_obj in viewtable_fields:
            if field_obj.data_instance:
                try:
                    old_guid = getattr(field_obj.data_instance, 'guid', 'unbekannt')
                    logger.debug(f"[_reload_viewtable_instance] Feld {field_key}: Reload GUID {new_guid} (vorher: {old_guid})")
                    
                    # WICHTIG: Setze die GUID auf None, damit read_guid() immer neu lädt
                    field_obj.data_instance.guid = None
                    field_obj.data_instance.read_guid(new_guid)
                    
                    # Dirty-Flag zurücksetzen nach erfolgreichem Laden
                    if hasattr(field_obj.data_instance, '_dirty'):
                        field_obj.data_instance._dirty = False
                    
                    new_loaded_guid = getattr(field_obj.data_instance, 'guid', 'unbekannt')
                    logger.debug(f"[_reload_viewtable_instance] Feld {field_key}: Reload erfolgreich, neue GUID: {new_loaded_guid}")
                except Exception as e:
                    logger.error(f"[_reload_viewtable_instance] Fehler beim Reload für {field_key}: {e}")
        
        # WICHTIG: Refresh alle ControlObjects für diese ViewTable-Felder
        if hasattr(self, '_control_objects'):
            refreshed_controls = 0
            logger.debug(f"[_reload_viewtable_instance] Prüfe {len(self._control_objects)} ControlObjects für ViewTable {target_table}")
            
            # WICHTIG: Auch das ViewTable-Referenzfeld refreshen (das liegt in der Root-Tabelle)
            ref_field_key = None
            for field_key, field_obj in self.fields.items():
                field_parts = field_key.split('_')
                if len(field_parts) >= 3:
                    table, grp, fld = field_parts[0], field_parts[1], '_'.join(field_parts[2:])
                    if '-' in fld and fld.split('-')[0].lower() == target_table:
                        ref_field_key = field_key
                        logger.debug(f"[_reload_viewtable_instance] ViewTable-Referenzfeld gefunden: {ref_field_key}")
                        break
            
            for control_obj in self._control_objects:
                try:
                    control_key = getattr(control_obj, 'key', 'unbekannt')
                    
                    # Prüfe ViewTable-Felder UND das Referenzfeld
                    is_viewtable_field = any(control_obj.key == fkey for fkey, _ in viewtable_fields) if hasattr(control_obj, 'key') else False
                    is_ref_field = (hasattr(control_obj, 'key') and control_obj.key == ref_field_key) if ref_field_key else False
                    
                    logger.debug(f"[_reload_viewtable_instance] ControlObject {control_key}: ist ViewTable-Feld = {is_viewtable_field}, ist Referenzfeld = {is_ref_field}")
                    
                    # Refresh sowohl ViewTable-Felder als auch das Referenzfeld
                    if hasattr(control_obj, 'key') and (is_viewtable_field or is_ref_field):
                        old_display_value = getattr(control_obj, 'display_value', 'unbekannt')
                        logger.debug(f"[_reload_viewtable_instance] Refreshe ControlObject für {control_obj.key} (alter display_value: '{old_display_value}')")
                        control_obj.refresh()
                        new_display_value = getattr(control_obj, 'display_value', 'unbekannt')
                        refreshed_controls += 1
                        logger.debug(f"[_reload_viewtable_instance] ControlObject für {control_obj.key} erfolgreich refreshed (neuer display_value: '{new_display_value}')")
                except Exception as e:
                    logger.error(f"[_reload_viewtable_instance] Fehler beim Refreshen des ControlObjects {getattr(control_obj, 'key', 'unbekannt')}: {e}")
            logger.debug(f"[_reload_viewtable_instance] {refreshed_controls} ControlObjects für ViewTable {target_table} refreshed")
        
        # WICHTIG: Refresh alle Input Widgets für diese ViewTable-Felder
        if hasattr(self, '_input_widgets'):
            refreshed_widgets = 0
            for input_widget in self._input_widgets:
                try:
                    logger.debug(f"[_reload_viewtable_instance] Refreshe Input Widget für ViewTable {target_table}")
                    # Input Widget komplett neu aufbauen (wie nach Stichtag-Änderung)
                    if hasattr(input_widget, 'build_fields_and_values'):
                        input_widget.build_fields_and_values()
                        refreshed_widgets += 1
                        logger.debug(f"[_reload_viewtable_instance] Input Widget erfolgreich refreshed")
                except Exception as e:
                    logger.error(f"[_reload_viewtable_instance] Fehler beim Refreshen des Input Widgets: {e}")
            logger.debug(f"[_reload_viewtable_instance] {refreshed_widgets} Input Widgets für ViewTable {target_table} refreshed")

    def register_control_object(self, control_obj):
        """
        Registriert ein ControlObject, damit es bei Stichtag-Änderungen refresht werden kann.
        """
        if not hasattr(self, '_control_objects'):
            self._control_objects = []
        if control_obj not in self._control_objects:
            self._control_objects.append(control_obj)

    def unregister_control_object(self, control_obj):
        """
        Entfernt ein ControlObject aus der Registrierung.
        """
        if hasattr(self, '_control_objects') and control_obj in self._control_objects:
            self._control_objects.remove(control_obj)

    def get_display_value(self, meta, value):
        """
        Gibt den anzeigbaren Wert für ein Feld zurück, abhängig vom Typ.
        Für Dropdown: Übersetzung, für Text: Wert, für Datetime: formatiert, für Viewtable: Wert oder GUID.
        """
        logger.debug(f"[PdvmInputManager] get_display_value für {meta.key} mit Wert {value} (Typ: {type(value)})")
        if meta.type == "dropdown":
            return self.translate_dropdown_value(meta, value, lang=self.language)
        elif meta.type == "datetime":
            # Annahme: value ist ein Zeitwert (float oder str)
            try:
                if hasattr(value, 'strftime'):
                    return value.strftime("%d.%m.%Y %H:%M")
                return str(value)
            except Exception:
                return str(value)
        # Für alle anderen Typen, inkl. viewtable: Standardanzeige
        return str(value) if value is not None else ""

    def get_data_instance(self, feld_key: str, guid: str = None, path: str = None):
        """
        Liefert die Dateninstanz für ein Feld anhand des feld_key und optionaler GUID/Path.
        Bevorzugt wird die direkt im FieldMeta gespeicherte Instanz.
        Falls nicht vorhanden, wird sie über den InstanceManager gesucht.
        """
        meta = self.fields.get(feld_key)
        if meta:
            # 1. Versuch: Direkt aus dem Meta-Feld
            inst = getattr(meta, 'data_instance', None)
            if inst:
                return inst
            # 2. Versuch: Über InstanceManager suchen (falls nötig)
            table, grp, fld = self._normalize_key(feld_key)
            if guid:
                inst = self.instance_manager.get_instance(table, guid)
                if inst:
                    return inst
            if path:
                inst = self.instance_manager.get_instance(table, path)
                if inst:
                    return inst
        return None

    def _debug_dump_instances(self):
        logger.info("[Instanz-Analyse] --- Übersicht aller Instanzen ---")
        for key, inst in self.instance_manager.instances.items():
            logger.info(f"[Instanz-Analyse] Instanz-Key={key}, GUID={inst.guid}, Tabelle={inst.table_name}, Daten={inst.data}")
        logger.info("[Instanz-Analyse] --- Ende Übersicht ---")

    def force_viewtable_refresh(self):
        """
        DEPRECATED: Verwendet jetzt die einheitliche Refresh-Methode.
        Diese Methode bleibt aus Kompatibilitätsgründen erhalten.
        """
        logger.debug("[force_viewtable_refresh] DEPRECATED - verwende unified_refresh()")
        self.unified_refresh(skip_stichtag_save=True)

    def get_history(self, field_key):
        """
        Holt die History für ein Feld über die Instanz.
        Verwendet get_value_all() um alle historischen Zeitstempel und Werte zu bekommen.
        """
        try:
            meta = self.fields.get(field_key)
            if not meta:
                print(f"[ERROR] get_history: Feld {field_key} nicht in fields gefunden")
                return []
                
            # Prüfe ob data_instance vorhanden ist
            if not hasattr(meta, 'data_instance') or not meta.data_instance:
                print(f"[ERROR] get_history: Keine data_instance für Feld {field_key}")
                return []
                
            # Feldname aus field_key extrahieren (format: table_gruppe_feldname)
            parts = field_key.split('_')
            if len(parts) >= 3:
                table = parts[0]
                grp = parts[1].upper()
                fld = '_'.join(parts[2:]).upper()
            else:
                print(f"[ERROR] get_history: Ungültiges field_key Format {field_key}")
                return []
            
            # History von der Instanz holen mit get_value_all
            # Das gibt ein Dict zurück: {timestamp_float: wert, ...}
            history_dict = meta.data_instance.get_value_all(grp, fld)
            
            if not history_dict:
                print(f"[DEBUG] get_history für {field_key}: Keine historischen Daten gefunden")
                return []
            
            # Konvertiere zu Liste von Dictionaries mit korrekten Zeitstempeln
            history_data = []
            for timestamp_float, value in history_dict.items():
                # Erstelle PdvmDateTime Instanz für jeden historischen Zeitstempel
                from pd_datetime import Pdvm_DateTime
                dt_inst = Pdvm_DateTime("DEU")
                dt_inst.PdvmDateTime = float(timestamp_float)
                
                history_entry = {
                    'timestamp': timestamp_float,
                    'value': value,
                    'ab_zeit': timestamp_float,
                    'datetime_instance': dt_inst,
                    'formatted_date': dt_inst.FormTimeStamp  # Formatiertes Datum für Anzeige (Property, nicht Methode)
                }
                history_data.append(history_entry)
            
            # Sortiere nach Zeitstempel (älteste zuerst)
            history_data.sort(key=lambda x: x['timestamp'])
            
            print(f"[DEBUG] get_history für {field_key}: {len(history_data)} Einträge gefunden")
            print(f"[DEBUG] History Zeitstempel: {[entry['timestamp'] for entry in history_data]}")
            
            return history_data
            
        except Exception as e:
            print(f"[ERROR] get_history für {field_key}: {e}")
            import traceback
            traceback.print_exc()
            return []

class ControlObject:
    """
    Ein ControlObject repräsentiert die UI-Kontrolle für ein Feld.
    Es verwaltet alle notwendigen Informationen für die Anzeige und 
    Interaktion mit dem Feld in der Benutzeroberfläche.
    """
    def __init__(self, meta, display_value, abdatum_inst, value_inst, 
                 label_width, value_width, button_width, indent_ab, frame_width, 
                 help_text, help_header, show_abdatum, show_history, manager, key, 
                 data_instance=None):
        self.meta = meta
        self.display_value = display_value
        self.abdatum_inst = abdatum_inst
        self.value_inst = value_inst
        self.label_width = label_width
        self.value_width = value_width
        self.button_width = button_width
        self.indent_ab = indent_ab
        self.frame_width = frame_width
        self.help_text = help_text
        self.help_header = help_header
        self.show_abdatum = show_abdatum
        self.show_history = show_history
        self.manager = manager
        self.key = key
        self.data_instance = data_instance
        self._refresh_callbacks = []

    def get_value(self):
        """Holt den aktuellen Wert und Abdatum für dieses Feld über den Manager."""
        if self.manager and self.key:
            return self.manager.get_value(self.key)
        return None, None

    def get_history(self):
        """Holt die Historie für dieses Feld über den Manager."""
        if self.manager and self.key:
            return self.manager.get_history(self.key)
        return []

    def set_value(self, value, abdatum):
        """
        Setzt einen neuen Wert und Abdatum für dieses Feld über den Manager.
        """
        if self.manager and self.key:
            self.manager.set_value(self.key, value, abdatum)
            self.refresh()

    def delete_history_entry(self, abdatum):
        """
        Löscht einen History-Eintrag für dieses Feld über den Manager.
        """
        if self.manager and self.key:
            result = self.manager.delete_value(self.key, abdatum)
            self.refresh()
            return result
        return False

    def refresh(self):
        """
        Aktualisiert Wert, Abdatum, display_value und ggf. verknüpfte Instanz(en) stichtagsgenau.
        Sollte nach jeder Änderung, History-Edit oder Stichtagwechsel aufgerufen werden.
        Benachrichtigt alle registrierten Callbacks (z.B. das Widget) nach Abschluss.
        """
        if not self.manager or not self.key:
            return
        
        # Wert und Abdatum neu holen
        old_display_value = self.display_value
        value, abdatum = self.manager.get_value(self.key)
        self.display_value = self.manager.get_display_value(self.meta, value)
        
        print(f"[DEBUG] ControlObject.refresh für '{self.key}': Wert: {value}, alt display_value: '{old_display_value}', neu display_value: '{self.display_value}'", flush=True)
        
        # Abdatum-Instanz ggf. aktualisieren
        if self.abdatum_inst is not None:
            self.abdatum_inst.PdvmDateTime = abdatum
        
        # Spezialfall: viewtable-Feld mit GUID-Verweis
        # Prüfe, ob es abhängige Felder gibt, die von dieser GUID-Änderung betroffen sind
        key_parts = self.key.split("_")
        if len(key_parts) >= 3:
            table = key_parts[0].lower()
            grp = key_parts[1].upper()
            fld = "_".join(key_parts[2:])
            
            # Wenn das aktuelle Feld eine viewtable-GUID ist (erkennbar am '-' im Feldnamen)
            if "-" in fld and table == self.manager.root_table.lower():
                # Das ist ein viewtable-Referenzfeld - aktualisiere alle abhängigen Felder
                target_table = fld.split("-")[0].lower()
                
                # Finde alle Felder, die von dieser Tabelle abhängen
                for dep_key, dep_field in self.manager.fields.items():
                    dep_parts = dep_key.split("_")
                    if len(dep_parts) >= 3 and dep_parts[0].lower() == target_table:
                        # Abhängiges Feld gefunden - aktualisiere seine Instanz
                        if hasattr(dep_field, 'data_instance') and dep_field.data_instance and value:
                            try:
                                # Nur aktualisieren, wenn sich die GUID geändert hat
                                if getattr(dep_field, 'data_guid', None) != value:
                                    dep_field.data_guid = value
                                    dep_field.data_instance.guid = value
                                    dep_field.data_instance.lesen()  # Daten mit neuer GUID laden
                                    logger.debug(f"[ControlObject.refresh] Abhängige Instanz für {dep_key} mit neuer GUID {value} geladen")
                            except Exception as e:
                                logger.error(f"[ControlObject.refresh] Fehler beim Aktualisieren der abhängigen Instanz für {dep_key}: {e}")
        
        # Für Datetime: Die Instanz wird ausschließlich vom Picker bearbeitet und per save() übernommen.
        meta_type = getattr(self.meta, 'type', None)
        if self.value_inst is not None and meta_type == "datetime":
            pass
        
        logger.debug(f"[ControlObject.refresh] Refreshed {self.key}: display_value={self.display_value}")
        
        # Callbacks benachrichtigen - aber nur die gültigen
        valid_callbacks = []
        for cb in self._refresh_callbacks:
            try:
                # Teste ob der Callback noch gültig ist (für Qt-Widgets)
                if hasattr(cb, '__self__'):
                    widget = cb.__self__
                    # Prüfe ob es ein Qt-Widget ist und ob es gelöscht wurde
                    if hasattr(widget, 'isVisible'):
                        try:
                            # Teste ob das Widget noch existiert
                            widget.isVisible()
                            valid_callbacks.append(cb)
                            cb()
                        except RuntimeError as re:
                            # Widget wurde gelöscht - Callback nicht mehr gültig
                            logger.debug(f"[ControlObject.refresh] Widget für Callback wurde gelöscht, überspringe: {re}")
                            continue
                    else:
                        # Kein Qt-Widget - führe Callback aus
                        valid_callbacks.append(cb)
                        cb()
                else:
                    # Funktions-Callback - führe aus
                    valid_callbacks.append(cb)
                    cb()
            except Exception as e:
                logger.error(f"[ControlObject.refresh] Fehler beim Ausführen des Refresh-Callbacks: {e}")
        
        # Aktualisiere die Callback-Liste mit nur den gültigen Callbacks
        self._refresh_callbacks = valid_callbacks

    def add_refresh_callback(self, callback):
        """Fügt einen Callback hinzu, der bei jedem refresh() aufgerufen wird."""
        if callback not in self._refresh_callbacks:
            self._refresh_callbacks.append(callback)

    def remove_refresh_callback(self, callback):
        """Entfernt einen Refresh-Callback."""
        if callback in self._refresh_callbacks:
            self._refresh_callbacks.remove(callback)
