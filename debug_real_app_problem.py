#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEBUG: Prüfe das spezifische Problem in der echten Anwendung
"""

def debug_real_app_problem():
    """
    Prüft das spezifische Problem mit der Display_View_Control_Struktur
    """
    print("🔍 DEBUG: Echte Anwendung Problem-Diagnose")
    print("=" * 50)
    
    # Füge das hier in deine echte Anwendung ein, wo du das Problem siehst:
    print("1. Welche view_guid suchst du?")
    print("   → Bitte die echte view_guid aus deiner Anwendung hier eingeben")
    
    print("\n2. Welche user_guid verwendest du?")
    print("   → Bitte die echte user_guid aus deiner Anwendung hier eingeben")
    
    print("\n3. Debug-Code für deine echte Anwendung:")
    print("   Füge das hier ein, wo du das Problem siehst:")
    
    debug_code = '''
# DEBUG: In deiner echten Anwendung einsetzen
from debug_systemsteuerung_view import debug_systemsteuerung_view_data

# Deine echten GUIDs hier einsetzen:
real_view_guid = "DEINE_ECHTE_VIEW_GUID_HIER"  
real_user_guid = "DEINE_ECHTE_USER_GUID_HIER"

# Deine echte Systemsteuerung-Instanz hier verwenden:
real_systemsteuerung = DEINE_ECHTE_SYSTEMSTEUERUNG_INSTANZ

# Debug durchführen:
debug_systemsteuerung_view_data(real_systemsteuerung, real_view_guid, real_user_guid)

# Direkter Test:
control_data = real_systemsteuerung.get_value(
    gruppe=real_view_guid,  # ← Das ist der Schlüssel!
    feld="display_view_control",
    ab_zeit=None
)

if control_data and control_data.get("wert"):
    print(f"✅ GEFUNDEN unter gruppe={real_view_guid}")
else:
    print(f"❌ NICHT GEFUNDEN unter gruppe={real_view_guid}")
    print(f"Verfügbare Gruppen in Systemsteuerung:")
    # Zeige alle verfügbaren Gruppen
    if hasattr(real_systemsteuerung, 'data') and real_systemsteuerung.data:
        for gruppe in real_systemsteuerung.data.keys():
            print(f"  - {gruppe}")
'''
    
    print(debug_code)
    
    print("\n4. Führe diesen Debug-Code in deiner echten Anwendung aus")
    print("   und teile mir das Ergebnis mit!")

if __name__ == "__main__":
    debug_real_app_problem()
