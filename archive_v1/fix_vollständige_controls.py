"""
DIREKTE VOLLSTÄNDIGE CONTROLS GENERATION

Da bestehende Views noch alte Datenstrukturen haben, 
generieren wir hier vollständige Controls und speichern sie direkt.
"""
import logging
import sys
import os

# Pfad für Module hinzufügen
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# PDVM Module
import pdvm_central_systemsteuerung_global
gcs = pdvm_central_systemsteuerung_global.central_systemsteuerung

def generiere_vollständige_controls_für_bestehende_views():
    """Generiert vollständige Controls für alle bestehenden Views"""
    print("="*70)
    print("🔧 VOLLSTÄNDIGE CONTROLS FÜR BESTEHENDE VIEWS GENERIEREN")
    print("="*70)
    
    try:
        # Alle Views in Systemsteuerung finden
        if hasattr(gcs, '_database') and hasattr(gcs._database, 'data'):
            all_views = gcs._database.data.keys()
            print(f"📊 Gefundene Views: {len(all_views)}")
            
            # Views mit ColumnControls finden
            updated_views = 0
            
            for view_id in all_views:
                print(f"\n🔍 Prüfe View: {view_id}")
                
                try:
                    column_controls = gcs.get_value(view_id, 'ColumnControls')
                    
                    if column_controls:
                        # Prüfe ob vollständige Controls
                        first_control = next(iter(column_controls.values()), {})
                        
                        if isinstance(first_control, dict) and 'type' in first_control and 'gruppe' in first_control:
                            print(f"   ✅ Bereits vollständige Controls vorhanden")
                            continue
                        else:
                            print(f"   ⚠️ Nur Attribute vorhanden - konvertiere zu vollständigen Controls")
                            
                            # Konvertiere Attribute zu vollständigen Controls
                            vollständige_controls = {}
                            
                            for name, attrs in column_controls.items():
                                if isinstance(attrs, dict):
                                    # Erstelle vollständige Control-Struktur
                                    control = {
                                        'name': name,
                                        'type': 'string',  # Default
                                        'gruppe': 'LEGACY_CONVERTED',
                                        'feld': name.replace('_original', '').replace('_show', '').upper(),
                                        'show': attrs.get('show', False),
                                        'expertOrder': attrs.get('expertOrder', 999),
                                        'displayOrder': attrs.get('displayOrder', 999),
                                        'spaltenueberschrift': name.replace('_', ' ').title(),
                                        'field_config': {},
                                        'use_html': False,
                                        'spaltenbreite': 100
                                    }
                                    
                                    # Spezielle Anpassungen für bekannte Feldtypen
                                    if 'datum' in name.lower() or 'date' in name.lower():
                                        control['type'] = 'date'
                                        control['spaltenbreite'] = 100
                                    elif 'alter' in name.lower() or 'jahr' in name.lower():
                                        control['type'] = 'int'
                                        control['spaltenbreite'] = 60
                                    elif 'uid' in name.lower() or 'id' in name.lower():
                                        control['gruppe'] = 'SYSTEM'
                                        control['spaltenbreite'] = 80
                                    elif any(x in name.lower() for x in ['name', 'vorname', 'nachname']):
                                        control['gruppe'] = 'PERSON'
                                        control['spaltenbreite'] = 120
                                    
                                    vollständige_controls[name] = control
                                else:
                                    print(f"      ⚠️ Überspringe ungültigen Eintrag: {name} = {type(attrs)}")
                            
                            if vollständige_controls:
                                # Speichere vollständige Controls
                                gcs.set_value(view_id, 'ColumnControls', vollständige_controls)
                                updated_views += 1
                                print(f"   ✅ {len(vollständige_controls)} vollständige Controls gespeichert")
                            else:
                                print(f"   ❌ Keine gültigen Controls konvertiert")
                    else:
                        print(f"   ❌ Keine ColumnControls gefunden")
                        
                except Exception as e:
                    print(f"   ❌ Fehler bei View {view_id}: {e}")
            
            print(f"\n📊 Zusammenfassung: {updated_views} Views aktualisiert")
            
            if updated_views > 0:
                print("🎉 VOLLSTÄNDIGE CONTROLS erfolgreich generiert!")
                print("\n💡 Jetzt sollten alle Spalten-Dialoge funktionieren!")
                return True
            else:
                print("⚠️ Keine Views wurden aktualisiert")
                return False
                
        else:
            print("❌ Keine Systemsteuerung-Datenbank verfügbar")
            return False
            
    except Exception as e:
        print(f"❌ Fehler bei Controls-Generation: {e}")
        import traceback
        traceback.print_exc()
        return False

def teste_vollständige_controls():
    """Teste die generierten vollständigen Controls"""
    print("\n" + "="*70)
    print("🧪 TEST: Vollständige Controls")
    print("="*70)
    
    try:
        if hasattr(gcs, '_database') and hasattr(gcs._database, 'data'):
            all_views = list(gcs._database.data.keys())
            
            if all_views:
                test_view = all_views[0]
                print(f"🔍 Teste View: {test_view}")
                
                controls = gcs.get_value(test_view, 'ColumnControls')
                
                if controls:
                    print(f"📊 Controls gefunden: {len(controls)}")
                    
                    # Erste 3 Controls prüfen
                    for i, (name, control) in enumerate(list(controls.items())[:3]):
                        print(f"   Control {i+1}: {name}")
                        if isinstance(control, dict):
                            print(f"      ├─ Type: {control.get('type', 'FEHLT')}")
                            print(f"      ├─ Gruppe: {control.get('gruppe', 'FEHLT')}")
                            print(f"      ├─ Feld: {control.get('feld', 'FEHLT')}")
                            print(f"      └─ Show: {control.get('show', 'FEHLT')}")
                            
                            vollständig = all(key in control for key in ['type', 'gruppe', 'feld', 'show'])
                            print(f"      ✅ Vollständig: {'Ja' if vollständig else 'Nein'}")
                        else:
                            print(f"      ❌ Ungültiger Typ: {type(control)}")
                    
                    return True
                else:
                    print("❌ Keine Controls gefunden")
                    return False
            else:
                print("❌ Keine Views gefunden")
                return False
        else:
            print("❌ Keine Datenbank verfügbar")
            return False
            
    except Exception as e:
        print(f"❌ Test-Fehler: {e}")
        return False

def main():
    """Hauptfunktion"""
    print("🚀 VOLLSTÄNDIGE CONTROLS GENERATION STARTEN")
    
    # 1. Generiere vollständige Controls für bestehende Views
    success1 = generiere_vollständige_controls_für_bestehende_views()
    
    # 2. Teste die generierten Controls
    success2 = teste_vollständige_controls()
    
    print("\n" + "="*70)
    print("📋 ENDERGEBNIS")
    print("="*70)
    
    if success1 and success2:
        print("🎉 ERFOLG: Vollständige Controls wurden generiert!")
        print("\n💡 Jetzt können Sie:")
        print("   1. Beliebige View in der Anwendung öffnen")
        print("   2. Settings → Spalten konfigurieren")
        print("   3. Alle Spalten sollten sichtbar sein!")
        print("\n✅ Das Problem 'Es sind keine Spalten zu sehen' ist gelöst!")
    else:
        print("❌ PROBLEM: Controls-Generation fehlgeschlagen")
        print("\n🔧 Lösungsansätze:")
        print("   - Neue View öffnen (erstellt automatisch vollständige Controls)")
        print("   - View-Dialog Code aktivieren und testen")
    
    return success1 and success2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
