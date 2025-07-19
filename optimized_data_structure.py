# -*- coding: utf-8 -*-
"""
Optimierte Datenarchitektur für parametrisierbare ERP-Anwendungen
Trennung von Frame-Definition und Feld-Metadaten
"""
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class FieldMetadata:
    """Zentrale Feld-Metadaten (wiederverwendbar)"""
    field_id: str  # Eindeutige GUID
    field_key: str  # z.B. "FAMILIENNAME"
    table_group: str  # z.B. "PERSDATEN"
    label: str
    field_type: str  # "text", "dropdown", "datetime", "viewtable"
    data_type: str  # "string", "number", "date", "boolean"
    historical: bool = True
    required: bool = False
    
    # Validierung
    validation_rules: Optional[Dict] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    regex_pattern: Optional[str] = None
    
    # Konvertierung
    conversion_in: Optional[str] = None
    conversion_out: Optional[str] = None
    
    # UI-Standardwerte (können im Frame überschrieben werden)
    default_width_label: int = 120
    default_width_control: int = 250
    default_tooltip: Optional[str] = None
    
    # Verweise (Multiple möglich!)
    dropdown_configs: List[Dict] = None  # Mehrere Dropdown-Konfigurationen möglich
    help_configs: List[Dict] = None  # Mehrere Hilfe-Konfigurationen möglich
    validation_configs: List[Dict] = None  # Mehrere Validierungen möglich

