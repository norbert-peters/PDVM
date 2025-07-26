#!/usr/bin/env python3
"""Analysiere die Datenstruktur in der persondaten-Tabelle"""

from pdvm_datenbank import PdvmDatenbank
import json

def analyze_persondaten():
    """Analysiere die Struktur der persondaten"""
    
    print("🔍 Analyse der persondaten-Tabelle")
    print("=" * 50)
    
    # Persondaten-Tabelle öffnen
    db = PdvmDatenbank('PdvmManager.db', 'persondaten')
    
    # Alle Datensätze laden
    rows = db.lesen_alle()
    print(f"📊 Gefunden: {len(rows)} Datensätze")
    
    # Ersten Datensatz analysieren (mit Daten)
    for i, row in enumerate(rows):
        uid = row.get('uid', 'N/A')
        daten_raw = row.get('daten', '')
        
        print(f"\n📋 Datensatz {i+1}: {uid}")
        
        if daten_raw:
            try:
                if isinstance(daten_raw, str):
                    data = json.loads(daten_raw)
                else:
                    data = daten_raw
                    
                print(f"📊 JSON-Struktur:")
                print(f"   Gruppen: {list(data.keys())}")
                
                # Zeige erste Gruppe im Detail
                for group_name, group_data in data.items():
                    print(f"\n   📁 Gruppe '{group_name}':")
                    if isinstance(group_data, dict):
                        for field, value in group_data.items():
                            print(f"      {field}: {value}")
                    else:
                        print(f"      Wert: {group_data}")
                    
                    # Nur erste Gruppe anzeigen für Übersicht
                    break
                
                # Wenn wir ein Beispiel mit Daten gefunden haben, stoppen
                if data:
                    break
                    
            except Exception as e:
                print(f"❌ JSON-Parse-Fehler: {e}")
        else:
            print("   (Keine Daten)")

if __name__ == "__main__":
    analyze_persondaten()
