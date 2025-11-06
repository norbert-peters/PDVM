#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Debug-Skript für Controls Struktur und Projektionen
Analysiert die Controls-Struktur für Expert Mode Probleme
"""

import sys
import os

# Pfad zur Anwendung hinzufügen
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Verwende die globale GCS-Instanz
    from global_gcs import gcs
    
    if gcs is None:
        print("❌ GCS ist nicht initialisiert!")
        print("Dieses Skript muss aus der laufenden Anwendung heraus verwendet werden.")
        sys.exit(1)
    
    print("✅ Globale GCS-Instanz gefunden")
    
except Exception as e:
    print(f"❌ Fehler beim GCS-Import: {e}")
    sys.exit(1)

def debug_controls_projection():
    """Analysiert Controls und Projektionen für Expert Mode"""
    
    # Test mit einer bekannten View GUID
    view_guid = '0d10a0d0-b1a5-4544-b284-e8a09ca979b5'
    
    print(f"\n🔍 Analysiere View: {view_guid}")
    
    # 1. Lade alle Controls
    try:
        controls, _ = gcs.db.get_value(view_guid, 'controls')
        if not controls:
            print("❌ Keine Controls gefunden")
            return
        
        print(f"📊 Gesamt Controls: {len(controls)}")
        
        # Analyse der Controls
        dummy_controls = 0
        visible_controls = 0
        hidden_controls = 0
        
        for control_guid, control_data in controls.items():
            control_type = control_data.get('type', 'unknown')
            
            # Prüfe auf Dummy Controls
            if control_type == 'dummy' or control_data.get('dummy', False):
                dummy_controls += 1
                continue
                
            # Prüfe Sichtbarkeit
            if control_data.get('visible', True):
                visible_controls += 1
            else:
                hidden_controls += 1
        
        print(f"  • Dummy Controls: {dummy_controls}")
        print(f"  • Sichtbare Controls: {visible_controls}")
        print(f"  • Versteckte Controls: {hidden_controls}")
        print(f"  • Nicht-Dummy Controls: {visible_controls + hidden_controls}")
        
    except Exception as e:
        print(f"❌ Fehler beim Laden der Controls: {e}")
        return
    
    # 2. Teste live Projektionen
    print(f"\n🔄 Teste Live-Projektionen:")
    
    try:
        # Test get_projection_column_management
        projection_result = gcs.get_projection_column_management(view_guid)
        if projection_result:
            print(f"✅ get_projection_column_management: {len(projection_result)} Controls")
            
            # Analysiere die Projektion
            for control_guid, control_data in projection_result.items():
                control_type = control_data.get('type', 'unknown')
                print(f"  • {control_guid[:8]}... (Type: {control_type})")
        else:
            print("❌ get_projection_column_management liefert keine Daten")
            
    except Exception as e:
        print(f"❌ Fehler bei get_projection_column_management: {e}")
    
    # 3. Expert Mode Test
    print(f"\n🧪 Expert Mode Test:")
    original_expert_mode = getattr(gcs, 'expert_mode', False)
    
    try:
        # Expert Mode aktivieren
        gcs.expert_mode = True
        print("✅ Expert Mode aktiviert")
        
        # Teste Projektion im Expert Mode
        expert_projection = gcs.get_projection_column_management(view_guid)
        if expert_projection:
            print(f"📊 Expert Mode Projektion: {len(expert_projection)} Controls")
            
            # Vergleiche mit normaler Projektion
            if projection_result:
                if len(expert_projection) != len(projection_result):
                    print(f"⚠️  Unterschied zwischen Normal ({len(projection_result)}) und Expert ({len(expert_projection)})")
                else:
                    print("✅ Expert Mode zeigt gleiche Anzahl Controls")
        else:
            print("❌ Expert Mode Projektion leer")
            
    except Exception as e:
        print(f"❌ Fehler im Expert Mode Test: {e}")
    finally:
        # Expert Mode zurücksetzen
        gcs.expert_mode = original_expert_mode
    
    print(f"\n✅ Analyse abgeschlossen")

if __name__ == "__main__":
    debug_controls_projection()