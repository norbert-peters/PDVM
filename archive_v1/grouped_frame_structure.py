# -*- coding: utf-8 -*-
"""
Erweiterte Framedaten-Struktur mit Gruppierungen für InputFrames
"""
import json
from typing import Dict, List, Any, Optional

class GroupedFrameDataStructure:
    """
    Erweiterte Framedaten-Struktur die Gruppierungen unterstützt
    für die Integration mit InputFrames
    """
    
    @staticmethod
    def get_root_parameter_groups():
        """Definition der ROOT-Parameter-Gruppen für InputFrames"""
        return {
            "Basis-Konfiguration": {
                "group_order": 1,
                "description": "Grundlegende Frame-Einstellungen",
                "fields": [
                    {
                        "key": "root_table",
                        "label": "Root Tabelle",
                        "type": "dropdown",
                        "tooltip": "Haupttabelle für diese Konfiguration",
                        "dropdown_config": {
                            "table": "system_tables",
                            "key": "table_list",
                            "value": "table_name"
                        },
                        "required": True
                    },
                    {
                        "key": "view_guid",
                        "label": "View GUID",
                        "type": "text",
                        "tooltip": "GUID der zugehörigen View",
                        "validation": "uuid",
                        "required": True
                    },
                    {
                        "key": "header_text",
                        "label": "Header Text",
                        "type": "text",
                        "tooltip": "Titel des Frames",
                        "required": True
                    }
                ]
            },
            "Anzeige-Einstellungen": {
                "group_order": 2,
                "description": "Datum und Zeit Anzeige-Optionen",
                "fields": [
                    {
                        "key": "display_st",
                        "label": "Display Style",
                        "type": "dropdown",
                        "tooltip": "Art der Datumsanzeige",
                        "dropdown_config": {
                            "options": ["only_date", "full_datetime", "short"]
                        },
                        "default": "only_date"
                    },
                    {
                        "key": "display_time_short",
                        "label": "Kurze Zeitanzeige",
                        "type": "boolean",
                        "tooltip": "Verkürzte Zeitanzeige verwenden",
                        "default": True
                    }
                ]
            },
            "Layout-Parameter": {
                "group_order": 3,
                "description": "UI-Layout und Größen-Einstellungen",
                "fields": [
                    {
                        "key": "width_indent_ab",
                        "label": "Einrückung Ab-Datum",
                        "type": "number",
                        "tooltip": "Einrückung für Ab-Datum Spalte",
                        "min": 0,
                        "max": 100,
                        "default": 0
                    },
                    {
                        "key": "width_label",
                        "label": "Breite Label",
                        "type": "number",
                        "tooltip": "Breite der Label-Spalte",
                        "min": 50,
                        "max": 300,
                        "default": 120
                    },
                    {
                        "key": "width_button",
                        "label": "Breite Button",
                        "type": "number",
                        "tooltip": "Breite der Button-Spalte",
                        "min": 30,
                        "max": 150,
                        "default": 60
                    },
                    {
                        "key": "width_control",
                        "label": "Breite Control",
                        "type": "number",
                        "tooltip": "Breite der Control-Spalte",
                        "min": 100,
                        "max": 500,
                        "default": 250
                    },
                    {
                        "key": "width_frame",
                        "label": "Breite Frame",
                        "type": "number",
                        "tooltip": "Gesamtbreite des Frames",
                        "min": 400,
                        "max": 1200,
                        "default": 600
                    }
                ]
            }
        }
    
    @staticmethod
    def get_ic_parameter_groups():
        """Definition der IC-Parameter-Gruppen für InputFrames"""
        return {
            "Basis-Parameter": {
                "group_order": 1,
                "description": "Grundlegende Feld-Einstellungen",
                "fields": [
                    {
                        "key": "label",
                        "label": "Feld-Label",
                        "type": "text",
                        "tooltip": "Anzeigename des Feldes",
                        "required": True
                    },
                    {
                        "key": "tooltip",
                        "label": "Tooltip",
                        "type": "text",
                        "tooltip": "Hilfetext für das Feld"
                    },
                    {
                        "key": "type",
                        "label": "Feldtyp",
                        "type": "dropdown",
                        "tooltip": "Art des Eingabefeldes",
                        "dropdown_config": {
                            "options": ["text", "dropdown", "datetime", "viewtable", "boolean", "number"]
                        },
                        "required": True
                    },
                    {
                        "key": "required",
                        "label": "Pflichtfeld",
                        "type": "boolean",
                        "tooltip": "Ist dieses Feld ein Pflichtfeld?",
                        "default": False
                    }
                ]
            },
            "Historisierung": {
                "group_order": 2,
                "description": "Einstellungen für historische Daten",
                "fields": [
                    {
                        "key": "historical",
                        "label": "Historisch",
                        "type": "boolean",
                        "tooltip": "Soll dieses Feld historisiert werden?",
                        "default": True
                    },
                    {
                        "key": "abdatum",
                        "label": "Ab-Datum",
                        "type": "boolean",
                        "tooltip": "Ab-Datum anzeigen?",
                        "default": True,
                        "depends_on": "historical"
                    },
                    {
                        "key": "display_ab",
                        "label": "Display Ab-Datum",
                        "type": "dropdown",
                        "tooltip": "Wie soll das Ab-Datum angezeigt werden?",
                        "dropdown_config": {
                            "options": ["all", "current", "none"]
                        },
                        "default": "all",
                        "depends_on": "historical"
                    }
                ]
            },
            "UI-Layout": {
                "group_order": 3,
                "description": "Benutzeroberflächen-Einstellungen",
                "fields": [
                    {
                        "key": "ui_width_label",
                        "label": "Breite Label",
                        "type": "number",
                        "tooltip": "Individuelle Label-Breite (null = Standard)",
                        "min": 50,
                        "max": 300,
                        "nullable": True
                    },
                    {
                        "key": "ui_width_value",
                        "label": "Breite Wert",
                        "type": "number",
                        "tooltip": "Individuelle Wert-Breite (null = Standard)",
                        "min": 100,
                        "max": 500,
                        "nullable": True
                    },
                    {
                        "key": "ui_width_button",
                        "label": "Breite Button",
                        "type": "number",
                        "tooltip": "Individuelle Button-Breite (null = Standard)",
                        "min": 30,
                        "max": 150,
                        "nullable": True
                    },
                    {
                        "key": "ui_indent_ab",
                        "label": "Einrückung Ab-Datum",
                        "type": "number",
                        "tooltip": "Individuelle Einrückung für Ab-Datum",
                        "min": 0,
                        "max": 100,
                        "nullable": True
                    }
                ]
            },
            "Dropdown-Konfiguration": {
                "group_order": 4,
                "description": "Einstellungen für Dropdown-Felder",
                "fields": [
                    {
                        "key": "dropdown_table",
                        "label": "Dropdown Tabelle",
                        "type": "text",
                        "tooltip": "Tabelle für Dropdown-Werte",
                        "show_if": {"type": "dropdown"}
                    },
                    {
                        "key": "dropdown_key",
                        "label": "Dropdown Key",
                        "type": "text",
                        "tooltip": "Schlüssel für Dropdown-Abfrage",
                        "show_if": {"type": "dropdown"}
                    },
                    {
                        "key": "dropdown_value",
                        "label": "Dropdown Value",
                        "type": "text",
                        "tooltip": "Wert-Feld für Dropdown",
                        "show_if": {"type": "dropdown"}
                    }
                ]
            },
            "ViewTable-Konfiguration": {
                "group_order": 5,
                "description": "Einstellungen für ViewTable-Felder",
                "fields": [
                    {
                        "key": "viewtable_guid",
                        "label": "ViewTable GUID",
                        "type": "text",
                        "tooltip": "GUID der ViewTable-Konfiguration",
                        "validation": "uuid",
                        "show_if": {"type": "viewtable"}
                    },
                    {
                        "key": "viewtable_mode",
                        "label": "ViewTable Modus",
                        "type": "dropdown",
                        "tooltip": "Anzeigemodus der ViewTable",
                        "dropdown_config": {
                            "options": ["readonly", "editable", "selectable"]
                        },
                        "default": "readonly",
                        "show_if": {"type": "viewtable"}
                    }
                ]
            },
            "Konvertierung": {
                "group_order": 6,
                "description": "Datenkonvertierung und Validierung",
                "fields": [
                    {
                        "key": "conversion_in",
                        "label": "Eingabe-Konvertierung",
                        "type": "text",
                        "tooltip": "Funktion für Eingabe-Konvertierung",
                        "nullable": True
                    },
                    {
                        "key": "conversion_out",
                        "label": "Ausgabe-Konvertierung",
                        "type": "text",
                        "tooltip": "Funktion für Ausgabe-Konvertierung",
                        "nullable": True
                    },
                    {
                        "key": "validation_rule",
                        "label": "Validierungsregel",
                        "type": "text",
                        "tooltip": "Regex oder Funktionsname für Validierung",
                        "nullable": True
                    }
                ]
            },
            "Hilfe-System": {
                "group_order": 7,
                "description": "Hilfe und Dokumentation",
                "fields": [
                    {
                        "key": "help_table",
                        "label": "Hilfe Tabelle",
                        "type": "text",
                        "tooltip": "Tabelle für Hilfe-Inhalte",
                        "default": "beschreibungen"
                    },
                    {
                        "key": "help_key",
                        "label": "Hilfe Key",
                        "type": "text",
                        "tooltip": "Schlüssel für Hilfe-Abfrage"
                    },
                    {
                        "key": "help_value",
                        "label": "Hilfe Value",
                        "type": "text",
                        "tooltip": "Wert-Feld für Hilfe-Inhalt"
                    }
                ]
            }
        }

    @staticmethod
    def generate_framedaten_for_groups(parameter_type="root"):
        """
        Generiert Framedaten-JSON für die Parameter-Gruppen
        Dies wird für die InputFrame-Integration benötigt
        """
        if parameter_type == "root":
            groups = GroupedFrameDataStructure.get_root_parameter_groups()
            base_key = "ROOT_PARAMETER"
        else:
            groups = GroupedFrameDataStructure.get_ic_parameter_groups()
            base_key = "IC_PARAMETER"
        
        framedaten = {
            "ROOT": {
                "root_table": "system_parameters",
                "view_guid": "system-parameter-view-guid",
                "header_text": f"{parameter_type.upper()} Parameter Editor",
                "display_st": "only_date",
                "display_time_short": True,
                "width_indent_ab": 0,
                "width_label": 150,
                "width_button": 60,
                "width_control": 300,
                "width_frame": 700
            },
            "Metadaten": {}
        }
        
        # Für jede Gruppe einen Metadaten-Bereich erstellen
        for group_name, group_config in groups.items():
            group_key = f"{base_key}_{group_name.upper().replace('-', '_').replace(' ', '_')}"
            
            framedaten["Metadaten"][group_key] = {}
            
            # Felder der Gruppe hinzufügen
            for field in group_config["fields"]:
                field_key = f"{group_key}_{field['key'].upper()}"
                
                # IC-Parameter basierend auf Feldtyp generieren
                ic_config = {
                    "source_path": "root",
                    "historical": field.get("historical", False),
                    "display_ti_ab_short": True,
                    "display_ti_val_short": False,
                    "abdatum": field.get("historical", False),
                    "display_ab": "all" if field.get("historical", False) else None,
                    "display_val": None,
                    "label": field["label"],
                    "tooltip": field.get("tooltip", ""),
                    "type": field["type"],
                    "conversion_in": None,
                    "conversion_out": None,
                    "ui_width_label": None,
                    "ui_width_value": None,
                    "ui_width_button": None,
                    "ui_indent_ab": None,
                    "dropdown": {},
                    "help": {}
                }
                
                # Dropdown-Konfiguration hinzufügen
                if field["type"] == "dropdown" and "dropdown_config" in field:
                    ic_config["dropdown"] = field["dropdown_config"]
                
                # ViewTable-Konfiguration hinzufügen
                if field["type"] == "viewtable" and "viewtable_config" in field:
                    ic_config["viewtable"] = field["viewtable_config"]
                
                framedaten["Metadaten"][field_key] = ic_config
        
        return framedaten

    @staticmethod
    def create_inputframe_call_data(parameter_type="root", parent_data=None):
        """
        Erstellt call_data für InputFrame basierend auf Parameter-Typ
        """
        if parameter_type == "root":
            frame_guid = "root-parameter-frame-guid"
            title = "ROOT Parameter bearbeiten"
        else:
            frame_guid = "ic-parameter-frame-guid"
            title = "IC Parameter bearbeiten"
        
        call_data = {
            "user_guid": "system-user-guid",
            "frame_guid": frame_guid,
            "mode": 1,  # Editiermodus
            "language": "de",
            "title": title,
            "parent_data": parent_data or {},
            "callback_function": "on_parameter_saved"
        }
        
        return call_data

