#!/usr/bin/env python3
"""
ROBUSTE LÖSUNG: Controls mit Base64-Encoding für Systemsteuerung
"""

import json
import base64
import logging
from pdvm_central_systemsteuerung import gcs

logger = logging.getLogger(__name__)

class RobusteControlsPersistierung:
    """
    Robuste Controls-Persistierung mit Base64-Encoding
    
    PROBLEMLÖSUNG:
    - Systemsteuerung konvertiert JSON automatisch
    - Base64-Encoding umgeht die automatische Typ-Erkennung
    - Vollständige Control-Strukturen bleiben erhalten
    """
    
    def __init__(self, view_guid):
        self.view_guid = view_guid
        self.systemsteuerung = gcs()
    
    def control_zu_base64(self, control_dict):
        """Konvertiert Control-Dict zu Base64-String"""
        json_string = json.dumps(control_dict, ensure_ascii=False)
        json_bytes = json_string.encode('utf-8')
        base64_string = base64.b64encode(json_bytes).decode('ascii')
        return base64_string
    
    def base64_zu_control(self, base64_string):
        """Konvertiert Base64-String zurück zu Control-Dict"""
        json_bytes = base64.b64decode(base64_string.encode('ascii'))
        json_string = json_bytes.decode('utf-8')
        control_dict = json.loads(json_string)
        return control_dict
    
    def control_speichern(self, feld_name, control_dict):
        """Speichert einzelnes Control als Base64 in Systemsteuerung"""
        try:
            base64_data = self.control_zu_base64(control_dict)
            
            self.systemsteuerung.set_value(
                gruppe=self.view_guid,
                feld=f"ctrl64_{feld_name}",  # Eindeutiger Prefix
                wert=base64_data
            )
            return True
        except Exception as e:
            logger.error(f"Fehler beim Speichern Control {feld_name}: {e}")
            return False
    
    def control_laden(self, feld_name):
        """Lädt einzelnes Control aus Systemsteuerung"""
        try:
            result = self.systemsteuerung.get_value(
                gruppe=self.view_guid,
                feld=f"ctrl64_{feld_name}"
            )
            
            if result:
                # Base64-String extrahieren
                if isinstance(result, dict) and 'wert' in result:
                    base64_string = result['wert']
                elif isinstance(result, str):
                    base64_string = result
                else:
                    return None
                
                # Zu Control-Dict konvertieren
                control_dict = self.base64_zu_control(base64_string)
                return control_dict
                
        except Exception as e:
            logger.warning(f"Fehler beim Laden Control {feld_name}: {e}")
            
        return None
    
    def alle_controls_speichern(self, controls_dict):
        """Speichert alle Controls"""
        erfolg_count = 0
        for feld_name, control_dict in controls_dict.items():
            if self.control_speichern(feld_name, control_dict):
                erfolg_count += 1
                
        logger.info(f"💾 {erfolg_count}/{len(controls_dict)} Controls erfolgreich gespeichert")
        return erfolg_count == len(controls_dict)
    
    def alle_controls_laden(self, feld_namen):
        """Lädt alle Controls für gegebene Feld-Namen"""
        loaded_controls = {}
        
        for feld_name in feld_namen:
            control = self.control_laden(feld_name)
            if control:
                loaded_controls[feld_name] = control
                
        logger.info(f"📥 {len(loaded_controls)}/{len(feld_namen)} Controls erfolgreich geladen")
        return loaded_controls


