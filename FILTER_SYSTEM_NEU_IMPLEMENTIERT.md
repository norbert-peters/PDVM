# FILTER-SYSTEM NEU IMPLEMENTIERT

## Zusammenfassung

Das Filter-System wurde komplett neu strukturiert gemäß den Anforderungen:

### 1. ✅ Menü vereinfacht
**Datei**: `pdvm_view_ui.py`

Zahnrad-Menü → Filter enthält jetzt nur noch:
- **Einfaches Filter** → Öffnet `pdvm_simple_filter_dialog.py`
- **Komplexes Filter** → Öffnet `pdvm_complex_filter_dialog.py`  
- **Filter zurücksetzen** → Setzt View auf BasisMatrix zurück

❌ Entfernt: "Parametrisches Filter" und "Erweitertes Filter"

---

### 2. ✅ Einfacher Filter-Dialog
**Datei**: `pdvm_simple_filter_dialog.py`

**Features**:
- Zeigt für jede **sichtbare Spalte** ein Suchfeld
- **+/- Toggle** pro Feld (Positiv/Negativ)
- Nur **"enthält"** Operator
- **UND-Verknüpfung** zwischen Feldern
- **Persistente Speicherung** in App-DB: `view_guid → 'einfach'`

**Struktur**:
```python
{
    'field_key': {
        'value': 'Suchtext',
        'mode': 'positive'/'negative'
    }
}
```

---

### 3. ✅ Komplexer Filter-Dialog
**Datei**: `pdvm_complex_filter_dialog.py`

**Features**:
- **4-Positionen Struktur** pro Bedingung:
  - Position 1: **FIRST/AND/OR** (Logische Verknüpfung)
  - Position 2: **IS/NOT** (Negation)
  - Position 3: **Operator** (enthält, beginnt mit, =, >, <, etc.)
  - Position 4: **Wert**
- **Mehrere Bedingungen** pro Feld möglich
- **UND-Verknüpfung** zwischen Feldern
- **Persistente Speicherung** in App-DB: `view_guid → 'komplex'`

**Struktur**:
```python
{
    'field_key': {
        'conditions': [
            {
                'value': 'Wert',
                'operator_type': 'enthält',
                'logic_operator': 'FIRST',
                'negation': 'IS'
            },
            {
                'value': 'Wert2',
                'operator_type': 'beginnt mit',
                'logic_operator': 'OR',
                'negation': 'NOT'
            }
        ]
    }
}
```

---

### 4. ✅ Suchzeile über View
**Datei**: `pdvm_view_ui.py`

**Features**:
- Suchzeile zwischen Header und Tabelle
- Sucht in **allen sichtbaren Spalten**
- **"enthält"** Operator mit **UND-Verknüpfung**
- **Nicht persistent** (User-Anforderung)
- **Real-time** bei Textänderung

**UI-Elemente**:
- `QLineEdit` mit Platzhalter-Text
- Löschen-Button (❌)
- Signal `search_requested` → Controller

---

### 5. ✅ Filter arbeiten auf BasisMatrix
**Datei**: `pdvm_view_controller.py`

**Pipeline-Architektur**:
```
BasisMatrix (ALLE Daten, ALLE Spalten)
    ↓ Filter anwenden
FilterMatrix
    ↓ Sortierung anwenden (falls vorhanden)
SortMatrix
    ↓ Projektion anwenden
ProjectionMatrix (NUR sichtbare Spalten)
    ↓
UI (Anzeige)
```

**Handler-Methoden**:
- `_handle_search(search_text)` → Schnellsuche
- `_handle_filter_request(filter_type, config)` → Einfach/Komplex
- `_apply_simple_filter(filter_data)` → Einfache Filter-Logik
- `_apply_complex_filter(filter_data)` → Komplexe Filter-Logik
- `_evaluate_condition(field_str, condition)` → Einzelne Bedingung

**Filter-Logik**:
- Filter arbeiten auf **BasisMatrix** → garantiert vollständige Datenbasis
- Nach Filter wird **Pipeline durchlaufen** (Sort → Projection)
- Sortierung bleibt nach Filter erhalten (`current_sort_column`)
- Array-Werte werden korrekt extrahiert (`WERT` Index)

---

### 6. ✅ Persistierung
**Implementierung**: In den Dialogen selbst

**App-DB Struktur**:
```python
# Einfacher Filter
gcs._app_db.set_value(view_guid, 'einfach', filter_data)

# Komplexer Filter  
gcs._app_db.set_value(view_guid, 'komplex', filter_data)

# Schnellsuche: NICHT persistent (wie gefordert)
```

**Laden beim Dialog-Öffnen**:
- `load_persistent_data()` in beiden Dialogen
- Setzt alle Felder mit gespeicherten Werten

**Speichern beim Anwenden**:
- `save_persistent_data()` bei "Filter anwenden"
- Nur aktuelle Eingaben werden gespeichert

---

## Signal-Fluss

### Schnellsuche (Suchzeile)
```
User tippt in Suchzeile
    ↓ textChanged Signal
pdvm_view_ui._on_search_changed()
    ↓ search_requested Signal
pdvm_view_controller._handle_search()
    ↓ Pipeline: BasisMatrix → Filter → Sort → Projection
pdvm_view_controller.refresh_ui_from_matrix()
```

