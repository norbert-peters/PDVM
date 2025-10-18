# Projektions-Tabellen Korrektur

**Datum**: 16. Oktober 2025  
**Status**: ✅ ABGESCHLOSSEN

## 🎯 Problem

Die Projektions-Tabellen für View und Spalten-Verwaltung waren nicht korrekt konfiguriert:
- ❌ Change Standard verwendete `display_order` statt `display_sort`
- ❌ Nur `dummy` wurde excludiert, aber nicht `row_type`
- ❌ View Expert sollte `dummy + row_type` ausschließen

## ✅ Lösung - Korrekte Projektions-Regeln

### 1. View Standard (Position 0)
- **Filter**: Alle Spalten mit `show=true`
- **Sortierung**: `display_order`
- **Verwendung**: Hauptansicht im Standard-Modus
- **Status**: ✅ Korrekt (war bereits richtig)

### 2. View Expert (Position 5)
- **Filter**: Alle Spalten AUSSER `dummy` UND `row_type`
- **Sortierung**: `expert_order`
- **Verwendung**: Hauptansicht im Expert-Modus
- **Status**: ⭐ KORRIGIERT (excludiert jetzt auch `row_type`)

### 3. Change Standard (Position 1)
- **Filter**: Alle Spalten mit `expert_mode=false`
- **Sortierung**: `display_sort` ⭐ **KORRIGIERT** (war `display_order`)
- **Verwendung**: Spalten-Verwaltung im Standard-Modus
- **Status**: ⭐ KORRIGIERT

### 4. Change Expert (Position 6)
- **Filter**: Alle Spalten AUSSER `dummy` UND `row_type`
- **Sortierung**: `expert_order`
- **Verwendung**: Spalten-Verwaltung im Expert-Modus
- **Status**: ⭐ KORRIGIERT (excludiert jetzt auch `row_type`)

### 5. Filter Standard/Expert (Positionen 2/7)
- **Status**: ✅ BEIBEHALTEN (war bereits korrekt)
- Standard: Alle sichtbaren Spalten
- Expert: Alle Spalten außer dummy+row_type

### 6. Sort Standard/Expert (Positionen 3/8)
- **Status**: ✅ BEIBEHALTEN (war bereits korrekt)
- Standard: Alle sichtbaren Spalten
- Expert: Alle Spalten außer dummy+row_type

## 🔧 Code-Änderungen

### 1. Control-Info erweitert (Zeile 695)
```python
control_info = {
    'key': control_key,
    'display_order': control_data.get('display_order', 999),
    'display_sort': control_data.get('display_sort', 999),  # ⭐ NEU
    'expert_order': control_data.get('expert_order', 999),
    'show': control_data.get('show', False),
    'expert_mode': control_data.get('expert_mode', False),
    'sortable': control_data.get('sortable', False),
    'filterable': control_data.get('filterable', False)
}
```

### 2. Exclusion-Logik erweitert (Zeile 687-694)
```python
# VORHER: Nur dummy
is_dummy = (control_type == 'dummy' or 
           control_data.get('dummy', False) or 
           control_key.lower().startswith('dummy'))

if is_dummy:
    dummy_controls.append(control_key)

# NACHHER: dummy + row_type
is_dummy = (control_type == 'dummy' or 
           control_data.get('dummy', False) or 
           control_key.lower().startswith('dummy'))
is_row_type = (control_key == 'row_type')

if is_dummy or is_row_type:
    excluded_controls.append(control_key)
```

### 3. Sortierung für Change Standard korrigiert (Zeile 723-727)
```python
# VORHER: display_order
non_expert_by_display = sorted(
    non_expert_controls, 
    key=lambda x: x['display_order']
)

# NACHHER: display_sort
non_expert_by_display_sort = sorted(
    non_expert_controls, 
    key=lambda x: x['display_sort']  # ⭐ KORRIGIERT
)
```

