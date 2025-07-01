#pdvm_menu.py
import json
import logging

logger = logging.getLogger(__name__)

from pdvm_datenbank import PdvmDatenbank

class PdvmMenu:
    def __init__(self, menu_id, db_name="PdvmManager.db"):
        self.menu_id = menu_id
        self.db = PdvmDatenbank(db_name, "menudaten", hist=False)
        daten = self.db.lesen(menu_id)
        self.__pd_structure = self.normalize_menu_structure(daten)
        self.validate_and_normalize_structure()

    def save_to_db(self):
        self.db.speichern(self.menu_id, self.__pd_structure)

    def validate_and_normalize_structure(self):
        self.__pd_structure = self.normalize_menu_structure(self.__pd_structure)
        self.sync_pd_commands(self.__pd_structure)

    def sync_pd_commands(self, struc):
        """
        Stellt sicher, dass in PD_commands für alle Blattpfade ein Eintrag existiert.
        Keys, die nicht mehr vorkommen, werden entfernt.
        """
        all_menu_paths = self.get_all_menu_paths()
        self.commands = struc["PD_commands"]
        obsolete_keys = [key for key in self.commands if key not in [path.replace('.', '_') for path in all_menu_paths]]
        for key in obsolete_keys:
            del self.commands[key]
        for path in all_menu_paths:
            path_key = path.replace('.', '_')
            if path_key not in self.commands:
                self.commands[path_key] = None

    def get_all_menu_paths(self):
        paths = []
        self.__collect_leaf_paths(self.__pd_structure["PD_grund"], "", paths)
        self.__collect_leaf_paths(self.__pd_structure["PD_menu"], "", paths)
        self.__collect_leaf_paths(self.__pd_structure["PD_zusatz"]["PD_z_Grund"], "", paths)
        self.__collect_leaf_paths(self.__pd_structure["PD_zusatz"]["PD_z_Menu"], "", paths)
        return paths

    def __collect_leaf_paths(self, menu_dict, prefix, paths):
        for key, value in menu_dict.items():
            full_path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict) and value:
                self.__collect_leaf_paths(value, full_path, paths)
            else:
                paths.append(full_path)

    def normalize_menu_structure(self, menu_data):
        if isinstance(menu_data, list):
            return {item: None for item in menu_data}
        elif isinstance(menu_data, dict):
            return {key: self.normalize_menu_structure(value) for key, value in menu_data.items()}
        else:
            return menu_data

    def is_leaf_node(self, full_path, menu_type):
        parts = full_path.split(".")
        current_level = self.get_menu_by_type(menu_type)
        for part in parts:
            if not isinstance(current_level, dict):
                return True
            if part in current_level:
                current_level = current_level[part]
            else:
                return False
        return not isinstance(current_level, dict) or not current_level

    def update_menu_structure_from_tree(self, tree, menu_type):
        """
        Extrahiert die Baumstruktur aus dem Treeview und ersetzt den Menüabschnitt,
        der durch den vollständig qualifizierten menu_type definiert ist.
        """
        def recursive_extract(parent_id):
            tree_structure = {}
            for child_id in tree.get_children(parent_id):
                key = tree.item(child_id, "text")
                subtree = recursive_extract(child_id)
                tree_structure[key] = subtree if subtree else None
            return tree_structure

        new_structure = recursive_extract("")
        parts = menu_type.split('.')
        if len(parts) == 1:
            self.__pd_structure[parts[0]] = new_structure
        else:
            section = self.__pd_structure
            for part in parts[:-1]:
                if part not in section:
                    section[part] = {}
                section = section[part]
            section[parts[-1]] = new_structure
        self.update_structure()

    def update_structure(self):
        self.sync_pd_commands(self.__pd_structure)
        print("Struktur aktualisiert.")

    def add_menu_entry(self, parent_path, name, command, menu_type):
        menu_section = self.menu_section(menu_type)
        # Wenn parent_path nicht leer ist, navigiere anhand der Punkte
        if parent_path:
            parts = parent_path.split('.')
            current_section = menu_section
            for part in parts:
                # Wenn es noch kein Dict an diesem Teil gibt (oder es war ein Leaf),
                # wandeln wir das in ein Dict um:
                if current_section.get(part) is None:
                    current_section[part] = {}
                current_section = current_section[part]
        else:
            current_section = menu_section

        # Und hier setzen wir dann den neuen Eintrag
        current_section[name] = None
        full_path = f"{parent_path}.{name}" if parent_path else name
        self.set_command(full_path, command)

    def delete_entry(self, full_path, menu_type):
        parts = full_path.split(".")
        current_level = self.menu_section(menu_type)
        for part in parts[:-1]:
            if part in current_level and isinstance(current_level[part], dict):
                current_level = current_level[part]
            else:
                logger.error(f"Der Menüpunkt '{full_path}' existiert nicht!")
                return
        last_part = parts[-1]
        if last_part in current_level:
            del current_level[last_part]
            logger.info(f"✅ Menüpunkt '{full_path}' wurde erfolgreich gelöscht.")
        else:
            logger.error(f"⚠️ Der Menüpunkt '{full_path}' existiert nicht!")
        self.update_structure()

    def rename_menu_entry(self, old_full_path, new_full_path, menu_type):
        logger.info(f"🔄 Umbenennen: '{old_full_path}' → '{new_full_path}'")
        parts = old_full_path.split('.')
        current_section = self.menu_section(menu_type)
        new_parts = new_full_path.split('.')
        for part in parts[:-1]:
            if part in current_section:
                current_section = current_section[part]
            else:
                return
        old_leaf = parts[-1]
        new_leaf = new_parts[-1]
        if old_leaf not in current_section:
            return
        current_section[new_leaf] = current_section.pop(old_leaf)
        old_key_cmd = old_full_path.replace('.', '_')
        new_key_cmd = new_full_path.replace('.', '_')
        if old_key_cmd in self.__pd_structure["PD_commands"]:
            self.__pd_structure["PD_commands"][new_key_cmd] = self.__pd_structure["PD_commands"].pop(old_key_cmd)

    def move_entry(self, old_full_path, new_full_path, menu_type):
        """
        Verschiebt einen Menüeintrag in der internen Struktur.
        Falls der Ziel-Elternknoten (new_parent_path) nicht existiert oder None ist,
        wird er automatisch angelegt.
        Liefert True zurück, wenn der Eintrag erfolgreich verschoben wurde, sonst False.
        """
        old_parts = old_full_path.split('.')
        new_parts = new_full_path.split('.')
        old_parent_path = '.'.join(old_parts[:-1])
        old_key = old_parts[-1]
        new_parent_path = '.'.join(new_parts[:-1])
        new_key = new_parts[-1]
        
        # Alten Eintrag finden
        old_parent = self.get_entry_by_path(old_parent_path, menu_type) if old_parent_path else self.menu_section(menu_type)
        if old_parent is None or old_key not in old_parent:
            logger.error(f"⚠️ FEHLER: Menüeintrag {old_full_path} nicht gefunden!")
            return False
        entry = old_parent.pop(old_key)
        
        # Ziel-Elternknoten ermitteln und bei Bedarf anlegen
        if new_parent_path:
            parts_np = new_parent_path.split('.')
            new_parent = self.menu_section(menu_type)
            for part in parts_np:
                if part not in new_parent or new_parent[part] is None:
                    new_parent[part] = {}
                new_parent = new_parent[part]
        else:
            new_parent = self.menu_section(menu_type)
        
        if new_parent is None:
            logger.error(f"⚠️ FEHLER: Zielpfad {new_parent_path} nicht gefunden!")
            return False
        new_parent[new_key] = entry
        return True

    def get_entry_by_path(self, full_path, menu_type):
        parts = full_path.split('.')
        node = self.menu_section(menu_type)
        for part in parts:
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return None
        return node

    def get_submenu(self, menu_type, call_path):
        """
        Ruft ein Zusatzmenü basierend auf dem vollständig qualifizierten menu_type ab.
        Beispiel: menu_type = "PD_zusatz.PD_z_Grund.Einstellungen_Layout"
        """
        try:
            submenu_section = self.menu_section(menu_type)
        except ValueError as e:
            print(e)
            submenu_section = {}
        if submenu_section is None:
            submenu_section = {}
        return submenu_section

    def get_menu_by_type(self, menu_type):
        return self.menu_section(menu_type)

    def menu_section(self, menu_type):
        """
        Greift auf einen Menüabschnitt in der Gesamtstruktur zu.
        Für Zusatzmenüs (menu_type beginnt mit "PD_zusatz") werden fehlende Schlüssel automatisch angelegt.
        Beispiel:
          Normal: "PD_grund" oder "PD_menu"
          Zusatz: "PD_zusatz.PD_z_Grund.Einstellungen_Layout"
        """
        parts = menu_type.split('.')
        section = self.__pd_structure
        for part in parts:
            if part in section:
                section = section[part]
            else:
                # Bei Zusatzmenüs Schlüssel automatisch anlegen
                if menu_type.startswith("PD_zusatz"):
                    section[part] = {}
                    section = section[part]
                else:
                    logger.error(f"⚠️ Ungültiger menu_type: {menu_type}")
                    raise ValueError(f"⚠️ Ungültiger menu_type: {menu_type}")
        return section

    def move_command(self, old_full_path, new_full_path):
        """
        Verschiebt das Kommando eines Menüeintrags.
        Dabei werden Punkte in den Pfaden in Unterstriche konvertiert.
        """
        old_key = old_full_path.replace('.', '_')
        new_key = new_full_path.replace('.', '_')
        
        commands = self.pd_structure.get("PD_commands", {})
        if old_key in commands:
            commands[new_key] = commands.pop(old_key)
            logger.info(f"✅ Kommando verschoben: '{old_key}' → '{new_key}'")
        else:
            logger.error(f"⚠️ FEHLER: Kommando '{old_key}' nicht gefunden!")

    def __get_pd_structure(self):
        return self.__pd_structure

    def __set_pd_structure(self, new_structure):
        self.__pd_structure = new_structure
        self.validate_and_normalize_structure()

    pd_structure = property(__get_pd_structure, __set_pd_structure)

    def __get_pdvm_grund(self):
        return self.__pd_structure["PD_grund"]

    def __set_pdvm_grund(self, value):
        if isinstance(value, dict):
            self.__pd_structure["PD_grund"] = value
            self.sync_pd_commands(self.__pd_structure)

    pdvm_grund = property(__get_pdvm_grund, __set_pdvm_grund)

    def __get_pdvm_menu(self):
        return self.__pd_structure["PD_menu"]

    def __set_pdvm_menu(self, value):
        if isinstance(value, dict):
            self.__pd_structure["PD_menu"] = value
            self.sync_pd_commands(self.__pd_structure)

    pdvm_menu = property(__get_pdvm_menu, __set_pdvm_menu)

    def __get_pdvm_zusatz(self):
        return self.__pd_structure["PD_zusatz"]

    def __set_pdvm_zusatz(self, value):
        if isinstance(value, dict) and "PD_z_Grund" in value and "PD_z_Menu" in value:
            self.__pd_structure["PD_zusatz"] = value
            self.sync_pd_commands(self.__pd_structure)

    pdvm_zusatz = property(__get_pdvm_zusatz, __set_pdvm_zusatz)

    def get_all_zusatz_menues(self):
        def convert_keys_to_dots(d):
            if isinstance(d, dict):
                new_dict = {}
                for k, v in d.items():
                    new_key = k.replace('_', '.')
                    new_dict[new_key] = convert_keys_to_dots(v)
                return new_dict
            else:
                return d
        grund_menus = self.__pd_structure["PD_zusatz"]["PD_z_Grund"]
        menu_menus = self.__pd_structure["PD_zusatz"]["PD_z_Menu"]
        combined_menus = {**grund_menus, **menu_menus}
        return convert_keys_to_dots(combined_menus)

    def get_command(self, key):
        key_with_underscores = key.replace('.', '_')
        command = self.__pd_structure["PD_commands"].get(key_with_underscores)
        return command

    def set_command(self, full_path, command):
        key = full_path.replace('.', '_')
        self.__pd_structure["PD_commands"][key] = command
        logger.info(f"Setze Kommando für '{key}' → '{command}'")

    def get_pdvm_commands(self):
        return self.__pd_structure["PD_commands"]

    def __str__(self):
        return json.dumps(self.__pd_structure, indent=2)
