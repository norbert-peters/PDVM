#!/usr/bin/env python3
"""
ERSTMALIGE EINRICHTUNG: Controls in einheitlicher Struktur erstellen

Das ist das Problem: Der Dialog lädt aus systemsteuerung.view_id.controls,
aber dort sind noch keine Daten gespeichert. Diese Routine erstellt 
erstmalig Controls aus den ViewDaten und speichert sie korrekt.
"""

import json
import logging
from pdvm_central_systemsteuerung import gcs
from pdvm_central_datenbank import PdvmCentralDatenbank

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def erstelle_controls_einheitliche_struktur():
    """
    Erstelle Controls aus ViewDaten und speichere sie in einheitlicher Struktur
    """
    print("🏗️ ERSTMALIGE EINRICHTUNG: Controls in einheitlicher Struktur")
    print("=" * 70)
    
    view_id = '0d10a0d0-b1a5-4544-b284-e8a09ca979b5'
    
    # SCHRITT 1: ViewDaten laden
    print("\n📊 SCHRITT 1: ViewDaten laden")
    try:
        view_db = PdvmCentralDatenbank(
            db_name='PdvmManager.db',
            table_name='viewdaten',
            guid=view_id
        )
        view_config = view_db.lesen()
        
        if not view_config:
            print("❌ Keine ViewDaten gefunden")
            return False
            
        print(f"✅ ViewDaten geladen: {list(view_config.keys())}")
        
        # Felder extrahieren
        felder = []
        if 'metadata' in view_config and 'persondaten' in view_config['metadata']:
            felder = view_config['metadata']['persondaten']['felder']
        elif 'METADATEN' in view_config and 'PERSONDATEN' in view_config['METADATEN']:
            felder = view_config['METADATEN']['PERSONDATEN']['felder']
        else:
            print("❌ Keine Felder in ViewDaten gefunden")
            return False
            
        print(f"📋 {len(felder)} Felder gefunden")
        
    except Exception as e:
        print(f"❌ Fehler beim Laden der ViewDaten: {e}")
        return False
    
    # SCHRITT 2: Controls erstellen (EINHEITLICHE STRUKTUR)
    print("\n🔧 SCHRITT 2: Controls in einheitlicher Struktur erstellen")
    
    controls_data = {}
    view_config_data = {}
    
    for idx, feld in enumerate(felder):
        feld_name = feld.get('feld', f'feld_{idx}')
        name = feld.get('name', feld_name)
        type_val = feld.get('type', 'string')
        
        # CONTROLS: Für Dialog mit vollständigen Informationen
        control = {
            'field_name': feld_name,
            'spaltenueberschrift': name,
            'type': type_val,
            'show': True,  # Standard: sichtbar
            'expert_mode': False,  # Standard: Normal-Mode
            'breite': 120,
            'ausrichtung': 'left',
            'display_order': idx,
            'expert_order': idx,
            '_version': '3.0',
            '_created_from': 'first_time_setup'
        }
        
        # VIEW_CONFIG: Identische Struktur!
        view_config_entry = {
            'field_name': feld_name,
            'spaltenueberschrift': name,
            'type': type_val,
            'show': True,
            'expert_mode': False,
            'breite': 120,
            'ausrichtung': 'left',
            'display_order': idx,
            'expert_order': idx,
            '_version': '3.0',
            '_created_from': 'first_time_setup'
        }
        
        # EINHEITLICHE SCHLÜSSEL: Beide verwenden feld_name als Key
        controls_data[feld_name] = control
        view_config_data[feld_name] = view_config_entry
        
        print(f"   📋 Control erstellt: {feld_name} → {name}")
    
    print(f"✅ {len(controls_data)} Controls erstellt (einheitliche Struktur)")
    
    # SCHRITT 3: In Systemsteuerung speichern (EINHEITLICHE SPEICHERUNG)
    print("\n💾 SCHRITT 3: Einheitliche Speicherung in Systemsteuerung")
    
    try:
        # Controls speichern (interne Feldnamen als Keys)
        controls_json = json.dumps(controls_data, ensure_ascii=False, indent=2)
        gcs().set_value_no_json(view_id, 'controls', controls_json)
        print(f"✅ Controls gespeichert: {len(controls_data)} Felder")
        
        # View-Config speichern (identische Struktur!)
        view_config_json = json.dumps(view_config_data, ensure_ascii=False, indent=2)
        gcs().set_value_no_json(view_id, 'view_config', view_config_json)
        print(f"✅ View-Config gespeichert: {len(view_config_data)} Felder")
        
        # Persistierung
        gcs().save_values()
        print("✅ Daten persistent gespeichert")
        
        # SCHRITT 4: Validierung
        print("\n🔍 SCHRITT 4: Validierung")
        
        # Controls wieder laden
        loaded_controls = gcs().get_value_no_json(view_id, 'controls')
        if loaded_controls:
            parsed_controls = json.loads(loaded_controls)
            print(f"✅ Controls-Validierung: {len(parsed_controls)} Felder geladen")
        else:
            print("❌ Controls-Validierung fehlgeschlagen")
            
        # View-Config wieder laden  
        loaded_view_config = gcs().get_value_no_json(view_id, 'view_config')
        if loaded_view_config:
            parsed_view_config = json.loads(loaded_view_config)
            print(f"✅ View-Config-Validierung: {len(parsed_view_config)} Felder geladen")
        else:
            print("❌ View-Config-Validierung fehlgeschlagen")
        
        print("\n🎯 EINRICHTUNG ABGESCHLOSSEN!")
        print("Der Spalten-Dialog kann jetzt die Controls korrekt laden.")
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Speichern: {e}")
        import traceback
        traceback.print_exc()
        return False

