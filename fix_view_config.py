#!/usr/bin/env python3
"""Korrigiere die View-Konfiguration in der Datenbank"""

from pdvm_central_datenbank import PdvmCentralDatenbank
import json

def fix_view_config():
    """Korrigiere die View-Konfiguration in der viewdaten-Tabelle"""
    
    print("🔧 KORREKTUR: View-Konfiguration in viewdaten")
    print("=" * 60)
    
    # View-Konfiguration laden
    view_db = PdvmCentralDatenbank(
        db_name='PdvmManager.db',
        table_name='viewdaten',
        guid='0d10a0d0-b1a5-4544-b284-e8a09ca979b5'
    )
    
    view_config = view_db.lesen()
    print(f"📊 Aktuelle View-Config geladen")
    
    # Korrekturen vornehmen
    if view_config and 'metadata' in view_config:
        metadata = view_config['metadata']
        if 'persondaten' in metadata:
            felder = metadata['persondaten']['felder']
            
            print(f"\n🔧 Korrigiere {len(felder)} Felder:")
            
            for feld in felder:
                old_gruppe = feld.get('gruppe', 'N/A')
                # KORREKTUR: Gruppe in Großbuchstaben
                if old_gruppe == 'PersDaten':
                    feld['gruppe'] = 'PERSDATEN'
                    print(f"   ✅ {feld['feld']}: {old_gruppe} → PERSDATEN")
                else:
                    print(f"   ℹ️ {feld['feld']}: {old_gruppe} (keine Änderung)")
            
            # Korrigierte Konfiguration speichern
            view_db.speichern('0d10a0d0-b1a5-4544-b284-e8a09ca979b5', view_config)
            print(f"\n✅ View-Konfiguration korrigiert und gespeichert!")
            
            # Test mit korrigierter Konfiguration
            print(f"\n🧪 TEST mit korrigierter Konfiguration:")
            test_db = PdvmCentralDatenbank('PdvmManager.db')
            result = test_db.get_value_view(view_config)
            
            print(f"📊 Anzahl Datensätze: {len(result)}")
            if result:
                first_record = result[0]
                print(f"\n📋 Erster Datensatz (korrigiert):")
                for key, value in first_record.items():
                    if value and value != '':  # Nur Felder mit Werten zeigen
                        print(f"   {key}: {value}")
                
        else:
            print("❌ Keine 'persondaten' in metadata gefunden")
    else:
        print("❌ Keine View-Konfiguration gefunden")

if __name__ == "__main__":
    fix_view_config()
