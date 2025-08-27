#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEBUG: String-Spalten Diagnose
=============================

Analysiert, warum String-Spalten leer sind
"""

import sys
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# pdvm_systemstart importieren
import importlib.util
spec = importlib.util.spec_from_file_location('pdvm_systemstart', 'pdvm_systemstart.py')
pdvm_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pdvm_module)

def debug_string_columns():
    """Debuggt String-Spalten Problem"""
    print("🔍 DEBUG: String-Spalten Diagnose")
    print("=" * 50)
    
    try:
        from pdvm_central_datenbank import PdvmCentralDatenbank
        from pdvm_view_daten_manager import PdvmViewDatenManager
        
        # 1. Direkter Test mit persondaten-DB
        print("\n1️⃣ DIREKTE DB-TESTS:")
        
        # Ersten Personendatensatz laden
        person_db = PdvmCentralDatenbank(db_name="PdvmManager.db", table_name="persondaten", guid=None)
        all_records = person_db.lesen_alle_ohne_system(limit=3)
        
        for i, record in enumerate(all_records):
            guid = record["uid"]
            print(f"\n   📋 Person {i+1}: {guid[:12]}...")
            
            # Personen-DB-Instanz für diesen Datensatz
            person_instance = PdvmCentralDatenbank(db_name="PdvmManager.db", table_name="persondaten", guid=guid)
            
            # Teste verschiedene Felder
            test_felder = [
                ("PERSDATEN", "FAMILIENNAME"),
                ("PERSDATEN", "VORNAME"), 
                ("PERSDATEN", "EMAIL"),
                ("PERSDATEN", "ANREDE"),
                ("PERSDATEN", "GEBURTSDATUM")
            ]
            
            for gruppe, feld in test_felder:
                result = person_instance.get_value(gruppe, feld)
                print(f"      {gruppe}.{feld:<15} = {result}")
        
        # 2. ViewDatenManager Test mit Debug
        print(f"\n2️⃣ VIEWDATENMANAGER DEBUG:")
        
        # ViewDaten laden
        view_db = PdvmCentralDatenbank(db_name="PdvmManager.db", table_name="viewdaten", guid=None)
        view_records = view_db.lesen_alle_ohne_system(limit=1)
        
        if view_records:
            view_guid = view_records[0]["uid"]
            print(f"   📋 View: {view_guid[:12]}...")
            
            call_daten = {
                "view_guid": view_guid,
                "user_guid": "test-user-guid",
                "stichtag": 1001.0,
                "mode": "normal"
            }
            
            manager = PdvmViewDatenManager(call_daten)
            
            # Schaue Column Control Konfiguration an
            print(f"\n   🔧 COLUMN CONTROL ANALYSE:")
            for col in manager.column_control.columns:
                if col['name'] in ['familienname_show', 'vorname_show', 'email_show', 'anrede_show']:
                    print(f"      {col['name']:<20} | feld: {col.get('feld')} | gruppe: {col.get('gruppe')} | type: {col.get('field_config', {}).get('type')}")
            
            # Lade ersten Datensatz und schaue was passiert
            manager.load_records_data(limit=1)
            
            if manager.column_control.row_guids:
                first_guid = manager.column_control.row_guids[0]
                first_row = manager.column_control.get_row_data(first_guid)
                
                print(f"\n   📊 GELADENE DATEN (GUID: {first_guid[:8]}...):")
                for key, value in first_row.items():
                    if 'familienname' in key or 'vorname' in key or 'email' in key or 'anrede' in key:
                        print(f"      {key:<25} = '{value}' (type: {type(value).__name__})")
        
        # 3. Rohdaten aus persondaten prüfen  
        print(f"\n3️⃣ ROHDATEN ANALYSE:")
        
        if all_records:
            first_person = all_records[0]
            daten_dict = first_person.get("daten_dict", {})
            
            print(f"   📋 Rohdaten-Gruppen: {list(daten_dict.keys())}")
            
            # Schaue in relevante Gruppen
            for gruppe_name in ["PERSDATEN", "DATEN"]:
                if gruppe_name in daten_dict:
                    gruppe_data = daten_dict[gruppe_name]
                    if isinstance(gruppe_data, str):
                        import json
                        try:
                            gruppe_data = json.loads(gruppe_data)
                        except:
                            continue
                    
                    print(f"   🔍 Gruppe {gruppe_name}:")
                    for feld, wert in gruppe_data.items():
                        if any(x in feld.upper() for x in ['FAMILIEN', 'VOR', 'EMAIL', 'ANREDE']):
                            print(f"      {feld:<20} = '{wert}'")
        
        return True
        
    except Exception as e:
        print(f"❌ DEBUG FEHLGESCHLAGEN: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_string_columns()
    sys.exit(0 if success else 1)