### Einfaches Filter
```
User klickt "Einfaches Filter" im Menü
    ↓ _request_filter('simple')
pdvm_view_controller._handle_filter_request()
    ↓ Dialog öffnen
pdvm_simple_filter_dialog.show_simple_filter_dialog()
    ↓ Lädt persistent
    ↓ User füllt aus
    ↓ "Filter anwenden"
    ↓ Speichert persistent
    ↓ Gibt filter_data zurück
pdvm_view_controller._apply_simple_filter()
    ↓ Pipeline: BasisMatrix → Filter → Sort → Projection
pdvm_view_controller.refresh_ui_from_matrix()
```

### Komplexes Filter
```
User klickt "Komplexes Filter" im Menü
    ↓ _request_filter('complex')
pdvm_view_controller._handle_filter_request()
    ↓ Dialog öffnen
pdvm_complex_filter_dialog.show_complex_filter_dialog()
    ↓ Lädt persistent
    ↓ User erstellt Bedingungen (4-Positionen)
    ↓ "Filter anwenden"
    ↓ Speichert persistent
    ↓ Gibt filter_data zurück
pdvm_view_controller._apply_complex_filter()
    ↓ Pipeline: BasisMatrix → Filter → Sort → Projection
pdvm_view_controller.refresh_ui_from_matrix()
```

---

## Code-Änderungen

### pdvm_view_ui.py
```python
# ÄNDERUNGEN:
1. Menü vereinfacht (Zeile ~628)
   - "Einfaches Filter"
   - "Komplexes Filter"
   - Kein Parametrisches Filter mehr

2. Suchzeile hinzugefügt (Zeile ~98-104)
   - _create_search_bar() Methode
   - Signal search_requested

3. Import erweitert
   - QLineEdit hinzugefügt

4. Handler-Methoden (Zeile ~704)
   - _on_search_changed()
   - _clear_search()
```

### pdvm_view_controller.py
```python
# ÄNDERUNGEN:
1. Instanzvariablen (Zeile ~96-97)
   - self.current_sort_column = None
   - self.current_sort_reverse = False

2. Signal-Verbindungen (Zeile ~453-455)
   - search_requested.connect()
   - filter_requested.connect()
   - sort_requested.connect()

3. Handler-Methoden (Zeile ~904+)
   - _handle_search()
   - _handle_filter_request()
   - _apply_simple_filter()
   - _apply_complex_filter()
   - _evaluate_condition()
   - _handle_sort_request()
```

### Neue Dateien
- `pdvm_simple_filter_dialog.py` (320 Zeilen)
- `pdvm_complex_filter_dialog.py` (480 Zeilen)

---

## Testen

### Einfacher Filter
1. Anwendung starten
2. View öffnen
3. Zahnrad → Filter → **Einfaches Filter**
4. Werte eingeben, +/- testen
5. "Filter anwenden"
6. Dialog schließen und erneut öffnen → Persistierung prüfen

### Komplexes Filter
1. Zahnrad → Filter → **Komplexes Filter**
2. Bedingungen hinzufügen (➕ Button)
3. 4 Positionen testen: FIRST/AND/OR, IS/NOT, Operator, Wert
4. "Filter anwenden"
5. Dialog schließen und erneut öffnen → Persistierung prüfen

### Schnellsuche
1. In Suchzeile tippen
2. View filtert live
3. ❌ Button → Filter entfernen
4. **NICHT persistent** → Nach Neustart leer

### Filter zurücksetzen
1. Filter anwenden (einfach/komplex)
2. Zahnrad → Filter → **Filter zurücksetzen**
3. View zeigt wieder alle Daten (BasisMatrix)

---

## Kritische Punkte

### ✅ Gelöst
- **BasisMatrix**: Filter arbeiten IMMER auf vollständiger Datenbasis
- **Pipeline**: Korrekte Reihenfolge (Filter → Sort → Projection)
- **Array-Werte**: WERT-Index wird korrekt extrahiert
- **Persistierung**: Getrennt für einfach/komplex, nicht für Schnellsuche
- **UND-Verknüpfung**: Zwischen Feldern (alle müssen passen)
- **OR/AND**: Innerhalb Feld für komplexen Filter

### ⚠️ Zu beachten
- **Sortierung**: Wird nach Filter beibehalten
- **Expert Mode**: Verwendet korrekte Projektion (standard/expert)
- **Gesamtfilter**: Wird NICHT persistent gespeichert (wie gefordert)

---

## Anforderungen-Checkliste

- [x] 1. Menü vereinfacht (2 Filter-Optionen)
- [x] 2. Dialoge getrennt (einfach/komplex)
- [x] 3. Suchzeile über View (enthält + UND)
- [x] 4. Filter auf BasisMatrix → Pipeline
- [x] 5. Persistierung (einfach/komplex, nicht Gesamtfilter)

---

## Status

✅ **ALLE ANFORDERUNGEN ERFÜLLT**

Die Implementierung ist vollständig und bereit zum Testen.
