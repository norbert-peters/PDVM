import json

class PDVMMenu:
    def __init__(self):
        # Gesamte Struktur mit leeren Default-Bereichen:
        self._structure = {
            "PD_commands": {},
            "PD_grund": {},
            "PD_menu": {},
            "PD_zusatz": {
                "PD_z_Grund": {},
                "PD_z_Menu": {}
            }
        }
    
    # Gesamtstruktur als Property
    @property
    def structure(self):
        return self._structure
    
    @structure.setter
    def structure(self, value):
        self._structure["PD_commands"] = value.get("PD_commands", {})
        self._structure["PD_grund"] = value.get("PD_grund", {})
        self._structure["PD_menu"] = value.get("PD_menu", {})
        self._structure["PD_zusatz"] = value.get("PD_zusatz", {"PD_z_Grund": {}, "PD_z_Menu": {}})
    
    # Properties für die einzelnen Bereiche:
    @property
    def pdvm_commands(self):
        return self._structure["PD_commands"]
    
    @pdvm_commands.setter
    def pdvm_commands(self, value):
        self._structure["PD_commands"] = value
    
    @property
    def pdvm_grund(self):
        return self._structure["PD_grund"]
    
    @pdvm_grund.setter
    def pdvm_grund(self, value):
        """
        Setzt eine neue Grundstruktur und entfernt ungültige Zusatzmenüs.
        """
        self.structure["PD_grund"] = value.get("PD_grund", {})
        self._cleanup_zusatz("PD_z_Grund", self.structure["PD_grund"])

    @property
    def pdvm_menu(self):
        return self._structure["PD_menu"]
    
    @pdvm_menu.setter
    def pdvm_menu(self, value):
        self._structure["PD_menu"] = value
    
    @property
    def pdvm_zusatz(self):
        return self._structure["PD_zusatz"]
    
    @pdvm_zusatz.setter
    def pdvm_zusatz(self, value):
        # Hier wird erwartet, dass value ein Dictionary mit den Keys "PD_z_Grund" und "PD_z_Menu" ist.
        self._structure["PD_zusatz"] = value

    # --- Hilfsmethoden für den Zugriff auf einzelne Menüeinträge ---
    def _get_item(self, area_dict, path):
        """ Holt einen Eintrag anhand eines Pfads (getrennt durch Punkte). """
        keys = path.split(".")
        current = area_dict
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current

    def _set_item(self, area_dict, path, value):
        """ Setzt einen Eintrag anhand eines Pfads. """
        keys = path.split(".")
        current = area_dict
        for key in keys[:-1]:
            current = current.setdefault(key, {})
        current[keys[-1]] = value

    def _delete_item(self, area_dict, path):
        """ Löscht einen Eintrag anhand eines Pfads. """
        keys = path.split(".")
        current = area_dict
        for key in keys[:-1]:
            if key in current:
                current = current[key]
            else:
                return None
        return current.pop(keys[-1], None)

    def get_item(self, area, path):
        """
        Ruft einen Menüeintrag aus dem angegebenen Bereich ab.
        Bei 'zusatz' wird nur die erste Stelle des Pfads aufgelöst, der Rest bleibt ein Schlüssel.
        """
        mapping = {
            "commands": self._structure.get("PD_commands", {}),
            "grund": self._structure.get("PD_grund", {}),
            "menu": self._structure.get("PD_menu", {}),
            "zusatz": self._structure.get("PD_zusatz", {})
        }

        if area not in mapping:
            return None

        if area == "zusatz":
            # Sonderbehandlung für 'PD_zusatz': Nur die erste Stelle des Pfads wird aufgelöst
            first_key, rest_key = path.split(".", 1) if "." in path else (path, None)
            
            if first_key in mapping[area]:
                return mapping[area][first_key].get(rest_key) if rest_key else mapping[area][first_key]
            return None
        else:
            # Standardverhalten für andere Bereiche
            return self._get_item(mapping[area], path)


    def set_item(self, area, path, value):
        """
        Setzt einen Menüeintrag in dem angegebenen Bereich.
        Bei 'zusatz' wird nur die erste Stelle des Pfads aufgelöst, der Rest bleibt ein Schlüssel.
        """
        mapping = {
            "commands": self._structure["PD_commands"],
            "grund": self._structure["PD_grund"],
            "menu": self._structure["PD_menu"],
            "zusatz": self._structure["PD_zusatz"]
        }
        
        if area not in mapping:
            return
        
        if area == "zusatz":
            # Sonderbehandlung für 'PD_zusatz': Nur die erste Stelle des Pfads wird aufgelöst
            first_key, rest_key = path.split(".", 1) if "." in path else (path, None)
            
            if rest_key:
                mapping[area][first_key][rest_key] = value  # Rest bleibt als Schlüssel
            else:
                mapping[area][first_key] = value  # Falls kein weiterer Pfad existiert
        else:
            # Standardverhalten für andere Bereiche
            self._set_item(mapping[area], path, value)


    def delete_item(self, area, path):
        """
        Löscht einen Menüeintrag im angegebenen Bereich.
        Bei 'zusatz' wird nur die erste Stelle des Pfads aufgelöst, der Rest bleibt ein Schlüssel.
        """
        mapping = {
            "commands": self._structure.get("PD_commands", {}),
            "grund": self._structure.get("PD_grund", {}),
            "menu": self._structure.get("PD_menu", {}),
            "zusatz": self._structure.get("PD_zusatz", {})
        }

        if area not in mapping:
            return

        if area == "zusatz":
            # Sonderbehandlung für 'PD_zusatz': Nur die erste Stelle des Pfads wird aufgelöst
            first_key, rest_key = path.split(".", 1) if "." in path else (path, None)
            
            if first_key in mapping[area]:
                if rest_key and rest_key in mapping[area][first_key]:
                    del mapping[area][first_key][rest_key]
                elif not rest_key:
                    del mapping[area][first_key]
        else:
            # Standardverhalten für andere Bereiche
            self._delete_item(mapping[area], path)

    def set_pdvm_grund(self, new_grund):
        """
        Setzt eine neue Grundstruktur und entfernt ungültige Zusatzmenüs.
        """
        self.structure["PD_grund"] = new_grund.get("PD_grund", {})
        self._cleanup_zusatz("PD_z_Grund", self.structure["PD_grund"])

    def set_pdvm_menu(self, new_menu):
        """
        Setzt eine neue Menüstruktur und entfernt ungültige Zusatzmenüs.
        """
        self.structure["PD_menu"] = new_menu.get("PD_menu", {})
        self._cleanup_zusatz("PD_z_Menu", self.structure["PD_menu"])
    
    def _cleanup_zusatz(self, zusatz_key, reference_structure):
        """
        Überprüft, ob die in PD_zusatz gespeicherten Pfade noch in der Hauptstruktur existieren.
        Entfernt verwaiste Einträge.
        """
        zusatz = self.structure["PD_zusatz"].get(zusatz_key, {})
        
        keys_to_delete = []
        for path in zusatz.keys():
            path_parts = path.split(".")
            if not self._path_exists(reference_structure, path_parts):
                keys_to_delete.append(path)
        
        for key in keys_to_delete:
            del self.structure["PD_zusatz"][zusatz_key][key]
    
    def _path_exists(self, structure, path_parts):
        """
        Prüft, ob ein gegebener Pfad in einer geschachtelten Struktur existiert.
        """
        current = structure
        for part in path_parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return False
        return True



# --- Beispiel-Testcode ---

if __name__ == '__main__':
    import TestStrukturen as ts
    
    manager = PDVMMenu()
    # Setze die Gesamtstruktur
    manager.structure = ts.pdvm_struktur()
    print("-- 1 --Gesamtstruktur:\n", json.dumps(manager.structure, indent=3))
    print(" -- 1 -- Neuer pdvm_grund\n ",ts.pdvm_grund())
    manager.pdvm_grund = ts.pdvm_grund()  

    print("-- 2 --Gesamtstruktur:\n", json.dumps(manager.structure, indent=3))
