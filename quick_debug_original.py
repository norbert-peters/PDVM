#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QUICK DEBUG: Original-Spalten laden
===================================
"""

import sys
import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

import importlib.util
spec = importlib.util.spec_from_file_location('pdvm_systemstart', 'pdvm_systemstart.py')
pdvm_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pdvm_module)

from pdvm_central_datenbank import PdvmCentralDatenbank
from pdvm_view_daten_manager import PdvmViewDatenManager

# ViewDaten finden
view_db = PdvmCentralDatenbank(db_name="PdvmManager.db", table_name="viewdaten", guid=None)
all_view_records = view_db.lesen_alle_ohne_system(limit=1)

if all_view_records:
    view_guid = all_view_records[0]["uid"]
    call_daten = {
        "view_guid": view_guid,
        "user_guid": "test-user-guid",
        "stichtag": 1001.0,
        "mode": "normal"
    }
    
    manager = PdvmViewDatenManager(call_daten)
    manager.load_records_data(limit=1)
    
    if manager.column_control.row_guids:
        first_guid = manager.column_control.row_guids[0]
        first_row = manager.column_control.get_row_data(first_guid)
        
        print("DEBUG ORIGINAL-SPALTEN:")
        for key, value in first_row.items():
            if key.endswith('_original'):
                print(f"   {key:<30} = '{value}' (type: {type(value).__name__}, len: {len(str(value)) if value else 0})")
        
        print("\nDEBUG DB-INSTANZ:")
        # Testen ob DB-Instanz korrekt funktioniert  
        person_db = PdvmCentralDatenbank(db_name="PdvmManager.db", table_name="persondaten", guid=first_guid)
        
        test_calls = [
            ("PERSDATEN", "FAMILIENNAME"),
            ("DATEN", "FAMILIENNAME"), 
            ("PERSDATEN", "VORNAME"),
            ("DATEN", "VORNAME"),
            ("PERSDATEN", "ANREDE"),
            ("DATEN", "ANREDE")
        ]
        
        for gruppe, feld in test_calls:
            result = person_db.get_value(gruppe, feld, ab_zeit=1001.0)
            print(f"   {gruppe}.{feld:<15} = {result}")

print("FERTIG!")
