import Personalstamm as ps
import allgemeines as all
from pd_datetime import Pdvm_DateTime as pdd
import pdvm_datenbank as db
import pdvm_default as pd_df

#pd_guid = "cc222a28-9fe8-42f0-a61f-db3ca26b878d"
#pd_guid = "10905894-64a6-4978-a9e1-79bb8d5bbc88"
#pd_guid = "a4f00502-e0c9-4de2-856b-388d43ef8986"
#pd_guid = "ed21cb69-046b-465f-b231-6e75852b50b3"
#pd_guid = "0d66233c-eaf5-4407-ac57-40781922bd94"
#pd_guid = "74573a62-d07c-473c-ba2a-4540e66977d8"
pd_guid = all.neue_guid()
g_datum = "28.02.2025"

# Beispielverwendung
#obj = pdd()
#obj.Date = "2023-04-06"  # Datum setzen
#print(obj.Date)  # Datum abfragen

obj = pdd()
obj.Date = g_datum
pd_gad = obj.PdvmDateTime
print (obj.Date)
print (obj.PdvmDateTime)

person = ps.Person(pd_guid, pd_gad)

print("gefunden ", person.data)
# Wert abrufen
if person.data != None:
    wert = person.get_value(pd_gad,"PersDaten","Personalnummer")
    print("Personalnummer     : ",wert)  # Ausgabe: wert1
    wert = person.get_value(pd_gad,"PersDaten","Name")
    print("Name               : ",wert)  # Ausgabe: wert1
    wert = person.get_value(pd_gad,"PersDaten","Vorname")
    print("Vorname            : ",wert)  # Ausgabe: wert1
    wert = person.get_value(pd_gad,"PersDaten","Geburtsdatum")
    print("Geburtsdatum       : ",wert)  # Ausgabe: wert1
    wert = person.get_value(pd_gad,"PersDaten","Familienstand")
    print("Familienstand      : ",wert)  # Ausgabe: wert1
    wert = person.get_value(pd_gad,"Anschriften","Adress")
    print("Anschrift          : ",wert)  # Ausgabe: wert1
    wert = person.get_value(pd_gad,"Sozialversicherung","Versicherungsnummer")
    print("Versicherungsnummer: ",wert)  # Ausgabe: wert1
    wert = person.get_value(pd_gad,"Steuer","Steuernummer")
    print("Steuernummer       : ",wert, "\n ")  # Ausgabe: wert1

    print (person.getListe(2024230.0))
    print ("\n")
    print (person.getListe(2025040.0))
    print ("\n")
else:
    person.data = pd_df.pers_base_data()
# Wert setzen """
person.set_value(pd_gad, "PersDaten", "Personalnummer", "A1")
person.set_value(pd_gad, "PersDaten", "Name", "Berblinger")
person.set_value(pd_gad, "PersDaten", "Vorname", "Host")
person.set_value(pd_gad, "PersDaten", "Familienstand","verheiratet")
person.set_value(pd_gad, "PersDaten", "Gebutsdatum","1967324.0")
person.set_value(pd_gad, "PersDaten", "Geschlecht","männlich")
person.set_value(pd_gad, "Anschrift_Person", "Strasse","Hauptstraße")
person.set_value(pd_gad, "Anschrift_Person", "Hausnummer","23")
person.set_value(pd_gad, "Anschrift_Person", "Postleitzahl","89173")
person.set_value(pd_gad, "Anschrift_Person", "Ort","Lonsee")
#person.delete_value(2025010.1,"Sozialversicherung","Versicherungsnummer")

# JSON-Daten zurück in die Datenbank speichern
json_data = person.to_json()
print(json_data)

person.speichern()
