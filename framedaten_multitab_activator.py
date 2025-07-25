# framedaten_multitab_activator.py
# -*- coding: utf-8 -*-

"""
Multi-Tab Framedaten Activator
=============================

Einfaches Tool zum Aktivieren/Deaktivieren von Multi-Tab für Framedaten
"""

import json
import logging

# Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def show_required_framedaten_structure():
    """Zeigt die erforderliche Struktur für Multi-Tab in framedaten"""
    
    print("=" * 60)
    print("ERFORDERLICHE FRAMEDATEN-STRUKTUR FÜR MULTI-TAB")
    print("=" * 60)
    print()
    
    required_structure = {
        "frame_guid": "Ihre-Frame-GUID-hier",
        "frame_name": "Name des Frames",
        
        # ===== WICHTIG: Multi-Tab-Konfiguration =====
        "multi_tab_config": {
            "multi_tab_enabled": True,          # 🔑 HAUPTSCHALTER für Multi-Tab
            "max_tabs_display": 3,              # Anzahl Tabs parallel (2-4)
            "layout_orientation": "horizontal", # "horizontal" oder "vertical"
            "tab_selection_mode": "smart",      # "smart", "manual", "all"
            "allow_user_override": True,        # Benutzer kann Einstellungen ändern
            "default_active": False,            # Beim Laden automatisch aktivieren
            "supported_layouts": ["horizontal", "vertical"],
            "max_tabs_limit": 4,
            "min_tabs_limit": 2,
            "config_source": "framedaten",
            "version": "1.0"
        },
        
        # ===== OPTIONAL: Tab-Definitionen erweitern =====
        "tabs": [
            {
                "tab_id": "stammdaten",
                "tab_name": "Stammdaten", 
                "tab_icon": "👤",
                "tab_order": 1,
                "multi_tab_eligible": True,     # 🔑 Tab für Multi-Tab freigeben
                "preferred_position": "left"    # "left", "center", "right"
            },
            {
                "tab_id": "geschaeft",
                "tab_name": "Geschäft",
                "tab_icon": "💼", 
                "tab_order": 2,
                "multi_tab_eligible": True,
                "preferred_position": "center"
            }
        ],
        
        # ===== OPTIONAL: Multi-Tab-Presets =====
        "multi_tab_presets": {
            "default_2_tabs": {
                "name": "Standard (2 Tabs)",
                "description": "Stammdaten + Geschäft",
                "layout": "horizontal",
                "tabs": ["stammdaten", "geschaeft"],
                "sizes": [50, 50]
            }
        }
    }
    
    print("MINIMAL-KONFIGURATION (nur das Wichtigste):")
    print("-" * 40)
    minimal_config = {
        "multi_tab_config": {
            "multi_tab_enabled": True,
            "max_tabs_display": 2,
            "layout_orientation": "horizontal"
        }
    }
    print(json.dumps(minimal_config, indent=2, ensure_ascii=False))
    print()
    
    print("VOLLSTÄNDIGE KONFIGURATION:")
    print("-" * 40) 
    print(json.dumps(required_structure, indent=2, ensure_ascii=False))
    print()
    
    print("WICHTIGE EIGENSCHAFTEN:")
    print("-" * 20)
    print("🔑 multi_tab_enabled: True/False - HAUPTSCHALTER")
    print("📊 max_tabs_display: 2-4 - Anzahl paralleler Tabs")
    print("📐 layout_orientation: 'horizontal'/'vertical'")
    print("🎯 tab_selection_mode: 'smart' (empfohlen)")
    print("✅ multi_tab_eligible: True - je Tab einzeln freischalten")
    print()

