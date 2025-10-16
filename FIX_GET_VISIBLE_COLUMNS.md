# FIX: _get_visible_columns_from_gcs() korrigieren

## Problem

Die Methode `_get_visible_columns_from_gcs()` in `pdvm_view_dialog.py` verwendet NICHT die Projektions-Tabellen aus der GCS, sondern filtert direkt aus `controls_config`.

**Aktueller Code (FALSCH):**
```python
# Filtert direkt aus controls_config
visible_cols = [key for key in self.controls_config.keys() 
               if (self.controls_config[key].get('control_type') == 'show' and 
                   self.controls_config[key].get('show', False))]
```

**Problem:**
- Ignoriert die Reihenfolge aus `display_order`
- Ignoriert die vorberechneten Projektions-Tabellen
- Änderungen im Column Management Dialog werden nicht übernommen

## Lösung

**Neuer Code (KORREKT):**
```python
def _get_visible_columns_from_gcs(self):
    """
    🎯 SPALTEN-PROJEKTION: Verwendet die vorberechneten Projektions-Tabellen aus GCS
    
    KORREKTE ARCHITEKTUR:
    - Verwendet get_projection_table() aus GCS
    - StandardMode: 'table_standard' Projektion (nur show=true)
    - ExpertMode: 'table_expert' Projektion (alle außer dummy)
    - Reihenfolge und Auswahl kommen aus den Projektions-Tabellen
    """
    try:
        from pdvm_central_systemsteuerung import get_gcs
        gcs = get_gcs()
        
        if not gcs:
            logger.warning("⚠️ GCS nicht verfügbar für Spalten-Projektion")
            return []
        
        # KRITISCH: Verwende die vorberechneten Projektions-Tabellen!
        # Diese werden bei rebuild_projection_tables() aus den Controls erstellt
        if gcs.expert_mode:
            projection = gcs.get_projection_table(self.view_guid, 'table_expert')
            mode_info = "ExpertMode"
        else:
            projection = gcs.get_projection_table(self.view_guid, 'table_standard')
            mode_info = "StandardMode"
        
        if not projection:
            logger.warning(f"⚠️ Keine Projektion verfügbar für {mode_info}")
            # Fallback: Projektions-Tabellen neu aufbauen
            logger.info(f"🔄 Baue Projektions-Tabellen neu auf...")
            gcs.rebuild_projection_tables(self.view_guid)
            
            # Erneut versuchen
            if gcs.expert_mode:
                projection = gcs.get_projection_table(self.view_guid, 'table_expert')
            else:
                projection = gcs.get_projection_table(self.view_guid, 'table_standard')
            
            if not projection:
                logger.error(f"❌ Auch nach rebuild keine Projektion verfügbar!")
                return []
        
        logger.info(f"✅ {mode_info} Projektion: {len(projection)} Spalten in Reihenfolge")
        logger.debug(f"📋 Spalten: {projection[:5]}..." if len(projection) > 5 else f"📋 Spalten: {projection}")
        
        return projection
    
    except Exception as e:
        logger.error(f"❌ Fehler bei Spalten-Projektion: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []
```

## Änderung durchführen

### Schritt 1: Öffnen Sie `pdvm_view_dialog.py`

### Schritt 2: Suchen Sie die Funktion `_get_visible_columns_from_gcs`
- Befindet sich bei Zeile ca. 2239

### Schritt 3: Ersetzen Sie die gesamte Funktion mit dem neuen Code oben

### Schritt 4: Speichern

## Was ändert sich

**Vorher:**
1. Methode fragt `controls_config` ab
2. Filtert manuell nach `show=True`
3. Keine Sortierung nach `display_order`
4. Änderungen aus Column Management werden ignoriert

**Nachher:**
1. Methode verwendet `gcs.get_projection_table()`
2. Holt vorberechnete, sortierte Liste
3. Enthält korrekte Reihenfolge aus `display_order`
4. Änderungen aus Column Management werden sofort übernommen

## Test

Nach der Änderung:
1. Anwendung starten
2. View öffnen
3. Spalten verwalten → Reihenfolge ändern
4. ✅ Neue Reihenfolge wird in View angezeigt
5. Spalten verwalten → Spalte aktivieren (show=true)
6. ✅ Neue Spalte wird in View angezeigt
