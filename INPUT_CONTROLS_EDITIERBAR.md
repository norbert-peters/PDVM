# ✅ INPUT-CONTROLS V2 - EDITIERBAR

**Datum**: 22.10.2025  
**Status**: ✅ Implementiert

---

## 🎯 IMPLEMENTIERTE FEATURES

### 1. ✅ QLineEdit statt QLabel
- Input-Controls verwenden jetzt `QLineEdit` für Bearbeitung
- Werte können direkt im Feld geändert werden
- Automatisches Dirty-Tracking bei Änderungen

### 2. ✅ Read-Only bei fehlender Instanz
- Wenn `db_instance` ist `None` → `setReadOnly(True)`
- Graues Styling für schreibgeschützte Felder
- Tooltip zeigt "🔒 SCHREIBGESCHÜTZT (keine Instanz)"

### 3. ✅ Visuelles Feedback
- **Normal** (editierbar): Weißer Hintergrund, blauer Rahmen
- **Geändert** (dirty): Gelber Hintergrund (`#fff9e6`), oranger Rahmen (`#f39c12`)
- **Read-Only**: Grauer Hintergrund (`#ecf0f1`), grauer Rahmen, grauer Text

### 4. ✅ Automatisches Dirty-Tracking
- `textChanged` Signal verbunden mit `_on_value_changed()`
- `is_dirty` wird automatisch gesetzt
- `current_value` wird automatisch aktualisiert

---

## 📋 ARCHITEKTUR

### Control-Zustand

```python
# DATEN
self.wert = None              # Ursprünglicher Wert aus DB
self.abdatum_wert = None      # Ursprüngliches Abdatum aus DB
self.original_value = None    # Original für Dirty-Check
self.current_value = None     # Aktueller Wert (aus QLineEdit)
self.is_dirty = False         # Hat sich geändert?

# UI
self.edit_widget = QLineEdit()  # Editierbares Feld
```

### Ablauf beim Editieren

```
User tippt im QLineEdit
  ↓
textChanged Signal
  ↓
_on_value_changed(text)
  ↓
current_value = text
is_dirty = (current_value != original_value)
  ↓
Styling aktualisiert (gelb wenn dirty)
```

### Ablauf beim Speichern

```
Manager: save_all()
  ↓
FOR each dirty Control:
  control.save(neues_abdatum)
    ↓
    db_instance.set_value(gruppe, feld, current_value, neues_abdatum)
    ↓
    original_value = current_value
    is_dirty = False
  ↓
FOR each instance:
  instance.save_all_values()
  ↓
Manager: refresh_all()
  ↓
FOR each Control:
  control.refresh()
    ↓
    _load_value_from_db()  # Neu laden
    _update_ui()           # QLineEdit aktualisieren
    is_dirty = False
    Styling zurücksetzen (weiß)
```

---

## 🎨 STYLING-DEFINITIONEN

### Editierbar (Normal)
```css
QLineEdit {
    background-color: white;
    border: 1px solid #3498db;      /* Blau */
    border-radius: 3px;
    padding: 5px;
    color: #2c3e50;                  /* Dunkelgrau */
}
QLineEdit:focus {
    border: 2px solid #2980b9;      /* Dunkelblau */
}
```

### Editierbar (Geändert/Dirty)
```css
QLineEdit {
    background-color: #fff9e6;      /* Hellgelb */
    border: 2px solid #f39c12;      /* Orange */
    border-radius: 3px;
    padding: 5px;
    color: #2c3e50;
}
```

### Read-Only (Schreibgeschützt)
```css
QLineEdit {
    background-color: #ecf0f1;      /* Hellgrau */
    border: 1px solid #bdc3c7;      /* Grau */
    border-radius: 3px;
    padding: 5px;
    color: #7f8c8d;                  /* Grau */
}
```

---

## 🔧 CODE-ÄNDERUNGEN

### pdvm_input_control_v2.py

#### 1. _create_ui() - QLineEdit statt QLabel

**VORHER**:
```python
self.value_label = QLabel()
self.value_label.setStyleSheet("...")
layout.addWidget(self.value_label, 1)
```

**NACHHER**:
```python
self.edit_widget = QLineEdit()

# Read-Only wenn keine Instanz
if not self.db_instance:
    self.edit_widget.setReadOnly(True)
    self.edit_widget.setStyleSheet("...")  # Grau
else:
    self.edit_widget.setReadOnly(False)
    self.edit_widget.setStyleSheet("...")  # Weiß/Blau

# Signal verbinden
self.edit_widget.textChanged.connect(self._on_value_changed)

layout.addWidget(self.edit_widget, 1)
```

