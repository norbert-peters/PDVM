# FILTER-SYSTEM VEREINFACHT

## Problem
Die Implementierung war zu kompliziert - mehrere Pipeline-Zugriffe, verschachtelte Logik.

## Lösung: EINFACHE ARCHITEKTUR

### Ablauf (User-Vorgabe):

```
1. Filter-Dialog erstellt search_string / filter_func
                ↓
2. Matrix Manager: apply_search_filter(search_string, visible_columns)
                ↓
        BasisMatrix (alle Zeilen)
                ↓ apply_filter(filter_func)
        FilterMatrix (NUR gefilterte Zeilen)
                ↓ apply_sort()
        SortMatrix (gefiltert + sortiert)
                ↓ project()
        ProjectionMatrix (nur sichtbare Spalten)
                ↓
3. UI zeigt gefilterte Zeilen automatisch
```

**WICHTIG**: Die Pipeline läuft automatisch durch - FilterMatrix enthält nur gefilterte Zeilen!

---

## Code-Änderungen

### pdvm_view_daten_manager.py

**NEU: Einfache Such-Methode**:
```python
def apply_search_filter(self, search_string: str, visible_columns: list):
    """
    EINFACHE SUCHE: Wendet Filter auf BasisMatrix an
    
    Args:
        search_string: Suchtext (aus Dialog)
        visible_columns: Sichtbare Spalten für Suche
    
    Returns:
        True wenn erfolgreich
    """
    if not search_string:
        # Leere Suche = Pipeline ohne Filter
        self.matrix_pipeline.rebuild_from_basis()
        return True
    
    # Filter-Funktion erstellen
    search_lower = search_string.lower()
    
    def search_filter(row_data):
        """Sucht in sichtbaren Spalten mit 'enthält'"""
        for col_key in visible_columns:
            if col_key in row_data:
                value_str = str(row_data[col_key]).lower() or ''
                if search_lower in value_str:
                    return True
        return False
    
    # Filter anwenden → FilterMatrix
    self.matrix_pipeline.apply_filter(search_filter)
    
    # Rest der Pipeline durchlaufen
    self.matrix_pipeline.apply_sort(
        self.matrix_pipeline.sort_column,
        self.matrix_pipeline.sort_reverse
    )
    self.matrix_pipeline.project(self.matrix_pipeline.visible_columns)
    
    return True
```

---

### pdvm_view_controller.py

**Schnellsuche - VEREINFACHT**:
```python
def execute_search(self):
    """EINFACH: Ruft Matrix Manager mit search_string auf"""
    search_text = getattr(self, 'pending_search_text', '')
    
    # Sichtbare Spalten
    visible_columns = self.get_projection_table(
        'table_expert' if self.gcs.expert_mode else 'table_standard'
    )
    
    # Matrix Manager macht die Arbeit!
    self.matrix_manager.apply_search_filter(search_text, visible_columns)
    
    # UI aktualisieren
    self.refresh_ui_from_matrix()
```

**Einfacher Filter - VEREINFACHT**:
```python
def _apply_simple_filter(self, filter_data):
    """EINFACH: Erstellt Filter-Funktion und ruft Matrix Manager auf"""
    
    # Filter-Funktion
    def simple_filter(row_data):
        for field_key, field_filter in filter_data.items():
            value_to_search = field_filter['value'].lower()
            is_positive = (field_filter['mode'] == 'positive')
            
            field_str = str(row_data.get(field_key, '')).lower()
            contains = value_to_search in field_str
            
            if is_positive and not contains:
                return False
            if not is_positive and contains:
                return False
        return True
    
    # Matrix Manager: Filter anwenden
    self.matrix_manager.matrix_pipeline.apply_filter(simple_filter)
    self.matrix_manager.matrix_pipeline.apply_sort(...)
    self.matrix_manager.matrix_pipeline.project(visible_columns)
    
    # UI aktualisieren
    self.refresh_ui_from_matrix()
```

**Komplexer Filter - VEREINFACHT**:
```python
def _apply_complex_filter(self, filter_data):
    """EINFACH: Erstellt Filter-Funktion und ruft Matrix Manager auf"""
    
    # Filter-Funktion (4-Positionen Logik)
    def complex_filter(row_data):
        for field_key, field_filter in filter_data.items():
            conditions = [SearchCondition.from_dict(c) 
                         for c in field_filter['conditions']]
            
            field_result = None
            for cond in conditions:
                match = self._evaluate_condition(field_str, cond)
                
                if cond.logic_operator == 'FIRST':
                    field_result = match
                elif cond.logic_operator == 'AND':
                    field_result = field_result and match
                elif cond.logic_operator == 'OR':
                    field_result = field_result or match
            
            if not field_result:
                return False
        return True
    
    # Matrix Manager: Filter anwenden
    self.matrix_manager.matrix_pipeline.apply_filter(complex_filter)
    self.matrix_manager.matrix_pipeline.apply_sort(...)
    self.matrix_manager.matrix_pipeline.project(visible_columns)
    
    # UI aktualisieren
    self.refresh_ui_from_matrix()
```

---

## Vorteile der Vereinfachung

### ✅ Keine doppelten Pipeline-Instanzen mehr
- Nur EINE Pipeline: `matrix_manager.matrix_pipeline`
- Kein `get_matrix_pipeline()` im Controller

### ✅ Klare Verantwortlichkeiten
- **Matrix Manager**: Führt Filter auf BasisMatrix aus
- **Controller**: Erstellt Filter-Funktionen, ruft Manager auf
- **Pipeline**: Läuft automatisch durch (Filter → Sort → Projection)

### ✅ Linear und einfach
```
Dialog → search_string → Matrix Manager → Pipeline → UI
```

Keine verschachtelten Aufrufe, keine Komplikationen!

---

## Testen

1. **Schnellsuche**: Suchtext eingeben → 🔍 Button → View zeigt gefilterte Zeilen
2. **Einfacher Filter**: Dialog → Felder füllen → Anwenden → View zeigt gefilterte Zeilen
3. **Komplexer Filter**: Dialog → Bedingungen → Anwenden → View zeigt gefilterte Zeilen

**Log-Ausgaben prüfen**:
```
🔍 Matrix Manager: Wende Filter an: 'Lau'
🔨 === BAUE FILTERMATRIX aus BasisMatrix ===
🔍 Filter angewendet: 100 → 3 Zeilen
✅ Filter angewendet: 3 Zeilen
```

---

## Status

✅ **ARCHITEKTUR VEREINFACHT** - So wie User es wollte!

Linear, einfach, keine Komplikationen. Matrix Manager macht die Arbeit, Controller ruft nur auf.
