# pdvm_instance_manager.py
# -*- coding: utf-8 -*-
"""
PdvmInstanceManager: Baut rekursiv Instanzen entlang GUID-Verbindungen auf und verwaltet deren Herkunft (guid_source).

WICHTIGER HINWEIS ZUR INSTANZVERWALTUNG UND LOOP-VERMEIDUNG:
-----------------------------------------------------------
Die Instanzverwaltung verwendet als Schlüssel (table, group) und legt für jede Kombination nur eine Instanz an.
Dadurch werden Endlosschleifen (Loops) bei rekursiven oder zyklischen Beziehungen zuverlässig verhindert:
Eine Subinstanz wird nur dann erzeugt, wenn für (table, group) noch keine Instanz existiert.
Falls ein Loop entstehen würde, wird die Subinstanz nicht erneut erzeugt und die Rekursion endet an dieser Stelle.

Einschränkung:
- Diese Logik unterstützt keine echten 1:n-Relationen (mehrere Subinstanzen pro (table, group)), sondern nur 1:1- und n:1-Beziehungen.
- Für 1:n-Relationen oder komplexere Strukturen müsste die Instanzverwaltung später erweitert werden (z.B. Key um GUID ergänzen).

Vorteil:
- Die Lösung ist einfach, robust und für typische Anwendungsfälle ausreichend.
- Loops werden zuverlässig verhindert, ohne dass eine maximale Rekursionstiefe oder weitere Prüfungen nötig sind.
"""
import logging
from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)


