import uuid


def neue_guid():
    # Eine neue GUID erzeugen
    return str(uuid.uuid4())

def convert_from_time(daten):
    # Funktion zur Konvertierung der Ab-Zeiten
    konvertierte_daten = {}
    for gruppe, schluessel_werte in daten.items():
        konvertierte_daten[gruppe] = {}
        for schluessel, werte in schluessel_werte.items():
            konvertierte_daten[gruppe][schluessel] = {float(k): v for k, v in werte.items()}
    return konvertierte_daten




    