def activate_multitab_for_frame(frame_guid, enable=True):
    """Aktiviert Multi-Tab für einen spezifischen Frame"""
    try:
        from pdvm_central_datenbank import PdvmCentralDatenbank
        
        logger.info(f"🔧 {'Aktiviere' if enable else 'Deaktiviere'} Multi-Tab für Frame: {frame_guid}")
        
        # Frame-Daten laden
        db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="framedaten",
            guid=frame_guid
        )
        
        frame_data = db.lesen()
        if not frame_data:
            logger.error(f"❌ Frame {frame_guid} nicht gefunden!")
            return False
        
        # Multi-Tab-Konfiguration hinzufügen/aktualisieren
        if "multi_tab_config" not in frame_data:
            frame_data["multi_tab_config"] = {}
        
        # Basis-Konfiguration setzen
        frame_data["multi_tab_config"].update({
            "multi_tab_enabled": enable,
            "max_tabs_display": 3 if enable else 2,
            "layout_orientation": "horizontal",
            "tab_selection_mode": "smart",
            "allow_user_override": True,
            "default_active": False,
            "config_source": "manual_activation",
            "version": "1.0"
        })
        
        # Tabs für Multi-Tab vorbereiten falls vorhanden
        if "tabs" in frame_data:
            for tab in frame_data["tabs"]:
                if "multi_tab_eligible" not in tab:
                    tab["multi_tab_eligible"] = enable
                if "preferred_position" not in tab:
                    order = tab.get("tab_order", 1)
                    if order == 1:
                        tab["preferred_position"] = "left"
                    elif order == 2: 
                        tab["preferred_position"] = "center"
                    else:
                        tab["preferred_position"] = "right"
        
        # Speichern
        db.speichern(frame_guid, frame_data)
        
        status = "✅ AKTIVIERT" if enable else "❌ DEAKTIVIERT"
        logger.info(f"{status} Multi-Tab für Frame {frame_guid}")
        
        if enable:
            logger.info("📱 Frame ist jetzt Multi-Tab-fähig!")
            logger.info("🎛️ Benutzer können F4 für Multi-Tab-Modus verwenden")
        else:
            logger.info("📄 Frame verwendet Standard-Dialog")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler: {e}")
        return False

def check_frame_multitab_status(frame_guid):
    """Prüft den Multi-Tab-Status eines Frames"""
    try:
        from pdvm_central_datenbank import PdvmCentralDatenbank
        
        db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="framedaten",
            guid=frame_guid
        )
        
        frame_data = db.lesen()
        if not frame_data:
            logger.warning(f"⚠️ Frame {frame_guid} nicht gefunden")
            return None
        
        multi_tab_config = frame_data.get("multi_tab_config", {})
        enabled = multi_tab_config.get("multi_tab_enabled", False)
        max_tabs = multi_tab_config.get("max_tabs_display", 2)
        layout = multi_tab_config.get("layout_orientation", "horizontal")
        
        print(f"\n📊 MULTI-TAB-STATUS für Frame {frame_guid}:")
        print("-" * 50)
        print(f"🎛️ Multi-Tab: {'✅ AKTIVIERT' if enabled else '❌ DEAKTIVIERT'}")
        print(f"📱 Max. Tabs: {max_tabs}")
        print(f"📐 Layout: {layout}")
        
        if "tabs" in frame_data:
            eligible_tabs = [tab for tab in frame_data["tabs"] if tab.get("multi_tab_eligible", False)]
            print(f"✅ Multi-Tab-fähige Tabs: {len(eligible_tabs)}")
            for tab in eligible_tabs:
                print(f"   • {tab.get('tab_icon', '📝')} {tab.get('tab_name', 'Unbenannt')}")
        
        return enabled
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Prüfen: {e}")
        return None

