#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JSON-Reparatur-Script für Menüstruktur
Behebt den Syntaxfehler in der JSON-Struktur
"""

import json
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def repair_and_update_menu_structure():
    """Repariert die JSON-Struktur und aktualisiert die Datenbank"""
    
    print("🔧 Repariere JSON-Struktur...")
    
    # Die korrigierte JSON-Struktur (Fehler behoben: überflüssige Klammern entfernt)
    corrected_structure = {
        "PD_commands": {
            "Basis_Hilfe": "self.show_text_klein('Mein Hilfetext')",
            "Basis_Abmelden": "self.logout()",
            "Einstellungen_Menues_Pflege Grundmenü": "self.open_menu_editor('PD_grund')",
            "Einstellungen_Menues_Pflege Vertikalmenü": "self.open_menu_editor('PD_menu')",
            "Basis_---": None,
            "Einstellungen": None,
            "Personaldaten_Person_Steuer_Lohnsteuer_Anmeldung_Formular": None,
            "Personaldaten_Person_Steuer_Lohnsteuer_Anmeldung_Versand": None,
            "Personaldaten_Person_Steuer_Lohnsteuer_Daten_Steuernummer": None,
            "Personaldaten_Person_Steuer_Lohnsteuer_Daten_Steuerklasse": None,
            "Personaldaten_Person_Steuer_Zusatzangaben_Meine Bemerkung_Bemerkung_1": None,
            "Personaldaten_Person_Steuer_Zusatzangaben_Meine Bemerkung_Bemerkung_2": None,
            "Personaldaten_Person_Steuer_Zusatzangaben_Meine Bemerkung_Bemerkung_3": None,
            "Personaldaten_Person_Steuer_Zusatzangaben_Meine Bemerkung_Bemerkung_4": None,
            "Personaldaten_Person_Steuer_Zusatzangaben_Meine Bemerkung_Bemerkung_5": None,
            "Personaldaten_Person_Steuer_Zusatzangaben_Hinweise_Hinweis_1": None,
            "Personaldaten_Person_Steuer_Zusatzangaben_Hinweise_Hinweis_2": None,
            "Personaldaten_Person_Steuer_Zusatzangaben_Hinweise_Hinweis_3": None,
            "Personaldaten_Person_Steuer_Zusatzangaben_Hinweise_Hinweis_4": None,
            "Personaldaten_Person_Steuer_Zusatzangaben_Hinweise_Hinweis_5": None,
            "Personaldaten_Person_Steuer_Zusatzangaben_Hinweise_Hinweis_6": None,
            "Personaldaten_Person_Steuer_Zusatzangaben_Hinweise_Hinweis_7": None,
            "Personaldaten_Person_Steuer_Lohnsteuer_Finanzamt Ulm": None,
            "Personalberechnung_Reisekosten": None,
            "Personalberechnung_Lohnrechnung": None,
            "Personalberechnung_Anschrift": "Neues Menükommando Anchrift",
            "Einstellungen_Layout_Neues Blatt": "und Kommando",
            "Einstellungen_Layout_Neuer Knoten": "",
            "Personaldaten_Person_Steuer": None,
            "Personaldaten_Person_Sozialversicherung": None,
            "Einstellungen_Layout_hinzufügen": None,
            "Einstellungen_Layout_speichern": None,
            "Basis_zu den Apps": "self.open_start_menu()",
            "Personaldaten_Person": None,
            "Einstellungen_Layout_Paula im Layout_Paul dabei": None,
            "Einstellungen_Paula": None,
            "Einstellungen_Layout_Neue Farbe": None,
            "Personalberechnung_Abrechnung_Einzeln": None,
            "Personalberechnung_Abrechnung_Mehrere": None,
            "Personalberechnung_Prüfung_Einzelprüfung": None,
            "Personalberechnung_Prüfung_Prüfung für Auswahl": None,
            "Testbereich_suchen/ändern pers einzeln": "self.pdvm_search(\"0d10a0d0-b1a5-4544-b284-e8a09ca979b5\",\"4078079f-4028-45ed-879c-3c779ecf3d0d\",0)",
            "Einstellungen_Layout_Paula1_Paula5": None,
            "Testbereich_Dialog Inputframe": "self.pdvm_dialog(\"4078079f-4028-45ed-879c-3c779ecf3d0d\", 0)"
        },
        "PD_grund": {
            "Basis": {
                "Hilfe": None,
                "---": None,
                "zu den Apps": None,
                "Abmelden": None
            },
            "Einstellungen": {
                "Menues": {
                    "Pflege Grundmenü": None,
                    "Pflege Vertikalmenü": None
                },
                "Layout": {
                    "Paula1": {
                        "Paula5": None
                    },
                    "Paula im Layout": {
                        "Paul dabei": None
                    }
                }
            },
            "Testbereich": {
                "suchen/ändern pers einzeln": None,
                "Dialog Inputframe": None
            }
        },
        "PD_zusatz": {
            "PD_z_Grund": {
                "Einstellungen_Layout": {
                    "speichern": None,
                    "hinzufügen": None
                },
                "Einstellungen": {
                    "Layout": {
                        "Neues Blatt": None,
                        "Neuer Knoten": None,
                        "Neue Farbe": None
                    }
                }
            },
            "PD_z_Menu": {
                "Personaldaten_Person_Steuer": {
                    "Lohnsteuer": {
                        "Anmeldung": {
                            "Formular": None,
                            "Versand": None
                        },
                        "Daten": {
                            "Steuernummer": None,
                            "Steuerklasse": None
                        },
                        "Finanzamt Ulm": None
                    },
                    "Zusatzangaben": {
                        "Meine Bemerkung": {
                            "Bemerkung_1": None,
                            "Bemerkung_2": None,
                            "Bemerkung_3": None,
                            "Bemerkung_4": None,
                            "Bemerkung_5": None
                        },
                        "Hinweise": {
                            "Hinweis_1": None,
                            "Hinweis_2": None,
                            "Hinweis_3": None,
                            "Hinweis_4": None,
                            "Hinweis_5": None,
                            "Hinweis_6": None,
                            "Hinweis_7": None
                        }
                    }
                },
                "Personaldaten_Person": None,
                "Personalberechnung": {
                    "Abrechnung": {
                        "Einzeln": None,
                        "Mehrere": None
                    },
                    "Prüfung": {
                        "Einzelprüfung": None,
                        "Prüfung für Auswahl": None
                    }
                }
            }
        },
        "PD_menu": {}  # Hinzugefügt: Fehlende PD_menu Sektion
    }
    
    try:
        # Validiere JSON
        json_str = json.dumps(corrected_structure, ensure_ascii=False, indent=2)
        print("✅ JSON-Struktur erfolgreich korrigiert und validiert!")
        
        # Aktualisiere Datenbank
        conn = sqlite3.connect('PdvmManager.db')
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE menudaten SET jsondaten = ? WHERE GUID = ?",
            (json_str, "e1e77039-d1b5-46ff-b12b-cced0ae0da7c")
        )
        
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        
        if affected_rows > 0:
            print("✅ Datenbank erfolgreich aktualisiert!")
            print(f"📊 Struktur-Übersicht:")
            print(f"   PD_commands: {len(corrected_structure['PD_commands'])} Kommandos")
            print(f"   PD_grund: {len(corrected_structure['PD_grund'])} Hauptkategorien")
            print(f"   PD_zusatz: {len(corrected_structure['PD_zusatz'])} Zusatzmenü-Bereiche")
            print(f"   PD_menu: {len(corrected_structure['PD_menu'])} Vertikal-Menü-Einträge")
            
            print(f"\n🎯 Korrigierte Probleme:")
            print(f"   ✅ Entfernte überflüssige schließende Klammern am Ende")
            print(f"   ✅ Hinzugefügte fehlende PD_menu Sektion")
            print(f"   ✅ Unicode-Zeichen (ü, ä) korrekt behandelt")
            
            return True
        else:
            print("⚠️ Keine Zeilen in der Datenbank aktualisiert")
            return False
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON-Validierung fehlgeschlagen: {e}")
        return False
    except Exception as e:
        print(f"❌ Fehler beim Datenbankupdate: {e}")
        return False

if __name__ == "__main__":
    repair_and_update_menu_structure()
