# setup_multi_tab_framedaten.py
# -*- coding: utf-8 -*-

"""
Setup für Multi-Tab-Konfiguration in Framedaten
===============================================

Erstellt Demo-Konfiguration für Multi-Tab-Funktionalität in der framedaten-Tabelle
"""

import json
import logging
from typing import Dict, Any

# Logger
logger = logging.getLogger(__name__)

def create_multi_tab_framedaten_config():
    """Erstellt Multi-Tab-Konfiguration für framedaten"""
    
    # Multi-Tab-Konfiguration
    multi_tab_config = {
        "multi_tab_enabled": True,
        "max_tabs_display": 3,  # Erlaubt 2-3 Tabs parallel
        "layout_orientation": "horizontal",
        "tab_selection_mode": "smart",  # Smart-Auswahl basierend auf aktivem Tab
        "allow_user_override": True,
        "default_active": False,
        "supported_layouts": ["horizontal", "vertical"],
        "max_tabs_limit": 4,
        "min_tabs_limit": 2,
        "config_source": "framedaten",
        "version": "1.0"
    }
    
    # Erweiterte Frame-Daten mit Multi-Tab-Support
    framedaten_structure = {
        "frame_guid": "4078079f-4028-45ed-879c-3c779ecf3d0d",
        "frame_name": "Enhanced Multi-Tab Demo Frame",
        "frame_version": "3.0",
        "view_guid": "test-view-guid",
        "view_name": "Multi-Tab Test View",
        
        # Dialog-Konfiguration
        "dialog_config": {
            "dialog_type": "enhanced_unified_tab_dialog",
            "width": 1000,
            "height": 700,
            "resizable": True,
            "show_status_bar": True,
            "show_toolbar": True
        },
        
        # Multi-Tab-Konfiguration
        "multi_tab_config": multi_tab_config,
        
        # Tab-Strukturen
        "tabs": [
            {
                "tab_id": "stammdaten",
                "tab_name": "Stammdaten",
                "tab_icon": "👤",
                "tab_order": 1,
                "tab_type": "inputframe",
                "groups": ["person_basic", "address_data", "contact_data"],
                "multi_tab_eligible": True,
                "preferred_position": "left"
            },
            {
                "tab_id": "geschaeftsdaten",
                "tab_name": "Geschäft",
                "tab_icon": "💼",
                "tab_order": 2,
                "tab_type": "inputframe",
                "groups": ["finance_data", "business_data"],
                "multi_tab_eligible": True,
                "preferred_position": "center"
            },
            {
                "tab_id": "zusatzdaten",
                "tab_name": "Zusatz",
                "tab_icon": "📋",
                "tab_order": 3,
                "tab_type": "inputframe",
                "groups": ["notes_data", "system_data"],
                "multi_tab_eligible": True,
                "preferred_position": "right"
            },
            {
                "tab_id": "dokumente",
                "tab_name": "Dokumente",
                "tab_icon": "📎",
                "tab_order": 4,
                "tab_type": "inputframe",
                "groups": ["documents_data"],
                "multi_tab_eligible": True,
                "preferred_position": "right"
            }
        ],
        
        # Gruppen-Definitionen
        "groups": {
            "person_basic": {
                "group_name": "Personen-Daten",
                "group_icon": "👤",
                "fields": ["vorname", "nachname", "email"],
                "layout": "grid"
            },
            "address_data": {
                "group_name": "Adress-Daten", 
                "group_icon": "🏠",
                "fields": ["strasse", "plz", "ort"],
                "layout": "grid"
            },
            "contact_data": {
                "group_name": "Kontakt-Daten",
                "group_icon": "📞", 
                "fields": ["telefon", "mobil"],
                "layout": "grid"
            },
            "finance_data": {
                "group_name": "Geschäftsdaten",
                "group_icon": "💼",
                "fields": ["firma", "abteilung", "position"],
                "layout": "grid"
            },
            "business_data": {
                "group_name": "Kontakt-Daten",
                "group_icon": "📞",
                "fields": ["telefon_geschaeft", "email_geschaeft"],
                "layout": "grid"
            },
            "notes_data": {
                "group_name": "Notizen & Kommentare",
                "group_icon": "📝",
                "fields": ["notizen", "kommentare"],
                "layout": "vertical"
            },
            "system_data": {
                "group_name": "System-Daten",
                "group_icon": "⚙️",
                "fields": ["erstellt", "geaendert", "status"],
                "layout": "grid"
            },
            "documents_data": {
                "group_name": "Dokumente & Dateien",
                "group_icon": "📎",
                "fields": ["anhaenge", "dokumente"],
                "layout": "vertical"
            }
        },
        
        # Multi-Tab-Presets
        "multi_tab_presets": {
            "default_2_tabs": {
                "name": "Standard (2 Tabs)",
                "description": "Stammdaten + Geschäft",
                "layout": "horizontal",
                "tabs": ["stammdaten", "geschaeftsdaten"],
                "sizes": [50, 50]
            },
            "complete_3_tabs": {
                "name": "Komplett (3 Tabs)",
                "description": "Stammdaten + Geschäft + Zusatz",
                "layout": "horizontal", 
                "tabs": ["stammdaten", "geschaeftsdaten", "zusatzdaten"],
                "sizes": [33, 33, 34]
            },
            "work_vertical": {
                "name": "Arbeitsbereich (vertikal)",
                "description": "Stammdaten oben, Dokumente unten",
                "layout": "vertical",
                "tabs": ["stammdaten", "dokumente"],
                "sizes": [70, 30]
            }
        },
        
        # Metadaten
        "created_at": "2025-01-21T10:30:00",
        "created_by": "system",
        "modified_at": "2025-01-21T15:45:00",
        "version": "3.0.0"
    }
    
    return framedaten_structure