class PdvmInstanceManager:
    def __init__(self, root_table, root_guid, stichtag, framedaten, db_name="PdvmManager.db", root_path=None):
        """
        framedaten: dict mit allen Metadaten der Felder (wie aus Framedaten/Metadaten)
        """
        self.db_name = db_name
        self.root_table = root_table
        self.root_guid = root_guid
        self.stichtag = stichtag
        self.root_path = root_path
        self.framedaten = framedaten  # Dict mit allen Feld-Metadaten
        self.instances = {}  # (table, source_path) -> instance
        self._build_all_instances()

    def _build_all_instances(self):
        # 1. Alle benötigten Instanzen aus den Metadaten extrahieren (table, source_path)
        needed_instances = set()
        for field_key, meta in (self.framedaten or {}).items():
            sp = meta.get('source_path')
            if sp:
                # Table aus Feldnamen extrahieren (immer klein)
                table = field_key.split('_')[0].lower() if '_' in field_key else self.root_table.lower()
                needed_instances.add((table, sp))
        # 2. Für alle benötigten Instanzen erzeugen (nicht nur Root!)
        for (table, sp) in needed_instances:
            if (table, sp) not in self.instances:
                # GUID bestimmen: Für Root-Tabelle root_guid, sonst Dummy oder None
                guid = self.root_guid if table == self.root_table.lower() else None
                try:
                    inst = PdvmCentralDatenbank(db_name=self.db_name, table_name=table, guid=guid, path=self.root_path, source_path=sp)
                    inst.guid_source = "ROOT" if table == self.root_table.lower() else f"AUTO_{table}_{sp}"
                    self.instances[(table, sp)] = inst
                    logger.info(f"[InstanceManager] Instanz für ({table}, {sp}) erzeugt.")
                except Exception as e:
                    logger.error(f"[InstanceManager] Fehler beim Erzeugen der Instanz für ({table}, {sp}): {e}")
        # 3. Rekursiv alle abhängigen Instanzen aufbauen, aber nur für benötigte source_paths
        root_inst = self.instances.get((self.root_table.lower(), 'root'))
        if root_inst:
            self._build_recursive(self.root_table, self.root_guid, self.root_path, root_inst, set(sp for _, sp in needed_instances))
        # 4. Für alle Felder in den Framedaten: Dropdown- und Hilfe-Instanzen anlegen, falls definiert
        for field_key, meta in (self.framedaten or {}).items():
            # Dropdown-Instanz
            dropdown_def = meta.get("dropdown", {})
            dropdown_table = dropdown_def.get("table") or dropdown_def.get("tabelle")
            dropdown_guid = dropdown_def.get("key") or dropdown_def.get("guid") or "11111111-1111-1111-1111-111111111111"
            dropdown_source_path = dropdown_def.get("source_path") or meta.get("source_path")
            if dropdown_table and dropdown_source_path:
                key = (dropdown_table, dropdown_source_path)
                if key not in self.instances:
                    try:
                        dropdown_inst = PdvmCentralDatenbank(db_name=self.db_name, table_name=dropdown_table, guid=dropdown_guid, source_path=dropdown_source_path)
                        dropdown_inst.guid_source = f"DROPDOWN_{field_key}"
                        self.instances[key] = dropdown_inst
                        logger.info(f"[InstanceManager] Dropdown-Instanz für {field_key}: {key} erzeugt.")
                    except Exception as e:
                        logger.error(f"[InstanceManager] Fehler beim Erzeugen der Dropdown-Instanz für {field_key}: {e}")
            # Hilfe-Instanz
            help_def = meta.get("help", {})
            help_table = help_def.get("table") or help_def.get("tabelle")
            help_guid = help_def.get("key") or help_def.get("guid") or "11111111-1111-1111-1111-111111111111"
            help_source_path = help_def.get("source_path") or meta.get("source_path")
            if help_table and help_source_path:
                key = (help_table, help_source_path)
                if key not in self.instances:
                    try:
                        help_inst = PdvmCentralDatenbank(db_name=self.db_name, table_name=help_table, guid=help_guid, source_path=help_source_path)
                        help_inst.guid_source = f"HELP_{field_key}"
                        self.instances[key] = help_inst
                        logger.info(f"[InstanceManager] Hilfe-Instanz für {field_key}: {key} erzeugt.")
                    except Exception as e:
                        logger.error(f"[InstanceManager] Fehler beim Erzeugen der Hilfe-Instanz für {field_key}: {e}")

    def _build_recursive(self, table, guid, path, inst, needed_instances):
        # Suche alle Felder mit '-' im Namen in der Instanz
        for grp, fields in getattr(inst, 'data', {}).items():
            if not isinstance(fields, dict):
                continue
            for fld, val in fields.items():
                if '-' in fld:
                    # Feldname: tabelle-gruppe
                    parts = fld.split('-')
                    if len(parts) != 2:
                        continue
                    sub_table, sub_group = parts[0].lower(), parts[1].upper()
                    # GUID für die Sub-Instanz immer mit get_value (inkl. Stichtag) auslesen
                    guid_val = inst.get_value(grp, fld, self.stichtag)
                    abdatum = None
                    # Logging: Zeige alle möglichen GUIDs, falls vorhanden
                    if isinstance(val, list):
                        logger.info(f"[InstanceManager] Feld {grp}.{fld}: Wert ist Liste mit {len(val)} Einträgen:")
                        for entry in val:
                            logger.info(f"    {entry}")
                    else:
                        logger.info(f"[InstanceManager] Feld {grp}.{fld}: Wert={val}")
                    # --- Erweiterte GUID-Extraktion: tuple, dict oder direkt ---
                    sub_guid = None
                    abdatum = None
                    if isinstance(guid_val, tuple):
                        sub_guid, abdatum = guid_val
                    elif isinstance(guid_val, dict):
                        sub_guid = guid_val.get('wert')
                        abdatum = guid_val.get('ab_zeit')
                    else:
                        sub_guid = guid_val
                    logger.info(f"[InstanceManager] Feld {grp}.{fld}: get_value -> GUID={sub_guid} abdatum={abdatum} (Stichtag={self.stichtag})")
                    # Prüfe, ob guid ein str oder float ist (kein dict, list, None)
                    if not isinstance(sub_guid, (str, float)) or not sub_guid:
                        logger.info(f"[InstanceManager] Feld {grp}.{fld}: GUID ungeeignet ({sub_guid}), übersprungen.")
                        continue
                    # source_path rekursiv aufbauen: parent_source_path + _ + sub_table
                    # parent_source_path ist der aktuelle path (source_path) der Elterninstanz
                    parent_source_path = getattr(inst, 'source_path', None)
                    if not parent_source_path:
                        raise RuntimeError(f"[InstanceManager] parent_source_path fehlt für Elterninstanz {table}.{guid} beim Aufbau von {sub_table}.{sub_guid}!")
                    # source_path für Subinstanz bilden
                    sub_source_path = f"{parent_source_path}_{sub_table}" if parent_source_path != 'root' else sub_table
                    # Nur Instanzen für benötigte source_paths erzeugen
                    if sub_source_path not in needed_instances:
                        continue
                    # Metadaten-Key suchen, der diesen source_path hat
                    meta_key = None
                    for k, v in self.framedaten.items():
                        if v.get('source_path') == sub_source_path:
                            meta_key = k
                            break
                    if not meta_key:
                        raise RuntimeError(f"[InstanceManager] Kein passender Metadaten-Key mit source_path={sub_source_path} für Sub-Instanz {fld} (table={sub_table}, guid={sub_guid})! Verfügbare source_paths: {[v.get('source_path') for v in self.framedaten.values()]}")
                    meta = self.framedaten.get(meta_key) or {}
                    source_path = meta.get('source_path')
                    key = (sub_table, source_path)
                    if key not in self.instances:
                        logger.info(f"[InstanceManager] Baue Sub-Instanz: {key} mit GUID={sub_guid} (abdatum={abdatum}) aus Feld {grp}.{fld}")
                        sub_inst = PdvmCentralDatenbank(db_name=self.db_name, table_name=sub_table, guid=sub_guid, path=path, source_path=source_path)
                        sub_inst.guid_source = f"{table}_{guid}_{fld}"  # Herkunft merken
                        self.instances[key] = sub_inst
                        logger.info(f"[InstanceManager] Instanz aufgebaut: {key} via {sub_inst.guid_source} (GUID={sub_guid}, abdatum={abdatum})")
                        # Rekursiv weiter
                        self._build_recursive(sub_table, sub_guid, path, sub_inst, needed_instances)

    def get_instance(self, table, source_path):
        return self.instances.get((table, source_path))

    def refresh_all(self, stichtag=None):
        if stichtag is not None:
            self.stichtag = stichtag
        # Alle Instanzen neu aufbauen (inkl. GUIDs nach neuem Stichtag)
        self.instances = {}
        self._build_all_instances()
        logger.info(f"[InstanceManager] refresh_all: Instanzen für Stichtag {self.stichtag} neu aufgebaut.")

