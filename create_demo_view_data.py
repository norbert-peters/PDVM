# create_demo_view_data.py
"""
Erstellt Demo-Daten für das moderne View-Widget
"""

import json
import logging
from pdvm_central_datenbank import PdvmCentralDatenbank
from datetime import datetime, date

logger = logging.getLogger(__name__)

def create_demo_view_configuration():
    """Erstellt die View-Konfiguration falls sie nicht existiert"""
    try:
        view_guid = "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"
        
        view_config = {
            "ROOT": {
                "stichtag": 3000001.0,
                "view_table": "persondaten",
                "history": True,
                "display_width": "150%"
            },
            "metadata": {
                "persondaten": {
                    "felder": [
                        {
                            "gruppe": "PersDaten",
                            "feld": "FAMILIENNAME",
                            "name": "Familienname",
                            "type": "string",
                            "default": "",
                            "lookup": None,
                            "ui": {
                                "searchable": True,
                                "sortable": True,
                                "sortDirection": "asc",
                                "sortByOriginal": False,
                                "width": "30%",
                                "filterType": "contains"
                            }
                        },
                        {
                            "gruppe": "PersDaten",
                            "feld": "VORNAME",
                            "name": "Vorname", 
                            "type": "string",
                            "default": "",
                            "lookup": None,
                            "ui": {
                                "searchable": True,
                                "sortable": True,
                                "sortDirection": "asc",
                                "sortByOriginal": False,
                                "width": "30%",
                                "filterType": "contains"
                            }
                        },
                        {
                            "gruppe": "PersDaten",
                            "feld": "GEBURTSDATUM",
                            "name": "Geburtsdatum",
                            "type": "date",
                            "default": None,
                            "lookup": None,
                            "ui": {
                                "searchable": True,
                                "sortable": True,
                                "sortDirection": "desc",
                                "sortByOriginal": True,
                                "width": "15%",
                                "filterType": "dateRange"
                            }
                        },
                        {
                            "gruppe": "PersDaten",
                            "feld": "ANREDE",
                            "name": "Anrede",
                            "type": "lookup",
                            "default": None,
                            "lookup": {
                                "table": "dropdowndaten",
                                "key": "ddaa6590-6d08-461b-a061-75faec26f4ba",
                                "value": "anrede"
                            },
                            "ui": {
                                "searchable": False,
                                "sortable": False,
                                "sortDirection": "asc",
                                "sortByOriginal": False,
                                "width": "10%",
                                "filterType": "dropdown"
                            }
                        },
                        {
                            "gruppe": "PersDaten",
                            "feld": "EMAIL",
                            "name": "E-Mail",
                            "type": "string",
                            "default": "",
                            "lookup": None,
                            "ui": {
                                "searchable": True,
                                "sortable": True,
                                "sortDirection": "asc",
                                "sortByOriginal": False,
                                "width": "25%",
                                "filterType": "contains"
                            }
                        }
                    ]
                }
            }
        }
        
        # View-Konfiguration speichern
        db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="viewdaten",
            guid=view_guid
        )
        
        db.speichern(view_guid, {"daten": view_config})
        logger.info(f"✅ View-Konfiguration erstellt: {view_guid}")
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen der View-Konfiguration: {e}")

def create_demo_person_data():
    """Erstellt Demo-Persondaten"""
    try:
        demo_persons = [
            {
                "_guid": "person-001",
                "FAMILIENNAME": "Müller",
                "VORNAME": "Hans",
                "GEBURTSDATUM": "1985-03-15",
                "ANREDE": "Herr",
                "EMAIL": "hans.mueller@example.com"
            },
            {
                "_guid": "person-002", 
                "FAMILIENNAME": "Schmidt",
                "VORNAME": "Anna",
                "GEBURTSDATUM": "1990-07-22",
                "ANREDE": "Frau",
                "EMAIL": "anna.schmidt@example.com"
            },
            {
                "_guid": "person-003",
                "FAMILIENNAME": "Weber",
                "VORNAME": "Klaus",
                "GEBURTSDATUM": "1978-11-08",
                "ANREDE": "Herr", 
                "EMAIL": "klaus.weber@example.com"
            },
            {
                "_guid": "person-004",
                "FAMILIENNAME": "Wagner",
                "VORNAME": "Maria",
                "GEBURTSDATUM": "1995-02-14",
                "ANREDE": "Frau",
                "EMAIL": "maria.wagner@example.com"
            },
            {
                "_guid": "person-005",
                "FAMILIENNAME": "Becker",
                "VORNAME": "Thomas",
                "GEBURTSDATUM": "1982-09-30",
                "ANREDE": "Herr",
                "EMAIL": "thomas.becker@example.com"
            }
        ]
        
        # Persondaten speichern
        for person in demo_persons:
            guid = person.pop("_guid")  # GUID entfernen für Speicherung
            
            db = PdvmCentralDatenbank(
                db_name="PdvmManager.db", 
                table_name="persondaten",
                guid=guid
            )
            
            db.speichern(guid, person)
        
        logger.info(f"✅ {len(demo_persons)} Demo-Persondaten erstellt")
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen der Demo-Persondaten: {e}")

def setup_demo_environment():
    """Richtet die komplette Demo-Umgebung ein"""
    logger.info("🔧 Erstelle Demo-Umgebung für modernes View-Widget...")
    
    create_demo_view_configuration()
    create_demo_person_data()
    
    logger.info("✅ Demo-Umgebung bereit!")
    logger.info("💡 Verwende pdvm_modern_view_test() zum Testen")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    setup_demo_environment()
