# -*- coding: utf-8 -*-
"""Prüft ob name_original und name_show in GCS gespeichert sind"""

from pdvm_central_systemsteuerung import get_gcs

try:
    gcs = get_gcs()
    if not gcs:
        print("❌ GCS nicht initialisiert - App muss laufen")
        exit(1)
    
    # Prüfe eine bekannte View (z.B. Personen-View)
    view_guids = ['personenview', 'personenstamm', 'persons']
    
    for view_guid in view_guids:
        print(f"\n{'='*60}")
        print(f"🔍 Prüfe View: {view_guid}")
        print(f"{'='*60}")
        
        controls, _ = gcs.db.get_value(view_guid, "ColumnControls")
        
        if not controls:
            print(f"⚠️ Keine Controls für {view_guid}")
            continue
        
        print(f"📋 Insgesamt {len(controls)} Controls")
        
        # Prüfe name_original und name_show
        has_name_original = 'name_original' in controls
        has_name_show = 'name_show' in controls
        
        print(f"\n✅ name_original vorhanden: {has_name_original}")
        print(f"✅ name_show vorhanden: {has_name_show}")
        
        if has_name_original:
            print(f"\n📄 name_original Config:")
            for key, value in controls['name_original'].items():
                print(f"  {key}: {value}")
        
        if has_name_show:
            print(f"\n📄 name_show Config:")
            for key, value in controls['name_show'].items():
                print(f"  {key}: {value}")
        
        # Zeige alle Spalten-Namen
        print(f"\n📋 Alle Spalten:")
        for name in sorted(controls.keys()):
            if 'name' in name.lower():
                print(f"  ✓ {name}")
        
        break  # Nur erste gefundene View prüfen

except Exception as e:
    print(f"\n❌ Fehler: {e}")
    import traceback
    traceback.print_exc()
