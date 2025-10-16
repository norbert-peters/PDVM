# Projection Table Array Struktur

## Konzept: Zentrale Array-basierte Projektionen

**Problem**: Projektionen werden am Verwendungsort modifiziert (z.B. `sortable` Filter), was gegen das Prinzip der zentralen, unveränderlichen Projektionen verstößt.

**Lösung**: 10-Positionen Array in GCS mit fester Systematik für verschiedene Verwendungszwecke.

## Array-Struktur

```python
# 10 Positionen: 0-4 Standard Mode, 5-9 Expert Mode
projection_tables[view_guid] = [
    # STANDARD MODE (0-4)
    0: table_standard,           # View-Darstellung (nur show=true, display_order)
    1: change_standard,          # Spalten verwalten (nicht expert_mode, display_order)  
    2: filter_standard,          # Filter-Dialog (alle sichtbaren + filterbare)
    3: sort_standard,            # Sort-Dialog (nur sortierbare aus change_standard)
    4: reserved_standard,        # Reserviert für zukünftige Dialoge
    
    # EXPERT MODE (5-9) - Entsprechende Position + 5
    5: table_expert,             # View-Darstellung (alle außer dummy, expert_order)
    6: change_expert,            # Spalten verwalten (alle außer dummy, expert_order)
    7: filter_expert,            # Filter-Dialog (alle außer dummy + filterbare)
    8: sort_expert,              # Sort-Dialog (nur sortierbare aus change_expert)
    9: reserved_expert           # Reserviert für zukünftige Dialoge
]
```

## Konstanten

```python
# Position-Indizes (Standard Mode, 0-4)
TABLE_INDEX_VIEW = 0           # View-Darstellung
TABLE_INDEX_CHANGE = 1         # Spalten verwalten
TABLE_INDEX_FILTER = 2         # Filter-Dialog
TABLE_INDEX_SORT = 3           # Sort-Dialog
TABLE_INDEX_RESERVED = 4       # Reserviert

# Expert Mode Offset
EXPERT_MODE_OFFSET = 5         # Expert Mode = Standard + 5

# Berechnung:
# index = BASE_INDEX + (EXPERT_MODE_OFFSET if expert_mode else 0)
```

## Vorteile

1. ✅ **Linear & Einfach**: Formel `index = base + (5 if expert else 0)`
2. ✅ **Zentral**: Alle Projektionen werden in `_build_projection_tables()` erstellt
3. ✅ **Unveränderlich**: Am Verwendungsort wird NICHT mehr gefiltert/modifiziert
4. ✅ **Erweiterbar**: 2 freie Slots (4, 9) für zukünftige Dialoge
5. ✅ **Konsistent**: Jede Projektion hat exakt die richtigen Spalten für ihren Zweck
6. ✅ **Performant**: Array-Zugriff O(1) statt Dict-Lookup

## Verwendung

### In Dialogen

```python
from pdvm_central_systemsteuerung import (
    get_gcs, 
    TABLE_INDEX_SORT,
    EXPERT_MODE_OFFSET
)

gcs = get_gcs()
expert_offset = EXPERT_MODE_OFFSET if gcs.expert_mode else 0
projection = gcs.get_projection_table(view_guid, TABLE_INDEX_SORT + expert_offset)

# projection enthält DIREKT die richtigen Spalten, KEINE weitere Filterung!
```

### Alte vs. Neue API

```python
# ❌ ALT (String-basiert, Filterung am Verwendungsort):
projection = gcs.get_projection_table(view_guid, 'change_standard')
sortable_columns = [col for col in projection 
                   if controls[col].get('sortable', False)]  # Filterung!

# ✅ NEU (Array-basiert, bereits gefiltert):
projection = gcs.get_projection_table(view_guid, TABLE_INDEX_SORT)
# projection enthält bereits NUR sortierbare Spalten!
```

## Projektions-Logik

### Position 0/5: View (table_standard/expert)
**Zweck**: Darstellung in der Hauptansicht (ProjectionMatrix)
- **Standard**: Nur `show=true`, sortiert nach `display_order`
- **Expert**: Alle Controls außer dummy, sortiert nach `expert_order`

### Position 1/6: Change (change_standard/expert)
**Zweck**: "Spalten verwalten" Dialog - welche Spalten sind verfügbar
- **Standard**: Nur `expert_mode != true`, sortiert nach `display_order`
- **Expert**: Alle Controls außer dummy, sortiert nach `expert_order`

