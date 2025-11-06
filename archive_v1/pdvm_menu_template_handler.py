# pdvm_menu_template_handler.py
"""
Template-Handler für Menü-Wiederverwendung
Unterstützt GUID-Referenzen in Menüstrukturen für zentrale Wartung
"""
import logging
from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)

class PdvmMenuTemplateHandler:
    """Handler für Template-basierte Menüs mit GUID-Referenzen"""
    
    def __init__(self):
        self.template_cache = {}  # Cache für geladene Templates
    
    def process_menu_templates(self, menu_data):
        """
        Verarbeitet Template-Referenzen in Menüdaten
        
        Args:
            menu_data: Original Menüstruktur (dict)
            
        Returns:
            dict: Verarbeitete Menüstruktur mit aufgelösten Templates
        """
        if not isinstance(menu_data, dict):
            return menu_data
        
        processed_data = {}  # Neue Struktur aufbauen um Reihenfolge zu erhalten
        template_commands = {}
        
        # 1. Alle Gruppen nach Template-Referenzen durchsuchen und in korrekter Reihenfolge verarbeiten
        for group_name, group_data in menu_data.items():
            if isinstance(group_data, dict):
                # Template-Verarbeitung für diese Gruppe
                processed_group = self._process_group_with_positioning(group_data, group_name)
                processed_data[group_name] = processed_group
                
                # Template-Kommandos sammeln falls vorhanden
                template_guid = group_data.get("!guid!")
                if template_guid:
                    try:
                        full_template = self._load_template(template_guid)
                        if full_template and isinstance(full_template, dict):
                            # Template-Kommandos sammeln für späteren Merge
                            if "PD_commands" in full_template:
                                template_commands.update(full_template["PD_commands"])
                    except Exception as e:
                        logger.error(f"❌ Fehler beim Sammeln der Template-Kommandos von {template_guid}: {e}")
            else:
                # Nicht-Dict Gruppen direkt übernehmen
                processed_data[group_name] = group_data
        
        # 2. Template-Kommandos zu bestehenden Kommandos hinzufügen
        if template_commands and "PD_commands" in processed_data:
            # Template-Kommandos zu bestehenden hinzufügen
            existing_commands = processed_data["PD_commands"].copy()
            existing_commands.update(template_commands)
            processed_data["PD_commands"] = existing_commands
            
            logger.info(f"✅ {len(template_commands)} Template-Kommandos hinzugefügt")
        elif template_commands:
            # Neue PD_commands Sektion erstellen
            processed_data["PD_commands"] = template_commands
            logger.info(f"✅ PD_commands Sektion mit {len(template_commands)} Template-Kommandos erstellt")
        
        return processed_data
    
    def _process_group_with_positioning(self, group_data, group_name):
        """
        Verarbeitet Template-Referenzen in einer Gruppe mit korrekter Positionierung
        
        Args:
            group_data: Gruppen-Daten (dict)
            group_name: Name der Gruppe (für Template-Zweig-Suche)
            
        Returns:
            dict: Verarbeitete Gruppen-Daten mit Template an korrekter Position
        """
        if not isinstance(group_data, dict):
            return group_data
        
        template_guid = group_data.get("!guid!")
        if not template_guid:
            # Keine Template-Referenz, Gruppe unverändert zurückgeben
            return group_data
        
        try:
            # Template laden
            full_template = self._load_template(template_guid)
            if not full_template or not isinstance(full_template, dict):
                logger.warning(f"⚠️ Template {template_guid} konnte nicht geladen werden")
                # !guid! entfernen und Rest behalten
                result = group_data.copy()
                del result["!guid!"]
                return result
            
            # Template-Zweig für diese Gruppe holen
            template_group_data = full_template.get(group_name, {})
            if not template_group_data:
                logger.warning(f"⚠️ Kein Template-Zweig '{group_name}' in Template {template_guid} gefunden")
                # !guid! entfernen und Rest behalten
                result = group_data.copy()
                del result["!guid!"]
                return result
            
            # Neue Gruppe mit korrekter Reihenfolge aufbauen
            processed_group = {}
            
            # Alle Einträge der Reihe nach durchgehen
            for key, value in group_data.items():
                if key == "!guid!":
                    # An dieser Stelle Template-Inhalte einfügen
                    for template_key, template_value in template_group_data.items():
                        processed_group[template_key] = template_value
                    logger.info(f"✅ Template-Zweig '{group_name}' aus {template_guid} an Position von !guid! eingefügt")
                else:
                    # Normale Einträge übernehmen
                    processed_group[key] = value
            
            return processed_group
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Verarbeiten von Template {template_guid}: {e}")
            # Fallback: !guid! entfernen und Rest behalten
            result = group_data.copy()
            del result["!guid!"]
            return result

    def _process_group_templates(self, group_data):
        """
        Verarbeitet Template-Referenzen in einer Menü-Gruppe
        
        Args:
            group_data: Gruppen-Daten (dict)
            
        Returns:
            dict: Verarbeitete Gruppen-Daten
        """
        if not isinstance(group_data, dict):
            return group_data
            
        processed_group = {}
        
        # Nach Template-Referenzen suchen
        for key, value in group_data.items():
            if key == "!guid!":
                # Template laden und einfügen
                try:
                    template_data = self._load_template(value)
                    if template_data:
                        # Template-Daten direkt in die Gruppe einfügen (ersetzt !guid!)
                        template_content = template_data.copy()
                        processed_group.update(template_content)
                        logger.info(f"✅ Template {value} erfolgreich eingefügt")
                    else:
                        logger.warning(f"⚠️ Template {value} konnte nicht geladen werden")
                except Exception as e:
                    logger.error(f"❌ Fehler beim Verarbeiten von Template {value}: {e}")
            else:
                # Normale Einträge übernehmen
                processed_group[key] = value
        
        return processed_group
    
    def _load_template(self, template_guid):
        """
        Lädt Template-Daten aus der Datenbank
        
        Args:
            template_guid: GUID des Templates
            
        Returns:
            dict: Template-Daten der aktuellen Gruppe oder None
        """
        # Cache prüfen
        if template_guid in self.template_cache:
            return self.template_cache[template_guid]
        
        try:
            # Template aus menudaten-Tabelle laden (KORRIGIERT: ohne db_name Parameter)
            db = PdvmCentralDatenbank(
                table_name="menudaten",
                guid=template_guid
            )
            
            template_raw = db.get_all_values()  # Korrigiert: get_all_values() statt lesen()
            if template_raw and isinstance(template_raw, dict):
                # Template-Daten extrahieren - verschiedene Formate unterstützen
                full_template = None
                
                # Format 1: Template direkt als Daten (normale Menüstruktur)
                if all(key in template_raw for key in ["PD_commands", "PD_grund"]):
                    full_template = template_raw
                    logger.info(f"✅ Template {template_guid} als direkte Menüstruktur erkannt")
                
                # Format 2: Template unter GUID mit "daten" Schlüssel
                elif template_guid in template_raw and "daten" in template_raw[template_guid]:
                    full_template = template_raw[template_guid]["daten"]
                    logger.info(f"✅ Template {template_guid} unter GUID->daten gefunden")
                
                # Format 3: Template unter "daten" Schlüssel
                elif "daten" in template_raw:
                    full_template = template_raw["daten"]
                    logger.info(f"✅ Template {template_guid} unter 'daten' gefunden")
                
                if not full_template:
                    logger.warning(f"⚠️ Template {template_guid}: Keine erkennbare Menüstruktur gefunden")
                    logger.debug(f"   Verfügbare Schlüssel: {list(template_raw.keys())}")
                    return None
                
                # Cache speichern (vollständiges Template)
                self.template_cache[template_guid] = full_template
                
                logger.info(f"✅ Template {template_guid} erfolgreich geladen")
                return full_template
            else:
                logger.warning(f"⚠️ Template {template_guid}: Keine Daten gefunden")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Templates {template_guid}: {e}")
        
        return None
    
    def create_standard_templates(self):
        """
        HINWEIS: Diese Methode erstellt KEINE Templates mehr automatisch.
        Templates müssen manuell über den Menüeditor erstellt werden.
        """
        logger.info("ℹ️ Template-System ist bereit")
        logger.info("💡 Templates müssen manuell über den Menüeditor erstellt werden")
        logger.info("📋 Erwartetes Format für Templates:")
        logger.info("   - Template ist ein normales Menü mit allen 4 Gruppen")
        logger.info("   - PD_commands, PD_grund, PD_zusatz, PD_menu")
        logger.info("   - Verwendung: '!guid!': 'template-guid' in beliebiger Gruppe")
        
        return True


# Beispiel-Verwendung für erweiterte Syntax:
"""
Erweiterte Template-Syntax:

1. Basis-Template einfügen:
"PD_grund": {
    "!guid!": "template-basis-standard",
    "Lokale Einträge": "lokale_funktion()"
}

2. Template am Anfang einfügen:
"PD_grund": {
    "!guid!prepend": "template-basis-standard",
    "Lokale Einträge": "lokale_funktion()"
}

3. Template am Ende einfügen:
"PD_grund": {
    "Lokale Einträge": "lokale_funktion()",
    "!guid!append": "template-basis-standard"
}

4. Template ersetzt alles:
"PD_grund": {
    "!guid!replace": "template-basis-standard"
}
"""
