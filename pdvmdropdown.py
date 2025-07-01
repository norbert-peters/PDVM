import uuid
from pdvm_datenbank import PdvmDatenbank
import json

class PdvmDropdown:
    def __init__(self, guid=None):
        # Wenn keine GUID übergeben wird, wird eine neue erstellt.
        self.guid = guid if guid is not None else str(uuid.uuid4())

        # Datenbank-Instanz erzeugen
        self.pers_db = PdvmDatenbank(table_name="dropdowndaten")
        # Daten aus der Datenbank laden
        self.data = self.pers_db.lesen(self.guid)
        if self.data is None:
            # Wenn keine Daten vorhanden sind, initialisiere mit leeren Strukturen
            #self.data = self.pers_db.lesen("94c9024d-6b61-416c-89ae-5fb18030977e")    # Standardwerte
            print("Keine Daten gefunden, initialisiere mit leeren Strukturen.")
            self.data = {}
#        self.convert_keys_to_upper()
        print(f"Dropdown mit GUID {self.guid} geladen.")
        print(f"Initialisierte Daten: {json.dumps(self.data, indent=4)}")

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

    def get_translation(self, section_key, key, language):
        """
        Wandelt den internen Schlüssel in den anzuzeigenden Text um.

        :param section_key: Der Bereich, z.B. "anrede" oder "waehrung".
        :param key: Der intern gespeicherte Schlüssel, z.B. "m" oder "EUR".
        :param language: Der gewünschte Sprachcode, z.B. "de" oder "en".
        :return: Der übersetzte Text oder, falls nicht vorhanden, der originale Schlüssel.
        """
        section = self.data.get(section_key)
        if not section:
            print(f"Warnung: Abschnitt '{section_key}' nicht gefunden.")
            return key
        for option in section.get("werte", []):
            if option.get("key") == key:
                return option.get(language, key)
        return key

    def get_value(self, section_key):
        """

        Gibt den zuletzt eingetragenen Wert (mit ab_zeit <= gegebenem Zeitpunkt) zurück.
        Falls kein Wert vorhanden ist, wird None zurückgegeben.
        """
        print(f"Suche Wert für {section_key}.")
        return self.data.get(section_key, None)

    def set_value(self, section_key, language , wert, ab_zeit=1001.0):
        """
        Überschreibt einen vorhandenen Wert mit derselben ab_zeit oder fügt einen neuen Eintrag hinzu.
        Wir erzeugen einen Schlüssel, indem wir ab_zeit als String mit 5 Nachkommastellen formatieren.
        """
        # Zuerst in einen Float umwandeln
        ab_zeit_float = float(ab_zeit)
        # Erzeuge den String-Key mit 5 Nachkommastellen
        ab_zeit_key = format(ab_zeit_float, ".5f")
        
        # Sicherstellen, dass die Gruppe und das Feld existieren
        if section_key not in self.data:
            self.data[section_key] = {}
        if language not in self.data[section_key]:
            self.data[section_key][language] = {}
        
        print(f"Setze Wert für {section_key}.{language} (ab_zeit: {ab_zeit_key}) auf {wert}.")
        self.data[section_key][language][ab_zeit_key] = wert

    def delete_value(self, gruppe, feld, ab_zeit=1001.0):
        """
        Löscht den Wert für den exakten ab_zeit, sofern vorhanden.
        """
        # Zuerst in einen Float umwandeln
        ab_zeit_float = float(ab_zeit)
        # Erzeuge den String-Key mit 5 Nachkommastellen
        ab_zeit_key = format(ab_zeit_float, ".5f")

        if not ab_zeit_float > 1002.0:
            return False  # Abbruch, wenn ab_zeit nicht größer als 1002.0 ist   
        try:
            if ab_zeit_key in self.data[gruppe][feld]:
                del self.data[gruppe][feld][ab_zeit_key]
                return True
        except KeyError:
            # Entweder existiert die Gruppe oder das Feld nicht – nichts zu löschen
            return False

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
        Fügt die DropdownSatz in die Datenbank ein.
        Hier wird nur ein Platzhalter genutzt – in der echten Implementierung
        würde hier z.B. ein Insert in die Datenbank erfolgen.
        """
        # Beispiel: PdvmDatenbank.create_values(self.guid, self.data)
        print(f"Dropdown mit GUID {self.guid} wird in der Datenbank erstellt.")

    def save_values(self):
        """
        Speichert (update) den DropdownSatz in der Datenbank.
        """
        # Beispiel: PdvmDatenbank.save_values(self.guid, self.data)
        self.pers_db.speichern(self.guid, self.data)

        # Hier wird die Datenbank aktualisiert gelesen.
#        self.data = self.pers_db.lesen(self.guid)
#        if self.data is None:
            # Wenn keine Daten vorhanden sind, initialisiere mit leeren Strukturen
#            self.data = self.pers_db.lesen("94c9024d-6b61-416c-89ae-5fb18030977e")    # Standardwerte
#        self.convert_keys_to_upper()

        print(f"Person mit GUID {self.guid} wird in der Datenbank gespeichert.")


# Beispielhafte Nutzung:
if __name__ == "__main__":
    # Neue Instanz erzeugen (mit automatischer GUID-Erstellung)
    dropdown = PdvmDropdown()
    
    # Lese einen Wert aus
    #wert = person.get_value(2025050.0, 'PersDaten', 'Name')
    #print("Name (zum Zeitpunkt 2025050.0):", wert)
    
    
    # Setze einen neuen Wert
    #person.set_value(2026000.0, 'PersDaten', 'Name', 'Mustermann')
    #neuer_wert = person.get_value(2026000.0, 'PersDaten', 'Name')
    #print("Neuer Name (zum Zeitpunkt 2026000.0):", neuer_wert)
    
    # Lösche den Wert für einen bestimmten Zeitpunkt
    #person.delete_value(2026000.0, 'PersDaten', 'Name')
    #gelöschter_wert = person.get_value(2026000.0, 'PersDaten', 'Name')
    #print("Name nach Löschen (zum Zeitpunkt 2026000.0):", gelöschter_wert)
    
    # Lösche ein komplettes Feld
    #person.delete_field('PersDaten', 'Telefon')
    #print("Telefon-Feld nach Löschen:", person.data.get('PersDaten', {}).get('Telefon'))
    
    # Lösche eine Gruppe
    #person.delete_group('Steuer')
    #print("Steuer-Gruppe nach Löschen:", person.data.get('Steuer'))
    
    # Erstelle bzw. speichere die Person in der (Platzhalter-)Datenbank
    dropdown.create_values()
    dropdown.save_values()
