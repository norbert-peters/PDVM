#!/usr/bin/env python3
"""
Hilfsskript zum Hinzufügen eines neuen Menüeintrags für das UnifiedPdvmDialogWidget
"""

import sqlite3
import uuid
import json
from pd_datetime import Pdvm_DateTime

def add_unified_menu_entry():
    """Fügt einen neuen Menüeintrag für das UnifiedPdvmDialogWidget hinzu."""
    
    # Verbindung zur Datenbank
    conn = sqlite3.connect('PdvmManager.db')
    cursor = conn.cursor()
    
    # Aktueller Zeitstempel im PDVM-Format
    pdvm_dt = Pdvm_DateTime()
    pdvm_dt.PdvmDateTimeNow()  # Setze auf aktuelle Zeit
    current_time = pdvm_dt.PdvmDateTime
    print(f"Aktueller PDVM-Zeitstempel: {current_time}")
    
    # Lade das Admin-Startmenü (uid: 5ca6674e-b9ce-4581-9756-64e742883f80)
    menu_uid = '5ca6674e-b9ce-4581-9756-64e742883f80'
    cursor.execute("SELECT daten FROM menudaten WHERE uid = ?", (menu_uid,))
    result = cursor.fetchone()
    
    if not result:
        print(f"❌ Menü mit UID {menu_uid} nicht gefunden!")
        conn.close()
        return
    
    # Parse die JSON-Daten
    menu_data = json.loads(result[0])
    print(f"Menü-Daten geladen für: {menu_uid}")
    
    # Prüfe, ob bereits ein Eintrag für "Unified Dialog Test" existiert
    commands = menu_data.get("PD_commands", {})
    unified_key = "Testbereich_🎨 Unified Dialog Test"
    
    if unified_key in commands:
        print(f"✅ Menüeintrag '{unified_key}' bereits vorhanden")
        print(f"   Aktueller Command: {commands[unified_key]}")
        
        # Aktualisiere den Command
        commands[unified_key] = "self.pdvm_unified_test()"
        print("   Command wurde aktualisiert")
    else:
        # Füge neuen Command hinzu
        commands[unified_key] = "self.pdvm_unified_test()"
        print(f"✅ Neuer Menüeintrag '{unified_key}' hinzugefügt")
    
    # Füge auch den Menüeintrag in die Struktur hinzu (falls nicht vorhanden)
    # Prüfe in PD_menu oder PD_grund
    if "PD_menu" in menu_data:
        if "Testbereich" not in menu_data["PD_menu"]:
            menu_data["PD_menu"]["Testbereich"] = {}
        if "🎨 Unified Dialog Test" not in menu_data["PD_menu"]["Testbereich"]:
            menu_data["PD_menu"]["Testbereich"]["🎨 Unified Dialog Test"] = None
            print("Menüstruktur in PD_menu erweitert")
    
    # Speichere die aktualisierten Daten zurück
    updated_json = json.dumps(menu_data, ensure_ascii=False, indent=2)
    cursor.execute("""
        UPDATE menudaten SET 
            daten = ?,
            last_modified = ?
        WHERE uid = ?
    """, (updated_json, current_time, menu_uid))
    
    # Änderungen speichern
    conn.commit()
    
    # Zeige alle Testbereich-Einträge
    print("\n" + "="*50)
    print("Alle Testbereich-Commands:")
    for key, value in commands.items():
        if key.startswith("Testbereich"):
            print(f"  • {key}")
            print(f"    Command: {value}")
            print()
    
    conn.close()
    print("✅ Menüeintrag erfolgreich hinzugefügt/aktualisiert!")

if __name__ == "__main__":
    add_unified_menu_entry()
