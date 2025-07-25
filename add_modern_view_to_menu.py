# add_modern_view_to_menu.py
"""
Fügt das moderne View-Widget zum Testbereich-Menü hinzu
"""

import json
import logging
from pdvm_central_datenbank import PdvmCentralDatenbank

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_modern_view_menu():
    """Fügt die modernen View-Funktionen zum Testbereich-Menü hinzu"""
    
    try:
        # Menüdaten laden
        db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="menudata",
            guid="5ca6674e-b9ce-4581-9756-64e742883f80"  # Startmenü-GUID
        )
        
        menu_raw = db.lesen()
        if not menu_raw:
            logger.error("❌ Keine Menüdaten gefunden!")
            return False
        
        # JSON parsen
        menu_data = json.loads(menu_raw["5ca6674e-b9ce-4581-9756-64e742883f80"])
        
        # Testbereich finden
        testbereich = None
        for group in menu_data.get("groups", []):
            if group.get("name") == "Testbereich":
                testbereich = group
                break
        
        if not testbereich:
            logger.error("❌ Testbereich-Gruppe nicht gefunden!")
            return False
        
        # Neue View-Menüpunkte hinzufügen
        new_items = [
            {
                "name": "📊 Modernes View-Widget (Demo)",
                "command": "self.pdvm_setup_demo_view()",
                "description": "Erstellt Demo-Daten und lädt das moderne View-Widget"
            },
            {
                "name": "📊 Modernes View-Widget (Direkt)",
                "command": "self.pdvm_modern_view_test()",
                "description": "Lädt das moderne View-Widget direkt"
            },
            {
                "name": "🔍 View-Widget (Persondaten)",
                "command": "self.pdvm_modern_view_test('0d10a0d0-b1a5-4544-b284-e8a09ca979b5')",
                "description": "Moderne View für Persondaten mit Search/Sort/Filter"
            }
        ]
        
        # Menüpunkte zu Testbereich hinzufügen
        if "items" not in testbereich:
            testbereich["items"] = []
        
        # Prüfen ob bereits vorhanden
        existing_names = [item.get("name", "") for item in testbereich["items"]]
        
        added_count = 0
        for new_item in new_items:
            if new_item["name"] not in existing_names:
                testbereich["items"].append(new_item)
                added_count += 1
                logger.info(f"✅ Hinzugefügt: {new_item['name']}")
            else:
                logger.info(f"⚠️ Bereits vorhanden: {new_item['name']}")
        
        if added_count > 0:
            # Aktualisierte Menüdaten speichern
            updated_raw = {
                "5ca6674e-b9ce-4581-9756-64e742883f80": json.dumps(menu_data, ensure_ascii=False, indent=2)
            }
            
            db.speichern("5ca6674e-b9ce-4581-9756-64e742883f80", updated_raw)
            logger.info(f"💾 Menü aktualisiert - {added_count} neue Einträge hinzugefügt")
        else:
            logger.info("ℹ️ Alle View-Menüpunkte bereits vorhanden")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Hinzufügen der View-Menüpunkte: {e}")
        return False

def show_testbereich_menu():
    """Zeigt alle Testbereich-Menüpunkte an"""
    try:
        db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="menudata",
            guid="5ca6674e-b9ce-4581-9756-64e742883f80"
        )
        
        menu_raw = db.lesen()
        if not menu_raw:
            logger.error("❌ Keine Menüdaten gefunden!")
            return
        
        menu_data = json.loads(menu_raw["5ca6674e-b9ce-4581-9756-64e742883f80"])
        
        # Testbereich finden und anzeigen
        for group in menu_data.get("groups", []):
            if group.get("name") == "Testbereich":
                print(f"\n🎯 {group['name']} Menüpunkte:")
                print("=" * 50)
                
                for i, item in enumerate(group.get("items", []), 1):
                    name = item.get("name", "Unbenannt")
                    command = item.get("command", "")
                    description = item.get("description", "")
                    
                    print(f"{i:2d}. {name}")
                    if description:
                        print(f"    📝 {description}")
                    print(f"    🔧 {command}")
                    print()
                
                break
        else:
            logger.error("❌ Testbereich-Gruppe nicht gefunden!")
            
    except Exception as e:
        logger.error(f"❌ Fehler beim Anzeigen der Menüpunkte: {e}")

if __name__ == "__main__":
    print("🚀 Moderne View-Widget Integration")
    print("=" * 40)
    
    # Menüpunkte hinzufügen
    if add_modern_view_menu():
        print("\n✅ View-Widget erfolgreich zum Testbereich-Menü hinzugefügt!")
    else:
        print("\n❌ Fehler beim Hinzufügen der View-Menüpunkte")
    
    # Aktuellen Testbereich anzeigen
    print("\n📋 Aktuelle Testbereich-Menüpunkte:")
    show_testbereich_menu()
    
    print("\n🎯 Verwendung in der Hauptanwendung:")
    print("   1. Starten Sie die Hauptanwendung")
    print("   2. Öffnen Sie das Testbereich-Menü")
    print("   3. Wählen Sie einen der neuen View-Menüpunkte:")
    print("      📊 Modernes View-Widget (Demo)    ← Empfohlen für ersten Test")
    print("      📊 Modernes View-Widget (Direkt)")
    print("      🔍 View-Widget (Persondaten)")
