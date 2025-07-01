"""Hier sind die Funktionen enthalten, die mit der Datenbank zu tun haben. In der 
Entwicklungszeit wird hier eine SQLite als Datenbank verwendet. Alle Daten werden 
im JSON-Format abglegt und als Dictionaries verarbeitet. Eine historische Daten-
ablage ist sichergestellt."""

import sqlite3
import json
import allgemeines as all
import pdvm_default as pd_df 

def pers_anlegen(daten):
    # Verbindung zur SQLite-Datenbank herstellen (erstellt die Datei, 
    # falls sie nicht existiert)
    conn = sqlite3.connect('PdvmManager.db')
    cursor = conn.cursor()

    # Tabelle erstellen falls sie nicht existiert
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS persondaten (
        uid TEXT PRIMARY KEY,
        daten TEXT NOT NULL
    )
    '''
    # Cursor setzten
    cursor.execute(create_table_query)

    json_daten = json.dumps(daten)

    # Daten einfügen
    insert_query = 'INSERT INTO persondaten (uid, daten) VALUES (?, ?)'
    uid = all.neue_guid()  # der Primärschlüssel ist eine GUID
    cursor.execute(insert_query, (str(uid), json_daten))

    # Änderungen speichern und Verbindung schließen
    conn.commit()
    conn.close()

def pers_speichern(guid, daten):
    # Verbindung zur SQLite-Datenbank herstellen
    conn = sqlite3.connect('PdvmManager.db')
    cursor = conn.cursor()

    pd_guid = str(guid)

    # Prüfen, ob der Datensatz bereits existiert
    select_query = 'SELECT COUNT(*) FROM persondaten WHERE uid = ?'
    cursor.execute(select_query, (pd_guid,))
    result = cursor.fetchone()

    json_daten = json.dumps(daten)

    if result[0] > 0:
        # Datensatz existiert, Update durchführen
        update_query = 'UPDATE persondaten SET daten = ? WHERE uid = ?'
        cursor.execute(update_query, (json_daten, pd_guid))
    else:
        # Datensatz existiert nicht, Insert durchführen
        insert_query = 'INSERT INTO persondaten (uid, daten) VALUES (?, ?)'
        cursor.execute(insert_query, (pd_guid, json_daten))

    # Änderungen speichern und Verbindung schließen
    conn.commit()
    conn.close()

def pers_lesen(guid):
    # Verbindung zur SQLite-Datenbank herstellen
    conn = sqlite3.connect('PdvmManager.db')
    cursor = conn.cursor()

    # Daten abrufen
    select_query = 'SELECT daten FROM persondaten WHERE uid = ?'
    cursor.execute(select_query, (str(guid),))
    result = cursor.fetchone()
    conn.close()

    if result:
        #print("result ",result[0])
        #print("json.load ",json.loads(result[0]))
        data_dict = all.convert_from_time(json.loads(result[0]))
        #data_dict = {} #wennn satz vorhanden ohne Daten zur Korrektur

        return data_dict
    else:
        print(f"GUID {guid} nicht gefunden.")
        return pd_df.pers_base_data()
    
# Menüdaten für Anwendung
#############################################################################
def menu_anlegen(daten):
    # Verbindung zur SQLite-Datenbank herstellen (erstellt die Datei, 
    # falls sie nicht existiert)
    conn = sqlite3.connect('PdvmManager.db')
    cursor = conn.cursor()

    # Tabelle erstellen falls sie nicht existiert
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS menudaten (
        uid Text PRIMARY KEY,
        daten TEXT NOT NULL
    )
    '''
    # Cursor setzten
    cursor.execute(create_table_query)

    json_daten = json.dumps(daten)

    # Daten einfügen
    insert_query = 'INSERT INTO menudaten (uid, daten) VALUES (?, ?)'
    uid = all.neue_guid()  # der Primärschlüssel ist eine GUID
    print("GUID ", str(uid))
    print("Daten: ", str(json_daten))
    cursor.execute(insert_query, (str(uid), str(json_daten)))

    # Änderungen speichern und Verbindung schließen
    conn.commit()
    conn.close()

def menu_speichern(guid, daten):
    # Verbindung zur SQLite-Datenbank herstellen
    conn = sqlite3.connect('PdvmManager.db')
    cursor = conn.cursor()

    pd_guid = str(guid)

    # Prüfen, ob der Datensatz bereits existiert
    select_query = 'SELECT COUNT(*) FROM menudaten WHERE uid = ?'
    cursor.execute(select_query, (pd_guid,))
    result = cursor.fetchone()

    json_daten = json.dumps(daten)

    if result[0] > 0:
        # Datensatz existiert, Update durchführen
        update_query = 'UPDATE menudaten SET daten = ? WHERE uid = ?'
        cursor.execute(update_query, (json_daten, pd_guid))
    else:
        # Datensatz existiert nicht, Insert durchführen
        insert_query = 'INSERT INTO menudaten (uid, daten) VALUES (?, ?)'
        cursor.execute(insert_query, (pd_guid, json_daten))

    # Änderungen speichern und Verbindung schließen
    conn.commit()
    conn.close()

def menu_lesen(guid):
    # Verbindung zur SQLite-Datenbank herstellen
    conn = sqlite3.connect('PdvmManager.db')
    cursor = conn.cursor()

    # Daten abrufen
    select_query = 'SELECT daten FROM menudaten WHERE uid = ?'
    cursor.execute(select_query, (str(guid),))
    result = cursor.fetchone()
    conn.close()

    if result:
        #print("result ",result[0])
        #print("json.load ",json.loads(result[0]))
        data_dict = all.convert_from_time(json.loads(result[0]))

        return data_dict
    else:
        print(f"GUID {guid} nicht gefunden.")
        return pd_df.menu_base_data()
    



# pers_anlegen("")
