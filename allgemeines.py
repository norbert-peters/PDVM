import uuid


def neue_guid():
    # Eine neue GUID erzeugen
    return str(uuid.uuid4())

def convert_from_time(daten):
    # Funktion zur Konvertierung der Ab-Zeiten (String → Float)
    konvertierte_daten = {}
    for gruppe, schluessel_werte in daten.items():
        konvertierte_daten[gruppe] = {}
        for schluessel, werte in schluessel_werte.items():
            # Robuste Konvertierung: Nur gültige Float-Keys übernehmen
            konvertierte_werte = {}
            for k, v in werte.items():
                try:
                    float_key = float(k)
                    konvertierte_werte[float_key] = v
                except (ValueError, TypeError) as e:
                    # Ungültigen Key überspringen (z.B. Objekt-Strings)
                    import logging
                    logging.warning(f"⚠️ Überspringe ungültigen Zeitstempel-Key: {k} (Fehler: {e})")
                    continue
            konvertierte_daten[gruppe][schluessel] = konvertierte_werte
    return konvertierte_daten


def convert_to_time(daten):
    # Funktion zur Konvertierung der Ab-Zeiten (Float → String für JSON)
    konvertierte_daten = {}
    for gruppe, schluessel_werte in daten.items():
        konvertierte_daten[gruppe] = {}
        for schluessel, werte in schluessel_werte.items():
            if isinstance(werte, dict):
                # Historische Daten: Float-Keys → String-Keys
                konvertierte_daten[gruppe][schluessel] = {str(k): v for k, v in werte.items()}
            else:
                # Direkter Wert (nicht-historisch)
                konvertierte_daten[gruppe][schluessel] = werte
    return konvertierte_daten




    