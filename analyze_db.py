#!/usr/bin/env python3
"""
Analysiere die Datenbank-Struktur für Suchparameter
"""

import sqlite3

def analyze_database():
    conn = sqlite3.connect('PdvmManager.db')
    cursor = conn.cursor()
    
    print("=== DATENBANK ANALYSE ===")
    
    # Tabellen auflisten
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("\n📋 Verfügbare Tabellen:")
    for row in tables:
        table_name = row[0]
        print(f"  - {table_name}")
        
        # Tabellenstruktur anzeigen
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"    Spalten: {[col[1] for col in columns]}")
        
        # Erste paar Einträge zeigen
        try:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            rows = cursor.fetchall()
            print(f"    Beispieldaten: {len(rows)} Einträge")
            for i, row in enumerate(rows[:2]):
                print(f"      {i+1}: {str(row)[:100]}...")
        except Exception as e:
            print(f"    Fehler beim Lesen: {e}")
        print()
    
    conn.close()

if __name__ == "__main__":
    analyze_database()