class OptimizedDataStructure:
    """Optimierte Datenstruktur für ERP-System"""
    
    @staticmethod
    def get_field_metadata_structure():
        """
        Zentrale Feld-Metadaten Struktur
        Gespeichert unter fester GUID: "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        """
        return {
            "metadata_version": "1.0",
            "created_at": "2025-01-16T12:00:00Z",
            "updated_at": "2025-01-16T12:00:00Z",
            
            # Zentrale Feld-Definitionen
            "field_definitions": {
                
                # PERSDATEN Felder
                "field_persdaten_familienname": {
                    "field_id": "f001-fami-name-guid",
                    "field_key": "FAMILIENNAME",
                    "table_group": "PERSDATEN",
                    "label": "Familienname",
                    "field_type": "text",
                    "data_type": "string",
                    "historical": True,
                    "required": True,
                    "validation_rules": {
                        "min_length": 2,
                        "max_length": 50,
                        "regex_pattern": "^[A-Za-zÄÖÜäöüß\\s\\-]+$"
                    },
                    "default_tooltip": "Familienname bzw. Nachname der Person",
                    "help_configs": [
                        {
                            "context": "default",
                            "table": "beschreibungen",
                            "key": "help-guid-familienname-1",
                            "value": "PERSDATEN_FAMILIENNAME"
                        }
                    ]
                },
                
                "field_persdaten_vorname": {
                    "field_id": "f002-vorn-name-guid",
                    "field_key": "VORNAME", 
                    "table_group": "PERSDATEN",
                    "label": "Vorname",
                    "field_type": "text",
                    "data_type": "string",
                    "historical": True,
                    "required": True,
                    "validation_rules": {
                        "min_length": 1,
                        "max_length": 100
                    },
                    "default_tooltip": "Alle Vornamen der Person"
                },
                
                "field_persdaten_anrede": {
                    "field_id": "f003-anre-de-guid",
                    "field_key": "ANREDE",
                    "table_group": "PERSDATEN", 
                    "label": "Anrede",
                    "field_type": "dropdown",
                    "data_type": "string",
                    "historical": True,
                    "required": True,
                    "dropdown_configs": [
                        {
                            "context": "standard",
                            "table": "dropdowndaten",
                            "key": "ddaa6590-6d08-461b-a061-75faec26f4ba",
                            "value": "anrede",
                            "description": "Standard Anreden"
                        },
                        {
                            "context": "formal",
                            "table": "dropdowndaten", 
                            "key": "ddaa6590-6d08-461b-a061-75faec26f4ba",
                            "value": "anrede_formal",
                            "description": "Formelle Anreden"
                        }
                    ],
                    "default_tooltip": "Anrede der Person"
                },
                
                "field_persdaten_geburtsdatum": {
                    "field_id": "f004-gebu-datum-guid",
                    "field_key": "GEBURTSDATUM",
                    "table_group": "PERSDATEN",
                    "label": "Geburtsdatum", 
                    "field_type": "datetime",
                    "data_type": "date",
                    "historical": True,
                    "required": False,
                    "validation_rules": {
                        "min_date": "1900-01-01",
                        "max_date": "today"
                    },
                    "default_tooltip": "Geburtsdatum der Person"
                },
                
                # FINANZDATEN Felder
                "field_finanzdaten_kontonummer": {
                    "field_id": "f101-kont-nummer-guid",
                    "field_key": "KONTONUMMER",
                    "table_group": "FINANZDATEN",
                    "label": "Konto Nummer",
                    "field_type": "text",
                    "data_type": "string", 
                    "historical": False,
                    "required": True,
                    "validation_rules": {
                        "regex_pattern": "^[0-9\\-]+$"
                    },
                    "default_tooltip": "Interne Kontonummer"
                },
                
                "field_finanzdaten_kontobezeichnung": {
                    "field_id": "f102-kont-bezeichnung-guid",
                    "field_key": "KONTOBEZEICHNUNG",
                    "table_group": "FINANZDATEN",
                    "label": "Konto Bezeichnung",
                    "field_type": "text",
                    "data_type": "string",
                    "historical": False,
                    "required": True,
                    "default_tooltip": "Bezeichnung des Kontos"
                },
                
                "field_finanzdaten_waehrung": {
                    "field_id": "f103-waeh-rung-guid",
                    "field_key": "KONTOWAEHRUNG",
                    "table_group": "FINANZDATEN",
                    "label": "Währung",
                    "field_type": "dropdown",
                    "data_type": "string",
                    "historical": False,
                    "required": True,
                    "dropdown_configs": [
                        {
                            "context": "default",
                            "table": "dropdowndaten",
                            "key": "ddaa6590-6d08-461b-a061-75faec26f4ba", 
                            "value": "waehrung",
                            "description": "Währungen"
                        }
                    ]
                },
                
                "field_finanzdaten_zuordnung": {
                    "field_id": "f104-finan-zuordnung-guid",
                    "field_key": "FINANZDATEN-FINANZDATEN",
                    "table_group": "FINANZDATEN",
                    "label": "Zuordnung Finanzen",
                    "field_type": "viewtable",
                    "data_type": "guid",
                    "historical": True,
                    "required": False,
                    "viewtable_configs": [
                        {
                            "context": "default",
                            "guid": "86aa89c0-43e3-4317-8df6-03dee6f63689",
                            "description": "Standard Finanzdaten View"
                        }
                    ],
                    "default_tooltip": "GUID-Zuordnung für Finanzdaten"
                }
            }
        }
    
    @staticmethod
    def get_frame_definition_structure():
        """
        Frame-Definition Struktur (nur UI-Layout, keine Feld-Metadaten)
        Gespeichert unter Frame-GUID: z.B. "4078079f-4028-45ed-879c-3c779ecf3d0d"
        """
        return {
            "frame_version": "1.0",
            "created_at": "2025-01-16T12:00:00Z",
            "updated_at": "2025-01-16T12:00:00Z",
            
            # ROOT-Informationen (nur Frame-spezifisch)
            "ROOT": {
                "frame_id": "4078079f-4028-45ed-879c-3c779ecf3d0d",
                "frame_name": "Persondaten Eingabe",
                "frame_type": "input",
                "root_table": "persondaten",
                "view_guid": "0d10a0d0-b1a5-4544-b284-e8a09ca979b5",
                "header_text": "Persönliche Daten - Eingabe",
                
                # UI-Layout (Frame-spezifisch)
                "ui_layout": {
                    "display_style": "only_date",
                    "display_time_short": True,
                    "width_indent_ab": 0,
                    "width_label": 140,  # Frame-spezifische Anpassung
                    "width_button": 60,
                    "width_control": 280,  # Frame-spezifische Anpassung
                    "width_frame": 650,
                    "enable_grouping": True,  # NEU: Gruppierung aktivieren
                    "group_style": "tabs"  # NEU: "tabs", "accordion", "sections"
                }
            },
            
            # GRUPPEN-Definitionen (NEU: Echte Gruppierung)
            "GROUPS": {
                "group_person_basis": {
                    "group_id": "grp-person-basis",
                    "group_name": "Basisdaten",
                    "group_order": 1,
                    "group_icon": "👤",
                    "group_description": "Grundlegende Personendaten",
                    "collapsible": False,
                    "initially_expanded": True
                },
                "group_person_kontakt": {
                    "group_id": "grp-person-kontakt", 
                    "group_name": "Kontaktdaten",
                    "group_order": 2,
                    "group_icon": "📞",
                    "group_description": "Kontakt und Adressinformationen",
                    "collapsible": True,
                    "initially_expanded": True
                },
                "group_finanzen": {
                    "group_id": "grp-finanzen",
                    "group_name": "Finanzdaten", 
                    "group_order": 3,
                    "group_icon": "💰",
                    "group_description": "Finanzielle Zuordnungen",
                    "collapsible": True,
                    "initially_expanded": False
                }
            },
            
            # FELD-Zuordnungen (Verweise auf zentrale Metadaten + Frame-spezifische Anpassungen)
            "FIELD_ASSIGNMENTS": {
                "field_assignment_familienname": {
                    "field_metadata_id": "f001-fami-name-guid",  # Verweis auf zentrale Metadaten
                    "group_id": "grp-person-basis",
                    "field_order": 1,
                    "visible": True,
                    "enabled": True,
                    
                    # Frame-spezifische Überschreibungen (optional)
                    "overrides": {
                        "label": None,  # null = verwende Standard aus Metadaten
                        "tooltip": None,  # null = verwende Standard
                        "required": None,  # null = verwende Standard
                        "width_label": None,  # null = verwende Frame-Standard
                        "width_control": None,  # null = verwende Frame-Standard
                        "dropdown_context": "standard",  # Welche Dropdown-Config verwenden
                        "help_context": "default"  # Welche Hilfe-Config verwenden
                    }
                },
                
                "field_assignment_vorname": {
                    "field_metadata_id": "f002-vorn-name-guid",
                    "group_id": "grp-person-basis", 
                    "field_order": 2,
                    "visible": True,
                    "enabled": True,
                    "overrides": {}
                },
                
                "field_assignment_anrede": {
                    "field_metadata_id": "f003-anre-de-guid",
                    "group_id": "grp-person-basis",
                    "field_order": 3,
                    "visible": True,
                    "enabled": True,
                    "overrides": {
                        "dropdown_context": "formal",  # Spezielle Dropdown-Config für dieses Frame
                        "width_control": 150  # Kleinere Breite für Dropdown
                    }
                },
                
                "field_assignment_geburtsdatum": {
                    "field_metadata_id": "f004-gebu-datum-guid",
                    "group_id": "grp-person-basis",
                    "field_order": 4,
                    "visible": True,
                    "enabled": True,
                    "overrides": {}
                },
                
                "field_assignment_konto": {
                    "field_metadata_id": "f101-kont-nummer-guid",
                    "group_id": "grp-finanzen",
                    "field_order": 1,
                    "visible": True,
                    "enabled": True,
                    "overrides": {}
                },
                
                "field_assignment_konto_bezeichnung": {
                    "field_metadata_id": "f102-kont-bezeichnung-guid",
                    "group_id": "grp-finanzen", 
                    "field_order": 2,
                    "visible": True,
                    "enabled": True,
                    "overrides": {}
                },
                
                "field_assignment_waehrung": {
                    "field_metadata_id": "f103-waeh-rung-guid",
                    "group_id": "grp-finanzen",
                    "field_order": 3, 
                    "visible": True,
                    "enabled": True,
                    "overrides": {}
                },
                
                "field_assignment_finanzen_zuordnung": {
                    "field_metadata_id": "f104-finan-zuordnung-guid",
                    "group_id": "grp-finanzen",
                    "field_order": 4,
                    "visible": True,
                    "enabled": True,
                    "overrides": {}
                }
            }
        }
    
    @staticmethod
    def get_dropdown_data_structure():
        """
        Neue Dropdown-Daten Struktur (Schema-kompatibel)
        """
        return {
            "dropdown_version": "1.0", 
            "created_at": "2025-01-16T12:00:00Z",
            
            # Dropdown-Listen
            "dropdown_lists": {
                "anrede": {
                    "list_id": "anrede",
                    "list_name": "Anreden",
                    "list_type": "key_value",
                    "items": [
                        {"key": "m", "value": "Herr", "order": 1, "active": True},
                        {"key": "w", "value": "Frau", "order": 2, "active": True},
                        {"key": "d", "value": "Divers", "order": 3, "active": True}
                    ]
                },
                "anrede_formal": {
                    "list_id": "anrede_formal",
                    "list_name": "Formelle Anreden",
                    "list_type": "key_value", 
                    "items": [
                        {"key": "m", "value": "Sehr geehrter Herr", "order": 1, "active": True},
                        {"key": "w", "value": "Sehr geehrte Frau", "order": 2, "active": True},
                        {"key": "d", "value": "Sehr geehrte Damen und Herren", "order": 3, "active": True}
                    ]
                },
                "waehrung": {
                    "list_id": "waehrung",
                    "list_name": "Währungen",
                    "list_type": "key_value",
                    "items": [
                        {"key": "EUR", "value": "Euro", "order": 1, "active": True},
                        {"key": "USD", "value": "US-Dollar", "order": 2, "active": True},
                        {"key": "CHF", "value": "Schweizer Franken", "order": 3, "active": True}
                    ]
                }
            }
        }
    
    @staticmethod  
    def get_help_data_structure():
        """
        Neue Hilfe-Daten Struktur
        """
        return {
            "help_version": "1.0",
            "created_at": "2025-01-16T12:00:00Z",
            
            # Hilfe-Inhalte
            "help_contents": {
                "PERSDATEN_FAMILIENNAME": {
                    "help_id": "help-familienname-1",
                    "title": "Familienname",
                    "content": "Der Familienname ist der Nachname der Person. Bitte geben Sie alle Namensteile ein.",
                    "content_type": "text",
                    "language": "de",
                    "context": "default"
                },
                "PERSDATEN_VORNAME": {
                    "help_id": "help-vorname-1", 
                    "title": "Vorname",
                    "content": "Geben Sie alle Vornamen der Person ein, getrennt durch Leerzeichen.",
                    "content_type": "text",
                    "language": "de", 
                    "context": "default"
                }
            }
        }

