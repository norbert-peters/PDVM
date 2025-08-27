"""
PDVM Column Control - Einfache, einheitliche Control-Klasse
Jedes Control kennt alle seine Eigenschaften und kann sich selbst verwalten.
"""

class PdvmColumnControl:
    """
    Einfache Control-Klasse für Spalten.
    Enthält ALLE Eigenschaften einer Spalte an einem Ort.
    """
    
    def __init__(self, name, **kwargs):
        """
        Initialisiert ein Column Control mit allen Eigenschaften
        
        Args:
            name: Eindeutiger Spaltenname (Identifier)
            **kwargs: Alle anderen Eigenschaften der Spalte
        """
        # Grundlegende Eigenschaften
        self.name = name  # Eindeutiger Identifier
        self.anzeige = kwargs.get('anzeige', name)
        
        # Mode-spezifische Sichtbarkeit
        self.show = kwargs.get('show', True)  # Expert-Mode Sichtbarkeit
        self.show_show = kwargs.get('show_show', True)  # Normal-Mode Sichtbarkeit
        
        # Mode-spezifische Reihenfolge  
        self.order = kwargs.get('order', 999)  # Expert-Mode Reihenfolge
        self.show_order = kwargs.get('show_order', 999)  # Normal-Mode Reihenfolge
        
        # Dialog-Arbeitsfelder (temporär für Dialog-Kommunikation)
        self.display_show = kwargs.get('display_show', True)  # Dialog Sichtbarkeit
        self.display_order = kwargs.get('display_order', 999)  # Dialog Reihenfolge
        
        self.expert = kwargs.get('expert', False)
        
        # UI-Eigenschaften
        self.width = kwargs.get('width', 'auto')
        self.sortable = kwargs.get('sortable', True)
        self.searchable = kwargs.get('searchable', True)
        self.filterType = kwargs.get('filterType', 'contains')
        
        # Typ-Eigenschaften
        self.type = kwargs.get('type', 'show')
        self.original_field = kwargs.get('original_field', None)
        
        # Erweiterte Eigenschaften (alle anderen aus kwargs)
        for key, value in kwargs.items():
            if not hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self):
        """Gibt alle Eigenschaften als Dictionary zurück"""
        return {
            key: value for key, value in self.__dict__.items()
        }
    
    def update(self, **kwargs):
        """Aktualisiert Eigenschaften des Controls"""
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def is_visible_in_mode(self, mode="normal"):
        """Prüft ob Control im gegebenen Mode sichtbar ist"""
        if mode == "normal":
            return not self.expert and self.show_show
        else:  # expert
            return self.show
    
    def get_visibility_for_mode(self, mode="normal"):
        """Gibt die richtige Sichtbarkeits-Eigenschaft für den Mode zurück"""
        if mode == "normal":
            return self.show_show
        else:  # expert
            return self.show
    
    def get_order_for_mode(self, mode="normal"):
        """Gibt die richtige Reihenfolge-Eigenschaft für den Mode zurück"""
        if mode == "normal":
            return self.show_order
        else:  # expert
            return self.order
    
    def prepare_for_dialog(self, mode="normal"):
        """Bereitet Control für Dialog vor - kopiert Mode-Werte in display_* Felder"""
        self.display_show = self.get_visibility_for_mode(mode)
        self.display_order = self.get_order_for_mode(mode)
    
    def apply_from_dialog(self, mode="normal"):
        """Übernimmt display_* Werte zurück in Mode-spezifische Felder"""
        if mode == "normal":
            self.show_show = self.display_show
            self.show_order = self.display_order
        else:  # expert
            self.show = self.display_show
            self.order = self.display_order
    
    def __str__(self):
        return f"Control({self.name}: {self.anzeige}, order={self.display_order}, show={self.show})"
    
    def __repr__(self):
        return self.__str__()


class PdvmControlsCollection:
    """
    Collection für alle Column Controls.
    Einzige Quelle der Wahrheit für alle Spalten-Informationen.
    """
    
    def __init__(self):
        self._controls = {}  # name -> PdvmColumnControl
    
    def add_control(self, control):
        """Fügt ein Control zur Collection hinzu"""
        if isinstance(control, dict):
            # Dictionary zu Control konvertieren
            name = control.get('name')
            control = PdvmColumnControl(name, **control)
        
        self._controls[control.name] = control
    
    def get_control(self, name):
        """Holt ein Control über seinen Namen"""
        return self._controls.get(name)
    
    def update_control(self, name, **kwargs):
        """Aktualisiert ein Control"""
        if name in self._controls:
            self._controls[name].update(**kwargs)
    
    def get_sorted_controls(self, mode="normal"):
        """
        Gibt sortierte Controls für einen Mode zurück.
        Controls sortieren sich selbst über ihre Mode-spezifische Reihenfolge.
        """
        # Alle Controls für den Mode filtern
        visible_controls = [
            control for control in self._controls.values()
            if control.is_visible_in_mode(mode)
        ]
        
        # Nach Mode-spezifischer Reihenfolge sortieren
        return sorted(visible_controls, key=lambda c: c.get_order_for_mode(mode))
    
    def get_all_controls(self):
        """Gibt alle Controls zurück"""
        return list(self._controls.values())
    
    def prepare_for_dialog(self, mode="normal"):
        """Bereitet alle Controls für Dialog vor"""
        for control in self._controls.values():
            control.prepare_for_dialog(mode)
    
    def apply_from_dialog(self, mode="normal"):
        """Übernimmt Dialog-Änderungen in alle Controls"""
        for control in self._controls.values():
            control.apply_from_dialog(mode)
    
    def get_dialog_controls(self, mode="normal"):
        """
        Gibt Controls für Dialog zurück - alle Controls mit display_* Feldern.
        Im Expert-Mode auch expert=True Controls, im Normal-Mode nur expert=False.
        """
        if mode == "normal":
            # Normal-Mode: Nur non-expert Controls
            dialog_controls = [
                control for control in self._controls.values()
                if not control.expert
            ]
        else:
            # Expert-Mode: Alle Controls
            dialog_controls = list(self._controls.values())
        
        # Nach display_order sortieren
        return sorted(dialog_controls, key=lambda c: c.display_order)
    
    def reorder_controls(self, new_order_mapping):
        """
        Ordnet Controls neu an.
        new_order_mapping: dict {name: new_display_order}
        """
        for name, new_order in new_order_mapping.items():
            if name in self._controls:
                self._controls[name].display_order = new_order
    
    def set_visibility(self, name, visible):
        """Setzt Sichtbarkeit eines Controls (display_show für Dialog)"""
        if name in self._controls:
            self._controls[name].display_show = visible
    
    def get_column_names(self, mode="normal"):
        """Gibt sortierte Spaltennamen für einen Mode zurück"""
        controls = self.get_sorted_controls(mode)
        return [control.name for control in controls]
    
    def to_legacy_format(self, mode="normal"):
        """
        Konvertiert zu Legacy-Format für bestehende UI-Komponenten
        (kann später entfernt werden)
        """
        controls = self.get_sorted_controls(mode)
        return [control.to_dict() for control in controls]
    
    def __len__(self):
        return len(self._controls)
    
    def __iter__(self):
        return iter(self._controls.values())
    
    def __str__(self):
        return f"ControlsCollection({len(self._controls)} controls)"
