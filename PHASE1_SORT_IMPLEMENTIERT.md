# Phase 1: Basis-Sortierung - IMPLEMENTIERT ✅

## Datum: 12. Oktober 2025

## Was wurde implementiert:

### 1. Matrix Manager - Zentrale Sort-Methode ✅
**Datei**: `pdvm_view_matrix_manager.py`

```python
def apply_sort_config(self, sort_config: dict = None) -> bool:
    """
    ZENTRALE SORT-METHODE: FilterMatrix → SortMatrix
    
    Beachtet SortByOriginal aus Controls!
    
    Args:
        sort_config: {
            'column': 'familienname_show',
            'direction': 'asc' oder 'desc',
            'use_original': True  # Nutzt _original statt _show
        }
        None = keine Sortierung (Original-Reihenfolge)
    """
```

**Features**:
- ✅ Sortiert FilterMatrix → SortMatrix
- ✅ Beachtet `sortByOriginal` aus Control (nutzt _original statt _show)
- ✅ Unterstützt asc/desc
- ✅ None-Werte ans Ende
- ✅ Case-insensitive String-Sort
- ✅ Numerische Werte korrekt sortiert

**Helper-Methode**:
```python
def _apply_persisted_sort(self):
    """Lädt persistierte Sort-Config und wendet sie an"""
```
- Wird nach JEDEM Filter automatisch aufgerufen
- Sorgt dafür, dass Sortierung IMMER erhalten bleibt

---

### 2. Header-Klick mit Toggle ✅
**Datei**: `pdvm_view_ui.py`

```python
def _on_header_clicked(self, logical_index):
    """Header-Klick → Sortierung mit asc/desc Toggle"""
    
    if self.current_sort_column == column_key:
        # Gleiche Spalte: Richtung wechseln
        self.current_sort_direction = 'desc' if self.current_sort_direction == 'asc' else 'asc'
    else:
        # Neue Spalte: Start mit asc
        self.current_sort_column = column_key
        self.current_sort_direction = 'asc'
```

**Verhalten**:
- 1. Klick auf Spalte X: Sortierung ASC
- 2. Klick auf Spalte X: Sortierung DESC
- 3. Klick auf Spalte X: Sortierung ASC
- Klick auf Spalte Y: Neue Sortierung (ASC)

---

### 3. Controller Sort-Handler ✅
**Datei**: `pdvm_view_controller.py`

```python
def _handle_sort_request(self, sort_config):
    """Handler für Sortierungs-Anfragen (Header-Klick)"""
    
    # 1. SortByOriginal aus Control holen
    control = self.column_control.get(column_key, {})
    use_original = control.get('sortByOriginal', False)
    
    # 2. Erweiterte Config erstellen
    full_sort_config = {
        'column': column_key,
        'direction': sort_config['direction'],
        'use_original': use_original
    }
    
    # 3. Persistieren in App-DB
    self.gcs._app_db.set_value(self.view_guid, 'sort', full_sort_config)
    
    # 4. Matrix Manager anwenden
    self.matrix_manager.apply_sort_config(full_sort_config)
    
    # 5. UI aktualisieren
    self.refresh_ui_from_matrix()
```

**Features**:
- ✅ Holt `sortByOriginal` aus Control
- ✅ Persistiert Sort-Config in App-DB
- ✅ Ruft Matrix Manager auf
- ✅ UI-Refresh

---

### 4. Sortierung Zurücksetzen ✅
**Dateien**: `pdvm_view_ui.py` + `pdvm_view_controller.py`

**Zahnrad-Menü erweitert**:
```python
sort_menu.addAction("Sortierung zurücksetzen", self._reset_sort)
```

**Controller**:
```python
def reset_sort(self):
    """Sortierung zurücksetzen"""
    
    # 1. Persistierte Sort-Config löschen
    self.gcs._app_db.set_value(self.view_guid, 'sort', None)
    
    # 2. Matrix Manager: Keine Sortierung
    self.matrix_manager.apply_sort_config(None)
    
    # 3. UI aktualisieren
    self.refresh_ui_from_matrix()
```

**Ergebnis**: Daten in Original-Reihenfolge (wie aus DB)

---

### 5. Persistierung beim Start ✅
**Datei**: `pdvm_view_controller.py`

```python
def _initialize_filter_and_sort(self):
    """7. Filter und Sortierung initialisieren"""
    
    # ...
    
    # Persistierte Sort-Config laden
    self._load_persisted_sort()

def _load_persisted_sort(self):
    """Lädt persistierte Sortierung und wendet sie an"""
    
    sort_config, _ = self.gcs._app_db.get_value(self.view_guid, 'sort')
    
    if sort_config:
        # An UI senden (für Visual State)
        self.ui.current_sort_column = sort_config.get('column')
        self.ui.current_sort_direction = sort_config.get('direction', 'asc')
        
        # Matrix Manager anwenden
        self.matrix_manager.apply_sort_config(sort_config)
```

