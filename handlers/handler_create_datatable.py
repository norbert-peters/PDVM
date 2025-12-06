# -*- coding: utf-8 -*-
"""
Handler: Neue Datentabelle anlegen

ABLAUF:
1. Abfrage Tabellenname (darf nicht mit sys_ beginnen)
2. Prüfung ob Tabelle bereits existiert
3. Tabelle via PdvmDatenbank anlegen
4. System-Satz (00000000-0000-0000-0000-000000000000) anlegen
5. Template-Satz (55555555-5555-5555-5555-555555555555) anlegen
6. Dialog-/Frame-/View-Daten anlegen für sofortige Template-Pflege

AUTOR: Norbert Peters
DATUM: 05.12.2025
"""
import logging
import sqlite3
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox

from pdvm_central_systemsteuerung import get_gcs
from pdvm_datenbank import PdvmDatenbank
from pdvm_central_datenbank import PdvmCentralDatenbank
from allgemeines import neue_guid

logger = logging.getLogger(__name__)


class CreateDatatableDialog(QDialog):
    """Dialog für Tabellen-Erstellung"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.table_name = None
        
        self.setWindowTitle("Neue Datentabelle anlegen")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        self._init_ui()
    
    def _init_ui(self):
        """UI aufbauen"""
        layout = QVBoxLayout(self)
        
        # Info-Text
        info = QLabel(
            "Legt eine neue Datentabelle im aktuellen Mandanten an.\n\n"
            "Die Tabelle wird automatisch mit System- und Template-Sätzen befüllt.\n"
            "Über 'Dialog Test' können Sie sofort die Templates pflegen."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        layout.addSpacing(20)
        
        # Tabellenname
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Tabellenname:"))
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("z.B. artikeldaten, kundendaten, ...")
        self.name_input.textChanged.connect(self._validate_input)
        name_layout.addWidget(self.name_input)
        
        layout.addLayout(name_layout)
        
        # Validierungs-Label
        self.validation_label = QLabel("")
        self.validation_label.setStyleSheet("color: #e74c3c; font-size: 9pt;")
        layout.addWidget(self.validation_label)
        
        layout.addSpacing(20)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.create_btn = QPushButton("Tabelle anlegen")
        self.create_btn.clicked.connect(self._create_table)
        self.create_btn.setEnabled(False)
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        button_layout.addWidget(self.create_btn)
        
        layout.addLayout(button_layout)
    
    def _validate_input(self):
        """Validiert Eingabe und aktiviert/deaktiviert Button"""
        table_name = self.name_input.text().strip().lower()
        
        if not table_name:
            self.validation_label.setText("")
            self.create_btn.setEnabled(False)
            return
        
        # Validierung 1: sys_ Präfix
        if table_name.startswith('sys_'):
            self.validation_label.setText("❌ Tabellenname darf nicht mit 'sys_' beginnen")
            self.create_btn.setEnabled(False)
            return
        
        # Validierung 2: Nur Buchstaben, Zahlen, Unterstrich
        if not all(c.isalnum() or c == '_' for c in table_name):
            self.validation_label.setText("❌ Nur Buchstaben, Zahlen und '_' erlaubt")
            self.create_btn.setEnabled(False)
            return
        
        # Validierung 3: Muss mit Buchstabe beginnen
        if not table_name[0].isalpha():
            self.validation_label.setText("❌ Tabellenname muss mit Buchstabe beginnen")
            self.create_btn.setEnabled(False)
            return
        
        # Validierung 4: Tabelle existiert bereits?
        gcs = get_gcs()
        if not gcs:
            self.validation_label.setText("❌ GCS nicht verfügbar")
            self.create_btn.setEnabled(False)
            return
        
        try:
            conn = sqlite3.connect(gcs.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            exists = cursor.fetchone() is not None
            conn.close()
            
            if exists:
                self.validation_label.setText(f"❌ Tabelle '{table_name}' existiert bereits")
                self.create_btn.setEnabled(False)
                return
        except Exception as e:
            logger.error(f"Fehler bei Tabellen-Prüfung: {e}")
            self.validation_label.setText(f"❌ Fehler bei Prüfung: {e}")
            self.create_btn.setEnabled(False)
            return
        
        # Alles OK!
        self.validation_label.setText("✅ Tabellenname verfügbar")
        self.validation_label.setStyleSheet("color: #27ae60; font-size: 9pt;")
        self.create_btn.setEnabled(True)
    
    def _create_table(self):
        """Erstellt die Tabelle mit allen Strukturen"""
        self.table_name = self.name_input.text().strip().lower()
        
        logger.info(f"🎯 === ERSTELLE DATENTABELLE: {self.table_name} ===")
        
        try:
            gcs = get_gcs()
            
            # SCHRITT 1: Tabelle anlegen via PdvmDatenbank
            logger.info(f"📂 SCHRITT 1: Lege Tabelle an...")
            db = PdvmDatenbank(self.table_name)
            logger.info(f"   ✅ Tabelle '{self.table_name}' angelegt")
            
            # SCHRITT 2: System-Satz (00000000-0000-0000-0000-000000000000)
            logger.info(f"📂 SCHRITT 2: Erstelle System-Satz...")
            system_guid = "00000000-0000-0000-0000-000000000000"
            system_data = {
                "ROOT": {
                    "name": "System"
                }
            }
            db.speichern(system_guid, system_data)
            db.set_name(system_guid, "System")
            
            # Security-Profile setzen
            from security_constants import SECURITY_SYSTEM_GUID
            db.set_sec_id(system_guid, SECURITY_SYSTEM_GUID)
            logger.info(f"   ✅ System-Satz angelegt (GUID: {system_guid}, sec_id: {SECURITY_SYSTEM_GUID})")
            
            # SCHRITT 3: Template-Satz (55555555-5555-5555-5555-555555555555)
            logger.info(f"📂 SCHRITT 3: Erstelle Template-Satz...")
            template_guid = "55555555-5555-5555-5555-555555555555"
            template_data = {
                "ROOT": {
                    "name": "Templates",
                    "TABLE": self.table_name
                },
                "ROOT_CONTROLS": {
                    # Controls für ROOT-Ebene mit GUID-Keys (wie in existierenden Tabellen)
                    "7994ccc2-9e29-4c16-b94c-094cb38c97da": {
                        "name": "NAME",
                        "label": "Name",
                        "type": "string",
                        "read_only": False,
                        "display_order": 0,
                        "required": True,
                        "default": ""
                    },
                    "f10aff00-3a6c-4278-a823-dda49a6ae0e4": {
                        "name": "TABLE",
                        "label": "Basis-Tabelle",
                        "type": "string",
                        "read_only": False,
                        "display_order": 1,
                        "required": True,
                        "default": ""
                    },
                    "ee717adf-f9a2-47c8-a963-04867cde4654": {
                        "name": "SELF_GUID",
                        "label": "GUID",
                        "type": "string",
                        "read_only": True,
                        "display_order": 2,
                        "required": False,
                        "default": ""
                    },
                    "a8854122-ad27-4a14-94c5-ac68b9c6e999": {
                        "name": "HEADER_TEXT",
                        "label": "Kopfzeile",
                        "type": "string",
                        "read_only": False,
                        "display_order": 3,
                        "required": False,
                        "default": ""
                    },
                    "6de0f199-cd5d-4a5b-b722-71804d6c7e38": {
                        "name": "NO_DATA",
                        "label": "Nur Metadaten",
                        "type": "bool",
                        "read_only": False,
                        "display_order": 4,
                        "required": False,
                        "default": False
                    },
                    "c6d377e4-5dc0-4b26-897a-6b77782fa28f": {
                        "name": "PROJECTION_MODE",
                        "label": "Projektionsmodus",
                        "type": "dropdown",
                        "read_only": False,
                        "display_order": 5,
                        "required": False,
                        "default": "standard",
                        "options": ["standard", "expert"]
                    },
                    "a03c90d8-e729-44c0-910a-79c004699eba": {
                        "name": "ALLOW_FILTER",
                        "label": "Filter erlauben",
                        "type": "bool",
                        "read_only": False,
                        "display_order": 6,
                        "required": False,
                        "default": True
                    },
                    "5732de41-d468-4b4b-85ef-b9e6ee08898b": {
                        "name": "ALLOW_SORT",
                        "label": "Sortierung erlauben",
                        "type": "bool",
                        "read_only": False,
                        "display_order": 7,
                        "required": False,
                        "default": True
                    },
                    "4a028586-40c5-4af4-8816-07f17344d309": {
                        "name": "DEFAULT_SORT_COLUMN",
                        "label": "Standard-Sortier-Spalte",
                        "type": "string",
                        "read_only": False,
                        "display_order": 8,
                        "required": False,
                        "default": ""
                    },
                    "be9b5cc3-2732-4efb-9347-f00128b05fea": {
                        "name": "DEFAULT_SORT_REVERSE",
                        "label": "Standard-Sortierung absteigend",
                        "type": "bool",
                        "read_only": False,
                        "display_order": 9,
                        "required": False,
                        "default": False
                    },
                    "52b6a567-5add-4cad-bd3b-9f4c07383f9c": {
                        "name": "EDIT_TYPE",
                        "label": "Type zum Editieren",
                        "type": "string",
                        "read_only": False,
                        "display_order": 999,
                        "required": False,
                        "default": ""
                    }
                },
                "CONTROL_PROPERTIES": {
                    # Standard Control-Properties für neue Felder
                    "name": {
                        "type": "string",
                        "label": "Feldname",
                        "display_order": 1,
                        "read_only": False,
                        "tab": 1
                    },
                    "label": {
                        "type": "string",
                        "label": "Anzeigetext",
                        "display_order": 2,
                        "read_only": False,
                        "tab": 1
                    },
                    "type": {
                        "type": "string",
                        "label": "Feldtyp",
                        "display_order": 3,
                        "read_only": False,
                        "tab": 1
                    },
                    "tooltip": {
                        "type": "string",
                        "label": "Tooltip",
                        "display_order": 4,
                        "read_only": False,
                        "tab": 1
                    },
                    "display_order": {
                        "type": "number",
                        "label": "Reihenfolge",
                        "display_order": 5,
                        "read_only": False,
                        "tab": 1
                    },
                    "tab": {
                        "type": "number",
                        "label": "Tab-Nr",
                        "display_order": 6,
                        "read_only": False,
                        "tab": 1
                    },
                    "read_only": {
                        "type": "bool",
                        "label": "Nur Lesen",
                        "display_order": 7,
                        "read_only": False,
                        "tab": 1
                    }
                }
            }
            db.speichern(template_guid, template_data)
            db.set_name(template_guid, "Templates")
            
            # Security-Profile setzen
            from security_constants import SECURITY_TEMPLATE_GUID
            db.set_sec_id(template_guid, SECURITY_TEMPLATE_GUID)
            logger.info(f"   ✅ Template-Satz angelegt (GUID: {template_guid}, sec_id: {SECURITY_TEMPLATE_GUID})")
            
            # SCHRITT 4: Dialog-Daten anlegen (sys_dialogdaten)
            logger.info(f"📂 SCHRITT 4: Erstelle Dialog-Daten...")
            dialog_guid = neue_guid()
            dialog_db = PdvmCentralDatenbank('sys_dialogdaten', dialog_guid)
            dialog_db.set_value('ROOT', 'name', f"{self.table_name.upper()} - Templates")
            dialog_db.set_value('ROOT', 'TABLE', self.table_name)
            dialog_db.set_value('ROOT', 'DIALOG_TYPE', 'input_controls')
            dialog_db.save_all_values()
            # Name auch in DB-Spalte schreiben (für bessere Auswahl)
            dialog_db._database.set_name(dialog_guid, f"{self.table_name.upper()} - Templates")
            logger.info(f"   ✅ Dialog-Daten angelegt (GUID: {dialog_guid})")
            
            # SCHRITT 5: Frame-Daten anlegen (sys_framedaten)
            logger.info(f"📂 SCHRITT 5: Erstelle Frame-Daten...")
            frame_guid = neue_guid()
            frame_db = PdvmCentralDatenbank('sys_framedaten', frame_guid)
            frame_db.set_value('ROOT', 'name', f"{self.table_name.upper()} Frame")
            frame_db.set_value('ROOT', 'TABLE', self.table_name)
            frame_db.set_value('ROOT', 'VIEW_GUID', '')  # Wird später gesetzt
            frame_db.set_value('ROOT', 'DIALOG_GUID', dialog_guid)
            frame_db.set_value('ROOT', 'HEADER_TEXT', f"{self.table_name.upper()} - Template Editor")
            frame_db.set_value('ROOT', 'EDIT_TYPE', 'input_controls')
            
            # Standard-Gruppen für Templates (ROOT_CONTROLS + CONTROL_PROPERTIES)
            frame_db.set_value('ROOT', 'CONTROL_GROUPS', ['ROOT_CONTROLS', 'CONTROL_PROPERTIES'])
            
            frame_db.save_all_values()
            # Name auch in DB-Spalte schreiben
            frame_db._database.set_name(frame_guid, f"{self.table_name.upper()} Frame")
            logger.info(f"   ✅ Frame-Daten angelegt (GUID: {frame_guid})")
            
            # SCHRITT 6: View-Daten anlegen (sys_viewdaten)
            logger.info(f"📂 SCHRITT 6: Erstelle View-Daten...")
            view_guid = neue_guid()
            view_db = PdvmCentralDatenbank('sys_viewdaten', view_guid)
            view_db.set_value('ROOT', 'name', f"{self.table_name.upper()} View")
            view_db.set_value('ROOT', 'TABLE', self.table_name)
            view_db.set_value('ROOT', 'VIEW_TABLE', self.table_name)
            view_db.set_value('ROOT', 'STICHTAG', None)  # Kein Stichtag = aktuell
            view_db.set_value('ROOT', 'NO_DATA_MODE', True)  # Nur uid + name
            
            # Security-Einstellungen (steuern Sichtbarkeit von Template/System-Sätzen)
            view_db.set_value('ROOT', 'security_mode', 'standard')  # standard|expert|admin
            view_db.set_value('ROOT', 'show_templates', False)  # Template-Sätze ausblenden
            view_db.set_value('ROOT', 'show_system', False)  # System-Sätze ausblenden
            
            view_db.save_all_values()
            # Name auch in DB-Spalte schreiben
            view_db._database.set_name(view_guid, f"{self.table_name.upper()} View")
            logger.info(f"   ✅ View-Daten angelegt (GUID: {view_guid})")
            
            # SCHRITT 7: View-GUID in Frame nachtragen
            logger.info(f"📂 SCHRITT 7: Verknüpfe Frame mit View...")
            frame_db.set_value('ROOT', 'VIEW_GUID', view_guid)
            frame_db.save_all_values()
            logger.info(f"   ✅ Frame mit View verknüpft")
            
            # SCHRITT 8: Modified Tracking initialisieren
            logger.info(f"📂 SCHRITT 8: Initialisiere Modified Tracking...")
            try:
                # Modified Tracking in sys_systemsteuerung für Mandant anlegen
                system_guid = "00000000-0000-0000-0000-000000000000"
                sys_db = PdvmCentralDatenbank('sys_systemsteuerung', system_guid)
                
                # Aktuelles Datum via PdvmDateTime
                from pd_datetime import Pdvm_DateTime
                temp_dt = Pdvm_DateTime()
                current_timestamp = temp_dt.PdvmDateTime  # PdvmFormat: z.B. 2024312.123456
                
                # MODIFIED_AT für diese Tabelle im System-Satz speichern
                sys_db.set_value(self.table_name, 'MODIFIED_AT', current_timestamp)
                sys_db.save_all_values()
                
                logger.info(f"   ✅ Modified Tracking initialisiert (Timestamp: {current_timestamp})")
            except Exception as e:
                logger.warning(f"   ⚠️ Modified Tracking konnte nicht initialisiert werden: {e}")
                # Nicht kritisch - Tracking ist optional
            
            # Erfolg!
            logger.info(f"✅ === TABELLE ERFOLGREICH ERSTELLT ===")
            logger.info(f"   📊 Tabelle: {self.table_name}")
            logger.info(f"   📋 Dialog-GUID: {dialog_guid}")
            logger.info(f"   🖼️  Frame-GUID: {frame_guid}")
            logger.info(f"   👁️  View-GUID: {view_guid}")
            
            QMessageBox.information(
                self,
                "Erfolg",
                f"✅ Tabelle '{self.table_name}' erfolgreich angelegt!\n\n"
                f"📋 Dialog-GUID: {dialog_guid}\n"
                f"🖼️  Frame-GUID: {frame_guid}\n"
                f"👁️  View-GUID: {view_guid}\n\n"
                f"Sie können die Templates jetzt über 'Dialog Test' pflegen."
            )
            
            self.accept()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anlegen der Tabelle: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            QMessageBox.critical(
                self,
                "Fehler",
                f"❌ Fehler beim Anlegen der Tabelle:\n\n{e}"
            )


def execute(params: dict, context: dict, gcs) -> bool:
    """
    Handler: Neue Datentabelle anlegen
    
    Öffnet Dialog für Tabellen-Erstellung mit vollständiger Struktur:
    - Tabelle im Mandanten
    - System-Satz (00000000...)
    - Template-Satz (55555555...)
    - Dialog-/Frame-/View-Daten für Template-Pflege
    
    Args:
        params: Handler-Parameter (dict)
        context: Kontext-Informationen (dict)
        gcs: Global Control System
        
    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    logger.info("🎯 Handler: create_datatable")
    
    try:
        # MainApp aus context holen
        main_app = context.get('main_app')
        
        dialog = CreateDatatableDialog(main_app)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            table_name = dialog.table_name
            logger.info(f"✅ Tabelle '{table_name}' erfolgreich angelegt")
            return True
        else:
            logger.info("❌ Tabellen-Erstellung abgebrochen")
            return False
            
    except Exception as e:
        logger.error(f"❌ Handler-Fehler: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
