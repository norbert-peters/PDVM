# setup_frame_view_integration.py
"""
Erweitert die framedaten um view_guid für die Dialog-View-Integration
"""

import logging
import json
from pdvm_central_datenbank import PdvmCentralDatenbank

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_frame_view_integration():
    """Erweitert die framedaten um view_guid-Referenzen"""
    
    try:
        # Standard Test-Frame erweitern
        test_frame_guid = "4078079f-4028-45ed-879c-3c779ecf3d0d"
        test_view_guid = "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"  # Persondaten-View
        
        # Framedaten laden
        db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="framedaten",
            guid=test_frame_guid
        )
        
        frame_data = db.lesen()
        if not frame_data:
            logger.info("🔧 Erstelle neue framedaten-Struktur...")
            frame_data = {}
        
        # View-GUID hinzufügen
        if isinstance(frame_data, dict):
            frame_data["view_guid"] = test_view_guid
            frame_data["title"] = "Personendaten Verwaltung"
            frame_data["description"] = "Moderne View für Personendaten mit Search/Sort/Filter"
            
            # Dialog-View-Konfiguration hinzufügen
            if "dialog_view_config" not in frame_data:
                frame_data["dialog_view_config"] = {
                    "enabled": True,
                    "show_new_button": True,
                    "show_edit_button": True,
                    "auto_refresh": True
                }
        else:
            # Falls framedaten in anderem Format vorliegen
            new_frame_data = {
                "view_guid": test_view_guid,
                "title": "Personendaten Verwaltung",
                "description": "Moderne View für Personendaten mit Search/Sort/Filter",
                "dialog_view_config": {
                    "enabled": True,
                    "show_new_button": True,
                    "show_edit_button": True,
                    "auto_refresh": True
                },
                "original_data": frame_data  # Alte Daten beibehalten
            }
            frame_data = new_frame_data
        
        # Aktualisierte framedaten speichern
        db.speichern(test_frame_guid, {test_frame_guid: frame_data})
        
        logger.info(f"✅ Framedaten {test_frame_guid} um view_guid {test_view_guid} erweitert")
        
        # Weitere Beispiel-Frames erstellen (für verschiedene Tabellen)
        example_frames = [
            {
                "guid": "frame-personen-list",
                "view_guid": test_view_guid,
                "title": "Personenliste",
                "table": "persondaten"
            },
            {
                "guid": "frame-finanzen-list", 
                "view_guid": "view-finanzen-guid",  # Würde für Finanztabelle erstellt
                "title": "Finanzdaten",
                "table": "finanzdaten"
            }
        ]
        
        for frame_info in example_frames:
            try:
                frame_db = PdvmCentralDatenbank(
                    db_name="PdvmManager.db",
                    table_name="framedaten",
                    guid=frame_info["guid"]
                )
                
                frame_config = {
                    "view_guid": frame_info["view_guid"],
                    "title": frame_info["title"],
                    "table_name": frame_info["table"],
                    "dialog_view_config": {
                        "enabled": True,
                        "show_new_button": True,
                        "show_edit_button": True,
                        "auto_refresh": True
                    }
                }
                
                frame_db.speichern(frame_info["guid"], {frame_info["guid"]: frame_config})
                logger.info(f"✅ Beispiel-Frame erstellt: {frame_info['guid']} → {frame_info['title']}")
                
            except Exception as e:
                logger.warning(f"⚠️ Fehler beim Erstellen von Beispiel-Frame {frame_info['guid']}: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Setup der Frame-View-Integration: {e}")
        return False

def show_frame_view_configuration():
    """Zeigt die aktuellen Frame-View-Konfigurationen an"""
    
    test_frame_guid = "4078079f-4028-45ed-879c-3c779ecf3d0d"
    
    try:
        db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="framedaten",
            guid=test_frame_guid
        )
        
        frame_data = db.lesen()
        
        print(f"\n📋 Frame-View-Konfiguration für {test_frame_guid}:")
        print("=" * 60)
        
        if frame_data:
            if isinstance(frame_data, dict):
                print(f"View-GUID: {frame_data.get('view_guid', 'Nicht gesetzt')}")
                print(f"Titel: {frame_data.get('title', 'Nicht gesetzt')}")
                print(f"Beschreibung: {frame_data.get('description', 'Nicht gesetzt')}")
                
                dialog_config = frame_data.get('dialog_view_config', {})
                print(f"\nDialog-View-Konfiguration:")
                print(f"  Aktiviert: {dialog_config.get('enabled', False)}")
                print(f"  Neu-Button: {dialog_config.get('show_new_button', False)}")
                print(f"  Bearbeiten-Button: {dialog_config.get('show_edit_button', False)}")
                print(f"  Auto-Refresh: {dialog_config.get('auto_refresh', False)}")
            else:
                print(f"Datenstruktur: {type(frame_data)}")
                print(f"Inhalt: {frame_data}")
        else:
            print("❌ Keine framedaten gefunden")
            
    except Exception as e:
        logger.error(f"❌ Fehler beim Anzeigen der Konfiguration: {e}")

if __name__ == "__main__":
    print("🔗 Frame-View-Integration Setup")
    print("=" * 40)
    
    # Setup ausführen
    if setup_frame_view_integration():
        print("✅ Frame-View-Integration erfolgreich eingerichtet!")
    else:
        print("❌ Fehler beim Setup der Frame-View-Integration")
    
    # Aktuelle Konfiguration anzeigen
    show_frame_view_configuration()
    
    print("\n🎯 Verwendung in der Hauptanwendung:")
    print("   self.pdvm_dialog_with_view()          ← Standard Test-Frame")
    print("   self.pdvm_dialog_with_view('frame-personen-list')  ← Spezifischer Frame")
    print("\n📊 Das View-Widget lädt automatisch die view_guid aus den framedaten!")
    print("💡 Verschiedene Frames können verschiedene Views/Tabellen laden")