def quick_setup_demo_frame():
    """Erstellt schnell einen Demo-Frame für Multi-Tab-Tests"""
    
    demo_frame_guid = "4078079f-4028-45ed-879c-3c779ecf3d0d"
    logger.info(f"🔧 Erstelle Demo-Frame für Multi-Tab: {demo_frame_guid}")
    
    try:
        from pdvm_central_datenbank import PdvmCentralDatenbank
        
        db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="framedaten",
            guid=demo_frame_guid
        )
        
        # Demo-Frame-Daten
        demo_frame_data = {
            "frame_guid": demo_frame_guid,
            "frame_name": "Multi-Tab Demo Frame",
            "frame_version": "3.0",
            
            # Multi-Tab-Konfiguration
            "multi_tab_config": {
                "multi_tab_enabled": True,
                "max_tabs_display": 3,
                "layout_orientation": "horizontal",
                "tab_selection_mode": "smart",
                "allow_user_override": True,
                "default_active": False,
                "supported_layouts": ["horizontal", "vertical"],
                "config_source": "demo_setup",
                "version": "1.0"
            },
            
            # Demo-Tabs
            "tabs": [
                {
                    "tab_id": "stammdaten",
                    "tab_name": "Stammdaten",
                    "tab_icon": "👤",
                    "tab_order": 1,
                    "multi_tab_eligible": True,
                    "preferred_position": "left"
                },
                {
                    "tab_id": "geschaeft",
                    "tab_name": "Geschäft", 
                    "tab_icon": "💼",
                    "tab_order": 2,
                    "multi_tab_eligible": True,
                    "preferred_position": "center"
                },
                {
                    "tab_id": "zusatz",
                    "tab_name": "Zusatz",
                    "tab_icon": "📋",
                    "tab_order": 3,
                    "multi_tab_eligible": True,
                    "preferred_position": "right"
                },
                {
                    "tab_id": "dokumente",
                    "tab_name": "Dokumente",
                    "tab_icon": "📎",
                    "tab_order": 4,
                    "multi_tab_eligible": True,
                    "preferred_position": "right"
                }
            ],
            
            # Multi-Tab-Presets
            "multi_tab_presets": {
                "default_2_tabs": {
                    "name": "Standard (2 Tabs)",
                    "description": "Stammdaten + Geschäft",
                    "layout": "horizontal",
                    "tabs": ["stammdaten", "geschaeft"],
                    "sizes": [50, 50]
                },
                "complete_3_tabs": {
                    "name": "Komplett (3 Tabs)",
                    "description": "Stammdaten + Geschäft + Zusatz",
                    "layout": "horizontal",
                    "tabs": ["stammdaten", "geschaeft", "zusatz"],
                    "sizes": [33, 33, 34]
                }
            }
        }
        
        # Speichern
        db.speichern(demo_frame_guid, demo_frame_data)
        
        logger.info("✅ Demo-Frame erfolgreich erstellt!")
        logger.info(f"📱 Frame-GUID: {demo_frame_guid}")
        logger.info("🎛️ Multi-Tab ist AKTIVIERT")
        logger.info(f"📊 {len(demo_frame_data['tabs'])} Tabs verfügbar")
        
        return demo_frame_guid
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen des Demo-Frames: {e}")
        return None

if __name__ == "__main__":
    print("🔧 Multi-Tab Framedaten Activator")
    print("=" * 40)
    print()
    print("Was möchten Sie tun?")
    print("1. 📖 Erforderliche Framedaten-Struktur anzeigen")
    print("2. ✅ Multi-Tab für Frame aktivieren")
    print("3. ❌ Multi-Tab für Frame deaktivieren")
    print("4. 📊 Multi-Tab-Status eines Frames prüfen")
    print("5. 🎯 Demo-Frame für Tests erstellen")
    print()
    
    try:
        choice = input("Ihre Wahl (1-5): ").strip()
        
        if choice == "1":
            show_required_framedaten_structure()
            
        elif choice == "2":
            frame_guid = input("Frame-GUID eingeben: ").strip()
            if frame_guid:
                activate_multitab_for_frame(frame_guid, enable=True)
            else:
                print("❌ Keine Frame-GUID eingegeben")
                
        elif choice == "3":
            frame_guid = input("Frame-GUID eingeben: ").strip()
            if frame_guid:
                activate_multitab_for_frame(frame_guid, enable=False)
            else:
                print("❌ Keine Frame-GUID eingegeben")
                
        elif choice == "4":
            frame_guid = input("Frame-GUID eingeben: ").strip()
            if frame_guid:
                check_frame_multitab_status(frame_guid)
            else:
                print("❌ Keine Frame-GUID eingegeben")
                
        elif choice == "5":
            demo_guid = quick_setup_demo_frame()
            if demo_guid:
                print(f"\n🎉 Demo-Frame erstellt: {demo_guid}")
                print("💡 Verwenden Sie diesen Frame in pdvm_dialog() für Tests")
                
        else:
            print("❌ Ungültige Auswahl")
            
    except KeyboardInterrupt:
        print("\n🛑 Abgebrochen")
    except Exception as e:
        print(f"❌ Fehler: {e}")
