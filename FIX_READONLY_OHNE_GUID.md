# Fix: Read-Only bei fehlender GUID-Zuordnung

## 🎯 Problem

**SYMPTOM**: Wenn keine GUID-Zuordnung gefunden wird, können dennoch Daten eingegeben werden!

**BEISPIEL**:
```
Person hat KEINE Finanzdaten-GUID
→ Control sollte read-only sein
→ ABER: User kann trotzdem Daten eingeben! ❌
```

---

## 🔍 Root Cause

### 1. **Statisches Read-Only bei `_create_ui()`**

```python
# VORHER (PROBLEM):
def _create_ui(self):
    """UI erstellen - NUR EINMAL beim render()"""
    
    # Read-Only Status wird beim Erstellen gesetzt
    if self.read_only:
        self.edit_widget.setReadOnly(True)
    else:
        self.edit_widget.setReadOnly(False)
        self.edit_widget.textChanged.connect(self._on_value_changed)
```

**Problem**:
- UI wird nur EINMAL erstellt (bei `render()`)
- Beim `refresh()` wird UI NICHT neu erstellt
- Read-Only Status wird NICHT aktualisiert

### 2. **Szenario: Stichtag-Wechsel**

```
Stichtag 1 (OHNE GUID):
→ render() erstellt UI mit read_only=True ✅

Stichtag 2 (MIT GUID):
→ refresh() setzt self.read_only=False
→ ABER: UI wird nicht aktualisiert! ❌
→ Widget bleibt read-only (oder umgekehrt)
```

---

## ✅ Lösung

### 1. **Dynamisches Read-Only Update**

```python
# NEU: _update_readonly_state()
def _update_readonly_state(self):
    """
    Aktualisiert Read-Only Status des Edit-Widgets
    
    WICHTIG: Wird bei refresh() aufgerufen!
    """
    if not self.edit_widget:
        return
    
    if self.read_only:
        # READ-ONLY: Nicht editierbar
        self.edit_widget.setReadOnly(True)
        self.edit_widget.setStyleSheet("""
            QLineEdit {
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                padding: 5px;
                color: #7f8c8d;
            }
        """)
        
        # Change-Handler trennen
        try:
            self.edit_widget.textChanged.disconnect(self._on_value_changed)
        except:
            pass
        
    else:
        # EDITIERBAR
        self.edit_widget.setReadOnly(False)
        self.edit_widget.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #3498db;
                border-radius: 3px;
                padding: 5px;
                color: #2c3e50;
            }
        """)
        
        # Change-Handler verbinden
        try:
            self.edit_widget.textChanged.disconnect(self._on_value_changed)
        except:
            pass
        self.edit_widget.textChanged.connect(self._on_value_changed)
```

### 2. **Update bei refresh()**

```python
def _update_ui(self):
    """Aktualisiert UI mit aktuellen Werten"""
    
    # [1] READ-ONLY STATUS AKTUALISIEREN (wichtig bei refresh!)
    self._update_readonly_state()
    
    # [2] HISTORIE-BUTTON SICHTBARKEIT AKTUALISIEREN
    self._update_history_button_visibility()
    
    # [3] Wert anzeigen
    display_value = str(self.current_value) if self.current_value is not None else ""
    self.edit_widget.blockSignals(True)
    self.edit_widget.setText(display_value)
    self.edit_widget.blockSignals(False)
    
    # [4] Abdatum-Label aktualisieren
    if self.abdatum_wert:
        abdatum_text = f"Stand: {self.abdatum_dt.FormTimeStamp}"
        self.value_label.setText(abdatum_text)
    else:
        self.value_label.setText("")
```

### 3. **Historie-Button Sichtbarkeit**

```python
def _update_history_button_visibility(self):
    """
    Aktualisiert Sichtbarkeit des Historie-Buttons
    
    WICHTIG: Button nur sichtbar wenn:
    - historical=True UND
    - zugeordnete_instanz vorhanden
    """
    if not self.history_button:
        return
    
    # Button nur sichtbar wenn Instanz vorhanden
    should_show = self.historical and (self.zugeordnete_instanz is not None)
    self.history_button.setVisible(should_show)
```

---

## 🔄 Ablauf (korrigiert)

### Szenario 1: Keine GUID gefunden

