#!/usr/bin/env python3
"""
Prüfe Suchparameter in anwendungsdaten
"""

import sqlite3
import json

def check_search_parameters():
    conn = sqlite3.connect('PdvmManager.db')
    cursor = conn.cursor()
    
    print("=== SUCHPARAMETER ANALYSE ===")
    
    # Alle anwendungsdaten anzeigen
    cursor.execute("SELECT uid, daten, name FROM anwendungsdaten")
    all_data = cursor.fetchall()
    
    print(f"\n📊 Alle Anwendungsdaten ({len(all_data)} Einträge):")
    for uid, daten, name in all_data:
        print(f"  UID: {uid}")
        print(f"  Name: {name}")
        try:
            data_dict = json.loads(daten) if daten else {}
            print(f"  Daten: {json.dumps(data_dict, indent=2)[:200]}...")
        except:
            print(f"  Daten (raw): {str(daten)[:100]}...")
        print()
    
    # Suche nach User GUID 4886ad26-061b-4662-a762-c8c83f36692d
    user_guid = "4886ad26-061b-4662-a762-c8c83f36692d"
    view_guid = "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"
    
    print(f"🔍 Suche nach Suchparametern für User: {user_guid}")
    cursor.execute("SELECT uid, daten, name FROM anwendungsdaten WHERE uid = ?", (user_guid,))
    user_data = cursor.fetchall()
    
    if user_data:
        for uid, daten, name in user_data:
            print(f"  ✅ User-Daten gefunden:")
            print(f"    UID: {uid}")
            print(f"    Name: {name}")
            try:
                data_dict = json.loads(daten) if daten else {}
                print(f"    Struktur: {list(data_dict.keys())}")
                
                # Prüfe auf View-GUID als Gruppe
                if view_guid in data_dict:
                    view_data = data_dict[view_guid]
                    print(f"    🎯 View-Daten für {view_guid}:")
                    print(f"       Felder: {list(view_data.keys()) if isinstance(view_data, dict) else 'Nicht dict-Format'}")
                    if isinstance(view_data, dict):
                        for field, value in view_data.items():
                            print(f"         {field}: {value}")
                else:
                    print(f"    ❌ Keine Daten für View {view_guid} gefunden")
                    print(f"    📋 Verfügbare Gruppen: {list(data_dict.keys())}")
                    
            except Exception as e:
                print(f"    ❌ Fehler beim Parsen der Daten: {e}")
                print(f"    Raw: {daten}")
    else:
        print(f"  ❌ Keine Daten für User {user_guid} gefunden")
    
    conn.close()

if __name__ == "__main__":
    check_search_parameters()