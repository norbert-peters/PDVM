#!/usr/bin/env python3
"""
Prüfe direkt in der Datenbank ob das \" Problem gelöst ist
"""

import sqlite3
import json

def check_database_directly():
    """Schaue direkt in die SQLite Datenbank"""
    
    print("=== DIREKTE DATENBANK-PRÜFUNG ===")
    
    # Verbinde zur Datenbank
    db_path = "systemsteuerung_data.db" 
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Hole alle Tabellen
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📋 Verfügbare Tabellen: {[t[0] for t in tables]}")
        
        # Versuche beide möglichen Tabellennamen
        table_names = ['systemsteuerung', 'SystemSteuerung', 'systemsteuerung_data']
        
        for table_name in table_names:
            try:
                cursor.execute(f"SELECT uid, daten FROM {table_name}")
                rows = cursor.fetchall()
                print(f"📊 Tabelle '{table_name}': {len(rows)} Einträge")
        
        for uid, daten in rows:
            if "test_linear_view" in uid or "test_problematic_view" in uid:
                print(f"\n🔍 EINTRAG: {uid}")
                print(f"📄 RAW DATA: {daten[:200]}...")
                
                # Prüfe auf \" Problem
                backslash_quote_count = daten.count('\\"')
                normal_quote_count = daten.count('"') - backslash_quote_count
                
                print(f"📈 ANALYSE:")
                print(f"   - Backslash-Quotes (\\\"): {backslash_quote_count}")
                print(f"   - Normale Quotes (\"): {normal_quote_count}")
                
                if backslash_quote_count > 0:
                    print(f"❌ JSON-DOPPEL-ENCODING PROBLEM NOCH DA!")
                else:
                    print(f"✅ KEIN JSON-DOPPEL-ENCODING PROBLEM!")
                
                # Versuche zu parsen
                try:
                    parsed = json.loads(daten)
                    print(f"✅ JSON erfolgreich geparst")
                    
                    # Zeige Struktur
                    if isinstance(parsed, dict):
                        for key, value in parsed.items():
                            print(f"   - {key}: {type(value).__name__}")
                            if isinstance(value, dict):
                                for subkey in value.keys():
                                    print(f"     - {subkey}: {type(value[subkey]).__name__}")
                            
                except Exception as e:
                    print(f"❌ JSON-Parse-Fehler: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Datenbank-Fehler: {e}")
    
    print(f"\n=== DATENBANK-PRÜFUNG ABGESCHLOSSEN ===")

if __name__ == "__main__":
    check_database_directly()
