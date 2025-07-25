#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JSON Reparatur und Menüstruktur-Korrektur
Repariert zuerst das beschädigte JSON, dann korrigiert die Menüstruktur.
"""

import sqlite3
import json
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JSONMenuRepairer:
    """Repariert beschädigtes JSON in der Menüdatenbank"""
    
    def __init__(self, db_path="PdvmManager.db", menu_guid="e1e77039-d1b5-46ff-b12b-cced0ae0da7c"):
        self.db_path = db_path
        self.menu_guid = menu_guid
        
    def repair_json_in_database(self):
        """Repariert das beschädigte JSON direkt in der Datenbank"""
        logger.info("🔧 Repariere JSON in der Datenbank...")
        
        try:
            # Verbindung zur Datenbank
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Hole den beschädigten JSON-String
            cursor.execute("SELECT daten FROM menudaten WHERE GUID = ?", (self.menu_guid,))
            result = cursor.fetchone()
            
            if not result:
                logger.error(f"❌ Keine Daten für GUID {self.menu_guid} gefunden")
                return False
                
            raw_json = result[0]
            logger.info(f"📄 Original JSON Länge: {len(raw_json)} Zeichen")
            
            # Zeige den problematischen Bereich
            error_pos = 4576
            start = max(0, error_pos - 50)
            end = min(len(raw_json), error_pos + 50)
            logger.info(f"🔍 Problematischer Bereich um Position {error_pos}:")
            logger.info(f"'{raw_json[start:end]}'")
            
            # Repariere häufige JSON-Probleme
            repaired_json = self._repair_json_string(raw_json)
            
            if repaired_json != raw_json:
                logger.info("✅ JSON repariert - speichere in Datenbank...")
                
                # Aktualisiere die Datenbank
                cursor.execute("UPDATE menudaten SET daten = ? WHERE GUID = ?", 
                             (repaired_json, self.menu_guid))
                conn.commit()
                logger.info("💾 Repariertes JSON gespeichert")
            else:
                logger.info("ℹ️ Keine JSON-Reparatur erforderlich")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei JSON-Reparatur: {e}")
            return False
    
    def _repair_json_string(self, json_str):
        """Repariert häufige JSON-Probleme"""
        logger.info("🔧 Analysiere und repariere JSON-Probleme...")
        
        # 1. Entferne trailing commas vor closing braces/brackets
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        # 2. Repariere doppelte closing braces
        json_str = re.sub(r'}\s*}+\s*$', '}', json_str)
        
        # 3. Stelle sicher, dass der JSON korrekt endet
        if not json_str.rstrip().endswith('}'):
            logger.info("🔧 Füge fehlendes schließendes '}' hinzu")
            json_str = json_str.rstrip() + '}'
        
        # 4. Entferne trailing commas nach dem letzten Element
        # Suche nach }, } Mustern und ersetze sie
        json_str = re.sub(r',(\s*})(\s*})', r'\1\2', json_str)
        
        # 5. Teste ob JSON jetzt valide ist
        try:
            json.loads(json_str)
            logger.info("✅ JSON ist jetzt valide")
            return json_str
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ JSON noch nicht valide: {e}")
            
            # Erweiterte Reparatur
            return self._advanced_json_repair(json_str, e)
    
    def _advanced_json_repair(self, json_str, error):
        """Erweiterte JSON-Reparatur basierend auf dem spezifischen Fehler"""
        logger.info("🔧 Erweiterte JSON-Reparatur...")
        
        error_msg = str(error)
        
        if "Expecting property name" in error_msg:
            # Suche nach dem Fehlerpunkt
            try:
                # Extrahiere Position aus Fehlermeldung
                pos_match = re.search(r'char (\d+)', error_msg)
                if pos_match:
                    error_pos = int(pos_match.group(1))
                    
                    # Zeige Kontext um den Fehler
                    start = max(0, error_pos - 100)
                    end = min(len(json_str), error_pos + 100)
                    context = json_str[start:end]
                    logger.info(f"🔍 Fehlerkontext: '{context}'")
                    
                    # Häufige Probleme in diesem Bereich
                    # 1. Trailing comma nach letztem Element
                    before_error = json_str[:error_pos]
                    after_error = json_str[error_pos:]
                    
                    # Suche nach }, } Muster und entferne überschüssige Kommas
                    if before_error.rstrip().endswith(','):
                        # Entferne trailing comma
                        before_error = before_error.rstrip()[:-1]
                        repaired = before_error + after_error
                        logger.info("🔧 Entfernte trailing comma")
                        
                        try:
                            json.loads(repaired)
                            return repaired
                        except:
                            pass
                    
                    # 2. Prüfe auf ungeschlossene Objekte
                    open_braces = before_error.count('{') - before_error.count('}')
                    if open_braces > 0:
                        # Füge fehlende closing braces hinzu
                        repaired = json_str + '}' * open_braces
                        logger.info(f"🔧 Füge {open_braces} fehlende closing braces hinzu")
                        
                        try:
                            json.loads(repaired)
                            return repaired
                        except:
                            pass
            
            except Exception as repair_error:
                logger.error(f"❌ Erweiterte Reparatur fehlgeschlagen: {repair_error}")
        
        # Als letzter Ausweg: Versuche den JSON zu truncaten an einer sinnvollen Stelle
        return self._truncate_to_valid_json(json_str)
    
    def _truncate_to_valid_json(self, json_str):
        """Trunciert JSON an einer Stelle, wo er noch valide ist"""
        logger.info("🔧 Versuche JSON-Truncation...")
        
        # Finde die letzte Position mit gleicher Anzahl öffnender und schließender Braces
        brace_count = 0
        last_valid_pos = 0
        
        for i, char in enumerate(json_str):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    # Vollständiges Objekt gefunden
                    last_valid_pos = i + 1
        
        if last_valid_pos > 0:
            truncated = json_str[:last_valid_pos]
            try:
                json.loads(truncated)
                logger.info(f"✅ JSON erfolgreich auf Position {last_valid_pos} trunciert")
                return truncated
            except:
                pass
        
        logger.error("❌ Konnte JSON nicht reparieren")
        return json_str
    
    def create_corrected_menu_structure(self):
        """Erstellt die korrigierte Menüstruktur basierend auf Ihrer Beschreibung"""
        logger.info("🎯 Erstelle korrigierte Menüstruktur...")
        
        # Die korrekte Struktur basierend auf Ihrer Erklärung
        corrected_structure = {
            "PD_commands": {
                # Basis-Kommandos
                "Basis_Hilfe": "self.show_text_klein('Mein Hilfetext')",
                "Basis_Abmelden": "self.logout()",
                "Basis_zu den Apps": "self.open_start_menu()",
                
                # Einstellungen
                "Einstellungen_Menues_Pflege Grundmenü": "self.open_menu_editor('PD_grund')",
                "Einstellungen_Menues_Pflege Vertikalmenü": "self.open_menu_editor('PD_menu')",
                
                # Testbereich
                "Testbereich_suchen/ändern pers einzeln": "self.pdvm_search(\"0d10a0d0-b1a5-4544-b284-e8a09ca979b5\",\"4078079f-4028-45ed-879c-3c779ecf3d0d\",0)",
                "Testbereich_Dialog Inputframe": "self.pdvm_dialog(\"4078079f-4028-45ed-879c-3c779ecf3d0d\", 0)",
                
                # Korrekte Lupe-Kommandos (Zusatzmenü für Dialog Inputframe)
                "Testbereich_Dialog Inputframe_🔍 Lupe Modi_Lupe Übersicht": "self.dialog_zusatz('View-Lupe')",
                "Testbereich_Dialog Inputframe_🔍 Lupe Modi_Lupe Eingaben": "self.dialog_zusatz('Input-Lupe')",
                "Testbereich_Dialog Inputframe_🔍 Lupe Modi_Lupen aus": "self.dialog_zusatz('Position-Normal')"
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
                    }
                },
                "Testbereich": {
                    "suchen/ändern pers einzeln": None,
                    "Dialog Inputframe": None
                }
            },
            "PD_zusatz": {
                "PD_z_Grund": {
                    # Zusatzmenü für Testbereich -> Dialog Inputframe
                    "Testbereich": {
                        "Dialog Inputframe": {
                            "🔍 Lupe Modi": {
                                "Lupe Übersicht": None,
                                "Lupe Eingaben": None,
                                "Lupen aus": None
                            }
                        }
                    }
                },
                "PD_z_Menu": {
                    # Hier können später Zusatzmenüs für das Vertikalmenü hinzugefügt werden
                }
            },
            "PD_menu": {
                # Das Vertikalmenü - kann erweitert werden
            }
        }
        
        return corrected_structure
    
    def save_corrected_structure(self):
        """Speichert die korrigierte Struktur in die Datenbank"""
        logger.info("💾 Speichere korrigierte Menüstruktur...")
        
        try:
            corrected_structure = self.create_corrected_menu_structure()
            json_str = json.dumps(corrected_structure, ensure_ascii=False, indent=2)
            
            # Speichere in Datenbank
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("UPDATE menudaten SET daten = ? WHERE GUID = ?", 
                         (json_str, self.menu_guid))
            conn.commit()
            conn.close()
            
            logger.info("✅ Korrigierte Menüstruktur gespeichert")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
            return False

def main():
    """Hauptfunktion"""
    repairer = JSONMenuRepairer()
    
    logger.info("🚀 Starte JSON-Reparatur und Menüstruktur-Korrektur...")
    
    # Option 1: Versuche JSON zu reparieren
    if repairer.repair_json_in_database():
        logger.info("✅ JSON-Reparatur abgeschlossen")
    else:
        logger.warning("⚠️ JSON-Reparatur nicht erfolgreich")
    
    # Option 2: Erstelle komplett neue, korrekte Struktur
    logger.info("🎯 Erstelle neue korrekte Menüstruktur...")
    if repairer.save_corrected_structure():
        logger.info("🎉 Menüstruktur erfolgreich korrigiert!")
    else:
        logger.error("❌ Menüstruktur-Korrektur fehlgeschlagen")

if __name__ == "__main__":
    main()