def save_multi_tab_config_to_database():
    """Speichert Multi-Tab-Konfiguration in der Datenbank"""
    
    try:
        from pdvm_central_datenbank import PdvmCentralDatenbank
        
        # Konfiguration erstellen
        config = create_multi_tab_framedaten_config()
        frame_guid = config["frame_guid"]
        
        # Datenbank-Verbindung
        db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="framedaten",
            guid=frame_guid
        )
        
        # Konfiguration speichern
        db.speichern(frame_guid, config)
        
        logger.info(f"✅ Multi-Tab-Konfiguration für Frame {frame_guid} gespeichert")
        logger.info(f"📊 {len(config['tabs'])} Tabs konfiguriert")
        logger.info(f"📱 Multi-Tab: {config['multi_tab_config']['max_tabs_display']} Tabs max")
        logger.info(f"🎛️ Presets: {len(config['multi_tab_presets'])} verfügbar")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Speichern der Multi-Tab-Konfiguration: {e}")
        return False

def create_demo_user_settings():
    """Erstellt Demo-Benutzer-Einstellungen für Multi-Tab"""
    
    try:
        from pdvm_central_datenbank import PdvmCentralDatenbank
        
        demo_user_guid = "demo-user-12345-enhanced"
        frame_guid = "4078079f-4028-45ed-879c-3c779ecf3d0d"
        
        # Systemsteuerung-Datenbank
        sys_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="systemsteuerung",
            guid=demo_user_guid
        )
        
        # Benutzer-Daten struktur
        user_data = {
            demo_user_guid: {
                "MultiTabSettings": {
                    frame_guid: {
                        "preferred_layout": "horizontal",
                        "max_tabs_display": 2,
                        "auto_activate": False,
                        "remember_state": True,
                        "last_used_preset": "default_2_tabs",
                        "custom_tab_order": ["stammdaten", "geschaeftsdaten", "zusatzdaten", "dokumente"],
                        "splitter_sizes": [400, 400],
                        "config_version": "1.0"
                    }
                },
                "UserPreferences": {
                    "theme": "default",
                    "language": "de",
                    "auto_save": True
                }
            }
        }
        
        # Benutzer-Einstellungen speichern
        sys_db.speichern(demo_user_guid, user_data)
        
        logger.info(f"✅ Demo-Benutzer-Einstellungen für {demo_user_guid} erstellt")
        logger.info(f"📱 Multi-Tab-Einstellungen für Frame {frame_guid} konfiguriert")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen der Benutzer-Einstellungen: {e}")
        return False

def setup_complete_multi_tab_environment():
    """Komplette Einrichtung der Multi-Tab-Umgebung"""
    
    logger.info("🔧 === Multi-Tab-Umgebung Setup ===")
    
    # 1. Framedaten-Konfiguration
    logger.info("📊 1. Erstelle Framedaten-Konfiguration...")
    if save_multi_tab_config_to_database():
        logger.info("✅ Framedaten-Konfiguration erfolgreich")
    else:
        logger.error("❌ Framedaten-Konfiguration fehlgeschlagen")
        return False
    
    # 2. Benutzer-Einstellungen
    logger.info("👤 2. Erstelle Benutzer-Einstellungen...")
    if create_demo_user_settings():
        logger.info("✅ Benutzer-Einstellungen erfolgreich")
    else:
        logger.error("❌ Benutzer-Einstellungen fehlgeschlagen")
        return False
    
    logger.info("🎉 === Multi-Tab-Setup abgeschlossen ===")
    logger.info("📱 Verwendung: F4 für Multi-Tab-Modus")
    logger.info("⚙️ Verwendung: F5 für Konfiguration")
    logger.info("🔍 Verwendung: F1/F2 für Lupe-Modi")
    
    return True

if __name__ == "__main__":
    # Logging konfigurieren
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    # Setup ausführen
    setup_complete_multi_tab_environment()
