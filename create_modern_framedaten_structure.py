# create_modern_framedaten_structure.py
# -*- coding: utf-8 -*-
"""
Erstellt eine moderne framedaten-Struktur für Tab-basierte Dialoge
================================================================

Neue Struktur mit:
- Tab-basierte Organisation der InputControls
- View-Integration mit richtiger Datenanzeige
- Vollständige Parametrisierung in framedaten
- Unterstützung für UnifiedPdvmDialogWidget V3
"""

import json
import logging
from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)

def create_modern_framedaten_structure():
    """
    Erstellt eine moderne framedaten-Struktur mit Tab-Organisation.
    
    Struktur:
    - ROOT: Zentrale Konfiguration mit View und Tabs
    - ViewConfig: View-Konfiguration für Datenanzeige  
    - TabConfig: Tab-Organisation der InputControls
    - InputControls: Moderne IC-Definition mit Tab-Zuordnung
    """
    
    # Test View-GUID für Persondaten
    test_view_guid = "12345678-1234-1234-1234-123456789abc"
    
    framedaten = {
        "ROOT": {
            "version": "2.0",
            "type": "unified_dialog",
            "frame_name": "Persondaten Verwaltung",
            "created_at": "2025-01-20T15:00:00",
            "widget_type": "UnifiedPdvmDialogWidget"
        },
        
        "ViewConfig": {
            "view_guid": test_view_guid,
            "view_enabled": True,
            "view_title": "Personen Übersicht",
            "root_table": "persondaten",
            "display_mode": "table",
            "columns": [
                {"field": "name", "title": "Name", "width": 150},
                {"field": "vorname", "title": "Vorname", "width": 150},
                {"field": "strasse", "title": "Straße", "width": 200},
                {"field": "plz", "title": "PLZ", "width": 80},
                {"field": "ort", "title": "Ort", "width": 150},
                {"field": "geburtsdatum", "title": "Geburtsdatum", "width": 120}
            ],
            "search_enabled": True,
            "filter_enabled": True
        },
        
        "TabConfig": {
            "tabs_enabled": True,
            "default_tab": "Stammdaten",
            "tabs": [
                {
                    "tab_id": "stammdaten",
                    "tab_name": "Stammdaten",
                    "tab_order": 1,
                    "icon": "person",
                    "enabled": True
                },
                {
                    "tab_id": "kontakt",
                    "tab_name": "Kontakt",
                    "tab_order": 2,
                    "icon": "contact",
                    "enabled": True
                },
                {
                    "tab_id": "zusatzinfo",
                    "tab_name": "Zusatzinfo",
                    "tab_order": 3,
                    "icon": "info",
                    "enabled": True
                }
            ]
        },
        
        "InputControls": {
            # STAMMDATEN TAB
            "ic_name": {
                "tab_id": "stammdaten",
                "order": 1,
                "type": "text",
                "label": "Name",
                "field": "name",
                "table": "persondaten",
                "source_path": "root",
                "required": True,
                "width": 200,
                "tooltip": "Nachname der Person",
                "validation": {
                    "type": "string",
                    "max_length": 100,
                    "pattern": "[A-Za-zÄÖÜäöüß\\s\\-]+"
                }
            },
            
            "ic_vorname": {
                "tab_id": "stammdaten",
                "order": 2,
                "type": "text",
                "label": "Vorname",
                "field": "vorname",
                "table": "persondaten",
                "source_path": "root",
                "required": True,
                "width": 200,
                "tooltip": "Vorname der Person",
                "validation": {
                    "type": "string",
                    "max_length": 100
                }
            },
            
            "ic_geburtsdatum": {
                "tab_id": "stammdaten",
                "order": 3,
                "type": "datetime",
                "label": "Geburtsdatum",
                "field": "geburtsdatum",
                "table": "persondaten",
                "source_path": "root",
                "required": False,
                "width": 150,
                "tooltip": "Geburtsdatum der Person",
                "datetime_config": {
                    "format": "DD.MM.YYYY",
                    "show_time": False,
                    "allow_empty": True,
                    "min_date": "01.01.1900",
                    "max_date": "today"
                }
            },
            
            "ic_geschlecht": {
                "tab_id": "stammdaten",
                "order": 4,
                "type": "dropdown",
                "label": "Geschlecht",
                "field": "geschlecht",
                "table": "persondaten",
                "source_path": "root",
                "required": False,
                "width": 120,
                "tooltip": "Geschlecht der Person",
                "dropdown_config": {
                    "source": "systemwerte",
                    "kategorie": "geschlecht",
                    "allow_empty": True,
                    "default_value": ""
                }
            },
            
            # KONTAKT TAB
            "ic_strasse": {
                "tab_id": "kontakt",
                "order": 1,
                "type": "text",
                "label": "Straße",
                "field": "strasse",
                "table": "persondaten",
                "source_path": "root",
                "required": False,
                "width": 300,
                "tooltip": "Straße und Hausnummer"
            },
            
            "ic_plz": {
                "tab_id": "kontakt",
                "order": 2,
                "type": "text",
                "label": "PLZ",
                "field": "plz",
                "table": "persondaten",
                "source_path": "root",
                "required": False,
                "width": 80,
                "tooltip": "Postleitzahl",
                "validation": {
                    "type": "string",
                    "pattern": "[0-9]{5}",
                    "max_length": 5
                }
            },
            
            "ic_ort": {
                "tab_id": "kontakt",
                "order": 3,
                "type": "text",
                "label": "Ort",
                "field": "ort",
                "table": "persondaten",
                "source_path": "root",
                "required": False,
                "width": 200,
                "tooltip": "Wohnort"
            },
            
            "ic_telefon": {
                "tab_id": "kontakt",
                "order": 4,
                "type": "text",
                "label": "Telefon",
                "field": "telefon",
                "table": "persondaten",
                "source_path": "root",
                "required": False,
                "width": 150,
                "tooltip": "Telefonnummer"
            },
            
            "ic_email": {
                "tab_id": "kontakt",
                "order": 5,
                "type": "text",
                "label": "E-Mail",
                "field": "email",
                "table": "persondaten",
                "source_path": "root",
                "required": False,
                "width": 250,
                "tooltip": "E-Mail Adresse",
                "validation": {
                    "type": "email",
                    "pattern": "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
                }
            },
            
            # ZUSATZINFO TAB
            "ic_familienstand": {
                "tab_id": "zusatzinfo",
                "order": 1,
                "type": "dropdown",
                "label": "Familienstand",
                "field": "familienstand",
                "table": "persondaten",
                "source_path": "root",
                "required": False,
                "width": 150,
                "tooltip": "Familienstand der Person",
                "dropdown_config": {
                    "source": "systemwerte",
                    "kategorie": "familienstand",
                    "allow_empty": True,
                    "default_value": ""
                }
            },
            
            "ic_partner": {
                "tab_id": "zusatzinfo",
                "order": 2,
                "type": "viewtable",
                "label": "Partner",
                "field": "partner_guid",
                "table": "persondaten",
                "source_path": "root",
                "required": False,
                "width": 250,
                "tooltip": "Partner der Person",
                "viewtable_config": {
                    "source_view": "personen_auswahl",
                    "display_field": "name_vorname",
                    "value_field": "guid",
                    "allow_empty": True,
                    "search_enabled": True
                }
            },
            
            "ic_bemerkungen": {
                "tab_id": "zusatzinfo",
                "order": 3,
                "type": "textarea",
                "label": "Bemerkungen",
                "field": "bemerkungen",
                "table": "persondaten",
                "source_path": "root",
                "required": False,
                "width": 400,
                "height": 100,
                "tooltip": "Zusätzliche Bemerkungen zur Person"
            }
        },
        
        "UIConfig": {
            "splitter_orientation": "horizontal",
            "view_default_size": 300,
            "input_default_size": 400,
            "resizable": True,
            "show_statusbar": True,
            "keyboard_shortcuts": {
                "F1": "toggle_view_lupe",
                "F2": "toggle_input_lupe",
                "F3": "restore_layout"
            }
        },
        
        "DataConfig": {
            "auto_save": True,
            "save_delay": 500,
            "load_on_select": True,
            "validate_on_save": True,
            "history_enabled": True
        }
    }
    
    return framedaten

