# SORTIERUNG AKTIVIEREN - Anleitung

## Problem:
Die Spalten sind als `sortable: false` konfiguriert. Deshalb zeigt die Sortierung keine Wirkung.

```
⚠️ Spalte 'anrede_show' ist nicht sortierbar
⚠️ Spalte 'familienname_show' ist nicht sortierbar
```

## Lösung:

Die Control-Konfiguration muss in der Datenbank (GCS) angepasst werden. Für jedes sortierbare Feld muss die UI-Konfiguration aktualisiert werden:

### Beispiel für `familienname_show`:

```json
{
    "control_key": "familienname_show",
    "name": "Familienname",
    "type": "string",
    "ui": {
        "sortable": true,           // ✅ DIES MUSS true SEIN!
        "sortDirection": "asc",     // Standard-Richtung
        "sortByOriginal": false     // Optional: Nach _original sortieren
    }
}
```

### Felder die sortierbar sein sollten:

1. **familienname_show** → `sortable: true`, `sortDirection: "asc"`
2. **vorname_show** → `sortable: true`, `sortDirection: "asc"`
3. **geburtsdatum_show** → `sortable: true`, `sortDirection: "desc"`, `sortByOriginal: true`
4. **geburtsdatum_alter_show** → `sortable: true`, `sortDirection: "desc"`
5. **anrede_show** → `sortable: true`, `sortDirection: "asc"`
6. **email_show** → `sortable: true`, `sortDirection: "asc"`

### Original-Felder (für ExpertMode):

7. **familienname_original** → `sortable: true`, `sortDirection: "asc"`
8. **vorname_original** → `sortable: true`, `sortDirection: "asc"`
9. **geburtsdatum_original** → `sortable: true`, `sortDirection: "desc"`
10. **anrede_original** → `sortable: true`, `sortDirection: "asc"`
11. **email_original** → `sortable: true`, `sortDirection: "asc"`

### Wie setzen?

**Option 1: Via Code (empfohlen für Massen-Update)**

Erstelle ein Skript `update_sortable_controls.py`:

```python
import logging
from pdvm_central_systemsteuerung import get_gcs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# View-GUID aus dem Log
VIEW_GUID = "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"

# Controls die sortierbar sein sollen
SORTABLE_CONTROLS = {
    # Show-Felder
    'familienname_show': {'direction': 'asc', 'by_original': False},
    'vorname_show': {'direction': 'asc', 'by_original': False},
    'geburtsdatum_show': {'direction': 'desc', 'by_original': True},
    'geburtsdatum_alter_show': {'direction': 'desc', 'by_original': False},
    'geburtsdatum_jahr_show': {'direction': 'desc', 'by_original': False},
    'geburtsdatum_monat_show': {'direction': 'asc', 'by_original': False},
    'geburtsdatum_tag_show': {'direction': 'asc', 'by_original': False},
    'anrede_show': {'direction': 'asc', 'by_original': False},
    'email_show': {'direction': 'asc', 'by_original': False},
    
    # Original-Felder
    'familienname_original': {'direction': 'asc', 'by_original': False},
    'vorname_original': {'direction': 'asc', 'by_original': False},
    'geburtsdatum_original': {'direction': 'desc', 'by_original': False},
    'geburtsdatum_alter_original': {'direction': 'desc', 'by_original': False},
    'geburtsdatum_jahr_original': {'direction': 'desc', 'by_original': False},
    'geburtsdatum_monat_original': {'direction': 'asc', 'by_original': False},
    'geburtsdatum_tag_original': {'direction': 'asc', 'by_original': False},
    'anrede_original': {'direction': 'asc', 'by_original': False},
    'email_original': {'direction': 'asc', 'by_original': False},
}

def update_sortable_controls():
    """Setzt sortable=true für alle relevanten Controls"""
    try:
        gcs = get_gcs()
        if not gcs:
            logger.error("❌ GCS nicht verfügbar!")
            return
        
        # Hole alle Controls für die View
        all_controls = gcs.get_all_controls(VIEW_GUID)
        
        if not all_controls:
            logger.warning("⚠️ Keine Controls gefunden!")
            return
        
        logger.info(f"📋 Gefunden: {len(all_controls)} Controls")
        
        # Aktualisiere jedes sortierbare Control
        updated_count = 0
        
        for control_key, sort_config in SORTABLE_CONTROLS.items():
            if control_key in all_controls:
                control = all_controls[control_key]
                
                # Stelle sicher, dass ui-Dict existiert
                if 'ui' not in control:
                    control['ui'] = {}
                
                # Aktualisiere Sortier-Einstellungen
                control['ui']['sortable'] = True
                control['ui']['sortDirection'] = sort_config['direction']
                control['ui']['sortByOriginal'] = sort_config['by_original']
                
                # Speichere in GCS
                gcs.set_control_value(VIEW_GUID, control_key, control)
                
                updated_count += 1
                logger.info(f"✅ {control_key}: sortable=true, direction={sort_config['direction']}")
            else:
                logger.warning(f"⚠️ Control nicht gefunden: {control_key}")
        
        # Rebuild Projektions-Tabellen nach Änderungen
        gcs.rebuild_projection_tables(VIEW_GUID)
        
        logger.info(f"🎉 {updated_count} Controls aktualisiert!")
        logger.info("✅ Projektions-Tabellen neu erstellt")
        
    except Exception as e:
        logger.error(f"❌ Fehler: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    update_sortable_controls()
```

**Ausführen:**
```bash
python update_sortable_controls.py
```

**Option 2: Via Spalten-Verwaltung (manuell)**

1. Öffne die View
2. Klicke auf Zahnrad → "Verwaltung der Spalten"
3. Für jede Spalte:
   - Prüfe ob `sortable` Checkbox vorhanden
   - Aktiviere sie
   - Setze `sortDirection` auf "asc" oder "desc"
4. "Spalten übernehmen"

## Test nach Update:

1. View öffnen
2. Klick auf "Familienname" Header
   - Sollte alphabetisch sortieren (A→Z)
3. Nochmal klicken
   - Sollte umgekehrt sortieren (Z→A)
4. Status-Log prüfen:
   - `✅ Einfache Sortierung angewandt: familienname_show`
   - Tabelle zeigt neue Reihenfolge

## Erweiterte Sortierung testen:

1. Zahnrad → "📊 Sortierung & Gruppierung"
2. Spalten per Drag & Drop hinzufügen
3. Doppelklick für Richtung (↑/↓)
4. Rechtsklick für Gruppierung
5. "Übernehmen"
6. Tabelle zeigt Gruppen mit Summen

## Debug:

Falls immer noch nicht sortierbar:

```python
# In Python-Konsole oder Skript:
from pdvm_central_systemsteuerung import get_gcs

gcs = get_gcs()
VIEW_GUID = "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"
controls = gcs.get_all_controls(VIEW_GUID)

# Prüfe familienname_show
fam_control = controls.get('familienname_show', {})
ui_config = fam_control.get('ui', {})

print(f"sortable: {ui_config.get('sortable')}")
print(f"sortDirection: {ui_config.get('sortDirection')}")
print(f"sortByOriginal: {ui_config.get('sortByOriginal')}")

# Sollte ausgeben:
# sortable: True
# sortDirection: asc
# sortByOriginal: False
```
