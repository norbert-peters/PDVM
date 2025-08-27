#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Beispiel für die Nutzung des zentralen Stichtag-Managers
"""

from pdvm_central_stichtag_manager import PdvmCentralStichtagManager
from pdvm_central_datenbank import PdvmCentralDatenbank

def demo_zentral_stichtag_manager():
    """Demonstriert die Verwendung des zentralen Stichtag-Managers"""
    
    print("🎯 Demo: Zentraler Stichtag-Manager")
    print("=" * 50)
    
    # 1. Zentrale Systemsteuerung einrichten (simuliert)
    print("\n1️⃣ Systemsteuerung initialisieren...")
    central_systemsteuerung = PdvmCentralDatenbank(
        db_name="PdvmManager.db",
        table_name="systemsteuerung",
        guid="test-user-guid"
    )
    
    # 2. Zentralen Stichtag-Manager erstellen
    print("\n2️⃣ Zentralen Stichtag-Manager erstellen...")
    stichtag_manager = PdvmCentralStichtagManager(
        central_systemsteuerung=central_systemsteuerung,
        user_guid="test-user-guid",
        initial_stichtag="2025216"
    )
    
    # 3. Aktueller Stichtag
    print(f"\n3️⃣ Aktueller Stichtag:")
    print(f"   Float: {stichtag_manager.get_stichtag_float()}")
    print(f"   String: {stichtag_manager.get_stichtag_string()}")
    print(f"   PdvmFormat: {stichtag_manager.get_stichtag_string_pdvm_format()}")
    print(f"   Formatiert: {stichtag_manager.get_formatted_stichtag()}")
    
    # 4. Stichtag ändern (ohne Zeit)
    print(f"\n4️⃣ Stichtag ändern (ohne Zeit)...")
    stichtag_manager.set_stichtag("2025300")
    print(f"   Neuer Stichtag: {stichtag_manager.get_formatted_stichtag()}")
    print(f"   PdvmFormat: {stichtag_manager.get_stichtag_string_pdvm_format()}")  # Sollte .00000 haben
    
    # 5. Stichtag mit Zeit setzen
    print(f"\n5️⃣ Stichtag mit Zeit setzen...")
    stichtag_manager.set_stichtag_with_time(day=15, month=12, year=2025, hour=14, minute=30, second=45)
    print(f"   Stichtag mit Zeit: {stichtag_manager.get_formatted_stichtag()}")
    print(f"   Float: {stichtag_manager.get_stichtag_float()}")
    print(f"   PdvmFormat: {stichtag_manager.get_stichtag_string_pdvm_format()}")  # Sollte Nachkommastellen haben
    time_components = stichtag_manager.get_time_components()
    print(f"   Zeit: {time_components['hour']:02d}:{time_components['minute']:02d}:{time_components['second']:02d}")
    
    # 6. PdvmDateTime-Instanz holen
    print(f"\n6️⃣ Direkte PdvmDateTime-Instanz:")
    pdvm_dt = stichtag_manager.get_pdvm_datetime()
    print(f"   Jahr: {pdvm_dt.Year}")
    print(f"   Monat: {pdvm_dt.Month}")  
    print(f"   Tag: {pdvm_dt.Day}")
    print(f"   Stunde: {pdvm_dt.Hour}")
    print(f"   Minute: {pdvm_dt.Minute}")
    print(f"   Sekunde: {pdvm_dt.Second}")
    
    # 7. Info-Dictionary
    print(f"\n7️⃣ Debug-Informationen:")
    info = stichtag_manager.get_info_dict()
    for key, value in info.items():
        print(f"   {key}: {value}")
    
    print(f"\n✅ Demo abgeschlossen!")
    
    # 8. Beispiel für DatetimePicker-Integration (würde so aussehen):
    print(f"\n8️⃣ Beispiel DatetimePicker-Integration:")
    print("   # In der MainApp:")
    print("   datetime_picker = PdvmDatetimePicker()")
    print("   self.connect_datetime_picker_to_central_stichtag(datetime_picker)")
    print("   # Picker arbeitet jetzt direkt auf zentraler Stichtag-Instanz!")
    print("   # Automatische Synchronisation mit korrektem PdvmFormat!")

if __name__ == "__main__":
    demo_zentral_stichtag_manager()
