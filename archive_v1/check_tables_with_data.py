# -*- coding: utf-8 -*-
"""Prüfe welche Tabellen Daten haben"""
import sqlite3

# Richtige DB aus PdvmInit.json verwenden
import json
with open('PdvmInit.json', 'r', encoding='utf-8') as f:
    init_data = json.load(f)
    db_path = init_data['ROOT']['datenbank']

print(f"📂 Verwende Datenbank: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Alle Tabellen
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    
    print("\n" + "="*60)
    print("📊 TABELLEN MIT DATEN")
    print("="*60)
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"\n✅ {table}: {count} Datensätze")
                
                # Prüfe ob 'name' Spalte existiert
                cursor.execute(f"PRAGMA table_info({table})")
                cols = cursor.fetchall()
                col_names = [c[1] for c in cols]
                
                has_name = 'name' in col_names
                has_uid = 'uid' in col_names
                
                print(f"   Spalten: uid={'✅' if has_uid else '❌'}, name={'✅' if has_name else '❌'}")
                
                # Wenn name-Spalte existiert, zeige Sample
                if has_name and has_uid:
                    cursor.execute(f"SELECT uid, name FROM {table} LIMIT 3")
                    samples = cursor.fetchall()
                    for uid, name in samples:
                        print(f"   - {uid[:8]}... → '{name}'")
        except Exception as e:
            print(f"   ⚠️ Fehler: {e}")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Fehler: {e}")
    import traceback
    traceback.print_exc()