# --- Testszenario ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # --- Test: Framedaten/Metadaten aus Frame-GUID laden ---
    import sys
    frame_guid = "4078079f-4028-45ed-879c-3c779ecf3d0d"  # Setze hier deine Frame-GUID
    from pdvm_central_datenbank import PdvmCentralDatenbank
    frm_db = PdvmCentralDatenbank(db_name="PdvmManager.db", table_name="framedaten", guid=frame_guid)
    raw_frame = frm_db.lesen()
    if not raw_frame:
        print(f"Keine Framedaten für GUID {frame_guid} gefunden!")
        sys.exit(1)
    # Metadaten extrahieren
    metadaten = raw_frame.get("Metadaten", {})
    print(f"Metadaten-Felder: {list(metadaten.keys())}")
    # Beispiel: Root ist 'persondaten', GUID '58c0acaa-fd40-4444-b516-c162f17a39b8', Stichtag 2025150.0
    root_table = "persondaten"
    root_guid = "58c0acaa-fd40-4444-b516-c162f17a39b8"
    stichtag = 2025150.0
    mgr = PdvmInstanceManager(root_table, root_guid, stichtag, metadaten)
    print("Alle Instanzen:")
    for key, inst in mgr.instances.items():
        print(f"  {key}: GUID={inst.guid}, guid_source={getattr(inst, 'guid_source', None)}")
    # Zugriff auf eine Sub-Instanz
    sub = mgr.get_instance("finanzdaten", "FINANZDATEN")
    if sub:
        print(f"Sub-Instanz: {sub.table_name}, GUID={sub.guid}, guid_source={getattr(sub, 'guid_source', None)}")
    else:
        print("Keine Sub-Instanz gefunden.")
    # Teste Refresh mit anderem Stichtag
    mgr.refresh_all(stichtag=2025158.0)
    print(f"\nNach Refresh (Stichtag {stichtag}):")
    for key, inst in mgr.instances.items():
        print(f"  {key}: GUID={inst.guid}, guid_source={getattr(inst, 'guid_source', None)}")
