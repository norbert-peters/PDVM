# FILTER-ARCHITEKTUR - PDVM System

## Matrix-Pipeline (LINEAR)

```
┌─────────────────────────────────────────────────────────────┐
│ BASIS_MATRIX                                                 │
│ - Alle Spalten (original + show + berechnete Felder)       │
│ - Alle Daten (komplett, ungefiltert)                       │
│ - Wird NUR bei Start/Stichtag-Wechsel neu befüllt          │
└─────────────────────────────────────────────────────────────┘
                           ↓ apply_filter()
┌─────────────────────────────────────────────────────────────┐
│ FILTER_MATRIX                                                │
│ - Alle Spalten (wie BASIS_MATRIX)                          │
│ - Gefilterte Daten (nach search_string)                    │
│ - Filter arbeitet auf ALLEN Spalten!                       │
└─────────────────────────────────────────────────────────────┘
                           ↓ apply_sort()
┌─────────────────────────────────────────────────────────────┐
│ SORT_MATRIX                                                  │
│ - Alle Spalten (wie FILTER_MATRIX)                         │
│ - Sortierte Daten (nach sort_column)                       │
└─────────────────────────────────────────────────────────────┘
                           ↓ Projektion
┌─────────────────────────────────────────────────────────────┐
│ VIEW (Tabelle)                                               │
│ - Nur SICHTBARE Spalten (aus GCS Projection)               │
│ - Standard: 7 Spalten (_show Felder)                       │
│ - Expert: Alle Spalten                                     │
└─────────────────────────────────────────────────────────────┘
```

## Filter-System

### 1. Globaler Filter (in View)
- **Eingabe**: Suchfeld in View-Header
- **Funktion**: Sucht in ALLEN Spalten der BASIS_MATRIX
- **Verarbeitung**: LinearFilterExecutionManager → MatrixManager.apply_filter()
- **Format**: Einfacher String `"li"` → sucht "li" in allen Spalten

### 2. Erweiterter Filter (Dialog)
- **Eingabe**: Filter-Dialog mit Spalten-Zeilen
- **UI**: Zwei Filter pro Spalte nebeneinander:
  - **Links: EINFACHER FILTER**
    - Eingabefeld + +/- Button (Include/Exclude)
    - Operator: Immer "enthält"
    - Generiert: `"column:value"` oder `"column:NOT:value"`
  - **Rechts: KOMPLEXER FILTER** (Stufe 2, zunächst inaktiv)
    - Details-Button + UND/ODER-Button
    
### 3. Filter-String Format

**Einfacher Filter:**
```python
# Include
"familienname:Müller"           # Familienname enthält "Müller"

# Exclude
"familienname:NOT:Müller"       # Familienname enthält NICHT "Müller"

# Multiple (ODER-Verknüpfung)
"familienname:Müller|vorname:Hans"  # Familienname enthält "Müller" ODER Vorname enthält "Hans"
```

**Komplexer Filter (Stufe 2):**
```python
# UND-Verknüpfung
"familienname:Müller&vorname:Hans"  # Familienname enthält "Müller" UND Vorname enthält "Hans"

# Operatoren
"geburtsdatum:>:2000"          # Geburtsdatum größer als 2000
"geburtsdatum:BETWEEN:1990:2000"  # Geburtsdatum zwischen 1990 und 2000
```

## Filter-Ausführung

### LinearFilterExecutionManager
```python
from linear_filter_execution_manager import get_linear_filter_manager

# 1. Manager holen
manager = get_linear_filter_manager(view_guid)

# 2. Filter ausführen (IMMER mit vollständigem Reset!)
manager.execute_filter_linear('global', 'li')  # Globale Suche

# 3. MatrixManager macht:
#    - BASIS_MATRIX bleibt unverändert
#    - Filtert auf FILTER_MATRIX
#    - Sortiert auf SORT_MATRIX
#    - View zeigt nur projizierte Spalten
```

## Wichtige Regeln

1. **ALLE Matrizen haben ALLE Spalten**
   - BASIS_MATRIX: 62 Spalten
   - FILTER_MATRIX: 62 Spalten
   - SORT_MATRIX: 62 Spalten
   - VIEW: 7 Spalten (nur Projektion!)

2. **Filter arbeitet auf ALLEN Spalten**
   - Auch wenn nur 7 Spalten sichtbar sind
   - Filter durchsucht alle 62 Spalten
   - Projektion erfolgt NACH Filter/Sort

3. **Dialog zeigt nur SICHTBARE Spalten**
   - Bessere UX - weniger Unübersichtlichkeit
   - Standard: 7 _show Felder
   - Expert Mode: Könnte alle zeigen

4. **Linear = Ein Filter zur Zeit**
   - Kein Filter-Stacking
   - Jeder neue Filter startet von BASIS_MATRIX
   - Konsistente Ergebnisse garantiert

## Code-Beispiele

### Filter-Dialog öffnen
```python
from pdvm_extended_filter_dialog import show_pdvm_extended_filter_dialog

# Hole sichtbare Spalten für Dialog
visible_columns = [
    ('familienname_show', 'Familienname'),
    ('vorname_show', 'Vorname'),
    # ... weitere sichtbare Spalten
]

# Dialog öffnen (filtert aber auf ALLEN Spalten!)
result = show_pdvm_extended_filter_dialog(parent, view_guid, visible_columns)
```

### Filter anwenden
```python
# Im Dialog:
def _execute_filter(self):
    # 1. Sammle Filter-Kriterien
    active_filters = [
        {'column': 'familienname', 'value': 'Müller', 'include': True},
        {'column': 'vorname', 'value': 'Hans', 'include': False}
    ]
    
    # 2. Generiere search_string
    search_string = "familienname:Müller|vorname:NOT:Hans"
    
    # 3. Wende auf MatrixManager an
    matrix_manager.apply_filter(search_string, filter_type='einzeln')
    
    # 4. Refresh View (zeigt projizierte Spalten)
    parent_view.refresh_table_direct()
```

## Debugging

### Matrix-Größen prüfen
```python
logger.info(f"BASIS: {len(matrix_manager.basis_matrix)} Zeilen")
logger.info(f"FILTER: {len(matrix_manager.filtered_matrix)} Zeilen")
logger.info(f"SORT: {len(matrix_manager.sorted_matrix)} Zeilen")
logger.info(f"SPALTEN: {len(matrix_manager.columns)} Spalten")
```

### Filter-Ergebnis prüfen
```python
logger.info(f"Filter: '{search_string}'")
logger.info(f"Vorher: {len(basis_matrix)} Zeilen")
logger.info(f"Nachher: {len(filtered_matrix)} Zeilen")
logger.info(f"Reduzierung: {len(basis_matrix) - len(filtered_matrix)} Zeilen")
```

## Status

- ✅ BASIS_MATRIX → FILTER_MATRIX Pipeline
- ✅ FILTER_MATRIX → SORT_MATRIX Pipeline (Durchlauf, Sortierung TODO)
- ✅ Projektion auf VIEW
- ✅ Globaler Filter funktioniert
- ✅ Filter-Dialog erstellt (pdvm_extended_filter_dialog.py)
- ⏳ Komplexer Filter (Stufe 2)
- ⏳ Sort-Funktionalität implementieren
