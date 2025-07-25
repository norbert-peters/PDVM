# repair_framedaten_structure.py
# -*- coding: utf-8 -*-
"""
Repariert die framedaten-Struktur für die GUID "4078079f-4028-45ed-879c-3c779ecf3d0d"
Erstellt die klassische Struktur mit ROOT und Metadaten für InputControls
"""

import json
import logging
from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)

def create_working_framedaten_structure():
    """
    Erstellt eine funktionstüchtige framedaten-Struktur mit ROOT und Metadaten.
    
    Struktur:
    - ROOT: Enthält zentrale Informationen (view_guid, root_table, etc.)
    - Metadaten: Enthält alle InputControls (ICs) mit verschiedenen Typen
    """
    
    # Test View-GUID für Persondaten
    test_view_guid = "12345678-1234-1234-1234-123456789abc"
    
    framedaten = {
        "ROOT": {
            "view_guid": test_view_guid,
            "root_table": "persondaten",
            "frame_name": "Person Datenpflege",
            "frame_type": "inputframe", 
            "mode": 0,
            "version": "1.0",
            "created_at": "2025-01-20T10:00:00"
        },
        
        "Metadaten": {
            # TEXT-Felder
            "persondaten_persdaten_name": {
                "label": "Name",
                "tooltip": "Nachname der Person",
                "type": "text",
                "source_path": "root",
                "historical": True,
                "display_ti_ab_short": True,
                "display_ti_val_short": False,
                "abdatum": True,
                "display_ab": "all",
                "display_val": None,
                "conversion_in": None,
                "conversion_out": None,
                "ui_width_label": None,
                "ui_width_value": None,
                "ui_width_button": None,
                "ui_indent_ab": None,
                "dropdown": {},
                "viewtable": {},
                "help": {}
            },
            
            "persondaten_persdaten_vorname": {
                "label": "Vorname",
                "tooltip": "Vorname der Person",
                "type": "text",
                "source_path": "root",
                "historical": True,
                "display_ti_ab_short": True,
                "display_ti_val_short": False,
                "abdatum": True,
                "display_ab": "all",
                "display_val": None,
                "conversion_in": None,
                "conversion_out": None,
                "ui_width_label": None,
                "ui_width_value": None,
                "ui_width_button": None,
                "ui_indent_ab": None,
                "dropdown": {},
                "viewtable": {},
                "help": {}
            },
            
            # DATETIME-Feld
            "persondaten_persdaten_geburtsdatum": {
                "label": "Geburtsdatum",
                "tooltip": "Geburtsdatum der Person",
                "type": "datetime",
                "source_path": "root",
                "historical": True,
                "display_ti_ab_short": True,
                "display_ti_val_short": True,
                "abdatum": True,
                "display_ab": "all",
                "display_val": "all",
                "conversion_in": None,
                "conversion_out": None,
                "ui_width_label": None,
                "ui_width_value": None,
                "ui_width_button": None,
                "ui_indent_ab": None,
                "dropdown": {},
                "viewtable": {},
                "help": {}
            },
            
            # DROPDOWN-Feld
            "persondaten_persdaten_geschlecht": {
                "label": "Geschlecht",
                "tooltip": "Geschlecht der Person",
                "type": "dropdown",
                "source_path": "root",
                "historical": True,
                "display_ti_ab_short": True,
                "display_ti_val_short": False,
                "abdatum": True,
                "display_ab": "all",
                "display_val": None,
                "conversion_in": None,
                "conversion_out": None,
                "ui_width_label": None,
                "ui_width_value": None,
                "ui_width_button": None,
                "ui_indent_ab": None,
                "dropdown": {
                    "table": "systemwerte",
                    "key": "00000000-0000-0000-0000-000000000000",
                    "value": "geschlecht",
                    "source_path": "root"
                },
                "viewtable": {},
                "help": {}
            },
            
            "persondaten_persdaten_familienstand": {
                "label": "Familienstand",
                "tooltip": "Familienstand der Person",
                "type": "dropdown",
                "source_path": "root",
                "historical": True,
                "display_ti_ab_short": True,
                "display_ti_val_short": False,
                "abdatum": True,
                "display_ab": "all",
                "display_val": None,
                "conversion_in": None,
                "conversion_out": None,
                "ui_width_label": None,
                "ui_width_value": None,
                "ui_width_button": None,
                "ui_indent_ab": None,
                "dropdown": {
                    "table": "systemwerte",
                    "key": "00000000-0000-0000-0000-000000000000",
                    "value": "familienstand",
                    "source_path": "root"
                },
                "viewtable": {},
                "help": {}
            },
            
            # VIEWTABLE-Feld (Referenz zu anderen Personen)
            "persondaten_persdaten_partner-persondaten": {
                "label": "Partner",
                "tooltip": "Verweis auf Partner-Person",
                "type": "viewtable",
                "source_path": "root",
                "historical": True,
                "display_ti_ab_short": True,
                "display_ti_val_short": False,
                "abdatum": True,
                "display_ab": "all",
                "display_val": None,
                "conversion_in": None,
                "conversion_out": None,
                "ui_width_label": None,
                "ui_width_value": None,
                "ui_width_button": None,
                "ui_indent_ab": None,
                "dropdown": {},
                "viewtable": {
                    "guid": test_view_guid  # Verweis auf die gleiche View (Personen)
                },
                "help": {}
            },
            
            # Weitere TEXT-Felder für Adresse
            "persondaten_persdaten_strasse": {
                "label": "Straße",
                "tooltip": "Straße und Hausnummer",
                "type": "text",
                "source_path": "root",
                "historical": True,
                "display_ti_ab_short": True,
                "display_ti_val_short": False,
                "abdatum": True,
                "display_ab": "all",
                "display_val": None,
                "conversion_in": None,
                "conversion_out": None,
                "ui_width_label": None,
                "ui_width_value": None,
                "ui_width_button": None,
                "ui_indent_ab": None,
                "dropdown": {},
                "viewtable": {},
                "help": {}
            },
            
            "persondaten_persdaten_plz": {
                "label": "PLZ",
                "tooltip": "Postleitzahl",
                "type": "text",
                "source_path": "root",
                "historical": True,
                "display_ti_ab_short": True,
                "display_ti_val_short": False,
                "abdatum": True,
                "display_ab": "all",
                "display_val": None,
                "conversion_in": None,
                "conversion_out": None,
                "ui_width_label": 80,
                "ui_width_value": 120,
                "ui_width_button": None,
                "ui_indent_ab": None,
                "dropdown": {},
                "viewtable": {},
                "help": {}
            },
            
            "persondaten_persdaten_ort": {
                "label": "Ort",
                "tooltip": "Wohnort",
                "type": "text",
                "source_path": "root",
                "historical": True,
                "display_ti_ab_short": True,
                "display_ti_val_short": False,
                "abdatum": True,
                "display_ab": "all",
                "display_val": None,
                "conversion_in": None,
                "conversion_out": None,
                "ui_width_label": None,
                "ui_width_value": None,
                "ui_width_button": None,
                "ui_indent_ab": None,
                "dropdown": {},
                "viewtable": {},
                "help": {}
            },
            
            # Kontakt-Felder
            "persondaten_persdaten_telefon": {
                "label": "Telefon",
                "tooltip": "Telefonnummer",
                "type": "text",
                "source_path": "root",
                "historical": True,
                "display_ti_ab_short": True,
                "display_ti_val_short": False,
                "abdatum": True,
                "display_ab": "all",
                "display_val": None,
                "conversion_in": None,
                "conversion_out": None,
                "ui_width_label": None,
                "ui_width_value": None,
                "ui_width_button": None,
                "ui_indent_ab": None,
                "dropdown": {},
                "viewtable": {},
                "help": {}
            },
            
            "persondaten_persdaten_email": {
                "label": "E-Mail",
                "tooltip": "E-Mail-Adresse",
                "type": "text",
                "source_path": "root",
                "historical": True,
                "display_ti_ab_short": True,
                "display_ti_val_short": False,
                "abdatum": True,
                "display_ab": "all",
                "display_val": None,
                "conversion_in": None,
                "conversion_out": None,
                "ui_width_label": None,
                "ui_width_value": 250,
                "ui_width_button": None,
                "ui_indent_ab": None,
                "dropdown": {},
                "viewtable": {},
                "help": {}
            }
        }
    }
    
    return framedaten

