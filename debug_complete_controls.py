#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug und Fix für vollständige Controls-System
"""

import sys
import json
from datetime import datetime

def debug_complete_controls_database():
    """Debuggt die Datenbank-Operationen für vollständige Controls"""
    
    print("🔍 DEBUG: Vollständige Controls Datenbank-Operationen")
    print("=" * 60)
    
    try:
        from pdvm_central_datenbank import PdvmCentralDatenbank
        
        user_guid = "debug-complete-user"
        view_guid = "debug-complete-view"
        
        print(f"User GUID: {user_guid}")
        print(f"View GUID: {view_guid}")
        print()
        
        # Schritt 1: DB-Verbindung
        print("1️⃣ DATENBANK-VERBINDUNG")
        print("-" * 30)
        
        sys_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="systemsteuerung",
            guid=user_guid
        )
        print("✅ DB-Verbindung erstellt")
        
        # Schritt 2: Aktuelle Daten prüfen
        print("\n2️⃣ AKTUELLE DATEN PRÜFEN")
        print("-" * 30)
        
        current_data = sys_db.lesen()
        print(f"Geladene Daten: {type(current_data)}")
        
        if current_data:
            print(f"Anzahl Root-Schlüssel: {len(current_data)}")
            print(f"Root-Schlüssel: {list(current_data.keys())}")
            
            if view_guid in current_data:
                view_data = current_data[view_guid]
                print(f"View-Daten vorhanden: {type(view_data)}")
                print(f"View-Schlüssel: {list(view_data.keys()) if isinstance(view_data, dict) else 'Nicht-Dict'}")
        else:
            print("Keine bestehenden Daten")
        
        # Schritt 3: Vollständige Controls erstellen
        print("\n3️⃣ VOLLSTÄNDIGE CONTROLS ERSTELLEN")
        print("-" * 30)
        
        # Einfache Test-Controls
        complete_controls = {
            'test_control_1': {
                'name': 'test_control_1',
                'label': 'Test Control 1',
                'type': 'string',
                'width': 100,
                'show': True,
                'order': 1,
                'user_display_show': True,
                'user_display_order': 1,
                'last_updated': datetime.now().isoformat()
            },
            'test_control_2': {
                'name': 'test_control_2',
                'label': 'Test Control 2', 
                'type': 'string',
                'width': 150,
                'show': True,
                'order': 2,
                'user_display_show': False,
                'user_display_order': 2,
                'last_updated': datetime.now().isoformat()
            }
        }
        
        print(f"✅ {len(complete_controls)} Test-Controls erstellt")
        
        # Schritt 4: Datenstruktur aufbauen
        print("\n4️⃣ DATENSTRUKTUR AUFBAUEN")
        print("-" * 30)
        
        user_data = current_data or {}
        print(f"Basis user_data: {type(user_data)}")
        
        # View-Gruppe
        if view_guid not in user_data:
            user_data[view_guid] = {}
            print(f"✅ View-Gruppe {view_guid} erstellt")
        
        # Complete Controls
        user_data[view_guid]['complete_controls'] = complete_controls
        print("✅ Complete Controls hinzugefügt")
        
        print(f"Finale Struktur:")
        print(f"  user_data[{repr(view_guid)}]['complete_controls'] = {len(complete_controls)} Controls")
        
        # Schritt 5: Speichern
        print("\n5️⃣ SPEICHERN")
        print("-" * 30)
        
        sys_db.speichern(user_guid, user_data)
        print("✅ Daten gespeichert")
        
        # Schritt 6: Neu laden zur Verifikation
        print("\n6️⃣ VERIFICATION")
        print("-" * 30)
        
        # Neue DB-Instanz
        verify_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="systemsteuerung",
            guid=user_guid
        )
        
        loaded_data = verify_db.lesen()
        print(f"Verifikation - Geladene Daten: {type(loaded_data)}")
        
        if loaded_data:
            print(f"Root-Schlüssel: {list(loaded_data.keys())}")
            
            if view_guid in loaded_data:
                print(f"✅ View-GUID {view_guid} gefunden")
                view_data = loaded_data[view_guid]
                
                if isinstance(view_data, dict) and 'complete_controls' in view_data:
                    print("✅ complete_controls gefunden")
                    controls = view_data['complete_controls']
                    
                    if isinstance(controls, dict):
                        print(f"✅ {len(controls)} Controls geladen")
                        
                        print("\n📋 GELADENE COMPLETE CONTROLS:")
                        for name, data in controls.items():
                            show = data.get('user_display_show', '?')
                            order = data.get('user_display_order', '?')
                            label = data.get('label', name)
                            print(f"   {name}: {label} | Show: {show} | Order: {order}")
                        
                        print("\n🎯 VOLLSTÄNDIGE CONTROLS - DATABASE OPERATIONS ERFOLGREICH!")
                        return True
                    else:
                        print(f"❌ Controls sind nicht Dict: {type(controls)}")
                else:
                    print("❌ complete_controls nicht gefunden in View-Daten")
                    if isinstance(view_data, dict):
                        print(f"   View-Schlüssel: {list(view_data.keys())}")
            else:
                print(f"❌ View-GUID {view_guid} nicht gefunden")
        else:
            print("❌ Keine Daten nach Verifikation geladen")
        
        return False
        
    except Exception as e:
        print(f"❌ DEBUG FEHLGESCHLAGEN: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False

def test_simple_complete_controls_workflow():
    """Testet einen einfachen, funktionierenden Workflow für vollständige Controls"""
    
    print("\n" + "=" * 60)
    print("🔧 EINFACHER COMPLETE CONTROLS WORKFLOW")
    print("=" * 60)
    
    try:
        from pdvm_central_datenbank import PdvmCentralDatenbank
        
        user_guid = "simple-workflow-user"
        view_guid = "simple-workflow-view"
        
        print(f"User GUID: {user_guid}")
        print(f"View GUID: {view_guid}")
        
        # Schritt 1: Vollständige Controls Definition
        print("\n1️⃣ VOLLSTÄNDIGE CONTROLS DEFINITION")
        print("-" * 30)
        
        # Simuliert Controls aus get_value_view + Benutzer-Einstellungen
        complete_controls_definition = {
            'familienname_original': {
                # Original aus get_value_view
                'name': 'familienname_original',
                'label': 'Familienname',
                'type': 'string', 
                'width': 150,
                'show': True,
                'order': 1,
                # Benutzer-Überschreibungen
                'user_display_show': True,
                'user_display_order': 1,
                'last_updated': datetime.now().isoformat(),
                'source': 'get_value_view + user_preferences'
            },
            'vorname_original': {
                'name': 'vorname_original',
                'label': 'Vorname',
                'type': 'string',
                'width': 120,
                'show': True,
                'order': 2,
                'user_display_show': True,
                'user_display_order': 2,
                'last_updated': datetime.now().isoformat(),
                'source': 'get_value_view + user_preferences'
            },
            'geburtsdatum_original': {
                'name': 'geburtsdatum_original',
                'label': 'Geburtsdatum',
                'type': 'date',
                'width': 100,
                'show': True,
                'order': 3,
                'user_display_show': False,  # Benutzer hat ausgeblendet
                'user_display_order': 3,
                'last_updated': datetime.now().isoformat(),
                'source': 'get_value_view + user_preferences'
            }
        }
        
        print(f"✅ {len(complete_controls_definition)} vollständige Controls definiert")
        
        # Schritt 2: Speichern
        print("\n2️⃣ COMPLETE CONTROLS SPEICHERN")
        print("-" * 30)
        
        sys_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="systemsteuerung",
            guid=user_guid
        )
        
        user_data = sys_db.lesen() or {}
        
        if view_guid not in user_data:
            user_data[view_guid] = {}
        
        user_data[view_guid]['complete_controls'] = complete_controls_definition
        result = sys_db.speichern(user_guid, user_data)
        
        print(f"✅ Speichern-Ergebnis: {result}")
        
        # Schritt 3: Laden und Tabelle aufbauen
        print("\n3️⃣ LADEN UND TABELLE AUFBAUEN")
        print("-" * 30)
        
        # Neu laden
        loaded_data = sys_db.lesen()
        
        if (loaded_data and 
            view_guid in loaded_data and 
            'complete_controls' in loaded_data[view_guid]):
            
            loaded_controls = loaded_data[view_guid]['complete_controls']
            print(f"✅ {len(loaded_controls)} Controls geladen")
            
            # Tabelle aufbauen (wie im Widget)
            sorted_controls = sorted(
                loaded_controls.items(),
                key=lambda x: x[1].get('user_display_order', 999)
            )
            
            column_order = [item[0] for item in sorted_controls]
            column_selection = {item[0]: item[1].get('user_display_show', True) for item in sorted_controls}
            
            print(f"✅ Tabellen-Parameter generiert:")
            print(f"   column_order: {column_order}")
            print(f"   column_selection: {column_selection}")
            
            # Schritt 4: Drag & Drop Simulation
            print("\n4️⃣ DRAG & DROP SIMULATION")
            print("-" * 30)
            
            # Neue Reihenfolge
            new_order = ['geburtsdatum_original', 'familienname_original', 'vorname_original']
            print(f"Neue Reihenfolge: {new_order}")
            
            # Controls aktualisieren
            for new_pos, control_name in enumerate(new_order, 1):
                if control_name in loaded_controls:
                    loaded_controls[control_name]['user_display_order'] = new_pos
                    loaded_controls[control_name]['last_updated'] = datetime.now().isoformat()
            
            # Zurückspeichern
            user_data[view_guid]['complete_controls'] = loaded_controls
            sys_db.speichern(user_guid, user_data)
            
            print("✅ Drag & Drop Änderungen gespeichert")
            
            # Schritt 5: Finale Verifikation
            print("\n5️⃣ FINALE VERIFIKATION")
            print("-" * 30)
            
            # Erneut laden
            final_data = sys_db.lesen()
            final_controls = final_data[view_guid]['complete_controls']
            
            # Neue Reihenfolge prüfen
            final_sorted = sorted(
                final_controls.items(),
                key=lambda x: x[1].get('user_display_order', 999)
            )
            
            final_order = [item[0] for item in final_sorted]
            
            print(f"Finale Reihenfolge: {final_order}")
            
            if final_order == new_order:
                print("✅ Drag & Drop Persistenz erfolgreich")
                
                print("\n🎉 EINFACHER WORKFLOW ERFOLGREICH!")
                print("✅ Vollständige Controls speichern funktioniert")
                print("✅ Vollständige Controls laden funktioniert")
                print("✅ Tabellen-Aufbau funktioniert")
                print("✅ Drag & Drop Persistenz funktioniert")
                print()
                print("🚀 BEREIT FÜR WIDGET-INTEGRATION!")
                
                return True
            else:
                print(f"❌ Drag & Drop Persistenz fehlgeschlagen")
                return False
        else:
            print("❌ Controls laden fehlgeschlagen")
            return False
        
    except Exception as e:
        print(f"❌ WORKFLOW TEST FEHLGESCHLAGEN: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🔧 VOLLSTÄNDIGE CONTROLS - DEBUG UND FIX")
    print("=" * 70)
    
    # Debug-Test
    success1 = debug_complete_controls_database()
    
    # Workflow-Test
    success2 = test_simple_complete_controls_workflow()
    
    print("\n" + "=" * 70)
    print("📊 DEBUG ZUSAMMENFASSUNG")
    print("=" * 70)
    
    if success1 and success2:
        print("🎉 ALLE DEBUG-TESTS ERFOLGREICH!")
        print()
        print("✅ Datenbank-Operationen für vollständige Controls funktionieren")
        print("✅ Einfacher Workflow funktioniert")
        print("✅ Persistenz-Mechanismus funktioniert")
        print()
        print("🎯 VOLLSTÄNDIGE CONTROLS SYSTEM IST READY!")
        print("📊 Nächster Schritt: Integration in pdvm_modern_view_widget.py")
    else:
        print("❌ DEBUG ZEIGT PROBLEME")
        if not success1:
            print("❌ Datenbank-Operationen fehlerhaft")
        if not success2:
            print("❌ Workflow fehlerhaft")
        print()
        print("🔧 WEITERE FIXES ERFORDERLICH")
    
    print("=" * 70)
