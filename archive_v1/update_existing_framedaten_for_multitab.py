# update_existing_framedaten_for_multitab.py
# -*- coding: utf-8 -*-

"""
Tool zum Aktualisieren bestehender Framedaten für Multi-Tab-Support
=================================================================

Dieses Tool erweitert existierende framedaten-Einträge um Multi-Tab-Konfiguration
"""

import json
import logging
from typing import Dict, Any, List

# Logger
logger = logging.getLogger(__name__)

def get_all_frame_guids():
    """Holt alle Frame-GUIDs aus der framedaten-Tabelle"""
    try:
        from pdvm_central_datenbank import PdvmCentralDatenbank
        
        # Direkt auf die Datenbank zugreifen um alle Einträge zu bekommen
        db = PdvmCentralDatenbank(
            db_name="PdvmManager.db", 
            table_name="framedaten"
        )
        
        # Alle verfügbaren GUIDs auflisten
        # Da die Klasse GUID-basiert ist, müssen wir eine andere Methode verwenden
        # Wir versuchen bekannte Frame-GUIDs oder fragen nach allen
        
        # Bekannte Frame-GUIDs (diese sollten in Ihrem System vorhanden sein)
        known_frame_guids = [
            "4078079f-4028-45ed-879c-3c779ecf3d0d",  # Enhanced Multi-Tab Demo Frame
            # Hier können weitere Frame-GUIDs aus Ihrem System hinzugefügt werden
        ]
        
        existing_guids = []
        for guid in known_frame_guids:
            try:
                test_db = PdvmCentralDatenbank(
                    db_name="PdvmManager.db",
                    table_name="framedaten", 
                    guid=guid
                )
                data = test_db.lesen()
                if data:
                    existing_guids.append(guid)
                    logger.info(f"✅ Frame-GUID gefunden: {guid}")
                else:
                    logger.info(f"❌ Frame-GUID nicht gefunden: {guid}")
            except Exception as e:
                logger.warning(f"⚠️ Fehler beim Prüfen von {guid}: {e}")
        
        return existing_guids
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Abrufen der Frame-GUIDs: {e}")
        return []

def add_multi_tab_config_to_frame(frame_guid: str, enable_multi_tab: bool = True, max_tabs: int = 3):
    """Fügt Multi-Tab-Konfiguration zu einem bestehenden Frame hinzu"""
    try:
        from pdvm_central_datenbank import PdvmCentralDatenbank
        
        # Frame-Daten laden
        db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="framedaten",
            guid=frame_guid
        )
        
        frame_data = db.lesen()
        if not frame_data:
            logger.warning(f"⚠️ Keine framedaten für {frame_guid} gefunden")
            return False
        
        # Multi-Tab-Konfiguration hinzufügen/aktualisieren
        multi_tab_config = {
            "multi_tab_enabled": enable_multi_tab,
            "max_tabs_display": max_tabs,
            "layout_orientation": "horizontal",
            "tab_selection_mode": "smart",
            "allow_user_override": True,
            "default_active": False,
            "supported_layouts": ["horizontal", "vertical"],
            "max_tabs_limit": 4,
            "min_tabs_limit": 2,
            "config_source": "auto_update",
            "version": "1.0"
        }
        
        # In Frame-Daten einfügen
        frame_data["multi_tab_config"] = multi_tab_config
        
        # Wenn noch keine Tab-Informationen vorhanden, Standard-Tabs hinzufügen
        if "tabs" not in frame_data:
            frame_data["tabs"] = create_default_tab_structure()
        else:
            # Bestehende Tabs für Multi-Tab erweitern
            update_existing_tabs_for_multi_tab(frame_data["tabs"])
        
        # Multi-Tab-Presets hinzufügen falls nicht vorhanden
        if "multi_tab_presets" not in frame_data:
            frame_data["multi_tab_presets"] = create_default_multi_tab_presets()
        
        # Aktualisierte Daten speichern
        db.speichern(frame_guid, frame_data)
        
        logger.info(f"✅ Multi-Tab-Konfiguration für Frame {frame_guid} {'aktiviert' if enable_multi_tab else 'deaktiviert'}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Aktualisieren von Frame {frame_guid}: {e}")
        return False

