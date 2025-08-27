"""
PDVM Controls Manager - Vereinfachte Control-Verwaltung
Zentrale Verwaltung aller Column Controls mit einfachem Zugriff.
"""

import logging
from pdvm_column_control import PdvmColumnControl, PdvmControlsCollection

logger = logging.getLogger(__name__)

class PdvmControlsManager:
    """
    Zentraler Manager für alle Column Controls.
    Ersetzt die komplizierte Provider-Logik mit einfacher Control-Verwaltung.
    """
    
    def __init__(self):
        self.controls = PdvmControlsCollection()
        self.current_mode = "normal"
        logger.info("🏗️ PdvmControlsManager initialisiert")
    
    def load_from_provider_data(self, provider_controls):
        """
        Lädt Controls aus Provider-Daten (Legacy-Kompatibilität)
        
        Args:
            provider_controls: Controls-Objekt vom Provider mit .columns Liste
        """
        logger.info(f"📥 Lade {len(provider_controls.columns)} Controls vom Provider")
        
        for idx, column_data in enumerate(provider_controls.columns):
            # Provider-Daten in Control umwandeln - explizite Parameter zur Vermeidung von Konflikten
            control_args = {
                'name': column_data.get('name'),
                'anzeige': column_data.get('anzeige', column_data.get('name')),
                
                # Mode-spezifische Sichtbarkeit
                'show': column_data.get('show', True),  # Expert-Mode
                'show_show': column_data.get('show_show', True),  # Normal-Mode
                
                # Mode-spezifische Reihenfolge
                'order': column_data.get('order', idx + 1),  # Expert-Mode
                'show_order': column_data.get('show_order', idx + 1),  # Normal-Mode
                
                # Dialog-Felder (erstmal mit Standard-Werten)
                'display_show': column_data.get('show', True),
                'display_order': column_data.get('display_order', idx + 1),
                
                'expert': column_data.get('expert', False),
                'width': column_data.get('width', 'auto'),
                'sortable': column_data.get('sortable', True),
                'searchable': column_data.get('searchable', True),
                'filterType': column_data.get('filterType', 'contains'),
                'type': column_data.get('type', 'show'),
                'original_field': column_data.get('original_field'),
            }
            
            # Alle anderen Eigenschaften hinzufügen (außer den bereits explizit behandelten)
            exclude_keys = ['name', 'anzeige', 'show', 'show_show', 'order', 'show_order', 
                           'display_show', 'display_order', 'expert', 'width', 'sortable', 
                           'searchable', 'filterType', 'type', 'original_field']
            
            for k, v in column_data.items():
                if k not in exclude_keys:
                    control_args[k] = v
            
            control = PdvmColumnControl(**control_args)
            self.controls.add_control(control)
            
        logger.info(f"✅ {len(self.controls)} Controls geladen")
    
    def get_controls_for_mode(self, mode=None):
        """
        Gibt sortierte Controls für einen Mode zurück.
        
        Args:
            mode: "normal" oder "expert" (None = aktueller Mode)
        """
        if mode is None:
            mode = self.current_mode
            
        controls = self.controls.get_sorted_controls(mode)
        logger.info(f"🔍 {len(controls)} Controls für Mode '{mode}' abgerufen")
        return controls
    
    def get_column_names(self, mode=None):
        """Gibt sortierte Spaltennamen für einen Mode zurück"""
        if mode is None:
            mode = self.current_mode
            
        return self.controls.get_column_names(mode)
    
    def update_visibility(self, column_name, visible):
        """Aktualisiert Sichtbarkeit einer Spalte"""
        self.controls.set_visibility(column_name, visible)
        logger.debug(f"🔄 Sichtbarkeit für '{column_name}': {visible}")
    
    def reorder_columns(self, new_order_mapping):
        """
        Ordnet Spalten neu an.
        
        Args:
            new_order_mapping: dict {column_name: new_display_order}
        """
        self.controls.reorder_controls(new_order_mapping)
        logger.debug(f"📋 Spalten neu angeordnet: {new_order_mapping}")
    
    def move_column_to_position(self, column_name, new_position):
        """
        Bewegt eine Spalte an eine neue Position.
        
        Args:
            column_name: Name der zu bewegenden Spalte
            new_position: Neue Position (0-basiert)
        """
        controls = self.get_controls_for_mode()
        
        # Aktuelle Positionen neu zuweisen
        new_mapping = {}
        current_pos = 0
        
        for control in controls:
            if control.name == column_name:
                continue  # Überspringe die zu bewegende Spalte
                
            if current_pos == new_position:
                current_pos += 1  # Platz für die eingefügte Spalte
                
            new_mapping[control.name] = current_pos + 1
            current_pos += 1
        
        # Die bewegte Spalte an neuer Position einfügen
        new_mapping[column_name] = new_position + 1
        
        self.reorder_columns(new_mapping)
        logger.debug(f"📈 Spalte '{column_name}' zu Position {new_position} bewegt")
    
    def get_control(self, column_name):
        """Holt ein spezifisches Control"""
        return self.controls.get_control(column_name)
    
    def set_mode(self, mode):
        """Setzt den aktuellen Mode"""
        self.current_mode = mode
        logger.info(f"🔄 Mode gewechselt zu: {mode}")
    
    def to_legacy_format(self, mode=None):
        """
        Konvertiert zu Legacy-Format für bestehende UI-Komponenten.
        Kann später entfernt werden.
        """
        if mode is None:
            mode = self.current_mode
            
        return self.controls.to_legacy_format(mode)
    
    def prepare_for_dialog(self, mode=None):
        """
        Bereitet alle Controls für Dialog vor.
        Kopiert Mode-spezifische Werte in display_* Felder.
        """
        if mode is None:
            mode = self.current_mode
            
        self.controls.prepare_for_dialog(mode)
        logger.info(f"🔧 Controls für Dialog vorbereitet - Mode: {mode}")
    
    def get_dialog_controls(self, mode=None):
        """
        Gibt Controls für Dialog zurück.
        Alle haben display_show und display_order für einheitliche Dialog-Handhabung.
        """
        if mode is None:
            mode = self.current_mode
            
        dialog_controls = self.controls.get_dialog_controls(mode)
        logger.info(f"📋 {len(dialog_controls)} Controls für Dialog bereitgestellt - Mode: {mode}")
        return dialog_controls
    
    def apply_dialog_changes(self, mode=None):
        """
        Übernimmt Dialog-Änderungen zurück in Mode-spezifische Felder.
        Transformiert display_* Werte in show/show_show und order/show_order.
        """
        if mode is None:
            mode = self.current_mode
            
        self.controls.apply_from_dialog(mode)
        logger.info(f"💾 Dialog-Änderungen übernommen - Mode: {mode}")
    
    def get_stats(self):
        """Gibt Statistiken über die Controls zurück"""
        total = len(self.controls)
        normal_visible = len([c for c in self.controls if c.is_visible_in_mode("normal")])
        expert_visible = len([c for c in self.controls if c.is_visible_in_mode("expert")])
        
        return {
            'total': total,
            'normal_visible': normal_visible,
            'expert_visible': expert_visible,
            'current_mode': self.current_mode
        }