def create_supporting_viewdaten():
    """Erstellt die View-Daten für die Persondaten-Anzeige"""
    
    test_view_guid = "12345678-1234-1234-1234-123456789abc"
    
    viewdaten = {
        test_view_guid: {
            "ROOT": {
                "view_name": "Personen Übersicht",
                "table_name": "persondaten",
                "view_type": "table_view",
                "created_at": "2025-01-20T15:00:00"
            },
            "Config": {
                "sortable": True,
                "filterable": True,
                "searchable": True,
                "selectable": True,
                "multi_select": False,
                "show_row_numbers": True,
                "alternating_row_colors": True
            },
            "Columns": {
                "name": {
                    "title": "Name",
                    "field": "name",
                    "width": 150,
                    "sortable": True,
                    "filterable": True,
                    "type": "text"
                },
                "vorname": {
                    "title": "Vorname", 
                    "field": "vorname",
                    "width": 150,
                    "sortable": True,
                    "filterable": True,
                    "type": "text"
                },
                "strasse": {
                    "title": "Straße",
                    "field": "strasse", 
                    "width": 200,
                    "sortable": True,
                    "filterable": True,
                    "type": "text"
                },
                "plz": {
                    "title": "PLZ",
                    "field": "plz",
                    "width": 80,
                    "sortable": True,
                    "filterable": True,
                    "type": "text"
                },
                "ort": {
                    "title": "Ort",
                    "field": "ort",
                    "width": 150,
                    "sortable": True,
                    "filterable": True,
                    "type": "text"
                },
                "geburtsdatum": {
                    "title": "Geburtsdatum",
                    "field": "geburtsdatum",
                    "width": 120,
                    "sortable": True,
                    "filterable": True,
                    "type": "date"
                }
            }
        }
    }
    
    return viewdaten