def create_default_tab_structure():
    """Erstellt eine Standard-Tab-Struktur für Multi-Tab"""
    return [
        {
            "tab_id": "stammdaten",
            "tab_name": "Stammdaten",
            "tab_icon": "👤",
            "tab_order": 1,
            "tab_type": "inputframe",
            "multi_tab_eligible": True,
            "preferred_position": "left"
        },
        {
            "tab_id": "details",
            "tab_name": "Details",
            "tab_icon": "📋",
            "tab_order": 2,
            "tab_type": "inputframe",
            "multi_tab_eligible": True,
            "preferred_position": "center"
        },
        {
            "tab_id": "zusatz",
            "tab_name": "Zusatz",
            "tab_icon": "📝",
            "tab_order": 3,
            "tab_type": "inputframe",
            "multi_tab_eligible": True,
            "preferred_position": "right"
        }
    ]

def update_existing_tabs_for_multi_tab(tabs: List[Dict[str, Any]]):
    """Erweitert bestehende Tabs um Multi-Tab-Eigenschaften"""
    for tab in tabs:
        # Multi-Tab-Eigenschaften hinzufügen falls nicht vorhanden
        if "multi_tab_eligible" not in tab:
            tab["multi_tab_eligible"] = True
        
        if "preferred_position" not in tab:
            # Position basierend auf tab_order bestimmen
            order = tab.get("tab_order", 1)
            if order == 1:
                tab["preferred_position"] = "left"
            elif order <= 2:
                tab["preferred_position"] = "center"
            else:
                tab["preferred_position"] = "right"

def create_default_multi_tab_presets():
    """Erstellt Standard-Multi-Tab-Presets"""
    return {
        "default_2_tabs": {
            "name": "Standard (2 Tabs)",
            "description": "Stammdaten + Details",
            "layout": "horizontal",
            "tabs": ["stammdaten", "details"],
            "sizes": [50, 50]
        },
        "complete_3_tabs": {
            "name": "Komplett (3 Tabs)",
            "description": "Stammdaten + Details + Zusatz",
            "layout": "horizontal",
            "tabs": ["stammdaten", "details", "zusatz"],
            "sizes": [33, 33, 34]
        },
        "work_vertical": {
            "name": "Arbeitsbereich (vertikal)",
            "description": "Stammdaten oben, Details unten",
            "layout": "vertical",
            "tabs": ["stammdaten", "details"],
            "sizes": [70, 30]
        }
    }

def update_all_frames_for_multi_tab():
    """Aktualisiert alle gefundenen Frames für Multi-Tab-Support"""
    logger.info("🔧 === Multi-Tab-Update für alle Frames ===")
    
    # Alle Frame-GUIDs holen
    frame_guids = get_all_frame_guids()
    
    if not frame_guids:
        logger.warning("⚠️ Keine Frame-GUIDs gefunden zum Aktualisieren")
        return False
    
    logger.info(f"📊 {len(frame_guids)} Frame(s) gefunden zum Aktualisieren")
    
    success_count = 0
    for frame_guid in frame_guids:
        logger.info(f"🔧 Aktualisiere Frame: {frame_guid}")
        
        if add_multi_tab_config_to_frame(frame_guid, enable_multi_tab=True, max_tabs=3):
            success_count += 1
        else:
            logger.error(f"❌ Fehler beim Aktualisieren von {frame_guid}")
    
    logger.info(f"✅ {success_count}/{len(frame_guids)} Frames erfolgreich aktualisiert")
    
    if success_count > 0:
        logger.info("🎉 Multi-Tab-Update abgeschlossen!")
        logger.info("📱 Frames sind jetzt Multi-Tab-fähig")
        logger.info("⚙️ Benutzer können Multi-Tab in den Dialog-Widgets aktivieren")
    
    return success_count == len(frame_guids)