### 4. Array-Zuweisung korrigiert (Zeile 739-760)
```python
# Position 1: Change Standard
# VORHER
tables[1] = [c['key'] for c in non_expert_by_display]

# NACHHER
tables[1] = [c['key'] for c in non_expert_by_display_sort]  # ⭐ KORRIGIERT

# Position 5/6: View/Change Expert
# VORHER
tables[5] = [c['key'] for c in all_controls_by_expert]  # dummy only
tables[6] = [c['key'] for c in all_controls_by_expert]  # dummy only

# NACHHER
tables[5] = [c['key'] for c in all_by_expert]  # dummy + row_type
tables[6] = [c['key'] for c in all_by_expert]  # dummy + row_type
```

## 📊 Projektions-Array Übersicht (KORRIGIERT)

```
Position | Name           | Filter                    | Sortierung    | Status
---------|----------------|---------------------------|---------------|--------
   0     | View Standard  | show=true                 | display_order | ✅
   1     | Change Std     | expert_mode=false         | display_sort  | ⭐
   2     | Filter Std     | show=true                 | display_order | ✅
   3     | Sort Std       | show=true                 | display_order | ✅
   4     | Reserviert     | -                         | -             | ✅
   5     | View Expert    | alle außer dummy+row_type | expert_order  | ⭐
   6     | Change Expert  | alle außer dummy+row_type | expert_order  | ⭐
   7     | Filter Expert  | alle außer dummy+row_type | expert_order  | ✅
   8     | Sort Expert    | alle außer dummy+row_type | expert_order  | ✅
   9     | Reserviert     | -                         | -             | ✅
```

## 🧪 Logging-Output (KORRIGIERT)

```
✅ ARRAY-BASIERTE Projektions-Tabellen für {view_guid} erstellt:
  [0] 📊 View Standard: X Spalten (show=true, display_order)
  [1] 🔧 Change Standard: X Spalten (expert_mode=false, display_sort) ⭐ KORRIGIERT
  [2] 🔍 Filter Standard: X Spalten (sichtbar + filterbar)
  [3] 🔄 Sort Standard: X Spalten (sichtbar + sortierbar)
  [4] ⏸️  Reserviert: 0 Spalten
  [5] 📊 View Expert: X Spalten (alle außer dummy+row_type, expert_order) ⭐ KORRIGIERT
  [6] 🔧 Change Expert: X Spalten (alle außer dummy+row_type, expert_order) ⭐ KORRIGIERT
  [7] 🔍 Filter Expert: X Spalten (alle filterbar)
  [8] 🔄 Sort Expert: X Spalten (alle sortierbar)
  [9] ⏸️  Reserviert: 0 Spalten
  ❌ Excluded: X (dummy + row_type) ⭐ KORRIGIERT
  📋 Non-Expert: X (für Change Standard)
```

## 🔍 Was wurde geändert?

### 3 Korrekturen:
1. ⭐ **Change Standard**: Sortierung `display_order` → `display_sort`
2. ⭐ **View Expert**: Excludiert jetzt `dummy` + `row_type` (vorher nur `dummy`)
3. ⭐ **Change Expert**: Excludiert jetzt `dummy` + `row_type` (vorher nur `dummy`)

### Was blieb gleich:
- ✅ View Standard (Position 0)
- ✅ Filter Standard/Expert (Position 2/7)
- ✅ Sort Standard/Expert (Position 3/8)
- ✅ Reservierte Positionen (4/9)

## 🎯 Auswirkungen

### Spalten-Verwaltung Dialog
- **Standard-Modus**: Zeigt jetzt Spalten in `display_sort` Reihenfolge (statt `display_order`)
- **Expert-Modus**: Zeigt alle Spalten außer `dummy` und `row_type`

### View-Ansicht
- **Expert-Modus**: `row_type` wird nicht mehr angezeigt (war vorher sichtbar)

### Datei geändert
- ✅ `pdvm_central_systemsteuerung.py` - Methode `_build_projection_tables()` (Zeile 654-794)

## 📋 Nächste Schritte

1. **Testen**: Spalten-Verwaltung im Standard- und Expert-Modus
2. **Verifizieren**: Korrekte Sortierung nach `display_sort`
3. **Prüfen**: `row_type` wird nicht mehr in Expert-View angezeigt

---

**Status**: ✅ Projektions-Tabellen korrekt konfiguriert
