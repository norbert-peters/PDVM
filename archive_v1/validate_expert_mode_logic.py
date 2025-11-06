#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validiert die Expert-Mode Logik für change_spalten Projektion
"""

def simulate_control_processing():
    """Simuliert die Control-Verarbeitung aus der realen Implementierung"""
    
    # Beispiel Controls - basierend auf realer Datenbankstruktur
    test_controls = {
        'id': {'expert_mode': False, 'show': True, 'type': 'number'},
        'datum': {'expert_mode': False, 'show': True, 'type': 'date'},
        'uhrzeit': {'expert_mode': False, 'show': True, 'type': 'time'},
        'kassenname': {'expert_mode': False, 'show': True, 'type': 'text'},
        'bonnummer': {'expert_mode': False, 'show': False, 'type': 'number'},  # versteckt
        'debug_info': {'expert_mode': True, 'show': False, 'type': 'text'},   # expert mode
        'internal_ref': {'expert_mode': True, 'show': False, 'type': 'text'}, # expert mode
        'dummy_spacer': {'type': 'dummy'},  # dummy column
        'betrag': {'expert_mode': False, 'show': True, 'type': 'currency'},
        'admin_flag': {'expert_mode': True, 'show': True, 'type': 'boolean'}   # expert mode, aber sichtbar
    }
    
    print("🧪 EXPERT-MODE LOGIK VALIDIERUNG")
    print("=" * 50)
    
    # Analysiere Controls wie in der realen Implementierung
    print("\n📊 Control-Analyse:")
    
    dummy_controls = []
    visible_controls = []
    hidden_controls = []
    expert_controls = []
    non_expert_controls = []
    
    for control_key, control_data in test_controls.items():
        control_type = control_data.get('type', '')
        is_dummy = (control_type == 'dummy' or 
                   control_data.get('dummy', False) or 
                   control_key.lower().startswith('dummy'))
        
        if is_dummy:
            dummy_controls.append(control_key)
        else:
            # Expert Mode Flag prüfen (wie in der realen Implementierung)
            if control_data.get('expert_mode', False):
                expert_controls.append(control_key)
            else:
                non_expert_controls.append(control_key)
            
            # Show Flag prüfen
            if control_data.get('show', False):
                visible_controls.append(control_key)
            else:
                hidden_controls.append(control_key)
    
    print(f"  • Dummy Controls: {len(dummy_controls)} → {dummy_controls}")
    print(f"  • Sichtbare Controls: {len(visible_controls)} → {visible_controls}")
    print(f"  • Versteckte Controls: {len(hidden_controls)} → {hidden_controls}")
    print(f"  • Expert-Mode Controls: {len(expert_controls)} → {expert_controls}")
    print(f"  • Non-Expert Controls: {len(non_expert_controls)} → {non_expert_controls}")
    
    # Simuliere die 6 Projektions-Tabellen
    print(f"\n🏗️  Simuliere STATISCHE Projektions-Tabellen:")
    
    projections = {}
    
    # table_standard: nur sichtbare, nicht-dummy Controls
    projections['table_standard'] = [ctrl for ctrl in visible_controls if ctrl not in dummy_controls]
    
    # table_expert: alle nicht-dummy Controls
    all_non_dummy = [ctrl for ctrl in test_controls.keys() if ctrl not in dummy_controls]
    projections['table_expert'] = all_non_dummy
    
    # search_standard: wie table_standard
    projections['search_standard'] = projections['table_standard'].copy()
    
    # search_expert: wie table_expert
    projections['search_expert'] = projections['table_expert'].copy()
    
    # change_spalten: NUR non-expert Controls (KORRIGIERTE LOGIK!)
    projections['change_spalten'] = non_expert_controls.copy()
    
    # admin: alle nicht-dummy Controls
    projections['admin'] = all_non_dummy.copy()
    
    # Ergebnisse anzeigen
    for proj_name, proj_controls in projections.items():
        print(f"  ✓ {proj_name}: {len(proj_controls)} Spalten → {proj_controls}")
    
    print(f"\n🔍 VALIDIERUNG - change_spalten Korrektheit:")
    
    # Prüfe ob change_spalten nur non-expert Controls enthält
    expert_in_change_spalten = []
    for control in projections['change_spalten']:
        if test_controls[control].get('expert_mode', False):
            expert_in_change_spalten.append(control)
    
    if len(expert_in_change_spalten) == 0:
        print(f"  ✅ KORREKT: change_spalten enthält KEINE Expert-Mode Controls")
        print(f"  ✅ change_spalten = {len(projections['change_spalten'])} Non-Expert Controls")
    else:
        print(f"  ❌ FEHLER: change_spalten enthält {len(expert_in_change_spalten)} Expert Controls:")
        for expert_ctrl in expert_in_change_spalten:
            print(f"    → {expert_ctrl} (expert_mode = True)")
    
    # Zusätzliche Validierungen
    print(f"\n📋 Weitere Validierungen:")
    
    # Standard ≤ Expert
    if len(projections['table_standard']) <= len(projections['table_expert']):
        print(f"  ✅ table_standard ({len(projections['table_standard'])}) ≤ table_expert ({len(projections['table_expert'])})")
    else:
        print(f"  ❌ table_standard ({len(projections['table_standard'])}) > table_expert ({len(projections['table_expert'])}) - FEHLER!")
    
    # change_spalten sollte weniger oder gleich als alle non-dummy haben
    if len(projections['change_spalten']) <= len(projections['admin']):
        print(f"  ✅ change_spalten ({len(projections['change_spalten'])}) ≤ admin ({len(projections['admin'])})")
    else:
        print(f"  ❌ change_spalten ({len(projections['change_spalten'])}) > admin ({len(projections['admin'])}) - FEHLER!")
    
    return projections

if __name__ == "__main__":
    simulate_control_processing()
    print(f"\n✅ Expert-Mode Logik Validierung abgeschlossen!")