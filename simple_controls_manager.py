"""
EINFACHER CONTROLS-MANAGER
=========================

Grundidee:
- Controls sind die einzige Quelle der Wahrheit
- Alle Attribute (show, expert_mode, display_order) sind in Controls
- Controls sind persistent in GCS
- Projektionen werden zur Laufzeit aus Controls generiert
- Änderungen gehen direkt an Controls und werden sofort persistent

Workflow:
1. Controls aus GCS laden
2. Bei Bedarf Projektionen aus Controls generieren  
3. Änderungen direkt in Controls -> GCS speichern
4. Projektionen neu generieren
"""

import logging
from global_gcs import gcs

logger = logging.getLogger(__name__)

class SimpleControlsManager:
    """Einfacher Manager: Controls sind die Wahrheit, Projektionen werden generiert"""
    
    def __init__(self, view_guid):
        self.view_guid = view_guid
        logger.info(f"📊 SimpleControlsManager für View {view_guid} erstellt")
    
    def get_controls(self):
        """Holt aktuelle Controls aus GCS (als Gruppe)"""
        controls = gcs.get_group(self.view_guid)
        
        # Sicherstellen, dass wir ein Dictionary haben
        if not isinstance(controls, dict):
            logger.warning(f"⚠️ Controls für {self.view_guid} sind kein Dictionary: {type(controls)}")
            logger.info(f"🔍 Controls-Inhalt: {controls}")
            
            # Fallback: Leeres Dictionary zurückgeben
            controls = {}
            logger.info(f"📝 Leeres Controls-Dictionary erstellt für {self.view_guid}")
        
        return controls
    
    def initialize_controls_from_config(self, controls_config):
        """Initialisiert Controls aus bestehender Konfiguration"""
        if not isinstance(controls_config, dict):
            logger.error(f"❌ Controls-Config ist kein Dictionary: {type(controls_config)}")
            return
            
        # Speichere Controls-Konfiguration in GCS als Gruppe
        gcs.set_group(self.view_guid, controls_config)
        logger.info(f"✅ Controls aus Konfiguration in GCS gespeichert: {len(controls_config)} Controls")
    
    def update_control(self, key, **attributes):
        """Ändert ein Control-Attribut und speichert sofort persistent"""
        controls = self.get_controls()
        if key in controls:
            # Aktualisiere Control-Dictionary
            for attr, value in attributes.items():
                controls[key][attr] = value
                logger.info(f"🔄 Control {key}.{attr} = {value}")
            
            # Sofort persistent speichern über set_group
            gcs.set_group(self.view_guid, controls)
            logger.info(f"💾 Controls für View {self.view_guid} gespeichert")
        else:
            logger.warning(f"⚠️ Control {key} nicht gefunden")
    
    def reorder_controls(self, new_order):
        """Ändert die Reihenfolge der Controls"""
        controls = self.get_controls()
        for i, key in enumerate(new_order):
            if key in controls:
                controls[key]['display_order'] = i
        
        # Sofort persistent speichern über set_group
        gcs.set_group(self.view_guid, controls)
        logger.info(f"🔄 Control-Reihenfolge geändert: {new_order}")
    
    def get_table_projection(self):
        """Generiert Tabellen-Projektion aus Controls"""
        controls = self.get_controls()
        result = []
        
        # Sammle alle Controls die angezeigt werden sollen
        for key, control in controls.items():
            if control.get('show', False):
                # Prüfe Expert-Mode
                if gcs.expert_mode or not control.get('expert_mode', False):
                    result.append(key)
        
        # Sortiere nach display_order
        result.sort(key=lambda k: controls[k].get('display_order', 999))
        
        logger.debug(f"📋 Tabellen-Projektion generiert: {len(result)} Spalten")
        return result
    
    def get_search_projection(self):
        """Generiert Such-Projektion aus Controls"""
        controls = self.get_controls()
        result = []
        
        # Sammle alle searchable Controls
        for key, control in controls.items():
            if control.get('searchable', False):
                # Prüfe Expert-Mode
                if gcs.expert_mode or not control.get('expert_mode', False):
                    result.append(key)
        
        # Sortiere nach display_order
        result.sort(key=lambda k: controls[k].get('display_order', 999))
        
        logger.debug(f"🔍 Such-Projektion generiert: {len(result)} Spalten")
        return result
    
    def get_management_projection(self):
        """Generiert Management-Projektion aus Controls (alle verfügbaren Controls)"""
        controls = self.get_controls()
        result = []
        
        # Sammle alle Controls die konfigurierbar sind
        for key, control in controls.items():
            # Prüfe Expert-Mode für Sichtbarkeit
            if gcs.expert_mode or not control.get('expert_mode', False):
                result.append(key)
        
        # Sortiere nach display_order
        result.sort(key=lambda k: controls[k].get('display_order', 999))
        
        logger.debug(f"⚙️ Management-Projektion generiert: {len(result)} Spalten")
        return result
    
    def get_available_controls(self):
        """Alle verfügbaren Controls für das Management"""
        return self.get_management_projection()
    
    def toggle_expert_mode(self, key):
        """Schaltet expert_mode für einen Control um"""
        controls = self.get_controls()
        if key in controls:
            current = controls[key].get('expert_mode', False)
            self.update_control(key, expert_mode=not current)
            logger.info(f"🔧 Expert-Mode für {key}: {not current}")
    
    def toggle_show(self, key):
        """Schaltet show für einen Control um"""
        controls = self.get_controls()
        if key in controls:
            current = controls[key].get('show', False)
            self.update_control(key, show=not current)
            logger.info(f"👁️ Show für {key}: {not current}")
    
    def toggle_searchable(self, key):
        """Schaltet searchable für einen Control um"""
        controls = self.get_controls()
        if key in controls:
            current = controls[key].get('searchable', False)
            self.update_control(key, searchable=not current)
            logger.info(f"🔍 Searchable für {key}: {not current}")