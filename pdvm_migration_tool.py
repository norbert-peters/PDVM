# -*- coding: utf-8 -*-
"""
PDVM Migration Tool
Konvertiert bestehende redundante Framedaten/Viewdaten zur optimierten Struktur
"""
import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import uuid
import hashlib

# Import der optimierten Struktur
from pdvm_optimized_data_manager import (
    OptimizedDataManager, FieldMetadata, GroupDefinition, 
    FieldAssignment, DropdownContext, HelpContext
)

# Logger Setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class DataMigrationTool:
    """Tool zur Migration von redundanten zu optimierten Datenstrukturen"""
    
    def __init__(self):
        self.optimized_manager = OptimizedDataManager()
        self.field_mapping = {}  # old_key -> field_guid
        self.migration_stats = {
            "fields_processed": 0,
            "fields_migrated": 0,
            "duplicates_found": 0,
            "groups_created": 0,
            "dropdowns_migrated": 0,
            "helps_migrated": 0,
            "frames_processed": 0
        }
        
        # Feld-Schlüssel-Normalisierung für Duplikat-Erkennung
        self.field_signatures = {}  # signature -> field_guid
    
    def create_field_signature(self, field_data: Dict[str, Any]) -> str:
        """
        Erstellt eine eindeutige Signatur für ein Feld zur Duplikat-Erkennung
        
        Args:
            field_data: Feld-Daten aus der alten Struktur
            
        Returns:
            MD5-Hash der relevanten Feld-Eigenschaften
        """
        # Relevante Eigenschaften für Duplikat-Erkennung
        signature_data = {
            "key": field_data.get("key", "").lower().strip(),
            "type": field_data.get("type", "text").lower(),
            "label": field_data.get("label", "").strip(),
            # Dropdown-Konfiguration berücksichtigen
            "dropdown_table": field_data.get("dropdown_config", {}).get("table", ""),
            "dropdown_key": field_data.get("dropdown_config", {}).get("key", ""),
            "dropdown_value": field_data.get("dropdown_config", {}).get("value", "")
        }
        
        # JSON-String erstellen und hashen
        signature_str = json.dumps(signature_data, sort_keys=True)
        return hashlib.md5(signature_str.encode('utf-8')).hexdigest()
    
    def extract_group_from_context(self, section_name: str, field_key: str) -> str:
        """
        Extrahiert eine sinnvolle Gruppen-ID aus dem Kontext
        
        Args:
            section_name: Name des Bereichs/Abschnitts
            field_key: Schlüssel des Feldes
            
        Returns:
            Gruppen-ID für das Feld
        """
        # Mapping-Regeln für Gruppen-Erkennung
        group_mappings = {
            # Person-bezogene Felder
            ("person", "grunddaten"): "person_basic",
            ("person", "kontakt"): "person_contact", 
            ("person", "adresse"): "person_address",
            
            # Finanz-bezogene Felder
            ("finance", "konto"): "finance_account",
            ("finance", "grunddaten"): "finance_basic",
            
            # System-Felder
            ("system", "meta"): "system_meta",
            ("_", ""): "system_meta",  # Felder die mit _ beginnen
        }
        
        section_lower = section_name.lower()
        field_lower = field_key.lower()
        
        # Direkte Mappings prüfen
        for (section_pattern, field_pattern), group_id in group_mappings.items():
            if section_pattern in section_lower and field_pattern in field_lower:
                return group_id
        
        # Heuristische Gruppierung basierend auf Feldnamen
        if any(term in field_lower for term in ["name", "vorname", "nachname", "geburt"]):
            return "person_basic"
        elif any(term in field_lower for term in ["email", "telefon", "phone", "fax", "anrede"]):
            return "person_contact"
        elif any(term in field_lower for term in ["strasse", "plz", "ort", "land", "adresse"]):
            return "person_address"
        elif any(term in field_lower for term in ["konto", "iban", "blz", "bank"]):
            return "finance_account"
        elif any(term in field_lower for term in ["betrag", "summe", "preis", "kosten"]):
            return "finance_basic"
        elif field_key.startswith("_") or any(term in field_lower for term in ["guid", "id", "created", "modified"]):
            return "system_meta"
        
        # Fallback: Bereichsname als Gruppe verwenden
        clean_section = section_lower.replace("_", " ").strip()
        if clean_section and clean_section != "metadaten":
            return f"custom_{clean_section}"
        
        return "default"
    
    def migrate_field(self, field_data: Dict[str, Any], section_name: str, frame_context: str) -> Optional[str]:
        """
        Migriert ein einzelnes Feld zur optimierten Struktur
        
        Args:
            field_data: Feld-Daten aus der alten Struktur
            section_name: Name des Bereichs
            frame_context: Kontext des Frames
            
        Returns:
            field_guid des migrierten Feldes oder None bei Duplikat
        """
        self.migration_stats["fields_processed"] += 1
        
        # Duplikat-Prüfung
        signature = self.create_field_signature(field_data)
        if signature in self.field_signatures:
            logger.debug(f"Duplikat erkannt für Feld {field_data.get('key')}: {signature}")
            self.migration_stats["duplicates_found"] += 1
            return self.field_signatures[signature]
        
        # Neue Feld-Metadaten erstellen
        field_guid = str(uuid.uuid4())
        group_id = self.extract_group_from_context(section_name, field_data.get("key", ""))
        
        field_meta = FieldMetadata(
            field_guid=field_guid,
            field_key=field_data.get("key", ""),
            label=field_data.get("label", ""),
            tooltip=field_data.get("tooltip", ""),
            field_type=field_data.get("type", "text"),
            historical=field_data.get("historical", True),
            group_id=group_id,
            sort_order=field_data.get("sort_order", 100),
            ui_width_label=field_data.get("ui_width_label"),
            ui_width_value=field_data.get("ui_width_value"), 
            ui_indent=field_data.get("ui_indent", 0),
            conversion_in=field_data.get("conversion_in"),
            conversion_out=field_data.get("conversion_out"),
            required=field_data.get("required", False),
            created_by="migration_tool",
            version="1.0"
        )
        
        # Feld-Metadaten hinzufügen
        self.optimized_manager.add_field_metadata(field_meta)
        
        # Signatur registrieren
        self.field_signatures[signature] = field_guid
        
        # Frame-Zuweisung erstellen
        assignment = FieldAssignment(
            field_guid=field_guid,
            frame_context=frame_context,
            assigned_by="migration_tool"
        )
        self.optimized_manager.assign_field_to_frame(field_guid, frame_context, assignment)
        
        # Dropdown-Konfiguration migrieren
        dropdown_config = field_data.get("dropdown_config")
        if dropdown_config and any(dropdown_config.values()):
            dropdown_ctx = DropdownContext(
                context_id=frame_context,
                field_guid=field_guid,
                source_type="table",
                source_table=dropdown_config.get("table", ""),
                source_key_field=dropdown_config.get("key", ""),
                source_value_field=dropdown_config.get("value", "")
            )
            self.optimized_manager.add_dropdown_context(field_guid, dropdown_ctx)
            self.migration_stats["dropdowns_migrated"] += 1
        
        # Hilfe-Konfiguration migrieren
        help_content = field_data.get("help", "")
        if help_content or field_meta.tooltip:
            help_ctx = HelpContext(
                context_id=frame_context,
                field_guid=field_guid,
                help_type="text",
                help_content=help_content or f"Hilfe für {field_meta.label}",
                help_position="tooltip"
            )
            self.optimized_manager.add_help_context(field_guid, help_ctx)
            self.migration_stats["helps_migrated"] += 1
        
        self.migration_stats["fields_migrated"] += 1
        logger.debug(f"Feld migriert: {field_data.get('key')} -> {field_guid} (Gruppe: {group_id})")
        
        return field_guid
    
    def migrate_frame_data(self, frame_data: Dict[str, Any], frame_context: str):
        """
        Migriert komplette Frame-Daten zur optimierten Struktur
        
        Args:
            frame_data: Frame-Daten in alter Struktur
            frame_context: Kontext-ID des Frames
        """
        logger.info(f"Migriere Frame: {frame_context}")
        self.migration_stats["frames_processed"] += 1
        
        metadaten = frame_data.get("Metadaten", {})
        
        for section_name, section_data in metadaten.items():
            if section_name.startswith("_"):
                continue  # Meta-Bereiche überspringen
            
            logger.debug(f"Verarbeite Bereich: {section_name}")
            
            # Felder des Bereichs migrieren
            felder = section_data.get("felder", [])
            for field_data in felder:
                try:
                    self.migrate_field(field_data, section_name, frame_context)
                except Exception as e:
                    logger.error(f"Fehler bei Migration von Feld {field_data.get('key', 'unbekannt')}: {e}")
    
    def migrate_from_legacy_structure(self, legacy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hauptmethode zur Migration von Legacy-Strukturen
        
        Args:
            legacy_data: Daten in alter redundanter Struktur
            
        Returns:
            Migrations-Bericht
        """
        logger.info("🔄 Starte Migration von Legacy-Struktur zur optimierten Architektur")
        
        start_time = datetime.now()
        
        # Frame-Daten migrieren (falls vorhanden)
        if "framedaten" in legacy_data:
            self.migrate_frame_data(legacy_data["framedaten"], "framedaten_legacy")
        
        if "viewdaten" in legacy_data:
            self.migrate_frame_data(legacy_data["viewdaten"], "viewdaten_legacy")
        
        # Direkte Metadaten migrieren (falls vorhanden)
        if "Metadaten" in legacy_data:
            frame_data = {"Metadaten": legacy_data["Metadaten"]}
            self.migrate_frame_data(frame_data, "direct_metadaten")
        
        # Zusätzliche Gruppen aus Migration erstellen
        self.create_dynamic_groups()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Migrations-Bericht erstellen
        migration_report = {
            "migration_id": str(uuid.uuid4()),
            "started_at": start_time.isoformat(),
            "completed_at": end_time.isoformat(),
            "duration_seconds": duration,
            "statistics": self.migration_stats.copy(),
            "field_mapping": self.field_mapping.copy(),
            "optimized_structure": {
                "total_fields": len(self.optimized_manager.field_metadata),
                "total_groups": len(self.optimized_manager.group_definitions),
                "total_assignments": sum(len(assignments) for assignments in self.optimized_manager.field_assignments.values()),
                "total_dropdown_contexts": sum(len(contexts) for contexts in self.optimized_manager.dropdown_contexts.values()),
                "total_help_contexts": sum(len(contexts) for contexts in self.optimized_manager.help_contexts.values())
            }
        }
        
        logger.info(f"✅ Migration abgeschlossen in {duration:.2f}s")
        logger.info(f"   - Felder verarbeitet: {self.migration_stats['fields_processed']}")
        logger.info(f"   - Felder migriert: {self.migration_stats['fields_migrated']}")
        logger.info(f"   - Duplikate erkannt: {self.migration_stats['duplicates_found']}")
        
        return migration_report
    
    def create_dynamic_groups(self):
        """Erstellt dynamische Gruppen basierend auf migrierten Feldern"""
        groups_used = set()
        
        # Alle verwendeten Gruppen sammeln
        for field_meta in self.optimized_manager.field_metadata.values():
            groups_used.add(field_meta.group_id)
        
        # Fehlende Gruppen erstellen
        for group_id in groups_used:
            if group_id not in self.optimized_manager.group_definitions:
                # Gruppen-Label aus ID generieren
                label = group_id.replace("_", " ").title()
                if group_id.startswith("custom_"):
                    label = "📁 " + label.replace("Custom ", "")
                elif group_id == "default":
                    label = "📋 Allgemein"
                else:
                    label = "📂 " + label
                
                group_def = GroupDefinition(
                    group_id=group_id,
                    label=label,
                    description=f"Automatisch erstellte Gruppe aus Migration",
                    sort_order=500 + len(self.optimized_manager.group_definitions)
                )
                
                self.optimized_manager.group_definitions[group_id] = group_def
                self.migration_stats["groups_created"] += 1
                logger.debug(f"Dynamische Gruppe erstellt: {group_id} -> {label}")


def create_sample_legacy_data():
    """Erstellt Beispiel-Daten in der alten redundanten Struktur"""
    return {
        "framedaten": {
            "Metadaten": {
                "person_grunddaten": {
                    "felder": [
                        {
                            "key": "person_name",
                            "label": "Name",
                            "tooltip": "Vollständiger Name der Person",
                            "type": "text",
                            "historical": True,
                            "sort_order": 10,
                            "ui_width_label": 120,
                            "ui_width_value": 200
                        },
                        {
                            "key": "person_vorname", 
                            "label": "Vorname",
                            "tooltip": "Vorname der Person",
                            "type": "text",
                            "historical": True,
                            "sort_order": 20
                        },
                        {
                            "key": "person_geburtsdatum",
                            "label": "Geburtsdatum",
                            "tooltip": "Geburtsdatum der Person",
                            "type": "datetime",
                            "historical": True,
                            "sort_order": 30
                        }
                    ]
                },
                "person_kontakt": {
                    "felder": [
                        {
                            "key": "person_email",
                            "label": "E-Mail",
                            "tooltip": "E-Mail-Adresse",
                            "type": "text",
                            "historical": False,
                            "sort_order": 10
                        },
                        {
                            "key": "person_telefon",
                            "label": "Telefon",
                            "tooltip": "Telefonnummer",
                            "type": "text",
                            "historical": False,
                            "sort_order": 20
                        },
                        {
                            "key": "person_anrede",
                            "label": "Anrede",
                            "tooltip": "Anrede der Person",
                            "type": "dropdown",
                            "historical": False,
                            "sort_order": 5,
                            "dropdown_config": {
                                "table": "anreden",
                                "key": "anrede_id",
                                "value": "anrede_text"
                            }
                        }
                    ]
                }
            }
        },
        "viewdaten": {
            "Metadaten": {
                "artikel_grunddaten": {
                    "felder": [
                        # Duplikat zu framedaten - sollte erkannt werden
                        {
                            "key": "person_name",
                            "label": "Name",
                            "tooltip": "Vollständiger Name der Person",
                            "type": "text",
                            "historical": True,
                            "sort_order": 10
                        },
                        {
                            "key": "artikel_nummer",
                            "label": "Artikelnummer",
                            "tooltip": "Eindeutige Artikelnummer",
                            "type": "text",
                            "historical": True,
                            "sort_order": 10
                        },
                        {
                            "key": "artikel_bezeichnung",
                            "label": "Bezeichnung",
                            "tooltip": "Artikelbezeichnung",
                            "type": "text",
                            "historical": True,
                            "sort_order": 20
                        }
                    ]
                },
                "artikel_preise": {
                    "felder": [
                        {
                            "key": "artikel_preis_vk",
                            "label": "VK-Preis",
                            "tooltip": "Verkaufspreis",
                            "type": "number",
                            "historical": True,
                            "sort_order": 10,
                            "ui_width_value": 100
                        },
                        {
                            "key": "artikel_preis_ek",
                            "label": "EK-Preis",
                            "tooltip": "Einkaufspreis",
                            "type": "number",
                            "historical": True,
                            "sort_order": 20,
                            "ui_width_value": 100
                        }
                    ]
                }
            }
        }
    }


def test_migration_tool():
    """Testet das Migration-Tool"""
    print("🔄 Test des Migration-Tools")
    print("=" * 50)
    
    # Legacy-Daten erstellen
    legacy_data = create_sample_legacy_data()
    print(f"📊 Legacy-Daten vorbereitet:")
    
    # Framedaten analysieren
    framedaten_sections = len(legacy_data["framedaten"]["Metadaten"])
    framedaten_fields = sum(len(section["felder"]) for section in legacy_data["framedaten"]["Metadaten"].values())
    print(f"   - Framedaten: {framedaten_sections} Bereiche, {framedaten_fields} Felder")
    
    # Viewdaten analysieren
    viewdaten_sections = len(legacy_data["viewdaten"]["Metadaten"])
    viewdaten_fields = sum(len(section["felder"]) for section in legacy_data["viewdaten"]["Metadaten"].values())
    print(f"   - Viewdaten: {viewdaten_sections} Bereiche, {viewdaten_fields} Felder")
    
    total_legacy_fields = framedaten_fields + viewdaten_fields
    print(f"   - Gesamt: {total_legacy_fields} Felder")
    
    # Migration durchführen
    print(f"\n🏗️ Migration starten...")
    migration_tool = DataMigrationTool()
    migration_report = migration_tool.migrate_from_legacy_structure(legacy_data)
    
    # Migrations-Bericht anzeigen
    print(f"\n📋 Migrations-Bericht:")
    stats = migration_report["statistics"]
    print(f"   - Verarbeitete Felder: {stats['fields_processed']}")
    print(f"   - Migrierte Felder: {stats['fields_migrated']}")
    print(f"   - Erkannte Duplikate: {stats['duplicates_found']}")
    print(f"   - Erstellte Gruppen: {stats['groups_created']}")
    print(f"   - Migrierte Dropdowns: {stats['dropdowns_migrated']}")
    print(f"   - Migrierte Hilfen: {stats['helps_migrated']}")
    print(f"   - Verarbeitete Frames: {stats['frames_processed']}")
    print(f"   - Dauer: {migration_report['duration_seconds']:.2f}s")
    
    # Optimierte Struktur analysieren
    print(f"\n🎯 Optimierte Struktur:")
    opt_stats = migration_report["optimized_structure"]
    print(f"   - Feld-Definitionen: {opt_stats['total_fields']}")
    print(f"   - Gruppen-Definitionen: {opt_stats['total_groups']}")
    print(f"   - Frame-Zuweisungen: {opt_stats['total_assignments']}")
    print(f"   - Dropdown-Kontexte: {opt_stats['total_dropdown_contexts']}")
    print(f"   - Hilfe-Kontexte: {opt_stats['total_help_contexts']}")
    
    # Duplikat-Effizienz prüfen
    deduplication_rate = (stats['duplicates_found'] / stats['fields_processed']) * 100 if stats['fields_processed'] > 0 else 0
    print(f"   - Deduplizierungs-Rate: {deduplication_rate:.1f}%")
    
    # Beispiel Frame-Konfiguration generieren
    print(f"\n🔧 Test Frame-Konfiguration:")
    frame_config = migration_tool.optimized_manager.get_frame_configuration("framedaten_legacy")
    print(f"   - Gruppen für framedaten_legacy: {len(frame_config['groups'])}")
    for group_id, group_data in list(frame_config['groups'].items())[:3]:
        print(f"     * {group_id}: {group_data['label']}")
    
    print(f"   - Felder für framedaten_legacy: {len(frame_config['fields'])}")
    for field in list(frame_config['fields'])[:5]:
        print(f"     * {field['field_key']} ({field['group_id']}): {field['label']}")
    
    # Export der migrierten Struktur
    export_file = "migrated_structure.json"
    migration_tool.optimized_manager.export_to_json(export_file)
    print(f"\n💾 Migrierte Struktur exportiert: {export_file}")
    
    # Cleanup
    try:
        os.remove(export_file)
        print(f"   - Test-Datei bereinigt")
    except:
        pass
    
    print(f"\n✅ Migration-Test abgeschlossen!")
    
    return migration_tool, migration_report


if __name__ == "__main__":
    test_migration_tool()
