"""
Debug-Script: GCS Mode prüfen
===============================
Prüft den 'mode' Wert in GCS
"""

import sys
sys.path.insert(0, '.')

def check_gcs_mode():
    """Prüft mode Wert in GCS"""
    print("=" * 70)
    print("🔍 GCS MODE DEBUG")
    print("=" * 70)
    
    # 1. GCS holen
    from v2_central_systemsteuerung import get_gcs
    gcs = get_gcs()
    
    if not gcs:
        print("❌ GCS nicht initialisiert!")
        print("   → Führe erst v2_main.py aus und logge dich ein")
        return
    
    print("✅ GCS verfügbar")
    print()
    
    # 2. User-GUID prüfen
    print(f"📋 User-GUID: {gcs.user_guid}")
    print()
    
    # 3. Mode über field_value()
    mode_via_field_value = gcs.field_value('mode')
    print(f"🔍 mode via field_value(): '{mode_via_field_value}'")
    print(f"   Type: {type(mode_via_field_value)}")
    print(f"   == 'admin': {mode_via_field_value == 'admin'}")
    print()
    
    # 4. Mode über Property
    mode_via_property = gcs.mode
    print(f"🔍 mode via property: '{mode_via_property}'")
    print(f"   Type: {type(mode_via_property)}")
    print(f"   == 'admin': {mode_via_property == 'admin'}")
    print()
    
    # 5. Expert Mode
    expert_mode = gcs.expert_mode
    print(f"👨‍💼 expert_mode: {expert_mode}")
    print(f"   Type: {type(expert_mode)}")
    print()
    
    # 6. User-Data komplett
    print("📦 Komplette User-Data:")
    if hasattr(gcs, '_user_data'):
        for key, value in gcs._user_data.items():
            print(f"   {key}: {value} (Type: {type(value)})")
    else:
        print("   ⚠️ _user_data nicht verfügbar")
    
    print()
    print("=" * 70)
    print("✅ Debug abgeschlossen")
    print("=" * 70)

if __name__ == '__main__':
    check_gcs_mode()
