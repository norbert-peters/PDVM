# -*- coding: utf-8 -*-
"""
PDVM Optimized Data Manager
Implementiert die optimierte Datenarchitektur mit zentralen Feld-Metadaten
"""
import os
import sys
import json
import logging
from dataclasses import dataclass, field, asdict, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import uuid

# Logger Setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@dataclass
class FieldMetadata:
    """Zentrale Feld-Metadaten unter fester GUID"""
    
    # Eindeutige Identifikation
    field_guid: str
    field_key: str
    
    # Basis-Eigenschaften
    label: str
    tooltip: str = ""
    field_type: str = "text"  # text, dropdown, datetime, viewtable, boolean, number
    historical: bool = True
    
    # Gruppierung
    group_id: str = "default"
    sort_order: int = 100
    
    # UI-Eigenschaften
    ui_width_label: Optional[int] = None
    ui_width_value: Optional[int] = None
    ui_indent: int = 0
    
    # Datenkonvertierung
    conversion_in: Optional[str] = None
    conversion_out: Optional[str] = None
    
    # Validierung
    required: bool = False
    validation_pattern: Optional[str] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    
    # Metadaten
    created_at: str = ""
    modified_at: str = ""
    created_by: str = ""
    version: str = "1.0"
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.modified_at:
            self.modified_at = self.created_at
        if not self.field_guid:
            self.field_guid = str(uuid.uuid4())


@dataclass
class GroupDefinition:
    """Definition einer Feld-Gruppe"""
    
    group_id: str
    label: str
    description: str = ""
    sort_order: int = 100
    ui_style: str = "section"  # section, tab, accordion, inline
    collapsible: bool = False
    initially_collapsed: bool = False
    icon: str = ""
    
    # UI-Layout
    columns: int = 1
    spacing: int = 5
    
    # Metadaten
    created_at: str = ""
    version: str = "1.0"
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class FieldAssignment:
    """Zuweisung eines Feldes zu einem Frame mit Overrides"""
    
    field_guid: str
    frame_context: str  # z.B. "framedaten_person", "viewdaten_artikel"
    
    # Override-Möglichkeiten
    override_label: Optional[str] = None
    override_tooltip: Optional[str] = None
    override_required: Optional[bool] = None
    override_group_id: Optional[str] = None
    override_sort_order: Optional[int] = None
    
    # Frame-spezifische UI-Anpassungen
    override_ui_width_label: Optional[int] = None
    override_ui_width_value: Optional[int] = None
    override_ui_indent: Optional[int] = None
    
    # Sichtbarkeit
    visible: bool = True
    readonly: bool = False
    
    # Metadaten
    assigned_at: str = ""
    assigned_by: str = ""
    
    def __post_init__(self):
        if not self.assigned_at:
            self.assigned_at = datetime.now().isoformat()


