#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KORREKTES CONTROLS SETUP

Erstellt Controls in der richtigen Struktur, die dem erwarteten Format entspricht.
"""

import json
import logging
import sys
import os

# Add project to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from pdvm_central_systemsteuerung import gcs
from pdvm_central_datenbank import PdvmCentralDatenbank

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_correct_controls_structure():
    """
    Erstelle Controls in der richtigen Struktur basierend auf dem Trace
    """
    print("🔧 KORREKTES CONTROLS SETUP")
    print("=" * 50)
    
    view_id = "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"
    
    # Laden der aktuellen ViewDaten für Metadaten
    view_db = PdvmCentralDatenbank()
    view_db.table = "viewdaten"
    view_db.guid = view_id
    view_db.load_data()
    view_data = view_db.get_all_data()
    
    print(f"📊 ViewDaten geladen: {list(view_data.keys())}")
    
    # Extrahiere Feldliste aus VIEW
    metadaten = view_data.get('METADATEN', {})
    if isinstance(metadaten, dict) and 'wert' in metadaten:
        meta_content = metadaten['wert']
        if isinstance(meta_content, dict):
            felder = meta_content.get('felder', [])
        else:
            felder = []
    else:
        felder = []
    
    print(f"📋 Gefundene Felder: {len(felder)}")
    for feld in felder:
        print(f"   - {feld.get('name', 'UNNAMED')}: {feld.get('type', 'unknown')}")
    
    # STRUKTUR BASIEREND AUF TRACE: Controls.fieldname + ColumnControls.fieldname
    controls_data = {}
    
    order_counter = 0
    
    for feld in felder:
        feld_name = feld.get('feld') or feld.get('name', 'UNNAMED')
        display_name = feld.get('name', feld_name)
        feld_type = feld.get('type', 'string')
        gruppe = feld.get('gruppe', 'SYSTEM')
        
        # Standard UI-Konfiguration aus dem Feld
        ui_config = feld.get('ui', {})
        
        # Basis field_config
        field_config = {
            "gruppe": gruppe,
            "feld": feld_name,
            "name": display_name,
            "type": feld_type,
            "default": feld.get('default'),
            "dropdown": feld.get('dropdown'),
            "ui": ui_config
        }
        
        # UI-Sichtbarkeit
        ui_visible = ui_config.get('searchable', True) or ui_config.get('sortable', True)
        if ui_visible:
            field_config["ui_visible"] = True
        
        # ORIGINAL-VARIANTEN (versteckt)
        for suffix, variant_type in [("_original", feld_type), ("_alter_original", "date_alter"), 
                                   ("_jahr_original", "date_jahr"), ("_monat_original", "date_monat"), 
                                   ("_tag_original", "date_tag")]:
            
            # Nur relevante Varianten für Datum-Felder
            if suffix != "_original" and feld_type != "date":
                continue
                
            control_key = f"Controls.{feld_name.lower()}{suffix}"
            controls_data[control_key] = {
                "name": f"{feld_name.lower()}{suffix}",
                "type": variant_type,
                "gruppe": gruppe,
                "feld": feld_name,
                "show": False,
                "expertOrder": order_counter,
                "displayOrder": order_counter,
                "field_config": field_config.copy(),
                "spaltenueberschrift": f"{display_name}{suffix.replace('_', ' ').title()}"
            }
            
            if ui_visible:
                controls_data[control_key]["ui_visible"] = True
            
            order_counter += 1
        
        # SHOW-VARIANTEN (sichtbar)
        for suffix, variant_type in [("_show", feld_type), ("_alter_show", "date_alter"), 
                                   ("_jahr_show", "date_jahr"), ("_monat_show", "date_monat"), 
                                   ("_tag_show", "date_tag")]:
            
            # Nur relevante Varianten für Datum-Felder
            if suffix != "_show" and feld_type != "date":
                continue
                
            control_key = f"Controls.{feld_name.lower()}{suffix}"
            controls_data[control_key] = {
                "name": f"{feld_name.lower()}{suffix}",
                "type": variant_type,
                "gruppe": gruppe,
                "feld": feld_name,
                "show": True,
                "expertOrder": order_counter,
                "displayOrder": order_counter,
                "field_config": field_config.copy(),
                "spaltenueberschrift": f"{display_name}{suffix.replace('_show', '')}",
                "ui_visible": True
            }
            
            order_counter += 1
    
    # DUMMY CONTROL
    controls_data["Controls.dummy"] = {
        "name": "dummy",
        "type": "dummy",
        "show": False,
        "expertOrder": order_counter,
        "displayOrder": order_counter,
        "field_config": {},
        "spaltenueberschrift": ""
    }
    
    # COLUMN CONTROLS (identische Struktur ohne "Controls." Prefix)
    column_controls = {}
    for key, value in controls_data.items():
        if key.startswith("Controls."):
            column_key = key.replace("Controls.", "")
            column_controls[column_key] = value.copy()
    
    # Vollständige Struktur
    full_controls = dict(controls_data)
    full_controls["ColumnControls"] = column_controls
    
    print(f"✅ {len(full_controls)} Controls erstellt (inkl. ColumnControls)")
    print(f"   - Controls.*: {len([k for k in full_controls.keys() if k.startswith('Controls.')])}")
    print(f"   - ColumnControls: {len(column_controls)}")
    
    # SPEICHERN
    print("\n💾 Speichere Controls...")
    controls_json = json.dumps(full_controls, ensure_ascii=False, indent=2)
    gcs().set_value_no_json(view_id, 'controls', controls_json)
    
    # VIEW_CONFIG (identische Struktur)
    print("💾 Speichere view_config...")
    view_config_json = json.dumps(full_controls, ensure_ascii=False, indent=2)
    gcs().set_value_no_json(view_id, 'view_config', view_config_json)
    
    # Persistierung
    gcs().save_values()
    print("✅ Daten persistent gespeichert")
    
    # VALIDIERUNG
    print("\n🔍 Validierung...")
    loaded_controls = gcs().get_value_no_json(view_id, 'controls')
    if loaded_controls:
        parsed_controls = json.loads(loaded_controls)
        print(f"✅ Controls geladen: {len(parsed_controls)} Felder")
        
        # Zeige Struktur
        controls_keys = [k for k in parsed_controls.keys() if k.startswith('Controls.')]
        print(f"   - Controls.*: {len(controls_keys)} (erste 5: {controls_keys[:5]})")
        
        if "ColumnControls" in parsed_controls:
            column_count = len(parsed_controls["ColumnControls"])
            print(f"   - ColumnControls: {column_count} Spalten")
        
    return True

if __name__ == "__main__":
    create_correct_controls_structure()
