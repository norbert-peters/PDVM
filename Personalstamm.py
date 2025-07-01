import json
import pdvm_datenbank as db
import allgemeines as all


class Person:
    """Diese Klasse ist für die Verwaltung der Personalstammdaten zuständig, für Speicherung 
    und Abfragen der Daten. Die Daten werden in der Form eines Dictionaries bereitgestellt.
    Für den Anfang wird die Entwicklung mit SQLite gespeichert und verwaltet.
     
    Die Berechnungen sollen über ein allgemein gültige Verfahrensweise erfolgen, so dass 
    das Objekt immer über eine UID erreichbar ist. Jeder Wert wird historisch verwaltet.
    Das Zeitformat besteht aus dem Tag als ganze Zahl (JJJJTTT) und die Tageszeit aus dem 
    prozentualen Teil des Tages über die Nachkommastellen. Der volle Tag wird immer mit 
    JJJJTTT.0 angegeben. Damit das Format durchgehend float ist."""

    def __init__(self, guid, ab_zeit):
        self.guid = guid
        self.ab_zeit = ab_zeit
        self.pers_db = db.PdvmDatenbank(table_name="persondaten", hist=True)
        self.data = self.pers_db.lesen(guid)

    @staticmethod
    def convert_to_dict(data_tuple):
        # Annahme: data_tuple enthält einen JSON-String
        if data_tuple:
            print ("tuple",data_tuple[0])
            json_string = data_tuple[0]
            print ("json", json_string) 
            data_dict = json.loads(json_string)
            data_dict = all.convert_from_time(data_dict)
            return data_dict
        else:
            return "{}"

    @classmethod
    def from_json(cls, pd_guid, ab_zeit):
        data = db.pers_lesen(pd_guid)
        return cls(pd_guid, data)

    def get_value(self, ab_zeit, gruppe, schluessel):
        print(f"self.data: {self.data}")
        if gruppe in self.data and schluessel in self.data[gruppe]:
            print("Gruppe und Schlüssel vorhanden")
            passende_werte = {}
            for zeit, wert in self.data[gruppe][schluessel].items():
                if zeit == 1.0:
                    zeit = ab_zeit
                if zeit <= ab_zeit:
                    passende_werte[zeit] = wert
            if passende_werte:
                neueste_zeit = max(passende_werte.keys())
                return passende_werte[neueste_zeit]
        return None

    def getListe(self, ab_zeit):
        result = {}
        for gruppe, schluessel_werte in self.data.items():
            for schluessel, werte in schluessel_werte.items():
                passende_werte = {zeit: wert for zeit, wert in werte.items() if zeit <= ab_zeit}
                if passende_werte:
                    neueste_zeit = max(passende_werte.keys())
                    result[schluessel] = passende_werte[neueste_zeit]
        result["Ab-Zeit"] = ab_zeit
        return json.dumps(result)

    def set_value(self, ab_zeit, gruppe="einfach", schluessel="neu", wert=None):
        if gruppe not in self.data:
            self.data[gruppe] = {}
        if schluessel not in self.data[gruppe]:
            self.data[gruppe][schluessel] = {}

        # Überprüfen, ob der Schlüssel bereits vorhanden ist und die ab_zeit 1.0 ist
        if 1.0 in self.data[gruppe][schluessel]:
            del self.data[gruppe][schluessel][1.0]

        # Wert setzen oder überschreiben
        self.data[gruppe][schluessel][ab_zeit] = wert


    def delete_value(self, ab_zeit, gruppe, schluessel):
        if gruppe in self.data and schluessel in self.data[gruppe]:
            if ab_zeit in self.data[gruppe][schluessel]:
                del self.data[gruppe][schluessel][ab_zeit]
                # Entferne den Schlüssel, wenn keine Werte mehr vorhanden sind
                if not self.data[gruppe][schluessel]:
                    del self.data[gruppe][schluessel]
                # Entferne die Gruppe, wenn keine Schlüssel mehr vorhanden sind
                if not self.data[gruppe]:
                    del self.data[gruppe]

    def to_json(self):
        return json.dumps(self.data)
    
    def speichern(self):
        self.pers_db.speichern(self.guid, self.data)

"""
#import pdvm_datenbank as pd_db
pers_db = db.PdvmDatenbank(table_name="persondaten")

# Neuen Personendatensatz speichern
pers_guid = pers_db.anlegen({"vorname": "Max", "nachname": "Mustermann", "alter": 30})
print("Neue Person mit GUID:", pers_guid)

# Personendaten abrufen
person_daten = pers_db.lesen(pers_guid)
print("Personendaten:", person_daten)

# Eintrag ändern
# menu_db.speichern(menu_guid, {"name": "Aktualisiertes Menü", "optionen": ["Home", "Einstellungen"]})

# Eintrag löschen
# menu_db.loeschen(menu_guid)

"""








