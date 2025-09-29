#!/usr/bin/env python3
"""
Bereinigung der Systemsteuerung-Struktur
========================================

Problem: Inkonsistente Datenstruktur in systemsteuerung-Tabelle
- Benutzer-Settings unter user_guid statt view_guid
- View-Daten teilweise korrekt/inkorrekt strukturiert

Lösung: Bereinigung nach dem Grundprinzip:
- Gruppe = view_guid
- Felder = alle view-spezifischen Daten (controls, projections, etc.)
"""

import sqlite3
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def analyze_current_structure():
    """
    Analysiert die aktuelle Struktur und zeigt Inkonsistenzen
    """
    print("🔍 ANALYSE DER AKTUELLEN SYSTEMSTEUERUNG-STRUKTUR")
    print("=" * 60)
    
    conn = sqlite3.connect('PdvmManager.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT uid, daten FROM systemsteuerung WHERE historisch = 0')
    rows = cursor.fetchall()
    
    view_guids = set()
    user_guids = set()
    
    for uid, daten_json in rows:
        if not daten_json or daten_json == '{}':
            continue
            
        try:
            daten = json.loads(daten_json)
        except:
            continue
            
        # Alle GUIDs sammeln
        for key in daten.keys():
            if len(key) == 36 and '-' in key:  # GUID Format
                if key.startswith('0d10a0d0') or key.startswith('3E8F') or key.startswith('4886'):
                    view_guids.add(key)
                else:
                    user_guids.add(key)
    
    print(f"📊 USER GUIDs: {len(user_guids)}")
    for guid in sorted(user_guids):
        print(f"   - {guid}")
        
    print(f"📊 VIEW GUIDs: {len(view_guids)}")  
    for guid in sorted(view_guids):
        print(f"   - {guid}")
    
    # Detailanalyse der Struktur
    print("\n🔍 DETAILANALYSE DER DATENSTRUKTUR")
    print("=" * 60)
    
    for uid, daten_json in rows:
        if not daten_json or daten_json == '{}':
            continue
            
        try:
            daten = json.loads(daten_json)
        except:
            continue
            
        print(f"\n📁 UID: {uid}")
        
        for key, value in daten.items():
            if len(key) == 36 and '-' in key:  # GUID
                if isinstance(value, dict):
                    print(f"   🔸 {key} ({len(value)} Felder)")
                    for subkey in value.keys():
                        if subkey.startswith(key + '_'):
                            print(f"      ✅ KORREKT: {subkey}")
                        elif subkey in ['controls', 'searchparameter', 'table_projection', 'search_projection', 'management_projection']:
                            print(f"      ❌ INKORREKT: {subkey} (sollte {key}_{subkey})")
                        else:
                            print(f"      ⚪ {subkey}")
    
    conn.close()

def create_clean_structure():
    """
    Erstellt eine bereinigte Struktur basierend auf view_guid Gruppierung
    """
    print("\n🧹 BEREINIGUNG DER SYSTEMSTEUERUNG-STRUKTUR")
    print("=" * 60)
    
    conn = sqlite3.connect('PdvmManager.db')
    cursor = conn.cursor()
    
    # Alle aktuellen Daten lesen
    cursor.execute('SELECT uid, daten FROM systemsteuerung WHERE historisch = 0')
    rows = cursor.fetchall()
    
    view_data_consolidated = {}
    user_settings = {}
    
    for uid, daten_json in rows:
        if not daten_json or daten_json == '{}':
            continue
            
        try:
            daten = json.loads(daten_json)
        except:
            continue
        
        # Durch alle Schlüssel iterieren
        for key, value in daten.items():
            if len(key) == 36 and '-' in key:  # GUID Format
                if key.startswith('0d10a0d0') or key.startswith('3E8F') or key.startswith('4886'):
                    # VIEW GUID - konsolidieren
                    if key not in view_data_consolidated:
                        view_data_consolidated[key] = {}
                    
                    if isinstance(value, dict):
                        # Alle Felder der View hinzufügen
                        for field_key, field_value in value.items():
                            # Korrekte Feldnamen mit view_guid Prefix
                            if field_key.startswith(key + '_'):
                                # Bereits korrekt
                                clean_field_key = field_key
                            elif field_key in ['controls', 'searchparameter', 'table_projection', 
                                             'search_projection', 'management_projection', 'projection_matrix']:
                                # Korrektur erforderlich
                                clean_field_key = field_key  # Ohne Prefix - das ist der Standard
                            else:
                                # Andere Felder beibehalten
                                clean_field_key = field_key
                            
                            view_data_consolidated[key][clean_field_key] = field_value
                            print(f"   ✅ {key}.{clean_field_key}")
                else:
                    # USER GUID - Settings
                    if uid not in user_settings:
                        user_settings[uid] = {}
                    user_settings[uid][key] = value
                    print(f"   👤 User {uid}: {key}")
            else:
                # Direkte Felder - ignorieren oder zu User Settings
                print(f"   ⚠️  Ignoriert: {key}")
    
    print(f"\n📊 BEREINIGTE STRUKTUR:")
    print(f"   - {len(view_data_consolidated)} View GUIDs")
    print(f"   - {len(user_settings)} User Settings")
    
    return view_data_consolidated, user_settings

