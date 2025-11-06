#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Diagnose: Zeigt wo Controls in der Datenbank gespeichert sind

Prüft ob name_original/name_show unter "controls" oder "ColumnControls" zu finden sind
"""

import sqlite3
import json
import os

DB_PATH = "PdvmManager.db"

def analyze_controls_storage():
    """Analysiert wo Controls in der DB gespeichert sind"""
    print("\n" + "="*80)
    print("DIAGNOSE: Controls-Speicherung in Datenbank")
    print("="*80)
    
    if not os.path.exists(DB_PATH):
        print(f"FEHLER: Datenbank nicht gefunden: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Finde systemsteuerung Tabelle
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%systemsteuerung%'")
    sys_tables = cursor.fetchall()
    
    if not sys_tables:
        print("\nKeine systemsteuerung Tabelle gefunden!")
        conn.close()
        return
    
    print(f"\nGefundene Systemsteuerung-Tabellen: {len(sys_tables)}")
    
    for (table_name,) in sys_tables:
        print(f"\n{'='*80}")
        print(f"TABELLE: {table_name}")
        print(f"{'='*80}")
        
        # Hole alle Einträge
        cursor.execute(f"SELECT uid, daten FROM {table_name}")
        rows = cursor.fetchall()
        
        print(f"\nGefundene Datensaetze: {len(rows)}")
        
        for uid, daten_str in rows:
            try:
                daten = json.loads(daten_str)
                
                # Prüfe auf beide Feldnamen
                has_controls = 'controls' in daten
                has_column_controls = 'ColumnControls' in daten
                
                if has_controls or has_column_controls:
                    print(f"\n{'─'*80}")
                    print(f"UID: {uid}")
                    print(f"{'─'*80}")
                    
                    if has_controls:
                        controls = daten['controls']
                        print(f"\n  [1] Feld 'controls' gefunden:")
                        print(f"      Anzahl Controls: {len(controls)}")
                        
                        # Prüfe auf name_original und name_show
                        has_name_orig = 'name_original' in controls
                        has_name_show = 'name_show' in controls
                        
                        print(f"\n      SYSTEM-Spalten:")
                        print(f"        uid_original:  {'JA' if 'uid_original' in controls else 'NEIN'}")
                        print(f"        name_original: {'JA' if has_name_orig else 'NEIN'}")
                        print(f"        uid_show:      {'JA' if 'uid_show' in controls else 'NEIN'}")
                        print(f"        name_show:     {'JA' if has_name_show else 'NEIN'}")
                        
                        if has_name_orig:
                            print(f"\n      name_original Details:")
                            print(f"        {json.dumps(controls['name_original'], indent=10)}")
                    
                    if has_column_controls:
                        col_controls = daten['ColumnControls']
                        print(f"\n  [2] Feld 'ColumnControls' gefunden:")
                        print(f"      Anzahl Controls: {len(col_controls)}")
                        
                        # Prüfe auf name_original und name_show
                        has_name_orig = 'name_original' in col_controls
                        has_name_show = 'name_show' in col_controls
                        
                        print(f"\n      SYSTEM-Spalten:")
                        print(f"        uid_original:  {'JA' if 'uid_original' in col_controls else 'NEIN'}")
                        print(f"        name_original: {'JA' if has_name_orig else 'NEIN'}")
                        print(f"        uid_show:      {'JA' if 'uid_show' in col_controls else 'NEIN'}")
                        print(f"        name_show:     {'JA' if has_name_show else 'NEIN'}")
                        
                        if has_name_orig:
                            print(f"\n      name_original Details:")
                            print(f"        {json.dumps(col_controls['name_original'], indent=10)}")
                    
                    # Vergleich
                    if has_controls and has_column_controls:
                        print(f"\n  [!] BEIDE Felder vorhanden!")
                        print(f"      GCS liest aus: 'controls'")
                        print(f"      VIEW schreibt in: 'ColumnControls'")
                        print(f"      => NAMENS-MISMATCH!")
                    elif has_controls:
                        print(f"\n  [OK] Nur 'controls' vorhanden - GCS findet es!")
                    elif has_column_controls:
                        print(f"\n  [!] Nur 'ColumnControls' vorhanden - GCS findet es NICHT!")
                        
            except json.JSONDecodeError:
                print(f"  WARNUNG: Konnte daten nicht parsen für UID {uid}")
                
    conn.close()
    print("\n" + "="*80)
    print("Diagnose abgeschlossen")
    print("="*80 + "\n")

if __name__ == '__main__':
    analyze_controls_storage()
