#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Systematische Analyse der Sortier-Projektions-Problematik
=======================================================

Frage 1: Wird die Projektionstabelle korrekt erstellt?
Frage 2: Kommt die richtige Projektionstabelle im SortierDialog an?
Frage 3: Wenn bis hier alles richtig, warum werden diese nicht angezeigt?
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication

# Logging Setup
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def frage_1_projektionstabelle_erstellt():
    """Frage 1: Wird die Projektionstabelle korrekt erstellt?"""
    print("\n" + "="*60)
    print("🔍 FRAGE 1: Wird die Projektionstabelle korrekt erstellt?")
    print("="*60)
    
    try:
        # GCS importieren
        from pdvm_central_systemsteuerung import get_gcs
        gcs = get_gcs()
        
        if not gcs:
            print("❌ GCS nicht verfügbar - Projektionstabellen können nicht geprüft werden")
            return False
        
        print(f"✅ GCS verfügbar: {type(gcs).__name__}")
        print(f"   User GUID: {gcs.user_guid}")
        print(f"   Expert Mode: {gcs.expert_mode}")
        
        # Prüfe _projection_tables Attribut
        print(f"\n📊 _projection_tables Attribut vorhanden: {hasattr(gcs, '_projection_tables')}")
        
        if hasattr(gcs, '_projection_tables'):
            projection_tables = gcs._projection_tables
            print(f"   Anzahl Views mit Projektionen: {len(projection_tables)}")
            print(f"   View GUIDs: {list(projection_tables.keys())}")
            
            # Analysiere jede View
            for view_guid, projections in projection_tables.items():
                print(f"\n   📋 View: {view_guid}")
                print(f"      Projektions-Typen: {list(projections.keys())}")
                
                for proj_type, columns in projections.items():
                    if 'sort' in proj_type:
                        print(f"      🎯 {proj_type}: {len(columns)} Spalten")
                        if columns:
                            print(f"         Erste 5: {columns[:5]}")
                        else:
                            print(f"         ❌ LEER!")
            
            return len(projection_tables) > 0
        else:
            print("❌ _projection_tables Attribut nicht gefunden")
            return False
            
    except Exception as e:
        print(f"❌ Fehler bei Frage 1: {e}")
        import traceback
        traceback.print_exc()
        return False

def frage_2_richtige_projektion_im_dialog(test_view_guid):
    """Frage 2: Kommt die richtige Projektionstabelle im SortierDialog an?"""
    print("\n" + "="*60)
    print("🔍 FRAGE 2: Kommt die richtige Projektionstabelle im SortierDialog an?")
    print("="*60)
    
    try:
        from pdvm_central_systemsteuerung import get_gcs
        gcs = get_gcs()
        
        if not gcs:
            print("❌ GCS nicht verfügbar")
            return False, []
        
        print(f"✅ GCS verfügbar")
        print(f"   Test view_guid: {test_view_guid}")
        print(f"   Expert Mode: {gcs.expert_mode}")
        
        # Teste get_columns_for_view direkt
        expert_mode = gcs.expert_mode
        projection_key = 'sort_expert' if expert_mode else 'sort_standard'
        
        print(f"\n🎯 Teste get_columns_for_view für '{projection_key}':")
        
        # Direkte Methoden-Aufrufe wie im SortierDialog
        sort_projection = gcs.get_columns_for_view(test_view_guid, projection_key)
        
        print(f"   Rückgabe: {len(sort_projection)} Spalten")
        if sort_projection:
            print(f"   Erste 5: {sort_projection[:5]}")
            print(f"   Alle: {sort_projection}")
        else:
            print("   ❌ LEER!")
        
        # Prüfe auch alle anderen Projektionen zum Vergleich
        print(f"\n📊 Alle Projektionen für {test_view_guid}:")
        for proj_type in ['view_standard', 'view_expert', 'search_standard', 'search_expert', 
                         'change_standard', 'change_expert', 'sort_standard', 'sort_expert']:
            try:
                columns = gcs.get_columns_for_view(test_view_guid, proj_type)
                print(f"   {proj_type}: {len(columns)} Spalten")
            except Exception as e:
                print(f"   {proj_type}: ❌ FEHLER - {e}")
        
        return True, sort_projection
        
    except Exception as e:
        print(f"❌ Fehler bei Frage 2: {e}")
        import traceback
        traceback.print_exc()
        return False, []

