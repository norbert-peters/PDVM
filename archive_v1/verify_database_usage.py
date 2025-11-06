#!/usr/bin/env python3
"""
VERIFIZIERUNG: KORREKTE DATENBANK-NUTZUNG
==========================================

Überprüft ob Filter jetzt korrekt in anwendungsdaten (nicht systemsteuerung) gespeichert werden
"""

import sqlite3
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_correct_database_usage():
    """Verifiziert dass Filter in anwendungsdaten landen"""
    print("🔍 VERIFIZIERUNG: Korrekte Datenbank-Nutzung")
    print("=" * 50)
    
    try:
        with sqlite3.connect("PdvmManager.db") as conn:
            cursor = conn.cursor()
            
            # 1. Check anwendungsdaten für Filter
            print("\\n📋 Prüfe anwendungsdaten Tabelle:")
            cursor.execute("SELECT uid, name, daten FROM anwendungsdaten WHERE uid LIKE '%test%'")
            
            anwendung_found = False
            for row in cursor.fetchall():
                uid, name, daten = row
                try:
                    data_dict = json.loads(daten) if daten else {}
                    filter_keys = [key for key in data_dict.keys() if key.endswith('_show')]
                    if filter_keys:
                        anwendung_found = True
                        print(f"   ✅ UID: {uid}")
                        print(f"       Filter-Spalten: {filter_keys}")
                        
                        for key in filter_keys:
                            if isinstance(data_dict[key], dict):
                                simple_search = data_dict[key].get('simple_search', '')
                                conditions = len(data_dict[key].get('conditions', []))
                                print(f"       {key}: simple='{simple_search}', conditions={conditions}")
                            else:
                                print(f"       {key}: {data_dict[key]}")
                except:
                    continue
            
            if not anwendung_found:
                print("   ⚠️ Keine Filter in anwendungsdaten gefunden")
            
            # 2. Check systemsteuerung für Filter (sollten KEINE da sein)
            print("\\n📋 Prüfe systemsteuerung Tabelle (sollte KEINE Filter enthalten):")
            cursor.execute("SELECT uid, name, daten FROM systemsteuerung WHERE uid LIKE '%test%'")
            
            system_found = False
            for row in cursor.fetchall():
                uid, name, daten = row
                try:
                    data_dict = json.loads(daten) if daten else {}
                    filter_keys = [key for key in data_dict.keys() if key.endswith('_show')]
                    if filter_keys:
                        system_found = True
                        print(f"   ❌ PROBLEM: Filter in systemsteuerung gefunden!")
                        print(f"       UID: {uid}")
                        print(f"       Filter-Spalten: {filter_keys}")
                except:
                    continue
            
            if not system_found:
                print("   ✅ Korrekt: Keine Filter in systemsteuerung gefunden")
            
            # 3. Zusammenfassung
            print("\\n📊 VERIFIZIERUNGS-ERGEBNIS:")
            if anwendung_found and not system_found:
                print("✅ KORREKT: Filter werden in anwendungsdaten gespeichert")
                print("✅ KORREKT: Keine Filter in systemsteuerung")
                print("🎉 Architektur-Fehler erfolgreich behoben!")
                return True
            elif system_found:
                print("❌ PROBLEM: Filter noch in systemsteuerung gefunden")
                return False
            else:
                print("⚠️ Keine Test-Filter gefunden")
                return False
                
    except Exception as e:
        print(f"❌ Fehler bei Verifizierung: {e}")
        return False


if __name__ == "__main__":
    success = verify_correct_database_usage()
    exit(0 if success else 1)