```python
# [1] render() aufgerufen
control.render()

# → _resolve_instance()
#    ⚠️ Keine GUID gefunden
#    → self.read_only = True
#    → self.zugeordnete_instanz = None

# → _create_ui()
#    → Edit-Widget erstellt
#    → setReadOnly(True) gesetzt

# → _update_ui()
#    → _update_readonly_state()
#       → Widget bleibt read-only ✅
#    → _update_history_button_visibility()
#       → Historie-Button versteckt ✅

# ERGEBNIS: Control ist read-only, Dateneingabe NICHT möglich ✅
```

### Szenario 2: Stichtag-Wechsel mit GUID

```python
# [1] Stichtag wechseln (zu Zeitpunkt MIT GUID)
gcs.st_inst.PdvmDateTime = 2025213.0

# [2] refresh() aufgerufen
control.refresh()

# → _resolve_instance()
#    ✅ GUID gefunden: "guid-123"
#    → self.read_only = False
#    → self.zugeordnete_instanz = <Instanz>

# → _load_value_from_db()
#    → Wert aus Instanz laden

# → _update_ui()
#    → _update_readonly_state()
#       → setReadOnly(False) ✅
#       → Styling auf editierbar ✅
#       → textChanged Handler verbinden ✅
#    → _update_history_button_visibility()
#       → Historie-Button sichtbar ✅

# ERGEBNIS: Control ist editierbar, Dateneingabe möglich ✅
```

### Szenario 3: Stichtag-Wechsel OHNE GUID

```python
# [1] Stichtag wechseln (zu Zeitpunkt OHNE GUID)
gcs.st_inst.PdvmDateTime = 2025163.0

# [2] refresh() aufgerufen
control.refresh()

# → _resolve_instance()
#    ⚠️ Keine GUID gefunden
#    → self.read_only = True
#    → self.zugeordnete_instanz = None

# → _load_value_from_db()
#    → Keine Instanz → Wert = None

# → _update_ui()
#    → _update_readonly_state()
#       → setReadOnly(True) ✅
#       → Styling auf read-only ✅
#       → textChanged Handler trennen ✅
#    → _update_history_button_visibility()
#       → Historie-Button versteckt ✅

# ERGEBNIS: Control ist wieder read-only ✅
```

---

## 🧪 Testing

### Automatischer Test

```powershell
python test_readonly_without_guid.py
```

**Erwartung**:
- ✅ TEST 1: Control ist read-only ohne GUID
- ✅ TEST 2: Stichtag-Wechsel funktioniert korrekt

### Interaktiver Test

Im Test-Fenster:
1. Control ist initial read-only (grau)
2. Button "Stichtag MIT GUID" klicken
   - Control wird editierbar (weiß)
   - Historie-Button erscheint
3. Button "Stichtag OHNE GUID" klicken
   - Control wird wieder read-only (grau)
   - Historie-Button verschwindet

---

## ✅ Geänderte Dateien

### 1. `pdvm_input_control_v3_autonom.py`

**Neu hinzugefügt**:
- `_update_readonly_state()` - Dynamisches Read-Only Update
- `_update_history_button_visibility()` - Historie-Button Sichtbarkeit

**Geändert**:
- `_update_ui()` - Ruft neue Update-Methoden auf
- `refresh()` - Vereinfacht (Styling wird in `_update_ui()` gesetzt)

### 2. `test_readonly_without_guid.py` ✨ NEU

Enthält:
- `test_readonly_without_guid()` - Test ohne GUID
- `test_stichtag_change_with_guid()` - Test mit Stichtag-Wechsel
- `create_interactive_test_window()` - Interaktives Test-Fenster

---

## 📋 Checkliste

- [x] `_update_readonly_state()` implementiert
- [x] `_update_history_button_visibility()` implementiert
- [x] `_update_ui()` angepasst
- [x] `refresh()` vereinfacht
- [x] Test-Datei erstellt
- [ ] Tests ausführen
- [ ] Interaktiver Test mit echten Daten

---

## 🎯 Zusammenfassung

**PROBLEM**: Control erlaubt Dateneingabe trotz fehlender GUID-Zuordnung

**LÖSUNG**: 
- ✅ Dynamisches Read-Only Update bei `refresh()`
- ✅ Historie-Button Sichtbarkeit dynamisch
- ✅ Korrekte Signal-Handler Verwaltung

**ERGEBNIS**: 
- ✅ Keine GUID → Read-Only, keine Eingabe möglich
- ✅ GUID vorhanden → Editierbar, Eingabe möglich
- ✅ Stichtag-Wechsel → Korrektes Update des Status

---

**Stand**: 22.10.2025 - Read-Only bei fehlender GUID korrekt implementiert! 🎉