def test_grouped_structure():
    """Test der gruppierten Struktur"""
    print("🏗️ Test der gruppierten Framedaten-Struktur")
    
    # ROOT-Parameter Framedaten
    root_framedaten = GroupedFrameDataStructure.generate_framedaten_for_groups("root")
    print(f"\n📋 ROOT-Parameter Framedaten:")
    print(f"  - ROOT-Felder: {len(root_framedaten['ROOT'])}")
    print(f"  - Metadaten-Bereiche: {len(root_framedaten['Metadaten'])}")
    
    # IC-Parameter Framedaten
    ic_framedaten = GroupedFrameDataStructure.generate_framedaten_for_groups("ic")
    print(f"\n⚙️ IC-Parameter Framedaten:")
    print(f"  - ROOT-Felder: {len(ic_framedaten['ROOT'])}")
    print(f"  - Metadaten-Bereiche: {len(ic_framedaten['Metadaten'])}")
    
    # Call-Data Beispiele
    root_call_data = GroupedFrameDataStructure.create_inputframe_call_data("root")
    ic_call_data = GroupedFrameDataStructure.create_inputframe_call_data("ic")
    
    print(f"\n📞 Call-Data erstellt:")
    print(f"  - ROOT Frame GUID: {root_call_data['frame_guid']}")
    print(f"  - IC Frame GUID: {ic_call_data['frame_guid']}")
    
    return root_framedaten, ic_framedaten, root_call_data, ic_call_data

if __name__ == "__main__":
    test_grouped_structure()
