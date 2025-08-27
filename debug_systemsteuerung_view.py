#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug-Tool: Prüft Systemsteuerung-Daten für ViewManager
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def debug_systemsteuerung_view_data(central_systemsteuerung, view_guid, user_guid):
    """
    Debug-Funktion: Prüft alle relevanten Daten in der Systemsteuerung
    """
    print("🔍 DEBUG: Systemsteuerung-Daten für ViewManager")
    print("=" * 60)
    
    try:
        # 1. Zentrale Systemsteuerung-Info
        print(f"📋 Zentrale Systemsteuerung:")
        print(f"   Typ: {type(central_systemsteuerung)}")
        print(f"   Tabelle: {getattr(central_systemsteuerung, 'table_name', 'Unbekannt')}")
        print(f"   GUID: {getattr(central_systemsteuerung, 'guid', 'Unbekannt')}")
        print(f"   Historisch: {getattr(central_systemsteuerung, 'historisch', 'Unbekannt')}")
        
        # 2. View-GUID und User-GUID
        print(f"\n📋 GUIDs:")
        print(f"   view_guid: {view_guid}")
        print(f"   user_guid: {user_guid}")
        
        # 3. Prüfe Display_View_Control_Struktur
        print(f"\n🔍 Prüfe Display_View_Control_Struktur:")
        control_data = central_systemsteuerung.get_value(
            gruppe=view_guid,
            feld="display_view_control",
            ab_zeit=None
        )
        
        if control_data and control_data.get("wert"):
            print(f"   ✅ GEFUNDEN in Gruppe={view_guid}")
            print(f"   Typ: {type(control_data.get('wert'))}")
            
            # Wenn es ein Dict ist, zeige Struktur
            if isinstance(control_data.get("wert"), dict):
                control_dict = control_data.get("wert")
                print(f"   Columns: {len(control_dict.get('columns', []))}")
                print(f"   Metadata: {bool(control_dict.get('metadata'))}")
                
                # Erste paar Spalten anzeigen
                columns = control_dict.get('columns', [])[:3]
                for i, col in enumerate(columns):
                    print(f"   Spalte {i+1}: {col.get('name', 'Unbekannt')} (show={col.get('show', False)})")
            else:
                print(f"   Inhalt (ersten 100 Zeichen): {str(control_data.get('wert'))[:100]}...")
        else:
            print(f"   ❌ NICHT GEFUNDEN in Gruppe={view_guid}")
        
        # 4. Prüfe andere Daten in der view_guid-Gruppe
        print(f"\n🔍 Prüfe andere Felder in Gruppe={view_guid}:")
        try:
            # Alle Daten für diese Gruppe laden (direkt aus der Instanz)
            all_data = central_systemsteuerung.lesen()
            view_gruppe_data = all_data.get(view_guid, {})
            
            if view_gruppe_data:
                print(f"   ✅ Gruppe {view_guid} hat {len(view_gruppe_data)} Felder:")
                for feld_name in list(view_gruppe_data.keys())[:5]:  # Erste 5 Felder
                    print(f"     - {feld_name}")
                if len(view_gruppe_data) > 5:
                    print(f"     ... und {len(view_gruppe_data) - 5} weitere")
            else:
                print(f"   ❌ Gruppe {view_guid} ist leer oder existiert nicht")
                
        except Exception as e:
            print(f"   ❌ Fehler beim Laden der Gruppen-Daten: {e}")
        
        # 5. Prüfe user_guid-Gruppe
        print(f"\n🔍 Prüfe user_guid-Gruppe={user_guid}:")
        try:
            all_data = central_systemsteuerung.lesen()
            user_gruppe_data = all_data.get(user_guid, {})
            
            if user_gruppe_data:
                print(f"   ✅ Gruppe {user_guid} hat {len(user_gruppe_data)} Felder:")
                for feld_name in list(user_gruppe_data.keys())[:5]:  # Erste 5 Felder
                    print(f"     - {feld_name}")
                if len(user_gruppe_data) > 5:
                    print(f"     ... und {len(user_gruppe_data) - 5} weitere")
            else:
                print(f"   ❌ Gruppe {user_guid} ist leer oder existiert nicht")
                
        except Exception as e:
            print(f"   ❌ Fehler beim Laden der User-Gruppen-Daten: {e}")
        
        # 6. Alle Top-Level-Gruppen anzeigen
        print(f"\n🔍 Alle verfügbaren Gruppen in Systemsteuerung:")
        try:
            all_data = central_systemsteuerung.lesen()
            if all_data:
                print(f"   Gefundene Gruppen ({len(all_data)}):")
                for gruppe_name in list(all_data.keys())[:10]:  # Erste 10 Gruppen
                    gruppe_size = len(all_data[gruppe_name]) if isinstance(all_data[gruppe_name], dict) else 1
                    print(f"     - {gruppe_name} ({gruppe_size} Felder)")
                if len(all_data) > 10:
                    print(f"     ... und {len(all_data) - 10} weitere Gruppen")
            else:
                print(f"   ❌ Keine Daten in Systemsteuerung gefunden")
                
        except Exception as e:
            print(f"   ❌ Fehler beim Laden aller Gruppen: {e}")
        
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Debug der Systemsteuerung: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🔧 Debug-Tool für Systemsteuerung-ViewManager-Integration")
    print("Verwende diese Funktion in deiner Hauptanwendung:")
    print("debug_systemsteuerung_view_data(self.central_systemsteuerung, view_guid, self.user_guid)")