def generate_optimized_ic_config(frame_definition, field_metadata):
    """
    Generiert IC-Konfiguration aus optimierter Struktur
    """
    ic_config = {}
    
    field_assignments = frame_definition.get("FIELD_ASSIGNMENTS", {})
    field_definitions = field_metadata.get("field_definitions", {})
    
    for assignment_key, assignment in field_assignments.items():
        field_metadata_id = assignment["field_metadata_id"]
        
        # Finde entsprechende Feld-Metadaten
        field_def = None
        for def_key, definition in field_definitions.items():
            if definition["field_id"] == field_metadata_id:
                field_def = definition
                break
        
        if not field_def:
            continue
        
        # IC-Key generieren
        table_group = field_def["table_group"]
        field_key = field_def["field_key"]
        ic_key = f"{table_group}_{field_key}"
        
        # Overrides anwenden
        overrides = assignment.get("overrides", {})
        
        # IC-Konfiguration erstellen
        ic_config[ic_key] = {
            "source_path": "root",
            "historical": field_def.get("historical", True),
            "display_ti_ab_short": True,
            "display_ti_val_short": False,
            "abdatum": field_def.get("historical", True),
            "display_ab": "all" if field_def.get("historical", True) else None,
            "display_val": None,
            "label": overrides.get("label") or field_def["label"],
            "tooltip": overrides.get("tooltip") or field_def.get("default_tooltip", ""),
            "type": field_def["field_type"],
            "conversion_in": field_def.get("conversion_in"),
            "conversion_out": field_def.get("conversion_out"),
            "ui_width_label": overrides.get("width_label"),
            "ui_width_value": overrides.get("width_control"),
            "ui_width_button": None,
            "ui_indent_ab": None,
            "dropdown": {},
            "viewtable": {},
            "help": {}
        }
        
        # Dropdown-Konfiguration
        if field_def["field_type"] == "dropdown":
            dropdown_context = overrides.get("dropdown_context", "default")
            dropdown_configs = field_def.get("dropdown_configs", [])
            for config in dropdown_configs:
                if config.get("context") == dropdown_context:
                    ic_config[ic_key]["dropdown"] = {
                        "table": config["table"],
                        "key": config["key"],
                        "value": config["value"]
                    }
                    break
        
        # ViewTable-Konfiguration
        if field_def["field_type"] == "viewtable":
            viewtable_configs = field_def.get("viewtable_configs", [])
            if viewtable_configs:
                ic_config[ic_key]["viewtable"] = {
                    "guid": viewtable_configs[0]["guid"]
                }
        
        # Hilfe-Konfiguration
        help_context = overrides.get("help_context", "default")
        help_configs = field_def.get("help_configs", [])
        for config in help_configs:
            if config.get("context") == help_context:
                ic_config[ic_key]["help"] = {
                    "table": config["table"],
                    "key": config["key"],
                    "value": config["value"]
                }
                break
    
    return ic_config