#### 2. _on_value_changed() - NEU!

```python
def _on_value_changed(self, text):
    """Callback: Wert wurde geändert"""
    self.current_value = text
    self.is_dirty = (self.current_value != self.original_value)
    
    # Visuelles Feedback
    if self.is_dirty and not self.edit_widget.isReadOnly():
        # Gelbes Styling (dirty)
        self.edit_widget.setStyleSheet("...")
    elif not self.edit_widget.isReadOnly():
        # Normales Styling
        self.edit_widget.setStyleSheet("...")
```

#### 3. _update_ui() - QLineEdit aktualisieren

**VORHER**:
```python
self.value_label.setText(display_value)
self.value_label.setToolTip(tooltip)
```

**NACHHER**:
```python
# Wert setzen (ohne Signal auszulösen!)
self.edit_widget.blockSignals(True)
self.edit_widget.setText(display_value)
self.edit_widget.blockSignals(False)

# Tooltip setzen
self.edit_widget.setToolTip(tooltip)
```

**WICHTIG**: `blockSignals(True)` verhindert, dass `textChanged` beim Initialisieren ausgelöst wird!

#### 4. refresh() - Styling zurücksetzen

```python
def refresh(self):
    # ... [laden + UI aktualisieren]
    
    # Styling zurücksetzen (wenn editierbar)
    if self.edit_widget and not self.edit_widget.isReadOnly():
        self.edit_widget.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #3498db;
                ...
            }
        """)
```

---

## 📊 BEISPIEL-ABLAUF

### Szenario: Familienname ändern

**1. Initial-Zustand** (nach Render):
```
QLineEdit: "Mustermann"
Styling: Weiß/Blau (normal)
is_dirty: False
original_value: "Mustermann"
current_value: "Mustermann"
```

**2. User ändert auf "Musterfrau"**:
```
textChanged Signal → _on_value_changed("Musterfrau")
  ↓
current_value: "Musterfrau"
is_dirty: True (current_value != original_value)
  ↓
Styling: Gelb/Orange (dirty)
```

**3. Manager: save_all()**:
```
Control: save(neues_abdatum)
  ↓
db_instance.set_value("PERSDATEN", "FAMILIENNAME", "Musterfrau", 2025294.123)
  ↓
original_value: "Musterfrau"
is_dirty: False
  ↓
Instance: save_all_values()  # Commit zu DB
```

**4. Manager: refresh_all()**:
```
Control: refresh()
  ↓
_load_value_from_db()  # Lädt "Musterfrau" + neues Abdatum
  ↓
_update_ui()  # QLineEdit: "Musterfrau"
  ↓
is_dirty: False
Styling: Weiß/Blau (zurückgesetzt)
```

---

## 🔒 READ-ONLY LOGIK

### Wann ist ein Control Read-Only?

```python
if not self.db_instance:
    # Keine Instanz vorhanden (z.B. verschachteltes Feld ohne GUID)
    self.edit_widget.setReadOnly(True)
```

### Beispiel: Verschachteltes Feld ohne GUID

**Field-Key**: `FINANZDATEN_FINANZDATEN_KONTOINHABER`  
**source_path**: `"root_PERSDATEN"`

**Wenn in ROOT unter** `PERSDATEN.FINANZDATEN-FINANZDATEN` **keine GUID**:
- Instanz-Pool enthält keine `FINANZDATEN_{guid}` Instanz
- Control wird mit `db_instance=None` erstellt
- QLineEdit wird auf `setReadOnly(True)` gesetzt
- Graues Styling
- Tooltip zeigt "🔒 SCHREIBGESCHÜTZT (keine Instanz)"

---

## ✅ VORTEILE DER V2-IMPLEMENTATION

1. **Einfach editierbar**: User kann direkt im Feld tippen
2. **Visuelles Feedback**: Sofort sichtbar wenn geändert (gelb)
3. **Read-Only bei fehlender Instanz**: Verhindert Fehler
4. **Automatisches Dirty-Tracking**: Kein manuelles Flag-Setzen
5. **Konsistentes Styling**: Klare visuelle Unterscheidung

---

## 🧪 NÄCHSTE SCHRITTE

1. ✅ Testen mit echten Daten
2. ⏳ Dropdown-Support (für Felder mit `type: "dropdown"`)
3. ⏳ Validierung (Regex, Pflichtfelder, etc.)
4. ⏳ Multi-Line Support (QTextEdit für lange Texte)
5. ⏳ Date-Picker Integration (für Datums-Felder)

---

**STATUS**: ✅ Input-Controls sind jetzt vollständig editierbar mit automatischem Read-Only bei fehlender Instanz!