def create_systemwerte_data():
    """Erstellt die Systemwerte für Dropdown-Felder"""
    
    systemwerte = {
        "geschlecht": {
            "m": {"value": "m", "text": "Männlich", "order": 1},
            "w": {"value": "w", "text": "Weiblich", "order": 2},
            "d": {"value": "d", "text": "Divers", "order": 3}
        },
        "familienstand": {
            "ledig": {"value": "ledig", "text": "Ledig", "order": 1},
            "verheiratet": {"value": "verheiratet", "text": "Verheiratet", "order": 2},
            "geschieden": {"value": "geschieden", "text": "Geschieden", "order": 3},
            "verwitwet": {"value": "verwitwet", "text": "Verwitwet", "order": 4},
            "getrennt": {"value": "getrennt", "text": "Getrennt lebend", "order": 5}
        }
    }
    
    return systemwerte

def create_sample_persondaten():
    """Erstellt Beispiel-Personendaten für Tests"""
    
    persondaten = {
        "person_001": {
            "guid": "person_001",
            "name": "Mustermann",
            "vorname": "Max",
            "strasse": "Musterstraße 123",
            "plz": "12345",
            "ort": "Musterstadt",
            "telefon": "0123/456789",
            "email": "max.mustermann@example.com",
            "geburtsdatum": "1985-05-15",
            "geschlecht": "m",
            "familienstand": "verheiratet",
            "partner_guid": "person_002",
            "bemerkungen": "Beispielperson für Tests"
        },
        "person_002": {
            "guid": "person_002", 
            "name": "Musterfrau",
            "vorname": "Maria",
            "strasse": "Musterstraße 123",
            "plz": "12345",
            "ort": "Musterstadt",
            "telefon": "0123/456789",
            "email": "maria.musterfrau@example.com",
            "geburtsdatum": "1987-08-22",
            "geschlecht": "w",
            "familienstand": "verheiratet",
            "partner_guid": "person_001",
            "bemerkungen": "Partner von Max Mustermann"
        },
        "person_003": {
            "guid": "person_003",
            "name": "Schmidt",
            "vorname": "Anna",
            "strasse": "Testweg 456",
            "plz": "54321", 
            "ort": "Testdorf",
            "telefon": "0987/654321",
            "email": "anna.schmidt@test.de",
            "geburtsdatum": "1990-12-03",
            "geschlecht": "w",
            "familienstand": "ledig",
            "partner_guid": "",
            "bemerkungen": ""
        }
    }
    
    return persondaten

