#!/usr/bin/env python3
"""
Korrektur der Menüdaten - entfernt GUID-Verschachtelung in der daten-Spalte
"""

import logging
import json
import sqlite3

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_menu_data_structure():
    """Korrigiert die Menüdaten - entfernt GUID-Verschachtelung aus der daten-Spalte"""
    
    db_path = "PdvmManager.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Beide problematische Menüs korrigieren
        menu_guids = [
            "5ca6674e-b9ce-4581-9756-64e742883f80",  # Admin-Startmenü
            "e1e77039-d1b5-46ff-b12b-cced0ae0da7c"   # Admin-Benutzermenü
        ]
        
        for menu_guid in menu_guids:
            print(f"\n🔧 Korrigiere Menü: {menu_guid}")
            
            # Aktuellen Inhalt laden
            cursor.execute("SELECT daten, bezeichnung FROM menudaten WHERE uid = ?", (menu_guid,))
            result = cursor.fetchone()
            
            if result:
                current_data, bezeichnung = result
                print(f"📋 Bezeichnung: {bezeichnung}")
                
                try:
                    # Lade aktuelle (fehlerhaft verschachtelte) Struktur
                    data_dict = json.loads(current_data)
                    print(f"❌ Fehlerhafte Struktur erkannt - Hauptschlüssel: {list(data_dict.keys())}")
                    
                    # Extrahiere die richtige Menüstruktur
                    if menu_guid in data_dict and "daten" in data_dict[menu_guid]:
                        # Korrekte Struktur aus der Verschachtelung extrahieren
                        correct_structure = json.loads(data_dict[menu_guid]["daten"])
                        print(f"✅ Korrekte Struktur extrahiert: {list(correct_structure.keys())}")
                        
                        # Direkt als JSON ohne GUID-Verschachtelung speichern
                        correct_json = json.dumps(correct_structure, ensure_ascii=False, indent=2)
                        
                        # In Datenbank aktualisieren
                        cursor.execute(
                            "UPDATE menudaten SET daten = ? WHERE uid = ?",
                            (correct_json, menu_guid)
                        )
                        
                        print(f"✅ Menü {menu_guid} korrekt ohne GUID-Verschachtelung gespeichert")
                        
                    else:
                        print(f"❌ Erwartete Verschachtelung nicht gefunden in {menu_guid}")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON-Fehler bei {menu_guid}: {e}")
            else:
                print(f"❌ Keine Daten für GUID {menu_guid} gefunden")
        
        # Änderungen committen
        conn.commit()
        print("\n✅ Alle Änderungen in die Datenbank committet")
        
        # Verification - Struktur nach Korrektur prüfen
        print("\n🔍 Verifikation der korrigierten Strukturen:")
        for menu_guid in menu_guids:
            cursor.execute("SELECT daten, bezeichnung FROM menudaten WHERE uid = ?", (menu_guid,))
            result = cursor.fetchone()
            if result:
                data, bezeichnung = result
                try:
                    structure = json.loads(data)
                    print(f"✅ {bezeichnung} ({menu_guid}): {list(structure.keys())}")
                    
                    # Prüfe ob PD_grund vorhanden ist
                    if "PD_grund" in structure:
                        print(f"   ✅ PD_grund gefunden: {list(structure['PD_grund'].keys())}")
                    else:
                        print(f"   ❌ PD_grund fehlt!")
                        
                except json.JSONDecodeError:
                    print(f"   ❌ JSON noch immer fehlerhaft")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Datenbankfehler: {e}")

if __name__ == "__main__":
    fix_menu_data_structure()
    print("\n🎯 Menüdaten-Korrektur abgeschlossen!")
    print("📋 Die daten-Spalte enthält jetzt direkt die Menüstruktur ohne GUID-Verschachtelung")
    print("🔄 Starten Sie das PDVM-System neu - der KeyError sollte behoben sein")
