# 🔄 MIGRATION: 3-Ebenen-Struktur von Keys zu Array

## Problem mit aktuellem System

**Aktuell**: 3 separate Dictionary-Keys pro Spalte
```python
row_data = {
    'familienname_original': 'Mustermann',
    'familienname_original_abdatum': 2025043.0,
    'familienname_original_formatiertes_abdatum': '12.02.2025 - 00:00:00',
    
    'vorname_original': 'Max',
    'vorname_original_abdatum': 2025043.0,
    'vorname_original_formatiertes_abdatum': '12.02.2025 - 00:00:00',
    
    # ... bei 20 Spalten = 60 Keys!
}
```

**Nachteile**:
- ❌ Viele separate Keys (3x Anzahl Spalten)
- ❌ Fehleranfällig: Vergessen einer Ebene möglich
- ❌ Kopieren komplex: Muss für jede Ebene einzeln erfolgen
- ❌ Projektion komplex: Muss alle 3 Ebenen explizit kopieren

## Neue Array-Struktur

**Neu**: Array mit 3 Elementen pro Spalte
```python
row_data = {
    'familienname_original': ['Mustermann', 2025043.0, '12.02.2025 - 00:00:00'],
    'vorname_original': ['Max', 2025043.0, '12.02.2025 - 00:00:00'],
    
    # Bei 20 Spalten = nur 20 Keys!
}

# Zugriff über Array-Indices:
WERT = 0        # Index 0: Der eigentliche Wert
ABDATUM = 1     # Index 1: AB-Datum (roh, float)
FORMATIERT = 2  # Index 2: Formatiertes AB-Datum (String)

# Verwendung:
wert = row_data['familienname_original'][WERT]
abdatum = row_data['familienname_original'][ABDATUM]
formatiert = row_data['familienname_original'][FORMATIERT]
```

**Vorteile**:
- ✅ **Linear**: Eine Spalte = Ein Array (atomare Einheit)
- ✅ **Einfach**: Kopieren kopiert automatisch alle Ebenen
- ✅ **Robust**: Vergessen einer Ebene unmöglich
- ✅ **Performance**: 3x weniger Keys im Dictionary
- ✅ **Erweiterbar**: Weitere Ebenen einfach hinzufügen

---

## Migration Plan

### 1. Array-Konstanten definieren

**Datei**: `pdvm_matrix_constants.py` (NEU)
```python
"""
Konstanten für 3-Ebenen Array-Struktur in Matrix
"""

# Array-Indices für Spalten-Werte
WERT = 0        # Index 0: Der eigentliche Wert (String, int, float, etc.)
ABDATUM = 1     # Index 1: AB-Datum (float, z.B. 2025043.0)
FORMATIERT = 2  # Index 2: Formatiertes AB-Datum (String, z.B. "12.02.2025 - 00:00:00")

# Anzahl Ebenen
EBENEN_COUNT = 3

def create_cell(wert, abdatum=None, formatiert=None):
    """
    Erstellt eine Zelle mit 3 Ebenen
    
    Args:
        wert: Der eigentliche Wert
        abdatum: AB-Datum (roh, optional)
        formatiert: Formatiertes AB-Datum (optional)
    
    Returns:
        Array mit 3 Elementen [wert, abdatum, formatiert]
    """
    return [wert, abdatum, formatiert]

def get_wert(cell):
    """Holt EBENE 1 (Wert) aus Zelle"""
    if isinstance(cell, list) and len(cell) >= 1:
        return cell[WERT]
    return cell  # Fallback für Legacy

def get_abdatum(cell):
    """Holt EBENE 2 (AB-Datum) aus Zelle"""
    if isinstance(cell, list) and len(cell) >= 2:
        return cell[ABDATUM]
    return None

def get_formatiert(cell):
    """Holt EBENE 3 (Formatiertes AB-Datum) aus Zelle"""
    if isinstance(cell, list) and len(cell) >= 3:
        return cell[FORMATIERT]
    return None
```

---

### 2. BasisMatrix-Erstellung anpassen

**Datei**: `pdvm_view_matrix_manager.py`

**Vorher** (Lines ~190-200):
```python
# EBENE 1: WERT speichern
row_data[control_key] = wert

# EBENE 2: ABDATUM speichern (roh)
row_data[f"{control_key}_abdatum"] = abdatum

# EBENE 3: FORMATIERTES ABDATUM speichern
if abdatum:
    formatiertes_abdatum = self._format_abdatum(abdatum)
    row_data[f"{control_key}_formatiertes_abdatum"] = formatiertes_abdatum
else:
    row_data[f"{control_key}_formatiertes_abdatum"] = None
```

