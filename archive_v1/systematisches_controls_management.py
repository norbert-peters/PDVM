#!/usr/bin/env python3
"""
SYSTEMATISCHER AUFBAU: Controls und view_config Management

STURER AUFBAU IN EXAKTER REIHENFOLGE:
1. Originalcontrols + view_configs aus view_daten erstellen (gleicher Schlüssel)
2. Zusatzcontrols bei date-Feldern erstellen (mit view_configs)
3. Showcontrols + view_configs aus Originalcontrols ableiten
4. Dummy-Spalte als Control + view_config erstellen
5. Mit Systemsteuerung synchronisieren (show, expert_mode, expertOrder, showOrder)
6. Controls + view_config in Systemsteuerung speichern (überschreibt alte)
7. Tabelle aus Systemsteuerung-Daten aufbauen
8. Spaltendialog aus Systemsteuerung-Daten befüllen
9. Dialog-Änderungen in Systemsteuerung schreiben (OK)
10. Persistent speichern
"""

import json
import logging
from pdvm_central_systemsteuerung import gcs
from pdvm_central_datenbank import PdvmCentralDatenbank

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystematischesControlsManagement:
    """Systematisches Controls-Management in sturer Reihenfolge"""
    
    def __init__(self, view_id):
        self.view_id = view_id
        self.view_daten = None
        self.original_controls = {}
        self.original_view_configs = {}
        self.zusatz_controls = {}
        self.zusatz_view_configs = {}
        self.show_controls = {}
        self.show_view_configs = {}
        self.dummy_control = {}
        self.dummy_view_config = {}
        self.finale_controls = {}
        self.finale_view_configs = {}
        
    def schritt_1_originalcontrols_aus_viewdaten(self):
        """1. Originalcontrols + view_configs aus view_daten erstellen (gleicher Schlüssel)"""
        print("\n📊 SCHRITT 1: Originalcontrols aus ViewDaten")
        
        # ViewDaten laden
        view_db = PdvmCentralDatenbank(
            db_name='PdvmManager.db',
            table_name='viewdaten',
            guid=self.view_id
        )
        self.view_daten = view_db.lesen()
        
        if not self.view_daten:
            raise ValueError("Keine ViewDaten gefunden")
            
        # Felder extrahieren
        felder = []
        if 'METADATEN' in self.view_daten and 'PERSONDATEN' in self.view_daten['METADATEN']:
            felder = self.view_daten['METADATEN']['PERSONDATEN']['felder']
        else:
            raise ValueError("Keine Felder in ViewDaten gefunden")
            
        print(f"   📋 {len(felder)} Felder gefunden")
        
        # Originalcontrols + view_configs erstellen
        for idx, feld in enumerate(felder):
            feld_name = feld.get('feld', f'feld_{idx}')
            control_name = f"{feld_name.lower()}_original"
            
            # ORIGINAL CONTROL
            control = {
                'field_name': control_name,
                'internal_field': feld_name,
                'spaltenueberschrift': f"{feld.get('name', feld_name)} (orig.)",
                'type': feld.get('type', 'string'),
                'show': False,  # Original = versteckt
                'expert_mode': True,  # Original = Expert-Mode
                'breite': 120,
                'ausrichtung': 'left',
                'expert_order': idx,
                'show_order': 9999,  # Original nicht in Show-Liste
                '_version': '4.0',
                '_type': 'original'
            }
            
            # VIEW_CONFIG (identisch!)
            view_config = control.copy()
            
            # Speichern mit gleichem Schlüssel
            self.original_controls[control_name] = control
            self.original_view_configs[control_name] = view_config
            
            print(f"   ✅ Original: {control_name}")
            
        print(f"   📊 {len(self.original_controls)} Originalcontrols erstellt")
        
    def schritt_2_zusatzcontrols_bei_date(self):
        """2. Zusatzcontrols bei date-Feldern erstellen (mit view_configs)"""
        print("\n🗓️ SCHRITT 2: Zusatzcontrols für Date-Felder")
        
        for control_name, control in self.original_controls.items():
            if control['type'] == 'date':
                base_name = control['internal_field'].lower()
                
                # Date-Zusatzfelder
                zusatz_typen = ['alter', 'jahr', 'monat', 'tag']
                
                for zusatz_typ in zusatz_typen:
                    zusatz_name = f"{base_name}_{zusatz_typ}_original"
                    
                    # ZUSATZ CONTROL
                    zusatz_control = {
                        'field_name': zusatz_name,
                        'internal_field': control['internal_field'],
                        'spaltenueberschrift': f"{control['spaltenueberschrift'].replace(' (orig.)', '')} {zusatz_typ.title()} (orig.)",
                        'type': f"date_{zusatz_typ}",
                        'show': False,
                        'expert_mode': True,
                        'breite': 80,
                        'ausrichtung': 'center',
                        'expert_order': len(self.original_controls) + len(self.zusatz_controls),
                        'show_order': 9999,
                        '_version': '4.0',
                        '_type': 'date_zusatz'
                    }
                    
                    # VIEW_CONFIG (identisch!)
                    zusatz_view_config = zusatz_control.copy()
                    
                    self.zusatz_controls[zusatz_name] = zusatz_control
                    self.zusatz_view_configs[zusatz_name] = zusatz_view_config
                    
                    print(f"   ✅ Date-Zusatz: {zusatz_name}")
                    
        print(f"   📊 {len(self.zusatz_controls)} Date-Zusatzcontrols erstellt")
        
    def schritt_3_showcontrols_ableiten(self):
        """3. Showcontrols + view_configs aus Originalcontrols ableiten"""
        print("\n👁️ SCHRITT 3: Showcontrols ableiten")
        
        # Alle Original + Zusatz zusammenfassen
        alle_original = {**self.original_controls, **self.zusatz_controls}
        
        show_order_counter = 0
        
        for control_name, original_control in alle_original.items():
            # Show-Namen erstellen
            show_name = control_name.replace('_original', '_show')
            
            # SHOW CONTROL
            show_control = original_control.copy()
            show_control.update({
                'field_name': show_name,
                'spaltenueberschrift': original_control['spaltenueberschrift'].replace(' (orig.)', ''),
                'show': True,  # Show = sichtbar
                'expert_mode': False,  # Show = Normal-Mode
                'show_order': show_order_counter,
                '_type': 'show'
            })
            
            # VIEW_CONFIG (identisch!)
            show_view_config = show_control.copy()
            
            self.show_controls[show_name] = show_control
            self.show_view_configs[show_name] = show_view_config
            
            show_order_counter += 1
            print(f"   ✅ Show: {show_name}")
            
        print(f"   📊 {len(self.show_controls)} Showcontrols erstellt")
        
    def schritt_4_dummy_spalte(self):
        """4. Dummy-Spalte als Control + view_config erstellen"""
        print("\n🎭 SCHRITT 4: Dummy-Spalte erstellen")
        
        # DUMMY CONTROL
        self.dummy_control = {
            'field_name': 'dummy',
            'internal_field': 'dummy',
            'spaltenueberschrift': '',
            'type': 'dummy',
            'show': False,
            'expert_mode': False,
            'breite': 0,
            'ausrichtung': 'left',
            'expert_order': 9999,
            'show_order': 9999,
            '_version': '4.0',
            '_type': 'dummy'
        }
        
        # VIEW_CONFIG (identisch!)
        self.dummy_view_config = self.dummy_control.copy()
        
        print("   ✅ Dummy-Spalte erstellt")
        
    def schritt_5_systemsteuerung_synchronisieren(self):
        """5. Mit Systemsteuerung synchronisieren"""
        print("\n🔄 SCHRITT 5: Systemsteuerung-Synchronisation")
        
        # Alle Controls zusammenfassen
        self.finale_controls = {
            **self.original_controls,
            **self.zusatz_controls,
            **self.show_controls,
            'dummy': self.dummy_control
        }
        
        self.finale_view_configs = {
            **self.original_view_configs,
            **self.zusatz_view_configs,
            **self.show_view_configs,
            'dummy': self.dummy_view_config
        }
        
        # Alte Einstellungen aus Systemsteuerung laden
        try:
            alte_controls = gcs().get_value_no_json(self.view_id, 'controls')
            if alte_controls:
                alte_controls_dict = json.loads(alte_controls)
                
                # Eigenschaften übernehmen
                for control_name, control in self.finale_controls.items():
                    if control_name in alte_controls_dict:
                        alte_settings = alte_controls_dict[control_name]
                        
                        # Systemsteuerung-Eigenschaften übernehmen
                        control['show'] = alte_settings.get('show', control['show'])
                        control['expert_mode'] = alte_settings.get('expert_mode', control['expert_mode'])
                        control['expert_order'] = alte_settings.get('expert_order', control['expert_order'])
                        control['show_order'] = alte_settings.get('show_order', control['show_order'])
                        
                        # Auch in view_config übernehmen
                        self.finale_view_configs[control_name].update({
                            'show': control['show'],
                            'expert_mode': control['expert_mode'],
                            'expert_order': control['expert_order'],
                            'show_order': control['show_order']
                        })
                        
                        print(f"   🔄 Übernommen: {control_name}")
                        
        except Exception as e:
            print(f"   ⚠️ Keine alten Einstellungen: {e}")
            
        print(f"   📊 {len(self.finale_controls)} Controls synchronisiert")
        
    def schritt_6_in_systemsteuerung_speichern(self):
        """6. Controls + view_config in Systemsteuerung speichern (überschreibt alte)"""
        print("\n💾 SCHRITT 6: In Systemsteuerung speichern")
        
        # Controls speichern
        controls_json = json.dumps(self.finale_controls, ensure_ascii=False, indent=2)
        gcs().set_value_no_json(self.view_id, 'controls', controls_json)
        
        # view_config speichern
        view_config_json = json.dumps(self.finale_view_configs, ensure_ascii=False, indent=2)
        gcs().set_value_no_json(self.view_id, 'view_config', view_config_json)
        
        # Persistieren
        gcs().save_values()
        
        print(f"   ✅ Controls gespeichert: {len(self.finale_controls)} Felder")
        print(f"   ✅ view_config gespeichert: {len(self.finale_view_configs)} Felder")
        print("   💾 Persistent gespeichert")
        
    def vollstaendiger_durchlauf(self):
        """Kompletter Durchlauf aller Schritte"""
        print("🚀 SYSTEMATISCHER CONTROLS-AUFBAU")
        print("=" * 60)
        
        self.schritt_1_originalcontrols_aus_viewdaten()
        self.schritt_2_zusatzcontrols_bei_date()
        self.schritt_3_showcontrols_ableiten()
        self.schritt_4_dummy_spalte()
        self.schritt_5_systemsteuerung_synchronisieren()
        self.schritt_6_in_systemsteuerung_speichern()
        
        print("\n✅ ALLE SCHRITTE ABGESCHLOSSEN!")
        print(f"📊 Finale Statistik:")
        print(f"   Original: {len(self.original_controls)}")
        print(f"   Zusatz: {len(self.zusatz_controls)}")
        print(f"   Show: {len(self.show_controls)}")
        print(f"   Dummy: 1")
        print(f"   GESAMT: {len(self.finale_controls)}")
        
        return True

def main():
    """Hauptfunktion"""
    view_id = '0d10a0d0-b1a5-4544-b284-e8a09ca979b5'
    
    manager = SystematischesControlsManagement(view_id)
    erfolg = manager.vollstaendiger_durchlauf()
    
    if erfolg:
        print("\n🎯 BEREIT FÜR:")
        print("7. Tabelle aus Systemsteuerung aufbauen")
        print("8. Spaltendialog aus Systemsteuerung befüllen")
        print("9. Dialog-Änderungen speichern")
        print("10. Persistent speichern")

if __name__ == "__main__":
    main()
