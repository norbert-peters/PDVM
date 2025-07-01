import uuid
import json 
from pdvm_datenbank import PdvmDatenbank

import logging
logger = logging.getLogger(__name__)

# Test-Meldung mit Unicode
logger.info("🔹 PdvmPerson gestartet")
#logger.warning("⚠ Achtung, etwas ist schiefgelaufen!")

class PdvmPerson:
    def __init__(self, guid=None):
        # Wenn keine GUID übergeben wird, wird eine neue erstellt.
        self.guid = guid if guid is not None else str(uuid.uuid4())

        # Datenbank-Instanz erzeugen
        self.pers_db = PdvmDatenbank(table_name="persondaten")
        # Daten aus der Datenbank laden
        self.data = self.pers_db.lesen(self.guid)
        if self.data is None:
            # Wenn keine Daten vorhanden sind, initialisiere mit leeren Strukturen
            self.data = self.pers_db.lesen("00000000-0000-0000-0000-000000000000")    # Standardwerte
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
        Gibt alle Werte der Person zurück.
        """
        return self.data

    def get_value(self, ab_zeit, gruppe, feld):
        """
        Gibt den zuletzt eingetragenen Wert (mit ab_zeit <= gegebenem Zeitpunkt) zurück.
        Falls kein Wert vorhanden ist, wird None zurückgegeben.
        """
        try:
            zeitpunkte = [zeit for zeit in self.data[gruppe][feld].keys() if zeit <= ab_zeit]
            if not zeitpunkte:
                return None
            # Wähle den maximalen Zeitpunkt (letzter gültiger Wert)
            max_zeit = max(zeitpunkte)
            return {"ab_zeit": max_zeit, "wert": self.data[gruppe][feld][max_zeit]}
        except KeyError:
            # Gruppe oder Feld existiert nicht
            return {}

    def set_value(self, ab_zeit, gruppe, feld, wert):
        """
        Überschreibt einen vorhandenen Wert mit derselben ab_zeit oder fügt einen neuen Eintrag hinzu.
        """
        if gruppe not in self.data:
            self.data[gruppe] = {}
        if feld not in self.data[gruppe]:
            self.data[gruppe][feld] = {}
        # Setze oder überschreibe den Wert für diesen Zeitpunkt.
        self.data[gruppe][feld][ab_zeit] = wert

    def delete_value(self, ab_zeit, gruppe, feld):
        """
        Löscht den Wert für den exakten ab_zeit, sofern vorhanden.
        """
        try:
            if ab_zeit in self.data[gruppe][feld]:
                del self.data[gruppe][feld][ab_zeit]
        except KeyError:
            # Entweder existiert die Gruppe oder das Feld nicht – nichts zu löschen
            pass

    def delete_field(self, gruppe, feld):
        """
        Entfernt das komplette Feld aus der angegebenen Gruppe.
        """
        try:
            del self.data[gruppe][feld]
        except KeyError:
            # Feld oder Gruppe nicht vorhanden.
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
        Fügt die Person in die Datenbank ein.
        Hier wird nur ein Platzhalter genutzt – in der echten Implementierung
        würde hier z.B. ein Insert in die Datenbank erfolgen.
        """
        # Beispiel: PdvmDatenbank.create_person(self.guid, self.data)
        print(f"Person mit GUID {self.guid} wird in der Datenbank erstellt.")

    def save_values(self):
        """
        Speichert (update) die Person in der Datenbank.
        Auch hier wird lediglich ein Platzhalter ausgegeben.
        """
        logger.info(f"🔹 Person mit GUID {self.guid} wird in der Datenbank gespeichert.")
        self.save_person(self.guid, self.data)
        logger.info(f"🔹 Daten zum Speichern: {json.dumps(self.data, indent=4)}")


"""
# Beispielhafte Nutzung:
if __name__ == "__main__":
    # Neue Instanz erzeugen (mit automatischer GUID-Erstellung)
    person = PdvmPerson()
    
    # Lese einen Wert aus
    wert = person.get_value(2025050.0, 'PersDaten', 'Name')
    print("Name (zum Zeitpunkt 2025050.0):", wert)
    
    
    # Setze einen neuen Wert
    person.set_value(2026000.0, 'PersDaten', 'Name', 'Mustermann')
    neuer_wert = person.get_value(2026000.0, 'PersDaten', 'Name')
    print("Neuer Name (zum Zeitpunkt 2026000.0):", neuer_wert)
    
    # Lösche den Wert für einen bestimmten Zeitpunkt
    person.delete_value(2026000.0, 'PersDaten', 'Name')
    gelöschter_wert = person.get_value(2026000.0, 'PersDaten', 'Name')
    print("Name nach Löschen (zum Zeitpunkt 2026000.0):", gelöschter_wert)
    
    # Lösche ein komplettes Feld
    person.delete_field('PersDaten', 'Telefon')
    print("Telefon-Feld nach Löschen:", person.data.get('PersDaten', {}).get('Telefon'))
    
    # Lösche eine Gruppe
    person.delete_group('Steuer')
    print("Steuer-Gruppe nach Löschen:", person.data.get('Steuer'))
    
    # Erstelle bzw. speichere die Person in der (Platzhalter-)Datenbank
    person.create_person()
    person.save_person()
"""