def preview_cleanup():
    """
    Zeigt eine Vorschau der bereinigten Struktur
    """
    print("🔍 VORSCHAU DER BEREINIGTEN STRUKTUR")
    print("=" * 60)
    
    view_data, user_settings = create_clean_structure()
    
    print("\n🎯 NEUE STRUKTUR PRO VIEW:")
    for view_guid, fields in view_data.items():
        print(f"\n📁 VIEW: {view_guid}")
        for field_name in sorted(fields.keys()):
            print(f"   ├─ {field_name}")
    
    print(f"\n👤 USER SETTINGS: {len(user_settings)} Benutzer")
    
    return view_data, user_settings

def apply_cleanup(confirm=False):
    """
    Wendet die Bereinigung tatsächlich an
    """
    if not confirm:
        print("\n⚠️  ACHTUNG: Dies ist nur eine Vorschau!")
        print("   Um die Bereinigung anzuwenden: apply_cleanup(confirm=True)")
        return
    
    print("\n🚀 ANWENDUNG DER BEREINIGUNG")
    print("=" * 60)
    
    view_data, user_settings = create_clean_structure()
    
    conn = sqlite3.connect('PdvmManager.db')
    cursor = conn.cursor()
    
    # Backup erstellen
    import datetime
    backup_suffix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS systemsteuerung_backup_{backup_suffix} AS 
        SELECT * FROM systemsteuerung WHERE historisch = 0
    ''')
    print(f"✅ Backup erstellt: systemsteuerung_backup_{backup_suffix}")
    
    # Alte Daten als historisch markieren
    cursor.execute('UPDATE systemsteuerung SET historisch = 1 WHERE historisch = 0')
    print("✅ Alte Daten als historisch markiert")
    
    # Neue bereinigte Struktur einfügen
    import time
    current_time = str(time.time())
    
    for view_guid, fields in view_data.items():
        clean_data = {view_guid: fields}
        cursor.execute('''
            INSERT INTO systemsteuerung (uid, daten, historisch, last_modified, stichtag)
            VALUES (?, ?, 0, ?, '9999365.00000')
        ''', (view_guid, json.dumps(clean_data, ensure_ascii=False), current_time))
        print(f"✅ View {view_guid}: {len(fields)} Felder eingefügt")
    
    # User Settings beibehalten
    for uid, settings in user_settings.items():
        cursor.execute('''
            INSERT INTO systemsteuerung (uid, daten, historisch, last_modified, stichtag)
            VALUES (?, ?, 0, ?, '9999365.00000')
        ''', (uid, json.dumps(settings, ensure_ascii=False), current_time))
        print(f"✅ User {uid}: Settings beibehalten")
    
    conn.commit()
    conn.close()
    
    print(f"\n🎉 BEREINIGUNG ABGESCHLOSSEN!")
    print(f"   - {len(view_data)} Views bereinigt")
    print(f"   - {len(user_settings)} User Settings beibehalten")

if __name__ == "__main__":
    # Schritt 1: Aktuelle Struktur analysieren
    analyze_current_structure()
    
    # Schritt 2: Vorschau der bereinigten Struktur
    preview_cleanup()
    
    print("\n" + "="*60)
    print("🎯 NÄCHSTE SCHRITTE:")
    print("   1. Diese Analyse überprüfen")
    print("   2. apply_cleanup(confirm=True) aufrufen um zu bereinigen")
    print("   3. Oder Daten manuell aus der Datenbank löschen")
    print("="*60)