@dataclass
class DropdownContext:
    """Dropdown-Konfiguration für verschiedene Kontexte"""
    
    context_id: str
    field_guid: str
    
    # Dropdown-Quelle
    source_type: str = "table"  # table, function, static, api
    source_table: str = ""
    source_key_field: str = ""
    source_value_field: str = ""
    source_function: Optional[str] = None
    source_static_values: Optional[Dict[str, str]] = None
    
    # Filter und Sortierung
    filter_conditions: Optional[Dict[str, Any]] = None
    sort_field: Optional[str] = None
    sort_direction: str = "ASC"
    
    # Caching
    cache_duration: int = 300  # Sekunden
    cache_key: Optional[str] = None
    
    # Metadaten
    created_at: str = ""
    version: str = "1.0"
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class HelpContext:
    """Hilfe-Konfiguration für verschiedene Kontexte"""
    
    context_id: str
    field_guid: str
    
    # Hilfe-Inhalt
    help_type: str = "text"  # text, html, markdown, url, function
    help_content: str = ""
    help_url: Optional[str] = None
    help_function: Optional[str] = None
    
    # UI-Eigenschaften
    help_position: str = "tooltip"  # tooltip, sidebar, modal, inline
    help_trigger: str = "hover"  # hover, click, focus
    help_icon: str = "❓"
    
    # Metadaten
    created_at: str = ""
    language: str = "de"
    version: str = "1.0"
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class TabDefinition:
    """Definition eines Tabs der mehrere Gruppen enthalten kann"""
    
    tab_id: str
    tab_name: str
    tab_description: str = ""
    tab_order: int = 100
    tab_icon: str = ""
    
    # UI-Eigenschaften
    tab_enabled: bool = True
    tab_visible: bool = True
    initially_active: bool = False
    
    # Gruppierung innerhalb des Tabs
    group_style: str = "sections"  # sections, accordion, inline, grid
    group_columns: int = 1
    group_spacing: int = 10
    
    # Scroll-Verhalten
    scrollable: bool = True
    max_height: Optional[int] = None
    
    # Metadaten
    created_at: str = ""
    version: str = "1.0"
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass 
class FrameLayoutDefinition:
    """Definition eines Frame-Layouts mit Tabs und Gruppen"""
    
    layout_type: str  # TAB_CONTAINER, SINGLE_FRAME, etc.
    layout_style: str = "default"  # default, mixed, etc.
    tabs: List[TabDefinition] = field(default_factory=list)
    groups: List[Dict] = field(default_factory=list)
    
    # Layout-Eigenschaften
    container_width: Optional[int] = None
    container_height: Optional[int] = None
    spacing: int = 10
    margins: int = 5
    
    # Metadaten
    created_at: str = ""
    version: str = "1.0"
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class OptimizedDataManager:
    """Verwaltet die optimierte Datenstruktur"""
    
    def __init__(self):
        # Zentrale Speicher
        self.field_metadata: Dict[str, FieldMetadata] = {}
        self.group_definitions: Dict[str, GroupDefinition] = {}
        self.field_assignments: Dict[str, List[FieldAssignment]] = {}  # frame_context -> assignments
        self.dropdown_contexts: Dict[str, List[DropdownContext]] = {}  # field_guid -> contexts
        self.help_contexts: Dict[str, List[HelpContext]] = {}  # field_guid -> contexts
        
        # Vereinfachte Speicher für Demo/Test
        self.central_fields: Dict[str, Dict] = {}  # field_id -> config
        self.field_groups: Dict[str, Dict] = {}  # group_id -> config
        
        # Tab- und Layout-Definitionen
        self.tab_definitions: Dict[str, TabDefinition] = {}
        self.frame_layout: Optional[FrameLayoutDefinition] = None
        
        # Gruppe-zu-Tab-Zuordnung
        self.group_tab_assignments: Dict[str, str] = {}  # group_id -> tab_id
        
        # Standard-Gruppen erstellen
        self.create_default_groups()
    
    def create_default_groups(self):
        """Erstellt Standard-Gruppen"""
        default_groups = [
            GroupDefinition("person_basic", "👤 Personen-Grunddaten", sort_order=10),
            GroupDefinition("person_contact", "📞 Kontaktdaten", sort_order=20),
            GroupDefinition("person_address", "🏠 Adressdaten", sort_order=30),
            GroupDefinition("finance_basic", "💰 Finanz-Grunddaten", sort_order=10),
            GroupDefinition("finance_account", "🏦 Kontodaten", sort_order=20),
            GroupDefinition("system_meta", "⚙️ System-Metadaten", sort_order=900),
            GroupDefinition("default", "📋 Allgemein", sort_order=999)
        ]
        
        for group in default_groups:
            self.group_definitions[group.group_id] = group
    
    def add_field_metadata(self, field_metadata: FieldMetadata) -> str:
        """
        Fügt Feld-Metadaten hinzu
        
        Returns:
            field_guid der hinzugefügten Metadaten
        """
        field_metadata.modified_at = datetime.now().isoformat()
        self.field_metadata[field_metadata.field_guid] = field_metadata
        
        logger.info(f"Feld-Metadaten hinzugefügt: {field_metadata.field_key} ({field_metadata.field_guid})")
        return field_metadata.field_guid
    
    def assign_field_to_frame(self, field_guid: str, frame_context: str, assignment: FieldAssignment):
        """Weist ein Feld einem Frame zu"""
        assignment.field_guid = field_guid
        assignment.frame_context = frame_context
        assignment.assigned_at = datetime.now().isoformat()
        
        if frame_context not in self.field_assignments:
            self.field_assignments[frame_context] = []
        
        self.field_assignments[frame_context].append(assignment)
        logger.info(f"Feld {field_guid} zu Frame {frame_context} zugewiesen")
    
    def add_dropdown_context(self, field_guid: str, dropdown_context: DropdownContext):
        """Fügt Dropdown-Kontext hinzu"""
        dropdown_context.field_guid = field_guid
        dropdown_context.created_at = datetime.now().isoformat()
        
        if field_guid not in self.dropdown_contexts:
            self.dropdown_contexts[field_guid] = []
        
        self.dropdown_contexts[field_guid].append(dropdown_context)
        logger.info(f"Dropdown-Kontext {dropdown_context.context_id} für Feld {field_guid} hinzugefügt")
    
    def add_help_context(self, field_guid: str, help_context: HelpContext):
        """Fügt Hilfe-Kontext hinzu"""
        help_context.field_guid = field_guid
        help_context.created_at = datetime.now().isoformat()
        
        if field_guid not in self.help_contexts:
            self.help_contexts[field_guid] = []
        
        self.help_contexts[field_guid].append(help_context)
        logger.info(f"Hilfe-Kontext {help_context.context_id} für Feld {field_guid} hinzugefügt")
    
    def add_tab_definition(self, tab_id: str, tab_def: TabDefinition):
        """Fügt eine Tab-Definition hinzu"""
        self.tab_definitions[tab_id] = tab_def
    
    def assign_group_to_tab(self, group_id: str, tab_id: str):
        """Weist eine Gruppe einem Tab zu"""
        if tab_id not in self.tab_definitions:
            raise ValueError(f"Tab '{tab_id}' existiert nicht")
        self.group_tab_assignments[group_id] = tab_id
    
    def get_tab_definition(self, tab_id: str) -> Optional[TabDefinition]:
        """Gibt eine Tab-Definition zurück"""
        return self.tab_definitions.get(tab_id)
    
    def get_groups_for_tab(self, tab_id: str) -> List[Dict]:
        """Gibt alle Gruppen zurück, die einem Tab zugeordnet sind"""
        groups = []
        for group_id, assigned_tab_id in self.group_tab_assignments.items():
            if assigned_tab_id == tab_id:
                if group_id in self.field_groups:
                    groups.append(self.field_groups[group_id])
        return groups
    
    def create_frame_layout(self, layout_type: str = "TAB_CONTAINER", 
                           style: str = "tabs") -> FrameLayoutDefinition:
        """Erstellt eine Frame-Layout-Definition"""
        if layout_type == "TAB_CONTAINER":
            return FrameLayoutDefinition(
                layout_type=layout_type,
                layout_style=style,
                tabs=list(self.tab_definitions.values()),
                groups=list(self.field_groups.values())
            )
        else:
            # Für andere Layout-Typen
            return FrameLayoutDefinition(
                layout_type=layout_type,
                layout_style=style,
                tabs=[],
                groups=list(self.field_groups.values())
            )
    
    def set_frame_layout(self, layout: FrameLayoutDefinition):
        """Setzt das Frame-Layout"""
        self.frame_layout = layout
    
    def get_frame_configuration(self, frame_context: str) -> Dict[str, Any]:
        """
        Generiert die vollständige Frame-Konfiguration
        
        Args:
            frame_context: Kontext des Frames (z.B. "framedaten_person")
            
        Returns:
            Vollständige Frame-Konfiguration mit gruppierten Feldern
        """
        if frame_context not in self.field_assignments:
            return {"groups": {}, "fields": [], "metadata": {}}
        
        # Gruppen sammeln
        groups_used = {}
        fields_config = []
        
        # Zugewiesene Felder verarbeiten
        assignments = self.field_assignments[frame_context]
        assignments.sort(key=lambda a: self.get_effective_sort_order(a))
        
        for assignment in assignments:
            if not assignment.visible:
                continue
            
            field_meta = self.field_metadata.get(assignment.field_guid)
            if not field_meta:
                logger.warning(f"Feld-Metadaten nicht gefunden: {assignment.field_guid}")
                continue
            
            # Effektive Werte berechnen (mit Overrides)
            effective_config = self.get_effective_field_config(field_meta, assignment)
            
            # Gruppe sammeln
            group_id = effective_config["group_id"]
            if group_id not in groups_used:
                group_def = self.group_definitions.get(group_id)
                if group_def:
                    groups_used[group_id] = asdict(group_def)
            
            # Dropdown-Kontext hinzufügen
            dropdown_config = self.get_dropdown_for_context(assignment.field_guid, frame_context)
            if dropdown_config:
                effective_config["dropdown_config"] = dropdown_config
            
            # Hilfe-Kontext hinzufügen
            help_config = self.get_help_for_context(assignment.field_guid, frame_context)
            if help_config:
                effective_config["help_config"] = help_config
            
            fields_config.append(effective_config)
        
        return {
            "frame_context": frame_context,
            "groups": groups_used,
            "fields": fields_config,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_fields": len(fields_config),
                "total_groups": len(groups_used)
            }
        }
    
    def get_effective_field_config(self, field_meta: FieldMetadata, assignment: FieldAssignment) -> Dict[str, Any]:
        """Berechnet die effektive Feld-Konfiguration mit Overrides"""
        config = asdict(field_meta)
        
        # Overrides anwenden
        if assignment.override_label is not None:
            config["label"] = assignment.override_label
        if assignment.override_tooltip is not None:
            config["tooltip"] = assignment.override_tooltip
        if assignment.override_required is not None:
            config["required"] = assignment.override_required
        if assignment.override_group_id is not None:
            config["group_id"] = assignment.override_group_id
        if assignment.override_sort_order is not None:
            config["sort_order"] = assignment.override_sort_order
        if assignment.override_ui_width_label is not None:
            config["ui_width_label"] = assignment.override_ui_width_label
        if assignment.override_ui_width_value is not None:
            config["ui_width_value"] = assignment.override_ui_width_value
        if assignment.override_ui_indent is not None:
            config["ui_indent"] = assignment.override_ui_indent
        
        # Assignment-spezifische Eigenschaften
        config["readonly"] = assignment.readonly
        config["visible"] = assignment.visible
        
        return config
    
    def get_effective_sort_order(self, assignment: FieldAssignment) -> int:
        """Berechnet die effektive Sortierreihenfolge"""
        if assignment.override_sort_order is not None:
            return assignment.override_sort_order
        
        field_meta = self.field_metadata.get(assignment.field_guid)
        if field_meta:
            return field_meta.sort_order
        
        return 999
    
    def get_dropdown_for_context(self, field_guid: str, context: str) -> Optional[Dict[str, Any]]:
        """Holt Dropdown-Konfiguration für einen spezifischen Kontext"""
        contexts = self.dropdown_contexts.get(field_guid, [])
        
        # Spezifischen Kontext suchen
        for dropdown_ctx in contexts:
            if dropdown_ctx.context_id == context:
                return asdict(dropdown_ctx)
        
        # Fallback: ersten verfügbaren Kontext verwenden
        if contexts:
            return asdict(contexts[0])
        
        return None
    
    def get_help_for_context(self, field_guid: str, context: str) -> Optional[Dict[str, Any]]:
        """Holt Hilfe-Konfiguration für einen spezifischen Kontext"""
        contexts = self.help_contexts.get(field_guid, [])
        
        # Spezifischen Kontext suchen
        for help_ctx in contexts:
            if help_ctx.context_id == context:
                return asdict(help_ctx)
        
        # Fallback: ersten verfügbaren Kontext verwenden
        if contexts:
            return asdict(contexts[0])
        
        return None
    
    def generate_ic_configuration(self, frame_context: str) -> Dict[str, Any]:
        """
        Generiert IC-Konfiguration aus der optimierten Struktur
        
        Args:
            frame_context: Kontext des Frames
            
        Returns:
            IC-Konfiguration im erwarteten Format
        """
        frame_config = self.get_frame_configuration(frame_context)
        ic_config = {}
        
        for field_config in frame_config["fields"]:
            field_key = field_config["field_key"]
            
            ic_config[field_key] = {
                "source_path": "root",
                "historical": field_config.get("historical", True),
                "display_ti_ab_short": True,
                "display_ti_val_short": False,
                "abdatum": field_config.get("historical", True),
                "display_ab": "all" if field_config.get("historical", True) else None,
                "display_val": None,
                "label": field_config.get("label", ""),
                "tooltip": field_config.get("tooltip", ""),
                "type": field_config.get("field_type", "text"),
                "conversion_in": field_config.get("conversion_in"),
                "conversion_out": field_config.get("conversion_out"),
                "ui_width_label": field_config.get("ui_width_label"),
                "ui_width_value": field_config.get("ui_width_value"),
                "ui_width_button": None,
                "ui_indent_ab": field_config.get("ui_indent"),
                "dropdown": field_config.get("dropdown_config", {}),
                "viewtable": field_config.get("viewtable_config", {}),
                "help": field_config.get("help_config", {}),
                "required": field_config.get("required", False),
                "readonly": field_config.get("readonly", False),
                "group_id": field_config.get("group_id", "default")
            }
        
        return ic_config
    
    def export_to_json(self, file_path: str):
        """Exportiert die gesamte Struktur als JSON"""
        export_data = {
            "field_metadata": {guid: asdict(meta) for guid, meta in self.field_metadata.items()},
            "group_definitions": {group_id: asdict(group) for group_id, group in self.group_definitions.items()},
            "field_assignments": {
                context: [asdict(assignment) for assignment in assignments]
                for context, assignments in self.field_assignments.items()
            },
            "dropdown_contexts": {
                field_guid: [asdict(ctx) for ctx in contexts]
                for field_guid, contexts in self.dropdown_contexts.items()
            },
            "help_contexts": {
                field_guid: [asdict(ctx) for ctx in contexts]
                for field_guid, contexts in self.help_contexts.items()
            },
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "version": "1.0",
                "total_fields": len(self.field_metadata),
                "total_groups": len(self.group_definitions),
                "total_contexts": len(self.field_assignments)
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Datenstruktur exportiert nach: {file_path}")
    
    def import_from_json(self, file_path: str):
        """Importiert die Struktur aus JSON"""
        with open(file_path, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
        
        # Field Metadata
        for guid, meta_dict in import_data.get("field_metadata", {}).items():
            self.field_metadata[guid] = FieldMetadata(**meta_dict)
        
        # Group Definitions
        for group_id, group_dict in import_data.get("group_definitions", {}).items():
            self.group_definitions[group_id] = GroupDefinition(**group_dict)
        
        # Field Assignments
        for context, assignments_list in import_data.get("field_assignments", {}).items():
            self.field_assignments[context] = [FieldAssignment(**assignment) for assignment in assignments_list]
        
        # Dropdown Contexts
        for field_guid, contexts_list in import_data.get("dropdown_contexts", {}).items():
            self.dropdown_contexts[field_guid] = [DropdownContext(**ctx) for ctx in contexts_list]
        
        # Help Contexts
        for field_guid, contexts_list in import_data.get("help_contexts", {}).items():
            self.help_contexts[field_guid] = [HelpContext(**ctx) for ctx in contexts_list]
        
        logger.info(f"Datenstruktur importiert von: {file_path}")
    
    def get_fields_in_group(self, group_id: str) -> List[Dict]:
        """Gibt alle Felder zurück, die einer Gruppe zugeordnet sind"""
        fields = []
        if group_id in self.field_groups:
            group = self.field_groups[group_id]
            for field_id in group.get('field_assignments', []):
                if field_id in self.central_fields:
                    field_config = self.central_fields[field_id].copy()
                    field_config['field_id'] = field_id
                    fields.append(field_config)
        return fields
    
    def add_central_field(self, field_id: str, field_config: Dict):
        """Fügt ein zentrales Feld hinzu (vereinfachte Schnittstelle)"""
        self.central_fields[field_id] = field_config
    
    def add_field_group(self, group_id: str, group_config: Dict):
        """Fügt eine Feldgruppe hinzu (vereinfachte Schnittstelle)"""
        self.field_groups[group_id] = group_config


def create_sample_optimized_structure():
    """Erstellt eine Beispiel-Struktur der optimierten Datenarchitektur"""
    manager = OptimizedDataManager()
    
    # Beispiel-Felder hinzufügen
    fields_data = [
        # Person Grunddaten
        ("person_name", "Name", "Vollständiger Name der Person", "text", "person_basic", 10),
        ("person_vorname", "Vorname", "Vorname der Person", "text", "person_basic", 20),
        ("person_geburtsdatum", "Geburtsdatum", "Geburtsdatum der Person", "datetime", "person_basic", 30),
        
        # Kontaktdaten
        ("person_email", "E-Mail", "E-Mail-Adresse", "text", "person_contact", 10),
        ("person_telefon", "Telefon", "Telefonnummer", "text", "person_contact", 20),
        ("person_anrede", "Anrede", "Anrede der Person", "dropdown", "person_contact", 5),
        
        # Finanz-Grunddaten
        ("finance_konto_nr", "Kontonummer", "Bankkontonummer", "text", "finance_account", 10),
        ("finance_blz", "BLZ", "Bankleitzahl", "text", "finance_account", 20),
        ("finance_iban", "IBAN", "Internationale Bankkontonummer", "text", "finance_account", 30),
    ]
    
    for field_key, label, tooltip, field_type, group_id, sort_order in fields_data:
        field_meta = FieldMetadata(
            field_guid=str(uuid.uuid4()),
            field_key=field_key,
            label=label,
            tooltip=tooltip,
            field_type=field_type,
            group_id=group_id,
            sort_order=sort_order,
            created_by="system"
        )
        field_guid = manager.add_field_metadata(field_meta)
        
        # Frame-Zuweisungen erstellen
        assignment = FieldAssignment(
            field_guid=field_guid,
            frame_context="framedaten_person",
            assigned_by="system"
        )
        manager.assign_field_to_frame(field_guid, "framedaten_person", assignment)
        
        # Dropdown für Anrede
        if field_key == "person_anrede":
            dropdown_ctx = DropdownContext(
                context_id="framedaten_person",
                field_guid=field_guid,
                source_type="static",
                source_static_values={
                    "herr": "Herr",
                    "frau": "Frau",
                    "dr": "Dr.",
                    "prof": "Prof."
                }
            )
            manager.add_dropdown_context(field_guid, dropdown_ctx)
        
        # Hilfe für alle Felder
        help_ctx = HelpContext(
            context_id="framedaten_person",
            field_guid=field_guid,
            help_type="text",
            help_content=f"Hilfe für {label}: {tooltip}",
            help_position="tooltip"
        )
        manager.add_help_context(field_guid, help_ctx)
    
    return manager


def test_optimized_structure():
    """Testet die optimierte Datenstruktur"""
    print("🏗️ Test der optimierten Datenstruktur")
    print("=" * 50)
    
    # Beispiel-Struktur erstellen
    manager = create_sample_optimized_structure()
    
    # Statistiken anzeigen
    print(f"📊 Statistiken:")
    print(f"   - Feld-Definitionen: {len(manager.field_metadata)}")
    print(f"   - Gruppen: {len(manager.group_definitions)}")
    print(f"   - Frame-Zuweisungen: {sum(len(assignments) for assignments in manager.field_assignments.values())}")
    print(f"   - Dropdown-Kontexte: {sum(len(contexts) for contexts in manager.dropdown_contexts.values())}")
    print(f"   - Hilfe-Kontexte: {sum(len(contexts) for contexts in manager.help_contexts.values())}")
    
    # Frame-Konfiguration generieren
    print(f"\n🎯 Frame-Konfiguration für 'framedaten_person':")
    frame_config = manager.get_frame_configuration("framedaten_person")
    
    print(f"   - Gruppen verwendet: {len(frame_config['groups'])}")
    for group_id, group_data in frame_config['groups'].items():
        print(f"     * {group_id}: {group_data['label']}")
    
    print(f"   - Felder konfiguriert: {len(frame_config['fields'])}")
    for field in frame_config['fields']:
        print(f"     * {field['field_key']} ({field['group_id']}): {field['label']}")
    
    # IC-Konfiguration generieren
    print(f"\n⚙️ IC-Konfiguration generieren:")
    ic_config = manager.generate_ic_configuration("framedaten_person")
    print(f"   - IC-Parameter generiert: {len(ic_config)}")
    
    # Beispiel IC-Parameter anzeigen
    for i, (key, config) in enumerate(list(ic_config.items())[:3]):
        print(f"     * {key}: {config['label']} (Gruppe: {config['group_id']})")
    
    # Export/Import Test
    export_file = "optimized_structure_test.json"
    print(f"\n💾 Export/Import Test:")
    manager.export_to_json(export_file)
    print(f"   - Exportiert nach: {export_file}")
    
    # Neuen Manager erstellen und importieren
    manager2 = OptimizedDataManager()
    manager2.import_from_json(export_file)
    print(f"   - Importiert: {len(manager2.field_metadata)} Felder")
    
    # Cleanup
    try:
        os.remove(export_file)
        print(f"   - Test-Datei bereinigt")
    except:
        pass
    
    print(f"\n✅ Test abgeschlossen!")
    return manager


if __name__ == "__main__":
    test_optimized_structure()