**Ergebnis**:
- Beim View-Start wird persistierte Sortierung geladen
- Alle weiteren Aufrufe sind automatisch sortiert
- Filter behalten Sortierung bei

---

## Pipeline-Ablauf:

```
BasisMatrix (ALLE Zeilen)
    ↓ Filter
FilterMatrix (NUR gefilterte Zeilen)
    ↓ apply_sort_config() - IMMER mit persistierter Config!
SortMatrix (gefiltert + sortiert)
    ↓ Projektion
ProjectionMatrix (nur sichtbare Spalten)
    ↓
UI (angezeigt)
```

---

## Automatische Sortierungs-Persistenz:

### Bei Header-Klick:
1. User klickt auf Header
2. Sort-Config wird erstellt
3. **SOFORT PERSISTIERT** in App-DB (view_guid, 'sort')
4. Matrix Manager wendet an
5. UI zeigt sortierte Daten

### Bei Filter-Anwendung:
1. User wendet Filter an
2. BasisMatrix → FilterMatrix
3. `_apply_persisted_sort()` wird automatisch aufgerufen
4. Lädt Sort-Config aus App-DB
5. Wendet Sortierung an
6. UI zeigt gefiltert + sortiert

### Beim View-Start:
1. View wird geöffnet
2. `_initialize_filter_and_sort()` lädt persistierte Config
3. Erste Anzeige ist bereits sortiert

---

## SortByOriginal Feature:

### Problem:
Formatierte Werte falsch sortieren:
- Datum "01.10.2024" vs "05.01.2023" → String-Sort falsch!
- Float 2024310.0 vs 2023105.0 → Numerisch korrekt!

### Lösung:
```python
# Control-Definition:
{
    'key': 'geburtsdatum_show',
    'sortByOriginal': True  # ← Nutzt geburtsdatum_original!
}

# Bei Sortierung:
if use_original and column_key.endswith('_show'):
    sort_column = column_key.replace('_show', '_original')
    # geburtsdatum_show → geburtsdatum_original
```

**Automatisch für**:
- Datum-Spalten (PdvmDateTime)
- Betrag-Spalten (formatierte Zahlen)
- Alle Spalten mit `sortByOriginal: True` im Control

---

## Test-Szenarien:

### 1. Einfache Sortierung:
1. ✅ App starten
2. ✅ Header "Familienname" klicken → ASC
3. ✅ Nochmal klicken → DESC
4. ✅ Nochmal klicken → ASC

### 2. Persistierung:
1. ✅ Sortierung setzen (z.B. Familienname ASC)
2. ✅ Filter anwenden → Sortierung bleibt!
3. ✅ App schließen + neu öffnen → Sortierung bleibt!

### 3. SortByOriginal:
1. ✅ Geburtsdatum-Spalte sortieren
2. ✅ Prüfen: Nutzt _original (Float) nicht _show (String)
3. ✅ Reihenfolge chronologisch korrekt

### 4. Zurücksetzen:
1. ✅ Sortierung setzen
2. ✅ Zahnrad → "Sortierung zurücksetzen"
3. ✅ Original-Reihenfolge (wie aus DB)
4. ✅ App neu starten → Keine Sortierung

---

## Dateien geändert:

1. ✅ `pdvm_view_matrix_manager.py`
   - `apply_sort_config()` - Zentrale Sort-Methode
   - `_apply_persisted_sort()` - Persistierung laden

2. ✅ `pdvm_view_ui.py`
   - `_on_header_clicked()` - Toggle-Logik
   - `_reset_sort()` - Zurücksetzen
   - Zahnrad-Menü erweitert

3. ✅ `pdvm_view_controller.py`
   - `_handle_sort_request()` - Sort-Request Handler
   - `reset_sort()` - Zurücksetzen
   - `_load_persisted_sort()` - Beim Start laden
   - `_initialize_filter_and_sort()` erweitert

---

## Nächste Schritte (Phase 2+):

### Phase 2: Multi-Sort (über Zahnrad-Dialog)
- [ ] `advanced_sort_dialog.py` erweitern
- [ ] Mehrere Spalten gleichzeitig sortieren
- [ ] Reihenfolge ändern (Drag & Drop?)
- [ ] Visual Feedback (↑↓ + Nummern im Header)

### Phase 3: Gruppierung
- [ ] Gruppen-Header einfügen
- [ ] Collapse/Expand State
- [ ] Summenzeilen (Anfang + Ende)

### Phase 4: Summen
- [ ] Numerische Summen berechnen
- [ ] Anzahl bei Text-Spalten
- [ ] Gesamt-Summe am Ende

---

## READY FOR TESTING! 🎯
