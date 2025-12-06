# -*- coding: utf-8 -*-
"""
Handler: Security System initialisieren

Erstellt sys_security Tabelle mit Standard-Profilen:
- Normal (Standard-Sätze)
- Template (Template-Sätze 5555...)
- System (System-Sätze 0000...)
- Deleted (Gelöschte Sätze)

AUTOR: Norbert Peters
DATUM: 06.12.2025
"""
import logging
from PyQt5.QtWidgets import QMessageBox
from pdvm_datenbank import PdvmDatenbank
from allgemeines import neue_guid

logger = logging.getLogger(__name__)

# Standard Security-Profile GUIDs (FEST für Referenzierung)
SECURITY_NORMAL_GUID = "11111111-1111-1111-1111-111111111111"
SECURITY_TEMPLATE_GUID = "22222222-2222-2222-2222-222222222222"
SECURITY_SYSTEM_GUID = "33333333-3333-3333-3333-333333333333"
SECURITY_DELETED_GUID = "44444444-4444-4444-4444-444444444444"


def execute(params: dict, context: dict, gcs) -> bool:
    """
    Handler: Initialisiert Security System
    
    Args:
        params: Handler-Parameter (leer)
        context: Kontext mit main_app
        gcs: Globale Systemsteuerung
        
    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    logger.info("🔐 === SECURITY SYSTEM INITIALISIERUNG ===")
    
    try:
        # Bestätigung vom User
        main_app = context.get('main_app')
        if main_app:
            reply = QMessageBox.question(
                main_app,
                "Security System initialisieren",
                "Soll das Security System initialisiert werden?\n\n"
                "Dies erstellt die sys_security Tabelle mit Standard-Profilen:\n"
                "- Normal (Standard-Sätze)\n"
                "- Template (Template-Sätze)\n"
                "- System (System-Sätze)\n"
                "- Deleted (Gelöschte Sätze)",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply != QMessageBox.Yes:
                logger.info("   ⚠️ Initialisierung abgebrochen")
                return False
        
        # SCHRITT 1: Tabelle anlegen
        logger.info("📂 SCHRITT 1: Erstelle sys_security Tabelle...")
        db = PdvmDatenbank('sys_security')
        logger.info("   ✅ Tabelle 'sys_security' angelegt")
        
        # SCHRITT 2: System-Satz (00000000-0000-0000-0000-000000000000)
        logger.info("📂 SCHRITT 2: Erstelle System-Satz...")
        system_guid = "00000000-0000-0000-0000-000000000000"
        system_data = {
            "ROOT": {
                "name": "System",
                "TABLE": "sys_security"
            }
        }
        db.speichern(system_guid, system_data)
        db.set_name(system_guid, "System")
        logger.info(f"   ✅ System-Satz angelegt (GUID: {system_guid})")
        
        # SCHRITT 3: Template-Satz (55555555-5555-5555-5555-555555555555)
        logger.info("📂 SCHRITT 3: Erstelle Template-Satz...")
        template_guid = "55555555-5555-5555-5555-555555555555"
        template_data = {
            "ROOT": {
                "name": "Templates",
                "TABLE": "sys_security"
            },
            "VISIBILITY": {
                "category": {
                    "type": "dropdown",
                    "label": "Kategorie",
                    "options": ["normal", "template", "system", "deleted"],
                    "display_order": 1,
                    "required": True,
                    "default": "normal"
                },
                "show_by_default": {
                    "type": "bool",
                    "label": "Standardmäßig anzeigen",
                    "display_order": 2,
                    "required": True,
                    "default": True
                },
                "requires_permission": {
                    "type": "string",
                    "label": "Benötigte Berechtigung",
                    "display_order": 3,
                    "required": False,
                    "default": ""
                }
            },
            "DATE_RANGE": {
                "valid_from": {
                    "type": "datetime",
                    "label": "Gültig von",
                    "display_order": 1,
                    "required": False,
                    "default": 1001.0
                },
                "valid_until": {
                    "type": "datetime",
                    "label": "Gültig bis",
                    "display_order": 2,
                    "required": False,
                    "default": 9999999.999999
                },
                "enforce_range": {
                    "type": "bool",
                    "label": "Datumsbereich erzwingen",
                    "display_order": 3,
                    "required": False,
                    "default": False
                }
            },
            "FILTER": {
                "pre_filter": {
                    "type": "json",
                    "label": "Pre-Filter Regeln",
                    "display_order": 1,
                    "required": False,
                    "default": ""
                },
                "post_filter": {
                    "type": "json",
                    "label": "Post-Filter Regeln",
                    "display_order": 2,
                    "required": False,
                    "default": ""
                }
            }
        }
        db.speichern(template_guid, template_data)
        db.set_name(template_guid, "Templates")
        logger.info(f"   ✅ Template-Satz angelegt (GUID: {template_guid})")
        
        # SCHRITT 4: Standard Security-Profile anlegen
        logger.info("📂 SCHRITT 4: Erstelle Standard Security-Profile...")
        
        # 4.1 NORMAL Profile
        logger.info("   🔹 NORMAL Profile...")
        normal_data = {
            "ROOT": {
                "name": "Normal",
                "TABLE": "sys_security"
            },
            "VISIBILITY": {
                "category": "normal",
                "show_by_default": True,
                "requires_permission": None
            },
            "DATE_RANGE": {
                "valid_from": 1001.0,
                "valid_until": 9999999.999999,
                "enforce_range": False
            },
            "FILTER": {
                "pre_filter": None,
                "post_filter": None
            }
        }
        db.speichern(SECURITY_NORMAL_GUID, normal_data)
        db.set_name(SECURITY_NORMAL_GUID, "Normal")
        logger.info(f"      ✅ NORMAL Profile: {SECURITY_NORMAL_GUID}")
        
        # 4.2 TEMPLATE Profile
        logger.info("   🔹 TEMPLATE Profile...")
        template_profile_data = {
            "ROOT": {
                "name": "Template",
                "TABLE": "sys_security"
            },
            "VISIBILITY": {
                "category": "template",
                "show_by_default": False,
                "requires_permission": "view_templates"
            },
            "DATE_RANGE": {
                "valid_from": 1001.0,
                "valid_until": 9999999.999999,
                "enforce_range": False
            },
            "FILTER": {
                "pre_filter": None,
                "post_filter": None
            }
        }
        db.speichern(SECURITY_TEMPLATE_GUID, template_profile_data)
        db.set_name(SECURITY_TEMPLATE_GUID, "Template")
        logger.info(f"      ✅ TEMPLATE Profile: {SECURITY_TEMPLATE_GUID}")
        
        # 4.3 SYSTEM Profile
        logger.info("   🔹 SYSTEM Profile...")
        system_profile_data = {
            "ROOT": {
                "name": "System",
                "TABLE": "sys_security"
            },
            "VISIBILITY": {
                "category": "system",
                "show_by_default": False,
                "requires_permission": "view_system"
            },
            "DATE_RANGE": {
                "valid_from": 1001.0,
                "valid_until": 9999999.999999,
                "enforce_range": False
            },
            "FILTER": {
                "pre_filter": None,
                "post_filter": None
            }
        }
        db.speichern(SECURITY_SYSTEM_GUID, system_profile_data)
        db.set_name(SECURITY_SYSTEM_GUID, "System")
        logger.info(f"      ✅ SYSTEM Profile: {SECURITY_SYSTEM_GUID}")
        
        # 4.4 DELETED Profile
        logger.info("   🔹 DELETED Profile...")
        deleted_profile_data = {
            "ROOT": {
                "name": "Deleted",
                "TABLE": "sys_security"
            },
            "VISIBILITY": {
                "category": "deleted",
                "show_by_default": False,
                "requires_permission": "view_deleted"
            },
            "DATE_RANGE": {
                "valid_from": 1001.0,
                "valid_until": 1001.0,  # Ungültig
                "enforce_range": True
            },
            "FILTER": {
                "pre_filter": None,
                "post_filter": None
            }
        }
        db.speichern(SECURITY_DELETED_GUID, deleted_profile_data)
        db.set_name(SECURITY_DELETED_GUID, "Deleted")
        logger.info(f"      ✅ DELETED Profile: {SECURITY_DELETED_GUID}")
        
        logger.info("✅ === SECURITY SYSTEM ERFOLGREICH INITIALISIERT ===")
        logger.info(f"   NORMAL:   {SECURITY_NORMAL_GUID}")
        logger.info(f"   TEMPLATE: {SECURITY_TEMPLATE_GUID}")
        logger.info(f"   SYSTEM:   {SECURITY_SYSTEM_GUID}")
        logger.info(f"   DELETED:  {SECURITY_DELETED_GUID}")
        
        # Erfolgs-Meldung
        if main_app:
            QMessageBox.information(
                main_app,
                "Security System initialisiert",
                "Security System wurde erfolgreich initialisiert!\n\n"
                "4 Standard-Profile wurden angelegt:\n"
                f"- Normal:   {SECURITY_NORMAL_GUID}\n"
                f"- Template: {SECURITY_TEMPLATE_GUID}\n"
                f"- System:   {SECURITY_SYSTEM_GUID}\n"
                f"- Deleted:  {SECURITY_DELETED_GUID}"
            )
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Security System Initialisierung fehlgeschlagen: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Fehler-Meldung
        if main_app:
            QMessageBox.critical(
                main_app,
                "Fehler",
                f"Security System Initialisierung fehlgeschlagen:\n\n{e}"
            )
        
        return False
