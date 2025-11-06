# -*- coding: utf-8 -*-
"""
PdvmJsonWidget - Erweiterte Version für echte Framedaten/Viewdaten
Basierend auf der realen Datenstruktur
"""
import json
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

@dataclass
class FieldDefinition:
    """Definition eines Feldes für IC-Parameter"""
    key: str
    label: str
    field_type: str  # "text", "dropdown", "datetime", "viewtable", etc.
    historical: bool = True
    source_path: str = "root"
    tooltip: Optional[str] = None
    dropdown: Optional[Dict] = None
    help: Optional[Dict] = None
    ui_settings: Optional[Dict] = None

@dataclass
class FrameSchema:
    """Schema für eine Frame-Konfiguration"""
    root_config: Dict[str, Any]  # ROOT-Bereich
    metadata_sections: Dict[str, List[FieldDefinition]]  # Metadaten-Bereiche

class PdvmFrameDataManager:
    """Manager für Framedaten/Viewdaten mit echten Strukturen"""
    
    def __init__(self):
        self.current_frame_guid = None
        self.current_data = {}
        
    def load_frame_data(self, frame_guid: str) -> FrameSchema:
        """Lädt Framedaten für eine bestimmte GUID"""
        # TODO: Aus Datenbank laden
        # Hier würde die echte Datenbankabfrage stehen
        return self.get_sample_frame_schema()
    
    def get_sample_frame_schema(self) -> FrameSchema:
        """Beispiel-Schema basierend auf deinen Daten"""
        root_config = {
            "root_table": {"type": "dropdown", "options": ["persondaten", "finanzdaten", "unternehmen"]},
            "view_guid": {"type": "text", "format": "uuid"},
            "header_text": {"type": "text"},
            "display_st": {"type": "dropdown", "options": ["only_date", "full_datetime", "short"]},
            "display_time_short": {"type": "boolean"},
            "width_indent_ab": {"type": "integer", "min": 0, "max": 100},
            "width_label": {"type": "integer", "min": 50, "max": 300},
            "width_button": {"type": "integer", "min": 30, "max": 150},
            "width_control": {"type": "integer", "min": 100, "max": 500},
            "width_frame": {"type": "integer", "min": 400, "max": 1200}
        }
        
        # Metadaten-Bereiche (vereinfacht)
        persondaten_fields = [
            FieldDefinition("ANREDE", "Anrede", "dropdown", True, "root", 
                          tooltip="Anrede bitte auswählen",
                          dropdown={"table": "dropdowndaten", "key": "ddaa6590-6d08-461b-a061-75faec26f4ba", "value": "anrede"}),
            FieldDefinition("VORNAME", "Vorname", "text", True, "root",
                          tooltip="Bitte alle Vornamen eingeben"),
            FieldDefinition("FAMILIENNAME", "Familienname", "text", True, "root",
                          tooltip="Familienname bzw. Nachname"),
            FieldDefinition("GEBURTSDATUM", "Geburtsdatum", "datetime", True, "root",
                          tooltip="Geburtsdatum der Person"),
        ]
        
        finanzdaten_fields = [
            FieldDefinition("KONTONUMMER", "Konto Nummer", "text", False, "root",
                          tooltip="Die Kontonummer des internen Kontos"),
            FieldDefinition("KONTOBEZEICHNUNG", "Konto Bezeichnung", "text", False, "root",
                          tooltip="Die Bezeichnung des internen Kontos"),
            FieldDefinition("KONTOINHABER", "Konto Inhaber", "text", False, "root",
                          tooltip="Der Inhaber des internen Kontos"),
            FieldDefinition("KONTOWAEHRUNG", "Konto Währung", "dropdown", False, "root",
                          dropdown={"table": "dropdowndaten", "key": "ddaa6590-6d08-461b-a061-75faec26f4ba", "value": "waehrung"}),
        ]
        
        metadata_sections = {
            "Persondaten": persondaten_fields,
            "Finanzdaten": finanzdaten_fields
        }
        
        return FrameSchema(root_config, metadata_sections)

    def generate_ic_config(self, field_def: FieldDefinition, section: str) -> Dict:
        """Generiert IC-Konfiguration für ein Feld"""
        ic_key = f"{section}_{field_def.key}"
        
        config = {
            "source_path": field_def.source_path,
            "historical": field_def.historical,
            "display_ti_ab_short": True,
            "display_ti_val_short": False,
            "abdatum": field_def.historical,
            "display_ab": "all" if field_def.historical else None,
            "display_val": None,
            "label": field_def.label,
            "tooltip": field_def.tooltip,
            "type": field_def.field_type,
            "conversion_in": None,
            "conversion_out": None,
            "ui_width_label": None,
            "ui_width_value": None,
            "ui_width_button": None,
            "ui_indent_ab": None,
            "dropdown": field_def.dropdown or {},
            "help": field_def.help or {}
        }
        
        return {ic_key: config}

