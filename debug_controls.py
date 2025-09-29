#!/usr/bin/env python3
"""Debug-Skript für Controls-Analyse"""

# Einfache Initialisierung von GCS
import sys, os

# Setze den Pfad falls notwendig
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import von GCS
try:
    # Lade GCS Konfiguration direkt
    from pdvm_central_systemsteuerung import PdvmCentralSystemsteuerung
    from pdvm_central_datenbank import PdvmCentralDatenbank
    
    # Initialisiere GCS direkt
    central_db = PdvmCentralDatenbank(db_path="datenbank.db")
    gcs = PdvmCentralSystemsteuerung(central_db)
    gcs.expert_mode = True  # Expert Mode für Test
    
    print("✅ GCS erfolgreich initialisiert")
    
except Exception as e:
    print(f"❌ Fehler bei GCS-Initialisierung: {e}")
    sys.exit(1)
view_guid = '0d10a0d0-b1a5-4544-b284-e8a09ca979b5'
controls, _ = gcs.db.get_value(view_guid, 'controls')

if controls:
    total_controls = len(controls)
    dummy_controls = sum(1 for k, v in controls.items() if v.get('control_type') == 'dummy')
    non_dummy_controls = total_controls - dummy_controls
    print(f'Total Controls: {total_controls}')
    print(f'Dummy Controls: {dummy_controls}')
    print(f'Non-Dummy Controls: {non_dummy_controls}')
    print()
    print('Controls Arten (erste 15):')
    
    # Erste 15 anzeigen
    for i, (k, v) in enumerate(list(controls.items())[:15]):
        control_type = v.get('control_type', 'unknown')
        expert_order = v.get('expert_order', 'N/A')
        display_order = v.get('display_order', 'N/A')
        visible = v.get('visible', 'N/A')
        print(f'  {i+1:2d}. {k}: type={control_type}, expert_order={expert_order}, display_order={display_order}, visible={visible}')
    
    print()
    print('Test der Spalten-Projektionen:')
    
    # Test verschiedene Projektionen
    print("1. get_projection_column_management:")
    col_mgmt = gcs.get_projection_column_management(view_guid)
    print(f"   Anzahl: {len(col_mgmt)} Spalten")
    if col_mgmt:
        print(f"   Erste 10: {col_mgmt[:10]}")
    
    print("\n2. get_projection_table:")
    table_proj = gcs.get_projection_table(view_guid)
    print(f"   Anzahl: {len(table_proj)} Spalten")
    if table_proj:
        print(f"   Erste 10: {table_proj[:10]}")
        
    print("\n3. get_projection_search:")
    search_proj = gcs.get_projection_search(view_guid)
    print(f"   Anzahl: {len(search_proj)} Spalten")
    if search_proj:
        print(f"   Erste 10: {search_proj[:10]}")
        
    # Expert Mode testen
    print(f"\n4. Expert Mode Status: {gcs.expert_mode}")
    
else:
    print('Keine Controls gefunden')