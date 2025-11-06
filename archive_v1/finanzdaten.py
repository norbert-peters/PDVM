import uuid
from pdvm_datenbank import PdvmDatenbank
#import tkinter as tk

import logging
logger = logging.getLogger(__name__)

# Test-Meldung mit Unicode
logger.info("🔹 PdvmInputManager gestartet")
#logger.warning("⚠ Achtung, etwas ist schiefgelaufen!")

class Finanzdaten:
    def __init__(self, guid=None):
        # Wenn keine GUID übergeben wird, wird eine neue erstellt.
        self.guid = guid if guid is not None else str(uuid.uuid4())

        # Datenbank-Instanz erzeugen
        self.finanz_db = PdvmDatenbank(table_name="finanzdaten")
        # Daten aus der Datenbank laden
        self.data = self.finanz_db.lesen(self.guid)

        self.convert_keys_to_upper()

    def convert_keys_to_upper(self):
        """
        Wandelt alle Gruppen- und Feldnamen in der Datenstruktur in Großbuchstaben um.
        """
        new_data = {}
        for group, fields in self.data.items():
            # Gruppe in Großbuchstaben
            new_fields = {}
            for field, value in fields.items():
                # Feldname in Großbuchstaben; ab_zeit-Schlüssel bleiben unverändert
                new_fields[field.upper()] = value
            new_data[group.upper()] = new_fields
        self.data = new_data
        
    def get_all_values(self):
        """
        Gibt alle Werte der Finanzdaten zurück. 
        """
        return self.data

    def get_value(self, gruppe, feld, ab_zeit=None):
        """
        Gibt den zuletzt eingetragenen Wert (mit ab_zeit <= gegebenem Zeitpunkt) zurück.
        Falls kein Wert vorhanden ist, wird None zurückgegeben.
        """
    #    logger.info(f"🔹 Suche Wert für in Finanzdaten {gruppe}.{feld} )")
        try:
            return {"wert":self.data[gruppe][feld]}
        except KeyError:
            # Gruppe oder Feld existiert nicht
            return {}

    def set_value(self, gruppe, feld, wert, ab_zeit=None):
        """
        Überschreibt einen vorhandenen Wert oder fügt einen neuen Eintrag hinzu.
        """
        if gruppe not in self.data:
            self.data[gruppe] = {}
        if feld not in self.data[gruppe]:
            self.data[gruppe][feld] = {}
        # Setze oder überschreibe den Wert für diesen Zeitpunkt.
        self.data[gruppe][feld] = wert

    def delete_value(self, gruppe, feld):
        """
        Löscht den Wert für den exakten ab_zeit, sofern vorhanden.
        """
        try:
            if feld in self.data[gruppe][feld]:
                del self.data[gruppe][feld]
        except KeyError:
            # Entweder existiert die Gruppe oder das Feld nicht – nichts zu löschen
            pass


    def delete_group(self, gruppe):
        """
        Entfernt die komplette Gruppe aus der Datenstruktur.
        """
        try:
            del self.data[gruppe]
        except KeyError:
            # Gruppe nicht vorhanden.
            pass

    def create_values(self):
        """
        Fügt die PersonFinanzdaten in die Datenbank ein.
        Hier wird nur ein Platzhalter genutzt – in der echten Implementierung
        würde hier z.B. ein Insert in die Datenbank erfolgen.
        """
        # Beispiel: PdvmDatenbank.create_person(self.guid, self.data)
        print(f"Finanzdaten mit GUID {self.guid} wird in der Datenbank erstellt.")

    def save_values(self):
        """
        Speichert (update) die Person in der Datenbank.
        """
        # Beispiel: PdvmDatenbank.save_person(self.guid, self.data)
        self.finanz_db.speichern(self.guid, self.data)
        print(f"Finanzdaten mit GUID {self.guid} wird in der Datenbank gespeichert.")


