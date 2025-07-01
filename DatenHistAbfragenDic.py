
# Funktion zum Abrufen des aktuellen Werts basierend auf dem Zeitstempel
def aktueller_wert(daten, zeitstempel):
    gültige_werte = {k: v for k, v in daten.items() if k <= zeitstempel}
    if gültige_werte:
        letzter_zeitstempel = max(gültige_werte.keys())
        return gültige_werte[letzter_zeitstempel]
    return None


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
"""
# Funktion zum Abrufen des Namens basierend auf dem Zeitstempel
def name_zu_ab_zeit(daten, feld, zeitstempel):
    gültige_werte = {k: v for k, v in daten.items() if k <= zeitstempel}
    if gültige_werte:
        letzter_zeitstempel = max(gültige_werte.keys())
        return gültige_werte[letzter_zeitstempel].get(feld)
    return None

"""
# Beispiel-Abfrage
zeitstempel = 2025010.2
name = name_zu_ab_zeit(personalstamm["Steuer"], "Steuernummer", zeitstempel)
print(f"Der Name zum Zeitstempel {zeitstempel} ist: {name}")
"""
# Funktion zur Konvertierung der Ab-Zeiten
def konvertiere_ab_zeiten(daten):
    konvertierte_daten = {}
    for bereich, werte in daten.items():
        konvertierte_daten[bereich] = {float(k): v for k, v in werte.items()}
    return konvertierte_daten

