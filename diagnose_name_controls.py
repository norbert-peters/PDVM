#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Diagnose-Script: Prüft ob name_original und name_show Controls in GCS gespeichert sind

Beantwortet die User-Fragen:
1. Werden Controls wie für uid_original aufgebaut? → JA (siehe Code)
2. Werden sie in GCS gespeichert? → PRÜFEN
3. Sind sie in der Projektion? → PRÜFEN
"""

import sqlite3
import json
import os

# Pfad zur Hauptdatenbank (aus PdvmInit.json)
DB_PATH = os.path.join(os.path.dirname(__file__), "PdvmManager.db")

def check_name_controls_in_db():
    """Prüft ob name_original und name_show in ColumnControls gespeichert sind"""
    print("\n" + "="*80)
    print("🔍 DIAGNOSE: name_original und name_show Controls")
    print("="*80)
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Datenbank nicht gefunden: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Hole alle Views aus der DB
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"\n📂 Tabellen in systemsteuerung.db: {len(tables)}")
    
    # Suche nach ColumnControls Einträgen
    for (table_name,) in tables:
        try:
            # Prüfe ob Tabelle 'daten' Spalte hat
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'daten' not in columns:
                continue
                
            # Hole ColumnControls Einträge
            cursor.execute(f"SELECT uid, daten FROM {table_name} WHERE uid LIKE '%ColumnControls%'")
            results = cursor.fetchall()
            
            if results:
                print(f"\n{'='*80}")
                print(f"📋 Tabelle: {table_name}")
                print(f"   Gefundene ColumnControls Einträge: {len(results)}")
                
                for uid, daten_str in results:
                    try:
                        daten = json.loads(daten_str)
                        
                        print(f"\n   🔑 UID: {uid}")
                        print(f"   📊 Anzahl Controls: {len(daten)}")
                        
                        # Prüfe auf name_original und name_show
                        has_name_original = 'name_original' in daten
                        has_name_show = 'name_show' in daten
                        has_uid_original = 'uid_original' in daten
                        has_uid_show = 'uid_show' in daten
                        
                        print(f"\n   ✅ SYSTEM-Controls:")
                        print(f"      uid_original:  {'✅ VORHANDEN' if has_uid_original else '❌ FEHLT'}")
                        print(f"      uid_show:      {'✅ VORHANDEN' if has_uid_show else '❌ FEHLT'}")
                        print(f"      name_original: {'✅ VORHANDEN' if has_name_original else '❌ FEHLT'}")
                        print(f"      name_show:     {'✅ VORHANDEN' if has_name_show else '❌ FEHLT'}")
                        
                        if has_name_original:
                            name_orig_data = daten['name_original']
                            print(f"\n   📝 name_original Details:")
                            print(f"      show:         {name_orig_data.get('show', 'N/A')}")
                            print(f"      expertOrder:  {name_orig_data.get('expertOrder', 'N/A')}")
                            print(f"      displayOrder: {name_orig_data.get('displayOrder', 'N/A')}")
                        
                        if has_name_show:
                            name_show_data = daten['name_show']
                            print(f"\n   📝 name_show Details:")
                            print(f"      show:         {name_show_data.get('show', 'N/A')}")
                            print(f"      expertOrder:  {name_show_data.get('expertOrder', 'N/A')}")
                            print(f"      displayOrder: {name_show_data.get('displayOrder', 'N/A')}")
                        
                        # Zeige alle Controls
                        print(f"\n   📜 Alle Controls in dieser View:")
                        for i, (key, val) in enumerate(daten.items(), 1):
                            show_flag = "👁️" if val.get('show', False) else "🙈"
                            print(f"      {i:2d}. {show_flag} {key:30s} (expert:{val.get('expertOrder', 'N/A'):3}, display:{val.get('displayOrder', 'N/A'):3})")
                        
                    except json.JSONDecodeError:
                        print(f"   ⚠️ Konnte daten nicht als JSON parsen")
                        
        except sqlite3.Error as e:
            print(f"   ⚠️ Fehler bei Tabelle {table_name}: {e}")
    
    conn.close()
    print("\n" + "="*80)
    print("✅ Diagnose abgeschlossen")
    print("="*80 + "\n")

if __name__ == '__main__':
    check_name_controls_in_db()
