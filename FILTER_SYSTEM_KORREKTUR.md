# FILTER-SYSTEM KORREKTUR

## Problem
Die Filter wurden in der View nicht sichtbar, weil:
1. **Zwei verschiedene Pipeline-Systeme** verwendet wurden:
   - `matrix_manager.matrix_pipeline` (wird beim Initialize verwendet)
   - `get_matrix_pipeline()` (wurde in neuen Filter-Handlern verwendet)
2. **Schnellsuche ohne Button** - lief automatisch bei jedem Tastendruck

## Lösung

### 1. ✅ Einheitliches Pipeline-System
**Alle Filter verwenden jetzt `self.matrix_manager.matrix_pipeline`**

```python
# VORHER (FALSCH):
pipeline = get_matrix_pipeline(self.view_guid)  # Separates System!

# NACHHER (RICHTIG):
pipeline = self.matrix_manager.matrix_pipeline  # Gleiche Pipeline!
```

**Vorteil**: 
- `matrix_manager` und Filter arbeiten mit der GLEICHEN Pipeline-Instanz
- Änderungen in einem System sind sofort im anderen sichtbar
- `refresh_ui_from_matrix()` liest die korrekte FilterMatrix

---

### 2. ✅ Such-Button hinzugefügt (Lupe 🔍)
**Schnellsuche wird jetzt über Button ausgelöst, nicht automatisch**

**UI-Änderungen** (`pdvm_view_ui.py`):
```python
# Suchzeile-Layout:
[🔍 Suchen:] [Suchfeld_______________] [🔍 Button] [❌]
                                       ↑ NEU!
```

**Funktionsweise**:
- Suchtext wird gespeichert (kein automatischer Filter)
- Button-Click oder Enter-Taste → `controller.execute_search()`
- Linear und einfach wie andere Filter

---

### 3. ✅ Filter auf BasisMatrix
**Pipeline-Ablauf ist jetzt korrekt**:

```
BasisMatrix (ALLE Zeilen, ALLE Spalten)
    ↓ apply_filter(filter_func)
FilterMatrix (NUR gefilterte Zeilen, ALLE Spalten)  ← WICHTIG!
    ↓ apply_sort(column, reverse)
SortMatrix (Gefilterte + sortierte Zeilen, ALLE Spalten)
    ↓ project(visible_columns)
ProjectionMatrix (Nur sichtbare Spalten)
    ↓
UI (Anzeige)
```

**Kritisch**: FilterMatrix enthält NUR noch die gefilterten Zeilen (nicht mehr alle!)

---

## Code-Änderungen

### pdvm_view_controller.py

#### Schnellsuche:
```python
def _handle_search(self, search_text):
    """Speichert Suchtext - wird über Button ausgeführt"""
    self.pending_search_text = search_text

def execute_search(self):
    """Führt Schnellsuche aus (via Button)"""
    pipeline = self.matrix_manager.matrix_pipeline  # Richtige Pipeline!
    
    # Filter-Funktion
    def search_filter(row_data):
        search_lower = search_text.lower()
        for col_key in visible_columns:
            if col_key in row_data:
                value_str = str(row_data[col_key]).lower()
                if search_lower in value_str:
                    return True  # Gefunden!
        return False  # Nicht gefunden
    
    # Pipeline durchlaufen
    pipeline.apply_filter(search_filter)
    pipeline.apply_sort(self.current_sort_column, self.current_sort_reverse)
    pipeline.project(visible_columns)
    
    # UI aktualisieren
    self.refresh_ui_from_matrix()
```

#### Einfacher Filter:
```python
def _apply_simple_filter(self, filter_data):
    pipeline = self.matrix_manager.matrix_pipeline  # Richtige Pipeline!
    
    def simple_filter(row_data):
        """UND-Verknüpfung zwischen Feldern, +/- pro Feld"""
        for field_key, field_filter in filter_data.items():
            value_to_search = field_filter['value'].lower()
            is_positive = (field_filter['mode'] == 'positive')
            
            field_str = str(row_data.get(field_key, '')).lower()
            contains = value_to_search in field_str
            
            if is_positive and not contains:
                return False  # Positiv: Muss enthalten
            if not is_positive and contains:
                return False  # Negativ: Darf nicht enthalten
        
        return True
    
    # Pipeline durchlaufen
    pipeline.apply_filter(simple_filter)
    pipeline.apply_sort(...)
    pipeline.project(...)
    self.refresh_ui_from_matrix()
```

