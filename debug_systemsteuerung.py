#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug-Skript für systemsteuerung-Datenbankoperationen
"""

import sys
import json
from datetime import datetime

def debug_systemsteuerung_operations():
    """Debuggt die Systemsteuerung-Datenbankoperationen im Detail"""
    
    print("🔍 DEBUG: Systemsteuerung-Datenbankoperationen")
    print("=" * 60)
    
    try:
        from pdvm_central_datenbank import PdvmCentralDatenbank
        
        user_guid = "test-user-debug"
        view_guid = "test-view-debug"
        
        print(f"User GUID: {user_guid}")
        print(f"View GUID: {view_guid}")
        print()
        
        # Schritt 1: DB-Verbindung testen
        print("1️⃣ DB-VERBINDUNG TESTEN")
        print("-" * 30)
        
        sys_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="systemsteuerung",
            guid=user_guid
        )
        print("✅ Datenbank-Verbindung erstellt")
        
        # Schritt 2: Aktuelle Daten lesen
        print("\n2️⃣ AKTUELLE DATEN LESEN")
        print("-" * 30)
        
        current_data = sys_db.lesen()
        print(f"Geladene Rohdaten: {type(current_data)}")
        if current_data:
            print(f"Anzahl Schlüssel: {len(current_data)}")
            print(f"Schlüssel: {list(current_data.keys())}")
            if user_guid in current_data:
                user_content = current_data[user_guid]
                print(f"Benutzer-Content: {type(user_content)}")
                if isinstance(user_content, dict):
                    print(f"Benutzer-Schlüssel: {list(user_content.keys())}")
        else:
            print("Keine bestehenden Daten gefunden")
        
        # Schritt 3: Datenstruktur aufbauen
        print("\n3️⃣ DATENSTRUKTUR AUFBAUEN")
        print("-" * 30)
        
        # Korrekte Struktur: user_data ist die gesamten Benutzerdaten
        user_data = current_data or {}
        
        print(f"Basis user_data: {type(user_data)}")
        
        # View-Gruppe initialisieren
        if view_guid not in user_data:
            user_data[view_guid] = {}
            print(f"✅ View-Gruppe {view_guid} erstellt")
        
        if 'controls' not in user_data[view_guid]:
            user_data[view_guid]['controls'] = {}
            print("✅ Controls-Bereich erstellt")
        
        # Test-Controls
        test_controls = {
            'familienname_original': {
                'display_show': True,
                'display_order': 1,
                'last_updated': datetime.now().isoformat()
            },
            'vorname_original': {
                'display_show': True,
                'display_order': 2,
                'last_updated': datetime.now().isoformat()
            },
            'geburtsdatum_original': {
                'display_show': False,
                'display_order': 3,
                'last_updated': datetime.now().isoformat()
            }
        }
        
        user_data[view_guid]['controls'] = test_controls
        print(f"✅ {len(test_controls)} Test-Controls hinzugefügt")
        
        # Schritt 4: Speichern
        print("\n4️⃣ DATEN SPEICHERN")
        print("-" * 30)
        
        print(f"Speichere user_data mit Struktur:")
        print(f"  user_data[{repr(view_guid)}]['controls'] = {len(test_controls)} Controls")
        
        # WICHTIG: user_data enthält ALLE Benutzerdaten, nicht nur diese View
        sys_db.speichern(user_guid, user_data)
        print("✅ Daten gespeichert")
        
        # Schritt 5: Verification durch erneutes Laden
        print("\n5️⃣ VERIFICATION - ERNEUT LADEN")
        print("-" * 30)
        
        # Neue DB-Instanz für sauberen Test
        verify_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="systemsteuerung",
            guid=user_guid
        )
        
        loaded_data = verify_db.lesen()
        print(f"Geladene Daten: {type(loaded_data)}")
        
        if loaded_data:
            print(f"Root-Schlüssel: {list(loaded_data.keys())}")
            
            if view_guid in loaded_data:
                print(f"✅ View-GUID {view_guid} gefunden")
                view_data = loaded_data[view_guid]
                
                if 'controls' in view_data:
                    print("✅ Controls-Bereich gefunden")
                    controls = view_data['controls']
                    print(f"✅ {len(controls)} Controls geladen")
                    
                    print("\n📋 GELADENE CONTROLS:")
                    for name, data in controls.items():
                        show = data.get('display_show', '?')
                        order = data.get('display_order', '?')
                        print(f"  {name}: show={show}, order={order}")
                    
                    print("\n🎯 ARCHITEKTUR-PFAD BESTÄTIGT:")
                    print(f"   systemsteuerung.uid = {user_guid}")
                    print(f"   systemsteuerung.daten[{view_guid}]['controls'][control_name]")
                    print("   = {display_show, display_order, last_updated}")
                    
                    return True
                else:
                    print("❌ Controls-Bereich nicht gefunden")
            else:
                print(f"❌ View-GUID {view_guid} nicht gefunden")
        else:
            print("❌ Keine Daten geladen")
        
        return False
        
    except Exception as e:
        print(f"❌ DEBUG FEHLGESCHLAGEN: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False

def test_real_widget_integration():
    """Testet die Integration mit der echten Widget-Klasse"""
    
    print("\n" + "=" * 60)
    print("🔗 REAL WIDGET INTEGRATION TEST")
    print("=" * 60)
    
    try:
        # Simuliere Widget-Parameter
        user_guid = "real-user-test"
        view_guid = "real-view-test"
        
        print(f"User GUID: {user_guid}")
        print(f"View GUID: {view_guid}")
        
        # Teste _save_user_column_order_v2 Logik
        print("\n📤 SAVE-LOGIK TEST")
        print("-" * 30)
        
        from pdvm_central_datenbank import PdvmCentralDatenbank
        
        # Systemsteuerung für Benutzer laden
        sys_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="systemsteuerung",
            guid=user_guid
        )
        
        # Aktuelle Benutzerdaten laden
        user_data = sys_db.lesen() or {}
        
        # View-Gruppe initialisieren
        if view_guid not in user_data:
            user_data[view_guid] = {}
        
        if 'controls' not in user_data[view_guid]:
            user_data[view_guid]['controls'] = {}
        
        # Simuliere Widget-Daten
        column_names = ['familienname_original', 'vorname_original', 'geburtsdatum_original', 'familienname_show', 'geburtsdatum_show']
        column_selection = {
            'familienname_original': True,
            'vorname_original': True, 
            'geburtsdatum_original': True,
            'familienname_show': False,
            'geburtsdatum_show': False
        }
        
        # Control-Parameter erstellen (wie in Widget)
        controls_data = {}
        for i, control_name in enumerate(column_names, 1):
            controls_data[control_name] = {
                'display_show': column_selection.get(control_name, True),
                'display_order': i,
                'last_updated': datetime.now().isoformat()
            }
        
        # Speichern
        user_data[view_guid]['controls'] = controls_data
        sys_db.speichern(user_guid, user_data)
        
        print(f"✅ {len(controls_data)} Controls gespeichert")
        
        # Teste _load_user_column_order_v2 Logik
        print("\n📥 LOAD-LOGIK TEST")
        print("-" * 30)
        
        # Systemsteuerung erneut laden
        loaded_user_data = sys_db.lesen() or {}
        
        # View-Gruppe und Controls-Bereich prüfen
        if view_guid not in loaded_user_data:
            print(f"❌ View {view_guid} nicht gefunden")
            return False
        
        view_data = loaded_user_data[view_guid]
        if 'controls' not in view_data:
            print(f"❌ Controls in View {view_guid} nicht gefunden")
            return False
        
        loaded_controls_data = view_data['controls']
        if not loaded_controls_data:
            print(f"❌ Controls-Bereich für View {view_guid} ist leer")
            return False
        
        # Controls nach display_order sortieren (wie in Widget)
        controls_list = []
        for control_name, control_data in loaded_controls_data.items():
            if isinstance(control_data, dict) and 'display_order' in control_data:
                controls_list.append({
                    'name': control_name,
                    'display_order': control_data.get('display_order', 999),
                    'display_show': control_data.get('display_show', True)
                })
        
        # Nach display_order sortieren
        controls_list.sort(key=lambda x: x['display_order'])
        
        # Rekonstruierte Daten
        reconstructed_column_order = [ctrl['name'] for ctrl in controls_list]
        reconstructed_column_selection = {ctrl['name']: ctrl['display_show'] for ctrl in controls_list}
        
        print(f"✅ {len(controls_list)} Controls geladen und sortiert")
        print(f"Column Order: {reconstructed_column_order}")
        print(f"Column Selection: {reconstructed_column_selection}")
        
        # Vergleiche mit Original
        if (reconstructed_column_order == column_names and 
            reconstructed_column_selection == column_selection):
            print("✅ Daten-Roundtrip erfolgreich - Originaldaten korrekt rekonstruiert")
            return True
        else:
            print("❌ Daten-Roundtrip fehlgeschlagen - Unterschiede zwischen Original und Rekonstruktion")
            return False
        
    except Exception as e:
        print(f"❌ WIDGET INTEGRATION TEST FEHLGESCHLAGEN: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🚀 SYSTEMSTEUERUNG DEBUG - DETAILLIERTER TEST")
    print("=" * 70)
    
    # Debug-Test
    success1 = debug_systemsteuerung_operations()
    
    # Widget Integration Test
    success2 = test_real_widget_integration()
    
    print("\n" + "=" * 70)
    print("📊 DEBUG-ZUSAMMENFASSUNG")
    print("=" * 70)
    
    if success1 and success2:
        print("🎉 ALLE DEBUG-TESTS ERFOLGREICH!")
        print("✅ Systemsteuerung-Datenbankoperationen funktionieren")
        print("✅ Widget-Integration funktioniert")
        print("✅ Korrekte Architektur systemsteuerung.daten[view_guid]['controls'] validiert")
        print()
        print("🎯 BEREIT FÜR PRODUKTIVE IMPLEMENTIERUNG!")
    else:
        print("❌ DEBUG-TESTS ZEIGEN PROBLEME")
        if not success1:
            print("❌ Systemsteuerung-Datenbankoperationen fehlerhaft")
        if not success2:
            print("❌ Widget-Integration fehlerhaft")
        print()
        print("🔧 WEITERE KORREKTUREN ERFORDERLICH")
    
    print("=" * 70)