def create_supporting_viewdaten():
    """
    Erstellt die benötigten viewdaten für die Test-View.
    """
    test_view_guid = "12345678-1234-1234-1234-123456789abc"
    
    viewdaten = {
        "ROOT": {
            "view_table": "persondaten",
            "view_name": "Personen-Übersicht", 
            "history": False,
            "historisch": True,
            "display_width": "100%",
            "created_at": "2025-01-20T10:00:00"
        },
        "metadata": {
            "persondaten": {
                "felder": [
                    {
                        "name": "name",
                        "label": "Name",
                        "type": "text",
                        "width": 150,
                        "sortable": True
                    },
                    {
                        "name": "vorname", 
                        "label": "Vorname",
                        "type": "text",
                        "width": 120,
                        "sortable": True
                    },
                    {
                        "name": "geburtsdatum",
                        "label": "Geburtsdatum",
                        "type": "date",
                        "width": 100,
                        "sortable": True
                    },
                    {
                        "name": "ort",
                        "label": "Ort",
                        "type": "text", 
                        "width": 120,
                        "sortable": True
                    }
                ]
            }
        }
    }
    
    return test_view_guid, viewdaten

def create_systemwerte_data():
    """
    Erstellt die notwendigen Systemwerte für Dropdowns.
    """
    systemwerte_guid = "00000000-0000-0000-0000-000000000000"
    
    systemwerte = {
        "ROOT": {
            # Geschlecht-Dropdown
            "geschlecht": {
                "m": "Männlich",
                "w": "Weiblich", 
                "d": "Divers"
            },
            # Familienstand-Dropdown
            "familienstand": {
                "ledig": "Ledig",
                "verheiratet": "Verheiratet",
                "geschieden": "Geschieden", 
                "verwitwet": "Verwitwet",
                "getrennt": "Getrennt lebend"
            }
        }
    }
    
    return systemwerte_guid, systemwerte