def create_enhanced_json_widget_schema():
    """Erstellt ein erweitertes Schema für das PdvmJsonWidget"""
    return {
        "type": "object",
        "title": "Frame/View Konfiguration",
        "properties": {
            "ROOT": {
                "type": "object",
                "title": "🏠 ROOT-Konfiguration",
                "properties": {
                    "root_table": {
                        "type": "string",
                        "title": "Root Tabelle",
                        "enum": ["persondaten", "finanzdaten", "unternehmen"],
                        "description": "Haupttabelle für diese Konfiguration"
                    },
                    "view_guid": {
                        "type": "string",
                        "title": "View GUID",
                        "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                        "description": "GUID der zugehörigen View"
                    },
                    "header_text": {
                        "type": "string",
                        "title": "Header Text",
                        "description": "Titel des Frames"
                    },
                    "display_st": {
                        "type": "string",
                        "title": "Display Style",
                        "enum": ["only_date", "full_datetime", "short"],
                        "default": "only_date"
                    },
                    "display_time_short": {
                        "type": "boolean",
                        "title": "Kurze Zeitanzeige",
                        "default": True
                    },
                    "ui_layout": {
                        "type": "object",
                        "title": "UI Layout",
                        "properties": {
                            "width_indent_ab": {
                                "type": "integer",
                                "title": "Einrückung Ab-Datum",
                                "minimum": 0,
                                "maximum": 100,
                                "default": 0
                            },
                            "width_label": {
                                "type": "integer",
                                "title": "Breite Label",
                                "minimum": 50,
                                "maximum": 300,
                                "default": 120
                            },
                            "width_button": {
                                "type": "integer",
                                "title": "Breite Button",
                                "minimum": 30,
                                "maximum": 150,
                                "default": 60
                            },
                            "width_control": {
                                "type": "integer",
                                "title": "Breite Control",
                                "minimum": 100,
                                "maximum": 500,
                                "default": 250
                            },
                            "width_frame": {
                                "type": "integer",
                                "title": "Breite Frame",
                                "minimum": 400,
                                "maximum": 1200,
                                "default": 600
                            }
                        }
                    }
                }
            },
            "Metadaten": {
                "type": "object",
                "title": "🗂️ Metadaten-Bereiche",
                "patternProperties": {
                    "^[A-Za-z0-9_]+$": {
                        "type": "object",
                        "title": "Bereich",
                        "properties": {
                            "_section_info": {
                                "type": "object",
                                "title": "Bereich Info",
                                "properties": {
                                    "name": {"type": "string", "title": "Bereichsname"},
                                    "order": {"type": "integer", "title": "Reihenfolge"},
                                    "active": {"type": "boolean", "title": "Aktiv", "default": True}
                                }
                            },
                            "felder": {
                                "type": "array",
                                "title": "Felder",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "key": {"type": "string", "title": "Feld-Key"},
                                        "label": {"type": "string", "title": "Label"},
                                        "type": {
                                            "type": "string",
                                            "title": "Typ",
                                            "enum": ["text", "dropdown", "datetime", "viewtable", "boolean", "number"]
                                        },
                                        "historical": {"type": "boolean", "title": "Historisch", "default": True},
                                        "tooltip": {"type": "string", "title": "Tooltip"},
                                        "dropdown_config": {
                                            "type": "object",
                                            "title": "Dropdown-Konfiguration",
                                            "properties": {
                                                "table": {"type": "string", "title": "Tabelle"},
                                                "key": {"type": "string", "title": "Key"},
                                                "value": {"type": "string", "title": "Value"}
                                            }
                                        },
                                        "viewtable_config": {
                                            "type": "object",
                                            "title": "ViewTable-Konfiguration",
                                            "properties": {
                                                "guid": {"type": "string", "title": "ViewTable GUID"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

# Beispiel-Daten basierend auf deiner Struktur
def get_sample_real_data():
    return {
        "ROOT": {
            "root_table": "persondaten",
            "view_guid": "0d10a0d0-b1a5-4544-b284-e8a09ca979b5",
            "header_text": "Persönliche Daten - Test",
            "display_st": "only_date",
            "display_time_short": True,
            "ui_layout": {
                "width_indent_ab": 0,
                "width_label": 120,
                "width_button": 60,
                "width_control": 250,
                "width_frame": 600
            }
        },
        "Metadaten": {
            "Persondaten": {
                "_section_info": {
                    "name": "Personendaten",
                    "order": 1,
                    "active": True
                },
                "felder": [
                    {
                        "key": "ANREDE",
                        "label": "Anrede",
                        "type": "dropdown",
                        "historical": True,
                        "tooltip": "Anrede bitte auswählen",
                        "dropdown_config": {
                            "table": "dropdowndaten",
                            "key": "ddaa6590-6d08-461b-a061-75faec26f4ba",
                            "value": "anrede"
                        }
                    },
                    {
                        "key": "VORNAME",
                        "label": "Vorname",
                        "type": "text",
                        "historical": True,
                        "tooltip": "Bitte alle Vornamen eingeben"
                    },
                    {
                        "key": "FAMILIENNAME",
                        "label": "Familienname",
                        "type": "text",
                        "historical": True,
                        "tooltip": "Familienname bzw. Nachname"
                    },
                    {
                        "key": "GEBURTSDATUM",
                        "label": "Geburtsdatum",
                        "type": "datetime",
                        "historical": True,
                        "tooltip": "Geburtsdatum der Person"
                    }
                ]
            },
            "Finanzdaten": {
                "_section_info": {
                    "name": "Finanzdaten",
                    "order": 2,
                    "active": True
                },
                "felder": [
                    {
                        "key": "KONTONUMMER",
                        "label": "Konto Nummer",
                        "type": "text",
                        "historical": False,
                        "tooltip": "Die Kontonummer des internen Kontos"
                    },
                    {
                        "key": "KONTOBEZEICHNUNG",
                        "label": "Konto Bezeichnung",
                        "type": "text",
                        "historical": False,
                        "tooltip": "Die Bezeichnung des internen Kontos"
                    },
                    {
                        "key": "KONTOWAEHRUNG",
                        "label": "Konto Währung",
                        "type": "dropdown",
                        "historical": False,
                        "dropdown_config": {
                            "table": "dropdowndaten",
                            "key": "ddaa6590-6d08-461b-a061-75faec26f4ba",
                            "value": "waehrung"
                        }
                    }
                ]
            }
        }
    }

if __name__ == "__main__":
    # Test der Datenstrukturen
    manager = PdvmFrameDataManager()
    schema = manager.get_sample_frame_schema()
    
    print("🔧 Frame Schema erstellt:")
    print(f"ROOT-Felder: {len(schema.root_config)}")
    print(f"Metadaten-Bereiche: {len(schema.metadata_sections)}")
    
    for section_name, fields in schema.metadata_sections.items():
        print(f"  {section_name}: {len(fields)} Felder")
        for field in fields:
            ic_config = manager.generate_ic_config(field, section_name)
            print(f"    ✓ {field.label} ({field.field_type})")
    
    print("\n📄 JSON Schema:")
    enhanced_schema = create_enhanced_json_widget_schema()
    print(json.dumps(enhanced_schema, indent=2, ensure_ascii=False)[:500] + "...")
    
    print("\n📋 Beispiel-Daten:")
    sample_data = get_sample_real_data()
    print(json.dumps(sample_data, indent=2, ensure_ascii=False)[:500] + "...")