def enable_multi_tab_for_specific_frame(frame_guid: str):
    """Aktiviert Multi-Tab für einen spezifischen Frame"""
    logger.info(f"🔧 === Multi-Tab-Aktivierung für Frame {frame_guid} ===")
    
    if add_multi_tab_config_to_frame(frame_guid, enable_multi_tab=True, max_tabs=3):
        logger.info(f"✅ Multi-Tab für Frame {frame_guid} erfolgreich aktiviert")
        logger.info("📱 Frame ist jetzt Multi-Tab-fähig")
        logger.info("🎛️ Benutzer können F4 für Multi-Tab-Modus verwenden")
        return True
    else:
        logger.error(f"❌ Fehler beim Aktivieren von Multi-Tab für Frame {frame_guid}")
        return False

def disable_multi_tab_for_specific_frame(frame_guid: str):
    """Deaktiviert Multi-Tab für einen spezifischen Frame"""
    logger.info(f"🔧 === Multi-Tab-Deaktivierung für Frame {frame_guid} ===")
    
    if add_multi_tab_config_to_frame(frame_guid, enable_multi_tab=False, max_tabs=2):
        logger.info(f"✅ Multi-Tab für Frame {frame_guid} erfolgreich deaktiviert")
        logger.info("📄 Frame verwendet Standard-Dialog-Widget")
        return True
    else:
        logger.error(f"❌ Fehler beim Deaktivieren von Multi-Tab für Frame {frame_guid}")
        return False

def show_frame_multi_tab_status():
    """Zeigt den Multi-Tab-Status aller Frames an"""
    logger.info("📊 === Multi-Tab-Status aller Frames ===")
    
    frame_guids = get_all_frame_guids()
    
    if not frame_guids:
        logger.warning("⚠️ Keine Frames gefunden")
        return
    
    for frame_guid in frame_guids:
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            
            db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="framedaten",
                guid=frame_guid
            )
            
            frame_data = db.lesen()
            if frame_data:
                multi_tab_config = frame_data.get("multi_tab_config", {})
                enabled = multi_tab_config.get("multi_tab_enabled", False)
                max_tabs = multi_tab_config.get("max_tabs_display", 2)
                layout = multi_tab_config.get("layout_orientation", "horizontal")
                
                status_icon = "✅" if enabled else "❌"
                logger.info(f"{status_icon} {frame_guid}: Multi-Tab {'ON' if enabled else 'OFF'} (max: {max_tabs}, {layout})")
            else:
                logger.info(f"❓ {frame_guid}: Keine Daten gefunden")
                
        except Exception as e:
            logger.error(f"❌ {frame_guid}: Fehler beim Abrufen - {e}")

if __name__ == "__main__":
    # Logging konfigurieren
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    print("🔧 Multi-Tab Framedaten Update Tool")
    print("===================================")
    print()
    print("Was möchten Sie tun?")
    print("1. Alle Frames für Multi-Tab aktualisieren")
    print("2. Multi-Tab für spezifischen Frame aktivieren")
    print("3. Multi-Tab für spezifischen Frame deaktivieren") 
    print("4. Multi-Tab-Status aller Frames anzeigen")
    print()
    
    try:
        choice = input("Ihre Wahl (1-4): ").strip()
        
        if choice == "1":
            update_all_frames_for_multi_tab()
        elif choice == "2":
            frame_guid = input("Frame-GUID eingeben: ").strip()
            if frame_guid:
                enable_multi_tab_for_specific_frame(frame_guid)
            else:
                print("❌ Keine gültige Frame-GUID eingegeben")
        elif choice == "3":
            frame_guid = input("Frame-GUID eingeben: ").strip()
            if frame_guid:
                disable_multi_tab_for_specific_frame(frame_guid)
            else:
                print("❌ Keine gültige Frame-GUID eingegeben")
        elif choice == "4":
            show_frame_multi_tab_status()
        else:
            print("❌ Ungültige Auswahl")
            
    except KeyboardInterrupt:
        print("\n🛑 Abgebrochen")
    except Exception as e:
        print(f"❌ Fehler: {e}")