"""# Beispielverwendung
#json_data = '{"gruppe1": {"schluessel1": "wert1", "schluessel2": "wert2"}, "gruppe2": {"schluessel3": "wert3"}}'

pd_guid = "cc222a28-9fe8-42f0-a61f-db3ca26b878d"
#json_data = db.pers_lesen(pd_guid)

person = Person(pd_guid, 2025013.2)

# Wert abrufen
wert = person.get_value(2025011.1,"persönliche Daten","Name")
print(wert, "\n ")  # Ausgabe: wert1
wert = person.get_value(2025011.1,"persönliche Daten","Geburtsdatum")
print(wert, "\n ")  # Ausgabe: wert1

# Wert setzen
person.set_value(2025013.0, "persönliche Daten", "Name", "Peter Paulus")
person.set_value(2025030.0, "persönliche Daten", "Familienstand","verheiratet")
person.set_value(2025030.0, "persönliche Daten", "Gebutsdatum","1967-12-03")
person.set_value(2025010.2, "persönliche Daten", "Geburtsdatum","2001-04-24")
person.delete_value(2025010.1,"Sozialversicherung","Versicherungsnummer")

# JSON-Daten zurück in die Datenbank speichern
json_data = person.to_json()
print(json_data)
print("\n ")
print(person.data)

person.speichern()
"""
"""    def get_value(self, gruppe, schluessel, ab_zeit):
        if gruppe in self.data and schluessel in self.data[gruppe]:
            passende_werte = {zeit: wert for zeit, wert in self.data[gruppe][schluessel].items() if zeit <= ab_zeit}
            if passende_werte:
                neueste_zeit = max(passende_werte.keys())
                return passende_werte[neueste_zeit]
        return None

    def set_value(self, ab_zeit, gruppe, schluessel, wert):
        if gruppe not in self.data:
            self.data[gruppe] = {}
        if schluessel not in self.data[gruppe]:
            self.data[gruppe][schluessel] = {}
        self.data[gruppe][schluessel][ab_zeit] = wert

    def to_json(self):
        return json.dumps(self.data)

# Beispielverwendung
data_dict = {
    'persönliche Daten': {
        'Name': {
            2025010.1: 'Max Mustermann',
            2025010.2: 'Max Mustermann'
        },
        'Geburtsdatum': {
            2025010.1: '1990-01-01'
        },
        'Telefon': {
            2025010.2: '0123456789'
        }
    },
    'Anschriften': {
        'Adresse': {
            2025010.1: 'Musterstraße 1, 12345 Musterstadt',
            2025011.1: 'Beispielweg 2, 67890 Beispielstadt'
        }
    },
    'Sozialversicherung': {
        'Versicherungsnummer': {
            2025010.1: '1234567890',
            2025012.1: '0987654321'
        }
    },
    'Steuer': {
        'Steuernummer': {
            2025010.1: '111222333',
            2025013.1: '444555666'
        }
    }
}"""




"""class MeineKlasse:
    def __init__(self, daten):
        self.daten = daten

    def zeige_daten(self):
        for schluessel, wert in self.daten.items():
            print(f"{schluessel}: {wert}")

# Beispiel-Dictionary
mein_dict = {"name": "Alice", "alter": 30, "stadt": "Berlin"}

# Instanz der Klasse erstellen und Dictionary übergeben
meine_instanz = MeineKlasse(mein_dict)

# Daten anzeigen
meine_instanz.zeige_daten()
"""

"""class Person:
    def __init__(self, name=None, steuernummer=None, versicherungsnummer=None):
        self.name = name
        self.steuernummer = steuernummer
        self.versicherungsnummer = versicherungsnummer

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def set_steuernummer(self, steuernummer):
        self.steuernummer = steuernummer

    def get_steuernummer(self):
        return self.steuernummer

    def set_versicherungsnummer(self, versicherungsnummer):
        self.versicherungsnummer = versicherungsnummer

    def get_versicherungsnummer(self):
        return self.versicherungsnummer

# Beispielverwendung
person = Person()
person.set_name("Max Mustermann")
person.set_steuernummer("111222333")
person.set_versicherungsnummer("1234567890")

print(f"Name: {person.get_name()}")
print(f"Steuernummer: {person.get_steuernummer()}")
print(f"Versicherungsnummer: {person.get_versicherungsnummer()}")
"""


"""
# Beispiel-Datenstruktur
personalstamm = {
    "persönliche Daten": {
        2025010.1: {"Name": "Max Mustermann", "Geburtsdatum": "1990-01-01"},
        2025010.2: {"Name": "Max Mustermann", "Geburtsdatum": "1990-01-01", "Telefon": "0123456789"}
    },
    "Anschriften": {
        2025010.1: {"Adresse": "Musterstraße 1, 12345 Musterstadt"},
        2025011.1: {"Adresse": "Beispielweg 2, 67890 Beispielstadt"}
    },
    "Sozialversicherung": {
        2025010.1: {"Versicherungsnummer": "1234567890"},
        2025012.1: {"Versicherungsnummer": "0987654321"}
    },
    "Steuer": {
        2025010.1: {"Steuernummer": "111222333"},
        2025013.1: {"Steuernummer": "444555666"}
    }
}

# Daten verändern
personalstamm["persönliche Daten"][2025010.2]["Telefon"] = "9876543210"

# Neue Daten zu einer neuen Ab-Zeit hinzufügen
personalstamm["persönliche Daten"][2025014.1] = {"Name": "Max Waltinger", "Geburtsdatum": "1990-01-01", "Telefon": "9876543210", "Email": "max@example.com"}

print(personalstamm)

"""