#### Komplexer Filter:
```python
def _apply_complex_filter(self, filter_data):
    pipeline = self.matrix_manager.matrix_pipeline  # Richtige Pipeline!
    
    def complex_filter(row_data):
        """4-Positionen pro Bedingung, UND zwischen Feldern"""
        for field_key, field_filter in filter_data.items():
            conditions = [SearchCondition.from_dict(c) for c in field_filter['conditions']]
            
            field_result = None
            for cond in conditions:
                match = self._evaluate_condition(field_str, cond)
                
                # Verknüpfung: FIRST/AND/OR
                if cond.logic_operator == 'FIRST':
                    field_result = match
                elif cond.logic_operator == 'AND':
                    field_result = field_result and match
                elif cond.logic_operator == 'OR':
                    field_result = field_result or match
            
            if not field_result:
                return False  # Feld passt nicht
        
        return True  # Alle Felder passen
    
    # Pipeline durchlaufen
    pipeline.apply_filter(complex_filter)
    pipeline.apply_sort(...)
    pipeline.project(...)
    self.refresh_ui_from_matrix()
```

---

### pdvm_view_ui.py

#### Such-Button:
```python
def _create_search_bar(self):
    """Suchzeile mit Button erstellen"""
    # ... Suchfeld ...
    
    # Suchen-Button (NEU!)
    search_button = QPushButton("🔍")
    search_button.clicked.connect(self._execute_search)
    search_layout.addWidget(search_button)
    
    # Enter-Taste führt auch Suche aus
    self.search_input.returnPressed.connect(self._execute_search)

def _execute_search(self):
    """Führt Suche aus"""
    self.controller.execute_search()

def _clear_search(self):
    """Löscht Suche und setzt Filter zurück"""
    self.search_input.clear()
    self.controller.refresh()  # Zurück zur BasisMatrix
```

---

## Testen

### Schnellsuche:
1. In Suchzeile tippen (z.B. "Lau")
2. **🔍 Button klicken** oder **Enter drücken**
3. View zeigt nur gefilterte Zeilen
4. ❌ Button → Zurück zur BasisMatrix

### Einfaches Filter:
1. Zahnrad → Filter → Einfaches Filter
2. Werte eingeben, +/- Buttons testen
3. "Filter anwenden"
4. View zeigt gefilterte Zeilen
5. Log prüfen: `FilterMatrix erstellt: X Zeilen`

### Komplexes Filter:
1. Zahnrad → Filter → Komplexes Filter
2. Bedingungen hinzufügen (4-Positionen)
3. "Filter anwenden"
4. View zeigt gefilterte Zeilen
5. Log prüfen: `FilterMatrix erstellt: X Zeilen`

---

## Debug-Tipps

### Log-Ausgaben prüfen:
```
🔍 Führe Schnellsuche aus: 'Lau'
🔨 === BAUE FILTERMATRIX aus BasisMatrix ===
🔍 Filter angewendet: 100 → 3 Zeilen    ← Wichtig!
✅ FilterMatrix erstellt: 3 Zeilen       ← Nur gefilterte!
✅ Schnellsuche abgeschlossen: 3 Zeilen
```

### FilterMatrix Zeilen-Anzahl:
- **Vorher (Bug)**: FilterMatrix hatte ALLE Zeilen (filter_func wurde ignoriert)
- **Nachher (Fix)**: FilterMatrix hat NUR gefilterte Zeilen

### Pipeline-Status loggen:
```python
pipeline.log_pipeline_status()
```

Zeigt:
```
📊 === PIPELINE STATUS ===
  ✅ BasisMatrix: 100 Zeilen
  ✅ FilterMatrix: 3 Zeilen    ← Nur gefilterte!
  ✅ SortMatrix: 3 Zeilen
  ✅ Projektion: 3 Zeilen, 8 Spalten
```

---

## Kritische Punkte

### ✅ Gelöst:
- **Einheitliches Pipeline-System**: Alle verwenden `matrix_manager.matrix_pipeline`
- **Filter funktionieren**: FilterMatrix enthält nur gefilterte Zeilen
- **Such-Button**: Linear und einfach wie andere Filter
- **UND-Verknüpfung**: Zwischen Feldern korrekt implementiert
- **Array-Werte**: Werden als String konvertiert und durchsucht

### ⚠️ Zu beachten:
- **Sortierung**: Bleibt nach Filter erhalten (`current_sort_column`)
- **Refresh**: Setzt Filter zurück, zeigt BasisMatrix
- **Persistierung**: Einfach/Komplex persistent, Schnellsuche NICHT

---

## Status

✅ **FILTER-SYSTEM FUNKTIONIERT JETZT**

Die FilterMatrix enthält jetzt nur noch die gefilterten Zeilen und die View zeigt diese korrekt an!