**Nachher**:
```python
from pdvm_matrix_constants import create_cell

# ALLE 3 EBENEN in einem Array
if abdatum:
    formatiertes_abdatum = self._format_abdatum(abdatum)
else:
    formatiertes_abdatum = None

row_data[control_key] = create_cell(wert, abdatum, formatiertes_abdatum)
```

**Änderungen**:
- ✅ 8 Zeilen → 1 Zeile
- ✅ Keine separaten Keys mehr
- ✅ Atomare Operation

---

### 3. Show-Spalten Kopieren anpassen

**Datei**: `pdvm_view_matrix_manager.py`

**Vorher** (Lines ~240-250):
```python
# Kopiere ALLE 3 Ebenen von Original zu Show
original_wert = row_data.get(original_key)
row_data[control_key] = original_wert

original_abdatum = row_data.get(f"{original_key}_abdatum")
row_data[f"{control_key}_abdatum"] = original_abdatum

original_formatiert = row_data.get(f"{original_key}_formatiertes_abdatum")
row_data[f"{control_key}_formatiertes_abdatum"] = original_formatiert
```

**Nachher**:
```python
# Array-Kopie: ALLE 3 Ebenen automatisch dabei!
row_data[control_key] = row_data.get(original_key, [None, None, None])
```

**Änderungen**:
- ✅ 7 Zeilen → 1 Zeile
- ✅ Automatisch komplett
- ✅ Kann nicht vergessen werden

---

### 4. Projektion anpassen

**Datei**: `pdvm_view_matrix_manager.py`

**Vorher** (Lines ~460-475):
```python
for col in available_columns:
    # EBENE 1: Basis-Wert
    projected_row[col] = row.get(col)
    
    # EBENE 2: AB-Datum (roh)
    abdatum_key = f"{col}_abdatum"
    if abdatum_key in row:
        projected_row[abdatum_key] = row.get(abdatum_key)
    
    # EBENE 3: Formatiertes AB-Datum
    formatiert_key = f"{col}_formatiertes_abdatum"
    if formatiert_key in row:
        projected_row[formatiert_key] = row.get(formatiert_key)
```

**Nachher**:
```python
for col in available_columns:
    # Array-Kopie: ALLE 3 Ebenen automatisch dabei!
    projected_row[col] = row.get(col)
```

**Änderungen**:
- ✅ 11 Zeilen → 1 Zeile
- ✅ Keine if-Checks mehr nötig
- ✅ Automatisch immer vollständig

---

### 5. View/UI Zugriff anpassen

**Datei**: `pdvm_view_ui.py` oder wo auch immer die Tabelle befüllt wird

**Vorher**:
```python
# Wert in Tabelle setzen
cell_value = row_data.get('familienname_show')
table.setItem(row_idx, col_idx, QTableWidgetItem(str(cell_value)))

# Tooltip erstellen
abdatum = row_data.get('familienname_show_formatiertes_abdatum')
if abdatum:
    item.setToolTip(f"Abdatum: {abdatum}")
```

**Nachher**:
```python
from pdvm_matrix_constants import WERT, FORMATIERT

# Array holen
cell_array = row_data.get('familienname_show', [None, None, None])

# Wert in Tabelle setzen
table.setItem(row_idx, col_idx, QTableWidgetItem(str(cell_array[WERT])))

# Tooltip erstellen
if cell_array[FORMATIERT]:
    item.setToolTip(f"Abdatum: {cell_array[FORMATIERT]}")
```

---

### 6. Filter/Sort anpassen

**Filter** arbeitet auf EBENE 1 (Wert):
```python
from pdvm_matrix_constants import WERT

def filter_func(row):
    familienname = row.get('familienname_original', [None, None, None])
    return 'Mustermann' in str(familienname[WERT])
```

**Sort** arbeitet auf EBENE 1 (Wert):
```python
from pdvm_matrix_constants import WERT

def sort_key(row):
    familienname = row.get('familienname_original', [None, None, None])
    return str(familienname[WERT])
```

---

## Migrations-Reihenfolge

### Phase 1: Foundation ✅
1. `pdvm_matrix_constants.py` erstellen
2. In allen Dateien importieren

