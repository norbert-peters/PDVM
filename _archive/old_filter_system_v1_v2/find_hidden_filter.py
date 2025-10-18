#!/usr/bin/env python3
"""
Suche nach dem versteckten vorname Filter
"""

import sqlite3
import json

def find_hidden_filter():
    conn = sqlite3.connect('PdvmManager.db')
    cursor = conn.cursor()
    
    print("=== SUCHE NACH VERSTECKTEM VORNAME FILTER ===")
    
    # Detaillierte Suche in systemsteuerung
    user_guid = "4886ad26-061b-4662-a762-c8c83f36692d"
    
    print(f"\n🔍 SYSTEMSTEUERUNG für User {user_guid}:")
    cursor.execute("SELECT uid, daten FROM systemsteuerung WHERE uid = ?", (user_guid,))
    systemdata = cursor.fetchall()
    
    for uid, daten in systemdata:
        try:
            data_dict = json.loads(daten)
            print(f"  📋 Systemsteuerung Struktur:")
            
            # Tiefe durchsuchen nach Filtern
            def deep_search(obj, path="ROOT"):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}.{key}"
                        if 'filter' in key.lower() or 'search' in key.lower() or 'vorname' in str(value).lower():
                            print(f"    🔍 POTENTIELLER FILTER: {current_path} = {value}")
                        deep_search(value, current_path)
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        deep_search(item, f"{path}[{i}]")
            
            deep_search(data_dict)
            
        except Exception as e:
            print(f"    ❌ Fehler beim Parsen Systemsteuerung: {e}")
    
    # Detaillierte Suche in menudaten
    print(f"\n🔍 MENUDATEN:")
    cursor.execute("SELECT uid, daten, bezeichnung FROM menudaten")
    menudata = cursor.fetchall()
    
    for uid, daten, bezeichnung in menudata:
        try:
            data_dict = json.loads(daten)
            print(f"  📋 Menu {bezeichnung}: {uid}")
            
            # Suche nach Spalten-Konfiguration mit Filtern
            if 'columns' in data_dict:
                columns = data_dict['columns']
                print(f"    📊 Columns ({len(columns)} Einträge):")
                for col in columns:
                    if isinstance(col, dict) and 'name' in col:
                        col_name = col['name']
                        print(f"      - {col_name}: {col}")
                        # Prüfe auf Filter-Related Properties
                        filter_props = ['filter', 'search', 'value']
                        for prop in filter_props:
                            if prop in col:
                                print(f"        🔍 FILTER GEFUNDEN: {col_name}.{prop} = {col[prop]}")
            
            # Suche nach anderen Filter-Strukturen
            def search_filters(obj, path="ROOT"):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}.{key}"
                        if 'vorname' in str(value).lower() or 'search' in key.lower() or 'filter' in key.lower():
                            print(f"    🔍 POTENTIELLER FILTER: {current_path} = {value}")
                        search_filters(value, current_path)
            
            search_filters(data_dict)
            
        except Exception as e:
            print(f"    ❌ Fehler beim Parsen Menu: {e}")
    
    conn.close()

if __name__ == "__main__":
    find_hidden_filter()