def repair_framedaten_database():
    """
    Repariert die Datenbank-Einträge für framedaten, viewdaten und systemwerte.
    """
    frame_guid = "4078079f-4028-45ed-879c-3c779ecf3d0d"
    
    try:
        # 1. Framedaten reparieren
        logger.info("🔧 Repariere framedaten-Struktur...")
        framedaten = create_working_framedaten_structure()
        
        frame_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="framedaten",
            guid=frame_guid
        )
        frame_db.speichern(frame_guid, framedaten)
        logger.info(f"✅ Framedaten für GUID {frame_guid} repariert")
        
        # 2. Viewdaten erstellen/aktualisieren
        logger.info("🔧 Erstelle viewdaten...")
        view_guid, viewdaten = create_supporting_viewdaten()
        
        view_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db", 
            table_name="viewdaten",
            guid=view_guid
        )
        view_db.speichern(view_guid, viewdaten)
        logger.info(f"✅ Viewdaten für GUID {view_guid} erstellt")
        
        # 3. Systemwerte erstellen/aktualisieren
        logger.info("🔧 Erstelle systemwerte...")
        systemwerte_guid, systemwerte = create_systemwerte_data()
        
        system_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="systemwerte", 
            guid=systemwerte_guid
        )
        system_db.speichern(systemwerte_guid, systemwerte)
        logger.info(f"✅ Systemwerte für GUID {systemwerte_guid} erstellt")
        
        # 4. Zusammenfassung
        logger.info("🎉 Reparatur abgeschlossen!")
        logger.info(f"📋 Frame-GUID: {frame_guid}")
        logger.info(f"👁️ View-GUID: {view_guid}")
        logger.info(f"⚙️ System-GUID: {systemwerte_guid}")
        
        # 5. Struktur-Info ausgeben
        logger.info("\n📊 Erstellte InputControls:")
        for ic_key in framedaten["Metadaten"].keys():
            ic_type = framedaten["Metadaten"][ic_key]["type"]
            ic_label = framedaten["Metadaten"][ic_key]["label"]
            logger.info(f"  • {ic_label} ({ic_type}) - {ic_key}")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler bei der Reparatur: {e}")
        return False

if __name__ == "__main__":
    # Logger konfigurieren
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    print("🔧 Starte Reparatur der framedaten-Struktur...")
    
    success = repair_framedaten_database()
    
    if success:
        print("\n✅ Reparatur erfolgreich abgeschlossen!")
        print("🎯 Das PdvmDialogWidget kann jetzt getestet werden mit:")
        print("   self.pdvm_dialog('4078079f-4028-45ed-879c-3c779ecf3d0d', 0)")
    else:
        print("\n❌ Reparatur fehlgeschlagen!")