### Phase 2: Matrix-Erstellung 🔄
3. `pdvm_view_matrix_manager.py` - `initialize_basis_matrix()`
   - Original-Felder befüllen (Array statt 3 Keys)
4. `pdvm_view_matrix_manager.py` - Show-Felder kopieren
   - Array-Kopie statt 3 separate Kopien

### Phase 3: Pipeline 🔄
5. `pdvm_view_matrix_manager.py` - `apply_filter()`
   - Filter auf `cell[WERT]` arbeiten lassen
6. `pdvm_view_matrix_manager.py` - `apply_sort()`
   - Sort auf `cell[WERT]` arbeiten lassen
7. `pdvm_view_matrix_manager.py` - `apply_projection()`
   - Einfache Array-Kopie (bereits gemacht!)

### Phase 4: UI/View 🔄
8. View-Tabellen Befüllung
   - `cell[WERT]` für Anzeige
   - `cell[FORMATIERT]` für Tooltips
9. Spalten-Management Dialoge
   - Bei Bedarf auf Array-Zugriff umstellen

### Phase 5: Testing ✅
10. Alte `_abdatum` Key-Zugriffe entfernen
11. Alte `_formatiertes_abdatum` Key-Zugriffe entfernen
12. Tests durchlaufen lassen

---

## Erwartete Verbesserungen

### Code-Reduktion
- **BasisMatrix-Erstellung**: ~30% weniger Code
- **Projektion**: ~80% weniger Code
- **Show-Spalten Kopie**: ~85% weniger Code

### Performance
- **Memory**: 3x weniger Keys pro Row (bei 20 Spalten: 60 Keys → 20 Keys)
- **Kopier-Speed**: Schneller durch weniger Dictionary-Operationen

### Robustheit
- **Keine vergessenen Ebenen**: Array ist atomar
- **Keine Sync-Probleme**: Alle Ebenen immer zusammen
- **Type-Safety**: Optional mit TypedDict möglich

---

## Rollback-Plan

Falls Probleme auftreten:

```python
# Helper-Funktion für Legacy-Support
def ensure_array_format(cell_value):
    """Konvertiert alte Key-Struktur zu Array"""
    if isinstance(cell_value, list):
        return cell_value  # Bereits Array
    else:
        return [cell_value, None, None]  # Legacy → Array
```

---

## Erweiterbarkeit (Zukunft)

Das Array-System ermöglicht einfache Erweiterungen:

```python
# Weitere Metadaten hinzufügen:
WERT = 0
ABDATUM = 1
FORMATIERT = 2
USER_CHANGED = 3      # Wer hat geändert?
VALIDATION_STATUS = 4  # Validierungsstatus
HISTORY_COUNT = 5      # Anzahl Änderungen

cell = [wert, abdatum, formatiert, user_guid, 'valid', 5]
```

Oder mit **NamedTuple** für benannte Zugriffe:
```python
from typing import NamedTuple

class CellValue(NamedTuple):
    wert: Any
    abdatum: float | None
    formatiert: str | None
    
cell = CellValue('Mustermann', 2025043.0, '12.02.2025')
print(cell.wert)       # Benannter Zugriff!
print(cell.abdatum)    # Type-Safe!
```

---

## Zusammenfassung

**Warum diese Migration?**
- ✅ **Einfacher**: Weniger Code, weniger Komplexität
- ✅ **Linearer**: Atomare Kopie-Operationen
- ✅ **Robuster**: Kann nichts vergessen werden
- ✅ **Schneller**: Weniger Dictionary-Keys
- ✅ **Zukunftssicher**: Einfach erweiterbar

**Aufwand**: Mittel (4-6 Stunden)
**Nutzen**: Hoch (Dauerhaft vereinfachter Code)
**Risiko**: Niedrig (Einfaches Rollback möglich)

---

## Status

- [ ] Konstanten-Datei erstellt
- [ ] BasisMatrix-Erstellung umgestellt
- [ ] Show-Spalten Kopie umgestellt
- [ ] Projektion umgestellt (✅ bereits vorbereitet)
- [ ] UI/View Zugriff umgestellt
- [ ] Filter/Sort umgestellt
- [ ] Tests durchgeführt
- [ ] Alte Key-Zugriffe entfernt
- [ ] Dokumentation aktualisiert

**Start**: 2025-10-11
**Ziel-Completion**: TBD