def create_modern_framedaten_database():
    """
    Erstellt die komplette moderne framedaten-Struktur in der Datenbank.
    """
    
    frame_guid = "4078079f-4028-45ed-879c-3c779ecf3d0d"
    
    try:
        logger.info("🔧 Erstelle moderne framedaten-Struktur...")
        
        # 1. Framedaten mit moderner Struktur
        framedaten_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="framedaten",
            guid=frame_guid
        )
        
        moderne_framedaten = create_modern_framedaten_structure()
        
        # DEBUG: Datenstruktur vor dem Speichern prüfen
        logger.debug(f"📊 Framedaten-Struktur: {list(moderne_framedaten.keys())}")
        
        # Speichern mit korrekter Struktur
        result = framedaten_db.speichern(frame_guid, {frame_guid: moderne_framedaten})
        logger.info(f"✅ Moderne framedaten-Struktur erstellt: {result}")
        
        # Verifikation: Daten wieder laden
        loaded_data = framedaten_db.lesen()
        if loaded_data and frame_guid in loaded_data:
            logger.info("✅ Framedaten erfolgreich gespeichert und verifiziert")
        else:
            logger.error("❌ Framedaten-Verifikation fehlgeschlagen")
            return False
        
        # 2. Viewdaten erstellen
        test_view_guid = "12345678-1234-1234-1234-123456789abc"
        viewdaten_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="viewdaten",
            guid=test_view_guid
        )
        
        viewdaten = create_supporting_viewdaten()
        view_result = viewdaten_db.speichern(test_view_guid, {test_view_guid: viewdaten[test_view_guid]})
        logger.info(f"✅ Viewdaten erstellt: {view_result}")
        
        # 3. Systemwerte erstellen
        systemwerte_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="systemwerte",
            guid="global"
        )
        
        systemwerte = create_systemwerte_data()
        sys_result = systemwerte_db.speichern("global", {"global": systemwerte})
        logger.info(f"✅ Systemwerte erstellt: {sys_result}")
        
        # 4. Beispiel-Personendaten erstellen
        persondaten_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="persondaten",
            guid="global"
        )
        
        persondaten = create_sample_persondaten()
        pers_result = persondaten_db.speichern("global", {"global": persondaten})
        logger.info(f"✅ Beispiel-Personendaten erstellt: {pers_result}")
        
        logger.info("🎯 Moderne framedaten-Struktur vollständig erstellt!")
        logger.info(f"🎯 Frame GUID: {frame_guid}")
        logger.info(f"🎯 View GUID: {test_view_guid}")
        logger.info("🎯 Das UnifiedPdvmDialogWidget V3 kann jetzt getestet werden!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen der modernen framedaten-Struktur: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Hauptfunktion zum Erstellen der modernen Struktur"""
    
    print("🚀 Erstelle moderne framedaten-Struktur für Tab-basierte Dialoge...")
    print("=" * 60)
    
    success = create_modern_framedaten_database()
    
    if success:
        print("\n✅ ERFOLGREICH!")
        print("🎯 Moderne framedaten-Struktur wurde erstellt")
        print("🎯 Tab-basierte InputControls konfiguriert")
        print("🎯 View-Integration vorbereitet")
        print("🎯 Systemwerte und Beispieldaten erstellt")
        print("\n📝 Verwendung:")
        print("   self.pdvm_unified_test()  # für UnifiedPdvmDialogWidget V3")
        print("   self.pdvm_dialog('4078079f-4028-45ed-879c-3c779ecf3d0d', 0)")
    else:
        print("\n❌ FEHLER!")
        print("Siehe Log für Details")

if __name__ == "__main__":
    main()
