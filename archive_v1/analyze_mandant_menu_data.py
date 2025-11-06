"""
Analysiert vorhandene Menü-Daten in den Mandanten-Datenbanken
"""
import sqlite3
import json
import os

def analyze_menu_data(db_path):
    """Analysiert Menü-Daten in einer Datenbank"""
    print(f"\n{'='*80}")
    print(f"Analysiere: {db_path}")
    print(f"{'='*80}")
    
    if not os.path.exists(db_path):
        print(f"❌ Datenbank nicht gefunden: {db_path}")
        return None
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Prüfe Tabelle
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%menu%'")
    tables = cursor.fetchall()
    print(f"\n📂 Menü-Tabellen: {[t[0] for t in tables]}")
    
    if 'sys_menudaten' not in [t[0] for t in tables]:
        print("❌ Tabelle sys_menudaten existiert nicht")
        conn.close()
        return None
    
    # Hole alle Menü-Einträge
    cursor.execute("SELECT uid, name, daten FROM sys_menudaten")
    rows = cursor.fetchall()
    
    print(f"\n📊 Anzahl Menü-Einträge: {len(rows)}")
    
    menu_data_list = []
    for row in rows:
        uid, name, daten_json = row
        print(f"\n{'─'*80}")
        print(f"UID: {uid}")
        print(f"Name: {name}")
        
        if daten_json:
            try:
                daten = json.loads(daten_json)
                print(f"Daten-Struktur:")
                print(f"  Keys: {list(daten.keys())}")
                
                # Zeige Details
                if isinstance(daten, dict):
                    for key, value in daten.items():
                        if isinstance(value, list):
                            print(f"  {key}: Liste mit {len(value)} Einträgen")
                            if len(value) > 0:
                                print(f"    Beispiel: {value[0]}")
                        elif isinstance(value, dict):
                            print(f"  {key}: Dict mit Keys: {list(value.keys())}")
                        else:
                            print(f"  {key}: {value}")
                
                menu_data_list.append({
                    'uid': uid,
                    'name': name,
                    'daten': daten
                })
            except Exception as e:
                print(f"❌ Fehler beim Parsen: {e}")
        else:
            print("⚠️  Keine Daten vorhanden")
    
    conn.close()
    return menu_data_list

if __name__ == "__main__":
    print("🔍 PDVM Menü-Daten Analyse")
    print("="*80)
    
    # Analysiere beide Mandanten
    mandant_001_data = analyze_menu_data("Daten/mandant_001/datenbank.db")
    mandant_002_data = analyze_menu_data("Daten/mandant_002/datenbank.db")
    
    print(f"\n\n{'='*80}")
    print("📋 ZUSAMMENFASSUNG")
    print(f"{'='*80}")
    print(f"Mandant 001: {len(mandant_001_data) if mandant_001_data else 0} Menüs gefunden")
    print(f"Mandant 002: {len(mandant_002_data) if mandant_002_data else 0} Menüs gefunden")
