#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEBUG: Analyse des Problems mit leerer Tabelle beim zweiten Aufruf
"""

def debug_tabelle_leer_problem():
    """
    Analysiert das Problem mit der leeren Tabelle beim zweiten Aufruf
    """
    print("🔍 DEBUG: Problem mit leerer Tabelle beim zweiten Aufruf")
    print("=" * 60)
    
    try:
        from pdvm_central_datenbank import PdvmCentralDatenbank
        from pdvm_view_manager_exakt import PdvmViewManager
        
        # Test-Setup
        user_guid = "test-user-debug"
        view_guid = "test_debug_view_789"
        
        # Zentrale Systemsteuerung
        central_systemsteuerung = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="systemsteuerung",
            guid=user_guid
        )
        
        # Test-View-Config
        test_view_config = {
            "ROOT": {"view_table": "persondaten"},
            "metadata": {
                "persondaten": {
                    "felder": [
                        {"feld": "VORNAME", "name": "Vorname", "type": "string", "gruppe": "DATEN"},
                        {"feld": "NACHNAME", "name": "Nachname", "type": "string", "gruppe": "DATEN"},
                        {"feld": "GEBURTSDATUM", "name": "Geburtsdatum", "type": "date", "gruppe": "DATEN"}
                    ]
                }
            }
        }
        
        print(f"1. ERSTER AUFRUF - Simuliere erste Verwendung")
        print(f"   → Keine Display_View_Control_Struktur in Systemsteuerung vorhanden")
        
        # Prüfe ob bereits Daten vorhanden
        existing_data = central_systemsteuerung.get_value(
            gruppe=view_guid,
            feld="display_view_control",
            ab_zeit=None
        )
        
        if existing_data:
            print(f"   ⚠️ ACHTUNG: Es sind bereits Daten vorhanden! Lösche für Test...")
            # Für Test: Daten löschen
            central_systemsteuerung.delete_value(gruppe=view_guid, feld="display_view_control")
            central_systemsteuerung.save_values()
        
        # Erster ViewManager (wie beim ersten Aufruf)
        view_manager_1 = PdvmViewManager(
            view_guid=view_guid,
            view_config=test_view_config,
            central_systemsteuerung=central_systemsteuerung,
            db_name="PdvmManager.db",
            stichtag=1001.0
        )
        
        # Analysiere erste Erstellung
        sichtbare_spalten_1 = view_manager_1.get_sichtbare_spalten()
        aktuelle_tabelle_1 = view_manager_1.get_aktuelle_tabelle()
        
        print(f"   📊 Erster Aufruf Ergebnisse:")
        print(f"      Sichtbare Spalten: {len(sichtbare_spalten_1)} → {sichtbare_spalten_1}")
        print(f"      Tabellen-Zeilen: {len(aktuelle_tabelle_1)}")
        
        # Prüfe was in Systemsteuerung gespeichert wurde
        saved_data_1 = central_systemsteuerung.get_value(
            gruppe=view_guid,
            feld="display_view_control",
            ab_zeit=None
        )
        
        if saved_data_1 and saved_data_1.get("wert"):
            control_struktur = saved_data_1["wert"]
            if isinstance(control_struktur, dict) and "columns" in control_struktur:
                columns = control_struktur["columns"]
                show_true_count = sum(1 for col in columns if col.get("show", False))
                show_false_count = sum(1 for col in columns if not col.get("show", True))
                
                print(f"   💾 Gespeicherte Struktur nach erstem Aufruf:")
                print(f"      Gesamte Spalten: {len(columns)}")
                print(f"      show=True: {show_true_count}")
                print(f"      show=False: {show_false_count}")
                
                print(f"   📋 Detail-Analyse der Spalten:")
                for i, col in enumerate(columns[:5]):  # Erste 5 Spalten
                    print(f"      {i+1}. {col.get('name', 'unknown')}: show={col.get('show', 'undefined')}, expert={col.get('expert', 'undefined')}")
                if len(columns) > 5:
                    print(f"      ... und {len(columns) - 5} weitere Spalten")
        
        print(f"\n2. ZWEITER AUFRUF - Simuliere Wiederverwendung")
        print(f"   → Display_View_Control_Struktur aus Systemsteuerung laden")
        
        # Zweiter ViewManager (wie beim zweiten Aufruf)
        view_manager_2 = PdvmViewManager(
            view_guid=view_guid,
            view_config=test_view_config,
            central_systemsteuerung=central_systemsteuerung,
            db_name="PdvmManager.db",
            stichtag=1001.0
        )
        
        # Analysiere zweite Verwendung
        sichtbare_spalten_2 = view_manager_2.get_sichtbare_spalten()
        aktuelle_tabelle_2 = view_manager_2.get_aktuelle_tabelle()
        
        print(f"   📊 Zweiter Aufruf Ergebnisse:")
        print(f"      Sichtbare Spalten: {len(sichtbare_spalten_2)} → {sichtbare_spalten_2}")
        print(f"      Tabellen-Zeilen: {len(aktuelle_tabelle_2)}")
        
        print(f"\n3. PROBLEM-ANALYSE:")
        
        if len(sichtbare_spalten_1) > 0 and len(sichtbare_spalten_2) == 0:
            print(f"   🔴 PROBLEM BESTÄTIGT:")
            print(f"      Erster Aufruf: {len(sichtbare_spalten_1)} sichtbare Spalten")
            print(f"      Zweiter Aufruf: {len(sichtbare_spalten_2)} sichtbare Spalten")
            print(f"   ➡️ URSACHE: Gespeicherte Spalten haben alle show=False!")
            
        elif len(aktuelle_tabelle_1) > 0 and len(aktuelle_tabelle_2) == 0:
            print(f"   🔴 PROBLEM BESTÄTIGT:")
            print(f"      Erster Aufruf: {len(aktuelle_tabelle_1)} Tabellenzeilen")
            print(f"      Zweiter Aufruf: {len(aktuelle_tabelle_2)} Tabellenzeilen")
            print(f"   ➡️ URSACHE: Datenfilterung durch fehlende sichtbare Spalten!")
            
        else:
            print(f"   ✅ KEIN PROBLEM erkannt oder Problem liegt wo anders")
            
        print(f"\n4. DETAILIERTE SPALTEN-ANALYSE:")
        
        # Vergleiche die Display_View_Control_Strukturen
        saved_data_2 = central_systemsteuerung.get_value(
            gruppe=view_guid,
            feld="display_view_control", 
            ab_zeit=None
        )
        
        if saved_data_2 and saved_data_2.get("wert"):
            control_struktur_2 = saved_data_2["wert"]
            if isinstance(control_struktur_2, dict) and "columns" in control_struktur_2:
                columns_2 = control_struktur_2["columns"]
                
                print(f"   Spalten-Status im Detail:")
                for col in columns_2:
                    col_name = col.get('name', 'unknown')
                    col_show = col.get('show', 'undefined')
                    col_expert = col.get('expert', 'undefined')
                    col_type = col.get('type', 'undefined')
                    print(f"      - {col_name}: show={col_show}, expert={col_expert}, type={col_type}")
        
        return True
        
    except Exception as e:
        print(f"❌ DEBUG FEHLGESCHLAGEN: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = debug_tabelle_leer_problem()
    
    if success:
        print(f"\n🎯 DEBUG ABGESCHLOSSEN")
        print(f"Falls das Problem bestätigt wurde:")
        print(f"1. Problem liegt in der Spalten-Sichtbarkeit (show=False)")
        print(f"2. get_sichtbare_spalten() filtert korrekt, aber keine Spalten sind sichtbar")
        print(f"3. Lösung: Standard-Sichtbarkeit bei Erstellung korrigieren")
    else:
        print(f"\n⚠️ Problem beim Debug - siehe Details oben")