### Position 2/7: Filter (filter_standard/expert)
**Zweck**: Filter-Dialog - welche Spalten sind filterbar
- **Standard**: Controls mit `show=true` UND `filterable=true`
- **Expert**: Alle Controls außer dummy mit `filterable=true`

### Position 3/8: Sort (sort_standard/expert) **NEU!**
**Zweck**: Sort-Dialog - welche Spalten sind sortierbar
- **Standard**: Controls aus `change_standard` mit `sortable=true`
- **Expert**: Controls aus `change_expert` mit `sortable=true`

**WICHTIG**: Sort-Projektion basiert auf Change-Projektion, nicht auf View!
- User kann in "Spalten verwalten" Spalten aktivieren/deaktivieren
- Diese Spalten sollen dann auch im Sort-Dialog verfügbar sein
- Auch wenn sie aktuell nicht sichtbar sind (show=false)

### Position 4/9: Reserviert
**Zweck**: Zukünftige Dialoge/Features
- Mögliche Verwendung: Gruppierungs-Dialog, Export-Dialog, etc.

## Migration

### Phase 1: GCS-Implementierung
- [x] Array-Struktur in `__init__`: `self._projection_tables = {}`
- [ ] Konstanten definieren
- [ ] `_build_projection_tables()` auf Array umstellen
- [ ] `get_projection_table()` auf Integer-Index umstellen
- [ ] Abwärtskompatibilität: String-Index → Integer-Mapping

### Phase 2: Dialog-Migration
- [ ] Sort-Dialog auf INDEX 3 umstellen
- [ ] Spalten-Dialog auf INDEX 1 umstellen
- [ ] Filter-Dialog auf INDEX 2 umstellen (falls vorhanden)
- [ ] View-Controller auf INDEX 0 umstellen

### Phase 3: Cleanup
- [ ] Alte String-basierte API entfernen
- [ ] Tests anpassen
- [ ] Dokumentation aktualisieren

## Kompatibilität

Für sanfte Migration: String-zu-Index-Mapping in `get_projection_table()`:

```python
# Mapping alte Namen → neue Indizes
_LEGACY_INDEX_MAP = {
    'table_standard': 0,
    'table_expert': 5,
    'change_standard': 1,
    'change_expert': 6,
    'filter_standard': 2,
    'filter_expert': 7,
    'sort_standard': 3,
    'sort_expert': 8,
    # Alte Namen (Kompatibilität)
    'search_standard': 2,
    'search_expert': 7,
}

def get_projection_table(self, view_guid: str, index_or_name):
    """
    Args:
        index_or_name: Integer (0-9) oder String (legacy)
    """
    if isinstance(index_or_name, str):
        # Legacy String → Integer
        index = _LEGACY_INDEX_MAP.get(index_or_name)
        if index is None:
            logger.warning(f"⚠️ Unbekannter Projektions-Name: {index_or_name}")
            return []
    else:
        index = index_or_name
    
    # Array-Zugriff
    tables = self._projection_tables.get(view_guid)
    return tables[index] if tables and 0 <= index < 10 else []
```

## Beispiel-Code

```python
# Sort-Dialog in pdvm_view_ui.py
from pdvm_central_systemsteuerung import (
    get_gcs, 
    TABLE_INDEX_SORT,
    EXPERT_MODE_OFFSET
)

def _request_advanced_sort(self):
    gcs = get_gcs()
    
    # Berechne Index: 3 (Standard) oder 8 (Expert)
    table_index = TABLE_INDEX_SORT + (EXPERT_MODE_OFFSET if gcs.expert_mode else 0)
    
    # Hole Projektion (bereits gefiltert: nur sortierbare Spalten!)
    projection = gcs.get_projection_table(self.controller.view_guid, table_index)
    
    logger.info(f"📋 Sort-Projektion Index {table_index}: {len(projection)} Spalten")
    
    # Dialog öffnen - KEINE weitere Filterung nötig!
    dialog = AdvancedSortDialog(
        controls_config=self.current_controls,
        view_guid=self.controller.view_guid,
        projection=projection,  # Bereits nur sortierbare Spalten
        parent=self
    )
```

## Status

- ✅ Konzept definiert
- ✅ Dokumentation erstellt
- 🔄 Implementation läuft
- ⏳ Migration ausstehend
- ⏳ Tests ausstehend
