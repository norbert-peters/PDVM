#!/usr/bin/env python3
"""
Detaillierte Analyse aller Speicherorte für Suchparameter
"""

import sqlite3
import json

def detailed_search_analysis():
    conn = sqlite3.connect('PdvmManager.db')
    cursor = conn.cursor()
    
    print("=== DETAILLIERTE SUCHPARAMETER ANALYSE ===")
    
    user_guid = "4886ad26-061b-4662-a762-c8c83f36692d"
    view_guid = "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"
    
    # 1. Komplette Anwendungsdaten für den User
    print(f"\n🔍 ALLE Daten für User {user_guid}:")
    cursor.execute("SELECT uid, daten, name FROM anwendungsdaten WHERE uid = ?", (user_guid,))
    user_data = cursor.fetchall()
    
    if user_data:
        for uid, daten, name in user_data:
            print(f"  📋 Datensatz: {name or 'Unnamed'}")
            try:
                data_dict = json.loads(daten) if daten else {}
                
                # Tiefe Analyse der View-Daten
                if view_guid in data_dict:
                    view_data = data_dict[view_guid]
                    print(f"\n  🎯 View-Daten für {view_guid}:")
                    
                    # Alle Keys auflisten
                    all_keys = list(view_data.keys())
                    print(f"    📝 Alle Keys ({len(all_keys)}): {all_keys}")
                    
                    # Detailanalyse jedes Keys
                    for key, value in view_data.items():
                        print(f"\n    🔑 Key: '{key}'")
                        print(f"       Type: {type(value)}")
                        
                        if isinstance(value, dict):
                            # Dict-Inhalt analysieren
                            if 'conditions' in value:
                                conditions = value['conditions']
                                print(f"       📊 Conditions ({len(conditions)} items): {conditions}")
                            else:
                                print(f"       📊 Dict-Keys: {list(value.keys())}")
                                for sub_key, sub_value in value.items():
                                    print(f"         - {sub_key}: {sub_value} ({type(sub_value)})")
                        else:
                            print(f"       📊 Direct Value: {value}")
                    
                    # Suche nach versteckten einfachen Filtern
                    print(f"\n  🔍 SUCHE nach einfachen Filtern:")
                    simple_filter_keys = ['familienname_show', 'vorname_show', 'anrede_show', 'geburtsdatum_show']
                    
                    for filter_key in simple_filter_keys:
                        if filter_key in view_data:
                            print(f"    ✅ GEFUNDEN: {filter_key} = {view_data[filter_key]}")
                        else:
                            print(f"    ❌ NICHT gefunden: {filter_key}")
                    
                    # Suche nach 'search_filters' Container
                    if 'search_filters' in view_data:
                        search_filters = view_data['search_filters']
                        print(f"\n  📦 SEARCH_FILTERS Container gefunden:")
                        print(f"     Type: {type(search_filters)}")
                        print(f"     Content: {search_filters}")
                    else:
                        print(f"\n  ❌ Kein 'search_filters' Container gefunden")
                    
                else:
                    print(f"  ❌ Keine Daten für View {view_guid}")
                    print(f"  📋 Verfügbare Views: {list(data_dict.keys())}")
                    
            except Exception as e:
                print(f"  ❌ Fehler beim Parsen: {e}")
                print(f"  Raw Data: {daten[:500]}...")
    else:
        print(f"  ❌ Keine Daten für User {user_guid}")
    
    # 2. Suche in ALLEN Tabellen nach möglichen Suchparameter-Speicherorten
    print(f"\n\n🗃️ SUCHE in ALLEN Tabellen nach '{user_guid}' oder 'vorname':")
    
    # Alle Tabellen durchsuchen
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    for table in tables:
        try:
            cursor.execute(f"SELECT * FROM {table} WHERE uid LIKE '%{user_guid}%' OR daten LIKE '%vorname%' LIMIT 5")
            rows = cursor.fetchall()
            if rows:
                print(f"\n  📋 Tabelle '{table}': {len(rows)} Treffer")
                for i, row in enumerate(rows[:2]):  # Nur erste 2 anzeigen
                    print(f"    {i+1}: {str(row)[:200]}...")
        except Exception as e:
            print(f"    ❌ Fehler bei Tabelle {table}: {e}")
    
    conn.close()

if __name__ == "__main__":
    detailed_search_analysis()