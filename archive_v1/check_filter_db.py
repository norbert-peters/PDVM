"""
Prüft DB-Inhalte für Filter-Parameter (Einfach-Filter Test)
"""

import sqlite3
from pdvm_central_systemsteuerung import get_gcs

def check_filter_data():
    """Prüft was in der DB gespeichert ist"""
    
    print("=== 🔍 FILTER DB CHECK ===\n")
    
    # GCS prüfen
    gcs = get_gcs()
    if gcs:
        print(f"✅ GCS verfügbar")
        print(f"   User GUID: {gcs.user_guid}")
    else:
        print("❌ GCS nicht verfügbar - App muss laufen!")
        return
    
    # Datenbank prüfen
    try:
        conn = sqlite3.connect('anwendungsdaten.db')
        cursor = conn.cursor()
        
        # Alle relevanten Filter-Einträge
        cursor.execute("""
            SELECT gruppe, feld, wert 
            FROM anwendungsdaten 
            WHERE feld IN ('s_string', 's_source', 'familienname_show', 'vorname_show', 'schnell')
            ORDER BY gruppe, feld
        """)
        
        results = cursor.fetchall()
        
        if not results:
            print("❌ Keine Filter-Daten in DB gefunden!")
        else:
            print(f"✅ {len(results)} Einträge gefunden:\n")
            
            current_gruppe = None
            for gruppe, feld, wert in results:
                if gruppe != current_gruppe:
                    print(f"\n📂 View GUID: {gruppe[:30]}...")
                    current_gruppe = gruppe
                
                # Wert kürzen wenn zu lang
                wert_str = str(wert)
                if len(wert_str) > 60:
                    wert_str = wert_str[:60] + "..."
                
                print(f"   {feld:20} → {wert_str}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Fehler beim DB-Zugriff: {e}")

if __name__ == '__main__':
    check_filter_data()