def zeige_aktuelle_daten():
    """Zeigt die aktuell gespeicherten Daten an"""
    view_id = '0d10a0d0-b1a5-4544-b284-e8a09ca979b5'
    
    print("\n🔍 AKTUELLE DATEN IN SYSTEMSTEUERUNG:")
    print("=" * 50)
    
    # Controls prüfen
    try:
        controls_result = gcs().get_value_no_json(view_id, 'controls')
        if controls_result:
            print(f"✅ Controls gefunden: {len(controls_result)} Zeichen")
            try:
                parsed = json.loads(controls_result)
                print(f"   📋 Felder: {list(parsed.keys())}")
            except:
                print("   ⚠️ JSON parsing fehlgeschlagen")
        else:
            print("❌ Keine Controls gefunden")
    except Exception as e:
        print(f"❌ Fehler beim Laden der Controls: {e}")
    
    # View-Config prüfen
    try:
        view_config_result = gcs().get_value_no_json(view_id, 'view_config')
        if view_config_result:
            print(f"✅ View-Config gefunden: {len(view_config_result)} Zeichen")
            try:
                parsed = json.loads(view_config_result)
                print(f"   📋 Felder: {list(parsed.keys())}")
            except:
                print("   ⚠️ JSON parsing fehlgeschlagen")
        else:
            print("❌ Keine View-Config gefunden")
    except Exception as e:
        print(f"❌ Fehler beim Laden der View-Config: {e}")

if __name__ == "__main__":
    print("🚀 FIRST-TIME CONTROLS SETUP")
    print("=" * 50)
    
    # Aktuelle Situation anzeigen
    zeige_aktuelle_daten()
    
    # Einrichtung durchführen
    erfolg = erstelle_controls_einheitliche_struktur()
    
    if erfolg:
        print("\n🎉 ERFOLG: Einheitliche Struktur eingerichtet!")
        print("Testen Sie jetzt den Spalten-Dialog...")
    else:
        print("\n❌ FEHLER: Einrichtung fehlgeschlagen")