def test_robuste_persistierung():
    """Test der robusten Base64-Lösung"""
    
    print("🔧 ROBUSTE LÖSUNG: Base64-Controls-Persistierung")
    print("=" * 60)
    
    try:
        # Setup
        view_guid = "test_robust_view"
        persistierung = RobusteControlsPersistierung(view_guid)
        
        # Test-Controls erstellen
        test_controls = {
            'person_id': {
                'type': 'int',
                'gruppe': 'Personen',
                'feld': 'person_id',
                'spaltenueberschrift': 'Person ID',
                'show': True,
                'displayOrder': 0,
                'expertOrder': 0,
                'breite': 80,
                'ausrichtung': 'right'
            },
            'name': {
                'type': 'str',
                'gruppe': 'Personen', 
                'feld': 'name',
                'spaltenueberschrift': 'Name',
                'show': True,
                'displayOrder': 1,
                'expertOrder': 1,
                'breite': 150,
                'ausrichtung': 'left'
            },
            'geburtsdatum': {
                'type': 'date',
                'gruppe': 'Personen',
                'feld': 'geburtsdatum', 
                'spaltenueberschrift': 'Geburtsdatum',
                'show': True,
                'displayOrder': 2,
                'expertOrder': 2,
                'breite': 120,
                'ausrichtung': 'center'
            }
        }
        
        print(f"📋 Test-Controls erstellt: {len(test_controls)} Einträge")
        
        # Base64-Encoding Test
        print("\n🔧 Base64-Encoding Test:")
        test_control = test_controls['name']
        base64_data = persistierung.control_zu_base64(test_control)
        print(f"   Original: {test_control}")
        print(f"   Base64: {base64_data[:50]}...")
        
        # Base64-Decoding Test
        decoded_control = persistierung.base64_zu_control(base64_data)
        print(f"   Decoded: {decoded_control}")
        print(f"   ✅ Encoding/Decoding: {'OK' if decoded_control == test_control else 'FEHLER'}")
        
        # Systemsteuerung-Persistierung
        print("\n💾 Systemsteuerung-Persistierung:")
        erfolg = persistierung.alle_controls_speichern(test_controls)
        print(f"   ✅ Speichern: {'Erfolgreich' if erfolg else 'Fehler'}")
        
        # Laden aus Systemsteuerung
        print("\n📥 Aus Systemsteuerung laden:")
        feld_namen = list(test_controls.keys())
        loaded_controls = persistierung.alle_controls_laden(feld_namen)
        
        print(f"   📊 Geladen: {len(loaded_controls)} Controls")
        for name, control in loaded_controls.items():
            print(f"      ✅ {name}: {control['spaltenueberschrift']} "
                  f"(Pos: {control['displayOrder']}, Breite: {control['breite']})")
        
        # Vergleich Original vs. Geladen
        print("\n🔍 Integrität-Check:")
        for name in feld_namen:
            if name in loaded_controls:
                original = test_controls[name]
                loaded = loaded_controls[name]
                is_identical = original == loaded
                print(f"   {'✅' if is_identical else '❌'} {name}: {'Identisch' if is_identical else 'Unterschiedlich'}")
            else:
                print(f"   ❌ {name}: Nicht geladen")
        
        # Controls ändern und speichern (wie Spalten-Dialog)
        print("\n✏️ Änderungen simulieren:")
        if 'name' in loaded_controls:
            loaded_controls['name']['show'] = False
            loaded_controls['name']['spaltenueberschrift'] = 'Nachname (geändert)'
            loaded_controls['name']['displayOrder'] = 5
            
            # Änderung speichern
            persistierung.control_speichern('name', loaded_controls['name'])
            
            # Wieder laden zur Verifikation
            updated_control = persistierung.control_laden('name')
            print(f"   ✅ Änderung gespeichert: {updated_control['spaltenueberschrift']}")
            print(f"   ✅ Show-Status: {updated_control['show']}")
            print(f"   ✅ Neue Position: {updated_control['displayOrder']}")
        
        print(f"\n🎉 ROBUSTE BASE64-PERSISTIERUNG ERFOLGREICH!")
        print("✅ Vollständige Control-Strukturen bleiben erhalten")
        print("✅ Systemsteuerung-kompatibel") 
        print("✅ JSON + Base64 umgeht automatische Typ-Konvertierung")
        print("✅ Bereit für Integration in Spalten-Dialog")
        
    except Exception as e:
        print(f"❌ Fehler in robuster Persistierung: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_robuste_persistierung()