def test_optimized_structure():
    """Test der optimierten Struktur"""
    print("🏗️ Test der optimierten Datenstruktur")
    
    # Strukturen laden
    field_metadata = OptimizedDataStructure.get_field_metadata_structure()
    frame_definition = OptimizedDataStructure.get_frame_definition_structure()
    dropdown_data = OptimizedDataStructure.get_dropdown_data_structure()
    help_data = OptimizedDataStructure.get_help_data_structure()
    
    print(f"\n📋 Feld-Metadaten:")
    print(f"  - Feld-Definitionen: {len(field_metadata['field_definitions'])}")
    
    print(f"\n🖼️ Frame-Definition:")
    print(f"  - Gruppen: {len(frame_definition['GROUPS'])}")
    print(f"  - Feld-Zuordnungen: {len(frame_definition['FIELD_ASSIGNMENTS'])}")
    
    print(f"\n📋 Dropdown-Daten:")
    print(f"  - Listen: {len(dropdown_data['dropdown_lists'])}")
    
    print(f"\n❓ Hilfe-Daten:")
    print(f"  - Inhalte: {len(help_data['help_contents'])}")
    
    # IC-Konfiguration generieren
    ic_config = generate_optimized_ic_config(frame_definition, field_metadata)
    print(f"\n⚙️ Generierte IC-Konfiguration:")
    print(f"  - IC-Parameter: {len(ic_config)}")
    
    # Beispiel-Ausgabe
    for key, config in list(ic_config.items())[:2]:
        print(f"    ✓ {key}: {config['label']} ({config['type']})")
    
    return field_metadata, frame_definition, dropdown_data, help_data, ic_config

if __name__ == "__main__":
    test_optimized_structure()