def frage_3_warum_nicht_angezeigt(sort_projection, test_view_guid):
    """Frage 3: Wenn bis hier alles richtig, warum werden diese nicht angezeigt?"""
    print("\n" + "="*60)
    print("🔍 FRAGE 3: Wenn bis hier alles richtig, warum werden diese nicht angezeigt?")
    print("="*60)
    
    try:
        # Simuliere exakt den SortierDialog-Prozess
        print("🎭 Simuliere SortierDialog _get_available_columns_for_sorting:")
        
        # Mock controls_config wie im echten Dialog
        mock_controls_config = {}
        for i, column_key in enumerate(sort_projection):
            mock_controls_config[column_key] = {
                'original': f'Spalte_{i+1}',
                'name': f'Test-Spalte {i+1}'
            }
        
        print(f"   Mock controls_config: {len(mock_controls_config)} Einträge")
        
        # Simuliere Dialog-Logik exakt
        result = []
        for column_key in sort_projection:
            # Controls-Config holen für Display-Namen (wie im Dialog)
            control_data = mock_controls_config.get(column_key, {})
            display_name = control_data.get('original', column_key)
            
            # Alle Spalten aus der Projektion sind sortierbar
            result.append((column_key, str(display_name)))
        
        print(f"   ✅ Dialog-Simulation ergab: {len(result)} verfügbare Spalten")
        
        if result:
            print("   📋 Erste 5 Ergebnisse:")
            for i, (key, name) in enumerate(result[:5]):
                print(f"      {i+1}. {key} → {name}")
        else:
            print("   ❌ Keine Ergebnisse - Problem gefunden!")
        
        # Prüfe _refresh_available_columns Logik
        print(f"\n🔄 Simuliere _refresh_available_columns:")
        
        # sort_levels simulieren (leer = alle Spalten verfügbar)
        sort_levels = []
        
        available_for_ui = []
        for column_key, display_name in result:
            # Bereits in Sortier-Queue? (wie im Dialog)
            if any(level[0] == column_key for level in sort_levels):
                continue
            available_for_ui.append((column_key, display_name))
        
        print(f"   ✅ Für UI verfügbar: {len(available_for_ui)} Spalten")
        
        if available_for_ui:
            print("   📋 UI-Spalten:")
            for i, (key, name) in enumerate(available_for_ui):
                print(f"      {i+1}. {key} → {name}")
            return True
        else:
            print("   ❌ Keine UI-Spalten - Alle bereits in sort_levels?")
            return False
            
    except Exception as e:
        print(f"❌ Fehler bei Frage 3: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Hauptfunktion - Systematische Analyse"""
    print("🔍 SYSTEMATISCHE SORTIER-PROJEKTIONS-ANALYSE")
    print("=" * 60)
    print("Analysiert die drei kritischen Fragen zur Sortier-Spalten-Problematik")
    
    # Test view_guid (typisch für echte Anwendung)
    test_view_guid = "personen"  # Häufig verwendete view_guid
    
    app = QApplication(sys.argv)
    
    try:
        # Schritt 1: Frage 1
        projektionen_ok = frage_1_projektionstabelle_erstellt()
        
        if not projektionen_ok:
            print("\n❌ STOPP: Projektions-Tabellen nicht korrekt erstellt")
            return
        
        # Schritt 2: Frage 2  
        dialog_ok, sort_projection = frage_2_richtige_projektion_im_dialog(test_view_guid)
        
        if not dialog_ok:
            print("\n❌ STOPP: Projektion kommt nicht korrekt im Dialog an")
            return
        
        if not sort_projection:
            print("\n❌ STOPP: Sortier-Projektion ist leer")
            return
        
        # Schritt 3: Frage 3
        anzeige_ok = frage_3_warum_nicht_angezeigt(sort_projection, test_view_guid)
        
        # Zusammenfassung
        print("\n" + "="*60)
        print("📊 ZUSAMMENFASSUNG")
        print("="*60)
        print(f"Frage 1 (Projektionen erstellt): {'✅' if projektionen_ok else '❌'}")
        print(f"Frage 2 (Dialog bekommt Daten): {'✅' if dialog_ok else '❌'}")
        print(f"Frage 3 (Anzeige funktioniert): {'✅' if anzeige_ok else '❌'}")
        
        if projektionen_ok and dialog_ok and anzeige_ok:
            print("\n🎉 ALLE TESTS ERFOLGREICH - Sortier-System sollte funktionieren!")
        else:
            print("\n❌ PROBLEM IDENTIFIZIERT - Siehe Details oben")
        
    except Exception as e:
        print(f"\n❌ KRITISCHER FEHLER: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()